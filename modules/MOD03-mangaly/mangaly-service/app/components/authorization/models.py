"""SQLAlchemy models for the `mangaly_authz` schema.

# [TR017/TR018/TR024] The canonical grant model every other schema's RLS keys off.
# Approach: one model module per component package, per
# `07a-db-implementation/README.md`'s ORM conventions. Columns mirror
# `schema.sql` exactly — this file describes the already-applied schema, it does
# not define it (migrations remain authoritative; `create_all` is never called).
# `subject_id` / `target_profile_id` are plain UUID columns with no
# `ForeignKey()`, matching the module-wide "no cross-schema database-level FK"
# rule (07a-er-model.md Assumptions #3).
# Traces to: TR017, TR018, TR024, SP017, SP018.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import OutboxEventMixin

_SCHEMA = "mangaly_authz"

# `native_enum=True` with `create_type=False`: the Postgres enum types already
# exist from migration 001 and must not be re-created by the ORM.
_grant_scope = SAEnum(
    "candidate_info",
    "family_info",
    name="grant_scope",
    schema=_SCHEMA,
    create_type=False,
)
_grant_type = SAEnum(
    "home_circle_membership",
    "connection_accepted",
    "safety_override",
    "admin_case",
    "pause_exception",
    name="grant_type",
    schema=_SCHEMA,
    create_type=False,
)
_grant_status = SAEnum(
    "active", "withheld", "revoked", name="grant_status", schema=_SCHEMA, create_type=False
)


class Grant(Base):
    """`mangaly_authz.grant` — written only through this component's interface."""

    __tablename__ = "grant"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    target_profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    scope: Mapped[str] = mapped_column(_grant_scope)
    grant_type: Mapped[str] = mapped_column(_grant_type)
    status: Mapped[str] = mapped_column(_grant_status)
    source_component: Mapped[str] = mapped_column(String)
    source_reference_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SafetyOverrideGrant(Base):
    """`mangaly_authz.safety_override_grant` — TR024's individually-audited exception."""

    __tablename__ = "safety_override_grant"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    grant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    safety_case_reference: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    ops_reviewed: Mapped[bool] = mapped_column(Boolean)
    ops_reviewer_account_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthzOutboxEvent(OutboxEventMixin, Base):
    """`mangaly_authz.outbox_event` — every grant/deny decision, same transaction.

    Declared via the shared mixin so all eleven outbox tables have provably
    identical columns (see `app/db/mixins.py`).
    """

    __table_args__ = {"schema": _SCHEMA}
