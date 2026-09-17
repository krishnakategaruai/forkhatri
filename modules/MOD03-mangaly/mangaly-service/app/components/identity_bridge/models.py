"""Identity Bridge ORM models — `mangaly_identity` schema.

[TR092 / SP104] This schema is the module's INTERIM credential store. It exists
only because Mangaly is first in build order and no Common Platform Identity &
Trust Service exists yet to delegate to (ADR-016/017). It is named technical
debt in `v1-decisions.md`, not a permanent design, and SP104 threat-models it
as the module's highest-value single target: it holds credentials, OTP
challenges, reset tokens and live sessions in one place.

Only the four tables this component owns are modelled here. Columns mirror
`07a-db-implementation/schema.sql` exactly — a conformance test reflects the
live table and fails if the two drift.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_SCHEMA = "mangaly_identity"


class AccountStatus(StrEnum):
    """Mirrors the `mangaly_identity.account_status` Postgres enum.

    An account is `pending_verification` until FR095's OTP check passes — it is
    deliberately unusable before then, which is what stops a signup against an
    identifier the registrant does not control (SP092 Spoofing).
    """

    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    LOCKED = "locked"
    DELETED = "deleted"


class Account(Base):
    """[TR092] An account, keyed by phone or email identifier.

    `credential_hash` holds an Argon2id digest and nothing else (SP092 /
    `v1-decisions.md` credential-hashing note) — never a fast general-purpose
    hash, never an unsalted one.
    """

    __tablename__ = "account"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    phone_identifier: Mapped[str | None] = mapped_column(default=None)
    email_identifier: Mapped[str | None] = mapped_column(default=None)
    # [Migration 019] The member's ForKhatri display name, refreshed on sign-in.
    display_name: Mapped[str | None] = mapped_column(default=None)
    # [Migration 014] NULL for a ForKhatri platform member's link row: they
    # authenticate to the platform, never to Mangaly.
    credential_hash: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[AccountStatus] = mapped_column(
        SqlEnum(
            AccountStatus,
            name="account_status",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=AccountStatus.PENDING_VERIFICATION,
    )
    identifier_verified_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class OtpChannel(StrEnum):
    """Mirrors `mangaly_identity.otp_channel`."""

    SMS = "sms"
    EMAIL = "email"


class OtpPurpose(StrEnum):
    """Mirrors `mangaly_identity.otp_purpose`.

    The purpose is stored per challenge so a code issued for one flow cannot be
    replayed into another — a code sent to confirm a password reset must not
    also complete a signup.
    """

    SIGNUP = "signup"
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"
    IDENTIFIER_CHANGE = "identifier_change"


class OtpChallenge(Base):
    """[TR095/FR095] A single-use, time-bound one-time code.

    `code_hash` holds a digest, never the code itself: an OTP is a credential
    for the length of its window, and a database read should not hand over live
    codes. `attempt_count` bounds brute force against a 6-digit space (SP095) —
    the challenge is spent on exhaustion rather than allowing unlimited guesses.
    """

    __tablename__ = "otp_challenge"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.account.id", ondelete="CASCADE")
    )
    channel: Mapped[OtpChannel] = mapped_column(
        SqlEnum(
            OtpChannel,
            name="otp_channel",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    purpose: Mapped[OtpPurpose] = mapped_column(
        SqlEnum(
            OtpPurpose,
            name="otp_purpose",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    code_hash: Mapped[str]
    attempt_count: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Session(Base):
    """[TR090/TR101] A server-side session. Its primary key IS the bearer token.

    There is no separate token column by design: the id is a server-generated
    UUIDv4 the client never influences, and revocation is a server-side row
    update rather than anything the client can be trusted to perform. SP101
    requires logout to revoke here — clearing client state alone would leave a
    stolen token live, which matters on a shared or lost device.
    """

    __tablename__ = "session"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.account.id", ondelete="CASCADE")
    )
    issued_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)
    last_seen_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
