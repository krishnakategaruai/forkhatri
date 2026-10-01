"""asyncpg pool. The service connects only as the non-owning `counsel_app`
role. All domain authorization happens in the application layer (every
handler checks the acting member against the row it touches); the runtime
role simply cannot alter the schema."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from app.settings import get_settings

_pool: asyncpg.Pool | None = None


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def open_pool() -> asyncpg.Pool:
    global _pool
    s = get_settings()
    _pool = await asyncpg.create_pool(s.dsn, min_size=1, max_size=s.db_pool_max, init=_init_conn, server_settings={"search_path": "counsel,public"})
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
    _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("database pool not open")
    return _pool


@asynccontextmanager
async def tx() -> AsyncIterator[asyncpg.Connection]:
    async with pool().acquire() as conn:
        async with conn.transaction():
            yield conn


async def fetch(sql: str, *args):
    async with pool().acquire() as conn:
        return await conn.fetch(sql, *args)


async def fetchrow(sql: str, *args):
    async with pool().acquire() as conn:
        return await conn.fetchrow(sql, *args)


async def fetchval(sql: str, *args):
    async with pool().acquire() as conn:
        return await conn.fetchval(sql, *args)


async def execute(sql: str, *args):
    async with pool().acquire() as conn:
        return await conn.execute(sql, *args)


def rows(records) -> list[dict]:
    return [dict(r) for r in records]
