"""Identity component — public interface (MODULE-ARCHITECTURE-STANDARD §3).

Implements docs/ParentApp/07-tech-reqs.md TR10, TR12-TR14, TR19, TR20. Routers
call only these functions; nothing else reads or writes identity tables.

Failed code attempts are committed before the error is raised: the request
transaction rolls back on error, and an attempt counter that rolls back with it
would never exhaust.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import rate_limiting
from app.components.identity import delivery
from app.components.identity.identifiers import InvalidIdentifier, mask_email, mask_phone, normalize
from app.components.identity.secrets import (
    constant_time_equal,
    hash_password,
    new_otp_code,
    new_session_token,
    otp_mac,
    password_needs_rehash,
    token_digest,
    verify_password,
)
from app.config.settings import Settings
from app.errors import DomainError

SessionFactory = async_sessionmaker[AsyncSession]
# "dev" is written only by the development member switcher (migration 004).
AuthMethod = Literal["otp", "password", "dev"]

_MEMBER_COLUMNS = (
    "m.id, m.display_name, m.preferred_language, m.identity_level, "
    "m.status::text AS status, m.phone_e164, m.email"
)
_RETURNING_MEMBER = (
    "id, display_name, preferred_language, identity_level, "
    "status::text AS status, phone_e164, email"
)
_EDITABLE_FIELDS = ("display_name", "preferred_language")


@dataclass(frozen=True, slots=True)
class Member:
    member_id: UUID
    display_name: str
    preferred_language: str
    identity_level: int
    status: str
    phone_e164: str | None
    email: str | None

    def public(self) -> dict[str, Any]:
        return {
            "member_id": str(self.member_id),
            "display_name": self.display_name,
            "preferred_language": self.preferred_language,
            "identity_level": self.identity_level,
            "phone_hint": mask_phone(self.phone_e164) if self.phone_e164 else None,
            "email_hint": mask_email(self.email) if self.email else None,
        }

    def claims(self, session_expires_at: datetime, *, include_identifiers: bool) -> dict[str, Any]:
        result: dict[str, Any] = {
            "member_id": str(self.member_id),
            "display_name": self.display_name,
            "preferred_language": self.preferred_language,
            "identity_level": self.identity_level,
            "status": self.status,
            "session_expires_at": session_expires_at.isoformat(),
        }
        if include_identifiers:
            result["phone_e164"] = self.phone_e164
            result["email"] = self.email
        return result


@dataclass(frozen=True, slots=True)
class CodeChallenge:
    challenge_id: UUID
    channel: str
    destination_hint: str
    expires_in: int
    resend_in: int
    dev_code: str | None


@dataclass(frozen=True, slots=True)
class SignedIn:
    member: Member
    session_token: str
    expires_at: datetime


def _member(row: Row[Any]) -> Member:
    return Member(*row[:7])


def _delivery_unavailable() -> DomainError:
    return DomainError(
        "delivery_unavailable",
        "A sign-in code cannot be sent there right now. Sign in with your password or use your email address.",
        503,
    )


def _inactive() -> DomainError:
    return DomainError("account_unavailable", "This account cannot sign in. Contact ForKhatri support.", 403)


async def start_code_challenge(
    db: AsyncSession, factory: SessionFactory, settings: Settings, raw_identifier: str, client_ip: str
) -> CodeChallenge:
    await rate_limiting.hit(factory, f"code:ip:{client_ip}", limit=settings.rate_limit_code_per_ip, window_seconds=settings.rate_limit_window_seconds)
    try:
        identifier = normalize(raw_identifier)
    except InvalidIdentifier as exc:
        raise DomainError("invalid_identifier", str(exc), 422) from exc
    if not delivery.channel_available(settings, identifier):
        # Depends only on the channel, never on whether a member exists (anti-enumeration).
        raise _delivery_unavailable()
    await rate_limiting.hit(factory, f"code:id:{identifier.value}", limit=settings.rate_limit_code_per_identifier, window_seconds=settings.rate_limit_window_seconds)

    last_sent = await db.scalar(
        text("SELECT max(created_at) FROM identity.otp_challenge WHERE identifier = :identifier"),
        {"identifier": identifier.value},
    )
    if last_sent is not None:
        wait = settings.otp_resend_seconds - int((datetime.now(UTC) - last_sent).total_seconds())
        if wait > 0:
            raise rate_limiting.RateLimitExceeded(wait)

    challenge_id = uuid4()
    code = new_otp_code()
    await db.execute(
        text(
            "INSERT INTO identity.otp_challenge (id, identifier, channel, code_hmac, max_attempts, expires_at) "
            "VALUES (:id, :identifier, CAST(:channel AS identity.otp_channel), :mac, :max_attempts, :expires_at)"
        ),
        {
            "id": challenge_id,
            "identifier": identifier.value,
            "channel": identifier.channel,
            "mac": otp_mac(settings.otp_pepper, challenge_id, code),
            "max_attempts": settings.otp_max_attempts,
            "expires_at": datetime.now(UTC) + timedelta(seconds=settings.otp_ttl_seconds),
        },
    )
    # Send before committing: if delivery fails the request rolls back, so no
    # undeliverable challenge is left behind to trip the resend interval.
    try:
        await delivery.send_code(settings, identifier, code, idempotency_key=f"otp-{challenge_id}")
    except delivery.DeliveryUnavailable as exc:
        raise _delivery_unavailable() from exc
    await db.commit()
    return CodeChallenge(
        challenge_id=challenge_id,
        channel=identifier.channel,
        destination_hint=identifier.hint(),
        expires_in=settings.otp_ttl_seconds,
        resend_in=settings.otp_resend_seconds,
        dev_code=code if settings.dev_expose_otp else None,
    )


async def _checked_challenge(
    db: AsyncSession, factory: SessionFactory, settings: Settings, challenge_id: UUID, code: str
) -> Row[Any]:
    await rate_limiting.hit(factory, f"verify:{challenge_id}", limit=settings.rate_limit_verify_per_challenge, window_seconds=settings.rate_limit_window_seconds)
    row = (
        await db.execute(
            text(
                "SELECT id, identifier, code_hmac, attempt_count, max_attempts, expires_at, verified_at, consumed_at "
                "FROM identity.otp_challenge WHERE id = :id FOR UPDATE"
            ),
            {"id": challenge_id},
        )
    ).first()
    if row is None or row.consumed_at is not None:
        raise DomainError("code_invalid", "That code is not valid.")
    if row.attempt_count >= row.max_attempts:
        raise DomainError("code_attempts_exhausted", "Too many attempts. Request a new code.")
    if row.expires_at <= datetime.now(UTC):
        raise DomainError("code_expired", "That code has expired. Request a new one.")
    if not constant_time_equal(otp_mac(settings.otp_pepper, row.id, code), row.code_hmac):
        await db.execute(
            text("UPDATE identity.otp_challenge SET attempt_count = attempt_count + 1 WHERE id = :id"),
            {"id": row.id},
        )
        await db.commit()
        if row.attempt_count + 1 >= row.max_attempts:
            raise DomainError("code_attempts_exhausted", "Too many attempts. Request a new code.")
        raise DomainError("code_invalid", "That code is not valid.")
    return row


async def _member_by_identifier(db: AsyncSession, value: str) -> Member | None:
    row = (
        await db.execute(
            text(f"SELECT {_MEMBER_COLUMNS} FROM identity.member m WHERE m.phone_e164 = :v OR m.email = :v"),
            {"v": value},
        )
    ).first()
    return _member(row) if row is not None else None


async def _open_session(
    db: AsyncSession, settings: Settings, member: Member, method: AuthMethod, user_agent: str | None
) -> SignedIn:
    token = new_session_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.session_ttl_days)
    await db.execute(
        text(
            "INSERT INTO identity.session (member_id, token_hash, auth_method, user_agent, expires_at) "
            "VALUES (:member_id, :token_hash, CAST(:method AS identity.auth_method), :user_agent, :expires_at)"
        ),
        {
            "member_id": member.member_id,
            "token_hash": token_digest(token),
            "method": method,
            "user_agent": (user_agent or "")[:300],
            "expires_at": expires_at,
        },
    )
    return SignedIn(member, token, expires_at)


async def verify_code(
    db: AsyncSession,
    factory: SessionFactory,
    settings: Settings,
    challenge_id: UUID,
    code: str,
    user_agent: str | None,
) -> SignedIn | None:
    """Sign an existing member in, or return None when the identifier is new (name required)."""
    row = await _checked_challenge(db, factory, settings, challenge_id, code)
    member = await _member_by_identifier(db, row.identifier)
    if member is None:
        if row.verified_at is None:
            await db.execute(
                text(
                    "UPDATE identity.otp_challenge SET verified_at = now(), "
                    "expires_at = now() + (:grace * interval '1 second') WHERE id = :id"
                ),
                {"grace": settings.otp_verified_grace_seconds, "id": row.id},
            )
        return None
    if member.status != "active":
        raise _inactive()
    await db.execute(
        text("UPDATE identity.otp_challenge SET verified_at = coalesce(verified_at, now()), consumed_at = now() WHERE id = :id"),
        {"id": row.id},
    )
    return await _open_session(db, settings, member, "otp", user_agent)


async def complete_welcome(
    db: AsyncSession,
    factory: SessionFactory,
    settings: Settings,
    *,
    challenge_id: UUID,
    code: str,
    display_name: str,
    preferred_language: str,
    user_agent: str | None,
) -> SignedIn:
    row = await _checked_challenge(db, factory, settings, challenge_id, code)
    if row.verified_at is None:
        raise DomainError("code_invalid", "Verify the code before continuing.")
    member = await _member_by_identifier(db, row.identifier)
    if member is None:
        identifier = normalize(row.identifier)
        column = "phone_e164" if identifier.kind == "phone" else "email"
        created = (
            await db.execute(
                text(
                    f"INSERT INTO identity.member (display_name, {column}, preferred_language) "
                    f"VALUES (:display_name, :identifier, :language) RETURNING {_RETURNING_MEMBER}"
                ),
                {"display_name": display_name, "identifier": identifier.value, "language": preferred_language},
            )
        ).first()
        member = _member(created)
    elif member.status != "active":
        raise _inactive()
    await db.execute(
        text("UPDATE identity.otp_challenge SET consumed_at = now() WHERE id = :id"), {"id": row.id}
    )
    return await _open_session(db, settings, member, "otp", user_agent)


async def password_sign_in(
    db: AsyncSession,
    factory: SessionFactory,
    settings: Settings,
    *,
    raw_identifier: str,
    password: str,
    client_ip: str,
    user_agent: str | None,
) -> SignedIn:
    invalid = DomainError("invalid_credentials", "That sign-in didn't work. Check the details and try again.", 401)
    await rate_limiting.hit(factory, f"password:ip:{client_ip}", limit=settings.rate_limit_password_per_ip, window_seconds=settings.rate_limit_window_seconds)
    try:
        identifier = normalize(raw_identifier)
    except InvalidIdentifier:
        verify_password(None, password)
        raise invalid from None
    await rate_limiting.hit(factory, f"password:id:{identifier.value}", limit=settings.rate_limit_password_per_identifier, window_seconds=settings.rate_limit_window_seconds)

    row = (
        await db.execute(
            text(
                f"SELECT {_MEMBER_COLUMNS}, c.password_hash FROM identity.member m "
                "LEFT JOIN identity.password_credential c ON c.member_id = m.id "
                "WHERE m.phone_e164 = :v OR m.email = :v"
            ),
            {"v": identifier.value},
        )
    ).first()
    stored_hash = row.password_hash if row is not None else None
    if not verify_password(stored_hash, password) or row is None or row.status != "active":
        raise invalid
    member = _member(row)
    if stored_hash is not None and password_needs_rehash(stored_hash):
        await db.execute(
            text("UPDATE identity.password_credential SET password_hash = :h, updated_at = now() WHERE member_id = :m"),
            {"h": hash_password(password), "m": member.member_id},
        )
    return await _open_session(db, settings, member, "password", user_agent)


async def members_by_id(db: AsyncSession, member_ids: list[UUID]) -> dict[UUID, Member]:
    """Active members among `member_ids` (unknown or inactive ids are omitted)."""
    if not member_ids:
        return {}
    rows = await db.execute(
        text(f"SELECT {_MEMBER_COLUMNS} FROM identity.member m WHERE m.id = ANY(CAST(:ids AS uuid[])) AND m.status = 'active'"),
        {"ids": member_ids},
    )
    return {member.member_id: member for member in map(_member, rows)}


async def open_development_session(
    db: AsyncSession, settings: Settings, member_id: UUID, user_agent: str | None
) -> SignedIn:
    """Development tools only (07-tech-reqs.md "Development tools"): a session without a credential.

    Refuses unless the development tools are active, so this cannot open a session
    in production even if something other than the dev router called it.
    """
    if not settings.dev_tools_active:
        raise RuntimeError("Development sessions are disabled in this environment.")
    member = (await members_by_id(db, [member_id])).get(member_id)
    if member is None:
        raise DomainError("member_unknown", "No active member has that id.", 404)
    return await _open_session(db, settings, member, "dev", user_agent)


async def resolve_session(db: AsyncSession, token: str) -> tuple[Member, datetime] | None:
    if not token or len(token) > 128:
        return None
    row = (
        await db.execute(
            text(
                f"SELECT {_MEMBER_COLUMNS}, s.id AS session_id, s.expires_at, s.last_seen_at "
                "FROM identity.session s JOIN identity.member m ON m.id = s.member_id "
                "WHERE s.token_hash = :h AND s.revoked_at IS NULL AND s.expires_at > now() AND m.status = 'active'"
            ),
            {"h": token_digest(token)},
        )
    ).first()
    if row is None:
        return None
    if row.last_seen_at < datetime.now(UTC) - timedelta(minutes=5):
        await db.execute(
            text("UPDATE identity.session SET last_seen_at = now() WHERE id = :id"), {"id": row.session_id}
        )
    return _member(row), row.expires_at


async def sign_out(db: AsyncSession, token: str, *, everywhere: bool) -> None:
    digest = token_digest(token)
    if everywhere:
        await db.execute(
            text(
                "UPDATE identity.session SET revoked_at = now() WHERE revoked_at IS NULL "
                "AND member_id = (SELECT member_id FROM identity.session WHERE token_hash = :h)"
            ),
            {"h": digest},
        )
    else:
        await db.execute(
            text("UPDATE identity.session SET revoked_at = now() WHERE token_hash = :h AND revoked_at IS NULL"),
            {"h": digest},
        )


async def update_member(db: AsyncSession, member_id: UUID, changes: dict[str, str | None]) -> Member:
    fields = [name for name in _EDITABLE_FIELDS if name in changes]
    if fields:
        assignments = ", ".join(f"{name} = :{name}" for name in fields)
        await db.execute(
            text(f"UPDATE identity.member SET {assignments}, updated_at = now() WHERE id = :id"),
            {**{name: changes[name] for name in fields}, "id": member_id},
        )
    row = (
        await db.execute(text(f"SELECT {_MEMBER_COLUMNS} FROM identity.member m WHERE m.id = :id"), {"id": member_id})
    ).first()
    return _member(row)


async def lookup_members(db: AsyncSession, member_ids: list[UUID]) -> list[dict[str, Any]]:
    if not member_ids:
        return []
    rows = await db.execute(
        text(
            "SELECT id, display_name, identity_level FROM identity.member "
            "WHERE id = ANY(CAST(:ids AS uuid[])) AND status = 'active'"
        ),
        {"ids": member_ids},
    )
    return [
        {"member_id": str(r.id), "display_name": r.display_name, "identity_level": r.identity_level}
        for r in rows
    ]
