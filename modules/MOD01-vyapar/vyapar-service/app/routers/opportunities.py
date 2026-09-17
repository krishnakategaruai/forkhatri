# [TR011] Opportunity Composer: create, share, or upload (FR11). One
# canonical Opportunity concept shared by every type (FR14) — Employment,
# Freelance/Project, Local Service promoted in V1; Partnership/Training/
# Community under "Other" (TR014). Entry modes create/share/upload never
# duplicate the schema, only how it's first populated.
# Approach: `poster_id` resolved server-side from AuthzContext, never client
# input (same pattern as listings.py's owner_id). `source_segment` is
# mandatory; `public` requires `source_name` or `source_url` (FR11's own
# edge case). Rule-based (not AI) field extraction for share/upload modes:
# a pasted URL/text is scanned for a title-like first line and any known
# capability keyword; an upload just requires manual entry since no OCR
# exists in V1 — both cases mark every inferred field `unconfirmed_fields`,
# never presented as fact, per FR12. Publish is blocked server-side until
# title/type/location/response_method are all in `confirmed_fields`
# (TR012) — this is the ONE gate every publish path (create/share/upload)
# goes through, not three independently-coded checks.
# Traces to: FR11, FR12, FR13, FR14, FR55, TR011, TR012, TR013, TR014, TR055
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.routers.privacy import require_accepted
from app.impressions import boosted_ids, log_events

router = APIRouter(prefix="/v1/opportunities", tags=["opportunities"])

V1_TYPES = ["employment", "freelance", "local_service"]
OTHER_TYPES = ["partnership", "training", "community"]
MATERIAL_FIELDS = {"title", "type", "location", "response_method"}

# [FR22 DEC-002 — same fixed vocabulary already verified on real apps and
# used by the (not-yet-built) Enquiries component; reused here read-only so
# the Opportunity detail's primary-action label can never independently
# drift from that one mapping (TR055's own "never a second, independently-
# coded type→label mapping" rule). [Product-owner i18n rule] Values here
# are i18n KEYS under opportunities.actionLabel.*, not display text — the
# frontend translates via `t('opportunities:actionLabel.'+key)`.]
TYPE_ACTION_LABEL = {
    "employment": "apply",
    "freelance": "submitProposal",
    "local_service": "enquireNow",
    "partnership": "contact",
    "training": "register",
    "community": "register",
}

# [FR40] advance-payment / registration-fee wording, in the three launch
# languages — the classic job-scam pattern the Indian job market reports.
ADVANCE_PAYMENT_PATTERNS = (
    "advance payment", "pay in advance", "registration fee", "registration charge", "security deposit",
    "joining fee", "processing fee", "pay to apply",
    "अग्रिम भुगतान", "पंजीकरण शुल्क", "रजिस्ट्रेशन फीस", "जमानत राशि",
    "ముందస్తు చెల్లింపు", "రిజిస్ట్రేషన్ ఫీజు", "సెక్యూరిటీ డిపాజిట్",
)

NOT_INTERESTED_REASONS = {
    "too_far", "wrong_type", "not_my_capability", "value_too_low", "wrong_timing", "already_found", "not_interested",
}


def _extract_fields(raw_input: str | None) -> dict:
    """[TR012] Rule-based extraction only — never an AI hot-path dependency,
    per FR12's own stated assumption. First non-empty line becomes a
    candidate title; a handful of keyword checks infer a type. Both are
    marked unconfirmed by the caller, never inserted as confirmed fact."""
    if not raw_input:
        return {}
    lines = [l.strip() for l in raw_input.splitlines() if l.strip()]
    title = lines[0][:200] if lines else None
    text = raw_input.lower()
    inferred_type = None
    if any(k in text for k in ["hiring", "job opening", "full-time", "full time"]):
        inferred_type = "employment"
    elif any(k in text for k in ["freelance", "project basis", "gig"]):
        inferred_type = "freelance"
    elif any(k in text for k in ["plumber", "electrician", "repair", "service needed"]):
        inferred_type = "local_service"
    return {"title": title, "type": inferred_type}


class OpportunityCreate(BaseModel):
    entry_mode: Literal["create", "share", "upload"] = "create"
    title: str | None = None
    type: str = "employment"
    description: str | None = None
    requirements: str | None = None
    compensation: str | None = None
    value_amount: float | None = None
    location: str | None = None
    work_mode: Literal["on_site", "remote", "both"] | None = None
    timing: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    response_method: Literal["in_app", "external"] = "in_app"
    deadline: datetime | None = None
    source_segment: Literal["community", "public"]
    source_name: str | None = None
    source_url: str | None = None
    raw_input: str | None = None
    raw_image_url: str | None = None


class OpportunityPatch(BaseModel):
    title: str | None = None
    type: str | None = None
    description: str | None = None
    requirements: str | None = None
    compensation: str | None = None
    value_amount: float | None = None
    location: str | None = None
    work_mode: Literal["on_site", "remote", "both"] | None = None
    timing: str | None = None
    required_capabilities: list[str] | None = None
    response_method: Literal["in_app", "external"] | None = None
    deadline: datetime | None = None


class ConfirmFieldsIn(BaseModel):
    fields: list[str]


class OpportunityOut(BaseModel):
    id: str
    poster_id: str
    is_poster: bool
    title: str
    type: str
    type_action_label: str
    description: str | None
    requirements: str | None
    compensation: str | None
    value_amount: float | None
    location: str | None
    work_mode: str | None
    timing: str | None
    required_capabilities: list[str]
    response_method: str | None
    deadline: datetime | None
    source_segment: str
    source_name: str | None
    source_url: str | None
    source_unreachable: bool
    entry_mode: str
    unconfirmed_fields: list[str]
    confirmed_fields: list[str]
    state: str
    state_reason: str | None
    saved: bool = False
    # [FR18 card fields — set only by feed.py's card builder, None elsewhere]
    submitter_name: str | None = None
    posted_days_ago: int | None = None
    relevance_reason: str | None = None  # i18n key under ranking.signal.*
    sponsored: bool = False  # [FR30/FR54] rendered only via SponsoredBadge


def _row_to_opp(row: asyncpg.Record, caller_id: str, saved: bool = False) -> OpportunityOut:
    return OpportunityOut(
        id=str(row["id"]),
        poster_id=row["poster_id"],
        is_poster=row["poster_id"] == caller_id,
        title=row["title"],
        type=row["type"],
        type_action_label=TYPE_ACTION_LABEL.get(row["type"], "contact"),
        description=row["description"],
        requirements=row["requirements"],
        compensation=row["compensation"],
        value_amount=float(row["value_amount"]) if row["value_amount"] is not None else None,
        location=row["location"],
        work_mode=row["work_mode"],
        timing=row["timing"],
        required_capabilities=list(row["required_capabilities"]),
        response_method=row["response_method"],
        deadline=row["deadline"],
        source_segment=row["source_segment"],
        source_name=row["source_name"],
        source_url=row["source_url"],
        source_unreachable=row["source_unreachable"],
        entry_mode=row["entry_mode"],
        unconfirmed_fields=list(row["unconfirmed_fields"]),
        confirmed_fields=list(row["confirmed_fields"]),
        state=row["state"],
        state_reason=row["state_reason"],
        saved=saved,
    )


@router.post("", response_model=OpportunityOut, status_code=201)
async def create_opportunity(
    body: OpportunityCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> OpportunityOut:
    if body.source_segment == "public" and not (body.source_name or body.source_url):
        raise HTTPException(status_code=422, detail=translate("opportunities.error.sourceRequired", lang))

    title, type_ = body.title, body.type
    unconfirmed: list[str] = []
    if body.entry_mode in ("share", "upload"):
        extracted = _extract_fields(body.raw_input)
        if not title and extracted.get("title"):
            title = extracted["title"]
            unconfirmed.append("title")
        if extracted.get("type"):
            type_ = extracted["type"]
            unconfirmed.append("type")
    if not title:
        title = translate("opportunities.error.untitled", lang)
        unconfirmed.append("title")
    if not body.location:
        unconfirmed.append("location")

    row = await conn.fetchrow(
        """INSERT INTO vyapar_opportunities.opportunities
             (poster_id, title, type, description, requirements, compensation, value_amount,
              location, work_mode, timing, required_capabilities, response_method, deadline,
              source_segment, source_name, source_url, entry_mode, raw_input, raw_image_url,
              unconfirmed_fields, content_language)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)
           RETURNING *""",
        ctx.member_id, title, type_, body.description, body.requirements, body.compensation, body.value_amount,
        body.location, body.work_mode, body.timing, body.required_capabilities, body.response_method, body.deadline,
        body.source_segment, body.source_name, body.source_url, body.entry_mode, body.raw_input, body.raw_image_url,
        unconfirmed, lang,
    )
    return _row_to_opp(row, ctx.member_id)


@router.get("/mine", response_model=list[OpportunityOut])
async def list_my_opportunities(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[OpportunityOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_opportunities.opportunities WHERE poster_id = $1 ORDER BY created_at DESC", ctx.member_id
    )
    return [_row_to_opp(r, ctx.member_id) for r in rows]


@router.get("/{opportunity_id}", response_model=OpportunityOut)
async def get_opportunity(
    opportunity_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    saved_row = await conn.fetchrow(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, viewed_at)
           VALUES ($1, $2, now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET viewed_at = now()
           RETURNING saved_at""",
        ctx.member_id, opportunity_id,
    )
    out = _row_to_opp(row, ctx.member_id, saved=saved_row["saved_at"] is not None)
    out.sponsored = str(row["id"]) in await boosted_ids(conn, "opportunity", [row["id"]])
    if not out.is_poster:  # [FR32] detail view event, never with member identity
        await log_events(conn, "opportunity", [row["id"]], "view", "opportunity_detail", {str(row["id"])} if out.sponsored else set())
    return out


@router.patch("/{opportunity_id}", response_model=OpportunityOut)
async def patch_opportunity(
    opportunity_id: str,
    body: OpportunityPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    # [TR014] type change after publish re-validates type-specific mandatory
    # fields (compensation for employment; location for local_service) —
    # rejects the save otherwise rather than silently accepting a half-typed record.
    new_type = body.type or current["type"]
    if body.type and body.type != current["type"] and current["state"] != "draft":
        if new_type == "employment" and not (body.compensation or current["compensation"]):
            raise HTTPException(status_code=422, detail=translate("opportunities.error.compensationRequired", lang))
        if new_type == "local_service" and not (body.location or current["location"]):
            raise HTTPException(status_code=422, detail=translate("opportunities.error.locationRequired", lang))
    row = await conn.fetchrow(
        """UPDATE vyapar_opportunities.opportunities SET
             title = COALESCE($2, title), type = COALESCE($3, type), description = COALESCE($4, description),
             requirements = COALESCE($5, requirements), compensation = COALESCE($6, compensation),
             value_amount = COALESCE($7, value_amount), location = COALESCE($8, location),
             work_mode = COALESCE($9, work_mode), timing = COALESCE($10, timing),
             required_capabilities = COALESCE($11, required_capabilities),
             response_method = COALESCE($12, response_method), deadline = COALESCE($13, deadline),
             last_confirmed_at = now(), updated_at = now()
           WHERE id = $1 RETURNING *""",
        opportunity_id, body.title, body.type, body.description, body.requirements, body.compensation,
        body.value_amount, body.location, body.work_mode, body.timing, body.required_capabilities,
        body.response_method, body.deadline,
    )
    return _row_to_opp(row, ctx.member_id)


# ---------------------------------------------------------------------------
# [TR012] Structured fields, uncertainty marking, contributor confirmation
# (FR12). Approach: `confirm` accepts the list of field names the
# contributor has reviewed and confirmed correct; removes them from
# `unconfirmed_fields` and adds to `confirmed_fields`. `publish` is blocked
# until all four material fields (title/type/location/response_method) are
# confirmed — one server-side gate, not a client-side checklist a modified
# client could bypass.
# Traces to: FR12, TR012
# ---------------------------------------------------------------------------
@router.patch("/{opportunity_id}/confirm", response_model=OpportunityOut)
async def confirm_fields(
    opportunity_id: str,
    body: ConfirmFieldsIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    confirmed = sorted(set(current["confirmed_fields"]) | set(body.fields))
    unconfirmed = [f for f in current["unconfirmed_fields"] if f not in body.fields]
    row = await conn.fetchrow(
        """UPDATE vyapar_opportunities.opportunities SET confirmed_fields = $2, unconfirmed_fields = $3, updated_at = now()
           WHERE id = $1 RETURNING *""",
        opportunity_id, confirmed, unconfirmed,
    )
    return _row_to_opp(row, ctx.member_id)


@router.post("/{opportunity_id}/publish", response_model=OpportunityOut)
async def publish_opportunity(
    opportunity_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    # [FR53/TR053] the gate every publish path calls before proceeding.
    await require_accepted(conn, ctx.member_id, "privacy", lang)
    await require_accepted(conn, ctx.member_id, "terms", lang)
    if current["state"] not in ("draft",):
        raise HTTPException(status_code=400, detail=translate("opportunities.error.alreadyPublished", lang))
    missing = MATERIAL_FIELDS - set(current["confirmed_fields"])
    # title/type are always present (defaulted at create); only require
    # explicit confirmation for fields that were actually marked unconfirmed.
    missing = {f for f in missing if f in current["unconfirmed_fields"]}
    if missing:
        raise HTTPException(status_code=422, detail=translate("opportunities.error.confirmRequired", lang, fields=", ".join(sorted(missing))))
    row = await conn.fetchrow(
        """UPDATE vyapar_opportunities.opportunities SET state='active', published_at=now(), last_confirmed_at=now(), updated_at=now()
           WHERE id=$1 RETURNING *""",
        opportunity_id,
    )
    # [FR40] "an opportunity mentioning advance payment/registration fees" is
    # an automated High flag: published, but auto-limited from distribution
    # pending operator review (automated flags prioritise, never finalise).
    text_blob = " ".join(filter(None, [row["title"], row["description"], row["requirements"], row["compensation"]])).lower()
    if any(pattern in text_blob for pattern in ADVANCE_PAYMENT_PATTERNS):
        await conn.execute(
            "SELECT vyapar_trust_safety.raise_auto_flag('opportunity', $1, $2, 'advance_payment', 'high')", opportunity_id, ctx.member_id
        )
        row = await conn.fetchrow(
            "UPDATE vyapar_opportunities.opportunities SET distribution_limited = true, updated_at = now() WHERE id = $1 RETURNING *",
            opportunity_id,
        )
    return _row_to_opp(row, ctx.member_id)


# ---------------------------------------------------------------------------
# [TR013] Opportunity lifecycle: pause/resume/close/renew (FR13).
# Traces to: FR13, TR013
# ---------------------------------------------------------------------------
@router.post("/{opportunity_id}/pause", response_model=OpportunityOut)
async def pause_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"active", "stale"}, to_state="paused")


@router.post("/{opportunity_id}/resume", response_model=OpportunityOut)
async def resume_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"paused"}, to_state="active", reset_freshness=True)


@router.post("/{opportunity_id}/close", response_model=OpportunityOut)
async def close_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"active", "paused", "stale"}, to_state="closed")


@router.post("/{opportunity_id}/renew", response_model=OpportunityOut)
async def renew_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    if current["state"] == "expired" and current["updated_at"] < datetime.now(timezone.utc) - timedelta(days=90):
        # [FR13] renewing an Expired record older than 90 days re-requires
        # material-field confirmation rather than a bare state flip.
        raise HTTPException(status_code=422, detail=translate("opportunities.error.tooOldToRenew", lang))
    row = await conn.fetchrow(
        "UPDATE vyapar_opportunities.opportunities SET state='active', last_confirmed_at=now(), updated_at=now() WHERE id=$1 RETURNING *",
        opportunity_id,
    )
    return _row_to_opp(row, ctx.member_id)


async def _lifecycle_action(conn, ctx, opportunity_id, lang: str, *, from_states: set[str], to_state: str, reset_freshness: bool = False) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    if current["state"] not in from_states:
        raise HTTPException(status_code=400, detail=translate("opportunities.error.invalidTransition", lang))
    if reset_freshness:
        row = await conn.fetchrow(
            "UPDATE vyapar_opportunities.opportunities SET state=$2, last_confirmed_at=now(), updated_at=now() WHERE id=$1 RETURNING *",
            opportunity_id, to_state,
        )
    else:
        row = await conn.fetchrow(
            "UPDATE vyapar_opportunities.opportunities SET state=$2, updated_at=now() WHERE id=$1 RETURNING *",
            opportunity_id, to_state,
        )
    return _row_to_opp(row, ctx.member_id)


# ---------------------------------------------------------------------------
# [TR055] Save / Not interested / Share-block-on-removed (FR55).
# Traces to: FR55, TR055
# ---------------------------------------------------------------------------
@router.post("/{opportunity_id}/save", response_model=OpportunityOut)
async def save_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, saved_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET saved_at = now()""",
        ctx.member_id, opportunity_id,
    )
    await log_events(conn, "opportunity", [row["id"]], "save", "opportunity_detail")  # [FR32]
    return _row_to_opp(row, ctx.member_id, saved=True)


@router.delete("/{opportunity_id}/save", response_model=OpportunityOut)
async def unsave_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    await conn.execute(
        "UPDATE vyapar_opportunities.member_opportunity SET saved_at = NULL WHERE member_id = $1 AND opportunity_id = $2",
        ctx.member_id, opportunity_id,
    )
    return _row_to_opp(row, ctx.member_id, saved=False)


class NotInterestedIn(BaseModel):
    reason: Literal["too_far", "wrong_type", "not_my_capability", "value_too_low", "wrong_timing", "already_found", "not_interested"]


@router.post("/{opportunity_id}/not-interested")
async def not_interested(opportunity_id: str, body: NotInterestedIn, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, hidden_at, hidden_reason)
           VALUES ($1,$2,now(),$3)
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET hidden_at = now(), hidden_reason = $3""",
        ctx.member_id, opportunity_id, body.reason,
    )
    return {"hidden": True}


@router.post("/{opportunity_id}/share")
async def share_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    row = await conn.fetchrow("SELECT state FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    if row["state"] == "removed":
        # [FR55] Sharing a Removed item is blocked at the API layer.
        raise HTTPException(status_code=400, detail=translate("opportunities.error.removedCannotShare", lang))
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, shared_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET shared_at = now()""",
        ctx.member_id, opportunity_id,
    )
    return {"shared": True}


@router.post("/{opportunity_id}/external-open")
async def external_open(opportunity_id: str, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    """[FR55] Records that the member opened a Public/External item's
    source link — a leave-app notice is the frontend's job; this just logs
    the action for TR048's later review use."""
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, external_opened_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET external_opened_at = now()""",
        ctx.member_id, opportunity_id,
    )
    return {"opened": True}
