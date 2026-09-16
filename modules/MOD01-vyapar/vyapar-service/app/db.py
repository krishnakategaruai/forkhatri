# [TR050 / MODULE-ARCHITECTURE-STANDARD §4] Every request that touches the
# database must run inside a transaction whose FIRST statement is
# `SET LOCAL vyapar.authz_context = '<resolved_member_id>'`, using the
# non-owning `vyapar_app` role (never `vyapar_owner` — RLS silently no-ops
# for a table's owning role, the exact failure mode §4 names). SET LOCAL
# (not plain SET) is load-bearing: a connection pool in transaction-mode
# pooling can hand the same physical connection to a different request's
# transaction, and a plain SET would leak one member's context onto another
# member's query.
# Approach: one asyncpg pool for the whole process; get_conn() is a FastAPI
# dependency that acquires a connection, opens a transaction, sets the RLS
# context from the already-resolved AuthzContext (never a raw client-
# supplied id — see identity.py), yields the connection to the route
# handler, and commits/rolls back on exit. Route handlers never see a
# connection without this context already set, so no handler can forget it.
# Traces to: TR050, SP001 (RLS-CC), SP050 (IdentityBridge-CC)
from __future__ import annotations

from collections.abc import AsyncIterator

import asyncpg
from fastapi import Depends

from app.config import get_settings
from app.identity import AuthzContext, resolve_authz_context

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=2,
            max_size=20,  # MODULE-ARCHITECTURE-STANDARD §4 pooling ceiling
        )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized — init_pool() must run at startup")
    return _pool


async def get_conn(
    ctx: AuthzContext = Depends(resolve_authz_context),
) -> AsyncIterator[asyncpg.Connection]:
    """Yields a connection inside a transaction with vyapar.authz_context set
    via SET LOCAL for the resolved member. Every router dependency should use
    this — never Depends(get_pool) directly for a member-scoped query."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "SELECT set_config('vyapar.authz_context', $1, true)",
                ctx.member_id,
            )
            yield conn


async def get_service_conn() -> AsyncIterator[asyncpg.Connection]:
    """For background/dispatcher use only (vyapar.service_role='dispatcher'),
    never for member-facing request handlers."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "SELECT set_config('vyapar.service_role', 'dispatcher', true)"
            )
            yield conn
