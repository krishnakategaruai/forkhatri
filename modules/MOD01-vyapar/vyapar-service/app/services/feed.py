# [TR018] Opportunity Discover feed, five sections (FR18). [TR020] "Why
# this?" explanation (FR20). (The Activity screen's groups, TR055, live in
# app/services/activity.py.)
# Discovery & Ranking owns no tables (07-tech-reqs.md's component table) —
# this file computes all three purely by reading Opportunities'/Listings'
# own rows and calling the ONE shared `app.ranking` module every ranked
# surface in this codebase uses (never a second scorer per TR019's own
# "single implementation" rule).
# Approach: five independent queries (For You / Explore / Near You /
# Community / Public), each running the SAME `_opportunity_signals()` +
# `score()` pair — never a single ranked list re-sliced client-side, so
# eligibility can't diverge section-to-section (IA018's own named risk).
# Empty sections are omitted server-side. A sparse-profile member (no
# `members.capabilities`) gets Near You + Community + Public + one
# enrichment prompt instead of an empty For You/Explore. "Why this?" calls
# the exact same `_opportunity_signals()` function the feed already used
# for that member/item pair — deterministic given the same inputs, so it
# can never independently drift from what actually ranked (TR020's own
# anti-drift rule), even without a separate signals cache table.
#
# [Coordinator browser-check fixes, 2026-09-15 — real behaviour bugs found
# by an actual click-through, not a self-review]:
#  1. Hard-excludes anything the member marked Not Interested
#     (`member_opportunity.hidden_at IS NOT NULL`) from every section — was
#     previously not filtered at all, breaking FR55's own invariant.
#  2. On-site opportunities outside the member's radius are now excluded as
#     a HARD constraint (before scoring, per FR19's own rule that hard
#     constraints never become soft penalties), using the same
#     `vyapar_platform.distance_km()` Haversine helper already used
#     elsewhere in this codebase.
#  3. `distribution_limited = true` (TR040's auto-limit flag, set once an
#     auto-flagged moderation case is High/Critical) now hard-excludes from
#     every section — was previously not checked at all.
#  4. Cross-section de-duplication: an item appears in at most its single
#     highest-priority section (for_you > explore > near_you > community >
#     public), not repeated across all of them.
#  5. Each section is capped (SECTION_CARD_LIMIT) with a `total_available`
#     count so the frontend can render a "See all N" affordance instead of
#     a long repetitive scroll — directly answering the product owner's
#     standing "no scrolling burden on primary content" rule.
#  6. Cards now carry `submitter_name` (poster's display name),
#     `posted_days_ago` (freshness), and `relevance_reason` (the literal
#     top-signal key `_opportunity_signals`/`score` already computed for
#     THIS card) — previously only title/location/value/type/segment.
# [Product-owner i18n rule] `relevance_reason` and `enrichment_prompt` are
# i18n KEYS, translated by the frontend, never pre-baked English.
#
# [IMP-B, 2026-09-28 — discovery filters that work]
#  7. `FeedFilters` (radius_km, sort, availability, plus q/type/work_mode)
#     are applied in the ONE candidate query every section, the section
#     views and the saved-search matcher share. Distance is a real
#     Haversine (`vyapar_platform.distance_km`) computed in SQL from the
#     member's coordinates; every card carries `distance_km`. With an
#     explicit radius, anything measurably farther is out (remote work
#     excepted); a member without coordinates falls back to locality text.
#  8. Near You is distance-based whenever the member has coordinates
#     (within their radius, or the requested one), locality text otherwise.
#  9. `sort`: relevance (FR19 score + diversification, unchanged default),
#     distance, freshness, verified_first (poster holds a verified listing),
#     salary_high (value_amount). The eligible SET never changes with sort.
# 10. `availability` for opportunities is an urgency bucket derived from
#     the posting's own timing text and deadline (now / this_week / later),
#     documented in `_AVAILABILITY_BUCKET_SQL`.
# 11. Cards are `FeedCard` (OpportunityOut plus distance_km, poster_badges
#     and, for employment, the seeker_protection notice) — additive.
# Traces to: FR18, FR19, FR20, FR21, FR28, FR40, FR55, TR018, TR019, TR020, TR021, TR040, TR055, SP018, SP019, SP020, SP040
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import json

import asyncpg
from pydantic import BaseModel, Field

from app.identity import AuthzContext
from app.impressions import boosted_ids, log_events
from app.ranking import RankingSignals, diversify, score, top_signal_keys
from app.reputation import BadgeOut, badges_for_members
from app.services.opportunities import OpportunityOut, _row_to_opp, format_inr
from app.taxonomy_cache import categories as taxonomy_categories, children_of, label_for
from app.viewer_profile import viewer_skills
from app.i18n import translate
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page, paginate
from app.services.trust_safety import SeekerProtectionOut, seeker_protection_notice


# [Fix #5] Keep the first screen short — a handful of cards per section,
# not a long repetitive scroll. The frontend renders a "See all {n}" link
# when `total_available > len(items)`.
SECTION_CARD_LIMIT = 4
CANDIDATE_LIMIT = 100
SECTION_VIEW_LIMIT = 200

SortKey = Literal["relevance", "distance", "freshness", "verified_first", "salary_high"]
Availability = Literal["now", "this_week", "later"]

# [Fix #10] Opportunities have no structured "start" field; urgency is read
# from the poster's own words and deadline. One expression, used by the
# filter and documented here so the buckets are the same everywhere.
_AVAILABILITY_BUCKET_SQL = """
  CASE WHEN o.timing ~* '(immediate|urgent|asap|today|right now|tomorrow|तुरंत|तत्काल|आज|కల|వెంటనే|అత్యవసర|ఈరోజు)'
         OR (o.deadline IS NOT NULL AND o.deadline <= now() + interval '7 days') THEN 'now'
       WHEN o.timing ~* '(this week|within a week|week|इस हफ्ते|इस सप्ताह|हफ्ते|ఈ వారం|వారం)'
         OR (o.deadline IS NOT NULL AND o.deadline <= now() + interval '14 days') THEN 'this_week'
       ELSE 'later' END"""


class FeedFilters(BaseModel):
    """The member-controlled filters every feed surface accepts."""

    skills: list[str] = Field(default_factory=list, description="Capability slugs; any overlap")
    q: str | None = Field(default=None, max_length=200, description="Free text over title, skills, description, location")
    type: Literal["employment", "freelance", "local_service", "partnership", "training", "community"] | None = None
    work_mode: Literal["on_site", "remote", "both"] | None = None
    radius_km: int | None = Field(default=None, ge=1, le=500, description="Overrides the member's own radius for this request")
    availability: Availability | None = Field(default=None, description="now = urgent/deadline within 7 days; this_week = within 14 days; later = the rest")
    sort: SortKey = "relevance"
    # [FE2 — Discover filters redesign, 2026-09-29] additive filters. Each is
    # applied in Python on the scored candidate set (see _passes_extra), so
    # every surface — sections, section views, results, saved searches —
    # agrees, and the results endpoint can count facets cheaply.
    types: list[str] = Field(default_factory=list, description="Several kinds at once (any of); `type` still works for one")
    pay_kind: Literal["monthly", "project"] | None = Field(default=None, description="monthly = job salary; project = project/service budget")
    pay_min_paise: int | None = Field(default=None, ge=0)
    pay_max_paise: int | None = Field(default=None, ge=0)
    posted_within: Literal["today", "week", "month"] | None = None
    shift: Literal["day", "night", "flexible"] | None = Field(default=None, description="flexible also matches rotational")
    experience: Literal["fresher", "1", "3"] | None = Field(default=None, description="The member's own experience: fresher = posts open to freshers; 1 / 3 = posts asking at most that many years")
    verified_only: bool = Field(default=False, description="Only posters who own a verified business listing")
    segment: Literal["community", "public"] | None = Field(default=None, description="community = posted by members; public = shared from official sources")

    @classmethod
    def from_query(cls, *, skills: str = "", q: str | None = None, type: str | None = None, work_mode: str | None = None,
                   radius_km: int | None = None, availability: str | None = None, sort: str | None = None, sort_by: str | None = None,
                   types: str = "", pay_kind: str | None = None, pay_min_paise: int | None = None, pay_max_paise: int | None = None,
                   posted_within: str | None = None, shift: str | None = None, experience: str | None = None,
                   verified_only: bool = False, segment: str | None = None) -> "FeedFilters":
        return cls(
            skills=[s.strip() for s in (skills or "").split(",") if s.strip()], q=(q or "").strip() or None,
            type=type or None, work_mode=work_mode or None, radius_km=radius_km, availability=availability or None,
            sort=(sort_by or sort or "relevance"),
            types=[t.strip() for t in (types or "").split(",") if t.strip()], pay_kind=pay_kind or None,
            pay_min_paise=pay_min_paise, pay_max_paise=pay_max_paise, posted_within=posted_within or None,
            shift=shift or None, experience=experience or None, verified_only=bool(verified_only), segment=segment or None,
        )


class FeedCard(OpportunityOut):
    """[IMP-B] A feed card: everything the opportunity carries, plus what
    the feed knows about it for THIS member."""

    distance_km: float | None = Field(default=None, description="Haversine km from the member; null when either side has no coordinates")
    poster_badges: list[BadgeOut] = []
    seeker_protection: SeekerProtectionOut | None = None


class FeedSection(BaseModel):
    key: str
    items: list[FeedCard]
    total_available: int


class FeedResponse(BaseModel):
    sections: list[FeedSection]
    enrichment_prompt: str | None = None  # i18n key under discover.enrichment.*
    # [TR030/FR30] at most one labelled Sponsored card, drawn only from boosted
    # opportunities that ALREADY pass this member's hard constraints (hidden,
    # distribution-limited, radius) and the boost's own audience narrowing.
    # Organic sections are built exactly as before — ranking has no paid input.
    sponsored: list[FeedCard] = []
    filters: FeedFilters = Field(default_factory=FeedFilters, description="The filters this response was built with")
    # Whether distance could be measured for this member (coordinates known).
    distance_available: bool = False


# [IMP-B, FE2 "Use my location"] An optional viewer position for THIS request
# only: it replaces the member's saved lat/lng for distance and radius, and is
# never written anywhere (saved searches keep FeedFilters, which has no
# position). Validated at the router (-90..90, -180..180, both or neither).
ViewerPosition = tuple[float, float] | None


def _at_position(member, position: ViewerPosition):
    if position is None or member is None:
        return member
    out = dict(member)
    out["lat"], out["lng"] = float(position[0]), float(position[1])
    return out


async def _member_profile(conn: asyncpg.Connection, member_id: str) -> dict | None:
    """[critique L14] The viewer profile every feed read ranks against: the
    member row's place and radius, with `capabilities` = own skills + the
    skills on their active listings, and `categories` from those listings
    (app/viewer_profile.py is the one definition)."""
    row = await conn.fetchrow(
        "SELECT help_with, locality, lat, lng, radius_km FROM vyapar_identity.members WHERE id = $1",
        member_id,
    )
    if row is None:
        return None
    caps, cats = await viewer_skills(conn, member_id)
    return {**dict(row), "capabilities": caps, "categories": cats}


def _opportunity_signals(row: asyncpg.Record, member: asyncpg.Record, distance_km: float | None) -> RankingSignals:
    """[TR019] The ONE allow-listed signal computation for an opportunity
    candidate, shared by every feed section and by /why — never a second
    implementation."""
    member_caps = set(member["capabilities"] or [])
    opp_caps = set(row["required_capabilities"] or [])
    capability_fit = len(member_caps & opp_caps) / len(opp_caps) if opp_caps else 0.3

    intent_fit = 0.5  # [FR05] intent_state is private-sensitive — never read
    # here directly; a real intent-aware score would call Listings &
    # Verification's own gated read method (per TR005), not this table.

    # [Fix #2] Real distance-based location_fit now that distance_km is
    # actually computed by the caller (was a flat placeholder before).
    location_fit = max(0.0, 1.0 - distance_km / 25.0) if distance_km is not None else 0.3

    age_days = (datetime.now(timezone.utc) - row["published_at"]).days if row["published_at"] else 0
    freshness_fit = max(0.0, 1.0 - age_days / 21.0)

    return RankingSignals(capability_fit=capability_fit, intent_fit=intent_fit, location_fit=location_fit, freshness_fit=freshness_fit)


async def _distance_km(conn: asyncpg.Connection, member: asyncpg.Record, row: asyncpg.Record) -> float | None:
    if member["lat"] is None or member["lng"] is None or row["lat"] is None or row["lng"] is None:
        return None
    return await conn.fetchval(
        "SELECT vyapar_platform.distance_km($1, $2, $3, $4)", member["lat"], member["lng"], row["lat"], row["lng"]
    )


def _row_to_feed_card(row: asyncpg.Record, caller_id: str, submitter_name: str, reason_key: str, lang: str = "en") -> FeedCard:
    base = _row_to_opp(row, caller_id, lang=lang)
    card = FeedCard(**base.model_dump())
    card.submitter_name = submitter_name
    card.posted_days_ago = (
        (datetime.now(timezone.utc) - row["published_at"]).days if row["published_at"] else None
    )
    card.relevance_reason = reason_key
    d = row["distance_km"] if "distance_km" in row.keys() else None
    card.distance_km = round(float(d), 1) if d is not None else None
    notice = seeker_protection_notice(lang, row["type"])
    card.seeker_protection = notice if notice.applies else None
    return card


# ---------------------------------------------------------------------------
# [IMP-B] The one candidate query builder: sections, section views and the
# saved-search matcher all go through here, so a filter can never apply to
# one surface and not another.
# ---------------------------------------------------------------------------
def _filter_clauses(filters: FeedFilters, params: list) -> list[str]:
    clauses: list[str] = []
    if filters.skills:
        params.append(filters.skills)
        clauses.append(f"o.required_capabilities && ${len(params)}::text[]")
    if filters.q:
        params.append(filters.q)
        clauses.append(f"(o.search_tsv @@ websearch_to_tsquery('simple', ${len(params)}) OR o.title ILIKE '%' || ${len(params)} || '%')")
    if filters.type:
        params.append(filters.type)
        clauses.append(f"o.type = ${len(params)}")
    if filters.types:
        params.append(filters.types)
        clauses.append(f"o.type = ANY(${len(params)}::text[])")
    if filters.segment:
        params.append(filters.segment)
        clauses.append(f"o.source_segment = ${len(params)}")
    if filters.work_mode and filters.work_mode != "both":
        params.append(filters.work_mode)
        clauses.append(f"(o.work_mode = ${len(params)} OR o.work_mode = 'both')")
    if filters.availability == "now":
        clauses.append(f"({_AVAILABILITY_BUCKET_SQL}) = 'now'")
    elif filters.availability == "this_week":
        clauses.append(f"({_AVAILABILITY_BUCKET_SQL}) IN ('now','this_week')")
    elif filters.availability == "later":
        clauses.append(f"({_AVAILABILITY_BUCKET_SQL}) = 'later'")
    return clauses


def _section_clause(section_key: str, member: asyncpg.Record, filters: FeedFilters, params: list) -> str | None:
    """Returns the SQL clause for a section, or None when the section does
    not apply to this member (no skills for For You, no location for Near You)."""
    caps = list(member["capabilities"] or [])
    if section_key == "for_you":
        if not caps:
            return None
        params.append(caps)
        return f"o.required_capabilities && ${len(params)}::text[]"
    if section_key == "explore":
        if not caps:
            return None
        params.append(caps)
        return f"NOT (o.required_capabilities && ${len(params)}::text[])"
    if section_key == "near_you":
        # [Fix #8] distance-based when the member has coordinates.
        if member["lat"] is not None and member["lng"] is not None:
            radius = filters.radius_km or member["radius_km"] or 10
            params.append(float(radius))
            return f"vyapar_platform.distance_km($2, $3, o.lat, o.lng) <= ${len(params)}"
        if member["locality"]:
            params.append(member["locality"])
            return f"o.location ILIKE '%' || ${len(params)} || '%'"
        return None
    if section_key == "community":
        return "o.source_segment = 'community'"
    if section_key == "public":
        return "o.source_segment = 'public'"
    return None


async def _candidates(
    conn: asyncpg.Connection, member_id: str, member: asyncpg.Record, filters: FeedFilters,
    section_clause: str | None, params: list, *, limit: int, extra_where: str = "",
) -> list[asyncpg.Record]:
    """`params` must already start with [member_id, lat, lng]."""
    where = [f"({section_clause})"] if section_clause else []
    where += [f"({c})" for c in _filter_clauses(filters, params)]
    if extra_where:
        where.append(f"({extra_where})")
    return await conn.fetch(
        f"""SELECT o.*, vyapar_platform.distance_km($2, $3, o.lat, o.lng) AS distance_km
              FROM vyapar_opportunities.opportunities o
             WHERE o.state = 'active'
               AND NOT o.distribution_limited
               -- [FE2, owner review] Discover never shows the viewer's own
               -- posts; the poster finds them in Activity → Posted.
               AND o.poster_id <> $1
               AND NOT EXISTS (
                 SELECT 1 FROM vyapar_opportunities.member_opportunity mo
                 WHERE mo.opportunity_id = o.id AND mo.member_id = $1 AND mo.hidden_at IS NOT NULL
               )
               {"AND " + " AND ".join(where) if where else ""}
             LIMIT {int(limit)}""",
        *params,
    )


def _base_params(member_id: str, member: asyncpg.Record) -> list:
    lat = float(member["lat"]) if member["lat"] is not None else None
    lng = float(member["lng"]) if member["lng"] is not None else None
    return [member_id, lat, lng]


def _passes_radius(row: asyncpg.Record, member: asyncpg.Record, filters: FeedFilters) -> bool:
    """[Fix #2 + #7] Hard constraints, never soft penalties: an on-site post
    beyond the member's radius is out; with an explicit radius, anything
    measurably beyond it is out unless the work is remote; a member without
    coordinates who asked for a radius gets the locality-text fallback."""
    distance = row["distance_km"]
    radius = filters.radius_km or member["radius_km"]
    if distance is not None and radius is not None:
        if row["work_mode"] == "on_site" and distance > radius:
            return False
        if filters.radius_km is not None and row["work_mode"] != "remote" and distance > radius:
            return False
        return True
    if filters.radius_km is not None and row["work_mode"] != "remote":
        # Distance can't be measured (member or post has no coordinates):
        # fall back to the locality text, never to "include everything".
        if member["locality"] and row["location"]:
            return member["locality"].lower() in row["location"].lower()
        return False
    return True


async def _verified_posters(conn: asyncpg.Connection, poster_ids: set[str]) -> set[str]:
    if not poster_ids:
        return set()
    rows = await conn.fetch(
        "SELECT DISTINCT owner_id FROM vyapar_listings.listings WHERE owner_id = ANY($1::text[]) AND state = 'active_verified'",
        list(poster_ids),
    )
    return {r["owner_id"] for r in rows}


async def _order(conn: asyncpg.Connection, scored: list[tuple[float, str, asyncpg.Record]], filters: FeedFilters) -> list[asyncpg.Record]:
    """[Fix #9] Applies the requested order to an already-eligible, scored
    set. Relevance keeps FR19's diversification; the explicit sorts are
    strict, because a person who asked for "nearest first" expects exactly that."""
    if filters.sort == "distance":
        scored.sort(key=lambda t: (t[2]["distance_km"] is None, t[2]["distance_km"] or 0.0, -t[0]))
        return [r for _, _, r in scored]
    if filters.sort == "freshness":
        scored.sort(key=lambda t: (t[2]["published_at"] or t[2]["created_at"], t[0]), reverse=True)
        return [r for _, _, r in scored]
    if filters.sort == "salary_high":
        scored.sort(key=lambda t: (t[2]["value_amount"] is None, -float(t[2]["value_amount"] or 0), -t[0]))
        return [r for _, _, r in scored]
    if filters.sort == "verified_first":
        verified = await _verified_posters(conn, {r["poster_id"] for _, _, r in scored})
        scored.sort(key=lambda t: (t[2]["poster_id"] not in verified, -t[0]))
        return [r for _, _, r in scored]
    scored.sort(key=lambda t: t[0], reverse=True)
    return diversify([r for _, _, r in scored], lambda r: r["poster_id"], lambda r: r["type"])


async def _names_and_badges(conn: asyncpg.Connection, poster_ids: set[str], lang: str) -> tuple[dict[str, str], dict[str, list[BadgeOut]]]:
    if not poster_ids:
        return {}, {}
    name_rows = await conn.fetch(
        "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", list(poster_ids)  # [FR18 bug fix, slice 7] members RLS blanked other posters' names
    )
    names = {nr["id"]: nr["display_name"] for nr in name_rows}
    badges = await badges_for_members(conn, list(poster_ids), lang)
    return names, badges


def _cards(rows: list[asyncpg.Record], caller_id: str, names: dict, badges: dict, reason_by_id: dict[str, str], lang: str) -> list[FeedCard]:
    cards = []
    for r in rows:
        card = _row_to_feed_card(r, caller_id, names.get(r["poster_id"], ""), reason_by_id.get(str(r["id"]), "matchesFilters"), lang)
        card.poster_badges = badges.get(r["poster_id"], [])
        cards.append(card)
    return cards


async def list_opportunity_feed(
    # [Original-Vyapar upgrade, product-owner direction: "based on skills we
    # need list to be flown"] an explicit, member-controlled skill filter —
    # FR19's own capability_fit ranking signal already exists, this makes
    # it a real filter too, not just an invisible ranking input. Injected
    # into the ONE shared candidate query below so every one of the 5
    # sections is filtered identically, never a per-section special case.
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    skills: str = "",
    filters: FeedFilters | None = None,
    lang: str = "en",
    position: ViewerPosition = None,
) -> FeedResponse:
    member = _at_position(await _member_profile(conn, ctx.member_id), position)
    sparse = not member["capabilities"]
    filters = filters or FeedFilters()
    if skills and not filters.skills:
        filters = filters.model_copy(update={"skills": [s for s in skills.split(",") if s]})

    async def scored_candidates(section_key: str | None, *, extra_where: str = "", extra_params: list | None = None) -> list[tuple[float, str, asyncpg.Record]]:
        params = _base_params(ctx.member_id, member)
        clause = _section_clause(section_key, member, filters, params) if section_key else None
        if section_key and clause is None:
            return []
        if extra_params:
            # extra_where may reference $N placeholders numbered after the current params
            params.extend(extra_params)
        rows = await _candidates(conn, ctx.member_id, member, filters, clause, params, limit=CANDIDATE_LIMIT, extra_where=extra_where)
        verified = await _verified_posters(conn, {r["poster_id"] for r in rows}) if filters.verified_only else set()
        out = []
        for r in rows:
            if not _passes_radius(r, member, filters) or not _passes_extra(r, filters, verified):
                continue
            signals = _opportunity_signals(r, member, r["distance_km"])
            keys = top_signal_keys(signals, limit=1)
            reason_key = keys[0] if keys else "matchesFilters"
            out.append((score(signals), reason_key, r))
        return out

    used_ids: set[str] = set()

    async def build_section(section_key: str) -> tuple[list[FeedCard], int]:
        scored = await scored_candidates(section_key)
        # [Fix #4] cross-section de-duplication — an item already placed in
        # a higher-priority section is skipped here entirely, not repeated.
        deduped = [(s, reason, r) for s, reason, r in scored if str(r["id"]) not in used_ids]
        ordered = await _order(conn, deduped, filters)
        reason_by_id = {str(r["id"]): reason for _, reason, r in deduped}
        total_available = len(ordered)
        page = ordered[:SECTION_CARD_LIMIT]
        names, badges = await _names_and_badges(conn, {r["poster_id"] for r in page}, lang)
        cards = _cards(page, ctx.member_id, names, badges, reason_by_id, lang)
        used_ids.update(str(r["id"]) for r in page)
        return cards, total_available

    sections: list[FeedSection] = []

    # Priority order matches the de-duplication comment above: for_you,
    # explore, near_you, community, public. Each later section only ever
    # shows items not already placed earlier.
    for key in ("for_you", "explore", "near_you", "community", "public"):
        if sparse and key in ("for_you", "explore"):
            continue
        items, total = await build_section(key)
        if items:
            sections.append(FeedSection(key=key, items=items, total_available=total))

    enrichment = "sparseProfile" if sparse else None

    sponsored_cards: list[FeedCard] = []
    boosts = await conn.fetch("SELECT * FROM vyapar_commercial.active_boosts('opportunity', NULL) ORDER BY starts_at")
    if boosts:
        boost_ids = [str(b["target_id"]) for b in boosts]
        audience_by_id = {str(b["target_id"]): (b["audience"] if isinstance(b["audience"], dict) else json.loads(b["audience"] or "{}")) for b in boosts}
        scored = await scored_candidates(None, extra_where="o.id = ANY($4::uuid[])", extra_params=[boost_ids])
        scored.sort(key=lambda t: t[0], reverse=True)
        for _, reason_key, r in scored:
            wanted = audience_by_id.get(str(r["id"]), {}).get("locality")
            if wanted and not (member["locality"] and wanted.lower() in member["locality"].lower()):
                continue
            names, badges = await _names_and_badges(conn, {r["poster_id"]}, lang)
            card = _cards([r], ctx.member_id, names, badges, {str(r["id"]): reason_key}, lang)[0]
            card.sponsored = True
            sponsored_cards.append(card)
            break

    # [FR32] impressions: organic slots are organic even for a boosted item;
    # only the Sponsored slot counts as a boosted impression.
    organic_ids = [c.id for s in sections for c in s.items]
    await log_events(conn, "opportunity", organic_ids, "impression", "feed", set())
    await log_events(conn, "opportunity", [c.id for c in sponsored_cards], "impression", "feed", {c.id for c in sponsored_cards})

    return FeedResponse(
        sections=sections, enrichment_prompt=enrichment, sponsored=sponsored_cards, filters=filters,
        distance_available=member["lat"] is not None and member["lng"] is not None,
    )


# [Fix #5 — "See all" affordance] A single-section deep view, reusing the
# exact same hard-constraint/scoring logic as the main feed (same candidate
# query) but with a much higher limit and no cross-section de-duplication —
# there is only one section in this request, so nothing to de-duplicate
# against.
SECTION_KEYS = ("for_you", "explore", "near_you", "community", "public")


async def list_opportunity_feed_section(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    section_key: str,
    filters: FeedFilters | None = None,
    lang: str = "en",
    position: ViewerPosition = None,
) -> list[FeedCard]:
    if section_key not in SECTION_KEYS:
        return []
    member = _at_position(await _member_profile(conn, ctx.member_id), position)
    filters = filters or FeedFilters()
    params = _base_params(ctx.member_id, member)
    clause = _section_clause(section_key, member, filters, params)
    if clause is None:
        return []
    rows = await _candidates(conn, ctx.member_id, member, filters, clause, params, limit=SECTION_VIEW_LIMIT)
    verified = await _verified_posters(conn, {r["poster_id"] for r in rows}) if filters.verified_only else set()
    scored = []
    for r in rows:
        if not _passes_radius(r, member, filters) or not _passes_extra(r, filters, verified):
            continue
        signals = _opportunity_signals(r, member, r["distance_km"])
        keys = top_signal_keys(signals, limit=1)
        scored.append((score(signals), keys[0] if keys else "matchesFilters", r))
    reason_by_id = {str(r["id"]): reason for _, reason, r in scored}
    ordered = await _order(conn, scored, filters)
    names, badges = await _names_and_badges(conn, {r["poster_id"] for r in ordered}, lang)
    return _cards(ordered, ctx.member_id, names, badges, reason_by_id, lang)


class WhyResponse(BaseModel):
    signals: list[str]  # i18n keys under ranking.signal.*
    gap: str | None = None
    gap_skills: str | None = None
    sponsored_note: str | None = None
    distance_km: float | None = None


async def get_opportunity_why(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    opportunity_id: str,
) -> WhyResponse:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        return WhyResponse(signals=["matchedSearch"])
    member = await _member_profile(conn, ctx.member_id)
    distance = await _distance_km(conn, member, row)
    signals = _opportunity_signals(row, member, distance)
    keys = top_signal_keys(signals, limit=3)
    if not keys:
        keys = ["matchedSearch"]
    gap = None
    member_caps = set(member["capabilities"] or [])
    opp_caps = set(row["required_capabilities"] or [])
    missing = opp_caps - member_caps
    if missing:
        gap = "missingSkills"
    # [TR020/FR30] Sponsored disclosure — populated when a boost is active,
    # stating it paid for reach, never that it changed this match.
    sponsored_note = "sponsored" if str(row["id"]) in await boosted_ids(conn, "opportunity", [row["id"]]) else None
    return WhyResponse(
        signals=keys, gap=gap, gap_skills=", ".join(sorted(missing)) if missing else None, sponsored_note=sponsored_note,
        distance_km=round(float(distance), 1) if distance is not None else None,
    )


async def list_opportunity_feed_section_page(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None, section_key: str = "",
    filters: FeedFilters | None = None,
    position: ViewerPosition = None,
) -> Page[FeedCard]:
    """[Refactor A] Cursor-paged `list_opportunity_feed_section` — same rows, same order."""
    return paginate(await list_opportunity_feed_section(conn, ctx, section_key=section_key, filters=filters, lang=lang, position=position), limit, cursor, lang)


# ---------------------------------------------------------------------------
# [IMP-B/FR21] Saved-search matching for the notification pass. Runs under
# the dispatcher context on the member's behalf, through the SAME candidate
# query the feed uses, restricted to posts published since the last alert.
# ---------------------------------------------------------------------------
async def saved_search_matches(
    conn: asyncpg.Connection, member: asyncpg.Record, query: str, filters: FeedFilters, since: datetime, limit: int = 5,
) -> list[asyncpg.Record]:
    effective = filters if not query else filters.model_copy(update={"q": query})
    params = _base_params(member["id"], member)
    params.append(since)
    rows = await _candidates(
        conn, member["id"], member, effective, None, params, limit=CANDIDATE_LIMIT,
        extra_where=f"o.published_at > ${len(params)} AND o.poster_id <> $1 AND o.type IN ('employment','freelance','local_service')",
    )
    kept = [r for r in rows if _passes_radius(r, member, effective)]
    kept.sort(key=lambda r: r["published_at"] or r["created_at"], reverse=True)
    return kept[:limit]


# ===========================================================================
# [FE2 — Discover filters redesign + themed rows, owner review 2026-09-29]
#
# 1. `_passes_extra`: the new filters (pay range, posted within, shift,
#    experience, verified posters) as plain predicates on a candidate row.
# 2. `list_opportunity_results`: ONE flat ranked list for a search or any
#    active filter, with its total and facet counts. Facets are counted
#    "disjunctively": each dimension's counts apply every OTHER active
#    filter but not its own, so a person sees what each option would give.
#    The counted dimensions (type, work mode, posted, shift, experience,
#    verified, skills, pay) are applied in Python here; q, availability
#    and the radius stay where they were.
# 3. `list_opportunity_rows`: the curated Discover home as themed rows:
#    For you, Near you (radius in the title), a row per category the member
#    works in, New today, Starting now, Paying 20,000+ a month, Verified
#    posters, From your community, Projects, Work from home. Each row names
#    the filters its "See all" opens.
# Everything goes through the same candidate query as the feed, so hidden,
# distribution-limited and the viewer's own posts never appear.
# ===========================================================================

RESULTS_CANDIDATE_LIMIT = 300
ROW_ITEM_LIMIT = 10
PAY_ROW_MIN_PAISE = 2_000_000  # 20,000 rupees a month
# [critique L13/L14] rows
PROJECT_ROW_MIN_PAISE = 1_000_000  # projects / local work with a budget over 10,000 rupees
ROWS_MAX = 6
ROW_MIN_ITEMS = 3
LOCAL_WORK_TYPES = ("employment", "local_service")
PROJECT_TYPES = ("freelance", "local_service")


def _col(row: asyncpg.Record, key: str):
    return row[key] if key in row.keys() else None


def _posted_days(row: asyncpg.Record) -> int | None:
    ts = row["published_at"] or row["created_at"]
    return (datetime.now(timezone.utc) - ts).days if ts else None


def _pay_range(row: asyncpg.Record, kind: str | None) -> tuple[int | None, int | None]:
    if kind == "monthly" or (kind is None and row["type"] == "employment"):
        return _col(row, "salary_min_paise"), _col(row, "salary_max_paise")
    lo = _col(row, "budget_min_paise") or _col(row, "budget_paise")
    hi = _col(row, "budget_max_paise") or _col(row, "budget_paise")
    return lo, hi


def _monthly_top(row: asyncpg.Record) -> int:
    lo, hi = _pay_range(row, "monthly")
    return hi or lo or 0


_POSTED_DAYS = {"today": 0, "week": 7, "month": 31}
_EXPERIENCE_MONTHS = {"fresher": 0, "1": 12, "3": 36}


def _shift_matches(row: asyncpg.Record, wanted: str) -> bool:
    return _col(row, "shift") in (("flexible", "rotational") if wanted == "flexible" else (wanted,))


def _dim_ok(row: asyncpg.Record, f: FeedFilters, dim: str, verified: set[str]) -> bool:
    if dim == "type":
        wanted = set(f.types) | ({f.type} if f.type else set())
        return not wanted or row["type"] in wanted
    if dim == "work_mode":
        return not f.work_mode or f.work_mode == "both" or row["work_mode"] in (f.work_mode, "both")
    if dim == "skills":
        return not f.skills or bool(set(row["required_capabilities"] or []) & set(f.skills))
    if dim == "posted":
        if not f.posted_within:
            return True
        days = _posted_days(row)
        return days is not None and days <= _POSTED_DAYS[f.posted_within]
    if dim == "shift":
        return not f.shift or _shift_matches(row, f.shift)
    if dim == "experience":
        return not f.experience or (_col(row, "experience_min_months") or 0) <= _EXPERIENCE_MONTHS[f.experience]
    if dim == "verified":
        return not f.verified_only or row["poster_id"] in verified
    if dim == "pay":
        if f.pay_min_paise is None and f.pay_max_paise is None:
            return True
        if f.pay_kind == "monthly" and row["type"] != "employment":
            return False
        if f.pay_kind == "project" and row["type"] not in ("freelance", "local_service"):
            return False
        lo, hi = _pay_range(row, f.pay_kind)
        if lo is None and hi is None:
            return False  # a pay filter only shows posts that state their pay
        top = hi if hi is not None else lo
        bottom = lo if lo is not None else hi
        if f.pay_min_paise is not None and top < f.pay_min_paise:
            return False
        if f.pay_max_paise is not None and bottom > f.pay_max_paise:
            return False
        return True
    return True


_EXTRA_DIMS = ("posted", "shift", "experience", "verified", "pay")
_RESULT_DIMS = ("type", "work_mode", "skills") + _EXTRA_DIMS


def _passes_extra(row: asyncpg.Record, f: FeedFilters, verified: set[str]) -> bool:
    return all(_dim_ok(row, f, d, verified) for d in _EXTRA_DIMS)


class FacetCount(BaseModel):
    value: str
    count: int
    label: str | None = None


class FeedFacets(BaseModel):
    type: list[FacetCount] = []
    work_mode: list[FacetCount] = []
    posted_within: list[FacetCount] = []
    shift: list[FacetCount] = []
    experience: list[FacetCount] = []
    verified: int = 0
    skills: list[FacetCount] = Field(default_factory=list, description="Top 8 skills among the results, localized")


class ResultsResponse(BaseModel):
    items: list[FeedCard]
    total: int
    facets: FeedFacets
    filters: FeedFilters
    distance_available: bool = False
    near_label: str | None = Field(default=None, description="The member's locality, for 'near ...' headings")
    radius_km: int | None = Field(default=None, description="The radius in effect (the filter, else the member's own)")


async def list_opportunity_results(
    conn: asyncpg.Connection, ctx: AuthzContext, filters: FeedFilters, lang: str = "en", limit: int = 60,
    position: ViewerPosition = None,
) -> ResultsResponse:
    member = _at_position(await _member_profile(conn, ctx.member_id), position)
    sql_filters = FeedFilters(q=filters.q, availability=filters.availability, segment=filters.segment)
    params = _base_params(ctx.member_id, member)
    rows = await _candidates(conn, ctx.member_id, member, sql_filters, None, params, limit=RESULTS_CANDIDATE_LIMIT)
    rows = [r for r in rows if _passes_radius(r, member, filters)]
    verified = await _verified_posters(conn, {r["poster_id"] for r in rows})

    def passes_all_but(r: asyncpg.Record, skip: str | None) -> bool:
        return all(_dim_ok(r, filters, d, verified) for d in _RESULT_DIMS if d != skip)

    def counts(dim: str, values: list[str], probe) -> list[FacetCount]:
        pool = [r for r in rows if passes_all_but(r, dim)]
        return [FacetCount(value=v, count=sum(1 for r in pool if probe(r, v))) for v in values]

    def posted_probe(r: asyncpg.Record, v: str) -> bool:
        days = _posted_days(r)
        return days is not None and days <= _POSTED_DAYS[v]

    facets = FeedFacets(
        type=counts("type", ["employment", "freelance", "local_service", "partnership", "training", "community"], lambda r, v: r["type"] == v),
        work_mode=counts("work_mode", ["on_site", "remote", "both"],
                         lambda r, v: r["work_mode"] == v or (v != "both" and r["work_mode"] == "both")),
        posted_within=counts("posted", ["today", "week", "month"], posted_probe),
        shift=counts("shift", ["day", "night", "flexible"], _shift_matches),
        experience=counts("experience", ["fresher", "1", "3"],
                          lambda r, v: (_col(r, "experience_min_months") or 0) <= _EXPERIENCE_MONTHS[v]),
        verified=sum(1 for r in rows if passes_all_but(r, "verified") and r["poster_id"] in verified),
    )
    skill_counts: dict[str, int] = {}
    for r in rows:
        if not passes_all_but(r, "skills"):
            continue
        for slug in set(r["required_capabilities"] or []):
            skill_counts[slug] = skill_counts.get(slug, 0) + 1
    for slug in filters.skills:  # a chosen skill always stays listed
        skill_counts.setdefault(slug, 0)
    top = sorted(skill_counts.items(), key=lambda kv: (kv[0] not in filters.skills, -kv[1], kv[0]))[:8]
    facets.skills = [FacetCount(value=slug, count=n, label=label_for(slug, lang)) for slug, n in top]

    matched = [r for r in rows if passes_all_but(r, None)]
    scored = []
    for r in matched:
        signals = _opportunity_signals(r, member, r["distance_km"])
        keys = top_signal_keys(signals, limit=1)
        scored.append((score(signals), keys[0] if keys else "matchesFilters", r))
    reason_by_id = {str(r["id"]): reason for _, reason, r in scored}
    ordered = await _order(conn, scored, filters)
    page = ordered[: max(1, min(limit, 100))]
    names, badges = await _names_and_badges(conn, {r["poster_id"] for r in page}, lang)
    items = _cards(page, ctx.member_id, names, badges, reason_by_id, lang)
    await log_events(conn, "opportunity", [c.id for c in items], "impression", "feed", set())
    return ResultsResponse(
        items=items, total=len(ordered), facets=facets, filters=filters,
        distance_available=member["lat"] is not None and member["lng"] is not None,
        near_label=member["locality"], radius_km=filters.radius_km or member["radius_km"],
    )


class FeedRow(BaseModel):
    key: str = Field(description="for_you | category:<slug> | near_you | pay_20k | pay_projects | new_today | starting_now | projects | remote")
    title_key: str = Field(description="i18n key under explore.rows.* (the web app translates it)")
    title: str = Field(default="", description="The same title, already localized by the server (fallback for a key the client lacks)")
    title_params: dict[str, str | int] = {}
    see_all: dict[str, str | int | bool] = Field(default_factory=dict, description="Discover filters that open this row as one full list")
    items: list[FeedCard]
    total: int


class RowsResponse(BaseModel):
    rows: list[FeedRow]
    enrichment_prompt: str | None = None
    distance_available: bool = False


async def list_opportunity_rows(conn: asyncpg.Connection, ctx: AuthzContext, lang: str = "en", position: ViewerPosition = None) -> RowsResponse:
    """[IMP-B, critique L13/L14, 2026-09-29] The Discover home as themed rows.

    - Relevance comes from the viewer profile (own skills + active listings',
      see app/viewer_profile.py), so a CA with skills only on her business
      profile gets "For you".
    - Rows are filled in priority order, most specific first: For you and the
      skill-category rows, Near you (within the radius, only kinds of work the
      member does, skill matches first), the pay band that fits the member
      (monthly jobs for people whose skills match jobs, project budgets for
      professionals), New today, Starting this week, then the generic Projects
      and Work from home rows from whatever is left.
    - A post shown in one row is never shown in another (the first row that
      shows it claims it). A row with fewer than ROW_MIN_ITEMS unclaimed posts
      is hidden, and the home stops at ROWS_MAX rows.
    - "Verified" and "Community" are no longer rows: they matched almost the
      whole feed, so they are filters and card badges, not themes.
    - Every row is ordered by relevance to the viewer first (their skill, a
      related skill in the same trade category, open local work, anything
      else; then the FR19 score); the row's own order (freshness, pay) breaks
      ties. Near you admits only the first three tiers, so a grant or a
      Python job never opens an electrician's Near you.
    `total` is the full count behind the row's See-all filters.
    """
    member = _at_position(await _member_profile(conn, ctx.member_id), position)
    params = _base_params(ctx.member_id, member)
    rows = await _candidates(conn, ctx.member_id, member, FeedFilters(), None, params, limit=RESULTS_CANDIDATE_LIMIT)
    rows = [r for r in rows if _passes_radius(r, member, FeedFilters())]
    caps = set(member["capabilities"] or [])
    score_by_id: dict[str, float] = {}
    reason_by_id: dict[str, str] = {}
    for r in rows:
        signals = _opportunity_signals(r, member, r["distance_km"])
        keys = top_signal_keys(signals, limit=1)
        score_by_id[str(r["id"])] = score(signals)
        reason_by_id[str(r["id"])] = keys[0] if keys else "matchesFilters"
    radius = int(member["radius_km"] or 10)
    now = datetime.now(timezone.utc)
    has_coords = member["lat"] is not None and member["lng"] is not None

    # Skills in the same trade category as the member's own (a plumbing job
    # is related work for an electrician: both are Home repair).
    related: set[str] = set()
    for term in taxonomy_categories():
        kids = set(children_of(term.slug))
        if kids & caps or term.slug in member["categories"]:
            related |= kids

    def skill_match(r) -> bool:
        return bool(set(r["required_capabilities"] or []) & caps)

    def tier(r) -> int:
        """0 their skill, 1 a related skill, 2 open local work asking for no
        particular skill, 3 anything else."""
        req = set(r["required_capabilities"] or [])
        if req & caps:
            return 0
        if req & related:
            return 1
        if not req and r["type"] in LOCAL_WORK_TYPES:
            return 2
        return 3

    def does_this_kind(r) -> bool:
        """Work the member can take. A member with no skills yet (a fresher)
        is shown jobs and local work."""
        return tier(r) <= 2 if caps else r["type"] in LOCAL_WORK_TYPES

    def relevance_key(r):
        return (tier(r) if caps else 0, -score_by_id[str(r["id"])])

    def pick(pred, tiebreak=None) -> list[asyncpg.Record]:
        chosen = [r for r in rows if pred(r)]
        chosen.sort(key=lambda r: (relevance_key(r), tiebreak(r) if tiebreak else 0))
        return chosen

    fresh = lambda r: -(r["published_at"] or r["created_at"]).timestamp()  # noqa: E731
    specs: list[tuple[str, str, dict, dict, list]] = []
    if caps:
        specs.append(("for_you", "forYou", {}, {"skills": ",".join(sorted(caps))}, pick(skill_match)))
        by_cat: dict[str, int] = {}
        for term in taxonomy_categories():
            n = len(set(children_of(term.slug)) & caps) + (1 if term.slug in member["categories"] else 0)
            if n:
                by_cat[term.slug] = n
        for slug, _ in sorted(by_cat.items(), key=lambda kv: -kv[1])[:2]:
            kids = set(children_of(slug))
            specs.append((f"category:{slug}", "category", {"category": label_for(slug, lang)}, {"skills": ",".join(sorted(kids))},
                          pick(lambda r, kids=kids: bool(set(r["required_capabilities"] or []) & kids))))
    if has_coords:
        specs.append(("near_you", "nearYou", {"km": radius, "place": member["locality"] or ""}, {"radius_km": radius},
                      pick(lambda r: r["distance_km"] is not None and r["distance_km"] <= radius and does_this_kind(r))))
    # The pay band that fits the member (L14): monthly pay for people whose
    # skills fit jobs (and freshers), project budgets for professionals.
    employment_fit = not caps or any(r["type"] == "employment" and skill_match(r) for r in rows)
    project_fit = bool(caps) and any(r["type"] in PROJECT_TYPES and skill_match(r) for r in rows)
    if employment_fit:
        specs.append(("pay_20k", "pay20k", {"amount": format_inr(PAY_ROW_MIN_PAISE)},
                      {"types": "employment", "pay_kind": "monthly", "pay_min_paise": PAY_ROW_MIN_PAISE, "sort": "salary_high"},
                      pick(lambda r: r["type"] == "employment" and _monthly_top(r) >= PAY_ROW_MIN_PAISE and does_this_kind(r),
                           lambda r: -_monthly_top(r))))
    if project_fit:
        specs.append(("pay_projects", "projectsBudget", {"amount": format_inr(PROJECT_ROW_MIN_PAISE)},
                      {"types": ",".join(PROJECT_TYPES), "pay_kind": "project", "pay_min_paise": PROJECT_ROW_MIN_PAISE, "sort": "salary_high"},
                      pick(lambda r: r["type"] in PROJECT_TYPES and (_pay_range(r, "project")[1] or 0) >= PROJECT_ROW_MIN_PAISE and skill_match(r),
                           lambda r: -(_pay_range(r, "project")[1] or 0))))
    specs += [
        ("new_today", "newToday", {}, {"posted_within": "today", "sort": "freshness"}, pick(lambda r: _posted_days(r) == 0, fresh)),
        ("starting_now", "startingNow", {}, {"availability": "now"},
         pick(lambda r: r["deadline"] is not None and r["deadline"] <= now + timedelta(days=7))),
        ("projects", "projects", {}, {"types": "freelance"}, pick(lambda r: r["type"] == "freelance")),
        ("remote", "remote", {}, {"work_mode": "remote"}, pick(lambda r: r["work_mode"] == "remote")),
    ]

    out: list[FeedRow] = []
    claimed: set[str] = set()
    for key, title_key, title_params, see_all, chosen in specs:
        if len(out) >= ROWS_MAX:
            break
        page = [r for r in chosen if str(r["id"]) not in claimed][:ROW_ITEM_LIMIT]
        if len(page) < ROW_MIN_ITEMS:
            continue  # hidden, and it claims nothing
        claimed.update(str(r["id"]) for r in page)
        names, badges = await _names_and_badges(conn, {r["poster_id"] for r in page}, lang)
        out.append(FeedRow(
            key=key, title_key=title_key, title=translate(f"discover.rows.{title_key}", lang, **title_params),
            title_params=title_params, see_all=see_all,
            items=_cards(page, ctx.member_id, names, badges, reason_by_id, lang), total=len(chosen),
        ))
    await log_events(conn, "opportunity", list(claimed), "impression", "feed", set())
    return RowsResponse(rows=out, enrichment_prompt=None if caps else "sparseProfile", distance_available=has_coords)
