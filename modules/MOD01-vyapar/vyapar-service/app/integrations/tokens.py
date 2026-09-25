# [IMP37 — Refactor B] Personal access tokens: minting, hashing, listing and
# revoking. A token is "vyp_" + 43 url-safe random characters (256 bits).
# Only sha256(token) is stored; the plaintext exists once, in the create
# response. The display prefix ("vyp_" + 8 chars) lets a member tell their
# tokens apart without it being usable. RLS (migration 015) keeps every row
# visible only to the member who owns it.
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg

TOKEN_PREFIX = "vyp_"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def looks_like_token(value: str) -> bool:
    return value.startswith(TOKEN_PREFIX) and 20 <= len(value) <= 100


def mint_token() -> tuple[str, str, str]:
    """Returns (plaintext, sha256 hex, display prefix)."""
    token = TOKEN_PREFIX + secrets.token_urlsafe(32)
    return token, hash_token(token), token[:12]


def _row_out(row: asyncpg.Record) -> dict:
    now = datetime.now(timezone.utc)
    if row["revoked_at"] is not None:
        status = "revoked"
    elif row["expires_at"] <= now:
        status = "expired"
    else:
        status = "active"
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "prefix": row["token_prefix"],
        "scopes": list(row["scopes"]),
        "status": status,
        "created_at": row["created_at"].isoformat(),
        "expires_at": row["expires_at"].isoformat(),
        "last_used_at": row["last_used_at"].isoformat() if row["last_used_at"] else None,
        "revoked_at": row["revoked_at"].isoformat() if row["revoked_at"] else None,
    }


async def count_active(conn: asyncpg.Connection, member_id: str) -> int:
    return await conn.fetchval(
        "SELECT count(*) FROM vyapar_integration.access_tokens WHERE member_id = $1 AND revoked_at IS NULL AND expires_at > now()",
        member_id,
    )


async def create_token(conn: asyncpg.Connection, *, member_id: str, name: str, scopes: list[str], days: int) -> dict:
    token, digest, prefix = mint_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    row = await conn.fetchrow(
        """INSERT INTO vyapar_integration.access_tokens (member_id, name, token_hash, token_prefix, scopes, expires_at)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING *""",
        member_id, name, digest, prefix, sorted(set(scopes)), expires_at,
    )
    return {**_row_out(row), "token": token}


async def list_tokens(conn: asyncpg.Connection, member_id: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_integration.access_tokens WHERE member_id = $1 ORDER BY created_at DESC", member_id
    )
    return [_row_out(r) for r in rows]


async def revoke_token(conn: asyncpg.Connection, member_id: str, token_id: str) -> dict | None:
    try:
        uuid.UUID(token_id)
    except ValueError:
        return None
    row = await conn.fetchrow(
        """UPDATE vyapar_integration.access_tokens SET revoked_at = coalesce(revoked_at, now())
           WHERE id = $1::uuid AND member_id = $2 RETURNING *""",
        token_id, member_id,
    )
    return _row_out(row) if row else None


async def lookup(conn: asyncpg.Connection, token: str) -> asyncpg.Record | None:
    return await conn.fetchrow("SELECT * FROM vyapar_integration.resolve_access_token($1)", hash_token(token))
