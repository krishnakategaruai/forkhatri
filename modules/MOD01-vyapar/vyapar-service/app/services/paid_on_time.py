# [Trust pack, 2026-09-30 — VISION-2040 item 2] "Paid on time", confirmed by
# the person who was paid.
#
# Why: unpredictable pay is the central complaint of gig and daily-wage
# workers (Fairwork India: 2 of 11 platforms earned the first Fair Pay point).
# A poster's own claim proves nothing; the payee's answer does.
#
# How:
#   * The hourly trust pass (and a dev trigger) finds who should be asked:
#     every released contract stage, and every hire older than
#     PAID_ON_TIME_ASK_AFTER_HIRE_DAYS (30) whose thread has no contract (the
#     contract's stages ask instead). vyapar_reviews.paid_on_time_due() reads
#     across members; each question is then written in its own transaction AS
#     THE PAYEE (RLS: only the payee reads or answers it) with one in-app
#     notification in their language.
#   * One question, Yes or No: `answerPaidOnTime`. Once answered it is final.
#   * The payer's profile, opportunity detail and member endpoint show the
#     count ("Paid on time: 12 of 13") only after PAID_ON_TIME_MIN_ANSWERS (3)
#     answers, so one person's answer can never be singled out. Who answered
#     what is never shown to the payer. No stars, no score.
# Traces to: FR27, FR28 (counts, never a score), VISION-2040 item 2
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
from app.notifications import notify_member

logger = logging.getLogger(__name__)


class PaidOnTimeSummary(BaseModel):
    member_id: str
    answered: int
    paid_on_time: int
    shown: bool = Field(description="False until at least the minimum number of paid people answered; then the label is shown")
    label: str | None = Field(description='"Paid on time: 12 of 13" in the reader\'s language, or null while hidden')
    min_answers: int


class PaidOnTimeAskOut(BaseModel):
    id: str
    source_kind: Literal["milestone", "hire"]
    title: str | None
    payer_id: str
    payer_name: str | None
    question: str = Field(description='"Were you paid on time for …?" in the reader\'s language')
    asked_at: str
    answered: bool
    answer: bool | None
    answered_at: str | None
    link: str | None = Field(description="The contract or thread this question is about")


class AnswerIn(BaseModel):
    paid_on_time: bool


class PassOut(BaseModel):
    asked: int


def _label(yes: int, answered: int, lang: str) -> str:
    return translate("reputation.paidOnTime.label", lang, yes=yes, total=answered)


async def summaries_for_members(conn: asyncpg.Connection, member_ids: list[str], lang: str) -> dict[str, PaidOnTimeSummary]:
    ids = [m for m in set(member_ids) if m]
    if not ids:
        return {}
    minimum = get_settings().paid_on_time_min_answers
    rows = {r["member_id"]: r for r in await conn.fetch("SELECT * FROM vyapar_reviews.paid_on_time_counts($1::text[])", ids)}
    out = {}
    for m in ids:
        r = rows.get(m)
        answered, yes = (r["answered"], r["paid_on_time"]) if r else (0, 0)
        shown = answered >= minimum
        out[m] = PaidOnTimeSummary(member_id=m, answered=answered if shown else 0, paid_on_time=yes if shown else 0,
                                   shown=shown, label=_label(yes, answered, lang) if shown else None, min_answers=minimum)
    return out


async def summary_for_member(conn: asyncpg.Connection, member_id: str, lang: str) -> dict | None:
    """The object put on a profile / opportunity: null while hidden."""
    s = (await summaries_for_members(conn, [member_id], lang)).get(member_id)
    return s.model_dump() if s and s.shown else None


async def get_member_summary(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, member_id: str) -> PaidOnTimeSummary:
    return (await summaries_for_members(conn, [member_id], lang))[member_id]


def _ask_out(r: asyncpg.Record, names: dict[str, str], lang: str) -> PaidOnTimeAskOut:
    title = r["title"] or ""
    link = f"/contracts/{r['contract_id']}" if r["contract_id"] else (f"/enquiries/{r['source_id']}" if r["source_kind"] == "hire" else None)
    return PaidOnTimeAskOut(
        id=str(r["id"]), source_kind=r["source_kind"], title=r["title"], payer_id=r["payer_id"], payer_name=names.get(r["payer_id"]),
        question=translate("reputation.paidOnTime.question", lang, title=title),
        asked_at=r["asked_at"].isoformat(), answered=r["answer"] is not None, answer=r["answer"],
        answered_at=r["answered_at"].isoformat() if r["answered_at"] else None, link=link,
    )


async def _names(conn: asyncpg.Connection, ids: list[str]) -> dict[str, str]:
    if not ids:
        return {}
    return {n["id"]: n["display_name"] for n in await conn.fetch(
        "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", list(set(ids)))}


async def list_my_asks(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, state: Literal["open", "all"] = "open") -> list[PaidOnTimeAskOut]:
    rows = await conn.fetch(
        """SELECT * FROM vyapar_reviews.paid_on_time_asks WHERE payee_id = $1 AND ($2 = 'all' OR answer IS NULL)
            ORDER BY asked_at DESC LIMIT 100""", ctx.member_id, state)
    names = await _names(conn, [r["payer_id"] for r in rows])
    return [_ask_out(r, names, lang) for r in rows]


async def answer(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, ask_id: str, body: AnswerIn) -> PaidOnTimeAskOut:
    try:
        row = await conn.fetchrow(
            "SELECT * FROM vyapar_reviews.paid_on_time_asks WHERE id = $1 AND payee_id = $2 FOR UPDATE", ask_id, ctx.member_id)
    except asyncpg.DataError:
        row = None
    if row is None:  # also the payer, or anyone else: the question is not theirs
        raise ApiError(404, "reputation.paidOnTime.error.notFound", lang, error_code="paid_on_time_ask_not_found")
    if row["answer"] is not None:
        raise ApiError(409, "reputation.paidOnTime.error.alreadyAnswered", lang, error_code="paid_on_time_already_answered")
    row = await conn.fetchrow(
        "UPDATE vyapar_reviews.paid_on_time_asks SET answer = $2, answered_at = now() WHERE id = $1 RETURNING *",
        row["id"], body.paid_on_time)
    return _ask_out(row, await _names(conn, [row["payer_id"]]), lang)


async def run_paid_on_time_pass(pool: asyncpg.Pool) -> dict:
    """Opens the question for everyone due. Idempotent: UNIQUE(source) and the
    notification key make a re-run a no-op."""
    settings = get_settings()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            due = await conn.fetch("SELECT * FROM vyapar_reviews.paid_on_time_due($1, 200)", settings.paid_on_time_ask_after_hire_days)
    asked = 0
    for d in due:
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", d["payee_id"])
                    row = await conn.fetchrow(
                        """INSERT INTO vyapar_reviews.paid_on_time_asks
                             (source_kind, source_id, payer_id, payee_id, title, opportunity_id, contract_id)
                           VALUES ($1, $2, $3, $4, $5, $6, $7)
                           ON CONFLICT (source_kind, source_id) DO NOTHING RETURNING id""",
                        d["source_kind"], d["source_id"], d["payer_id"], d["payee_id"], d["title"], d["opportunity_id"], d["contract_id"])
                    if row is None:
                        continue
                    await notify_member(
                        conn, member_id=d["payee_id"], template="paidOnTimeAsk", link=f"/paid-on-time/{row['id']}",
                        idempotency_key=f"paid_on_time_ask:{row['id']}", params={"title": d["title"] or ""},
                    )
                    asked += 1
        except Exception:  # one bad row never stops the pass
            logger.exception("paid-on-time ask failed for %s %s", d["source_kind"], d["source_id"])
    return {"asked": asked}


async def enrich_opportunity_with_paid_on_time(conn: asyncpg.Connection, ctx, lang: str, opportunity: dict) -> dict:
    poster = opportunity.get("poster_id")
    return {"poster_paid_on_time": await summary_for_member(conn, poster, lang)} if poster else {}


from app.services import hooks as _hooks  # noqa: E402

_hooks.register_opportunity_enricher(enrich_opportunity_with_paid_on_time)
