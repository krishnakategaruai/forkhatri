# [TR030/TR031/TR032/TR054] Boosts: options, draft, confirm, cancel, the
# performance report and operator reject — HTTP front door only. Rules,
# pricing, credit and lifecycle passes live in app/services/commercial.py.
# Traces to: FR30, FR31, FR32, FR54, TR030, TR031, TR032, TR054, SP030, SP031, SP032, SP054
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import commercial as svc
from app.services.commercial import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    ConfirmIn,
    PerformanceReportOut,
    PromotionCancelOut,
    PromotionCreatedOut,
    PromotionDetailOut,
    PromotionIn,
    PromotionOptionsOut,
    PromotionRejectOut,
    PromotionSummaryOut,
    PurchaseResultOut,
    RejectIn,
    TargetKind,
    run_commercial_lifecycle_pass,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(tags=["commercial"], responses=ERROR_RESPONSES)
admin_router = APIRouter(prefix="/v1/admin/promotions", tags=["admin-commercial"], responses=ERROR_RESPONSES)


@router.get("/v1/promotions/options", response_model=PromotionOptionsOut, operation_id="listPromotionOptions", summary="List promotion (boost) options")
async def boost_options(
    target_kind: TargetKind,
    target_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PromotionOptionsOut:
    return await svc.list_promotion_options(conn, ctx, lang, target_kind=target_kind, target_id=target_id)


@router.get("/v1/promotions/quote", response_model=svc.PromotionQuoteOut, operation_id="quoteCustomPromotion", summary="Price a custom-length boost")
async def quote_custom_promotion(
    days: int,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> svc.PromotionQuoteOut:
    return await svc.quote_custom_promotion(conn, ctx, lang, days=days)


@router.post("/v1/promotions", status_code=201, response_model=PromotionCreatedOut, operation_id="createPromotion", summary="Create a promotion draft")
async def create_promotion_draft(
    body: PromotionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PromotionCreatedOut:
    return await svc.create_promotion(conn, ctx, lang, body=body)


@router.post("/v1/promotions/{promotion_id}/confirm-purchase", response_model=PurchaseResultOut, response_model_exclude_unset=True, operation_id="confirmPromotionPurchase", summary="Confirm a promotion purchase")
async def confirm_purchase(
    promotion_id: str,
    body: ConfirmIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PurchaseResultOut:
    return await svc.confirm_promotion_purchase(conn, ctx, lang, promotion_id=promotion_id, body=body)


@router.get("/v1/promotions/mine", response_model=list[PromotionSummaryOut], operation_id="listMyPromotions", summary="List the member's promotions")
async def list_my_promotions(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[PromotionSummaryOut]:
    return await svc.list_my_promotions(conn, ctx)


@router.get("/v1/promotions/mine/page", response_model=Page[PromotionSummaryOut], operation_id="listMyPromotionsPage", summary="List the member's promotions, one page at a time")
async def list_my_promotions_page(
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> Page[PromotionSummaryOut]:
    return await svc.list_my_promotions_page(conn, ctx, lang, limit=limit, cursor=cursor)


@router.get("/v1/promotions/{promotion_id}", response_model=PromotionDetailOut, operation_id="getPromotion", summary="Get one promotion")
async def get_promotion(
    promotion_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PromotionDetailOut:
    return await svc.get_promotion(conn, ctx, lang, promotion_id=promotion_id)


@router.post("/v1/promotions/{promotion_id}/cancel", response_model=PromotionCancelOut, operation_id="cancelPromotion", summary="Cancel a promotion")
async def cancel_promotion(
    promotion_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PromotionCancelOut:
    return await svc.cancel_promotion(conn, ctx, lang, promotion_id=promotion_id)


@router.get("/v1/performance/{target_kind}/{target_id}", response_model=PerformanceReportOut, operation_id="getPerformanceReport", summary="Get the performance report for a listing or opportunity")
async def performance_report(
    target_kind: TargetKind,
    target_id: str,
    lang: Locale,
    promotion_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PerformanceReportOut:
    return await svc.get_performance_report(conn, ctx, lang, target_kind=target_kind, target_id=target_id, promotion_id=promotion_id, days=days)


@admin_router.post("/{promotion_id}/reject", response_model=PromotionRejectOut, operation_id="rejectPromotion", summary="Reject a promotion (admin)")
async def reject_promotion(
    promotion_id: str,
    body: RejectIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PromotionRejectOut:
    return await svc.reject_promotion(conn, ctx, lang, promotion_id=promotion_id, body=body)
