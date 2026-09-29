"""Shared model mixins.

# [TR069/SP069] Eleven schemas each own an identically-shaped `outbox_event`
# table; they get ONE declaration, not eleven hand-copied ones.
# Approach: the same "one shared implementation, never a per-component copy"
# discipline `/MODULE-ARCHITECTURE-STANDARD.md` §4c applies to rate limiting.
# A component declares its outbox table by subclassing `OutboxEventMixin` and
# `Base` and setting `__table_args__` to its own schema — the column set cannot
# drift between components because there is only one definition of it.
# Traces to: TR069, SP069, MODULE-ARCHITECTURE-STANDARD §6.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class OutboxEventMixin:
    """Columns of every `<schema>.outbox_event` table, exactly as migration 001 created them."""

    __tablename__ = "outbox_event"

    @declared_attr
    def id(cls) -> Mapped[UUID]:  # noqa: N805
        return mapped_column(PGUUID(as_uuid=True), primary_key=True)

    @declared_attr
    def aggregate_id(cls) -> Mapped[UUID]:  # noqa: N805
        return mapped_column(PGUUID(as_uuid=True), nullable=False)

    @declared_attr
    def event_type(cls) -> Mapped[str]:  # noqa: N805
        return mapped_column(String, nullable=False)

    @declared_attr
    def payload(cls) -> Mapped[dict]:  # noqa: N805
        return mapped_column(JSONB, nullable=False)

    @declared_attr
    def occurred_at(cls) -> Mapped[datetime]:  # noqa: N805
        return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def published_at(cls) -> Mapped[datetime | None]:  # noqa: N805
        # NULL until the dispatcher forwards it to the Audit Bridge. SP069's
        # Class I threshold pages Operations when a row stays NULL for >15 min.
        return mapped_column(DateTime(timezone=True), nullable=True)


class TimestampMixin:
    """`created_at` / `updated_at`, both server-defaulted as the migrations declare them."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:  # noqa: N805
        return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:  # noqa: N805
        return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
