"""SQLAlchemy models for the `mangaly_discovery` schema.

# [TR021/TR026/TR027] One model module per component package. Columns mirror
# `schema.sql` exactly.
#
# [Confirmed live, 2026-09-13] `profile_id` here is, like every other
# `*_profile_id` column already found across Home Circle, Authorization and
# this schema, the candidate's ACCOUNT id — `discovery_index_searchable_or_owner`
# calls `mangaly_authz.is_self(profile_id)`, which only ever matches
# `mangaly.account_id`. `interface.py` names this at every write site.
# Traces to: TR021, TR026, TR027, SP021, SP026.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_SCHEMA = "mangaly_discovery"


class DiscoveryProfileIndex(Base):
    """[TR021/TR027] The Discovery read model — a denormalized copy of just
    enough profile state to filter and rank, refreshed synchronously by
    `profile.interface`'s own writes (see `interface.refresh_index`'s
    docstring for why this is a direct call rather than an outbox consumer
    for now). Never joined live against `mangaly_profile` — that is the
    entire point of this table existing.
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
    # written via a raw `to_tsvector(...)` expression in `interface.py`,
    # since SQLAlchemy has no native Python-side representation for it.
    ranking_input_snapshot: Mapped[dict | None] = mapped_column(JSONB, default=None)
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
