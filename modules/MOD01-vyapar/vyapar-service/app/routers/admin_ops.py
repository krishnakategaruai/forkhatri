# [TR046/TR048/TR052] Marketplace health, the opportunity/stale queues,
# taxonomy management, dead letters and the MOD05 Dashboard Read Bridge —
# HTTP front door only. Rules and queries live in app/services/admin_ops.py.
# Traces to: FR46, FR48, FR52, TR046, TR048, TR052, SP046, SP048, SP052
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import admin_ops as svc
from app.services.admin_ops import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    BulkStaleIn,
    BulkStaleOut,
    DashboardSummaryOut,
    DeadLetterOut,
    MarketplaceHealthOut,
    OpportunityQueueItemOut,
    QueueDecisionIn,
    QueueDecisionOut,
    StaleItemOut,
    TaxonomyAddIn,
    TaxonomyCreatedOut,
    TaxonomyMergedOut,
    TaxonomyMergeIn,
    TaxonomyRenamedOut,
    TaxonomyRenameIn,
    TaxonomyTermOut,
)

router = APIRouter(tags=["admin-ops"], responses=ERROR_RESPONSES)
# [Known dev-only shortcut — see app/services/admin_ops.py] the MOD05 bridge
# still resolves a connection through get_conn(); it needs its own
# internal-service-key dependency once the real MOD05 integration is wired.
internal_router = APIRouter(prefix="/internal/v1", tags=["internal-bridges"], responses=ERROR_RESPONSES)


@router.get("/v1/admin/marketplace-health", response_model=MarketplaceHealthOut, operation_id="getMarketplaceHealth", summary="Get marketplace health metrics (admin)")
async def marketplace_health(
    lang: Locale,
    days: int = Query(default=30, ge=1, le=365),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> MarketplaceHealthOut:
    return await svc.get_marketplace_health(conn, ctx, lang, days=days)


@router.get("/v1/admin/opportunities-queue", response_model=list[OpportunityQueueItemOut], operation_id="listOpportunityReviewQueue", summary="List opportunities awaiting review (admin)")
async def opportunities_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[OpportunityQueueItemOut]:
    return await svc.list_opportunity_review_queue(conn, ctx, lang)


@router.post("/v1/admin/opportunities-queue/{opportunity_id}/decide", response_model=QueueDecisionOut, operation_id="decideOpportunityReview", summary="Decide an opportunity review (admin)")
async def decide_opportunity(
    opportunity_id: str,
    body: QueueDecisionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> QueueDecisionOut:
    return await svc.decide_opportunity_review(conn, ctx, lang, opportunity_id=opportunity_id, body=body)


@router.get("/v1/admin/stale-queue", response_model=list[StaleItemOut], operation_id="listStaleQueue", summary="List stale items (admin)")
async def stale_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[StaleItemOut]:
    return await svc.list_stale_queue(conn, ctx, lang)


@router.post("/v1/admin/stale-queue/bulk", response_model=BulkStaleOut, operation_id="bulkStaleAction", summary="Apply an action to stale items in bulk (admin)")
async def bulk_stale_action(
    body: BulkStaleIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> BulkStaleOut:
    return await svc.bulk_stale_action(conn, ctx, lang, body=body)


@router.get("/v1/admin/taxonomy", response_model=list[TaxonomyTermOut], operation_id="listTaxonomyTerms", summary="List taxonomy terms (admin)")
async def list_taxonomy(
    lang: Locale,
    kind: Literal["category", "capability"] | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[TaxonomyTermOut]:
    return await svc.list_taxonomy_terms(conn, ctx, lang, kind=kind)


@router.post("/v1/admin/taxonomy", status_code=201, response_model=TaxonomyCreatedOut, operation_id="createTaxonomyTerm", summary="Add a taxonomy term (admin)")
async def add_taxonomy_term(
    body: TaxonomyAddIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> TaxonomyCreatedOut:
    return await svc.create_taxonomy_term(conn, ctx, lang, body=body)


@router.post("/v1/admin/taxonomy/merge", response_model=TaxonomyMergedOut, operation_id="mergeTaxonomyTerms", summary="Merge taxonomy terms (admin)")
async def merge_taxonomy_terms(
    body: TaxonomyMergeIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> TaxonomyMergedOut:
    return await svc.merge_taxonomy_terms(conn, ctx, lang, body=body)


@router.post("/v1/admin/taxonomy/{term_id}/rename", response_model=TaxonomyRenamedOut, response_model_exclude_unset=True, operation_id="renameTaxonomyTerm", summary="Rename a taxonomy term (admin)")
async def rename_taxonomy_term(
    term_id: int,
    body: TaxonomyRenameIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> TaxonomyRenamedOut:
    return await svc.rename_taxonomy_term(conn, ctx, lang, term_id=term_id, body=body)


@router.get("/v1/admin/dead-letters", response_model=list[DeadLetterOut], operation_id="listDeadLetters", summary="List dead-lettered outbox events (admin)")
async def list_dead_letters(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[DeadLetterOut]:
    return await svc.list_dead_letters(conn, ctx, lang)


@internal_router.get("/dashboard-summary/{listing_id}", response_model=DashboardSummaryOut, operation_id="getDashboardSummary", summary="Get a listing's summary for the platform dashboard (internal)")
async def dashboard_summary(listing_id: str, conn: asyncpg.Connection = Depends(get_conn)) -> DashboardSummaryOut:
    return await svc.get_dashboard_summary(conn, listing_id=listing_id)
