# [TR018/TR020/TR055] Opportunity Discover feed, "Why this?" and Activity —
# HTTP front door only. Rules and queries live in app/services/feed.py and
# app/services/activity.py (see their headers for the approach).
# Traces to: FR18, FR19, FR20, FR55, TR018, TR019, TR020, TR040, TR055, SP018, SP019, SP020, SP040
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import activity as activity_svc
from app.services import feed as svc
from app.services.activity import ActivityResponse  # noqa: F401
from app.services.feed import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    FeedResponse,
    WhyResponse,
)
from app.services.opportunities import OpportunityOut
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(tags=["feed"], responses=ERROR_RESPONSES)


@router.get("/v1/opportunities/feed", response_model=FeedResponse, operation_id="listOpportunityFeed", summary="Get the member's opportunity feed")
async def opportunity_feed(
    # [Original-Vyapar upgrade, product-owner direction: "based on skills we
    # need list to be flown"] an explicit, member-controlled skill filter —
    # FR19's own capability_fit ranking signal already exists, this makes
    # it a real filter too, not just an invisible ranking input. Injected
    # into the ONE shared `candidates()` choke point below so every one of
    # the 5 sections is filtered identically, never a per-section special case.
    skills: str = Query(default=""),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> FeedResponse:
    return await svc.list_opportunity_feed(conn, ctx, skills=skills)


@router.get("/v1/opportunities/feed/section/{section_key}", response_model=list[OpportunityOut], operation_id="listOpportunityFeedSection", summary="Get all items in one feed section")
async def feed_section_full(
    section_key: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[OpportunityOut]:
    return await svc.list_opportunity_feed_section(conn, ctx, section_key=section_key)


@router.get("/v1/opportunities/feed/section/{section_key}/page", response_model=Page[OpportunityOut], operation_id="listOpportunityFeedSectionPage", summary="Get one feed section, one page at a time")
async def list_opportunity_feed_section_page(
    section_key: str,
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> Page[OpportunityOut]:
    return await svc.list_opportunity_feed_section_page(conn, ctx, lang, limit=limit, cursor=cursor, section_key=section_key)


@router.get("/v1/opportunities/{opportunity_id}/why", response_model=WhyResponse, operation_id="getOpportunityWhy", summary="Explain why an opportunity is shown to the member")
async def why_this(
    opportunity_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> WhyResponse:
    return await svc.get_opportunity_why(conn, ctx, opportunity_id=opportunity_id)


@router.get("/v1/activity", response_model=ActivityResponse, operation_id="getActivity", summary="Get the member's activity (saved, applied, posted, received)")
async def get_activity(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ActivityResponse:
    return await activity_svc.get_activity(conn, ctx)
