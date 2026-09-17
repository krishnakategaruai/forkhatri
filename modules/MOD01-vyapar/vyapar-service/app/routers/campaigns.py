# [TR035] Community/Opportunity Campaigns (FR35).
# Approach:
#  - A campaign is nothing more than a package of boosts: creating one calls
#    Commercial's ONE `create_item_promotion()` per item (SP035's explicit
#    requirement), so every item inherits FR30's verified-only eligibility, the
#    Sponsored label and the organic-rank guarantee. There is no campaign-
#    specific boost path that could drift from those rules.
#  - Up to 10 items, package budgets from configuration (`products` of kind
#    `campaign`), a date range, and the same audience narrowing a single boost
#    offers. Items that fail eligibility are reported back by name instead of
#    being silently dropped.
#  - Gated on the Business Workspace plan through the Authorization Engine
#    (`campaigns` capability), so a Paused plan locks campaign creation while
#    keeping every existing campaign's data.
#  - One payment for the package (FR35's "one payment"), then payment success
#    activates the campaign and all of its item boosts together.
#  - Reporting is TR032's own aggregate grouped over the campaign's items
#    (`campaign_impressions_report`), never a second report implementation.
# Reference (Upwork + WorkIndia lens): WorkIndia sells job-post packs that
# spread paid reach across several postings, and Upwork bundles Connects per
# job rather than per placement — both are "one purchase covering several
# items", which is what a campaign is here. Neither implies changed relevance.
# Traces to: FR35, FR30, FR31, FR32, FR33, TR035, SP035
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import authz
from app.audit import audit
from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.routers.commercial import MIN_IMPRESSIONS_TO_COMPARE, REPORT_KINDS, create_item_promotion, products_for_kind
from app.routers.payments import GatewayUnavailable, create_payment_order

router = APIRouter(tags=["campaigns"])

MAX_CAMPAIGN_ITEMS = 10


class CampaignItem(BaseModel):
    kind: Literal["listing", "opportunity"]
    id: str


class CampaignIn(BaseModel):
    listing_id: str
    name: str = Field(min_length=2, max_length=120)
    product_id: str
    items: list[CampaignItem] = Field(min_length=1, max_length=MAX_CAMPAIGN_ITEMS)
    days: int = Field(default=14, ge=1, le=90)
    audience_locality: str | None = Field(default=None, max_length=120)


@router.get("/v1/campaigns/options")
async def campaign_options(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    wctx = await authz.require(conn, listing_id, "campaigns", lang)
    listings = await conn.fetch(
        """SELECT id, name, locality FROM vyapar_listings.listings
           WHERE owner_id = $1 AND state = 'active_verified' ORDER BY name""",
        wctx.owner_id,
    )
    opportunities = await conn.fetch(
        "SELECT id, title FROM vyapar_opportunities.opportunities WHERE poster_id = $1 AND state = 'active' ORDER BY created_at DESC LIMIT 50",
        wctx.owner_id,
    )
    return {
        "packages": [
            {"id": p["id"], "version": p["version"], "duration_days": p["duration_days"], "price_paise": p["price_paise"],
             "tax_paise": p["tax_paise"], "total_paise": p["total_paise"]}
            for p in await products_for_kind(conn, "campaign")
        ],
        "max_items": MAX_CAMPAIGN_ITEMS,
        "locality": listings[0]["locality"] if listings else None,
        "items": (
            [{"kind": "listing", "id": str(r["id"]), "title": r["name"]} for r in listings]
            + [{"kind": "opportunity", "id": str(r["id"]), "title": r["title"]} for r in opportunities]
        ),
    }


@router.post("/v1/campaigns", status_code=201)
async def create_campaign(
    body: CampaignIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    wctx = await authz.require(conn, body.listing_id, "campaigns", lang)
    package = next((p for p in await products_for_kind(conn, "campaign") if p["id"] == body.product_id), None)
    if package is None:
        raise HTTPException(status_code=422, detail=translate("campaigns.error.packageNotFound", lang))
    seen = {(i.kind, i.id) for i in body.items}
    if len(seen) != len(body.items):
        raise HTTPException(status_code=422, detail=translate("campaigns.error.duplicateItems", lang))

    starts_at = datetime.now(timezone.utc)
    ends_at = starts_at + timedelta(days=body.days)
    import json

    campaign = await conn.fetchrow(
        """INSERT INTO vyapar_commercial.campaigns
             (listing_id, owner_id, name, product_id, product_version, budget_paise, tax_paise, starts_at, ends_at, audience, item_refs, state)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb, 'awaiting_payment') RETURNING *""",
        body.listing_id, wctx.owner_id, body.name.strip(), package["id"], package["version"],
        package["price_paise"], package["tax_paise"], starts_at, ends_at,
        json.dumps({"locality": body.audience_locality} if body.audience_locality else {}),
        json.dumps([{"kind": i.kind, "id": i.id} for i in body.items]),
    )

    # [SP035] one shared boost-application call per item — the budget is split
    # evenly so each item's own pro-rata credit maths (FR31) still works.
    share = package["price_paise"] // len(body.items)
    tax_share = package["tax_paise"] // len(body.items)
    accepted, rejected = [], []
    for item in body.items:
        row = await create_item_promotion(
            conn, owner_id=wctx.owner_id, target_kind=item.kind, target_id=item.id,
            product_id=package["id"], product_version=package["version"],
            price_paise=share, tax_paise=tax_share,
            audience={"locality": body.audience_locality} if body.audience_locality else {},
            campaign_id=campaign["id"], state="awaiting_payment",
        )
        (accepted if row is not None else rejected).append(item.id)
    if not accepted:
        raise HTTPException(status_code=422, detail=translate("campaigns.error.noEligibleItems", lang))
    await audit(conn, actor_id=ctx.member_id, action="campaign_created", object_kind="campaign", object_id=campaign["id"],
                details={"listing_id": body.listing_id, "items": len(accepted), "rejected": len(rejected), "package": package["id"]})
    return {
        "id": str(campaign["id"]), "state": "awaiting_payment", "accepted_items": accepted, "rejected_items": rejected,
        "budget_paise": package["price_paise"], "tax_paise": package["tax_paise"],
        "total_paise": package["total_paise"], "starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat(),
    }


async def _own_campaign(conn: asyncpg.Connection, campaign_id: str, lang: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_commercial.campaigns WHERE id = $1", campaign_id)
    except asyncpg.DataError:
        row = None
    if row is None:  # RLS already limits this to the owner, workspace or a commercial operator
        raise HTTPException(status_code=404, detail=translate("campaigns.error.notFound", lang))
    return row


class ConfirmIn(BaseModel):
    confirmed: Literal[True]  # [TR054] explicit confirmation of the disclosure screen


@router.post("/v1/campaigns/{campaign_id}/confirm-purchase")
async def confirm_campaign_purchase(
    campaign_id: str,
    body: ConfirmIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    campaign = await _own_campaign(conn, campaign_id, lang)
    await authz.require(conn, campaign["listing_id"], "campaigns", lang)
    if campaign["state"] != "awaiting_payment":
        raise HTTPException(status_code=400, detail=translate("campaigns.error.invalidTransition", lang))
    try:
        order = await create_payment_order(
            conn, kind="campaign", ref_id=campaign["id"], member_id=campaign["owner_id"],
            amount_paise=campaign["budget_paise"], tax_paise=campaign["tax_paise"],
            description=f"Vyapar campaign {campaign['name']}", return_path=f"/campaigns/{campaign['id']}",
        )
    except GatewayUnavailable:
        return {"state": campaign["state"], "checkout_url": None, "notice": "gatewayUnavailable"}
    return {"state": campaign["state"], "checkout_url": order["checkout_url"], "payment_order_id": order["id"], "notice": None}


@router.get("/v1/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    campaign = await _own_campaign(conn, campaign_id, lang)
    items = await conn.fetch(
        """SELECT p.id, p.target_kind, p.target_id, p.state, p.price_paise, p.tax_paise, p.credit_paise,
                  coalesce(l.name, o.title) AS title
           FROM vyapar_commercial.promotions p
           LEFT JOIN vyapar_listings.listings l ON p.target_kind = 'listing' AND l.id = p.target_id
           LEFT JOIN vyapar_opportunities.opportunities o ON p.target_kind = 'opportunity' AND o.id = p.target_id
           WHERE p.campaign_id = $1 ORDER BY p.created_at""",
        campaign["id"],
    )
    order = await conn.fetchrow(
        "SELECT state, gateway_payment_ref FROM vyapar_payments.payment_orders WHERE ref_id = $1 ORDER BY created_at DESC LIMIT 1",
        campaign["id"],
    )
    spent = sum(i["price_paise"] + i["tax_paise"] - i["credit_paise"] for i in items if i["state"] in ("active", "completed", "paused"))
    return {
        "id": str(campaign["id"]), "name": campaign["name"], "state": campaign["state"], "listing_id": campaign["listing_id"],
        "product_id": campaign["product_id"], "product_version": campaign["product_version"],
        "budget_paise": campaign["budget_paise"], "tax_paise": campaign["tax_paise"], "spent_paise": spent,
        "starts_at": campaign["starts_at"].isoformat(), "ends_at": campaign["ends_at"].isoformat(),
        "payment_state": order["state"] if order else None,
        "receipt_ref": order["gateway_payment_ref"] if order else None,
        "items": [
            {"promotion_id": str(i["id"]), "kind": i["target_kind"], "target_id": str(i["target_id"]), "title": i["title"],
             "state": i["state"], "allocated_paise": i["price_paise"] + i["tax_paise"], "credit_paise": i["credit_paise"]}
            for i in items
        ],
    }


@router.post("/v1/campaigns/{campaign_id}/items-state")
async def set_campaign_items_state(
    campaign_id: str,
    body: dict,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    """[FR35/UX21 Pause-Resume] The sealed `campaigns.state` CHECK has no
    `paused` value, so pausing a campaign pauses its ITEM boosts (which do
    have that state) and leaves the campaign itself Active. Declared in the
    implementation record rather than adding a state the ER model doesn't have."""
    campaign = await _own_campaign(conn, campaign_id, lang)
    await authz.require(conn, campaign["listing_id"], "campaigns", lang)
    action = body.get("action")
    if action not in ("pause", "resume"):
        raise HTTPException(status_code=422, detail=translate("campaigns.error.invalidTransition", lang))
    if action == "pause":
        status = await conn.execute(
            "UPDATE vyapar_commercial.promotions SET state = 'paused', paused_at = now(), updated_at = now() WHERE campaign_id = $1 AND state = 'active'",
            campaign["id"],
        )
    else:
        status = await conn.execute(
            """UPDATE vyapar_commercial.promotions SET state = 'active', paused_at = NULL, updated_at = now()
               WHERE campaign_id = $1 AND state = 'paused' AND ends_at > now()""",
            campaign["id"],
        )
    await audit(conn, actor_id=ctx.member_id, action=f"campaign_items_{action}", object_kind="campaign", object_id=campaign["id"])
    return {"action": action, "items_changed": int(status.split()[-1])}


@router.get("/v1/campaigns/{campaign_id}/report")  # its own path: /v1/performance/{kind}/{id} only accepts listing|opportunity
async def campaign_report(
    campaign_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    """[FR32/FR35] Campaign-level counts: TR032's own aggregate grouped over the
    campaign's items. Same five counts, same 10-impression comparison floor,
    same absence of any projection or causal field."""
    campaign = await _own_campaign(conn, campaign_id, lang)
    rows = await conn.fetch("SELECT * FROM vyapar_commercial.campaign_impressions_report($1)", campaign["id"])
    start, end = campaign["starts_at"], min(campaign["ends_at"], datetime.now(timezone.utc))
    counts = {k: {"boosted": 0, "organic": 0} for k in REPORT_KINDS}
    for r in rows:
        if start.date() <= r["day"] <= end.date() and r["kind"] in counts:
            counts[r["kind"]]["boosted" if r["sponsored"] else "organic"] += r["n"]
    impressions = counts["impression"]["boosted"] + counts["impression"]["organic"]
    comparable = impressions >= MIN_IMPRESSIONS_TO_COMPARE
    return {
        "from": start.isoformat(), "to": end.isoformat(), "boost_ran": True, "comparable": comparable,
        "too_little_data": impressions < MIN_IMPRESSIONS_TO_COMPARE,
        "counts": [
            {"kind": k, "total": v["boosted"] + v["organic"],
             "boosted": v["boosted"] if comparable else None, "organic": v["organic"] if comparable else None}
            for k, v in counts.items()
        ],
    }
