"""Every declared SQLAlchemy model must match the live, migration-created table.

`07a-db-implementation/README.md` makes `migrations/*.sql` authoritative and
forbids Alembic autogeneration from owning schema evolution. That leaves one
real risk: an ORM model drifting from the table it describes, with nothing to
catch it — the models are never used to create anything, so a wrong column name
only shows up as a runtime failure on whichever query happens to touch it.

This test closes that by reflecting the live database and comparing column sets
against `Base.metadata`. It is the ORM-side equivalent of the Class G
schema-introspection gate `08-security-performance.md` already requires for
structural-absence checks.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import inspect

# Importing a model module registers its tables on `Base.metadata`. Every model
# module must be imported here or its tables are not covered by this test.
import app.components.authorization.models  # noqa: F401
import app.db.platform_models  # noqa: F401
from app.db.base import Base
from app.db.engine import create_engine


@pytest_asyncio.fixture(scope="module")
async def engine():
    eng = create_engine()
    yield eng
    await eng.dispose()


@pytest.mark.parametrize(
    "qualified_name",
    sorted(f"{t.schema}.{t.name}" for t in Base.metadata.tables.values()),
)
async def test_Given_a_declared_model_When_compared_to_the_live_table_Then_columns_match(
    engine, qualified_name: str
):
    schema, name = qualified_name.split(".", 1)
    table = Base.metadata.tables[qualified_name]
    declared = {c.name for c in table.columns}

    async with engine.connect() as conn:

        def _reflect(sync_conn):
            return {c["name"] for c in inspect(sync_conn).get_columns(name, schema=schema)}

        live = await conn.run_sync(_reflect)

    assert declared == live, (
        f"{qualified_name} drifted: declared-only={sorted(declared - live)}, "
        f"live-only={sorted(live - declared)}"
    )
