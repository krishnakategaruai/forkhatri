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
# Traces to: FR18, FR19, FR20, FR55, TR018, TR019, TR020, TR040, TR055, SP018, SP019, SP020, SP040
from __future__ import annotations

from datetime import datetime, timezone

import json

import asyncpg
from pydantic import BaseModel

from app.identity import AuthzContext
from app.impressions import boosted_ids, log_events
from app.ranking import RankingSignals, diversify, score, top_signal_keys
from app.services.opportunities import OpportunityOut, _row_to_opp
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page, paginate


# [Fix #5] Keep the first screen short — a handful of cards per section,
# not a long repetitive scroll. The frontend renders a "See all {n}" link
# when `total_available > len(items)`.
SECTION_CARD_LIMIT = 4


async def _member_profile(conn: asyncpg.Connection, member_id: str) -> asyncpg.Record:
    return await conn.fetchrow(
        "SELECT capabilities, help_with, locality, lat, lng, radius_km FROM vyapar_identity.members WHERE id = $1",
        member_id,
    )


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


def _row_to_feed_card(row: asyncpg.Record, caller_id: str, submitter_name: str, reason_key: str) -> OpportunityOut:
    card = _row_to_opp(row, caller_id)
    card.submitter_name = submitter_name
    card.posted_days_ago = (
        (datetime.now(timezone.utc) - row["published_at"]).days if row["published_at"] else None
    )
    card.relevance_reason = reason_key
    return card


class FeedSection(BaseModel):
    key: str
    items: list[OpportunityOut]
    total_available: int


class FeedResponse(BaseModel):
    sections: list[FeedSection]
    enrichment_prompt: str | None = None  # i18n key under discover.enrichment.*
    # [TR030/FR30] at most one labelled Sponsored card, drawn only from boosted
    # opportunities that ALREADY pass this member's hard constraints (hidden,
    # distribution-limited, radius) and the boost's own audience narrowing.
    # Organic sections are built exactly as before — ranking has no paid input.
    sponsored: list[OpportunityOut] = []


async def list_opportunity_feed(
    # [Original-Vyapar upgrade, product-owner direction: "based on skills we
    # need list to be flown"] an explicit, member-controlled skill filter —
    # FR19's own capability_fit ranking signal already exists, this makes
    # it a real filter too, not just an invisible ranking input. Injected
    # into the ONE shared `candidates()` choke point below so every one of
    # the 5 sections is filtered identically, never a per-section special case.
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    skills: str = "",
) -> FeedResponse:
    member = await _member_profile(conn, ctx.member_id)
    sparse = not member["capabilities"]
    skills_list = [s for s in skills.split(",") if s]

    async def candidates(where: str, params: list) -> list[asyncpg.Record]:
        # [Fix #1 + #3] hard-excludes hidden-by-this-member and
        # distribution-limited rows for EVERY section, at the query level —
        # never a soft penalty, never left to per-section logic to remember.
        extra_params = list(params)
        skills_clause = ""
        if skills_list:
            skills_clause = f" AND o.required_capabilities && ${len(extra_params) + 2}"
            extra_params.append(skills_list)
        return await conn.fetch(
            f"""SELECT o.* FROM vyapar_opportunities.opportunities o
                WHERE o.state = 'active'
                  AND NOT o.distribution_limited
                  AND NOT EXISTS (
                    SELECT 1 FROM vyapar_opportunities.member_opportunity mo
                    WHERE mo.opportunity_id = o.id AND mo.member_id = $1 AND mo.hidden_at IS NOT NULL
                  )
                  AND ({where})
                  {skills_clause}
                LIMIT 100""",
            ctx.member_id, *extra_params,
        )

    async def scored_candidates(where: str, params: list) -> list[tuple[float, str, asyncpg.Record]]:
        rows = await candidates(where, params)
        out = []
        for r in rows:
            # [Fix #2] Hard constraint, not a soft penalty: an on-site
            # opportunity outside the member's radius is excluded entirely
            # before scoring, per FR19's own "hard constraints never
            # degrade to a soft penalty" rule.
            distance = await _distance_km(conn, member, r)
            if r["work_mode"] == "on_site" and distance is not None and member["radius_km"] is not None and distance > member["radius_km"]:
                continue
            signals = _opportunity_signals(r, member, distance)
            keys = top_signal_keys(signals, limit=1)
            reason_key = keys[0] if keys else "matchesFilters"
            out.append((score(signals), reason_key, r))
        out.sort(key=lambda t: t[0], reverse=True)
        return out

    used_ids: set[str] = set()

    async def build_section(where: str, params: list) -> tuple[list[OpportunityOut], int]:
        scored = await scored_candidates(where, params)
        # [Fix #4] cross-section de-duplication — an item already placed in
        # a higher-priority section is skipped here entirely, not repeated.
        deduped = [(reason, r) for _, reason, r in scored if str(r["id"]) not in used_ids]
        ordered = diversify([r for _, r in deduped], lambda r: r["poster_id"], lambda r: r["type"])
        reason_by_id = {str(r["id"]): reason for reason, r in deduped}
        total_available = len(ordered)
        page = ordered[:SECTION_CARD_LIMIT]
        poster_ids = {r["poster_id"] for r in page}
        names = {}
        if poster_ids:
            name_rows = await conn.fetch(
                "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", list(poster_ids)  # [FR18 bug fix, slice 7] members RLS blanked other posters' names
            )
            names = {nr["id"]: nr["display_name"] for nr in name_rows}
        cards = [
            _row_to_feed_card(r, ctx.member_id, names.get(r["poster_id"], ""), reason_by_id[str(r["id"])])
            for r in page
        ]
        used_ids.update(str(r["id"]) for r in page)
        return cards, total_available

    sections: list[FeedSection] = []

    # Priority order matches the de-duplication comment above: for_you,
    # explore, near_you, community, public. Each later section only ever
    # shows items not already placed earlier.
    if not sparse:
        items, total = await build_section("o.required_capabilities && $2", [list(member["capabilities"])])
        if items:
            sections.append(FeedSection(key="for_you", items=items, total_available=total))
        items, total = await build_section("NOT (o.required_capabilities && $2)", [list(member["capabilities"])])
        if items:
            sections.append(FeedSection(key="explore", items=items, total_available=total))

    if member["locality"]:
        items, total = await build_section("o.location ILIKE '%' || $2 || '%'", [member["locality"]])
        if items:
            sections.append(FeedSection(key="near_you", items=items, total_available=total))

    items, total = await build_section("o.source_segment = 'community'", [])
    if items:
        sections.append(FeedSection(key="community", items=items, total_available=total))

    items, total = await build_section("o.source_segment = 'public'", [])
    if items:
        sections.append(FeedSection(key="public", items=items, total_available=total))

    enrichment = "sparseProfile" if sparse else None

    sponsored_cards: list[OpportunityOut] = []
    boosts = await conn.fetch("SELECT * FROM vyapar_commercial.active_boosts('opportunity', NULL) ORDER BY starts_at")
    if boosts:
        boost_ids = [str(b["target_id"]) for b in boosts]
        audience_by_id = {str(b["target_id"]): (b["audience"] if isinstance(b["audience"], dict) else json.loads(b["audience"] or "{}")) for b in boosts}
        for _, reason_key, r in await scored_candidates("o.id = ANY($2::uuid[])", [boost_ids]):
            wanted = audience_by_id.get(str(r["id"]), {}).get("locality")
            if wanted and not (member["locality"] and wanted.lower() in member["locality"].lower()):
                continue
            names = {nr["id"]: nr["display_name"] for nr in await conn.fetch(
                "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", [r["poster_id"]])}
            card = _row_to_feed_card(r, ctx.member_id, names.get(r["poster_id"], ""), reason_key)
            card.sponsored = True
            sponsored_cards.append(card)
            break

    # [FR32] impressions: organic slots are organic even for a boosted item;
    # only the Sponsored slot counts as a boosted impression.
    organic_ids = [c.id for s in sections for c in s.items]
    await log_events(conn, "opportunity", organic_ids, "impression", "feed", set())
    await log_events(conn, "opportunity", [c.id for c in sponsored_cards], "impression", "feed", {c.id for c in sponsored_cards})

    return FeedResponse(sections=sections, enrichment_prompt=enrichment, sponsored=sponsored_cards)


# [Fix #5 — "See all" affordance] A single-section deep view, reusing the
# exact same hard-constraint/scoring logic as the main feed (same
# candidates()/scored_candidates() shape) but with a much higher limit and
# no cross-section de-duplication — there is only one section in this
# request, so nothing to de-duplicate against.
_SECTION_WHERE = {
    "for_you": ("o.required_capabilities && $2", "capabilities"),
    "explore": ("NOT (o.required_capabilities && $2)", "capabilities"),
    "near_you": ("o.location ILIKE '%' || $2 || '%'", "locality"),
    "community": ("o.source_segment = 'community'", None),
    "public": ("o.source_segment = 'public'", None),
}


async def list_opportunity_feed_section(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    section_key: str,
) -> list[OpportunityOut]:
    if section_key not in _SECTION_WHERE:
        return []
    member = await _member_profile(conn, ctx.member_id)
    where, param_source = _SECTION_WHERE[section_key]
    params = [list(member["capabilities"])] if param_source == "capabilities" else [member["locality"]] if param_source == "locality" else []

    rows = await conn.fetch(
        f"""SELECT o.* FROM vyapar_opportunities.opportunities o
            WHERE o.state = 'active'
              AND NOT o.distribution_limited
              AND NOT EXISTS (
                SELECT 1 FROM vyapar_opportunities.member_opportunity mo
                WHERE mo.opportunity_id = o.id AND mo.member_id = $1 AND mo.hidden_at IS NOT NULL
              )
              AND ({where})
            LIMIT 200""",
        ctx.member_id, *params,
    )
    scored = []
    for r in rows:
        distance = await _distance_km(conn, member, r)
        if r["work_mode"] == "on_site" and distance is not None and member["radius_km"] is not None and distance > member["radius_km"]:
            continue
        signals = _opportunity_signals(r, member, distance)
        keys = top_signal_keys(signals, limit=1)
        scored.append((score(signals), keys[0] if keys else "matchesFilters", r))
    scored.sort(key=lambda t: t[0], reverse=True)
    ordered = diversify([r for _, _, r in scored], lambda r: r["poster_id"], lambda r: r["type"])
    reason_by_id = {str(r["id"]): reason for _, reason, r in scored}
    poster_ids = {r["poster_id"] for r in ordered}
    names = {}
    if poster_ids:
        name_rows = await conn.fetch(
            "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", list(poster_ids)  # [FR18 bug fix, slice 7] members RLS blanked other posters' names
        )
        names = {nr["id"]: nr["display_name"] for nr in name_rows}
    return [
        _row_to_feed_card(r, ctx.member_id, names.get(r["poster_id"], ""), reason_by_id[str(r["id"])])
        for r in ordered
    ]


class WhyResponse(BaseModel):
    signals: list[str]  # i18n keys under ranking.signal.*
    gap: str | None = None
    gap_skills: str | None = None
    sponsored_note: str | None = None


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
    return WhyResponse(signals=keys, gap=gap, gap_skills=", ".join(sorted(missing)) if missing else None, sponsored_note=sponsored_note)


async def list_opportunity_feed_section_page(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None, section_key: str = "",
) -> Page[OpportunityOut]:
    """[Refactor A] Cursor-paged `list_opportunity_feed_section` — same rows, same order."""
    return paginate(await list_opportunity_feed_section(conn, ctx, section_key=section_key), limit, cursor, lang)
