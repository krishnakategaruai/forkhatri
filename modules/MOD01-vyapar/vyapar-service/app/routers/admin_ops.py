# [TR046] Marketplace health metrics, min-group-size suppression (FR46).
# [TR048] Opportunity review / stale queue / taxonomy management (FR48).
# [TR052] Dead-letter visibility and the MOD05 Dashboard Read Bridge (FR52).
# Approach:
#  - FR46: every metric is a real aggregate over `analytics_events` and
#    `vyapar_commercial.impressions` (never fabricated). Any GROUP BY here
#    suppresses a group with fewer than 10 rows SERVER-SIDE — the row is
#    never included in the response at all, not merely hidden by the
#    client (TR046's own explicit rule). There is no profile-completion
#    metric anywhere in this response, a permanent, intentional omission.
#  - FR48: three areas, gated on the `content` operator permission (taxonomy
#    on the `content` permission too, since Listings & Verification owns
#    taxonomy per the component table — this admin surface calls into its
#    existing `taxonomy_terms` table directly rather than a second copy).
#    Merge keeps both labels as aliases so search never breaks on an old
#    term. Every taxonomy change and every opportunity queue decision
#    publishes a `publish_with_outbox()` event, picked up by the same
#    dispatcher pass that stands in for the Search Bridge, satisfying the
#    5-minute reindex rule without a second implementation.
#  - FR52: `GET /v1/admin/dead-letters` is the operator-visible half of the
#    shared outbox mechanism (`app/outbox.py`). `GET /internal/v1/
#    dashboard-summary/{listing_id}` is the literal MOD05 contract —
#    unauthenticated by member session (a genuine server-to-server call),
#    answered entirely by migration 010's `dashboard_summary()` allow-list
#    function, which returns nothing for a listing that isn't public.
# Traces to: FR46, FR48, FR52, TR046, TR048, TR052, SP046, SP048, SP052
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.audit import audit
from app.db import get_conn, get_pool
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.outbox import publish_with_outbox
from app.taxonomy_cache import refresh_taxonomy_cache
from app.routers.opportunities import _lifecycle_action

router = APIRouter(tags=["admin-ops"])

MIN_GROUP_SIZE = 10


async def _require(conn: asyncpg.Connection, ctx: AuthzContext, permission: str, lang: str) -> None:
    perms = await conn.fetchval("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    if not perms or permission not in perms:
        raise HTTPException(status_code=403, detail=translate("adminOps.error.permissionRequired", lang, permission=permission))


# ---------------------------------------------------------------------------
# FR46 — marketplace health
# ---------------------------------------------------------------------------
@router.get("/v1/admin/marketplace-health")
async def marketplace_health(
    lang: Locale,
    days: int = Query(default=30, ge=1, le=365),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require(conn, ctx, "analytics", lang)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    async def count_ge(sql: str, *params) -> int | None:
        """Returns None (suppressed) if the underlying count is below the
        minimum group size — the metric is then OMITTED by the caller."""
        n = await conn.fetchval(sql, *params)
        n = n or 0
        return n if n >= MIN_GROUP_SIZE else None

    zero_result_searches = await conn.fetchval(
        "SELECT count(*) FROM vyapar_analytics.analytics_events WHERE event='search_executed' AND at >= $1 AND props->>'zero_result' = 'true'", since
    )
    total_searches = await conn.fetchval("SELECT count(*) FROM vyapar_analytics.analytics_events WHERE event='search_executed' AND at >= $1", since)
    reports = await conn.fetchval("SELECT count(*) FROM vyapar_trust_safety.reports WHERE created_at >= $1", since)
    interactions = await conn.fetchval(
        "SELECT count(*) FROM vyapar_analytics.analytics_events WHERE level IN ('action','confirmed_outcome') AND at >= $1", since
    )
    listing_views = await conn.fetchval("SELECT count(*) FROM vyapar_analytics.analytics_events WHERE event='listing_viewed' AND at >= $1", since)
    listing_enquiries = await conn.fetchval("SELECT count(*) FROM vyapar_analytics.analytics_events WHERE event='enquiry_submitted' AND at >= $1", since)
    opp_responses = await conn.fetchval(
        "SELECT count(*) FROM vyapar_analytics.analytics_events WHERE event='enquiry_submitted' AND at >= $1 AND props->>'target_kind' = 'opportunity'", since
    )
    opp_actionable = await conn.fetchval(
        "SELECT count(*) FROM vyapar_opportunities.opportunities WHERE state = 'active' AND created_at >= $1", since
    )
    opp_confirmed = await conn.fetchval(
        "SELECT count(*) FROM vyapar_analytics.analytics_events WHERE event='enquiry_resolved' AND at >= $1 AND props->>'target_kind' = 'opportunity'", since
    )
    notif_sent = await conn.fetchval("SELECT count(*) FROM vyapar_integration.notifications WHERE created_at >= $1", since)
    notif_muted = await conn.fetchval("SELECT count(*) FROM vyapar_analytics.analytics_events WHERE event='notification_muted' AND at >= $1", since)
    promo_orders = await conn.fetchval(
        "SELECT count(*) FROM vyapar_commercial.promotions WHERE created_at >= $1 AND state NOT IN ('draft','cancelled')", since
    )
    promo_repeat_owners = await conn.fetchval(
        """SELECT count(*) FROM (SELECT owner_id FROM vyapar_commercial.promotions WHERE created_at >= $1
             GROUP BY owner_id HAVING count(*) > 1) x""",
        since,
    )
    revenue_paise = await conn.fetchval(
        "SELECT coalesce(sum(amount_paise + tax_paise), 0) FROM vyapar_payments.payment_orders WHERE state = 'succeeded' AND created_at >= $1", since
    )
    refunds_paise = await conn.fetchval(
        "SELECT coalesce(sum(refund_paise), 0) FROM vyapar_payments.payment_orders WHERE created_at >= $1", since
    )
    fresh_opps = await conn.fetchval(
        "SELECT count(*) FROM vyapar_opportunities.opportunities WHERE state = 'active' AND published_at >= now() - interval '21 days'"
    )
    total_active_opps = await conn.fetchval("SELECT count(*) FROM vyapar_opportunities.opportunities WHERE state = 'active'")

    def rate(numer: int | None, denom: int | None) -> float | None:
        if numer is None or not denom:
            return None
        return round(numer / denom, 4)

    metrics: dict[str, dict] = {
        "opportunity_coverage": {"level": "action", "value": await count_ge("SELECT count(DISTINCT poster_id) FROM vyapar_opportunities.opportunities WHERE created_at >= $1", since)},
        "relevant_discovery_rate": {"level": "impression", "value": rate(total_searches - zero_result_searches if total_searches else None, total_searches)},
        "zero_result_rate": {"level": "impression", "value": rate(zero_result_searches, total_searches)},
        "opportunity_action_rate": {"level": "action", "value": rate(await count_ge("SELECT $1::int", opp_responses), opp_actionable)},
        "relevant_opportunity_connections": {"level": "attributed_outcome", "value": await count_ge("SELECT $1::int", opp_responses)},
        "successful_connection_rate": {"level": "confirmed_outcome", "value": rate(await count_ge("SELECT $1::int", opp_confirmed), opp_responses)},
        "discovery_to_enquiry_rate_listings": {"level": "action", "value": rate(await count_ge("SELECT $1::int", listing_enquiries), listing_views)},
        "freshness": {"level": "operational", "value": rate(fresh_opps, total_active_opps)},
        "reports_per_1000_interactions": {"level": "operational", "value": round((reports or 0) / (interactions or 1) * 1000, 2) if interactions and interactions >= MIN_GROUP_SIZE else None},
        "notification_opt_out_rate": {"level": "action", "value": rate(await count_ge("SELECT $1::int", notif_muted), notif_sent)},
        "promotion_repeat_rate": {"level": "confirmed_outcome", "value": rate(await count_ge("SELECT $1::int", promo_repeat_owners), promo_orders)},
        "revenue_paise": {"level": "confirmed_outcome", "value": revenue_paise if promo_orders and promo_orders >= MIN_GROUP_SIZE else None},
        "refunds_paise": {"level": "confirmed_outcome", "value": refunds_paise if promo_orders and promo_orders >= MIN_GROUP_SIZE else None},
        "time_to_first_relevant_opportunity_hours": {"level": "attributed_outcome", "value": None},  # needs a per-member cohort join beyond this prototype's event volume
    }
    return {"period_days": days, "min_group_size": MIN_GROUP_SIZE, "metrics": metrics}


# ---------------------------------------------------------------------------
# FR48(a) — opportunity review queue
# ---------------------------------------------------------------------------
@router.get("/v1/admin/opportunities-queue")
async def opportunities_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    await _require(conn, ctx, "content", lang)
    rows = await conn.fetch(
        """SELECT id, title, type, state, entry_mode, source_unreachable, unconfirmed_fields, created_at
           FROM vyapar_opportunities.opportunities
           WHERE state = 'pending_review' OR source_unreachable OR cardinality(unconfirmed_fields) > 0
           ORDER BY created_at"""
    )
    return [
        {
            "id": str(r["id"]), "title": r["title"], "type": r["type"], "state": r["state"], "entry_mode": r["entry_mode"],
            "flags": [f for f, v in (("source_unreachable", r["source_unreachable"]), ("unconfirmed_fields", bool(r["unconfirmed_fields"]))) if v],
            "age_days": (datetime.now(timezone.utc) - r["created_at"]).days,
        }
        for r in rows
    ]


class QueueDecisionIn(BaseModel):
    action: Literal["approve", "return", "remove"]
    reason: str | None = Field(default=None, max_length=200)


@router.post("/v1/admin/opportunities-queue/{opportunity_id}/decide")
async def decide_opportunity(
    opportunity_id: str,
    body: QueueDecisionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require(conn, ctx, "content", lang)
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None:
        raise HTTPException(status_code=404, detail=translate("common.error.opportunityNotFound", lang))
    if body.action == "approve":
        await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"pending_review", "draft"}, to_state="active", reset_freshness=True)
        new_state = "active"
    elif body.action == "return":
        await conn.execute(
            "UPDATE vyapar_opportunities.opportunities SET state = 'draft', state_reason = $2, updated_at = now() WHERE id = $1",
            opportunity_id, body.reason or "returned_for_more_info",
        )
        new_state = "draft"
    else:
        await conn.execute(
            "UPDATE vyapar_opportunities.opportunities SET state = 'removed', state_reason = $2, updated_at = now() WHERE id = $1",
            opportunity_id, body.reason or "removed_by_operator",
        )
        new_state = "removed"
    await publish_with_outbox(conn, schema="opportunity", event_type="opportunity.queue_decided", payload={"id": opportunity_id, "action": body.action})
    await audit(conn, actor_id=ctx.member_id, action=f"opportunity_queue_{body.action}", object_kind="opportunity", object_id=opportunity_id, reason_code=body.reason)
    return {"state": new_state}


# ---------------------------------------------------------------------------
# FR48(b) — stale/expired queue, bulk actions
# ---------------------------------------------------------------------------
@router.get("/v1/admin/stale-queue")
async def stale_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    await _require(conn, ctx, "content", lang)
    rows = await conn.fetch(
        """SELECT id, title, state, published_at FROM vyapar_opportunities.opportunities
           WHERE state IN ('stale', 'active') AND (published_at IS NULL OR published_at < now() - interval '21 days')
           ORDER BY published_at NULLS FIRST"""
    )
    return [
        {"id": str(r["id"]), "title": r["title"], "state": r["state"],
         "age_days": (datetime.now(timezone.utc) - r["published_at"]).days if r["published_at"] else None}
        for r in rows
    ]


class BulkStaleIn(BaseModel):
    action: Literal["remind", "expire"]
    ids: list[str] = Field(min_length=1, max_length=200)
    confirm_count: int  # [FR48] "bulk actions require confirmation with counts" — the client must echo the count it saw


@router.post("/v1/admin/stale-queue/bulk")
async def bulk_stale_action(
    body: BulkStaleIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require(conn, ctx, "content", lang)
    if body.confirm_count != len(body.ids):
        raise HTTPException(status_code=422, detail=translate("adminOps.error.confirmCountMismatch", lang))
    if body.action == "remind":
        from app.notifications import notify_member

        rows = await conn.fetch("SELECT id, poster_id, title FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", body.ids)
        for r in rows:
            await notify_member(
                conn, member_id=r["poster_id"], template="opportunityStaleReminder", link=f"/opportunities/{r['id']}",
                idempotency_key=f"stale_reminder:{r['id']}:{datetime.now(timezone.utc).date().isoformat()}",
                params={"title": r["title"]},
            )
        changed = len(rows)
    else:
        status = await conn.execute(
            "UPDATE vyapar_opportunities.opportunities SET state = 'expired', updated_at = now() WHERE id = ANY($1::uuid[])", body.ids
        )
        changed = int(status.split()[-1])
    await audit(conn, actor_id=ctx.member_id, action=f"stale_queue_bulk_{body.action}", object_kind="opportunity", object_id="bulk", details={"count": changed})
    return {"action": body.action, "changed": changed}


# ---------------------------------------------------------------------------
# FR48(c) — taxonomy management
# ---------------------------------------------------------------------------
@router.get("/v1/admin/taxonomy")
async def list_taxonomy(
    lang: Locale,
    kind: Literal["category", "capability"] | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    await _require(conn, ctx, "content", lang)
    rows = await conn.fetch(
        "SELECT * FROM vyapar_listings.taxonomy_terms WHERE ($1::text IS NULL OR kind = $1) ORDER BY kind, name_en", kind
    )
    return [
        {"id": r["id"], "kind": r["kind"], "slug": r["slug"], "name_en": r["name_en"], "name_hi": r["name_hi"], "name_te": r["name_te"],
         "aliases": list(r["aliases"]), "status": r["status"], "merged_into": r["merged_into"], "version": r["version"]}
        for r in rows
    ]


class TaxonomyAddIn(BaseModel):
    kind: Literal["category", "capability"]
    slug: str = Field(min_length=2, max_length=60)
    name_en: str = Field(min_length=2, max_length=80)
    name_hi: str | None = None
    name_te: str | None = None


@router.post("/v1/admin/taxonomy", status_code=201)
async def add_taxonomy_term(
    body: TaxonomyAddIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require(conn, ctx, "content", lang)
    try:
        row = await conn.fetchrow(
            "INSERT INTO vyapar_listings.taxonomy_terms (kind, slug, name_en, name_hi, name_te) VALUES ($1,$2,$3,$4,$5) RETURNING id",
            body.kind, body.slug, body.name_en, body.name_hi, body.name_te,
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=translate("adminOps.error.taxonomySlugExists", lang))
    await publish_with_outbox(conn, schema="listing", event_type="taxonomy.changed", payload={"id": row["id"], "op": "add"})
    await refresh_taxonomy_cache(get_pool())
    await audit(conn, actor_id=ctx.member_id, action="taxonomy_added", object_kind="taxonomy_term", object_id=str(row["id"]))
    return {"id": row["id"]}


class TaxonomyMergeIn(BaseModel):
    from_id: int
    into_id: int


@router.post("/v1/admin/taxonomy/merge")
async def merge_taxonomy_terms(
    body: TaxonomyMergeIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require(conn, ctx, "content", lang)
    if body.from_id == body.into_id:
        raise HTTPException(status_code=422, detail=translate("adminOps.error.taxonomyMergeSameTerm", lang))
    source = await conn.fetchrow("SELECT * FROM vyapar_listings.taxonomy_terms WHERE id = $1", body.from_id)
    target = await conn.fetchrow("SELECT id FROM vyapar_listings.taxonomy_terms WHERE id = $1", body.into_id)
    if source is None or target is None:
        raise HTTPException(status_code=404, detail=translate("adminOps.error.taxonomyNotFound", lang))
    await conn.execute(
        """UPDATE vyapar_listings.taxonomy_terms SET status = 'merged', merged_into = $2, version = version + 1, updated_at = now() WHERE id = $1""",
        body.from_id, body.into_id,
    )
    # [FR48] "merging preserves both labels via aliases, so search continues to resolve the old term"
    await conn.execute(
        "UPDATE vyapar_listings.taxonomy_terms SET aliases = array_append(aliases, $2), version = version + 1, updated_at = now() WHERE id = $1 AND NOT ($2 = ANY(aliases))",
        body.into_id, source["slug"],
    )
    await publish_with_outbox(conn, schema="listing", event_type="taxonomy.changed", payload={"from": body.from_id, "into": body.into_id, "op": "merge"})
    await refresh_taxonomy_cache(get_pool())
    await audit(conn, actor_id=ctx.member_id, action="taxonomy_merged", object_kind="taxonomy_term", object_id=str(body.from_id), details={"into": body.into_id})
    return {"merged_from": body.from_id, "merged_into": body.into_id}


class TaxonomyRenameIn(BaseModel):
    name_en: str | None = None
    name_hi: str | None = None
    name_te: str | None = None


@router.post("/v1/admin/taxonomy/{term_id}/rename")
async def rename_taxonomy_term(
    term_id: int,
    body: TaxonomyRenameIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require(conn, ctx, "content", lang)
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    if not fields:
        raise HTTPException(status_code=422, detail=translate("adminOps.error.nothingToRename", lang))
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(fields))
    result = await conn.execute(
        f"UPDATE vyapar_listings.taxonomy_terms SET {sets}, version = version + 1, updated_at = now() WHERE id = $1", term_id, *fields.values()
    )
    if result.split()[-1] == "0":
        raise HTTPException(status_code=404, detail=translate("adminOps.error.taxonomyNotFound", lang))
    await publish_with_outbox(conn, schema="listing", event_type="taxonomy.changed", payload={"id": term_id, "op": "rename"})
    await refresh_taxonomy_cache(get_pool())
    await audit(conn, actor_id=ctx.member_id, action="taxonomy_renamed", object_kind="taxonomy_term", object_id=str(term_id), details=fields)
    return {"id": term_id, **fields}


# ---------------------------------------------------------------------------
# FR52 — dead-letter visibility (feeds FR49)
# ---------------------------------------------------------------------------
@router.get("/v1/admin/dead-letters")
async def list_dead_letters(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    perms = await conn.fetchval("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    if not perms:  # [TR052] visible to any operator — it is cross-cutting infrastructure health, not one permission's business data
        raise HTTPException(status_code=403, detail=translate("adminOps.error.permissionRequired", lang, permission="any"))
    rows = await conn.fetch("SELECT * FROM vyapar_integration.dead_letters ORDER BY created_at DESC LIMIT 200")
    return [
        {"id": r["id"], "target": r["target"], "payload": r["payload"], "error": r["error"], "attempts": r["attempts"], "created_at": r["created_at"].isoformat()}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# FR52(e) — MOD05 Dashboard Read Bridge (no member session; server-to-server)
# ---------------------------------------------------------------------------
# [Known dev-only shortcut, declared rather than hidden] this route still
# goes through get_conn()/resolve_authz_context() for the pool connection,
# which in DEV_MODE defaults to a dev member header. That default is HARMLESS
# here: dashboard_summary() is SECURITY DEFINER and reads no authz_context at
# all, so any caller identity bypasses RLS the same way (as the function's
# owner) regardless of who the connection resolves to. In a real deployment
# (DEV_MODE=false) this route would incorrectly demand a real platform
# session for what FR52 defines as a server-to-server call with none — a
# genuine follow-up for whoever wires the real MOD05 integration: give this
# route its own internal-service-key dependency instead of get_conn().
internal_router = APIRouter(prefix="/internal/v1", tags=["internal-bridges"])


@internal_router.get("/dashboard-summary/{listing_id}")
async def dashboard_summary(listing_id: str, conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    row = await conn.fetchrow("SELECT * FROM vyapar_listings.dashboard_summary($1)", listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return {"name": row["name"], "category": row["category"], "locality": row["locality"],
            "verification_state": row["verification_state"], "freshness": row["freshness"]}
