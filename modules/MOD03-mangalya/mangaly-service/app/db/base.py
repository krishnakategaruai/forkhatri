"""SQLAlchemy declarative base shared by every component's `models.py`.

# [SCAFFOLD per 07a-db-implementation/README.md "ORM / migration-tool
# conventions for Step 9"] One typed declarative base; one model module per
# component package; no cross-schema ForeignKey.
# Approach: the README fixes SQLAlchemy 2.x async with the `Mapped[...]` /
# `mapped_column()` typed style, and explicitly forbids (a) Alembic owning
# schema evolution — `migrations/*.sql` stay authoritative — and (b) a
# SQLAlchemy `ForeignKey()` reaching across component schemas. This base
# therefore carries NO metadata-driven DDL story at all: `Base.metadata` exists
# for query construction and for tests to introspect, and `create_all` is never
# called anywhere in this service, so there is exactly one system that can
# create a table and it is the hand-written SQL migrations.
# Traces to: 07a-db-implementation/README.md, 07a-er-model.md Assumptions #3.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase

# Match the naming Postgres already generated for the applied migrations, so an
# introspection test comparing ORM metadata against the live database compares
# like with like rather than reporting spurious constraint-name differences.
NAMING_CONVENTION = {
    "ix": "idx_%(column_0_label)s",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    """Declarative base for every component's models.

    Deliberately has no `create_all` helper and is never passed to one — see the
    comment block above.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Every timestamp column in this database is `timestamptz` (schema.sql uses
    # `timestamp with time zone` throughout), so a bare `Mapped[datetime]` must
    # map to a timezone-AWARE type. Without this, SQLAlchemy's default maps it
    # to a naive `TIMESTAMP` and asyncpg then rejects the aware datetimes the
    # application produces with "can't subtract offset-naive and offset-aware
    # datetimes" — a confusing error that points at arithmetic rather than at
    # the column type. Fixing it once here rather than per column means a new
    # model cannot reintroduce it by forgetting `DateTime(timezone=True)`.
    type_annotation_map = {datetime: DateTime(timezone=True)}
