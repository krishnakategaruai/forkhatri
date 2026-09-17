"""Identity Bridge — public interface.

This module is the ONLY way other components reach identity state
(`/MODULE-ARCHITECTURE-STANDARD.md` §3): nothing imports this component's
models or repository directly.

Implements:
  * FR092 / TR092 — account sign-up (interim store, IA092 technical debt)
  * FR093 / TR093 — login, structurally anti-enumeration and rate-limited
  * FR090 / TR090 — session validation on launch
  * FR101 / TR101 — logout by server-side session revocation

Security findings from Step 8 that are implemented here as code, not advice:
  * SP093 — an identical response body AND an identical time profile for
    "wrong password" and "no such account". The dummy-verify below is what
    makes the second half true; without it, a slow Argon2id hash on the
    account-exists path re-reveals exactly what the identical body hides.
  * SP092 — sign-up does not disclose whether an identifier is already
    registered. See `sign_up`'s docstring for the deviation this represents
    from UX03's older error-state table, and why UI03 already set the
    precedent.
  * SP103 — the pre-authentication lookup goes through the exact-match
    `mangaly_identity.lookup_by_identifier()` SECURITY DEFINER function, which
    returns at most one row and only three columns. No pattern match, no
    caller-supplied predicate, and no general repository method exists to call
    by mistake.
  * SP104 — `mangaly.account_id` is bound with SET LOCAL only, inside the
    request transaction, so a pooled connection cannot inherit it.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import insert, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.identity_bridge import delivery
from app.components.identity_bridge import otp as otp_module
from app.components.identity_bridge import platform as platform_client
from app.components.identity_bridge.credentials import (
    CredentialTooWeak,
    get_credential_hasher,
)
from app.components.identity_bridge.models import Account, AccountStatus, Session
from app.components.identity_bridge.otp import OtpOutcome, OtpPurpose
from app.config.settings import get_settings
from app.db.session import set_account_context
from app.rate_limiting import limiter

# Re-exported so callers (the auth router) reach OTP through this one module
# rather than importing a sibling component file directly — `interface.py`
# stays the single public surface (`/MODULE-ARCHITECTURE-STANDARD.md` §3).
__all__ = [
    "AuthError",
    "OtpOutcome",
    "OtpPurpose",
    "OtpVerifyResult",
    "PlatformIdentityUnavailable",
    "PlatformLinkRefused",
    "PlatformSession",
    "PlatformSessionInvalid",
    "RateLimited",
    "ResendRateLimited",
    "SessionToken",
    "SignUpResult",
    "WeakCredential",
    "aclose_platform_client",
    "confirm_password_reset",
    "get_own_identifiers",
    "log_in",
    "log_out",
    "request_login_otp",
    "request_otp_resend",
    "request_password_reset",
    "resolve_platform_session",
    "revoke_all_sessions",
    "sign_up",
    "validate_session",
    "verify_otp",
]

ResendRateLimited = otp_module.ResendRateLimited
PlatformIdentityUnavailable = platform_client.PlatformIdentityUnavailable
PlatformSessionInvalid = platform_client.PlatformSessionInvalid
aclose_platform_client = platform_client.aclose_client

SESSION_TTL = timedelta(days=get_settings().session_ttl_days)


class AuthError(Exception):
    """The single failure type every auth path raises.

    [SP093] Deliberately carries no reason code and no field attribution. One
    exception type means a caller physically cannot render "wrong password"
    differently from "no such account", because it never learns which occurred.
    """


class WeakCredential(Exception):
    """Raised when a credential fails the strength floor at sign-up.

    [ADR-010] Carries an i18n key + params (see `credentials.CredentialTooWeak`)
    rather than English prose, for the HTTP layer to localize.
    """

    def __init__(self, key: str, **params: object) -> None:
        super().__init__(key)
        self.key = key
        self.params = params


class RateLimited(Exception):
    """Raised when the shared rate limiter rejects an attempt."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("rate limited")
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True, slots=True)
class SignUpResult:
    """What sign-up tells the caller.

    [SP092] Note what is NOT here: any indication of whether the identifier was
    already registered. `created` is for the server's own branching (whether to
    send a verification code or an account-already-exists notice out of band);
    the HTTP layer renders one identical response either way.
    """

    created: bool
    account_id: UUID | None


@dataclass(frozen=True, slots=True)
class SessionToken:
    token: str
    account_id: UUID
    expires_at: datetime


def _normalise(identifier: str) -> str:
    return identifier.strip().lower()


def _is_email(identifier: str) -> bool:
    return "@" in identifier


async def sign_up(
    session: AsyncSession,
    *,
    identifier: str,
    credential: str | None = None,
) -> SignUpResult:
    """[FR092/TR092, DEC-V1-012] Create an account for a phone or email identifier.

    `credential` is now OPTIONAL (DEC-V1-012, 2026-09-13): sign-up's primary
    path is identifier + OTP only, matching the lowest-friction pattern real
    competitor research found this module's own named audience is best served
    by. When omitted, a random, unguessable, never-exposed credential is
    generated server-side purely to satisfy the account table's existing
    `credential_hash NOT NULL` column — no schema migration needed, and the
    Argon2id infrastructure this module already built stays exactly as
    correct for the deferred "set a real password later" path DEC-V1-012 also
    names. A caller that DOES supply a credential still gets it validated and
    hashed for real, for that same later opt-in path.

    Returns `created=False` when the identifier is already registered. The
    caller MUST NOT surface that difference to the client.

    **Deviation from UX03, recorded deliberately.** UX03's error-state table
    specifies an inline "This phone is already registered. Log in instead?"
    message. SP092 found that to be an account-enumeration oracle, and on a
    matrimonial platform the single bit it leaks — that a named person has an
    account — discloses that they are seeking marriage, which carries real
    social consequence in this module's context. UI03 had already resolved the
    identical tension for FR094's reset screen ("exactly one visual variant...
    no differing error state exists in the spec", citing GitHub/Google
    anti-enumeration UX), so the generic response is this design system's own
    established precedent rather than a new invention. The user is not
    stranded: an already-registered identifier receives an out-of-band notice
    on the channel only its real owner can read.
    """
    normalised = _normalise(identifier)

    # [SP092 denial-of-service row] Rate-limit signup itself, per identifier —
    # named in this file's own header as a finding, but never actually wired
    # until this pass. Durable, matching every other abuse-prevention counter
    # in this component (a rejected signup still must count).
    settings = get_settings()
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.SIGNUP,
            subject=normalised,
            limit_max=settings.rate_limit_login_failure_max,
            window_seconds=settings.rate_limit_login_failure_window_seconds,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    hasher = get_credential_hasher()
    if credential is not None:
        try:
            # [FR092 failure outcome] "A ... weak credential ... blocks account
            # creation with a specific, actionable reason" — applies only when
            # a credential is actually supplied (DEC-V1-012's opt-in path); the
            # primary OTP-only path has no credential to validate.
            hasher.validate_strength(credential)
        except CredentialTooWeak as exc:
            # Credential strength IS safe to report — it describes what the
            # caller just typed, not whether anyone else exists. Key + params
            # carried through unchanged for the HTTP layer to localize (ADR-010).
            raise WeakCredential(exc.key, **exc.params) from exc
        credential_hash = hasher.hash(credential)
    else:
        # Never validated, never returned, never logged — this hash exists
        # only so the column is non-null. `verify_or_dummy` will correctly
        # reject any login attempt against it, indistinguishably from a wrong
        # password, which is exactly the desired behaviour for a credential
        # nobody — including its own account holder — knows.
        credential_hash = hasher.hash(secrets.token_urlsafe(32))

    existing = await _lookup_by_identifier(session, normalised)
    if existing is not None:
        # Deliberately does no work against the existing row. The out-of-band
        # notice is the caller's job (Notification Bridge); this component does
        # not mutate another account's state on an unauthenticated request.
        return SignUpResult(created=False, account_id=None)

    account_id = uuid4()
    # [TR017] Deliberately a Core INSERT with no RETURNING, not `session.add()`.
    #
    # The ORM flush emits `INSERT ... RETURNING id`, and under RLS Postgres
    # applies the table's SELECT policy to the returned row. `account_self_only`
    # restricts SELECT to `id = mangaly.account_id`, which at signup is by
    # definition unset — so the RETURNING clause fails the policy and Postgres
    # reports it as "new row violates row-level security policy", which reads
    # like a WITH CHECK failure and sends you looking in the wrong place.
    # Migration 003 fixed the WITH CHECK half of this; this is the read-back
    # half. Same root cause, and the same fix already applied to the outbox in
    # `app/events/bus.py`: generate the id application-side and never ask for it
    # back, rather than widening the SELECT policy to make a write convenient.
    await session.execute(
        insert(Account).values(
            id=account_id,
            phone_identifier=None if _is_email(normalised) else normalised,
            email_identifier=normalised if _is_email(normalised) else None,
            credential_hash=credential_hash,
            status=AccountStatus.PENDING_VERIFICATION,
        )
    )

    # [FR095] "set a minimum credential, before reaching onboarding" (FR092) —
    # signup issues the verification code as part of the same call, not as a
    # separate step the caller has to remember to invoke. The account context
    # is bindable here even pre-verification: the row was just created in this
    # same transaction, so `mangaly.account_id` naming it is not a forged claim.
    await set_account_context(session, account_id)
    challenge = await otp_module.issue(
        session, account_id=account_id, identifier=normalised, purpose=OtpPurpose.SIGNUP
    )
    await delivery.deliver(normalised, challenge)

    return SignUpResult(created=True, account_id=account_id)


async def log_in(
    session: AsyncSession,
    *,
    identifier: str,
    credential: str,
) -> SessionToken:
    """[FR093/TR093] Authenticate and open a server-side session.

    Raises `AuthError` for every failure — wrong credential, unknown
    identifier, or non-active account alike.
    """
    normalised = _normalise(identifier)

    # [TR093/SP093] Rate-limit per identifier BEFORE any hashing work, so a
    # flood costs the attacker a lookup rather than costing us Argon2id CPU.
    settings = get_settings()
    try:
        # `enforce_durable`, not `enforce`: a failed login rolls this transaction
        # back, and a counter incremented inside it would roll back too — the
        # limiter would then never reach its threshold. See its docstring.
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.LOGIN_FAILURE,
            subject=normalised,
            limit_max=settings.rate_limit_login_failure_max,
            window_seconds=settings.rate_limit_login_failure_window_seconds,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    record = await _lookup_by_identifier(session, normalised)
    hasher = get_credential_hasher()

    # [SP093] The timing half of anti-enumeration. `verify_or_dummy` runs the
    # same Argon2id work against a decoy when there is no account, so the
    # no-such-account branch cannot be identified by being measurably faster.
    # The lookup result is passed straight in: this function deliberately never
    # branches on existence before deciding whether to hash.
    stored_hash = record[1] if record is not None else None
    if not hasher.verify_or_dummy(stored_hash, credential):
        raise AuthError

    assert record is not None  # verify_or_dummy only returns True for a real hash
    account_id, _, status = record
    if status != AccountStatus.ACTIVE.value:
        # Same opaque failure: whether an account exists but is unverified or
        # suspended is not the caller's business either.
        raise AuthError

    return await _open_session(session, account_id)


async def _open_session(session: AsyncSession, account_id: UUID) -> SessionToken:
    """Create a server-side session for an already-authenticated account.

    Shared by `log_in` (password-authenticated) and `verify_otp` (channel-
    control-authenticated, immediately after signup) — both have independently
    established who the caller is by the time this runs, so session creation
    itself does not re-check credentials, only records the new session.
    """
    # [TR017/SP017] Bind the resolved identity for THIS transaction only. Every
    # RLS predicate below — including the session INSERT's own policy — reads
    # `mangaly.account_id`, and SET LOCAL is what keeps it from leaking onto the
    # next request that borrows this pooled connection.
    await set_account_context(session, account_id)

    expires_at = datetime.now(UTC) + SESSION_TTL
    row = Session(id=uuid4(), account_id=account_id, expires_at=expires_at)
    session.add(row)
    await session.flush()

    return SessionToken(token=str(row.id), account_id=account_id, expires_at=expires_at)


class PlatformLinkRefused(Exception):
    """The member is signed in to ForKhatri but may not enter Mangaly as-is.

    `code` is `platform_identity_conflict` (another proven Mangaly account holds
    one of the member's identifiers) or `platform_account_not_active` (the
    member's own Mangaly account is locked or deleted). Both need a human; the
    request fails closed rather than guessing.
    """

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class PlatformSession:
    """A resolved ForKhatri session as Mangaly sees it."""

    account_id: UUID
    expires_at: datetime | None


_LINK_REFUSAL_SQLSTATES = {
    "MGL09": "platform_identity_conflict",
    "MGL03": "platform_account_not_active",
}


def _link_refusal_code(exc: DBAPIError) -> str | None:
    orig = exc.orig
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    if sqlstate in _LINK_REFUSAL_SQLSTATES:
        return _LINK_REFUSAL_SQLSTATES[str(sqlstate)]
    message = str(orig)
    for code in _LINK_REFUSAL_SQLSTATES.values():
        if code in message:
            return code
    return None


async def resolve_platform_session(session: AsyncSession, token: str) -> PlatformSession:
    """[ForKhatri TR15] Resolve an `fk_session` token to Mangaly's account id.

    1. Claims come from the Identity & Trust Service (cached ≤30 s / 5 s,
       `platform.py`).
    2. `mangaly_identity.ensure_platform_account()` (migration 014) creates the
       member-link row just-in-time, or syncs its phone/email to the platform's
       verified identifiers — Home Circle matches invitations against exactly
       those columns (`get_own_identifiers`). It runs on every request, not only
       on a cache miss: the row write belongs to this request's transaction, and
       a cached "already ensured" could outlive a rolled-back first request.
    3. `mangaly.account_id` is bound with SET LOCAL, exactly as the interim
       `validate_session` did, so every RLS policy downstream is unchanged.

    `member_id == account_id` by construction (TR10/TR23).

    Raises `PlatformSessionInvalid` (→ 401), `PlatformIdentityUnavailable`
    (→ 503, never a default account) or `PlatformLinkRefused` (→ 403).
    """
    claims = await platform_client.resolve_token(token)
    if claims.status != "active":
        raise PlatformSessionInvalid

    try:
        result = await session.execute(
            text(
                "SELECT mangaly_identity.ensure_platform_account(:member_id, :phone, :email)"
            ).bindparams(member_id=claims.member_id, phone=claims.phone_e164, email=claims.email)
        )
    except DBAPIError as exc:
        code = _link_refusal_code(exc)
        if code is not None:
            raise PlatformLinkRefused(code) from exc
        if "platform_identity_invalid" in str(exc.orig):
            # Claims without identifiers: the platform is not sending Mangaly
            # what TR14 says it must. A configuration fault — fail closed.
            raise PlatformIdentityUnavailable from exc
        raise

    account_id: UUID = result.scalar_one()
    await set_account_context(session, account_id)
    if claims.display_name:
        # Keeps the member's own link row in step with their ForKhatri name
        # (migration 019). Allowed by `account_self_only`; writes only on change.
        await session.execute(
            text(
                "UPDATE mangaly_identity.account SET display_name = :name, updated_at = now() "
                "WHERE id = :account_id AND display_name IS DISTINCT FROM :name"
            ).bindparams(name=claims.display_name, account_id=account_id)
        )
    return PlatformSession(account_id=account_id, expires_at=claims.session_expires_at)


async def validate_session(session: AsyncSession, token: str) -> UUID | None:
    """[FR090/TR090] Resolve a bearer token to a live account id, or None.

    [2026-09-14] INTERIM path only — reached solely when
    `interim_identity_enabled` is true (automated tests). Platform sessions go
    through `resolve_platform_session`.

    Returns None for anything not currently valid — malformed, unknown,
    expired, or revoked — so a caller cannot distinguish those cases either.
    """
    try:
        session_id = UUID(token)
    except (ValueError, AttributeError):
        return None

    # [TR090/SP103-class] Goes through `lookup_session()`, a SECURITY DEFINER
    # function, for the same reason `_lookup_by_identifier` does: validating the
    # token is what ESTABLISHES `mangaly.account_id`, so it cannot itself be
    # gated on that value being set. A direct SELECT here matched zero rows
    # under `session_self_only` and failed every authenticated request with a
    # silent 401 (migration 004 records the finding). The function enforces
    # revoked/expired liveness internally, so this caller cannot skip it.
    result = await session.execute(
        text(
            "SELECT account_id FROM mangaly_identity.lookup_session(:sid)"
        ).bindparams(sid=session_id),
    )
    row = result.first()
    if row is None:
        return None

    account_id: UUID = row[0]
    await set_account_context(session, account_id)
    await session.execute(
        update(Session).where(Session.id == session_id).values(last_seen_at=datetime.now(UTC))
    )
    return account_id


async def get_own_identifiers(
    session: AsyncSession, *, account_id: UUID
) -> tuple[str | None, str | None]:
    """[FR007] The caller's OWN phone/email identifiers — `(phone, email)`.

    Not a general lookup: `account_self_only` restricts SELECT to
    `id = mangaly.account_id`, so this can only ever return the identifiers
    of the account whose own session already authenticated this request —
    there is no path from this function to another account's data. Built for
    Home Circle's invite-by-identifier flow (TR007's own named fallback,
    since a directory/username search does not exist in this module): the
    invitee side of `list_pending_invitations()` matches a stored
    `invitee_identifier` against these, never the other way around.
    SP103's "no general lookup method" rule governs the *pre-authentication*
    surface specifically (`_lookup_by_identifier`, exact-match only, called
    before `mangaly.account_id` exists) — this function is a different,
    self-only, post-authentication read and does not widen that surface.
    """
    row = (
        await session.execute(
            text(
                "SELECT phone_identifier, email_identifier FROM mangaly_identity.account "
                "WHERE id = :account_id"
            ).bindparams(account_id=account_id)
        )
    ).first()
    if row is None:
        return (None, None)
    return (row[0], row[1])


async def log_out(session: AsyncSession, token: str) -> None:
    """[FR101/TR101] Revoke a session server-side.

    SP101: clearing client state is a consequence of logout, never the
    mechanism — a stolen token has to stop working at the server.
    """
    try:
        session_id = UUID(token)
    except (ValueError, AttributeError):
        return
    await session.execute(
        update(Session)
        .where(Session.id == session_id, Session.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


async def revoke_all_sessions(session: AsyncSession, account_id: UUID) -> None:
    """[SP094] Invalidate every live session for an account.

    Called on password reset: if the attacker's session survives the victim's
    reset, the reset accomplishes nothing.
    """
    await session.execute(
        update(Session)
        .where(Session.account_id == account_id, Session.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


@dataclass(frozen=True, slots=True)
class OtpVerifyResult:
    """[UX04, DEC-V1-012] Success routes onward — Onboarding after signup, Home
    after an OTP-primary login, Set-new-password after reset. The signup and
    login paths both land already authenticated rather than asking the user to
    prove who they are a second time. `session` is populated for
    `purpose in {signup, login}`; a reset-purpose verification has no session
    to open yet — that happens after the new password is set."""

    outcome: OtpOutcome
    session: SessionToken | None = None


_PURPOSES_THAT_OPEN_A_SESSION = frozenset({OtpPurpose.SIGNUP, OtpPurpose.LOGIN})


async def verify_otp(
    session: AsyncSession, *, identifier: str, code: str, purpose: OtpPurpose
) -> OtpVerifyResult:
    """[FR095/TR095, DEC-V1-012] Check a verification code. See `otp.verify`
    for the full rationale, including why UX04's distinct error copy and
    SP095's uniform responses are compatible rather than contradictory."""
    outcome = await otp_module.verify(session, identifier=identifier, code=code, purpose=purpose)
    if outcome is not OtpOutcome.VERIFIED or purpose not in _PURPOSES_THAT_OPEN_A_SESSION:
        return OtpVerifyResult(outcome=outcome)

    record = await _lookup_by_identifier(session, _normalise(identifier))
    assert record is not None  # just verified; the account cannot have vanished
    token = await _open_session(session, record[0])
    return OtpVerifyResult(outcome=outcome, session=token)


async def request_login_otp(session: AsyncSession, *, identifier: str) -> None:
    """[FR093/DEC-V1-012] Request an OTP for the primary, passwordless login path.

    Same anti-enumeration shape as `request_otp_resend`: a no-op, from the
    caller's point of view indistinguishable from success, for an identifier
    that does not exist or is not yet active (SP092-class oracle by another
    route — this endpoint is unauthenticated, same as sign-up's).
    """
    settings = get_settings()
    normalised = _normalise(identifier)

    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.LOGIN_OTP_REQUEST,
            subject=normalised,
            limit_max=settings.rate_limit_otp_resend_max_per_hour,
            window_seconds=3600,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    record = await _lookup_by_identifier(session, normalised)
    if record is None or record[2] != AccountStatus.ACTIVE.value:
        # Unknown identifier and "exists but not yet verified" are the same
        # no-op from here — an unverified account has no completed sign-up to
        # log into yet, and saying so would itself leak existence.
        return

    account_id = record[0]
    await set_account_context(session, account_id)
    challenge = await otp_module.issue(
        session, account_id=account_id, identifier=normalised, purpose=OtpPurpose.LOGIN
    )
    await delivery.deliver(normalised, challenge)


async def request_password_reset(session: AsyncSession, *, identifier: str) -> None:
    """[FR094/TR094] Request a password-reset OTP.

    Same anti-enumeration shape as `request_login_otp()` — a no-op,
    indistinguishable from success, for an identifier that does not exist or
    is not yet active. Reuses FR095's own OTP challenge/verify machinery
    rather than the separate `password_reset_token` table `07a-er-model.md`
    defined: `OtpVerifyResult`'s own docstring already anticipated this
    ("Set-new-password after reset"), and `revoke_all_sessions()` below was
    already written and documented as "Called on password reset" before this
    function existed to call it — this pass is wiring up work that was
    already half-built, not inventing a new mechanism.
    """
    settings = get_settings()
    normalised = _normalise(identifier)

    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.PASSWORD_RESET_REQUEST,
            subject=normalised,
            limit_max=settings.rate_limit_otp_resend_max_per_hour,
            window_seconds=3600,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    record = await _lookup_by_identifier(session, normalised)
    if record is None or record[2] != AccountStatus.ACTIVE.value:
        # Unknown or unverified identifier: same no-op as request_login_otp(),
        # for the same reason (SP094's anti-enumeration requirement).
        return

    account_id = record[0]
    await set_account_context(session, account_id)
    challenge = await otp_module.issue(
        session, account_id=account_id, identifier=normalised, purpose=OtpPurpose.PASSWORD_RESET
    )
    await delivery.deliver(normalised, challenge)


async def confirm_password_reset(
    session: AsyncSession, *, identifier: str, code: str, new_credential: str
) -> OtpOutcome:
    """[FR094/TR094] Verify the reset code and set a new credential in one
    step. There is no separate "reset ticket" state between verification and
    setting the password: an OTP challenge is single-use, so it cannot be
    checked once to open a ticket and again to confirm the new password —
    identifier, code, and the new credential all arrive together.

    On success, every existing session for the account is revoked
    (`revoke_all_sessions` — SP094: a stolen session must not outlive the
    legitimate owner's reset) and the new credential replaces the old one
    through the same Argon2id hasher every other credential path uses.
    """
    outcome = await otp_module.verify(
        session, identifier=identifier, code=code, purpose=OtpPurpose.PASSWORD_RESET
    )
    if outcome is not OtpOutcome.VERIFIED:
        return outcome

    hasher = get_credential_hasher()
    try:
        hasher.validate_strength(new_credential)
    except CredentialTooWeak as exc:
        raise WeakCredential(exc.key, **exc.params) from exc

    record = await _lookup_by_identifier(session, _normalise(identifier))
    assert record is not None  # just verified; the account cannot have vanished
    account_id = record[0]

    await session.execute(
        update(Account)
        .where(Account.id == account_id)
        .values(credential_hash=hasher.hash(new_credential))
    )
    await revoke_all_sessions(session, account_id)
    return outcome


async def request_otp_resend(
    session: AsyncSession, *, identifier: str, purpose: OtpPurpose
) -> None:
    """[FR095/SP095] Re-send a code, rate-limited per identifier.

    Looks up the account itself (rather than requiring the caller already have
    an account_id) so the resend endpoint can sit alongside signup/reset with
    the same identifier-only request shape — and, like signup, says nothing
    different for an unknown identifier (SP092-class oracle by another route).
    """
    normalised = _normalise(identifier)
    record = await _lookup_by_identifier(session, normalised)
    if record is None:
        # Deliberately a no-op that still "succeeds" from the caller's view —
        # the HTTP layer returns the same response either way.
        return
    account_id = record[0]
    await set_account_context(session, account_id)
    challenge = await otp_module.request_resend(
        session, account_id=account_id, identifier=normalised, purpose=purpose
    )
    await delivery.deliver(normalised, challenge)


async def _lookup_by_identifier(
    session: AsyncSession, identifier: str
) -> tuple[UUID, str, str] | None:
    """[SP103] The module's one pre-authentication read, exact match only.

    Goes through `mangaly_identity.lookup_by_identifier()` — a SECURITY DEFINER
    function returning at most one row and only (id, credential_hash, status).
    This exists because `account_self_only` restricts SELECT to
    `id = mangaly.account_id`, which is by definition unset before login. SP103
    treats this function as a frozen surface: no pattern matching, no extra
    columns, and no general lookup method for a caller to reach for instead.
    """
    result = await session.execute(
        text(
            "SELECT id, credential_hash, status "
            "FROM mangaly_identity.lookup_by_identifier(:ident)"
        ).bindparams(ident=identifier)
    )
    row = result.first()
    if row is None:
        return None
    return (row[0], row[1], str(row[2]))
