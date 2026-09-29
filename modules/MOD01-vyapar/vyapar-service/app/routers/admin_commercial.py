# [TR049] Commercial administration and audit review — HTTP front door
# only. Separation of powers is by operation ABSENCE: see the header of
# app/services/admin_commercial.py for what deliberately does not exist.
# Traces to: FR49, FR31, FR32, TR049, TR019, SP049
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import admin_commercial as svc
from app.services.admin_commercial import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    AdminProductOut,
    AuditEventOut,
    CommercialOrderOut,
    ProductVersionCreatedOut,
    ProductVersionIn,
    RankingDiagnosticsOut,
    RefundIn,
    RefundOut,
)

router = APIRouter(prefix="/v1/admin/commercial", tags=["admin-commercial"], responses=ERROR_RESPONSES)
audit_router = APIRouter(prefix="/v1/admin/audit", tags=["admin-audit"], responses=ERROR_RESPONSES)


@router.get("/products", response_model=list[AdminProductOut], operation_id="listCommercialProducts", summary="List commercial products (admin)")
async def list_products(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[AdminProductOut]:
    return await svc.list_commercial_products(conn, ctx, lang)


@router.post("/products", status_code=201, response_model=ProductVersionCreatedOut, operation_id="createCommercialProductVersion", summary="Create a new commercial product version (admin)")
async def create_product_version(
    body: ProductVersionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ProductVersionCreatedOut:
    return await svc.create_commercial_product_version(conn, ctx, lang, body=body)


@router.get("/orders", response_model=list[CommercialOrderOut], operation_id="listCommercialOrders", summary="List commercial orders (admin)")
async def list_orders(
    lang: Locale,
    kind: Literal["promotion", "entitlement", "campaign"] = "promotion",
    state: str | None = None,
    limit: int = Query(default=50, le=200),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[CommercialOrderOut]:
    return await svc.list_commercial_orders(conn, ctx, lang, kind=kind, state=state, limit=limit)


@router.post("/refunds", response_model=RefundOut, response_model_exclude_unset=True, operation_id="processRefund", summary="Process a refund (admin)")
async def process_refund(
    body: RefundIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> RefundOut:
    return await svc.process_refund(conn, ctx, lang, body=body)


@router.get("/diagnostics/{target_kind}/{target_id}", response_model=RankingDiagnosticsOut, operation_id="getRankingDiagnostics", summary="Get ranking diagnostics for an item (admin)")
async def ranking_diagnostics(
    target_kind: Literal["listing", "opportunity"],
    target_id: str,
    lang: Locale,
    q: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> RankingDiagnosticsOut:
    return await svc.get_ranking_diagnostics(conn, ctx, lang, target_kind=target_kind, target_id=target_id, q=q)


@audit_router.get("", response_model=list[AuditEventOut], operation_id="searchAuditLog", summary="Search the audit log (admin)")
async def search_audit(
    lang: Locale,
    actor_id: str | None = None,
    object_kind: str | None = None,
    object_id: str | None = None,
    action: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, le=500),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[AuditEventOut]:
    return await svc.search_audit_log(conn, ctx, lang, actor_id=actor_id, object_kind=object_kind, object_id=object_id, action=action, days=days, limit=limit)
