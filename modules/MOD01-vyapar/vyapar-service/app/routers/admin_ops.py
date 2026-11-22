# [TR046/TR048/TR052] Marketplace health, the opportunity/stale queues,
# taxonomy management, dead letters and the MOD05 Dashboard Read Bridge —
# HTTP front door only. Rules and queries live in app/services/admin_ops.py.
# Traces to: FR46, FR48, FR52, TR046, TR048, TR052, SP046, SP048, SP052
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

import json

from app.db import get_conn, get_internal_conn
from app.services.privacy import ErasureOut
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.integrations.internal_auth import require_platform_service
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
# [IMP-ADMIN, 2026-09-29] The MOD05 bridge is a server-to-server call: it is
# authenticated by the platform service key (require_platform_service), not
# by a member session, and runs on a connection with no member context —
# dashboard_summary() is an allow-list SECURITY DEFINER function that answers
# only for public listings. (It used to resolve a member through get_conn(),
# so with the real ForKhatri provider it answered 401 to the platform, and in
# development it answered anyone.)
internal_router = APIRouter(
    prefix="/internal/v1", tags=["internal-bridges"], responses=ERROR_RESPONSES,
    dependencies=[Depends(require_platform_service)],
)


@router.get("/v1/admin/marketplace-health", response_model=MarketplaceHealthOut, operation_id="getMarketplaceHealth", summary="Get marketplace health metrics (admin)")
async def marketplace_health(
    lang: Locale,
    days: int = Query(default=30, ge=1, le=365),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> MarketplaceHealthOut:
    return await svc.get_marketplace_health(conn, ctx, lang, days=days)


@router.get("/v1/admin/opportunities-queue", response_model=list[OpportunityQueueItemOut], operation_id="listOpportunityReviewQueue", summary="List opportunities awaiting review (admin)")
async def opportunities_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[OpportunityQueueItemOut]:
    return await svc.list_opportunity_review_queue(conn, ctx, lang)


@router.post("/v1/admin/opportunities-queue/{opportunity_id}/decide", response_model=QueueDecisionOut, operation_id="decideOpportunityReview", summary="Decide an opportunity review (admin)")
async def decide_opportunity(
    opportunity_id: str,
    body: QueueDecisionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> QueueDecisionOut:
    return await svc.decide_opportunity_review(conn, ctx, lang, opportunity_id=opportunity_id, body=body)


@router.get("/v1/admin/stale-queue", response_model=list[StaleItemOut], operation_id="listStaleQueue", summary="List stale items (admin)")
async def stale_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[StaleItemOut]:
    return await svc.list_stale_queue(conn, ctx, lang)


@router.post("/v1/admin/stale-queue/bulk", response_model=BulkStaleOut, operation_id="bulkStaleAction", summary="Apply an action to stale items in bulk (admin)")
async def bulk_stale_action(
    body: BulkStaleIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> BulkStaleOut:
    return await svc.bulk_stale_action(conn, ctx, lang, body=body)


@router.get("/v1/admin/taxonomy", response_model=list[TaxonomyTermOut], operation_id="listTaxonomyTerms", summary="List taxonomy terms (admin)")
async def list_taxonomy(
    lang: Locale,
    kind: Literal["category", "capability"] | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[TaxonomyTermOut]:
    return await svc.list_taxonomy_terms(conn, ctx, lang, kind=kind)


@router.post("/v1/admin/taxonomy", status_code=201, response_model=TaxonomyCreatedOut, operation_id="createTaxonomyTerm", summary="Add a taxonomy term (admin)")
async def add_taxonomy_term(
    body: TaxonomyAddIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> TaxonomyCreatedOut:
    return await svc.create_taxonomy_term(conn, ctx, lang, body=body)


@router.post("/v1/admin/taxonomy/merge", response_model=TaxonomyMergedOut, operation_id="mergeTaxonomyTerms", summary="Merge taxonomy terms (admin)")
async def merge_taxonomy_terms(
    body: TaxonomyMergeIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> TaxonomyMergedOut:
    return await svc.merge_taxonomy_terms(conn, ctx, lang, body=body)


@router.post("/v1/admin/taxonomy/{term_id}/rename", response_model=TaxonomyRenamedOut, response_model_exclude_unset=True, operation_id="renameTaxonomyTerm", summary="Rename a taxonomy term (admin)")
async def rename_taxonomy_term(
    term_id: int,
    body: TaxonomyRenameIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> TaxonomyRenamedOut:
    return await svc.rename_taxonomy_term(conn, ctx, lang, term_id=term_id, body=body)


@router.get("/v1/admin/dead-letters", response_model=list[DeadLetterOut], operation_id="listDeadLetters", summary="List dead-lettered outbox events (admin)")
async def list_dead_letters(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[DeadLetterOut]:
    return await svc.list_dead_letters(conn, ctx, lang)


@internal_router.get("/dashboard-summary/{listing_id}", response_model=DashboardSummaryOut, operation_id="getDashboardSummary", summary="Get a listing's summary for the platform dashboard (internal)")
async def dashboard_summary(listing_id: str, conn: asyncpg.Connection = Depends(get_internal_conn)) -> DashboardSummaryOut:
    return await svc.get_dashboard_summary(conn, listing_id=listing_id)


@internal_router.post("/members/{member_id}/erase", response_model=ErasureOut, operation_id="eraseMemberInternal", summary="Erase everything Vyapar holds about a member (internal, idempotent)")
async def erase_member_internal(member_id: str) -> ErasureOut:
    # ForKhatri account deletion (docs/ParentApp/ACCOUNT-DELETION.md): the identity
    # service calls this with the service key. Own transaction so the files are
    # removed only after the database work has committed.
    from app.db import get_pool
    from app.services import privacy as privacy_svc

    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            try:
                res = await conn.fetchval("SELECT vyapar_identity.erase_member($1, $2)", member_id, privacy_svc.pseudonymize(member_id))
            except asyncpg.PostgresError as exc:
                if "operator_role_must_be_removed" in str(exc):
                    raise HTTPException(status_code=409, detail="operator_role_must_be_removed")
                raise
    out = json.loads(res) if isinstance(res, str) else res
    files = privacy_svc._remove_files(member_id, list(out.get("file_urls") or []))
    return ErasureOut(status=out["status"], deleted=out["deleted"], retained=out["retained"], files_removed=files)
