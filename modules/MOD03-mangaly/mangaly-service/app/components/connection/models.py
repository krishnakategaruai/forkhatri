"""SQLAlchemy models for the `mangaly_connection` schema.

# [TR042-TR045] One model module per component package. Columns mirror
# `schema.sql` exactly.
#
# [Confirmed live, 2026-09-13] `acting_account_id` and `target_profile_id`
# are both ACCOUNT ids — `connection_participants`'s `is_self()` calls only
# ever match `mangaly.account_id`. `on_behalf_of_profile_id` is different:
# it is read by `has_scope(on_behalf_of_profile_id, 'candidate_info')`, and
# `mangaly_profile.profile`'s own RLS (`profile_owner_or_granted`) requires
# a `candidate_info` grant's `target_profile_id` to equal the real
# `profile.id` for that policy to ever pass — so a `candidate_info` grant
# (unlike Home Circle's `family_info` grants) must be created with the
# candidate's REAL `profile.id`, not their account id. Two different grant
# TYPES, two different id spaces, each internally consistent with its own
# one consuming RLS policy — `interface.py` names this at every write site.
# Traces to: TR042, TR043, TR044, TR045, SP042, SP043.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_SCHEMA = "mangaly_connection"


class ConnectionStatus(StrEnum):
    """Mirrors `mangaly_connection.connection_status`. No auto-expiry
    transition exists — a `pending` request stays pending indefinitely
    (FR043's own explicit failure-outcome requirement)."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ConnectionRequest(Base):
    """[TR042] `on_behalf_of_profile_id` is populated only for a family
    member acting for the candidate (M01-C's Capacity.FAMILY); a candidate
    acting for themselves leaves it NULL — `interface.py` never guesses
    which case it is from other fields."""

    __tablename__ = "connection_request"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    acting_account_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    on_behalf_of_profile_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), default=None)
    target_profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    status: Mapped[ConnectionStatus] = mapped_column(
        SqlEnum(
            ConnectionStatus,
            name="connection_status",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ConnectionStatus.PENDING,
    )
    requested_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    decided_at: Mapped[datetime | None] = mapped_column(default=None)
    decided_by_account_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
