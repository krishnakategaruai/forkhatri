"""SQLAlchemy models for the `mangaly_home_circle` schema.

# [TR007-TR016] One model module per component package, per the project's
# established ORM convention. Columns mirror `schema.sql` (as amended by
# `migrations/005-home-circle-relationship-type.sql`) exactly — this file
# describes the already-applied schema, it does not define it. No
# cross-schema `ForeignKey()` for `candidate_profile_id`/`member_account_id`/
# `inviter_account_id` — those are plain UUID columns into other schemas,
# resolved only through their own components' interfaces.
#
# [Confirmed live, 2026-09-13] Despite the column name inherited from
# `07a-er-model.md`, `candidate_profile_id` on every table here stores the
# candidate's ACCOUNT id, not `profile.id` — verified empirically against
# `mangaly_authz.is_self()`, which every RLS policy on these tables calls,
# and which only ever matches `mangaly.account_id`/`mangaly.authz_context`.
# `interface.py` names this explicitly at every write site rather than
# leaving it to be rediscovered by a second live failure.
# Traces to: TR007, TR008, TR009, TR010, TR011, TR014, TR016, SP007-SP016.
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
from app.db.mixins import OutboxEventMixin

_SCHEMA = "mangaly_home_circle"


class InvitationStatus(StrEnum):
    """Mirrors `mangaly_home_circle.invitation_status`."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class MembershipStatus(StrEnum):
    """Mirrors `mangaly_home_circle.membership_status`. Never a hard delete —
    `removed`/`left` preserve history for BR15 audit (M01-C §9: leaving does
    not erase that the participation happened)."""

    ACTIVE = "active"
    REMOVED = "removed"
    LEFT = "left"


class RelationshipType(StrEnum):
    """Mirrors `mangaly_home_circle.relationship_type` (migration 005).

    M01-C §4's functional-responsibility taxonomy — Candidate is the profile
    owner and is never itself a membership row, so only the other three
    categories exist here."""

    PARENT = "parent"
    SIBLING = "sibling"
    RELATIVE = "relative"


class Invitation(Base):
    """[TR007] One row per invite attempt. `invitee_account_id` starts NULL
    (TR007's own confirmed fallback: invite by identifier, not by directory
    search — no username/lookup capability exists in Identity Bridge) and is
    filled in only once the invitee actually accepts."""

    __tablename__ = "invitation"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    inviter_account_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    invitee_identifier: Mapped[str | None] = mapped_column(default=None)
    invitee_account_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), default=None)
    relationship_type: Mapped[RelationshipType] = mapped_column(
        SqlEnum(
            RelationshipType,
            name="relationship_type",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    status: Mapped[InvitationStatus] = mapped_column(
        SqlEnum(
            InvitationStatus,
            name="invitation_status",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=InvitationStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    expires_at: Mapped[datetime | None] = mapped_column(default=None)


class Membership(Base):
    """[TR008] One row per (candidate, member). `relationship_type` is copied
    from the accepted invitation rather than joined at read time, because
    `invitation_id` is `ON DELETE SET NULL` — the relationship claim must
    outlive the invitation row (see migration 005)."""

    __tablename__ = "membership"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    member_account_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    invitation_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.invitation.id", ondelete="SET NULL"),
        default=None,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        SqlEnum(
            RelationshipType,
            name="relationship_type",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    status: Mapped[MembershipStatus] = mapped_column(
        SqlEnum(
            MembershipStatus,
            name="membership_status",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=MembershipStatus.ACTIVE,
    )
    joined_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    removed_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class HomeCircleNote(Base):
    """[TR016, migration 022] A private working note about one match
    (`subject_account_id`, an account id), readable only by its author.
    Forwarding is per note: the author asks (`forward_requested_at`), the
    candidate reads it (`forwarded_at`) or says not now
    (`forward_declined_at`) — reading one note never exposes another."""

    __tablename__ = "home_circle_note"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    author_membership_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.membership.id", ondelete="CASCADE")
    )
    subject_account_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    content: Mapped[str]
    forward_requested_at: Mapped[datetime | None] = mapped_column(default=None)
    forwarded_at: Mapped[datetime | None] = mapped_column(default=None)
    forward_declined_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Suggestion(Base):
    """[TR014] Suggestion ≠ decision — structurally, not just by convention:
    no column here references `mangaly_connection.connection_request`, and
    `interface.py` has no function that reads a suggestion and writes one."""

    __tablename__ = "suggestion"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    suggested_by_membership_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.membership.id", ondelete="CASCADE")
    )
    suggested_profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    note: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Report(Base):
    """[TR011] M01-C §8's false-relationship-claim / abusive-invitation report."""

    __tablename__ = "report"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    reporter_account_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    membership_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.membership.id", ondelete="CASCADE")
    )
    reason: Mapped[str]
    case_reference: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class HomeCircleOutboxEvent(Base, OutboxEventMixin):
    __table_args__ = {"schema": _SCHEMA}
