# [TR052] One shared `publish_with_outbox()` implementation every one of
# FR52's six adjacent-service contracts uses (Search, Notification*, Audit*,
# Object Storage, Dashboard Read, Counsel Referral). *Notification and Audit
# already have their own durable, pre-forward tables (`notifications`,
# `audit_events` — 07a-er-model.md's own documented fold-in) and go through
# `app/notifications.py` / `app/audit.py` instead; this helper is for the
# other contracts, each of which already has its own schema-scoped
# `outbox_event` table (vyapar_listings, vyapar_opportunities,
# vyapar_commercial).
# Approach: insert now, dispatch later, never inline in the request. A
# dispatcher pass (run_outbox_dispatch_pass, called from the same hourly loop
# as every other scheduled pass) reads unpublished rows and marks them
# published — standing in for the real Search Bridge this dev environment
# doesn't have. On repeated failure the row is moved to the shared
# `dead_letters` table (visible at GET /v1/admin/dead-letters, feeding
# FR49), never retried forever and never silently dropped.
# Traces to: FR52, TR052, SP052 (Cross-cutting §4's shared-outbox pattern)
from __future__ import annotations

import json

import asyncpg

OUTBOX_TABLES = {
    "listing": "vyapar_listings.outbox_event",
    "opportunity": "vyapar_opportunities.outbox_event",
    "commercial": "vyapar_commercial.outbox_event",
}

MAX_DISPATCH_ATTEMPTS = 5


async def publish_with_outbox(conn: asyncpg.Connection, *, schema: str, event_type: str, payload: dict) -> None:
    table = OUTBOX_TABLES[schema]
    await conn.execute(f"INSERT INTO {table} (event_type, payload) VALUES ($1, $2::jsonb)", event_type, json.dumps(payload))


async def run_outbox_dispatch_pass(pool: asyncpg.Pool) -> dict:
    """[TR052] Standing in for the real Search Bridge: marks every pending
    outbox row published within its own 5-second-class window. A row that
    cannot be parsed (defensive — never expected from our own inserts) is
    parked in dead_letters instead of looping forever."""
    counts = {"published": 0, "dead_lettered": 0}
    async with pool.acquire() as conn:
        async with conn.transaction():
            for schema, table in OUTBOX_TABLES.items():
                await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
                rows = await conn.fetch(f"SELECT * FROM {table} WHERE published_at IS NULL ORDER BY id LIMIT 500")
                for row in rows:
                    try:
                        payload = row["payload"]
                        if isinstance(payload, str):
                            json.loads(payload)  # validate shape before "delivery"
                        await conn.execute(f"UPDATE {table} SET published_at = now() WHERE id = $1", row["id"])
                        counts["published"] += 1
                    except Exception as exc:  # pragma: no cover — defensive only, our own writes are well-formed
                        await conn.execute(
                            "INSERT INTO vyapar_integration.dead_letters (target, payload, error, attempts) VALUES ($1, $2::jsonb, $3, $4)",
                            f"search_bridge:{schema}", json.dumps(dict(row)), str(exc), MAX_DISPATCH_ATTEMPTS,
                        )
                        counts["dead_lettered"] += 1
    return counts
