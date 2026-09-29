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
from pydantic import BaseModel

from app.config import get_settings
from app.db import get_pool
from app.i18n import translate
from app.identity import AuthzContext
from app.notifications import send_notification
from app.ranking import score
from app.services.feed import _distance_km, _opportunity_signals
from app.services.pagination import DEFAULT_LIMIT, Page, keyset_after, keyset_cursor

logger = logging.getLogger(__name__)


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


class UnreadCountOut(BaseModel):
    count: int


class ReadOut(BaseModel):
    read: bool


async def list_notifications(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
) -> list[NotificationOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_integration.notifications WHERE member_id = $1 ORDER BY created_at DESC LIMIT 50",
        ctx.member_id,
    )
    return [
        NotificationOut(id=str(r["id"]), kind=r["kind"], title=r["title"], body=r["body"], link=r["link"], read=r["read_at"] is not None, created_at=r["created_at"])
        for r in rows
    ]


async def list_notifications_page(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> Page[NotificationOut]:
    """[Refactor A] The full inbox, newest first, paged with a (created_at, id)
    keyset cursor — unlike the plain inbox route it does not stop at 50."""
    after_t, after_id = keyset_after(cursor, lang)
    rows = await conn.fetch(
        """SELECT * FROM vyapar_integration.notifications
           WHERE member_id = $1
             AND ($2::timestamptz IS NULL OR (created_at, id::text) < ($2::timestamptz, $3::text))
           ORDER BY created_at DESC, id::text DESC
           LIMIT $4""",
        ctx.member_id, after_t, after_id, limit + 1,
    )
    page, more = rows[:limit], len(rows) > limit
    return Page[NotificationOut](
        items=[
            NotificationOut(id=str(r["id"]), kind=r["kind"], title=r["title"], body=r["body"], link=r["link"], read=r["read_at"] is not None, created_at=r["created_at"])
            for r in page
        ],
        next_cursor=keyset_cursor(page[-1]["created_at"], page[-1]["id"]) if more else None,
    )


async def get_unread_notification_count(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
) -> UnreadCountOut:
    count = await conn.fetchval(
        "SELECT count(*) FROM vyapar_integration.notifications WHERE member_id = $1 AND read_at IS NULL", ctx.member_id
    )
    return UnreadCountOut(count=count)


async def mark_notification_read(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    notification_id: str,
) -> ReadOut:
    await conn.execute(
        "UPDATE vyapar_integration.notifications SET read_at = now() WHERE id = $1 AND member_id = $2 AND read_at IS NULL",
        notification_id, ctx.member_id,
    )
    return ReadOut(read=True)


async def mark_all_notifications_read(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
) -> ReadOut:
    await conn.execute(
        "UPDATE vyapar_integration.notifications SET read_at = now() WHERE member_id = $1 AND read_at IS NULL", ctx.member_id
    )
    return ReadOut(read=True)


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
                # [Coordinator bug #3 fix] never re-alert the same still-open
                # match within 7 days — the daily idempotency key alone only
                # guarantees no same-DAY duplicate, not "not effectively the
                # same notification again tomorrow".
                already_recent = await conn.fetchval(
                    """SELECT EXISTS (SELECT 1 FROM vyapar_integration.notifications
                         WHERE member_id = $1 AND template_id = 'strong_match'
                           AND params->>'opportunity_id' = $2 AND created_at > now() - interval '7 days')""",
                    member["id"], str(best_opp["id"]),
                )
                if already_recent:
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

            # [IMP-B/FR21] Saved searches with alert=true: new posts matching
            # the member's own saved filters, through the feed's query
            # builder, under the SAME per-member daily cap and mute rules —
            # never a second notification budget.
            sent += await _saved_search_alerts(conn, {m["id"]: m for m in members}, muted_by_member, settings)
    return sent


async def _saved_search_alerts(conn: asyncpg.Connection, members: dict[str, asyncpg.Record], muted_by_member: dict, settings) -> int:
    from app.services.feed import saved_search_matches
    from app.services.saved_searches import _row_to_out

    sent = 0
    searches = await conn.fetch(
        "SELECT * FROM vyapar_opportunities.saved_searches WHERE alert AND member_id = ANY($1::text[]) ORDER BY created_at",
        list(members),
    )
    for search in searches:
        member = members.get(search["member_id"])
        if member is None or "opportunity" in muted_by_member.get(member["id"], set()):
            continue
        saved = _row_to_out(search)
        since = search["last_alerted_at"] or search["created_at"]
        matches = await saved_search_matches(conn, member, saved.query, saved.filters, since)
        if not matches:
            continue
        allowed = await conn.fetchval(
            "SELECT vyapar_platform.check_and_increment($1, 86400, $2)",
            f"notify:{member['id']}:day", settings.rate_limit_notify_strong_match_per_day,
        )
        if not allowed:
            continue
        name = saved.name or saved.query or ", ".join(saved.filters.skills) or translate("discover.section.for_you", member["language"])
        idem_key = f"saved_search:{search['id']}:{date.today().isoformat()}"
        written = await send_notification(
            conn, member_id=member["id"], kind="opportunity_match", template_id="saved_search_match",
            title=translate("notifications.savedSearchMatch.title", member["language"], count=len(matches), name=name),
            body=translate("notifications.savedSearchMatch.body", member["language"]),
            link=f"/opportunities/{matches[0]['id']}",
            params={"saved_search_id": str(search["id"]), "opportunity_ids": [str(m["id"]) for m in matches]},
            idempotency_key=idem_key,
        )
        await conn.execute(
            "UPDATE vyapar_opportunities.saved_searches SET last_alerted_at = now(), updated_at = now() WHERE id = $1", search["id"]
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

