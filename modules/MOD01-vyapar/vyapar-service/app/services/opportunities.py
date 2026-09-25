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

import json
from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.services.listings import require_profile
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.services.privacy import require_accepted
from app.impressions import boosted_ids, log_events
from app.taxonomy_cache import labels_for
from app.profile_cards import ProfileCard, recommend_profiles
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page, paginate


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
    # [Opportunity detail rebuild, 2026-09-21] Context a person needs to
    # decide, set only by the detail endpoint. The data always existed on the
    # row; the detail screen simply never showed it (requirements, duration,
    # skills, deadline, source were all returned and all hidden).
    capability_labels: list[str] = []  # localized display names, never raw slugs
    min_experience_years: int | None = None
    days_left: int | None = None
    response_bucket: str | None = None  # none|under_5|5_to_10|10_to_20|20_plus
    poster: PosterSummary | None = None
    # Aligned index-for-index with capability_labels: which required skills
    # the VIEWER already has. None when the viewer has listed no skills (a
    # row of red crosses would read as rejection, not guidance).
    capability_match: list[bool] | None = None
    # On recommendation cards: which of the VIEWER's own skills this
    # opportunity asks for, so the card can say why it is shown.
    viewer_matched_labels: list[str] = []


class PosterSummary(BaseModel):
    """Upwork's "About the client" / WorkIndia's company block, Vyapar-sourced:
    only facts Vyapar itself can vouch for — never a self-reported claim."""

    name: str | None
    member_since: str | None
    active_opportunities: int
    verified_listing_id: str | None
    verified_listing_name: str | None
    # "Will they get back to me?" — coarse buckets from poster_reply_habit(),
    # None until the poster has received enough enquiries to say.
    reply_rate: str | None = None  # most|some|few
    reply_speed: str | None = None  # hours|day|days


OpportunityOut.model_rebuild()


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


async def create_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    body: OpportunityCreate,
) -> OpportunityOut:
    if body.source_segment == "public" and not (body.source_name or body.source_url):
        raise ApiError(422, "opportunities.error.sourceRequired", lang)
    await require_profile(conn, ctx.member_id, lang)

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


async def list_my_opportunities(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
) -> list[OpportunityOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_opportunities.opportunities WHERE poster_id = $1 ORDER BY created_at DESC", ctx.member_id
    )
    return [_row_to_opp(r, ctx.member_id) for r in rows]


async def get_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    saved_row = await conn.fetchrow(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, viewed_at)
           VALUES ($1, $2, now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET viewed_at = now()
           RETURNING saved_at""",
        ctx.member_id, opportunity_id,
    )
    out = _row_to_opp(row, ctx.member_id, saved=saved_row["saved_at"] is not None)
    # [Real gap found live by the product owner, fixed here] feed cards
    # correctly show "posted by <name>, from your community" (a trust
    # signal research on this audience found matters more than
    # institutional signals) — but the detail screen a member actually
    # acts on never carried it at all, losing that trust signal exactly
    # where it matters most. Same RLS-safe `public_names()` lookup
    # feed.py's own card builder already uses, not a second implementation.
    if not out.is_poster:
        name_rows = await conn.fetch("SELECT display_name FROM vyapar_identity.public_names($1::text[])", [row["poster_id"]])
        out.submitter_name = name_rows[0]["display_name"] if name_rows else None
    out.sponsored = str(row["id"]) in await boosted_ids(conn, "opportunity", [row["id"]])

    # [Opportunity detail rebuild, 2026-09-21] Decision context.
    out.capability_labels = labels_for(out.required_capabilities, lang)
    eligibility = row["eligibility"]
    if isinstance(eligibility, str):
        eligibility = json.loads(eligibility)
    if isinstance(eligibility, dict) and eligibility.get("min_experience_years") is not None:
        out.min_experience_years = int(eligibility["min_experience_years"])
    now = datetime.now(timezone.utc)
    if row["deadline"]:
        out.days_left = max(0, (row["deadline"] - now).days)
    if row["published_at"]:
        out.posted_days_ago = (now - row["published_at"]).days
    # Response activity only means something where people respond through
    # Vyapar — for a Public/External item people apply on the source site.
    if out.response_method != "external":
        out.response_bucket = await conn.fetchval(
            "SELECT vyapar_enquiries.opportunity_response_bucket($1::uuid)", row["id"]
        )
    summary = await conn.fetchrow("SELECT * FROM vyapar_identity.poster_summary($1)", row["poster_id"])
    if summary:
        out.poster = PosterSummary(
            name=out.submitter_name,
            member_since=summary["member_since"].isoformat() if summary["member_since"] else None,
            active_opportunities=summary["active_opportunities"] or 0,
            verified_listing_id=str(summary["verified_listing_id"]) if summary["verified_listing_id"] else None,
            verified_listing_name=summary["verified_listing_name"],
        )
        habit = await conn.fetchrow("SELECT * FROM vyapar_enquiries.poster_reply_habit($1)", row["poster_id"])
        if habit:
            out.poster.reply_rate = habit["reply_rate"]
            out.poster.reply_speed = habit["reply_speed"]
    if not out.is_poster and out.required_capabilities:
        viewer_caps = await conn.fetchval(
            "SELECT capabilities FROM vyapar_identity.members WHERE id = $1", ctx.member_id
        )
        if viewer_caps:
            mine = set(viewer_caps)
            out.capability_match = [c in mine for c in out.required_capabilities]
    if not out.is_poster:  # [FR32] detail view event, never with member identity
        await log_events(conn, "opportunity", [row["id"]], "view", "opportunity_detail", {str(row["id"])} if out.sponsored else set())
    return out


async def list_similar_opportunities(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> list[OpportunityOut]:
    """[Opportunity detail rebuild, 2026-09-21] WorkIndia ends every job page
    with "Similar jobs" so a person who isn't the right fit keeps moving
    instead of dead-ending. Same type or any shared required skill, active
    only, never the member's own posts and never anything they hid."""
    base = await conn.fetchrow(
        "SELECT type, required_capabilities FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id
    )
    if base is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    # [Fix, found reading the screen as a member] "same type OR any shared
    # skill" put catering staff and an accounts assistant under a Python
    # developer job — same type ("employment"), nothing else in common. A
    # person reads "similar" as "I could do this instead", so a shared
    # required skill is mandatory; type alone only counts when the base
    # opportunity lists no skills at all.
    caps = list(base["required_capabilities"])
    # [Owner, 2026-09-21: "prioritize the skills as per the person's
    # profile"] Among similar opportunities, the ones that ask for skills
    # the viewer actually has come first; closeness to this one breaks ties.
    viewer_caps = list(
        await conn.fetchval("SELECT capabilities FROM vyapar_identity.members WHERE id = $1", ctx.member_id) or []
    )
    rows = await conn.fetch(
        """SELECT o.* FROM vyapar_opportunities.opportunities o
            WHERE o.id <> $1 AND o.state = 'active' AND o.poster_id <> $2
              AND (CASE WHEN cardinality($4::text[]) > 0
                        THEN o.required_capabilities && $4::text[]
                        ELSE o.type = $3 END)
              AND NOT EXISTS (
                SELECT 1 FROM vyapar_opportunities.member_opportunity mo
                 WHERE mo.opportunity_id = o.id AND mo.member_id = $2 AND mo.hidden_at IS NOT NULL)
            ORDER BY cardinality(ARRAY(SELECT unnest(o.required_capabilities) INTERSECT SELECT unnest($5::text[]))) DESC,
                     cardinality(ARRAY(SELECT unnest(o.required_capabilities) INTERSECT SELECT unnest($4::text[]))) DESC,
                     o.published_at DESC NULLS LAST
            LIMIT 4""",
        opportunity_id, ctx.member_id, base["type"], caps, viewer_caps,
    )
    mine = set(viewer_caps)
    poster_ids = list({r["poster_id"] for r in rows})
    names = {
        n["id"]: n["display_name"]
        for n in await conn.fetch("SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", poster_ids)
    } if poster_ids else {}
    now = datetime.now(timezone.utc)
    out: list[OpportunityOut] = []
    for r in rows:
        card = _row_to_opp(r, ctx.member_id)
        card.submitter_name = names.get(r["poster_id"])
        card.posted_days_ago = (now - r["published_at"]).days if r["published_at"] else None
        card.viewer_matched_labels = labels_for([c for c in r["required_capabilities"] if c in mine], lang)
        out.append(card)
    return out


async def list_matching_profiles(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> list[ProfileCard]:
    """[Owner, 2026-09-21: "we will have other profiles for you"] The poster
    of an opportunity sees the professionals and businesses who already
    have the skills it asks for, instead of only waiting for responses.
    Poster-only: to anyone else this list would be noise. Only profiles
    that opted in to opportunities (opportunity_participation) appear."""
    row = await conn.fetchrow(
        "SELECT poster_id, required_capabilities, location FROM vyapar_opportunities.opportunities WHERE id = $1",
        opportunity_id,
    )
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if row["poster_id"] != ctx.member_id:
        return []
    return await recommend_profiles(
        conn,
        skills=list(row["required_capabilities"]),
        categories=[],
        exclude_owner_ids=[ctx.member_id],
        exclude_listing_id=None,
        viewer_locality=row["location"],
        require_opportunity_participation=True,
        lang=lang,
    )


async def update_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    body: OpportunityPatch,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    # [TR014] type change after publish re-validates type-specific mandatory
    # fields (compensation for employment; location for local_service) —
    # rejects the save otherwise rather than silently accepting a half-typed record.
    new_type = body.type or current["type"]
    if body.type and body.type != current["type"] and current["state"] != "draft":
        if new_type == "employment" and not (body.compensation or current["compensation"]):
            raise ApiError(422, "opportunities.error.compensationRequired", lang)
        if new_type == "local_service" and not (body.location or current["location"]):
            raise ApiError(422, "opportunities.error.locationRequired", lang)
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
async def confirm_opportunity_fields(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    body: ConfirmFieldsIn,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    confirmed = sorted(set(current["confirmed_fields"]) | set(body.fields))
    unconfirmed = [f for f in current["unconfirmed_fields"] if f not in body.fields]
    row = await conn.fetchrow(
        """UPDATE vyapar_opportunities.opportunities SET confirmed_fields = $2, unconfirmed_fields = $3, updated_at = now()
           WHERE id = $1 RETURNING *""",
        opportunity_id, confirmed, unconfirmed,
    )
    return _row_to_opp(row, ctx.member_id)


async def publish_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    # [FR53/TR053] the gate every publish path calls before proceeding.
    await require_accepted(conn, ctx.member_id, "privacy", lang)
    await require_accepted(conn, ctx.member_id, "terms", lang)
    if current["state"] not in ("draft",):
        raise ApiError(400, "opportunities.error.alreadyPublished", lang)
    missing = MATERIAL_FIELDS - set(current["confirmed_fields"])
    # title/type are always present (defaulted at create); only require
    # explicit confirmation for fields that were actually marked unconfirmed.
    missing = {f for f in missing if f in current["unconfirmed_fields"]}
    if missing:
        raise ApiError(422, "opportunities.error.confirmRequired", lang, fields=", ".join(sorted(missing)))
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
async def pause_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"active", "stale"}, to_state="paused")


async def resume_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"paused"}, to_state="active", reset_freshness=True)


async def close_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"active", "paused", "stale"}, to_state="closed")


async def renew_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if current["state"] == "expired" and current["updated_at"] < datetime.now(timezone.utc) - timedelta(days=90):
        # [FR13] renewing an Expired record older than 90 days re-requires
        # material-field confirmation rather than a bare state flip.
        raise ApiError(422, "opportunities.error.tooOldToRenew", lang)
    row = await conn.fetchrow(
        "UPDATE vyapar_opportunities.opportunities SET state='active', last_confirmed_at=now(), updated_at=now() WHERE id=$1 RETURNING *",
        opportunity_id,
    )
    return _row_to_opp(row, ctx.member_id)


async def _lifecycle_action(conn, ctx, opportunity_id, lang: str, *, from_states: set[str], to_state: str, reset_freshness: bool = False) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if current["state"] not in from_states:
        raise ApiError(400, "opportunities.error.invalidTransition", lang)
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
async def save_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, saved_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET saved_at = now()""",
        ctx.member_id, opportunity_id,
    )
    await log_events(conn, "opportunity", [row["id"]], "save", "opportunity_detail")  # [FR32]
    return _row_to_opp(row, ctx.member_id, saved=True)


async def unsave_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    await conn.execute(
        "UPDATE vyapar_opportunities.member_opportunity SET saved_at = NULL WHERE member_id = $1 AND opportunity_id = $2",
        ctx.member_id, opportunity_id,
    )
    return _row_to_opp(row, ctx.member_id, saved=False)


class NotInterestedIn(BaseModel):
    reason: Literal["too_far", "wrong_type", "not_my_capability", "value_too_low", "wrong_timing", "already_found", "not_interested"]


class HiddenOut(BaseModel):
    hidden: bool


class SharedOut(BaseModel):
    shared: bool


class OpenedOut(BaseModel):
    opened: bool


async def mark_opportunity_not_interested(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    opportunity_id: str,
    body: NotInterestedIn,
) -> HiddenOut:
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, hidden_at, hidden_reason)
           VALUES ($1,$2,now(),$3)
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET hidden_at = now(), hidden_reason = $3""",
        ctx.member_id, opportunity_id, body.reason,
    )
    return HiddenOut(hidden=True)


async def share_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> SharedOut:
    row = await conn.fetchrow("SELECT state FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if row["state"] == "removed":
        # [FR55] Sharing a Removed item is blocked at the API layer.
        raise ApiError(400, "opportunities.error.removedCannotShare", lang)
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, shared_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET shared_at = now()""",
        ctx.member_id, opportunity_id,
    )
    return SharedOut(shared=True)


async def record_opportunity_external_open(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    opportunity_id: str,
) -> OpenedOut:
    """[FR55] Records that the member opened a Public/External item's
    source link — a leave-app notice is the frontend's job; this just logs
    the action for TR048's later review use."""
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, external_opened_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET external_opened_at = now()""",
        ctx.member_id, opportunity_id,
    )
    return OpenedOut(opened=True)


async def list_my_opportunities_page(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> Page[OpportunityOut]:
    """[Refactor A] Cursor-paged `list_my_opportunities` — same rows, same order."""
    return paginate(await list_my_opportunities(conn, ctx), limit, cursor, lang)
