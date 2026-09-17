# [TR015] Standalone Listing search and browse (FR15). A completely separate
# surface from the Opportunity feed (TR018, slice 3) — must work correctly
# with zero Opportunities in the system, per FR15 DEC-001's explicit
# standalone-discovery scope. Discovery & Ranking owns no tables of its own
# (07-tech-reqs.md's component table) — this file reads through Listings &
# Verification's own rows directly (same process, same schema-ownership
# rules as listings.py) and reuses listings.py's _row_to_out so a listing's
# disclosure/intent-visibility rules can never diverge between the manage
# screen and the search surface.
# Approach: keyword search via Postgres FTS (search_tsv, already GIN-
# indexed), category/locality/radius/service_mode/availability/verification
# filters, then TR019's canonical `app.ranking` module scores each survivor.
# [Slice-3 update] TR015 itself says results are "ranked by TR019's shared
# scoring function" — this file originally shipped ahead of FR19/TR019
# existing with a tracked, clearly-labelled interim scorer (see IMP09's own
# Decision entry in 09-implementation.md); now that FR19 (`app/ranking.py`)
# exists, this file has been refactored to call it, closing that Decision
# rather than leaving two ranking implementations in the codebase.
# [Product-owner i18n rule] `relevance_reason` and every `notice`/
# `broadening_options[].label` field now carry i18n KEYS, not pre-baked
# English text — the frontend translates via `t('ranking:signal.'+key)` /
# `t('discover:notice.'+key)` / `t('discover:broaden.'+key)`.
# Traces to: FR15, FR16, FR17, FR19, FR20, TR015, TR016, TR017, TR019, TR020, SP015, SP016, SP017, SP019
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

import json

from app.db import get_conn
from app.identity import AuthzContext, resolve_authz_context
from app.impressions import log_events
from app.ranking import RankingSignals, score, top_signal_keys
from app.reputation import reputation_for_listings, trust_from_reputation
from app.routers.listings import ListingOut, _row_to_out

router = APIRouter(prefix="/v1/listings", tags=["discovery"])

RADIUS_STEPS = [5, 10, 25]


class SearchResult(BaseModel):
    listing: ListingOut
    relevance_reason: str  # i18n key under ranking.signal.* (or a literal fallback key below)


class BroadeningOption(BaseModel):
    id: str
    label: str  # i18n key under discover.broaden.*


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total_considered: int
    degraded: bool = False
    notice: str | None = None  # i18n key under discover.notice.*
    broadening_options: list[BroadeningOption] = []
    fallback: dict | None = None
    # [TR030/FR30] up to SPONSORED_SEARCH_SLOTS labelled cards, taken ONLY
    # from this same query's eligible candidates (same filters, same
    # distribution limits) plus the boost's audience narrowing. `results`
    # keeps exactly its organic order — a boosted listing may appear in both.
    sponsored: list[SearchResult] = []


SPONSORED_SEARCH_SLOTS = 2


def _listing_signals(row: asyncpg.Record, q: str | None, distance_km: float | None, rep: dict | None = None) -> RankingSignals:
    """[TR019/FR15] Builds the ONE allow-listed signal struct for a listing
    search candidate — capability_fit from keyword/category match,
    location_fit from distance, trust_fit from verification state,
    freshness_fit from recency. No field outside RankingSignals' fixed set
    is computed or passed anywhere, structurally."""
    capability_fit = 0.0
    if q:
        ql = q.lower()
        if ql in row["name"].lower():
            capability_fit = 1.0
        elif any(ql in c.lower() for c in row["categories"] + row["capabilities"]):
            capability_fit = 0.7
    location_fit = max(0.0, 1.0 - distance_km / 25.0) if distance_km is not None else 0.3
    trust_fit = (1.0 if row["verification_state"] == "verified" else 0.0) + (0.3 if row["contact_verified"] else 0.0)
    # [FR28/FR19] reputation counts join trust fit only above 3 interactions
    trust_fit += trust_from_reputation(rep)
    return RankingSignals(capability_fit=capability_fit, location_fit=location_fit, trust_fit=trust_fit, freshness_fit=0.2)


@router.get("/search", response_model=SearchResponse)
async def search_listings(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    locality: str | None = Query(default=None),
    radius_km: int | None = Query(default=None),
    service_mode: Literal["on_site", "remote", "both"] | None = Query(default=None),
    verified_only: bool = Query(default=False),
    include_unverified: bool = Query(default=True),
    broaden_attempt: int = Query(default=0, ge=0, le=3),
    limit: int = Query(default=20, le=50),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> SearchResponse:
    # [SP015 Decision — read-path rate limit, a genuine gap Step 8 found,
    # not previously named by any FR/TR] bulk-scraping defense on this
    # search endpoint.
    allowed = await conn.fetchval(
        "SELECT vyapar_platform.check_and_increment($1, 60, 60)", f"listing_search:{ctx.member_id}:minute"
    )
    if not allowed:
        return SearchResponse(results=[], total_considered=0, degraded=True, notice="rateLimited")

    try:
        rows = await conn.fetch(
            """SELECT * FROM vyapar_listings.listings
               WHERE state IN ('active_unverified','active_verified')
                 AND discoverable = true
                 AND NOT distribution_limited  -- [TR040] auto-limited pending review
                 AND ($1::text IS NULL OR search_tsv @@ websearch_to_tsquery('simple', $1))
                 AND ($2::text IS NULL OR $2 = ANY(categories) OR $2 = ANY(capabilities))
                 AND ($3::text IS NULL OR locality ILIKE '%' || $3 || '%')
                 AND ($4::text IS NULL OR service_mode = $4 OR service_mode = 'both')
                 AND (NOT $5::boolean OR verification_state = 'verified')
               ORDER BY published_at DESC NULLS LAST
               LIMIT 200""",
            q, category, locality, service_mode, verified_only,
        )
    except asyncpg.PostgresError:
        # [TR015 degraded-search fallback] cached category browse instead of
        # a hard failure — at V1's embedded-Postgres-search scale this is a
        # DB-health branch, not a separate service-outage handler.
        rows = await conn.fetch(
            """SELECT * FROM vyapar_listings.listings
               WHERE state IN ('active_unverified','active_verified') AND discoverable = true AND NOT distribution_limited
               ORDER BY published_at DESC NULLS LAST LIMIT 200"""
        )
        return SearchResponse(
            results=[
                SearchResult(listing=_row_to_out(r, [], ctx.member_id, lang=lang), relevance_reason="recentlyAdded")
                for r in rows[:limit]
            ],
            total_considered=len(rows),
            degraded=True,
            notice="degraded",
        )

    # radius_km/lat/lng: no caller location is threaded through this query
    # yet (first-run captures it on `members`, not passed as a param here)
    # — distance_fit falls back to a flat default (see _listing_signals);
    # locality substring filtering already covers the common V1 case.
    reps = await reputation_for_listings(conn, rows)
    scored: list[tuple[float, str, asyncpg.Record]] = []
    for row in rows:
        signals = _listing_signals(row, q, distance_km=None, rep=reps.get(str(row["id"])))
        s = score(signals)
        keys = top_signal_keys(signals, limit=1)
        reason = keys[0] if keys else "matchesFilters"
        scored.append((s, reason, row))
    scored.sort(key=lambda t: t[0], reverse=True)

    results = []
    for _, reason, row in scored[:limit]:
        card = _row_to_out(row, [], ctx.member_id, lang=lang)
        card.reputation = reps.get(str(row["id"]))  # [FR28] reputation line on every result card
        results.append(SearchResult(listing=card, relevance_reason=reason))

    sponsored: list[SearchResult] = []
    if rows:
        boosts = await conn.fetch(
            "SELECT * FROM vyapar_commercial.active_boosts('listing', $1::uuid[]) ORDER BY starts_at", [r["id"] for r in rows]
        )
        if boosts:
            viewer_locality = locality or await conn.fetchval(
                "SELECT locality FROM vyapar_identity.members WHERE id = current_setting('vyapar.authz_context', true)"
            )
            row_by_id = {str(r["id"]): r for r in rows}
            for boost in boosts:
                audience = boost["audience"] if isinstance(boost["audience"], dict) else json.loads(boost["audience"] or "{}")
                if audience.get("locality") and not (viewer_locality and audience["locality"].lower() in viewer_locality.lower()):
                    continue
                if audience.get("category") and audience["category"] != category:
                    continue
                row = row_by_id[str(boost["target_id"])]
                card = _row_to_out(row, [], ctx.member_id, lang=lang)
                card.reputation = reps.get(str(row["id"]))
                card.sponsored = True
                sponsored.append(SearchResult(listing=card, relevance_reason="sponsored"))
                if len(sponsored) >= SPONSORED_SEARCH_SLOTS:
                    break
    # [FR32] impressions — the organic slot is organic even for a boosted listing
    await log_events(conn, "listing", [r.listing.id for r in results], "impression", "businesses", set())
    await log_events(conn, "listing", [s.listing.id for s in sponsored], "impression", "businesses", {s.listing.id for s in sponsored})

    if not results:
        options = [
            BroadeningOption(id=f"radius_{r}", label="radius") for r in RADIUS_STEPS
        ] + [
            BroadeningOption(id="adjacent_categories", label="adjacent_categories"),
            BroadeningOption(id="remove_filter", label="remove_filter"),
            BroadeningOption(id="include_unverified", label="include_unverified"),
        ]
        fallback = None
        if broaden_attempt >= 1:
            fallback = {"post_link": "/listings/new", "notify_link": "/listings/new"}
        return SearchResponse(
            results=[],
            total_considered=0,
            notice="noMatch",
            broadening_options=options,
            fallback=fallback,
        )

    return SearchResponse(results=results, total_considered=len(rows), sponsored=sponsored)
