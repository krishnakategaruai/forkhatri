# [Trust pack, 2026-09-30 — VISION-2040 item 3] Close the loop: every
# applicant reaches a final answer.
#
# Why: silence after applying is what drives people away (Apna's poster
# nudges raised leads by 23%). Before this, a post that closed, expired or
# filled left its remaining applicants on "New" or "Shortlisted" for ever.
#
# What happens now:
#   * When a post CLOSES (poster), EXPIRES (hourly pass, as the poster) or
#     FILLS (hires reach `openings`, which also closes it with state_reason
#     `filled`), every applicant still `new` or `shortlisted` whose thread is
#     not in progress becomes `declined`; an open thread is closed with
#     state_reason `post_closed`. Each gets ONE polite notification in their
#     own language that says the post closed — never that they were rejected
#     — and points them back to Discover. The existing applicant.declined
#     domain event fires as for any decline.
#   * A declined-because-closed applicant may apply again if the post is
#     renewed (enquiries.create_enquiry ignores state_reason `post_closed`).
#   * Before closing, the poster sees "N applicants are still waiting"
#     (`getOpportunityCloseCheck`, and `applicants_waiting` on their detail
#     read), and the hourly pass nudges a poster whose applicants have waited
#     APPLICANTS_WAITING_NUDGE_DAYS (7) days without an answer, once a week.
#   * A thread already `in_progress` (the poster accepted it) is left alone:
#     they are talking, and the poster decides.
# Traces to: FR13, FR22, FR23, VISION-2040 item 3
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.config import get_settings
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext

logger = logging.getLogger(__name__)
Cause = Literal["closed", "expired", "filled"]
WAITING_STAGES = ("new", "shortlisted")
_WAITING_SQL = """
    SELECT e.id, e.sender_id, e.stage, e.state, e.created_at FROM vyapar_enquiries.enquiries e
     WHERE e.opportunity_id = $1 AND e.provider_id = $2 AND e.delivered
       AND e.stage = ANY($3::text[]) AND e.state NOT IN ('in_progress', 'withdrawn')
"""


class WaitingOut(BaseModel):
    waiting: int = Field(description="Applicants still new or shortlisted who have no answer yet")
    new: int
    shortlisted: int
    oldest_waiting_days: int | None
    message: str | None = Field(description='"3 applicants are still waiting for an answer." or null when none')


class CloseCheckOut(WaitingOut):
    close_message: str = Field(description="What closing will do for them, in the poster's language")


async def _waiting_rows(conn: asyncpg.Connection, opportunity_id, poster_id: str) -> list[asyncpg.Record]:
    return list(await conn.fetch(_WAITING_SQL, opportunity_id, poster_id, list(WAITING_STAGES)))


def _waiting_out(rows: list[asyncpg.Record], lang: str) -> WaitingOut:
    now = datetime.now(timezone.utc)
    n = len(rows)
    oldest = max(((now - r["created_at"]).days for r in rows), default=None)
    message = None
    if n:
        message = translate("opportunities.closeLoop.waiting.one" if n == 1 else "opportunities.closeLoop.waiting.many", lang, count=n)
    return WaitingOut(waiting=n, new=sum(1 for r in rows if r["stage"] == "new"),
                      shortlisted=sum(1 for r in rows if r["stage"] == "shortlisted"),
                      oldest_waiting_days=oldest, message=message)


async def get_close_check(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, opportunity_id: str) -> CloseCheckOut:
    try:
        opp = await conn.fetchrow("SELECT id, poster_id FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    except asyncpg.DataError:
        opp = None
    if opp is None or opp["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    base = _waiting_out(await _waiting_rows(conn, opp["id"], ctx.member_id), lang)
    close_key = "opportunities.closeLoop.closeMessage.some" if base.waiting else "opportunities.closeLoop.closeMessage.none"
    return CloseCheckOut(**base.model_dump(), close_message=translate(close_key, lang, count=base.waiting))


async def close_waiting_applicants(conn: asyncpg.Connection, opp, cause: Cause) -> int:
    """Runs in the POSTER's context (their close, or the expiry pass acting
    as them). Returns how many applicants were given their final answer."""
    from app.notifications import notify_interaction_party

    rows = await _waiting_rows(conn, opp["id"], opp["poster_id"])
    template = "applicantPostFilled" if cause == "filled" else "applicantPostClosed"
    for r in rows:
        if r["state"] in ("open", "awaiting_response"):
            await conn.execute(
                """UPDATE vyapar_enquiries.enquiries SET state = 'closed', state_reason = 'post_closed',
                     last_activity_at = now(), updated_at = now() WHERE id = $1""", r["id"])
        else:
            await conn.execute(
                "UPDATE vyapar_enquiries.enquiries SET state_reason = coalesce(state_reason, 'post_closed'), updated_at = now() WHERE id = $1",
                r["id"])
        await conn.execute(
            "UPDATE vyapar_enquiries.enquiries SET stage = 'declined', stage_changed_at = now(), updated_at = now() WHERE id = $1", r["id"])
        await notify_interaction_party(
            conn, interaction_kind="enquiry", interaction_id=r["id"], recipient=r["sender_id"], template=template,
            link=f"/enquiries/{r['id']}", idempotency_key=f"applicant_post_closed:{r['id']}", params={"title": opp["title"]},
        )
    return len(rows)


async def maybe_close_filled(conn: asyncpg.Connection, opportunity_id) -> bool:
    """After a hire: when the hires reach the post's `openings`, the post is
    closed as filled and everyone still waiting is told."""
    opp = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if opp is None or not opp["openings"] or opp["state"] not in ("active", "paused", "stale"):
        return False
    hired = await conn.fetchval(
        "SELECT count(*) FROM vyapar_enquiries.enquiries WHERE opportunity_id = $1 AND provider_id = $2 AND stage = 'hired'",
        opp["id"], opp["poster_id"])
    if hired < opp["openings"]:
        return False
    await conn.execute(
        "UPDATE vyapar_opportunities.opportunities SET state = 'closed', state_reason = 'filled', updated_at = now() WHERE id = $1", opp["id"])
    await close_waiting_applicants(conn, opp, "filled")
    return True


async def enrich_opportunity_with_waiting(conn: asyncpg.Connection, ctx, lang: str, opportunity: dict) -> dict:
    if not opportunity.get("is_poster") or opportunity.get("state") not in ("active", "paused", "stale"):
        return {}
    rows = await _waiting_rows(conn, opportunity["id"], ctx.member_id)
    return {"applicants_waiting": _waiting_out(rows, lang).model_dump() if rows else None}


async def run_waiting_nudge_pass(pool: asyncpg.Pool) -> dict:
    """Once a week per post: "N applicants are still waiting on <title>"."""
    from app.notifications import notify_member

    days = get_settings().applicants_waiting_nudge_days
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", get_settings().dispatcher_operator_member_id)
            due = await conn.fetch(
                """SELECT o.id, o.poster_id, o.title, count(*) AS waiting
                     FROM vyapar_opportunities.opportunities o
                     JOIN vyapar_enquiries.enquiries e ON e.opportunity_id = o.id AND e.provider_id = o.poster_id
                    WHERE o.state IN ('active','paused','stale') AND e.delivered AND e.stage = ANY($1::text[])
                      AND e.state IN ('open','awaiting_response') AND e.created_at < now() - make_interval(days => $2)
                    GROUP BY o.id, o.poster_id, o.title LIMIT 500""", list(WAITING_STAGES), days)
    week = datetime.now(timezone.utc).strftime("%G-W%V")
    nudged = 0
    for d in due:
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", d["poster_id"])
                    if await notify_member(
                        conn, member_id=d["poster_id"], template="applicantsWaiting", link=f"/opportunities/{d['id']}/applicants",
                        idempotency_key=f"applicants_waiting:{d['id']}:{week}", params={"title": d["title"], "count": str(d["waiting"])},
                    ):
                        nudged += 1
        except Exception:
            logger.exception("applicants-waiting nudge failed for %s", d["id"])
    return {"nudged": nudged}


from app.services import hooks as _hooks  # noqa: E402

_hooks.register_opportunity_enricher(enrich_opportunity_with_waiting)
