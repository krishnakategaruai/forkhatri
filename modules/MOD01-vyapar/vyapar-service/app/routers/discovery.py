# [TR015] Standalone Listing search and browse (FR15) — HTTP front door
# only. Filters, ranking and sponsored slots live in
# app/services/discovery.py (see its header for the approach).
# Traces to: FR15, FR16, FR17, FR19, FR20, TR015, TR016, TR017, TR019, TR020, SP015, SP016, SP017, SP019
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import discovery as svc
from app.services.discovery import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    SearchResponse,
    SearchSuggestionsOut,
)

router = APIRouter(prefix="/v1/listings", tags=["discovery"], responses=ERROR_RESPONSES)


@router.get("/search", response_model=SearchResponse, operation_id="searchListings", summary="Search business and professional listings")
async def search_listings(
    lang: Locale,
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    locality: str | None = Query(default=None),
    radius_km: int | None = Query(default=None),
    service_mode: Literal["on_site", "remote", "both"] | None = Query(default=None),
    availability: Literal["now", "this_week", "later"] | None = Query(default=None),
    verified_only: bool = Query(default=False),
    include_unverified: bool = Query(default=True),
    # [Real regression found and fixed — coordinator's live testing + code
    # critique] FR15 names radius/service-mode/availability/verification/
    # freshness as real FILTERS and organic relevance as "text match,
    # category match, distance, verification, freshness -
    # configuration-weighted". The IntentBar free-text field had quietly
    # become the ONLY way to narrow results, with hardcoded English-keyword
    # parsing standing in for structured filtering — a regression, not a
    # simplification. `sort_by` restores an explicit, user-chosen order on
    # top of the same organic set; it never touches which rows are eligible
    # (that's still the hard WHERE clause below, per FR19's own
    # eligibility-before-ranking rule).
    sort_by: Literal["relevance", "distance", "freshness", "verified_first"] = Query(default="relevance"),
    # [Original-Vyapar upgrade, product-owner direction: "based on skills we
    # need list to be flown"] a real, explicit skill/capability filter —
    # array overlap against `listings.capabilities`, the same real taxonomy
    # slugs every listing already carries.
    skills: str = Query(default=""),
    broaden_attempt: int = Query(default=0, ge=0, le=3),
    limit: int = Query(default=20, le=50),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> SearchResponse:
    return await svc.search_listings(conn, ctx, lang, q=q, category=category, locality=locality, radius_km=radius_km, service_mode=service_mode, availability=availability, verified_only=verified_only, include_unverified=include_unverified, sort_by=sort_by, skills=skills, broaden_attempt=broaden_attempt, limit=limit)


@router.get("/search-suggestions", response_model=SearchSuggestionsOut, operation_id="getSearchSuggestions", summary="Get search suggestions for a partial query")
async def search_suggestions(lang: Locale, conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> SearchSuggestionsOut:
    return await svc.get_search_suggestions(conn, lang)
