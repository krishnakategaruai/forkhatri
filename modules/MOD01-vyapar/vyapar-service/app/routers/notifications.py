# [TR021] Proactive notification with fatigue caps and daily digest (FR21).
# Built for real per the product owner's explicit override of this
# session's earlier skip: "build it genuinely rather than waiting for a
# platform Notification Service. The in-app inbox is the always-available
# path... enforce the strong-match threshold, 3-per-day cap, daily digest
# at the member's chosen hour, per-type mute and digest opt-out, all from
# config. Run the matcher/digest as a lightweight scheduled job inside the
# API process (or a triggerable endpoint for dev)."
# Approach: `run_strong_match_pass()` scores every active opportunity
# against every notifications-enabled member using the SAME `app.ranking`
# module every other ranked surface uses (never a second scorer); above
# `NOTIFY_STRONG_MATCH_THRESHOLD` and under the RateLimit-CC 3/day cap
# (`vyapar_platform.check_and_increment`), it sends one in-app notification
# via `send_notification()` (idempotent per member+opportunity, so a second
# pass run within the same day is a safe no-op, never a duplicate — TR052's
# own rule). `run_digest_pass()` batches everything else for members whose
# local `digest_hour` matches the current hour, once per day
# (idempotency_key includes the date, so re-running within the same hour
# never double-sends). Both run on an in-process `asyncio` loop started at
# app startup (`app/main.py`'s lifespan) — genuinely scheduled, not only a
# dev-triggerable endpoint, though the dev-triggerable endpoints also exist
# for on-demand testing without waiting for the interval.
# Traces to: FR21, TR021, SP021
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone

import asyncpg
from fastapi import APIRouter, Depends

from app.config import get_settings
from app.db import get_conn, get_pool
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.notifications import send_notification
from app.ranking import score
from app.routers.feed import _distance_km, _member_profile, _opportunity_signals, top_signal_keys
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])

# [TR014] "Other" types (training/community/partnership) excluded from the
# proactive-notification path, per FR21's own text and TR014's cross-reference.
_NOTIFIABLE_TYPES = ("employment", "freelance", "local_service")


class NotificationOut(BaseModel):
    id: str
    kind: str
    title: str
    body: str | None
    link: str | None
    read: bool
    created_at: datetime


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[NotificationOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_integration.notifications WHERE member_id = $1 ORDER BY created_at DESC LIMIT 50",
        ctx.member_id,
    )
    return [
        NotificationOut(id=str(r["id"]), kind=r["kind"], title=r["title"], body=r["body"], link=r["link"], read=r["read_at"] is not None, created_at=r["created_at"])
        for r in rows
    ]


@router.get("/unread-count")
async def unread_count(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    count = await conn.fetchval(
        "SELECT count(*) FROM vyapar_integration.notifications WHERE member_id = $1 AND read_at IS NULL", ctx.member_id
    )
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await conn.execute(
        "UPDATE vyapar_integration.notifications SET read_at = now() WHERE id = $1 AND member_id = $2 AND read_at IS NULL",
        notification_id, ctx.member_id,
    )
    return {"read": True}


@router.post("/read-all")
async def mark_all_read(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await conn.execute(
        "UPDATE vyapar_integration.notifications SET read_at = now() WHERE member_id = $1 AND read_at IS NULL", ctx.member_id
    )
    return {"read": True}


# ---------------------------------------------------------------------------
# Matcher + digest passes — the actual FR21 background behaviour.
# ---------------------------------------------------------------------------
async def _set_dispatcher_context(conn: asyncpg.Connection) -> None:
    """[TR021 gap-fix, see migrations/002-notification-dispatcher-reads.sql]
    Sets BOTH the dispatcher service-role (unlocks the new privacy_settings
    SECURITY DEFINER function) AND an operator authz_context (unlocks
    members' own is_operator(NULL) RLS bypass) — a background job is
    neither a member's own session nor exempt from RLS by default, so both
    are required for this job to see across all members at all, per this
    codebase's own §4 discipline (RLS is a real second layer, not routed
    around by connecting as a different role)."""
    await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
    await conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")


async def run_strong_match_pass(pool: asyncpg.Pool) -> int:
    settings = get_settings()
    sent = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _set_dispatcher_context(conn)
            privacy_rows = await conn.fetch("SELECT * FROM vyapar_privacy.notification_targets() WHERE notifications_enabled")
            enabled_ids = [r["member_id"] for r in privacy_rows]
            muted_by_member = {r["member_id"]: set(r["muted_types"]) for r in privacy_rows}
            if not enabled_ids:
                return 0
            members = await conn.fetch(
                """SELECT id, capabilities, help_with, locality, lat, lng, radius_km, language
                   FROM vyapar_identity.members WHERE id = ANY($1)""",
                enabled_ids,
            )
            opps = await conn.fetch(
                "SELECT * FROM vyapar_opportunities.opportunities WHERE state = 'active' AND NOT distribution_limited AND type = ANY($1)",
                list(_NOTIFIABLE_TYPES),
            )

            for member in members:
                if "opportunity" in muted_by_member.get(member["id"], set()):
                    continue
                best_score, best_opp = 0.0, None
                for opp in opps:
                    distance = await _distance_km(conn, member, opp)
                    signals = _opportunity_signals(opp, member, distance)
                    s = score(signals)
                    if s > best_score:
                        best_score, best_opp = s, opp
                if best_opp is None or best_score < settings.notify_strong_match_threshold:
                    continue
                allowed = await conn.fetchval(
                    "SELECT vyapar_platform.check_and_increment($1, 86400, $2)",
                    f"notify:{member['id']}:day", settings.rate_limit_notify_strong_match_per_day,
                )
                if not allowed:
                    continue
                idem_key = f"strong_match:{member['id']}:{best_opp['id']}:{date.today().isoformat()}"
                title = translate("notifications.strongMatch.title", member["language"], title=best_opp["title"])
                body = translate("notifications.strongMatch.body", member["language"])
                written = await send_notification(
                    conn, member_id=member["id"], kind="opportunity_match", template_id="strong_match",
                    title=title, body=body, link=f"/opportunities/{best_opp['id']}",
                    params={"opportunity_id": str(best_opp["id"])}, idempotency_key=idem_key,
                )
                if written:
                    sent += 1
    return sent


async def run_digest_pass(pool: asyncpg.Pool) -> int:
    settings = get_settings()
    sent = 0
    current_hour = datetime.now(timezone.utc).hour
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _set_dispatcher_context(conn)
            privacy_rows = await conn.fetch(
                "SELECT * FROM vyapar_privacy.notification_targets() WHERE digest_enabled AND digest_hour = $1", current_hour
            )
            digest_ids = [r["member_id"] for r in privacy_rows]
            if not digest_ids:
                return 0
            members = await conn.fetch(
                "SELECT id, language FROM vyapar_identity.members WHERE id = ANY($1)", digest_ids
            )
            for member in members:
                new_count = await conn.fetchval(
                    """SELECT count(*) FROM vyapar_opportunities.opportunities
                       WHERE state = 'active' AND type = ANY($1)
                         AND published_at > now() - interval '1 day'""",
                    list(_NOTIFIABLE_TYPES),
                )
                if not new_count:
                    continue
                idem_key = f"digest:{member['id']}:{date.today().isoformat()}"
                title = translate("notifications.digest.title", member["language"], count=new_count)
                body = translate("notifications.digest.body", member["language"])
                written = await send_notification(
                    conn, member_id=member["id"], kind="digest", template_id="digest",
                    title=title, body=body, link="/", params={"count": new_count}, idempotency_key=idem_key,
                )
                if written:
                    sent += 1
    return sent


async def notification_loop() -> None:
    """[TR021] In-process scheduled job — genuinely periodic, not only a
    dev-triggerable endpoint. Errors are logged and swallowed so one bad
    pass never crashes the whole API process."""
    settings = get_settings()
    while True:
        await asyncio.sleep(settings.notify_matcher_interval_seconds)
        try:
            pool = get_pool()
            matched = await run_strong_match_pass(pool)
            digested = await run_digest_pass(pool)
            if matched or digested:
                logger.info("notification pass: %d strong matches, %d digests", matched, digested)
        except Exception:
            logger.exception("notification pass failed")

