# [TR035] Community/Opportunity Campaigns — HTTP front door only. Package
# rules and the one shared boost-application path live in
# app/services/campaigns.py and app/services/commercial.py.
# Traces to: FR35, FR30, FR31, FR32, FR33, TR035, SP035
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import campaigns as svc
from app.services.campaigns import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    CampaignCreatedOut,
    CampaignIn,
    CampaignItemsStateIn,
    CampaignItemsStateOut,
    CampaignOptionsOut,
    CampaignOut,
    CampaignPurchaseOut,
    ConfirmIn,
)
from app.services.commercial import PerformanceReportOut

router = APIRouter(tags=["campaigns"], responses=ERROR_RESPONSES)


@router.get("/v1/campaigns/options", response_model=CampaignOptionsOut, operation_id="listCampaignOptions", summary="List campaign options")
async def campaign_options(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> CampaignOptionsOut:
    return await svc.list_campaign_options(conn, ctx, lang, listing_id=listing_id)


@router.post("/v1/campaigns", status_code=201, response_model=CampaignCreatedOut, operation_id="createCampaign", summary="Create a campaign")
async def create_campaign(
    body: CampaignIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> CampaignCreatedOut:
    return await svc.create_campaign(conn, ctx, lang, body=body)


@router.post("/v1/campaigns/{campaign_id}/confirm-purchase", response_model=CampaignPurchaseOut, response_model_exclude_unset=True, operation_id="confirmCampaignPurchase", summary="Confirm a campaign purchase")
async def confirm_campaign_purchase(
    campaign_id: str,
    body: ConfirmIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> CampaignPurchaseOut:
    return await svc.confirm_campaign_purchase(conn, ctx, lang, campaign_id=campaign_id, body=body)


@router.get("/v1/campaigns/{campaign_id}", response_model=CampaignOut, operation_id="getCampaign", summary="Get one campaign")
async def get_campaign(
    campaign_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> CampaignOut:
    return await svc.get_campaign(conn, ctx, lang, campaign_id=campaign_id)


@router.post("/v1/campaigns/{campaign_id}/items-state", response_model=CampaignItemsStateOut, operation_id="setCampaignItemsState", summary="Pause or resume a campaign's items")
async def set_campaign_items_state(
    campaign_id: str,
    body: CampaignItemsStateIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> CampaignItemsStateOut:
    return await svc.set_campaign_items_state(conn, ctx, lang, campaign_id=campaign_id, body=body)


@router.get("/v1/campaigns/{campaign_id}/report", response_model=PerformanceReportOut, operation_id="getCampaignReport", summary="Get a campaign's performance report")
async def campaign_report(
    campaign_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PerformanceReportOut:
    return await svc.get_campaign_report(conn, ctx, lang, campaign_id=campaign_id)
