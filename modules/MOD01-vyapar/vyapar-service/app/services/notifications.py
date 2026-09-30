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
import hashlib
import json
from datetime import date, datetime, timedelta, timezone

import asyncpg
from pydantic import BaseModel

from app.config import get_settings
from app.db import get_pool
from app.i18n import translate
from app.identity import AuthzContext
from app.notifications import render_notification, send_notification
from app.viewer_profile import viewer_skills
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


def _out(r, lang: str) -> NotificationOut:
    title, body = render_notification(r, lang)
    return NotificationOut(id=str(r["id"]), kind=r["kind"], title=title, body=body, link=r["link"], read=r["read_at"] is not None, created_at=r["created_at"])


async def list_notifications(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str = "en",
) -> list[NotificationOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_integration.notifications WHERE member_id = $1 ORDER BY created_at DESC LIMIT 50",
        ctx.member_id,
    )
    return [_out(r, lang) for r in rows]


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
        items=[_out(r, lang) for r in page],
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


async def _notified_opportunity_ids(conn: asyncpg.Connection, member_id: str) -> set[str]:
    """[IMP-B, owner 2026-09-30] Every post a member has already been told
    about, by any kind (a match, a saved-search alert, a digest): the one
    dedupe set, so no post is ever announced to the same person twice."""
    rows = await conn.fetch(
        """SELECT params->>'opportunity_id' AS one, params->'opportunity_ids' AS many
             FROM vyapar_integration.notifications
            WHERE member_id = $1 AND kind IN ('opportunity_match', 'digest')""",
        member_id,
    )
    out: set[str] = set()
    for r in rows:
        if r["one"]:
            out.add(r["one"])
        many = r["many"]
        if isinstance(many, str):
            many = json.loads(many)
        out.update(str(x) for x in (many or []))
    return out


async def _viewer(conn: asyncpg.Connection, member: asyncpg.Record) -> dict:
    """The member row with skills from their profiles too (critique L14)."""
    caps, cats = await viewer_skills(conn, member["id"])
    return {**dict(member), "capabilities": caps, "categories": cats}


_LIVE_POST_SQL = """state = 'active' AND NOT distribution_limited AND type = ANY($1)
                    AND (deadline IS NULL OR deadline > now())"""


async def run_strong_match_pass(pool: asyncpg.Pool) -> int:
    """[TR021] One strong match per member per pass, under the daily cap.
    [IMP-B, owner 2026-09-30] Never the same post twice to the same member
    (permanent idempotency key + the notified set), never an expired post,
    never the member's own post, and the notification stores its template so
    it is read in the reader's language."""
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
            member_rows = await conn.fetch(
                """SELECT id, capabilities, help_with, locality, lat, lng, radius_km, language
                   FROM vyapar_identity.members WHERE id = ANY($1)""",
                enabled_ids,
            )
            members = [await _viewer(conn, m) for m in member_rows]
            opps = await conn.fetch(
                f"SELECT * FROM vyapar_opportunities.opportunities WHERE {_LIVE_POST_SQL}", list(_NOTIFIABLE_TYPES),
            )

            for member in members:
                if "opportunity" in muted_by_member.get(member["id"], set()):
                    continue
                notified = await _notified_opportunity_ids(conn, member["id"])
                best_score, best_opp = 0.0, None
                for opp in opps:
                    if opp["poster_id"] == member["id"] or str(opp["id"]) in notified:
                        continue
                    distance = await _distance_km(conn, member, opp)
                    s = score(_opportunity_signals(opp, member, distance))
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
                spec = {"title": "notifications.strongMatch.title", "body": "notifications.strongMatch.body",
                        "values": {"title": best_opp["title"]}}
                written = await send_notification(
                    conn, member_id=member["id"], kind="opportunity_match", template_id="strong_match",
                    title=translate(spec["title"], member["language"], title=best_opp["title"]),
                    body=translate(spec["body"], member["language"]),
                    link=f"/opportunities/{best_opp['id']}",
                    params={"opportunity_id": str(best_opp["id"])},
                    idempotency_key=f"match:{member['id']}:{best_opp['id']}",  # permanent: once per member and post
                    i18n=spec,
                )
                if written:
                    sent += 1

            # [IMP-B/FR21] Saved searches with alert=true, under the SAME
            # per-member daily cap and mute rules — never a second budget.
            sent += await _saved_search_alerts(conn, {m["id"]: m for m in members}, muted_by_member, settings)
    return sent


def _saved_search_link(filters) -> str:
    """Opens Discover with the saved search's own filters (the web reads them from the URL)."""
    from urllib.parse import urlencode

    data = filters.model_dump(exclude_none=True, exclude_defaults=True)
    query = {k: (",".join(v) if isinstance(v, list) else ("true" if v is True else v)) for k, v in data.items() if v not in ([], "", False)}
    return "/?" + urlencode(query) if query else "/"


async def _saved_search_alerts(conn: asyncpg.Connection, members: dict, muted_by_member: dict, settings) -> int:
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
        notified = await _notified_opportunity_ids(conn, member["id"])
        matches = [m for m in await saved_search_matches(conn, member, saved.query, saved.filters, since)
                   if str(m["id"]) not in notified and (m["deadline"] is None or m["deadline"] > datetime.now(timezone.utc))]
        if not matches:
            continue
        allowed = await conn.fetchval(
            "SELECT vyapar_platform.check_and_increment($1, 86400, $2)",
            f"notify:{member['id']}:day", settings.rate_limit_notify_strong_match_per_day,
        )
        if not allowed:
            continue
        name = saved.name or saved.query or ", ".join(saved.filters.skills)
        spec = {"title": "notifications.savedSearchMatch.title", "body": "notifications.savedSearchMatch.body",
                "values": {"count": len(matches), "name": name}}
        ids = sorted(str(m["id"]) for m in matches)
        written = await send_notification(
            conn, member_id=member["id"], kind="opportunity_match", template_id="saved_search_match",
            title=translate(spec["title"], member["language"], count=len(matches), name=name),
            body=translate(spec["body"], member["language"]),
            # one post -> that post; several -> the saved search itself, opened as a filtered Discover
            link=f"/opportunities/{ids[0]}" if len(ids) == 1 else _saved_search_link(saved.filters),
            params={"saved_search_id": str(search["id"]), "opportunity_ids": ids},
            idempotency_key=f"saved_search:{search['id']}:{hashlib.sha1(','.join(ids).encode()).hexdigest()[:16]}",
            i18n=spec,
        )
        await conn.execute(
            "UPDATE vyapar_opportunities.saved_searches SET last_alerted_at = now(), updated_at = now() WHERE id = $1", search["id"]
        )
        if written:
            sent += 1
    return sent


async def run_digest_pass(pool: asyncpg.Pool) -> int:
    """[TR021] Once a day at the member's own hour (IST). [IMP-B, owner
    2026-09-30] The digest counts only posts the member has NOT already been
    told about (no match, no alert, no earlier digest), that are live and not
    their own; it is skipped when there is nothing new, never sent twice
    within 20 hours, lists its posts in params, and opens Discover on "New
    today"."""
    settings = get_settings()
    sent = 0
    local_hour = datetime.now(timezone(timedelta(minutes=settings.contact_timezone_offset_minutes))).hour
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _set_dispatcher_context(conn)
            privacy_rows = await conn.fetch(
                "SELECT * FROM vyapar_privacy.notification_targets() WHERE digest_enabled AND digest_hour = $1", local_hour
            )
            digest_ids = [r["member_id"] for r in privacy_rows]
            if not digest_ids:
                return 0
            members = await conn.fetch("SELECT id, language FROM vyapar_identity.members WHERE id = ANY($1)", digest_ids)
            fresh = await conn.fetch(
                f"""SELECT id, poster_id FROM vyapar_opportunities.opportunities
                     WHERE {_LIVE_POST_SQL} AND published_at > now() - interval '1 day'""",
                list(_NOTIFIABLE_TYPES),
            )
            for member in members:
                recent = await conn.fetchval(
                    """SELECT EXISTS (SELECT 1 FROM vyapar_integration.notifications
                         WHERE member_id = $1 AND kind = 'digest' AND created_at > now() - interval '20 hours')""",
                    member["id"],
                )
                if recent:
                    continue
                notified = await _notified_opportunity_ids(conn, member["id"])
                items = sorted(str(r["id"]) for r in fresh if r["poster_id"] != member["id"] and str(r["id"]) not in notified)
                if not items:
                    continue
                spec = {"title": "notifications.digest.title", "body": "notifications.digest.body", "values": {"count": len(items)}}
                written = await send_notification(
                    conn, member_id=member["id"], kind="digest", template_id="digest",
                    title=translate(spec["title"], member["language"], count=len(items)),
                    body=translate(spec["body"], member["language"]),
                    link="/?posted_within=today&sort=freshness",
                    params={"count": len(items), "opportunity_ids": items},
                    idempotency_key=f"digest:{member['id']}:{date.today().isoformat()}", i18n=spec,
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

