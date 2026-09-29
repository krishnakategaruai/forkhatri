# [TR018/TR020/TR055] Opportunity Discover feed, "Why this?" and Activity —
# HTTP front door only. Rules and queries live in app/services/feed.py and
# app/services/activity.py (see their headers for the approach).
# [IMP-B] The feed and section routes take the same filter set
# (skills, q, type, work_mode, radius_km, availability, sort) — see
# FeedFilters in the service. `sort_by` is accepted as an alias of `sort`
# for symmetry with /v1/listings/search.
# Traces to: FR18, FR19, FR20, FR55, TR018, TR019, TR020, TR040, TR055, SP018, SP019, SP020, SP040
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES, ApiError
from app.identity import AuthzContext, resolve_authz_context
from app.services import activity as activity_svc
from app.services import feed as svc
from app.services.activity import ActivityResponse  # noqa: F401
from app.services.feed import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    FeedCard,
    FeedFilters,
    FeedResponse,
    WhyResponse,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(tags=["feed"], responses=ERROR_RESPONSES)

SortQuery = Literal["relevance", "distance", "freshness", "verified_first", "salary_high"]
AvailabilityQuery = Literal["now", "this_week", "later"]
TypeQuery = Literal["employment", "freelance", "local_service", "partnership", "training", "community"]
WorkModeQuery = Literal["on_site", "remote", "both"]


def feed_filters(
    # [Original-Vyapar upgrade, product-owner direction: "based on skills we
    # need list to be flown"] an explicit, member-controlled skill filter —
    # FR19's own capability_fit ranking signal already exists, this makes
    # it a real filter too, not just an invisible ranking input. Injected
    # into the ONE shared candidate query so every one of the 5 sections
    # is filtered identically, never a per-section special case.
    skills: str = Query(default="", description="Comma-separated capability slugs"),
    q: str | None = Query(default=None, max_length=200),
    type: TypeQuery | None = Query(default=None),
    work_mode: WorkModeQuery | None = Query(default=None),
    radius_km: int | None = Query(default=None, ge=1, le=500),
    availability: AvailabilityQuery | None = Query(default=None),
    sort: SortQuery = Query(default="relevance"),
    sort_by: SortQuery | None = Query(default=None, description="Alias of sort"),
    # [FE2 — Discover filters redesign] additive
    types: str = Query(default="", description="Comma-separated kinds (any of); `type` still accepts one"),
    pay_kind: Literal["monthly", "project"] | None = Query(default=None, description="monthly = job salary; project = project or service budget"),
    pay_min_paise: int | None = Query(default=None, ge=0),
    pay_max_paise: int | None = Query(default=None, ge=0),
    posted_within: Literal["today", "week", "month"] | None = Query(default=None),
    shift: Literal["day", "night", "flexible"] | None = Query(default=None),
    experience: Literal["fresher", "1", "3"] | None = Query(default=None, description="The member's own experience"),
    verified_only: bool = Query(default=False),
    segment: Literal["community", "public"] | None = Query(default=None),
) -> FeedFilters:
    return FeedFilters.from_query(
        skills=skills, q=q, type=type, work_mode=work_mode, radius_km=radius_km, availability=availability, sort=sort, sort_by=sort_by,
        types=types, pay_kind=pay_kind, pay_min_paise=pay_min_paise, pay_max_paise=pay_max_paise, posted_within=posted_within,
        shift=shift, experience=experience, verified_only=verified_only, segment=segment,
    )


def viewer_position(
    lang: Locale,
    lat: float | None = Query(default=None, ge=-90, le=90, description="Viewer's current latitude (Use my location). Distance and radius only; never stored."),
    lng: float | None = Query(default=None, ge=-180, le=180, description="Viewer's current longitude; send together with lat."),
) -> svc.ViewerPosition:
    """[IMP-B] Optional per-request position override: both or neither."""
    if (lat is None) != (lng is None):
        raise ApiError(422, "discover.error.positionIncomplete", lang, error_code="position_incomplete")
    return (lat, lng) if lat is not None else None


@router.get("/v1/opportunities/feed/results", response_model=svc.ResultsResponse, operation_id="listOpportunityResults",
            summary="One flat ranked list for a search or filters, with its total and facet counts")
async def opportunity_results(
    lang: Locale,
    filters: FeedFilters = Depends(feed_filters),
    limit: int = Query(default=60, ge=1, le=100),
    position: svc.ViewerPosition = Depends(viewer_position),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> svc.ResultsResponse:
    return await svc.list_opportunity_results(conn, ctx, filters, lang=lang, limit=limit, position=position)


@router.get("/v1/opportunities/feed/rows", response_model=svc.RowsResponse, operation_id="listOpportunityRows",
            summary="The Discover home as themed rows (For you, Near you, categories, New today, ...)")
async def opportunity_rows(
    lang: Locale,
    position: svc.ViewerPosition = Depends(viewer_position),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> svc.RowsResponse:
    return await svc.list_opportunity_rows(conn, ctx, lang=lang, position=position)


@router.get("/v1/opportunities/feed", response_model=FeedResponse, operation_id="listOpportunityFeed", summary="Get the member's opportunity feed")
async def opportunity_feed(
    lang: Locale,
    filters: FeedFilters = Depends(feed_filters),
    position: svc.ViewerPosition = Depends(viewer_position),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> FeedResponse:
    return await svc.list_opportunity_feed(conn, ctx, filters=filters, lang=lang, position=position)


@router.get("/v1/opportunities/feed/section/{section_key}", response_model=list[FeedCard], operation_id="listOpportunityFeedSection", summary="Get all items in one feed section")
async def feed_section_full(
    section_key: str,
    lang: Locale,
    filters: FeedFilters = Depends(feed_filters),
    position: svc.ViewerPosition = Depends(viewer_position),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[FeedCard]:
    return await svc.list_opportunity_feed_section(conn, ctx, section_key=section_key, filters=filters, lang=lang, position=position)


@router.get("/v1/opportunities/feed/section/{section_key}/page", response_model=Page[FeedCard], operation_id="listOpportunityFeedSectionPage", summary="Get one feed section, one page at a time")
async def list_opportunity_feed_section_page(
    section_key: str,
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    filters: FeedFilters = Depends(feed_filters),
    position: svc.ViewerPosition = Depends(viewer_position),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> Page[FeedCard]:
    return await svc.list_opportunity_feed_section_page(conn, ctx, lang, limit=limit, cursor=cursor, section_key=section_key, filters=filters, position=position)


@router.get("/v1/opportunities/{opportunity_id}/why", response_model=WhyResponse, operation_id="getOpportunityWhy", summary="Explain why an opportunity is shown to the member")
async def why_this(
    opportunity_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> WhyResponse:
    return await svc.get_opportunity_why(conn, ctx, opportunity_id=opportunity_id)


@router.get("/v1/activity", response_model=ActivityResponse, operation_id="getActivity", summary="Get the member's activity (saved, applied, posted, received)")
async def get_activity(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ActivityResponse:
    return await activity_svc.get_activity(conn, ctx)
