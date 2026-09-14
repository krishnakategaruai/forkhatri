"""Async engine and session factory for the non-owning application role.

# [TR017/SP017] The application connects as `mangaly_app` and never as the
# table-owning role, because RLS silently no-ops for a table's owner.
# Approach: `Settings` deliberately exposes no owner credentials at all, so this
# module cannot construct an owner connection even by mistake. On top of that,
# an engine-level `connect` event asserts at runtime — on the first connection,
# in every environment — that `current_user` owns zero tables in this database.
# SP017's own threshold demands this be "an automated check in CI/CD deploy
# pipeline (not just a one-time manual query)"; running it at process start
# means a misconfigured deployment fails loudly at boot rather than silently
# serving every row of every table to every caller.
# Traces to: TR017, SP017, SP104, CODING-GUIDE.md §7.
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

_OWNED_TABLE_COUNT_SQL = text(
    """
    SELECT count(*)
    FROM pg_tables
    WHERE tableowner = current_user
      AND schemaname LIKE 'mangaly%'
    """
)


class NonOwningRoleViolation(RuntimeError):
    """Raised when the runtime role owns tables — RLS would be bypassed entirely."""


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    """Build the async engine for the non-owning application role."""
    settings = settings or get_settings()
    return create_async_engine(
        settings.sqlalchemy_url,
        pool_size=settings.db_pool_max_connections,
        max_overflow=0,
        pool_pre_ping=True,
        # asyncpg caches prepared statements per connection. That is safe here
        # only because every session variable is set via `set_config(..., true)`
        # (transaction-local) rather than a plain `SET` — see `app/db/session.py`.
        echo=settings.api_debug,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )


# A process-wide handle on the session factory, set once at startup.
#
# Almost everything should take its session from the request-scoped dependency
# instead of reaching for this. The one legitimate use is work that must
# SURVIVE the caller's rollback — see `rate_limiting.limiter.enforce_durable`,
# where counting a failed login inside the failing transaction means the count
# is rolled back with it.
_session_factory: async_sessionmaker[AsyncSession] | None = None


def set_process_session_factory(factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = factory


def get_process_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("session factory not initialised; app startup has not run")
    return _session_factory


async def assert_non_owning_role(engine: AsyncEngine) -> int:
    """[TR017/SP017] Fail startup if the runtime role owns any mangaly table.

    Returns the owned-table count (0 on success) so a caller/test can assert on
    the number rather than only on the absence of an exception.
    """
    async with engine.connect() as conn:
        owned = (await conn.execute(_OWNED_TABLE_COUNT_SQL)).scalar_one()
        current_user = (await conn.execute(text("SELECT current_user"))).scalar_one()

    if owned:
        raise NonOwningRoleViolation(
            f"Runtime role {current_user!r} owns {owned} mangaly table(s). "
            "Postgres bypasses row-level security for a table's owner, so every "
            "RLS policy in this module would be a no-op. Connect as the "
            "non-owning application role (TR017/SP017)."
        )

    logger.info("TR017 non-owning-role check passed: %s owns 0 mangaly tables", current_user)
    return owned
