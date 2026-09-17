# [TR030] Purchase a Boost (FR30). [TR031] Promotion lifecycle, price
# versioning, cancellation and credit (FR31). [TR032] Provider performance
# reporting without unsupported claims (FR32). [TR054] Commercial disclosure
# (FR54 — boosts are one-time, so the renewal-reminder gate ships with FR33
# entitlements in slice 9).
# Approach:
#  - Eligibility (TR030): a listing must be Active and verified (checked via
#    Listings' own `is_active()`); an opportunity must be Active and its
#    poster must own an Active-Verified listing (`has_verified_listing()`).
#    Unverified => "verify first" with a route to verification.
#  - Two structurally separate steps (TR054): POST /v1/promotions creates a
#    Draft that charges nothing; POST .../confirm-purchase with
#    `confirmed: true` (a literal the client must send) is the only route that
#    can start a payment. No confirm, no order.
#  - The product row (id + version) and its price/tax are snapshotted onto the
#    promotion, so every order is reconstructible against the exact price in
#    force (TR031). Price = products.price_paise, tax = tax_rate_bp.
#  - Credit (FR31 pro-rata credit, FR30 auto-credit on suspension) is real
#    money-equivalent: it is applied to the next purchase at confirm time and
#    consumed from the source promotions, oldest first; a fully covered
#    purchase activates without a gateway call.
#  - Gateway outage: the promotion stays Awaiting Payment and the response
#    says so (no exception, so the saved state isn't rolled back).
#  - Cancel: before payment => Cancelled; while Active => pro-rata credit of
#    what was paid. Operator Reject (safety) => full refund through the
#    Payment Bridge; a refund the gateway can't process stays Rejected with
#    the order still succeeded, which is what FR49's queue (slice 9) lists.
#  - Report (FR32): five separate counts for the period (impressions, detail
#    views, saves, enquiries, confirmed outcomes), boosted vs organic when a
#    boost ran, the split suppressed below 10 impressions. The response model
#    has no field for a projection, ROI or causal claim, and no member data.
#  - Organic ranking is untouched: `RankingSignals` has no paid field;
#    Sponsored is an extra labelled slot (discovery.py / feed.py).
# Reference (Upwork + WorkIndia lens): Upwork's Boosted profiles/proposals sit
# in top slots with a visible "Boosted" label while organic results stay as
# they are; WorkIndia's "Boost" sends the job to more ELIGIBLE candidates.
# Vyapar takes both halves — a labelled extra slot, only inside the audience
# the item already fits — and rejects Upwork's auction bidding (FR30 uses
# fixed, disclosed prices and "never pay-to-win").
# Traces to: FR30, FR31, FR32, FR54, TR030, TR031, TR032, TR054, SP030, SP031, SP032, SP054
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import get_conn, get_pool
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.notifications import notify_member
from app.routers.listings import has_verified_listing, is_active
from app.routers.payments import GatewayUnavailable, create_payment_order, refund_payment_order

router = APIRouter(tags=["commercial"])
admin_router = APIRouter(prefix="/v1/admin/promotions", tags=["admin-commercial"])

TargetKind = Literal["listing", "opportunity"]
REPORT_KINDS = ("impression", "view", "save", "enquiry", "outcome")
MIN_IMPRESSIONS_TO_COMPARE = 10


def _tax(price_paise: int, tax_rate_bp: int) -> int:
    return (price_paise * tax_rate_bp + 5000) // 10000


async def _eligible_target(conn: asyncpg.Connection, kind: str, target_id: str, member_id: str) -> tuple[dict | None, str | None]:
    """Returns (target summary, ineligibility reason key or None)."""
    if kind == "listing":
        try:
            row = await conn.fetchrow(
                "SELECT id, owner_id, name, state, verification_state, locality, categories FROM vyapar_listings.listings WHERE id = $1", target_id
            )
        except asyncpg.DataError:
            return None, "notFound"
        if row is None:
            return None, "notFound"
        target = {"id": str(row["id"]), "title": row["name"], "locality": row["locality"], "categories": list(row["categories"])}
        if row["owner_id"] != member_id:
            return target, "notOwner"
        active = await is_active(conn, target_id)
        if active is None:
            return target, "notActive"
        if active["verification_state"] not in ("verified", "expiring"):
            return target, "verifyFirst"
        return target, None
    try:
        row = await conn.fetchrow(
            "SELECT id, poster_id, title, state, location, type FROM vyapar_opportunities.opportunities WHERE id = $1", target_id
        )
    except asyncpg.DataError:
        return None, "notFound"
    if row is None:
        return None, "notFound"
    target = {"id": str(row["id"]), "title": row["title"], "locality": row["location"], "categories": [row["type"]]}
    if row["poster_id"] != member_id:
        return target, "notOwner"
    if row["state"] != "active":
        return target, "notActive"
    if not await has_verified_listing(conn, member_id):
        return target, "verifyFirst"
    return target, None


async def products_for_kind(conn: asyncpg.Connection, kind: str) -> list[dict]:
    """[TR031/TR049] The latest ACTIVE version of each product of a kind.
    `products` is insert-only, so "latest version" is how a new price reaches
    buyers while every historical order still resolves to the exact version it
    was bought at. Shared by boosts (FR30), workspace plans (FR33) and
    campaign packages (FR35) — one price/tax computation, not three."""
    rows = await conn.fetch(
        "SELECT DISTINCT ON (id) * FROM vyapar_commercial.products WHERE kind = $1 AND active ORDER BY id, version DESC", kind
    )
    products = [
        {
            "id": r["id"], "version": r["version"], "duration_days": r["duration_days"], "price_paise": r["price_paise"],
            "tax_paise": _tax(r["price_paise"], r["tax_rate_bp"]),
            "total_paise": r["price_paise"] + _tax(r["price_paise"], r["tax_rate_bp"]),
            "billing": r["billing"],
            "capabilities": list(r["capabilities"]),
        }
        for r in rows
    ]
    return sorted(products, key=lambda p: p["duration_days"] or 0)


async def _boost_products(conn: asyncpg.Connection) -> list[dict]:
    return await products_for_kind(conn, "boost")


async def _available_credit(conn: asyncpg.Connection, member_id: str, exclude_id=None) -> int:
    return await conn.fetchval(
        "SELECT coalesce(sum(credit_paise), 0) FROM vyapar_commercial.promotions WHERE owner_id = $1 AND ($2::uuid IS NULL OR id <> $2)",
        member_id, exclude_id,
    )


async def _history(
    conn: asyncpg.Connection, order_id, from_state: str | None, to_state: str, reason: str, order_kind: str = "promotion"
) -> None:
    """[FR31] One state-history writer for every commercial order kind. The
    `order_kind` is not cosmetic: `commercial_order_history`'s RLS policy
    resolves the owner through THAT kind's table, so a mislabelled row is
    rejected outright (found live — an entitlement row written as 'promotion'
    failed the policy)."""
    await conn.execute(
        "INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason) VALUES ($5, $1, $2, $3, $4)",
        order_id, from_state, to_state, reason, order_kind,
    )


@router.get("/v1/promotions/options")
async def boost_options(
    target_kind: TargetKind,
    target_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    target, reason = await _eligible_target(conn, target_kind, target_id, ctx.member_id)
    if target is None:
        raise HTTPException(status_code=404, detail=translate("commercial.error.notFound", lang))
    return {
        "eligible": reason is None,
        "reason": reason,
        "target_title": target["title"],
        "audience": {"locality": target["locality"], "categories": target["categories"]},
        "products": await _boost_products(conn) if reason is None else [],
        "credit_available_paise": await _available_credit(conn, ctx.member_id),
    }


class PromotionIn(BaseModel):
    target_kind: TargetKind
    target_id: str
    product_id: str
    audience_locality: str | None = Field(default=None, max_length=120)
    audience_category: str | None = Field(default=None, max_length=120)


@router.post("/v1/promotions", status_code=201)
async def create_promotion_draft(
    body: PromotionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    target, reason = await _eligible_target(conn, body.target_kind, body.target_id, ctx.member_id)
    if target is None:
        raise HTTPException(status_code=404, detail=translate("commercial.error.notFound", lang))
    if reason:
        raise HTTPException(status_code=400, detail=translate(f"commercial.error.{reason}", lang))
    product = next((p for p in await _boost_products(conn) if p["id"] == body.product_id), None)
    if product is None:
        raise HTTPException(status_code=422, detail=translate("commercial.error.productNotFound", lang))
    # [FR30] audience narrowing stays INSIDE the item's own eligible audience
    if body.audience_locality and body.audience_locality != target["locality"]:
        raise HTTPException(status_code=422, detail=translate("commercial.error.invalidAudience", lang))
    if body.audience_category and body.audience_category not in target["categories"]:
        raise HTTPException(status_code=422, detail=translate("commercial.error.invalidAudience", lang))
    audience = {k: v for k, v in {"locality": body.audience_locality, "category": body.audience_category}.items() if v}
    import json

    row = await conn.fetchrow(
        """INSERT INTO vyapar_commercial.promotions
             (owner_id, target_kind, target_id, product_id, product_version, price_paise, tax_paise, audience, state)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, 'draft') RETURNING id""",
        ctx.member_id, body.target_kind, body.target_id, product["id"], product["version"], product["price_paise"],
        product["tax_paise"], json.dumps(audience),
    )
    await _history(conn, row["id"], None, "draft", "created")
    return {"id": str(row["id"]), "state": "draft"}


class ConfirmIn(BaseModel):
    confirmed: Literal[True]  # [TR054] the disclosure screen's explicit confirmation — no default


async def _own_promotion(conn: asyncpg.Connection, promotion_id: str, member_id: str, lang: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_commercial.promotions WHERE id = $1 AND owner_id = $2", promotion_id, member_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise HTTPException(status_code=404, detail=translate("commercial.error.promotionNotFound", lang))
    return row


@router.post("/v1/promotions/{promotion_id}/confirm-purchase")
async def confirm_purchase(
    promotion_id: str,
    body: ConfirmIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    promo = await _own_promotion(conn, promotion_id, ctx.member_id, lang)
    if promo["state"] not in ("draft", "awaiting_payment"):
        raise HTTPException(status_code=400, detail=translate("commercial.error.invalidTransition", lang))
    _, reason = await _eligible_target(conn, promo["target_kind"], str(promo["target_id"]), ctx.member_id)
    if reason:  # eligibility is re-checked at purchase time, not only at draft
        raise HTTPException(status_code=400, detail=translate(f"commercial.error.{reason}", lang))

    total = promo["price_paise"] + promo["tax_paise"]
    if promo["state"] == "draft":
        remaining, applied = total, 0
        sources = await conn.fetch(
            "SELECT id, credit_paise FROM vyapar_commercial.promotions WHERE owner_id = $1 AND credit_paise > 0 AND id <> $2 ORDER BY updated_at",
            ctx.member_id, promo["id"],
        )
        for source in sources:
            if remaining == 0:
                break
            take = min(source["credit_paise"], remaining)
            await conn.execute("UPDATE vyapar_commercial.promotions SET credit_paise = credit_paise - $2, updated_at = now() WHERE id = $1", source["id"], take)
            remaining -= take
            applied += take
        if applied:
            await _history(conn, promo["id"], "draft", "draft", f"credit_applied:{applied}")
        charge = remaining
    else:  # retry within the 24-hour window: same amount as the first attempt
        last = await conn.fetchrow(
            "SELECT amount_paise, tax_paise FROM vyapar_payments.payment_orders WHERE ref_id = $1 AND member_id = $2 ORDER BY created_at DESC LIMIT 1",
            promo["id"], ctx.member_id,
        )
        charge = (last["amount_paise"] + last["tax_paise"]) if last else total

    if charge <= 0:
        product_days = await conn.fetchval(
            "SELECT duration_days FROM vyapar_commercial.products WHERE id = $1 AND version = $2", promo["product_id"], promo["product_version"]
        )
        await conn.execute(
            """UPDATE vyapar_commercial.promotions SET state = 'active', starts_at = now(),
                 ends_at = now() + make_interval(days => $2), updated_at = now() WHERE id = $1""",
            promo["id"], product_days or 7,
        )
        await _history(conn, promo["id"], promo["state"], "active", "paid_with_credit")
        return {"state": "active", "checkout_url": None, "notice": None}

    if promo["state"] == "draft":
        await conn.execute("UPDATE vyapar_commercial.promotions SET state = 'awaiting_payment', updated_at = now() WHERE id = $1", promo["id"])
        await _history(conn, promo["id"], "draft", "awaiting_payment", "confirmed")
    else:
        await conn.execute("UPDATE vyapar_commercial.promotions SET updated_at = now() WHERE id = $1", promo["id"])

    tax_part = round(charge * promo["tax_paise"] / total) if total else 0
    try:
        order = await create_payment_order(
            conn, kind="promotion", ref_id=promo["id"], member_id=ctx.member_id,
            amount_paise=charge - tax_part, tax_paise=tax_part,
            description=f"Vyapar boost {promo['product_id']} v{promo['product_version']}",
            return_path=f"/promotions/{promo['id']}",
        )
    except GatewayUnavailable:
        return {"state": "awaiting_payment", "checkout_url": None, "notice": "gatewayUnavailable"}
    await conn.execute("UPDATE vyapar_commercial.promotions SET payment_order_id = $2 WHERE id = $1", promo["id"], order["id"])
    return {"state": "awaiting_payment", "checkout_url": order["checkout_url"], "payment_order_id": order["id"], "notice": None}


def _credit_preview(promo: asyncpg.Record) -> int:
    if promo["state"] != "active" or not promo["starts_at"] or not promo["ends_at"]:
        return 0
    now = datetime.now(timezone.utc)
    total_secs = (promo["ends_at"] - promo["starts_at"]).total_seconds()
    remaining = max(0.0, (promo["ends_at"] - now).total_seconds())
    return int((promo["price_paise"] + promo["tax_paise"]) * remaining / total_secs) if total_secs > 0 else 0


@router.get("/v1/promotions/mine")
async def list_my_promotions(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    rows = await conn.fetch(
        """SELECT p.id, p.target_kind, p.target_id, p.state, p.product_id, p.ends_at, p.created_at,
                  coalesce(l.name, o.title) AS target_title
           FROM vyapar_commercial.promotions p
           LEFT JOIN vyapar_listings.listings l ON p.target_kind = 'listing' AND l.id = p.target_id
           LEFT JOIN vyapar_opportunities.opportunities o ON p.target_kind = 'opportunity' AND o.id = p.target_id
           WHERE p.owner_id = $1 ORDER BY p.created_at DESC""",
        ctx.member_id,
    )
    return [
        {
            "id": str(r["id"]), "target_kind": r["target_kind"], "target_id": str(r["target_id"]), "target_title": r["target_title"],
            "state": r["state"], "product_id": r["product_id"], "ends_at": r["ends_at"].isoformat() if r["ends_at"] else None,
        }
        for r in rows
    ]


@router.get("/v1/promotions/{promotion_id}")
async def get_promotion(
    promotion_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    promo = await _own_promotion(conn, promotion_id, ctx.member_id, lang)
    target_title = await conn.fetchval(
        "SELECT name FROM vyapar_listings.listings WHERE id = $1" if promo["target_kind"] == "listing"
        else "SELECT title FROM vyapar_opportunities.opportunities WHERE id = $1",
        promo["target_id"],
    )
    duration = await conn.fetchval(
        "SELECT duration_days FROM vyapar_commercial.products WHERE id = $1 AND version = $2", promo["product_id"], promo["product_version"]
    )
    order = await conn.fetchrow(
        "SELECT id, state, amount_paise, tax_paise, gateway_payment_ref, refund_ref FROM vyapar_payments.payment_orders WHERE ref_id = $1 AND member_id = $2 ORDER BY created_at DESC LIMIT 1",
        promo["id"], ctx.member_id,
    )
    history = await conn.fetch(
        "SELECT from_state, to_state, reason, at FROM vyapar_commercial.commercial_order_history WHERE order_kind = 'promotion' AND order_id = $1 ORDER BY at, id",
        promo["id"],
    )
    credit_applied = sum(int(h["reason"].split(":")[1]) for h in history if h["reason"] and h["reason"].startswith("credit_applied:"))
    if promo["state"] in ("draft", "awaiting_payment"):
        cancel_preview = {"kind": "cancel", "amount_paise": 0}
    elif promo["state"] == "active":
        cancel_preview = {"kind": "credit", "amount_paise": _credit_preview(promo)}
    else:
        cancel_preview = None
    return {
        "id": str(promo["id"]), "target_kind": promo["target_kind"], "target_id": str(promo["target_id"]), "target_title": target_title,
        "state": promo["state"], "product_id": promo["product_id"], "product_version": promo["product_version"], "duration_days": duration,
        "price_paise": promo["price_paise"], "tax_paise": promo["tax_paise"], "credit_applied_paise": credit_applied,
        "charged_paise": (order["amount_paise"] + order["tax_paise"]) if order else 0,
        "credit_paise": promo["credit_paise"], "audience": promo["audience"] if isinstance(promo["audience"], dict) else None,
        "starts_at": promo["starts_at"].isoformat() if promo["starts_at"] else None,
        "ends_at": promo["ends_at"].isoformat() if promo["ends_at"] else None,
        "reject_reason": promo["reject_reason"],
        "payment_order_id": str(order["id"]) if order else None, "payment_state": order["state"] if order else None,
        "receipt_ref": order["gateway_payment_ref"] if order else None, "refund_ref": order["refund_ref"] if order else None,
        "cancel_preview": cancel_preview,
        "history": [{"from_state": h["from_state"], "to_state": h["to_state"], "reason": h["reason"], "at": h["at"].isoformat()} for h in history],
    }


@router.post("/v1/promotions/{promotion_id}/cancel")
async def cancel_promotion(
    promotion_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    promo = await _own_promotion(conn, promotion_id, ctx.member_id, lang)
    if promo["state"] in ("draft", "awaiting_payment"):
        await conn.execute("UPDATE vyapar_commercial.promotions SET state = 'cancelled', updated_at = now() WHERE id = $1", promo["id"])
        await _history(conn, promo["id"], promo["state"], "cancelled", "cancelled_by_owner")
        return {"state": "cancelled", "credit_paise": 0}
    if promo["state"] == "active":
        credit = _credit_preview(promo)
        await conn.execute(
            "UPDATE vyapar_commercial.promotions SET state = 'cancelled', ends_at = now(), credit_paise = credit_paise + $2, updated_at = now() WHERE id = $1",
            promo["id"], credit,
        )
        await _history(conn, promo["id"], "active", "cancelled", "cancelled_by_owner")
        return {"state": "cancelled", "credit_paise": credit}
    raise HTTPException(status_code=400, detail=translate("commercial.error.invalidTransition", lang))


@router.get("/v1/performance/{target_kind}/{target_id}")
async def performance_report(
    target_kind: TargetKind,
    target_id: str,
    lang: Locale,
    promotion_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    owner_sql = (
        "SELECT owner_id FROM vyapar_listings.listings WHERE id = $1" if target_kind == "listing"
        else "SELECT poster_id FROM vyapar_opportunities.opportunities WHERE id = $1"
    )
    try:
        owner = await conn.fetchval(owner_sql, target_id)
    except asyncpg.DataError:
        owner = None
    if owner != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("commercial.error.notFound", lang))
    now = datetime.now(timezone.utc)
    start, end = now - timedelta(days=days), now
    if promotion_id:
        promo = await _own_promotion(conn, promotion_id, ctx.member_id, lang)
        start = promo["starts_at"] or promo["created_at"]
        end = min(promo["ends_at"] or now, now)
    rows = await conn.fetch("SELECT * FROM vyapar_commercial.impressions_report($1, $2)", target_kind, target_id)
    counts = {k: {"boosted": 0, "organic": 0} for k in REPORT_KINDS}
    for r in rows:
        if start.date() <= r["day"] <= end.date() and r["kind"] in counts:
            counts[r["kind"]]["boosted" if r["sponsored"] else "organic"] += r["n"]
    impressions_total = counts["impression"]["boosted"] + counts["impression"]["organic"]
    boost_ran = bool(promotion_id) or any(c["boosted"] for c in counts.values())
    comparable = boost_ran and impressions_total >= MIN_IMPRESSIONS_TO_COMPARE
    return {
        "from": start.isoformat(), "to": end.isoformat(), "boost_ran": boost_ran, "comparable": comparable,
        "too_little_data": boost_ran and impressions_total < MIN_IMPRESSIONS_TO_COMPARE,
        "counts": [
            {
                "kind": k, "total": v["boosted"] + v["organic"],
                "boosted": v["boosted"] if comparable else None, "organic": v["organic"] if comparable else None,
            }
            for k, v in counts.items()
        ],
    }


class RejectIn(BaseModel):
    reason_code: str = Field(min_length=2, max_length=60)


@admin_router.post("/{promotion_id}/reject")
async def reject_promotion(
    promotion_id: str,
    body: RejectIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    perms = await conn.fetchval("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    if not perms or "commercial" not in perms:
        raise HTTPException(status_code=403, detail=translate("commercial.error.permissionRequired", lang))
    try:
        async with conn.transaction():
            row = await conn.fetchrow("SELECT * FROM vyapar_commercial.reject_promotion($1, $2)", promotion_id, body.reason_code)
    except asyncpg.DataError:
        raise HTTPException(status_code=404, detail=translate("commercial.error.promotionNotFound", lang))
    except asyncpg.RaiseError as exc:
        if "invalid_transition" in str(exc):
            raise HTTPException(status_code=400, detail=translate("commercial.error.invalidTransition", lang))
        raise HTTPException(status_code=404, detail=translate("commercial.error.promotionNotFound", lang))

    refunded = False
    order = None
    if row["payment_order_id"]:
        order = await conn.fetchrow("SELECT * FROM vyapar_payments.payment_orders WHERE id = $1", row["payment_order_id"])
    if order and order["state"] == "succeeded":
        refund_ref = await refund_payment_order(conn, order, order["amount_paise"] + order["tax_paise"] - order["refund_paise"])
        if refund_ref:
            await conn.execute("SELECT set_config('vyapar.service_role', 'payment_webhook', true)")
            await conn.fetch("SELECT * FROM vyapar_commercial.apply_payment_result('promotion', $1, $2, 'refunded')", promotion_id, order["id"])
            refunded = True
    await notify_member(
        conn, member_id=row["owner_id"], template="promotionRejected", link=f"/promotions/{promotion_id}",
        idempotency_key=f"promotion_rejected:{promotion_id}", key_params={"reason": f"trust_safety.reasonCode.{body.reason_code}"},
    )
    return {"state": "refunded" if refunded else "rejected", "refund_requested": order is not None and order["state"] == "succeeded"}


async def run_promotion_lifecycle_pass(pool: asyncpg.Pool) -> dict:
    """[FR30/FR31] 24-hour payment window, completion, Paused + credit."""
    counts = {"cancelled": 0, "completed": 0, "paused": 0}
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", get_settings().dispatcher_operator_member_id)
            rows = await conn.fetch("SELECT * FROM vyapar_commercial.run_promotion_lifecycle()")
            for r in rows:
                counts[r["to_state"]] = counts.get(r["to_state"], 0) + 1
                if r["to_state"] == "paused":
                    await notify_member(
                        conn, member_id=r["owner_id"], template="promotionPaused", link=f"/promotions/{r['promotion_id']}",
                        idempotency_key=f"promotion_paused:{r['promotion_id']}", params={"amount": f"₹{r['credit_paise'] / 100:.2f}"},
                    )
    return counts


# ---------------------------------------------------------------------------
# [TR035/SP035] The ONE boost-application function. Campaigns call this once
# per item rather than re-implementing boost mechanics — which is exactly the
# divergence IA035/SP035 name: a campaign path that quietly skips FR30's
# verified-only rule or its organic-rank guarantee. Everything that creates a
# promotion goes through here, so those guarantees hold uniformly.
# Traces to: FR30, FR35, TR030, TR035, SP035
# ---------------------------------------------------------------------------
async def create_item_promotion(
    conn: asyncpg.Connection,
    *,
    owner_id: str,
    target_kind: str,
    target_id: str,
    product_id: str,
    product_version: int,
    price_paise: int,
    tax_paise: int,
    audience: dict | None = None,
    campaign_id=None,
    state: str = "draft",
) -> asyncpg.Record | None:
    """Returns the new promotion row, or None when the item fails FR30
    eligibility (the caller reports which items were rejected and why)."""
    import json

    target, reason = await _eligible_target(conn, target_kind, str(target_id), owner_id)
    if target is None or reason:
        return None
    row = await conn.fetchrow(
        """INSERT INTO vyapar_commercial.promotions
             (owner_id, target_kind, target_id, product_id, product_version, price_paise, tax_paise, audience, state, campaign_id)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10) RETURNING *""",
        owner_id, target_kind, target_id, product_id, product_version, price_paise, tax_paise,
        json.dumps(audience or {}), state, campaign_id,
    )
    await _history(conn, row["id"], None, state, "created" if campaign_id is None else "campaign_item")
    return row


async def run_commercial_lifecycle_pass(pool: asyncpg.Pool) -> dict:
    """[FR30/FR31/FR33/FR35/FR54] One scheduled pass over every commercial
    lifecycle: boosts (payment window, completion, pause + credit),
    entitlements (3-day reminder, renewal, 7-day grace, pause) and campaigns
    (completion). The renewal reminder GATES the renewal: a renewal charge is
    only ever raised for an entitlement whose reminder was actually delivered,
    and the delivery is recorded before the charge exists (TR054)."""
    counts = await run_promotion_lifecycle_pass(pool)
    counts.update({"reminders_sent": 0, "renewal_charges": 0, "entitlements_paused": 0, "entitlements_completed": 0, "campaigns_completed": 0})
    settings = get_settings()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", settings.dispatcher_operator_member_id)

            for r in await conn.fetch("SELECT * FROM vyapar_commercial.run_entitlement_lifecycle()"):
                link = f"/workspace/{r['listing_id']}"
                renews = r["renews_at"].date().isoformat() if r["renews_at"] else ""
                if r["action"] == "reminder_due":
                    sent = await notify_member(
                        conn, member_id=r["owner_id"], template="entitlementRenewalReminder", link=link,
                        idempotency_key=f"renewal_reminder:{r['entitlement_id']}:{renews}", params={"date": renews},
                    )
                    if sent:
                        # only now may the renewal proceed (TR054's own guard)
                        await conn.execute("SELECT vyapar_commercial.mark_reminder_acked($1)", r["entitlement_id"])
                        counts["reminders_sent"] += 1
                elif r["action"] == "charge_due":
                    ent = await conn.fetchrow(
                        "SELECT price_paise, tax_paise, product_id, product_version, grace_until FROM vyapar_commercial.entitlements WHERE id = $1",
                        r["entitlement_id"],
                    )
                    # [FR51] Vyapar stores no payment credentials, so a renewal
                    # is completed by the member on the gateway's hosted page
                    # within the 7-day grace window — a renewal can never be
                    # charged silently, which is also FR54's intent.
                    try:
                        order = await create_payment_order(
                            conn, kind="entitlement", ref_id=r["entitlement_id"], member_id=r["owner_id"],
                            amount_paise=ent["price_paise"], tax_paise=ent["tax_paise"],
                            description=f"Vyapar Business Workspace renewal {ent['product_id']} v{ent['product_version']}",
                            return_path=link, idempotency_key=f"entitlement_renewal:{r['entitlement_id']}:{renews}",
                        )
                        checkout = order["checkout_url"]
                    except GatewayUnavailable:
                        checkout = None
                    await notify_member(
                        conn, member_id=r["owner_id"], template="entitlementRenewalDue", link=link,
                        idempotency_key=f"renewal_due:{r['entitlement_id']}:{renews}",
                        params={"date": (ent["grace_until"].date().isoformat() if ent["grace_until"] else "")},
                    )
                    counts["renewal_charges"] += 1
                    if checkout is None:
                        logging.getLogger(__name__).warning("renewal checkout unavailable for entitlement %s", r["entitlement_id"])
                elif r["action"].startswith("paused"):
                    reason = "renewalReminderUndelivered" if r["action"] == "paused_no_reminder" else "graceExpired"
                    await notify_member(
                        conn, member_id=r["owner_id"], template="entitlementPaused", link=link,
                        idempotency_key=f"entitlement_paused:{r['entitlement_id']}:{reason}",
                        key_params={"reason": f"workspace.pausedReason.{reason}"},
                    )
                    counts["entitlements_paused"] += 1
                elif r["action"] == "completed_cancelled":
                    await notify_member(
                        conn, member_id=r["owner_id"], template="entitlementEnded", link=link,
                        idempotency_key=f"entitlement_ended:{r['entitlement_id']}", params={"date": renews},
                    )
                    counts["entitlements_completed"] += 1

            for c in await conn.fetch("SELECT * FROM vyapar_commercial.run_campaign_lifecycle()"):
                name = await conn.fetchval("SELECT name FROM vyapar_commercial.campaigns WHERE id = $1", c["campaign_id"])
                await notify_member(
                    conn, member_id=c["owner_id"], template="campaignCompleted", link=f"/campaigns/{c['campaign_id']}",
                    idempotency_key=f"campaign_completed:{c['campaign_id']}", params={"name": name or ""},
                )
                counts["campaigns_completed"] += 1
    return counts
