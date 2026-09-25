# [IMP37 — Refactor B] Outbound webhook dispatch.
#
# Two passes, run by webhook_loop() from main.py's lifespan every
# WEBHOOK_DISPATCH_INTERVAL_SECONDS:
#
#  1. Fan-out. Reads outbox rows newer than a per-source cursor (the outbox
#     tables in app/outbox.py — the same rows the Search Bridge pass marks
#     published; the cursor is independent of `published_at`, so neither pass
#     disturbs the other) and writes one delivery row per matching active
#     subscription: event type subscribed (or "*"), and either the
#     subscriber is in the event's `audience` or the subscription is an
#     operator's all-events subscription. Cursor rows are locked FOR UPDATE,
#     so two API processes never fan out the same event twice (and
#     UNIQUE(subscription_id, event_id) makes it idempotent regardless).
#
#  2. Delivery. Claims due deliveries with FOR UPDATE SKIP LOCKED and a
#     2-minute lease, commits, then POSTs each one outside any transaction.
#     2xx = delivered. Anything else is retried with backoff
#     (30s, 2m, 10m, 1h, 6h) up to WEBHOOK_MAX_ATTEMPTS, then marked failed.
#     Every attempt's status code/error is kept on the delivery row — that
#     row IS the delivery log members read. A subscription whose deliveries
#     keep failing is switched off after WEBHOOK_DISABLE_AFTER_FAILURES in a
#     row, so a dead endpoint does not collect retries forever.
#
# Requests never follow redirects, and (outside development) never go to a
# private/loopback/link-local address — checked at subscription time and
# again at delivery time against DNS rebinding.
from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import asyncpg

from app.config import get_settings
from app.integrations.webhooks import signing
from app.outbox import OUTBOX_TABLES

logger = logging.getLogger(__name__)

BACKOFF_SECONDS = (30, 120, 600, 3600, 21600)
FANOUT_BATCH = 500
DELIVERY_BATCH = 50
LEASE = "2 minutes"
USER_AGENT = "Vyapar-Webhooks/1.0"


# ---------------------------------------------------------------------------
# Target validation
# ---------------------------------------------------------------------------
def _is_private_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True  # unresolvable: treat as unsafe
    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast or addr.is_unspecified:
            return True
    return False


def target_problem(url: str) -> str | None:
    """Returns an error code, or None when the URL is an acceptable target."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return "invalid_webhook_url"
    if parsed.scheme not in ("http", "https") or not parsed.hostname or len(url) > 2000:
        return "invalid_webhook_url"
    if parsed.username or parsed.password:
        return "invalid_webhook_url"
    if get_settings().webhook_allow_private_targets:
        return None
    if parsed.scheme != "https":
        return "invalid_webhook_url"
    if _is_private_host(parsed.hostname):
        return "private_webhook_target"
    return None


# ---------------------------------------------------------------------------
# One HTTP attempt
# ---------------------------------------------------------------------------
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def envelope(event_id: str, event_type: str, data: dict, created_at: datetime | None = None) -> dict:
    return {
        "id": event_id,
        "type": event_type,
        "created_at": (created_at or datetime.now(timezone.utc)).isoformat(),
        "data": data,
    }


async def post_delivery(url: str, secret: str, delivery_id: int | str, body_obj: dict) -> tuple[bool, int | None, str | None]:
    """Returns (delivered, http_status, error)."""
    if target_problem(url) is not None:
        return False, None, "target_not_allowed"
    body = json.dumps(body_obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "X-Vyapar-Event": str(body_obj.get("type")),
        "X-Vyapar-Event-Id": str(body_obj.get("id")),
        "X-Vyapar-Delivery": str(delivery_id),
        "X-Vyapar-Signature": signing.sign(secret, body),
    }
    timeout = get_settings().webhook_timeout_seconds

    def _send() -> int:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with _opener.open(req, timeout=timeout) as resp:
                resp.read(1024)
                return resp.status
        except urllib.error.HTTPError as exc:
            return exc.code

    try:
        status = await asyncio.wait_for(asyncio.to_thread(_send), timeout=timeout + 1)
    except (urllib.error.URLError, asyncio.TimeoutError, TimeoutError, OSError, ValueError) as exc:
        return False, None, type(exc).__name__ + (f": {exc.reason}" if isinstance(exc, urllib.error.URLError) else "")
    return 200 <= status < 300, status, None if 200 <= status < 300 else f"HTTP {status}"


async def record_attempt(conn: asyncpg.Connection, delivery_id: int, subscription_id, attempts_before: int,
                         ok: bool, status: int | None, error: str | None) -> str:
    settings = get_settings()
    attempts = attempts_before + 1
    if ok:
        new_status = "delivered"
        await conn.execute(
            """UPDATE vyapar_integration.webhook_deliveries
                  SET status = 'delivered', attempts = $2, last_status_code = $3, last_error = NULL, delivered_at = now()
                WHERE id = $1""",
            delivery_id, attempts, status,
        )
        await conn.execute(
            "UPDATE vyapar_integration.webhook_subscriptions SET failure_streak = 0, updated_at = now() WHERE id = $1",
            subscription_id,
        )
        return new_status
    if attempts >= settings.webhook_max_attempts:
        new_status = "failed"
        await conn.execute(
            """UPDATE vyapar_integration.webhook_deliveries
                  SET status = 'failed', attempts = $2, last_status_code = $3, last_error = $4
                WHERE id = $1""",
            delivery_id, attempts, status, (error or "")[:500],
        )
    else:
        new_status = "pending"
        delay = BACKOFF_SECONDS[min(attempts - 1, len(BACKOFF_SECONDS) - 1)]
        await conn.execute(
            """UPDATE vyapar_integration.webhook_deliveries
                  SET attempts = $2, last_status_code = $3, last_error = $4,
                      next_attempt_at = now() + make_interval(secs => $5)
                WHERE id = $1""",
            delivery_id, attempts, status, (error or "")[:500], float(delay),
        )
    await conn.execute(
        """UPDATE vyapar_integration.webhook_subscriptions
              SET failure_streak = failure_streak + 1,
                  active = CASE WHEN failure_streak + 1 >= $2 THEN false ELSE active END,
                  updated_at = now()
            WHERE id = $1""",
        subscription_id, settings.webhook_disable_after_failures,
    )
    return new_status


# ---------------------------------------------------------------------------
# Passes
# ---------------------------------------------------------------------------
def _as_dict(value) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return dict(value or {})


async def run_webhook_fanout_pass(pool: asyncpg.Pool) -> int:
    created = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            cursors = {
                r["source"]: r["last_id"]
                for r in await conn.fetch("SELECT source, last_id FROM vyapar_integration.webhook_cursors FOR UPDATE")
            }
            subs = await conn.fetch(
                """SELECT id, member_id, event_types, all_events FROM vyapar_integration.webhook_subscriptions
                    WHERE active AND deleted_at IS NULL"""
            )
            for source, table in OUTBOX_TABLES.items():
                last_id = cursors.get(source)
                if last_id is None:
                    last_id = await conn.fetchval(f"SELECT coalesce(max(id), 0) FROM {table}")
                    await conn.execute(
                        "INSERT INTO vyapar_integration.webhook_cursors (source, last_id) VALUES ($1, $2) ON CONFLICT (source) DO NOTHING",
                        source, last_id,
                    )
                    continue
                rows = await conn.fetch(
                    f"SELECT id, event_type, payload, created_at FROM {table} WHERE id > $1 ORDER BY id LIMIT {FANOUT_BATCH}",
                    last_id,
                )
                if not rows:
                    continue
                for row in rows:
                    payload = _as_dict(row["payload"])
                    audience = set(payload.pop("audience", None) or [])
                    event_id = f"evt_{source}_{row['id']}"
                    body = envelope(event_id, row["event_type"], payload, row["created_at"])
                    for sub in subs:
                        types = set(sub["event_types"])
                        if "*" not in types and row["event_type"] not in types:
                            continue
                        if not (sub["all_events"] or sub["member_id"] in audience):
                            continue
                        result = await conn.execute(
                            """INSERT INTO vyapar_integration.webhook_deliveries
                                 (subscription_id, member_id, event_id, event_type, payload)
                               VALUES ($1, $2, $3, $4, $5::jsonb) ON CONFLICT (subscription_id, event_id) DO NOTHING""",
                            sub["id"], sub["member_id"], event_id, row["event_type"], json.dumps(body),
                        )
                        created += int(result.split()[-1])
                await conn.execute(
                    "UPDATE vyapar_integration.webhook_cursors SET last_id = $2, updated_at = now() WHERE source = $1",
                    source, rows[-1]["id"],
                )
    return created


async def run_webhook_delivery_pass(pool: asyncpg.Pool) -> dict:
    counts = {"delivered": 0, "retrying": 0, "failed": 0}
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            due = await conn.fetch(
                f"""UPDATE vyapar_integration.webhook_deliveries d
                       SET next_attempt_at = now() + interval '{LEASE}'
                      FROM vyapar_integration.webhook_subscriptions s
                     WHERE d.subscription_id = s.id
                       AND d.id IN (SELECT id FROM vyapar_integration.webhook_deliveries
                                     WHERE status = 'pending' AND next_attempt_at <= now()
                                     ORDER BY next_attempt_at LIMIT {DELIVERY_BATCH} FOR UPDATE SKIP LOCKED)
                 RETURNING d.id, d.subscription_id, d.attempts, d.payload, s.url, s.secret_enc, s.active, s.deleted_at"""
            )
    for d in due:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
                if not d["active"] or d["deleted_at"] is not None:
                    await conn.execute(
                        "UPDATE vyapar_integration.webhook_deliveries SET status = 'failed', last_error = 'subscription_inactive' WHERE id = $1",
                        d["id"],
                    )
                    counts["failed"] += 1
                    continue
        ok, status, error = await post_delivery(d["url"], signing.decrypt_secret(d["secret_enc"]), d["id"], _as_dict(d["payload"]))
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
                outcome = await record_attempt(conn, d["id"], d["subscription_id"], d["attempts"], ok, status, error)
        counts["delivered" if outcome == "delivered" else "failed" if outcome == "failed" else "retrying"] += 1
    return counts


async def purge_idempotency_keys(pool: asyncpg.Pool) -> int:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            return await conn.fetchval("SELECT vyapar_platform.purge_expired_idempotency_keys()")


async def webhook_loop() -> None:
    """Started from main.py's lifespan."""
    from app.db import get_pool

    last_purge = 0.0
    while True:
        await asyncio.sleep(get_settings().webhook_dispatch_interval_seconds)
        try:
            pool = get_pool()
            await run_webhook_fanout_pass(pool)
            await run_webhook_delivery_pass(pool)
            if time.time() - last_purge > 3600:
                await purge_idempotency_keys(pool)
                last_purge = time.time()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("webhook dispatch pass failed")
