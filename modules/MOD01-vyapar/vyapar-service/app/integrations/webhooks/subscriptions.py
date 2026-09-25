# [IMP37] Webhook subscription management — runs in the member's own
# request connection (vyapar.authz_context set), so RLS keeps every
# subscription and delivery visible only to its owner.
from __future__ import annotations

import json
import uuid

import asyncpg

from app.integrations.webhooks import signing
from app.integrations.webhooks.dispatcher import envelope, post_delivery, record_attempt


def _sub_out(row: asyncpg.Record) -> dict:
    return {
        "id": str(row["id"]),
        "url": row["url"],
        "description": row["description"],
        "event_types": list(row["event_types"]),
        "all_events": row["all_events"],
        "secret_prefix": row["secret_prefix"],
        "active": row["active"],
        "failure_streak": row["failure_streak"],
        "created_at": row["created_at"].isoformat(),
    }


def _delivery_out(row: asyncpg.Record) -> dict:
    return {
        "id": row["id"],
        "event_id": row["event_id"],
        "event_type": row["event_type"],
        "status": row["status"],
        "attempts": row["attempts"],
        "last_status_code": row["last_status_code"],
        "last_error": row["last_error"],
        "created_at": row["created_at"].isoformat(),
        "delivered_at": row["delivered_at"].isoformat() if row["delivered_at"] else None,
        "next_attempt_at": row["next_attempt_at"].isoformat() if row["status"] == "pending" else None,
    }


async def count_live(conn: asyncpg.Connection, member_id: str) -> int:
    return await conn.fetchval(
        "SELECT count(*) FROM vyapar_integration.webhook_subscriptions WHERE member_id = $1 AND deleted_at IS NULL",
        member_id,
    )


async def create(conn: asyncpg.Connection, *, member_id: str, url: str, event_types: list[str],
                 description: str | None, all_events: bool) -> dict:
    secret = signing.new_secret()
    row = await conn.fetchrow(
        """INSERT INTO vyapar_integration.webhook_subscriptions
             (member_id, url, description, event_types, all_events, secret_enc, secret_prefix)
           VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *""",
        member_id, url, description, sorted(set(event_types)), all_events, signing.encrypt_secret(secret), secret[:12],
    )
    return {**_sub_out(row), "secret": secret}


async def list_for(conn: asyncpg.Connection, member_id: str) -> list[dict]:
    rows = await conn.fetch(
        """SELECT * FROM vyapar_integration.webhook_subscriptions
            WHERE member_id = $1 AND deleted_at IS NULL ORDER BY created_at DESC""",
        member_id,
    )
    return [_sub_out(r) for r in rows]


async def get(conn: asyncpg.Connection, member_id: str, sub_id: str) -> asyncpg.Record | None:
    try:
        uuid.UUID(sub_id)
    except ValueError:
        return None
    return await conn.fetchrow(
        "SELECT * FROM vyapar_integration.webhook_subscriptions WHERE id = $1::uuid AND member_id = $2 AND deleted_at IS NULL",
        sub_id, member_id,
    )


async def delete(conn: asyncpg.Connection, member_id: str, sub_id: str) -> bool:
    if await get(conn, member_id, sub_id) is None:
        return False
    await conn.execute(
        """UPDATE vyapar_integration.webhook_subscriptions SET active = false, deleted_at = now(), updated_at = now()
            WHERE id = $1::uuid AND member_id = $2""",
        sub_id, member_id,
    )
    # Pending deliveries to a deleted subscription will never be sent.
    await conn.execute(
        """UPDATE vyapar_integration.webhook_deliveries SET status = 'failed', last_error = 'subscription_deleted'
            WHERE subscription_id = $1::uuid AND status = 'pending'""",
        sub_id,
    )
    return True


async def deliveries(conn: asyncpg.Connection, member_id: str, sub_id: str, limit: int) -> list[dict]:
    rows = await conn.fetch(
        """SELECT * FROM vyapar_integration.webhook_deliveries
            WHERE subscription_id = $1::uuid AND member_id = $2 ORDER BY id DESC LIMIT $3""",
        sub_id, member_id, limit,
    )
    return [_delivery_out(r) for r in rows]


async def send_test_ping(conn: asyncpg.Connection, member_id: str, sub: asyncpg.Record) -> dict:
    """Records a `ping` delivery and attempts it right away, so the member
    sees the real outcome (status code or error) in the response."""
    event_id = f"ping_{uuid.uuid4().hex}"
    body = envelope(event_id, "ping", {"subscription_id": str(sub["id"]), "member_id": member_id})
    delivery_id = await conn.fetchval(
        """INSERT INTO vyapar_integration.webhook_deliveries
             (subscription_id, member_id, event_id, event_type, payload, next_attempt_at)
           VALUES ($1, $2, $3, 'ping', $4::jsonb, now() + interval '1 hour') RETURNING id""",
        sub["id"], member_id, event_id, json.dumps(body),
    )
    ok, status, error = await post_delivery(sub["url"], signing.decrypt_secret(sub["secret_enc"]), delivery_id, body)
    # A test ping is a single attempt: record it, then close it out so the
    # background pass never retries a ping.
    await record_attempt(conn, delivery_id, sub["id"], 0, ok, status, error)
    if not ok:
        await conn.execute(
            "UPDATE vyapar_integration.webhook_deliveries SET status = 'failed' WHERE id = $1", delivery_id
        )
    row = await conn.fetchrow("SELECT * FROM vyapar_integration.webhook_deliveries WHERE id = $1", delivery_id)
    return _delivery_out(row)
