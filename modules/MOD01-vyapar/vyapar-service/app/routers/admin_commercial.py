# [TR049] Commercial administration and audit review (FR49).
# Approach — separation of powers by ROUTE ABSENCE, not by permission checks on
# routes that exist (SP049's canonical Critical item). This module deliberately
# contains **no route** that can:
#   * write `listings.verification_state` (verification is Trust & Safety's own
#     queue, IMP20), or
#   * change ranking weights — `vyapar_app` holds SELECT-only rights on
#     `vyapar_integration.config`, so even a future bug here cannot write one, or
#   * touch `moderation_cases` / safety decisions (IMP21's queue owns those).
# What it does contain:
#   * Product/price versioning that is INSERT-ONLY: a new price is a new
#     `(id, version)` row, so every historical order still reconstructs against
#     the exact version it was bought at. There is no update-product route at all.
#   * Promotions / entitlements / campaigns by state.
#   * Refund and credit processing with a mandatory reason code and a
#     server-side `amount <= order total - already refunded` guard, executed
#     through the Payment Bridge (never a direct gateway call from here).
#   * Ranking diagnostics that call the SAME scorer members are ranked by
#     (`app/ranking.py`'s `explain()`), showing the eligibility verdict and the
#     per-signal breakdown — and offering no override. A record excluded by a
#     hard constraint is reported as excluded, with the constraint named.
#   * Audit search by actor, object, action and date.
# Every action here writes an audit row attributed to the individual operator.
# Traces to: FR49, FR31, FR32, TR049, TR019, SP049
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.audit import audit, audit_out_of_band
from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.ranking import explain
from app.routers.commercial import _tax
from app.routers.discovery import _listing_signals
from app.routers.payments import refund_payment_order

router = APIRouter(prefix="/v1/admin/commercial", tags=["admin-commercial"])
audit_router = APIRouter(prefix="/v1/admin/audit", tags=["admin-audit"])


async def _require_commercial(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> None:
    perms = await conn.fetchval("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    if not perms or "commercial" not in perms:
        raise HTTPException(status_code=403, detail=translate("commercial.error.permissionRequired", lang))


@router.get("/products")
async def list_products(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    await _require_commercial(conn, ctx, lang)
    rows = await conn.fetch("SELECT * FROM vyapar_commercial.products ORDER BY kind, id, version DESC")
    return [
        {
            "id": r["id"], "version": r["version"], "kind": r["kind"], "name": r["name"], "description": r["description"],
            "duration_days": r["duration_days"], "billing": r["billing"], "price_paise": r["price_paise"],
            "tax_rate_bp": r["tax_rate_bp"], "tax_paise": _tax(r["price_paise"], r["tax_rate_bp"]),
            "capabilities": list(r["capabilities"]), "active": r["active"],
            "orders": await conn.fetchval(
                """SELECT (SELECT count(*) FROM vyapar_commercial.promotions p WHERE p.product_id = $1 AND p.product_version = $2)
                        + (SELECT count(*) FROM vyapar_commercial.entitlements e WHERE e.product_id = $1 AND e.product_version = $2)
                        + (SELECT count(*) FROM vyapar_commercial.campaigns c WHERE c.product_id = $1 AND c.product_version = $2)""",
                r["id"], r["version"],
            ),
        }
        for r in rows
    ]


class ProductVersionIn(BaseModel):
    id: str = Field(min_length=2, max_length=60)
    kind: Literal["boost", "workspace", "campaign"]
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    duration_days: int | None = Field(default=None, ge=1, le=730)
    billing: Literal["one_time", "monthly", "annual"]
    price_paise: int = Field(ge=0, le=100_000_000)
    tax_rate_bp: int = Field(default=1800, ge=0, le=5000)
    capabilities: list[str] = Field(default_factory=list)
    active: bool = True


@router.post("/products", status_code=201)
async def create_product_version(
    body: ProductVersionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    """[FR49/TR049] A price change is a NEW version — there is no route that
    updates an existing `(id, version)`, so orders stay reconstructible."""
    await _require_commercial(conn, ctx, lang)
    current = await conn.fetchval("SELECT max(version) FROM vyapar_commercial.products WHERE id = $1", body.id)
    existing_kind = await conn.fetchval("SELECT kind FROM vyapar_commercial.products WHERE id = $1 LIMIT 1", body.id)
    if existing_kind and existing_kind != body.kind:
        raise HTTPException(status_code=422, detail=translate("commercial.error.productKindMismatch", lang))
    version = (current or 0) + 1
    await conn.execute(
        """INSERT INTO vyapar_commercial.products
             (id, version, kind, name, description, duration_days, billing, price_paise, tax_rate_bp, capabilities, active)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)""",
        body.id, version, body.kind, body.name, body.description, body.duration_days, body.billing,
        body.price_paise, body.tax_rate_bp, body.capabilities, body.active,
    )
    await audit(conn, actor_id=ctx.member_id, action="product_version_created", object_kind="product",
                object_id=f"{body.id}:{version}", details={"price_paise": body.price_paise, "kind": body.kind})
    return {"id": body.id, "version": version, "price_paise": body.price_paise}


@router.get("/orders")
async def list_orders(
    lang: Locale,
    kind: Literal["promotion", "entitlement", "campaign"] = "promotion",
    state: str | None = None,
    limit: int = Query(default=50, le=200),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    await _require_commercial(conn, ctx, lang)
    table = {"promotion": "promotions", "entitlement": "entitlements", "campaign": "campaigns"}[kind]
    rows = await conn.fetch(
        f"""SELECT o.id, o.owner_id, o.state, o.product_id, o.product_version, o.created_at, o.payment_order_id,
                   po.state AS payment_state, po.amount_paise, po.tax_paise, po.refund_paise
            FROM vyapar_commercial.{table} o
            LEFT JOIN vyapar_payments.payment_orders po ON po.id = o.payment_order_id
            WHERE ($1::text IS NULL OR o.state = $1) ORDER BY o.created_at DESC LIMIT {int(limit)}""",
        state,
    )
    return [
        {
            "id": str(r["id"]), "kind": kind, "owner_id": r["owner_id"], "state": r["state"],
            "product": f"{r['product_id']} v{r['product_version']}", "created_at": r["created_at"].isoformat(),
            "payment_order_id": str(r["payment_order_id"]) if r["payment_order_id"] else None,
            "payment_state": r["payment_state"],
            "charged_paise": (r["amount_paise"] + r["tax_paise"]) if r["amount_paise"] is not None else None,
            "refunded_paise": r["refund_paise"],
        }
        for r in rows
    ]


class RefundIn(BaseModel):
    payment_order_id: str
    amount_paise: int = Field(gt=0)
    reason_code: str = Field(min_length=2, max_length=60)


@router.post("/refunds")
async def process_refund(
    body: RefundIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require_commercial(conn, ctx, lang)
    try:
        order = await conn.fetchrow("SELECT * FROM vyapar_payments.payment_orders WHERE id = $1", body.payment_order_id)
    except asyncpg.DataError:
        order = None
    if order is None:
        raise HTTPException(status_code=404, detail=translate("commercial.error.orderNotFound", lang))
    if order["state"] not in ("succeeded", "refunded"):
        raise HTTPException(status_code=400, detail=translate("commercial.error.notRefundable", lang))
    # [FR49] a refund may never exceed what remains of the order's value
    remaining = order["amount_paise"] + order["tax_paise"] - order["refund_paise"]
    if body.amount_paise > remaining:
        await audit_out_of_band(actor_id=ctx.member_id, action="refund_rejected", object_kind="payment_order",
                                object_id=str(order["id"]), reason_code=body.reason_code, outcome="rejected",
                                details={"requested_paise": body.amount_paise, "remaining_paise": remaining})
        raise HTTPException(
            status_code=422,
            detail=translate("commercial.error.refundExceedsOrder", lang, remaining=f"{remaining / 100:.2f}"),
        )
    refund_ref = await refund_payment_order(conn, order, body.amount_paise)
    if refund_ref is None:
        await audit(conn, actor_id=ctx.member_id, action="refund_failed", object_kind="payment_order",
                    object_id=order["id"], reason_code=body.reason_code, outcome="gateway_unavailable")
        return {"refunded": False, "notice": "gatewayUnavailable"}
    await conn.execute("SELECT set_config('vyapar.service_role', 'payment_webhook', true)")
    await conn.fetch(
        "SELECT * FROM vyapar_commercial.apply_payment_result($1, $2, $3, 'refunded')",
        order["kind"], order["ref_id"], order["id"],
    )
    await audit(conn, actor_id=ctx.member_id, action="refund_processed", object_kind="payment_order", object_id=order["id"],
                reason_code=body.reason_code, details={"amount_paise": body.amount_paise, "refund_ref": refund_ref})
    return {"refunded": True, "refund_ref": refund_ref, "amount_paise": body.amount_paise}


@router.get("/diagnostics/{target_kind}/{target_id}")
async def ranking_diagnostics(
    target_kind: Literal["listing", "opportunity"],
    target_id: str,
    lang: Locale,
    q: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    """[FR49] Why is this record where it is — and never an override. Hard
    constraints are reported as exclusions with the constraint named; the score
    breakdown comes from the same ranking function real results use."""
    await _require_commercial(conn, ctx, lang)
    exclusions: list[str] = []
    if target_kind == "listing":
        try:
            row = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", target_id)
        except asyncpg.DataError:
            row = None
        if row is None:
            raise HTTPException(status_code=404, detail=translate("commercial.error.notFound", lang))
        if row["state"] not in ("active_unverified", "active_verified"):
            exclusions.append("state_not_active")
        if not row["discoverable"]:
            exclusions.append("not_discoverable")
        if row["distribution_limited"]:
            exclusions.append("distribution_limited_pending_review")
        if row["verification_state"] not in ("verified", "expiring"):
            exclusions.append("unverified_excluded_from_verified_only_searches")
        breakdown = explain(_listing_signals(row, q, distance_km=None, rep=None))
        return {
            "target_kind": target_kind, "target_id": str(row["id"]), "title": row["name"],
            "eligible": not exclusions, "exclusions": exclusions, "score": breakdown,
            "note": "memberRelative" if q is None else None,
        }
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", target_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise HTTPException(status_code=404, detail=translate("commercial.error.notFound", lang))
    if row["state"] != "active":
        exclusions.append("state_not_active")
    if row["distribution_limited"]:
        exclusions.append("distribution_limited_pending_review")
    missing = {"title", "type", "location", "response_method"} - set(row["confirmed_fields"] or [])
    if missing & set(row["unconfirmed_fields"] or []):
        exclusions.append("material_fields_unconfirmed")
    # Opportunity relevance is scored per viewer (capability/location/timing fit
    # against THAT member), so there is no single global score to show here.
    return {
        "target_kind": target_kind, "target_id": str(row["id"]), "title": row["title"],
        "eligible": not exclusions, "exclusions": exclusions, "score": None, "note": "memberRelative",
    }


@audit_router.get("")
async def search_audit(
    lang: Locale,
    actor_id: str | None = None,
    object_kind: str | None = None,
    object_id: str | None = None,
    action: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, le=500),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    """[FR49] Audit search by actor, object, action and date. `audit_events` is
    operator-read-only at the RLS layer, so this is the only way to read it."""
    await _require_commercial(conn, ctx, lang)
    rows = await conn.fetch(
        f"""SELECT * FROM vyapar_integration.audit_events
            WHERE at > now() - make_interval(days => $1)
              AND ($2::text IS NULL OR actor_id = $2)
              AND ($3::text IS NULL OR object_kind = $3)
              AND ($4::text IS NULL OR object_id = $4)
              AND ($5::text IS NULL OR action = $5)
            ORDER BY at DESC LIMIT {int(limit)}""",
        days, actor_id, object_kind, object_id, action,
    )
    return [
        {
            "id": r["id"], "at": r["at"].isoformat(), "actor_id": r["actor_id"], "action": r["action"],
            "object_kind": r["object_kind"], "object_id": r["object_id"], "reason_code": r["reason_code"],
            "outcome": r["outcome"], "details": r["details"],
        }
        for r in rows
    ]
