# [Trust pack, 2026-09-30 — VISION-2040 item 3] Every restriction has a
# reason and a human appeal path.
#
# Why: Fairwork India's deactivation findings — a worker whose account or
# post is held back must be told why and must be able to ask a person. The
# moderation appeal flow existed, but several code paths restricted content
# without a case (so nothing could be appealed): an operator suspending a
# listing, an operator removing a post from the review queue, and the interim
# holds (an auto-flag, or the seeker-charge report pause) that wait for a
# decision. Migration 028 records the first two as decided cases and lets the
# interim holds be appealed; this module is the member's one read of "what
# of mine is restricted, why, and how do I appeal".
#
# Restriction sources covered (each links to createAppeal via the case id):
#   decided moderation case (limit/remove/suspend/request_verification) — decide_moderation_case
#   operator suspend of a listing                                         — listings.suspend_listing
#   operator removal from the opportunity review queue                    — admin_ops.decide_opportunity_review
#   account suspension (tag account_suspended:<case>)                     — decide_moderation_case 'suspend'
#   seeker-charge report pause (2 independent reports)                    — trust_safety.apply_seeker_charge_reports
#   automated hold on a new listing (prohibited content / spam)           — listings.submit_listing
#   hidden review                                                         — decide_moderation_case 'limit' on a review
# Traces to: FR40, FR41, FR53, VISION-2040 item 3
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.i18n import translate
from app.identity import AuthzContext

APPEAL_LINK = "/moderation/outcomes"
Restriction = Literal["removed", "paused", "suspended", "limited", "held", "hidden"]


class RestrictionOut(BaseModel):
    object_kind: str
    object_id: str
    title: str | None
    restriction: Restriction
    restriction_label: str
    reason_code: str | None
    reason_label: str | None
    case_id: str | None = Field(description="The moderation case to appeal (createAppeal body.case_id)")
    under_review: bool = Field(description="True while a person has not decided yet (an interim hold)")
    can_appeal: bool
    appeal_state: str | None = Field(description="open | delayed | upheld | overturned, when already appealed")
    appeal_deadline: str | None
    appeal_link: str = APPEAL_LINK
    message: str = Field(description="One localized sentence: what happened and what the member can do")


def _reason_label(code: str | None, lang: str) -> str | None:
    if not code:
        return None
    if code.startswith("account_suspended:"):
        code = "account_suspended"
    key = f"trust_safety.reasonCode.{code}"
    text = translate(key, lang)
    return text if text != key else translate("trust_safety.reasonCode.policy_other", lang)


def _classify(kind: str, row: asyncpg.Record | dict) -> Restriction | None:
    state = row["state"]
    reason = row["state_reason"]
    limited = row["distribution_limited"]
    if kind == "opportunity":
        if state == "removed":
            return "removed"
        if state == "paused" and reason:  # a poster's own pause has no reason
            return "paused"
        if limited and state in ("active", "paused", "stale"):
            return "limited"
    elif kind == "listing":
        if state == "suspended":
            return "suspended"
        if state == "submitted" and reason:
            return "held"
        if limited and state in ("active_unverified", "active_verified"):
            return "limited"
    return None


def _case_for(cases: list[asyncpg.Record], object_id: str, reason: str | None) -> asyncpg.Record | None:
    if reason and reason.startswith("account_suspended:"):
        cid = reason.split(":", 1)[1]
        hit = next((c for c in cases if str(c["case_id"]) == cid), None)
        if hit is not None:
            return hit
    return next((c for c in cases if str(c["object_id"]) == object_id), None)


def _out(kind: str, object_id: str, title: str | None, restriction: Restriction, reason: str | None,
         case: asyncpg.Record | None, lang: str) -> RestrictionOut:
    now = datetime.now(timezone.utc)
    reason_code = reason or (case["reason_code"] or case["primary_reason"] if case is not None else None)
    under_review = case is not None and case["decided_at"] is None
    can_appeal = case is not None and case["appeal_state"] is None and now < case["appeal_deadline"]
    if can_appeal:
        msg_key = "trust_safety.restriction.message.underReview" if under_review else "trust_safety.restriction.message.canAppeal"
    elif case is not None and case["appeal_state"] in ("open", "delayed"):
        msg_key = "trust_safety.restriction.message.appealOpen"
    else:
        msg_key = "trust_safety.restriction.message.contact"
    from app.services.trust_safety import GRIEVANCE_CONTACT

    return RestrictionOut(
        object_kind=kind, object_id=object_id, title=title, restriction=restriction,
        restriction_label=translate(f"trust_safety.restriction.kind.{restriction}", lang),
        reason_code=reason_code.split(":", 1)[0] if reason_code else None, reason_label=_reason_label(reason_code, lang),
        case_id=str(case["case_id"]) if case is not None else None, under_review=under_review, can_appeal=can_appeal,
        appeal_state=case["appeal_state"] if case is not None else None,
        appeal_deadline=case["appeal_deadline"].isoformat() if case is not None else None,
        message=translate(msg_key, lang, contact=GRIEVANCE_CONTACT),
    )


async def _cases(conn: asyncpg.Connection) -> list[asyncpg.Record]:
    return list(await conn.fetch("SELECT * FROM vyapar_trust_safety.my_restriction_cases()"))


async def restriction_for_object(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, kind: str, row) -> dict | None:
    """For the OWNER's own read of a listing or post: the restriction and its
    appeal path, or None."""
    restriction = _classify(kind, row)
    if restriction is None:
        return None
    title = row["title"] if kind == "opportunity" else row["name"]
    reason = row["state_reason"]
    return _out(kind, str(row["id"]), title, restriction, reason, _case_for(await _cases(conn), str(row["id"]), reason), lang).model_dump()


async def list_my_restrictions(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> list[RestrictionOut]:
    cases = await _cases(conn)
    out: list[RestrictionOut] = []
    covered: set[str] = set()
    for r in await conn.fetch(
            """SELECT id, title, state, state_reason, distribution_limited FROM vyapar_opportunities.opportunities
                WHERE poster_id = $1 AND (state = 'removed' OR (state = 'paused' AND state_reason IS NOT NULL)
                                          OR (distribution_limited AND state IN ('active','paused','stale')))
                ORDER BY updated_at DESC""", ctx.member_id):
        kind = _classify("opportunity", r)
        if kind:
            out.append(_out("opportunity", str(r["id"]), r["title"], kind, r["state_reason"], _case_for(cases, str(r["id"]), r["state_reason"]), lang))
            covered.add(str(r["id"]))
    for r in await conn.fetch(
            """SELECT id, name, state, state_reason, distribution_limited FROM vyapar_listings.listings
                WHERE owner_id = $1 AND (state = 'suspended' OR (state = 'submitted' AND state_reason IS NOT NULL)
                                         OR (distribution_limited AND state IN ('active_unverified','active_verified')))
                  AND NOT (state = 'archived')
                ORDER BY updated_at DESC""", ctx.member_id):
        kind = _classify("listing", r)
        if kind:
            out.append(_out("listing", str(r["id"]), r["name"], kind, r["state_reason"], _case_for(cases, str(r["id"]), r["state_reason"]), lang))
            covered.add(str(r["id"]))
    # Decided cases on other things (a hidden review, a hidden thread) that
    # still hold something back.
    for c in cases:
        if str(c["object_id"]) in covered or not c["held"] or c["object_kind"] in ("listing", "opportunity"):
            continue
        out.append(_out(c["object_kind"], str(c["object_id"]), None, "hidden", c["reason_code"] or c["primary_reason"], c, lang))
    return out


async def enrich_opportunity_with_restriction(conn: asyncpg.Connection, ctx, lang: str, opportunity: dict) -> dict:
    """[Poster only] the restriction on their own post, with the appeal path."""
    if not opportunity.get("is_poster"):
        return {}
    row = await conn.fetchrow(
        "SELECT id, title, state, state_reason, distribution_limited FROM vyapar_opportunities.opportunities WHERE id = $1",
        opportunity["id"])
    return {"restriction": await restriction_for_object(conn, ctx, lang, "opportunity", row) if row is not None else None}


from app.services import hooks as _hooks  # noqa: E402

_hooks.register_opportunity_enricher(enrich_opportunity_with_restriction)
