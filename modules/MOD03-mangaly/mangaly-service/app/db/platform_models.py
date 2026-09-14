"""Models for `mangaly_platform` — shared cross-cutting infrastructure.

# [TR102/TR037/SP102/SP037] The idempotency-key store and the rate-limit counter
# are infrastructure, not a business component's data, so they live in `db/`
# rather than under `components/`.
# Approach: `07a-db-implementation/README.md` is explicit that `mangaly_platform`
# is "not a business-logic component's schema (does not extend architecture.md's
# 12-schema business list)". Putting these models inside some component's
# package would make one component the apparent owner of a table three
# components' flows write to, which is exactly the ownership confusion the
# schema-per-component rule exists to prevent. `app/db/` is the shared
# infrastructure layer, so they belong here.
#
# These models exist for query construction and for the schema-conformance test
# to introspect. The hot paths in `app/idempotency/store.py` and
# `app/rate_limiting/limiter.py` deliberately use hand-written SQL instead,
# because both need Postgres-specific atomicity (`ON CONFLICT ... DO UPDATE
# ... RETURNING`) that the ORM would obscure, and both are on a Class H
# (P95 < 20 ms) budget.
# Traces to: TR037, TR102, SP037, SP102.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_SCHEMA = "mangaly_platform"


class IdempotencyKey(Base):
    """`mangaly_platform.idempotency_key` — account-scoped since migration 002."""

    __tablename__ = "idempotency_key"
    __table_args__ = (
        # [SP102] Account-scoped, NOT global. A client-generated key is unique
        # WITHIN one account; a global namespace returned one account's cached
        # response to another. Mirrors migration 002's constraint name exactly.
        UniqueConstraint(
            "account_id", "idempotency_key", "endpoint", name="idempotency_key_account_scope"
        ),
        {"schema": _SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    request_hash: Mapped[str] = mapped_column(String, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer)
    response_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RateLimitCounter(Base):
    """`mangaly_platform.rate_limit_counter` — one shared (key, window, limit) counter.

    Deliberately has no `account_id` column and no RLS policy: two of its three
    callers (login failure, OTP resend) key on a pre-authentication identifier,
    where no `mangaly.account_id` exists yet to enforce a policy against. SP102's
    caution records this as a deliberate difference from `idempotency_key`, not
    an oversight.
    """

    __tablename__ = "rate_limit_counter"
    __table_args__ = (
        UniqueConstraint("rate_limit_key", "window_start"),
        {"schema": _SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    rate_limit_key: Mapped[str] = mapped_column(String, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_max: Mapped[int] = mapped_column(Integer, nullable=False)
