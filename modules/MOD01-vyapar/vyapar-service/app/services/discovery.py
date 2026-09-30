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

import json

import asyncpg
from pydantic import BaseModel

from app.identity import AuthzContext
from app.impressions import log_events
from app.ranking import RankingSignals, score, top_signal_keys
from app.reputation import badges_for_members, reputation_for_listings, trust_from_reputation
from app.taxonomy_cache import label_for, labels_for, term_for
from app.geo import place_words, resolve_place
from app.i18n import translate
from app.text_fold import contains_phrase, fold, prefix_hits, words
from app.trade_match import trade_matcher
from app.services.listings import ListingOut, _row_to_out


RADIUS_STEPS = [5, 10, 25]
PLACE_RADIUS_STEPS = [5, 15, 30]  # [IMP-B] around a typed place: start close, then widen


class SearchResult(BaseModel):
    listing: ListingOut
    relevance_reason: str  # i18n key under ranking.signal.* (or a literal fallback key below)
    distance_km: float | None = None  # [FR15] real, only when both caller and listing have coordinates


class BroadeningOption(BaseModel):
    id: str
    label: str  # i18n key under discover.broaden.*


class PlaceOut(BaseModel):
    name: str
    lat: float
    lng: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total_considered: int
    degraded: bool = False
    notice: str | None = None  # i18n key under discover.notice.* (widenedRadius | droppedPlace | anyWord added)
    # [IMP-B] the place the query was read as (distance is measured from it),
    # the radius in effect, what broadening happened, and the notice already
    # localized by the server.
    place: "PlaceOut | None" = None
    radius_km: float | None = None
    broadened: list[str] = []
    notice_text: str | None = None
    broadening_options: list[BroadeningOption] = []
    fallback: dict | None = None
    # [TR030/FR30] up to SPONSORED_SEARCH_SLOTS labelled cards, taken ONLY
    # from this same query's eligible candidates (same filters, same
    # distribution limits) plus the boost's audience narrowing. `results`
    # keeps exactly its organic order — a boosted listing may appear in both.
    sponsored: list[SearchResult] = []


SPONSORED_SEARCH_SLOTS = 2


class CategorySuggestion(BaseModel):
    slug: str
    label: str


class SearchSuggestionsOut(BaseModel):
    categories: list[CategorySuggestion]
    localities: list[str]


def _listing_signals(row: asyncpg.Record, q: str | None, distance_km: float | None, rep: dict | None = None) -> RankingSignals:
    """[TR019/FR15] Builds the ONE allow-listed signal struct for a listing
    search candidate — capability_fit from keyword/category match,
    location_fit from distance, trust_fit from verification state,
    freshness_fit from recency. No field outside RankingSignals' fixed set
    is computed or passed anywhere, structurally."""
    capability_fit = 0.0
    if q:
        ql = q.lower()
        if ql in row["name"].lower() or ql in (_business_name(row) or "").lower():  # [Backend A] person or business name
            capability_fit = 1.0
        elif any(ql in c.lower() for c in row["categories"] + row["capabilities"]):
            capability_fit = 0.7
    location_fit = max(0.0, 1.0 - distance_km / 25.0) if distance_km is not None else 0.3
    trust_fit = (1.0 if row["verification_state"] == "verified" else 0.0) + (0.3 if row["contact_verified"] else 0.0)
    # [FR28/FR19] reputation counts join trust fit only above 3 interactions
    trust_fit += trust_from_reputation(rep)
    return RankingSignals(capability_fit=capability_fit, location_fit=location_fit, trust_fit=trust_fit, freshness_fit=0.2)


async def search_listings(
    # [IMP-B, owner 2026-09-30: "searching 'krishna' or 'ameerpet' finds
    # nothing real"] Rewritten matching, same endpoint and response shape
    # (fields only added):
    #  * words are matched spelling-tolerantly (app/text_fold.py) as word
    #    prefixes against the business name, the owner's name, the skills and
    #    trade words (names in en/hi/te + aliases), categories, headline and
    #    description — every word must hit something; the field it hits sets
    #    its weight (name/owner 3, skills 2, headline 1.5, description 1);
    #  * a place named in the query or in `locality` becomes a DISTANCE filter
    #    around that place (app/geo.py), default 5 km, not a text match;
    #  * results rank by that relevance, then distance, then the FR19 score
    #    (`sort_by` still overrides the order, never the eligible set);
    #  * zero results broaden automatically, and say so: widen the radius
    #    around the place, then drop the place, then accept any of the words.
    # Structured filters (category, service mode, availability, verification,
    # skills — skills through the trade matcher, so a category or a trade word
    # works) stay hard eligibility, as FR19 requires.
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    q: str | None = None,
    category: str | None = None,
    locality: str | None = None,
    radius_km: int | None = None,
    service_mode: Literal["on_site", "remote", "both"] | None = None,
    availability: Literal["now", "this_week", "later"] | None = None,
    verified_only: bool = False,
    include_unverified: bool = True,
    sort_by: Literal["relevance", "distance", "freshness", "verified_first"] = "relevance",
    skills: str = "",
    broaden_attempt: int = 0,
    limit: int = 20,
) -> SearchResponse:
    # [SP015 Decision — read-path rate limit] bulk-scraping defense.
    allowed = await conn.fetchval(
        "SELECT vyapar_platform.check_and_increment($1, 60, 60)", f"listing_search:{ctx.member_id}:minute"
    )
    if not allowed:
        return SearchResponse(results=[], total_considered=0, degraded=True, notice="rateLimited")

    caller = await conn.fetchrow("SELECT lat, lng, locality FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    place = resolve_place(locality) or resolve_place(q)
    q_words = [w for w in words(q) if w not in (place_words(q) if place is not None and not resolve_place(locality) else set())]
    text_locality = locality if (locality and resolve_place(locality) is None) else None
    origin = (place.lat, place.lng) if place else ((caller["lat"], caller["lng"]) if caller and caller["lat"] is not None else (None, None))
    skill_list = [s for s in skills.split(",") if s]
    matcher = trade_matcher(skill_list) if skill_list else None

    try:
        rows = await conn.fetch(
            """SELECT *, vyapar_platform.distance_km($5::double precision, $6::double precision, lat, lng) AS distance_km
                 FROM vyapar_listings.listings
                WHERE state IN ('active_unverified','active_verified')
                  AND discoverable = true
                  AND NOT distribution_limited  -- [TR040] auto-limited pending review
                  AND ($1::text IS NULL OR $1 = ANY(categories) OR $1 = ANY(capabilities))
                  AND ($2::text IS NULL OR service_mode = $2 OR service_mode = 'both')
                  AND (NOT $3::boolean OR verification_state = 'verified')
                  AND ($4::text IS NULL OR availability = $4)
                  AND ($7::text IS NULL OR locality ILIKE '%' || $7 || '%')
                ORDER BY published_at DESC NULLS LAST
                LIMIT 2000""",
            category, service_mode, verified_only, availability, origin[0], origin[1], text_locality,
        )
    except asyncpg.PostgresError:
        rows = await conn.fetch(
            """SELECT * FROM vyapar_listings.listings
               WHERE state IN ('active_unverified','active_verified') AND discoverable = true AND NOT distribution_limited
               ORDER BY published_at DESC NULLS LAST LIMIT 200"""
        )
        return SearchResponse(
            results=[SearchResult(listing=_row_to_out(r, [], ctx.member_id, lang=lang), relevance_reason="recentlyAdded") for r in rows[:limit]],
            total_considered=len(rows), degraded=True, notice="degraded",
        )
    if matcher is not None:
        rows = [r for r in rows if matcher.matches(list(r["capabilities"]) + list(r["unmapped_labels"]), r["headline"] or r["name"])]

    owner_names = {}
    if rows:
        owner_names = {n["id"]: n["display_name"] for n in await conn.fetch(
            "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", list({r["owner_id"] for r in rows}))}

    def relevance(r, qw: list[str], require_all: bool) -> float | None:
        if not qw:
            return 0.0
        fields = (
            (3.0, [r["name"], _business_name(r), owner_names.get(r["owner_id"])]),
            (2.0, [skill_text(list(r["capabilities"]) + list(r["unmapped_labels"]) + list(r["categories"]), lang)]),
            (1.5, [r["headline"]]),
            (1.0, [r["description"], r["locality"]]),
        )
        total, hits = 0.0, 0
        for w in qw:
            best = 0.0
            for weight, texts in fields:
                if any(prefix_hits([w], t) for t in texts if t):
                    best = max(best, weight)
                    break
            if best:
                hits += 1
                total += best
        if require_all and hits < len(qw):
            return None
        if not hits:
            return None
        if any(contains_phrase(" ".join(qw), t) for t in (r["name"], _business_name(r), owner_names.get(r["owner_id"]))):
            total += 1.0
        return total

    def run(radius: float | None, use_place: bool, require_all: bool):
        out = []
        for r in rows:
            d = r["distance_km"] if "distance_km" in r.keys() else None
            if use_place and place is not None and radius is not None:
                if d is None:
                    if fold(place.name) not in fold(r["locality"]):
                        continue
                elif d > radius:
                    continue
            elif not use_place and place is None and radius_km is not None and d is not None and d > radius_km:
                continue  # the caller's own radius, around their own position
            rel = relevance(r, q_words, require_all)
            if rel is None:
                continue
            out.append((rel, r, d))
        return out

    broadened: list[str] = []
    radius = float(radius_km or PLACE_RADIUS_STEPS[0]) if place else None
    matched = run(radius, True, True)
    if not matched and place is not None:
        for step in PLACE_RADIUS_STEPS[1:]:
            if radius is not None and step <= radius:
                continue
            radius = float(step)
            matched = run(radius, True, True)
            if matched:
                broadened.append("widenedRadius")
                break
    if not matched and place is not None:
        matched = run(None, False, True)
        if matched:
            broadened.append("droppedPlace")
    if not matched and len(q_words) > 1:
        matched = run(radius, place is not None, False) or run(None, False, False)
        if matched:
            broadened.append("anyWord")

    reps = await reputation_for_listings(conn, [r for _, r, _ in matched])
    scored = []
    for rel, r, d in matched:
        signals = _listing_signals(r, q, distance_km=d, rep=reps.get(str(r["id"])))
        keys = top_signal_keys(signals, limit=1)
        scored.append((rel, score(signals), keys[0] if keys else "matchesFilters", r, d))
    if sort_by == "distance":
        scored.sort(key=lambda t: (t[4] is None, t[4] or 0, -t[0]))
    elif sort_by == "freshness":
        scored.sort(key=lambda t: t[3]["published_at"] or t[3]["created_at"], reverse=True)
    elif sort_by == "verified_first":
        scored.sort(key=lambda t: (t[3]["verification_state"] != "verified", -t[0], t[4] if t[4] is not None else 1e9))
    else:
        scored.sort(key=lambda t: (-t[0], t[4] is None, t[4] or 0, -t[1]))

    results = []
    page_rows = scored[:limit]
    owner_badges = await badges_for_members(conn, [row["owner_id"] for _, _, _, row, _ in page_rows], lang)
    for _, _, reason, row, d in page_rows:
        card = _row_to_out(row, [], ctx.member_id, lang=lang)
        card.reputation = reps.get(str(row["id"]))
        card.badges = [b.model_dump() for b in owner_badges.get(row["owner_id"], [])]
        results.append(SearchResult(listing=card, relevance_reason=reason, distance_km=round(d, 1) if d is not None else None))

    sponsored: list[SearchResult] = []
    eligible = [r for _, _, _, r, _ in scored]
    if eligible:
        boosts = await conn.fetch(
            "SELECT * FROM vyapar_commercial.active_boosts('listing', $1::uuid[]) ORDER BY starts_at", [r["id"] for r in eligible]
        )
        if boosts:
            viewer_locality = locality or (caller["locality"] if caller else None)
            row_by_id = {str(r["id"]): r for r in eligible}
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
    await log_events(conn, "listing", [r.listing.id for r in results], "impression", "businesses", set())
    await log_events(conn, "listing", [s.listing.id for s in sponsored], "impression", "businesses", {s.listing.id for s in sponsored})

    place_out = PlaceOut(name=place.name, lat=place.lat, lng=place.lng) if place else None
    notice_text = None
    if broadened:
        notice_text = translate(f"discover.notice.{broadened[-1]}", lang, km=int(radius or 0), place=place.name if place else "")
    if not results:
        options = [BroadeningOption(id=f"radius_{r}", label="radius") for r in RADIUS_STEPS] + [
            BroadeningOption(id="adjacent_categories", label="adjacent_categories"),
            BroadeningOption(id="remove_filter", label="remove_filter"),
            BroadeningOption(id="include_unverified", label="include_unverified"),
        ]
        fallback = {"post_link": "/listings/new", "notify_link": "/listings/new"} if broaden_attempt >= 1 else None
        return SearchResponse(results=[], total_considered=0, notice="noMatch", broadening_options=options, fallback=fallback,
                              place=place_out, radius_km=radius, notice_text=translate("discover.notice.noMatch", lang))
    return SearchResponse(results=results, total_considered=len(scored), sponsored=sponsored, place=place_out,
                          radius_km=radius if place else radius_km, broadened=broadened,
                          notice=f"{broadened[-1]}" if broadened else None, notice_text=notice_text)


def _business_name(r) -> str | None:
    return r["business_name"] if "business_name" in r.keys() else None


def skill_text(slugs: list[str], lang: str) -> str:
    """Every word a person might use for these skills: slug words, names in
    the three languages, aliases, and the reader's own label."""
    parts: list[str] = []
    for s in slugs:
        parts.append(str(s).replace("_", " "))
        term = term_for("capability", s) or term_for("category", s)
        if term is not None:
            parts.extend(term.names.values())
            parts.extend(term.aliases)
        else:
            parts.append(label_for(s, lang))
    return " ".join(parts)


async def get_search_suggestions(
    conn: asyncpg.Connection,
    lang: str,
) -> SearchSuggestionsOut:
    """[Real gap found via third critique pass, fixed here] IntentBar was
    parsing free text against a hardcoded 14-item English category/
    locality list — the exact class of gap first-run's own capability
    picker already fixed by fetching from the real taxonomy/data instead
    of a static array. Categories come from the same shared taxonomy
    every listing already uses (`labels_for`'s own source table); real
    localities come from actual seeded listings, not a fixed Hyderabad-area
    guess list, so this genuinely grows/shrinks with real member data.
    [Same-class live bug found and fixed here, self-caught via a project-
    wide grep after the coordinator's live Hindi/Telugu report on a
    different endpoint] this also hardcoded `labels_for(cat_slugs, "en")`
    — category names in IntentBar's own suggestion chips would have stayed
    in English in Hindi/Telugu exactly like the onboarding screen just
    fixed. Caught proactively via `grep -rn 'labels_for([^)]*"en"'` across
    the whole backend before being live-reported a second time."""
    cat_rows = await conn.fetch("SELECT slug FROM vyapar_listings.taxonomy_terms WHERE kind = 'category' AND status = 'active' ORDER BY slug")
    cat_slugs = [r["slug"] for r in cat_rows]
    cat_labels = labels_for(cat_slugs, lang)
    localities = await conn.fetch(
        "SELECT DISTINCT locality FROM vyapar_listings.listings WHERE state IN ('active_unverified','active_verified') AND discoverable = true ORDER BY locality LIMIT 50"
    )
    return SearchSuggestionsOut(
        categories=[CategorySuggestion(slug=s, label=l) for s, l in zip(cat_slugs, cat_labels)],
        localities=[r["locality"] for r in localities],
    )
