"""Async engine and session factory for the non-owning application role.

# [TR16, MODULE-ARCHITECTURE-STANDARD §4] The application connects as
# `milavn_app` and never as the table-owning role, because Postgres bypasses
# RLS for a table's owner.
# Approach: `Settings` carries no owner credential, and at process start the
# service asserts that `current_user` owns zero `milavn_*` tables — refusing to
# boot rather than silently serving every row of every table to every caller.
# Traces to: TR16, TR-CROSSCUT-03, architecture.md §3.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

_OWNED_TABLE_COUNT_SQL = text("SELECT count(*) FROM pg_tables WHERE tableowner = current_user AND schemaname LIKE 'milavn%'")


class NonOwningRoleViolation(RuntimeError):
    """Raised when the runtime role owns tables — RLS would be bypassed entirely."""


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    return create_async_engine(
        settings.sqlalchemy_url,
        pool_size=settings.db_pool_max_connections,
        max_overflow=0,
        pool_pre_ping=True,
        echo=settings.api_debug,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


_session_factory: async_sessionmaker[AsyncSession] | None = None


def set_process_session_factory(factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = factory


def get_process_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("session factory not initialised; app startup has not run")
    return _session_factory


async def assert_non_owning_role(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        owned = (await conn.execute(_OWNED_TABLE_COUNT_SQL)).scalar_one()
        current_user = (await conn.execute(text("SELECT current_user"))).scalar_one()
    if owned:
        raise NonOwningRoleViolation(
            f"Runtime role {current_user!r} owns {owned} milavn table(s); RLS would be a no-op. "
            "Connect as the non-owning application role (MODULE-ARCHITECTURE-STANDARD §4)."
        )
    logger.info("non-owning-role check passed: %s owns 0 milavn tables", current_user)
    return owned
