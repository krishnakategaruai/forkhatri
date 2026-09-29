"""SQLAlchemy models for the `mangaly_discovery` schema.

# [TR021/TR026/TR027] One model module per component package. Columns mirror
# `schema.sql` (as amended by migrations 031/032) exactly.
#
# [Confirmed live, 2026-09-13] `profile_id` here is, like every other
# `*_profile_id` column already found across Home Circle, Authorization and
# this schema, the candidate's ACCOUNT id — `discovery_index_searchable_or_owner`
# calls `mangaly_authz.is_self(profile_id)`, which only ever matches
# `mangaly.account_id`. `interface.py` names this at every write site.
# Traces to: TR021, TR026, TR027, SP021, SP026.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_SCHEMA = "mangaly_discovery"


class DiscoveryProfileIndex(Base):
    """[TR021/TR027] The Discovery read model — a denormalized copy of just
    enough profile state to filter and rank, refreshed synchronously by
    `profile.interface`'s own writes. Never joined live against
    `mangaly_profile` — that is the entire point of this table existing.

    [Migration 031] The biodata facts the rework filters on are real columns
    so filtering happens in SQL.
    """

    __tablename__ = "discovery_profile_index"
    __table_args__ = {"schema": _SCHEMA}

    profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    searchable: Mapped[bool] = mapped_column(Boolean, default=False)
    locality: Mapped[str | None] = mapped_column(default=None)
    relocation_willingness: Mapped[str | None] = mapped_column(default=None)
    education_level: Mapped[str | None] = mapped_column(default=None)
    profession: Mapped[str | None] = mapped_column(default=None)
    # `search_vector` (tsvector) is deliberately not an ORM column — it is
    # written via a raw `to_tsvector(...)` expression in `interface.py`.
    ranking_input_snapshot: Mapped[dict | None] = mapped_column(JSONB, default=None)
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    gender: Mapped[str | None] = mapped_column(default=None)
    looking_for: Mapped[str | None] = mapped_column(default=None)
    date_of_birth: Mapped[date | None] = mapped_column(Date, default=None)
    marital_status: Mapped[str | None] = mapped_column(default=None)
    diet: Mapped[str | None] = mapped_column(default=None)
    height_cm: Mapped[int | None] = mapped_column(default=None)
    gotra: Mapped[str | None] = mapped_column(default=None)
    sub_community: Mapped[str | None] = mapped_column(default=None)
    mother_tongue: Mapped[str | None] = mapped_column(default=None)
    income_band: Mapped[str | None] = mapped_column(default=None)
    manglik: Mapped[str | None] = mapped_column(default=None)
    profile_created_at: Mapped[datetime | None] = mapped_column(default=None)
    last_active_at: Mapped[datetime | None] = mapped_column(default=None)
