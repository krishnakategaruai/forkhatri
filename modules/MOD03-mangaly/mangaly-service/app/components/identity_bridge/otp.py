"""One-time code issue and verification — FR095 / TR095 / UX04 / UI04 / TS212-213 / SP095.

Kept as its own module rather than grown inside `interface.py`: OTP has its own
lifecycle (issue, resend, verify, expire, exhaust) and its own abuse surface,
and `interface.py` re-exports the few functions other code actually needs.

What the source documents fix, and where each lands here:

  * FR095 — codes are time-bound and single-use; resend is rate-limited;
    success produces a BR08 account-authenticity evidence record. The evidence
    record is the `IdentifierVerified` domain event published in the same
    transaction as the state change (TS212 asks for an *event*), consumed by
    Trust & Verification when it lands. It cannot be written into
    `mangaly_trust.verification_layer_status` directly from here: that table is
    keyed by `profile_id`, and at signup no profile exists yet (FR001 comes
    later). Publishing the event is therefore both the correct component
    boundary and the only thing that is true right now.

  * SP095 — attempts are bounded and the challenge is SPENT on exhaustion, so a
    6-digit space cannot be walked; codes are hashed at rest; resend is limited
    per identifier through the shared durable limiter.

  * UX04 wants distinct "wrong code" and "expired code" messages, while SP095
    wants uniform responses. Both hold, because they are different
    distinctions: once a challenge exists the caller has already demonstrated
    they know the identifier, so telling them *why* their code failed leaks
    nothing. What must stay uniform is "no challenge exists for this
    identifier" — that would disclose whether the identifier is registered
    (SP092's oracle, by another route), so it returns the same result as a
    wrong code.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.identity_bridge.models import (
    Account,
    AccountStatus,
    OtpChallenge,
    OtpChannel,
    OtpPurpose,
)
from app.config.settings import get_settings
from app.events import bus
from app.rate_limiting import limiter

logger = logging.getLogger(__name__)


class OtpOutcome(StrEnum):
    """Why a verification failed, for the caller to render.

    `INVALID` deliberately covers both "wrong code" and "no challenge exists",
    so the two are indistinguishable from outside (see module docstring).
    """

    VERIFIED = "verified"
    INVALID = "invalid"
    EXPIRED = "expired"
    TOO_MANY_ATTEMPTS = "too_many_attempts"


@dataclass(frozen=True, slots=True)
class IssuedChallenge:
    """The result of issuing a code.

    `code` is returned so the caller can hand it to a delivery channel. It is
    never persisted in the clear and never returned to an end user outside
    debug mode.
    """

    challenge_id: UUID
    code: str
    expires_at: datetime
    channel: OtpChannel


def _hash_code(code: str, account_id: UUID) -> str:
    """Hash a code for storage, salted by the account it belongs to.

    A fast hash is correct here, unlike for passwords: the code is six digits
    and lives for minutes, so brute-force resistance comes from the bounded
    attempt count and the short window, not from hashing cost. Making this slow
    would only slow legitimate verification. Salting with the account id stops
    one stolen digest from being matched against every other account's.
    """
    return hashlib.sha256(f"{account_id}:{code}".encode()).hexdigest()


def _generate_code(digits: int) -> str:
    """A uniformly random numeric code, including leading zeros."""
    upper = 10**digits
    return str(secrets.randbelow(upper)).zfill(digits)


def channel_for(identifier: str) -> OtpChannel:
    return OtpChannel.EMAIL if "@" in identifier else OtpChannel.SMS


def mask_identifier(identifier: str) -> str:
    """[UX04] "We sent a 6-digit code to +91 XXXXX·····".

    Shows enough for the user to confirm they typed the right thing, never
    enough for a shoulder-surfer to read the whole identifier back.
    """
    if "@" in identifier:
        local, _, domain = identifier.partition("@")
        head = local[:2] if len(local) > 2 else local[:1]
        return f"{head}{'·' * max(3, len(local) - len(head))}@{domain}"
    tail = identifier[-3:]
    return f"{identifier[:3]}{'·' * max(3, len(identifier) - 6)}{tail}"


async def issue(
    session: AsyncSession,
    *,
    account_id: UUID,
    identifier: str,
    purpose: OtpPurpose,
) -> IssuedChallenge:
    """Create a challenge, superseding any live one for the same account+purpose.

    Superseding matters: without it a resend leaves the previous code valid, so
    "resend" would widen the window of live codes rather than replace it.
    """
    settings = get_settings()
    now = datetime.now(UTC)

    await session.execute(
        update(OtpChallenge)
        .where(
            OtpChallenge.account_id == account_id,
            OtpChallenge.purpose == purpose,
            OtpChallenge.used_at.is_(None),
        )
        .values(used_at=now)
    )

    code = _generate_code(settings.otp_code_digits)
    challenge_id = uuid4()
    expires_at = now + timedelta(seconds=settings.otp_ttl_seconds)

    # No RETURNING: the SELECT policy on this table keys on `mangaly.account_id`,
    # which is unset during signup. Same read-back problem as the account insert
    # (see `interface.sign_up`), same fix — the id is generated here.
    await session.execute(
        insert(OtpChallenge).values(
            id=challenge_id,
            account_id=account_id,
            channel=channel_for(identifier),
            purpose=purpose,
            code_hash=_hash_code(code, account_id),
            attempt_count=0,
            expires_at=expires_at,
        )
    )

    return IssuedChallenge(
        challenge_id=challenge_id,
        code=code,
        expires_at=expires_at,
        channel=channel_for(identifier),
    )


async def request_resend(
    session: AsyncSession,
    *,
    account_id: UUID,
    identifier: str,
    purpose: OtpPurpose,
) -> IssuedChallenge:
    """[FR095/SP095] Re-issue a code, rate-limited per identifier.

    Uses the DURABLE limiter: a resend that fails downstream still counted as an
    attempt, and a counter rolled back with the request would let an attacker
    drive unlimited SMS. SMS bombing costs Mangaly money directly, so this is a
    cost control as much as a user-harassment one.
    """
    settings = get_settings()
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.OTP_RESEND,
            subject=identifier.lower(),
            limit_max=settings.rate_limit_otp_resend_max_per_hour,
            window_seconds=3600,
        )
    except limiter.RateLimitExceeded as exc:
        raise ResendRateLimited(exc.result.retry_after_seconds) from exc

    return await issue(
        session, account_id=account_id, identifier=identifier, purpose=purpose
    )


class ResendRateLimited(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("resend rate limited")
        self.retry_after_seconds = retry_after_seconds


async def verify(
    session: AsyncSession,
    *,
    identifier: str,
    code: str,
    purpose: OtpPurpose,
) -> OtpOutcome:
    """[FR095/TR095/TS212/TS213] Check a code and, on success, activate the account.

    On success this both marks the challenge used and flips the account to
    `active` with `identifier_verified_at` set — the state change FR092's
    "sign-up succeeds only after identifier verification completes" refers to —
    and publishes the BR08 evidence event, all in the caller's one transaction.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    normalised = identifier.strip().lower()

    # Pre-authentication lookup: same SECURITY DEFINER function and the same
    # reasoning as everywhere else in this component (SP103).
    account_row = (
        await session.execute(
            text(
                "SELECT id, credential_hash, status "
                "FROM mangaly_identity.lookup_by_identifier(:ident)"
            ).bindparams(ident=normalised)
        )
    ).first()
    if account_row is None:
        # Indistinguishable from a wrong code, deliberately (SP092/SP095).
        return OtpOutcome.INVALID

    account_id: UUID = account_row[0]

    # [SP095] Bound guesses per challenge as well as per identifier, so a single
    # live challenge cannot be walked even within one rate-limit window.
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.OTP_VERIFY_ATTEMPT,
            subject=normalised,
            limit_max=settings.otp_max_attempts * 3,
            window_seconds=settings.otp_ttl_seconds,
        )
    except limiter.RateLimitExceeded:
        return OtpOutcome.TOO_MANY_ATTEMPTS

    # The account context is what the challenge table's RLS policy keys on, and
    # it is safe to bind here: the account was resolved server-side from the
    # identifier, not asserted by the caller.
    from app.db.session import set_account_context

    await set_account_context(session, account_id)

    challenge = (
        await session.execute(
            select(OtpChallenge)
            .where(
                OtpChallenge.account_id == account_id,
                OtpChallenge.purpose == purpose,
                OtpChallenge.used_at.is_(None),
            )
            .order_by(OtpChallenge.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if challenge is None:
        return OtpOutcome.INVALID

    if challenge.expires_at <= now:
        return OtpOutcome.EXPIRED

    if challenge.attempt_count >= settings.otp_max_attempts:
        # Spend the challenge rather than leaving it guessable for the rest of
        # its window — exhaustion has to actually cost something.
        await session.execute(
            update(OtpChallenge).where(OtpChallenge.id == challenge.id).values(used_at=now)
        )
        return OtpOutcome.TOO_MANY_ATTEMPTS

    if not hmac.compare_digest(challenge.code_hash, _hash_code(code, account_id)):
        await session.execute(
            update(OtpChallenge)
            .where(OtpChallenge.id == challenge.id)
            .values(attempt_count=challenge.attempt_count + 1)
        )
        return OtpOutcome.INVALID

    # --- Success. Everything below is one atomic unit with the caller. -------
    await session.execute(
        update(OtpChallenge).where(OtpChallenge.id == challenge.id).values(used_at=now)
    )
    await session.execute(
        update(Account)
        .where(Account.id == account_id)
        .values(
            status=AccountStatus.ACTIVE,
            identifier_verified_at=now,
            updated_at=now,
        )
    )

    # [TS212/FR095] The BR08 account-authenticity evidence record. Published in
    # this same transaction (TR069's outbox rule), so the evidence and the state
    # change cannot diverge.
    await bus.publish(
        session,
        schema="mangaly_authz",
        aggregate_id=account_id,
        event_type="IdentifierVerified",
        payload={
            "account_id": str(account_id),
            "channel": str(challenge.channel),
            "purpose": str(purpose),
            "verified_at": now.isoformat(),
            "evidence_layer": "account_authenticity",
        },
    )

    return OtpOutcome.VERIFIED
