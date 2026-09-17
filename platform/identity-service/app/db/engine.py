"""Database engine for the Identity & Trust Service."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.sqlalchemy_url, pool_size=settings.db_pool_size, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def assert_non_owning_role(engine: AsyncEngine) -> None:
    """Refuse to serve when connected as the schema owner (MODULE-ARCHITECTURE-STANDARD §4)."""
    async with engine.connect() as conn:
        owned = await conn.scalar(
            text(
                "SELECT count(*) FROM pg_tables "
                "WHERE schemaname IN ('identity', 'registry', 'platform') AND tableowner = current_user"
            )
        )
    if owned:
        raise RuntimeError(
            "The runtime database role owns identity tables. Connect as the non-owning "
            "application role (identity_app)."
        )
