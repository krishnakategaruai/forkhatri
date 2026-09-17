# [TR036] Six contextual privacy controls, one screen (FR36).
# [TR037] Data export, correction, deletion, consent withdrawal (FR37).
# [TR038] Inspect and confirm derived preferences (FR38).
# [TR053] Privacy notice, terms, and grievance contact (FR53) — the
# acceptance gate and legal-document reads live here; the grievance/appeal
# text on Report and outcome screens was already built in IMP21.
# Approach:
#  - GET/PATCH /v1/privacy is a lazy upsert on `privacy_settings` (its own
#    RLS already admits a member inserting their own row, so no definer
#    function is needed). Defaults match TR036 exactly: contact after
#    accept, seeking private, commercial comms off. `prompted[]` tracks which
#    of the six contextual explainers has already been shown once, so
#    `mark_prompted` never re-shows the same one-sentence explainer twice.
#  - FR37: `POST /v1/privacy/export` creates a `data_requests` row and, since
#    this dev environment has no object storage (the same honest gap IMP20
#    already declared), builds the export inline as a JSON document rather
#    than faking a queued job — the export completes well inside its 72-hour
#    budget. `POST /v1/privacy/delete` anonymizes the member's own identity
#    row in place (`members.anonymized=true`, name/phone cleared) — never a
#    cascading hard delete, so a counterpart's own thread or review is
#    untouched (TR037's own explicit rule) — deferred while a paid
#    promotion/entitlement is active. `POST /v1/privacy/withdraw-consent`
#    flips one boolean immediately. Correction is already served by the
#    existing per-resource PATCH routes (listings, opportunities, member
#    settings) — FR37(b) names no new endpoint, and none is added here.
#  - FR38: the member reads and decides on their own `derived_preferences`
#    rows (self-only RLS, no definer needed for reads/decisions); the
#    proposing side is the scheduled detector in `run_preference_detection_pass`
#    (main.py's hourly loop), which calls migration 010's
#    `propose_derived_preference()`.
#  - FR53: `GET /v1/legal/{kind}` returns the latest version in the caller's
#    language (falling back to English) plus whether they've already
#    accepted it; `POST /v1/legal/{kind}/accept` records `accepted_at` for
#    exactly that version. `require_accepted()` is the ONE gate every gated
#    action calls before proceeding — used here by listings.py/
#    opportunities.py/enquiries.py, never re-implemented per call site.
# Traces to: FR36, FR37, FR38, FR53, TR036, TR037, TR038, TR053
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import get_conn
from app.deps import Locale
from app.events import emit_event
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context

router = APIRouter(tags=["privacy"])

SIX_CONTROLS = (
    "capability_visible", "seeking_visible", "contact_disclosure",
    "discoverable", "notifications_enabled", "commercial_comms",
)


async def require_accepted(conn: asyncpg.Connection, member_id: str, kind: Literal["privacy", "terms"], lang: str) -> None:
    """[TR053] The gate every gated action calls before proceeding."""
    ok = await conn.fetchval("SELECT vyapar_privacy.has_accepted($1, $2)", member_id, kind)
    if not ok:
        raise HTTPException(
            status_code=403,
            detail={"message": translate("privacy.error.acceptanceRequired", lang), "code": "acceptance_required", "kind": kind},
        )


async def _ensure_row(conn: asyncpg.Connection, member_id: str) -> asyncpg.Record:
    row = await conn.fetchrow(
        """INSERT INTO vyapar_privacy.privacy_settings (member_id) VALUES ($1)
           ON CONFLICT (member_id) DO NOTHING RETURNING *""",
        member_id,
    )
    if row is None:
        row = await conn.fetchrow("SELECT * FROM vyapar_privacy.privacy_settings WHERE member_id = $1", member_id)
    return row


def _settings_out(row: asyncpg.Record) -> dict:
    return {
        "capability_visible": row["capability_visible"], "seeking_visible": row["seeking_visible"],
        "contact_disclosure": row["contact_disclosure"], "discoverable": row["discoverable"],
        "notifications_enabled": row["notifications_enabled"], "commercial_comms": row["commercial_comms"],
        "behavioral_analytics": row["behavioral_analytics"], "digest_enabled": row["digest_enabled"],
        "digest_hour": row["digest_hour"], "muted_types": list(row["muted_types"]), "prompted": list(row["prompted"]),
    }


@router.get("/v1/privacy")
async def get_privacy(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    return _settings_out(await _ensure_row(conn, ctx.member_id))


class PrivacyPatch(BaseModel):
    capability_visible: bool | None = None
    seeking_visible: bool | None = None
    contact_disclosure: Literal["public", "after_accept", "hidden"] | None = None
    discoverable: bool | None = None
    notifications_enabled: bool | None = None
    commercial_comms: bool | None = None
    behavioral_analytics: bool | None = None
    digest_enabled: bool | None = None
    digest_hour: int | None = Field(default=None, ge=0, le=23)
    mark_prompted: str | None = None  # [TR036] one of SIX_CONTROLS — shown once


@router.patch("/v1/privacy")
async def patch_privacy(
    body: PrivacyPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _ensure_row(conn, ctx.member_id)
    if body.mark_prompted and body.mark_prompted not in SIX_CONTROLS:
        raise HTTPException(status_code=422, detail=translate("privacy.error.unknownControl", lang))
    fields = body.model_dump(exclude_unset=True, exclude={"mark_prompted"})
    if fields:
        sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(fields))
        await conn.execute(
            f"UPDATE vyapar_privacy.privacy_settings SET {sets}, updated_at = now() WHERE member_id = $1",
            ctx.member_id, *fields.values(),
        )
    if body.mark_prompted:
        await conn.execute(
            "UPDATE vyapar_privacy.privacy_settings SET prompted = array_append(prompted, $2) WHERE member_id = $1 AND NOT ($2 = ANY(prompted))",
            ctx.member_id, body.mark_prompted,
        )
    row = await conn.fetchrow("SELECT * FROM vyapar_privacy.privacy_settings WHERE member_id = $1", ctx.member_id)
    # [FR45] a privacy change is a state change — operational, always logged, consent flags never gate this one
    await emit_event(conn, member_id=ctx.member_id, event="privacy_settings_changed", level="operational", props={"fields": list(fields.keys())})
    return _settings_out(row)


# ---------------------------------------------------------------------------
# FR37 — data rights
# ---------------------------------------------------------------------------
class ExportDocument(BaseModel):
    generated_at: str
    profile: dict
    listings: list[dict]
    opportunities: list[dict]
    enquiries_sent: list[dict]
    reviews_written: list[dict]
    consents: list[dict]


@router.post("/v1/privacy/export", status_code=201)
async def request_export(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    from datetime import datetime, timezone

    member = await conn.fetchrow("SELECT * FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    listings = await conn.fetch("SELECT id, name, kind, state, created_at FROM vyapar_listings.listings WHERE owner_id = $1", ctx.member_id)
    opportunities = await conn.fetch("SELECT id, title, type, state, created_at FROM vyapar_opportunities.opportunities WHERE poster_id = $1", ctx.member_id)
    enquiries = await conn.fetch("SELECT id, action_type, state, created_at FROM vyapar_enquiries.enquiries WHERE sender_id = $1", ctx.member_id)
    reviews = await conn.fetch("SELECT id, recommend, tags, comment, created_at FROM vyapar_reviews.reviews WHERE author_id = $1", ctx.member_id)
    consents = await conn.fetch("SELECT kind, version, accepted_at FROM vyapar_privacy.acceptances WHERE member_id = $1", ctx.member_id)

    document = ExportDocument(
        generated_at=datetime.now(timezone.utc).isoformat(),
        profile={"id": member["id"], "display_name": member["display_name"], "locality": member["locality"], "language": member["language"]},
        listings=[dict(r) | {"id": str(r["id"]), "created_at": r["created_at"].isoformat()} for r in listings],
        opportunities=[dict(r) | {"id": str(r["id"]), "created_at": r["created_at"].isoformat()} for r in opportunities],
        enquiries_sent=[dict(r) | {"id": str(r["id"]), "created_at": r["created_at"].isoformat()} for r in enquiries],
        reviews_written=[dict(r) | {"id": str(r["id"]), "created_at": r["created_at"].isoformat(), "tags": list(r["tags"])} for r in reviews],
        consents=[dict(r) | {"accepted_at": r["accepted_at"].isoformat()} for r in consents],
    )
    row = await conn.fetchrow(
        """INSERT INTO vyapar_privacy.data_requests (member_id, kind, state, detail, due_at, completed_at)
           VALUES ($1, 'export', 'ready', $2, now() + interval '72 hours', now()) RETURNING id, due_at""",
        ctx.member_id, document.model_dump_json(),
    )
    await emit_event(conn, member_id=ctx.member_id, event="data_export_completed", level="operational")
    return {"id": str(row["id"]), "state": "ready", "document": document.model_dump()}


@router.post("/v1/privacy/withdraw-consent")
async def withdraw_consent(
    body: dict,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    field = body.get("field")
    if field not in ("commercial_comms", "behavioral_analytics", "notifications_enabled"):
        raise HTTPException(status_code=422, detail="unknown_consent_field")
    await _ensure_row(conn, ctx.member_id)
    await conn.execute(f"UPDATE vyapar_privacy.privacy_settings SET {field} = false, updated_at = now() WHERE member_id = $1", ctx.member_id)
    await conn.execute(
        "INSERT INTO vyapar_privacy.data_requests (member_id, kind, state, detail, completed_at) VALUES ($1, 'withdraw', 'completed', $2, now())",
        ctx.member_id, field,
    )
    return {"field": field, "withdrawn": True}


@router.post("/v1/privacy/delete", status_code=201)
async def request_deletion(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    active_paid = await conn.fetchval(
        """SELECT (EXISTS (SELECT 1 FROM vyapar_commercial.promotions WHERE owner_id = $1 AND state IN ('awaiting_payment','active'))
                OR EXISTS (SELECT 1 FROM vyapar_commercial.entitlements WHERE owner_id = $1 AND state IN ('awaiting_payment','active')))""",
        ctx.member_id,
    )
    if active_paid:
        row = await conn.fetchrow(
            """INSERT INTO vyapar_privacy.data_requests (member_id, kind, state, detail)
               VALUES ($1, 'delete', 'blocked', 'active paid order') RETURNING id""",
            ctx.member_id,
        )
        return {"id": str(row["id"]), "state": "blocked", "reason": translate("privacy.error.deleteBlockedActiveOrder", lang)}

    retained = ["audit_events (regulatory retention)", "payment_orders (financial record retention)"]
    await conn.execute(
        """UPDATE vyapar_identity.members SET anonymized = true, display_name = 'Deleted member',
             phone = NULL, avatar_url = NULL, deleted_at = now(), updated_at = now() WHERE id = $1""",
        ctx.member_id,
    )
    row = await conn.fetchrow(
        """INSERT INTO vyapar_privacy.data_requests (member_id, kind, state, retained_categories, completed_at)
           VALUES ($1, 'delete', 'completed', $2, now()) RETURNING id""",
        ctx.member_id, retained,
    )
    return {"id": str(row["id"]), "state": "completed", "retained_categories": retained}


@router.get("/v1/privacy/requests")
async def list_my_requests(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    rows = await conn.fetch("SELECT * FROM vyapar_privacy.data_requests WHERE member_id = $1 ORDER BY created_at DESC", ctx.member_id)
    return [
        {"id": str(r["id"]), "kind": r["kind"], "state": r["state"], "retained_categories": list(r["retained_categories"]),
         "created_at": r["created_at"].isoformat(), "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# FR38 — derived preferences
# ---------------------------------------------------------------------------
@router.get("/v1/preferences/mine")
async def list_my_preferences(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_privacy.derived_preferences WHERE member_id = $1 AND state != 'removed' ORDER BY proposed_at DESC",
        ctx.member_id,
    )
    return [
        {"id": str(r["id"]), "key": r["key"], "value": r["value"], "evidence": r["evidence"], "source": r["source"],
         "state": r["state"], "proposed_at": r["proposed_at"].isoformat()}
        for r in rows
    ]


@router.post("/v1/preferences/{pref_id}/{action}")
async def decide_preference(
    pref_id: str,
    action: Literal["confirm", "decline", "remove"],
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_privacy.derived_preferences WHERE id = $1 AND member_id = $2", pref_id, ctx.member_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise HTTPException(status_code=404, detail=translate("privacy.error.preferenceNotFound", lang))
    new_state = {"confirm": "active", "decline": "declined", "remove": "removed"}[action]
    await conn.execute(
        "UPDATE vyapar_privacy.derived_preferences SET state = $2, decided_at = now() WHERE id = $1", pref_id, new_state
    )
    return {"state": new_state}


# ---------------------------------------------------------------------------
# FR53 — legal notice, terms, acceptance
# ---------------------------------------------------------------------------
@router.get("/v1/legal/{kind}")
async def get_legal_document(
    kind: Literal["privacy", "terms"],
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    row = await conn.fetchrow(
        """SELECT * FROM vyapar_privacy.legal_documents WHERE kind = $1 AND language = $2
           ORDER BY version DESC LIMIT 1""",
        kind, lang,
    )
    if row is None:  # [TR042] fallback to English, never a hard failure
        row = await conn.fetchrow(
            "SELECT * FROM vyapar_privacy.legal_documents WHERE kind = $1 AND language = 'en' ORDER BY version DESC LIMIT 1", kind
        )
    accepted = await conn.fetchval("SELECT vyapar_privacy.has_accepted($1, $2)", ctx.member_id, kind)
    return {"kind": kind, "version": row["version"], "title": row["title"], "body": row["body"], "accepted": bool(accepted)}


@router.post("/v1/legal/{kind}/accept")
async def accept_legal_document(
    kind: Literal["privacy", "terms"],
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    version = await conn.fetchval("SELECT max(version) FROM vyapar_privacy.legal_documents WHERE kind = $1", kind)
    await conn.execute(
        "INSERT INTO vyapar_privacy.acceptances (member_id, kind, version) VALUES ($1,$2,$3) ON CONFLICT DO NOTHING",
        ctx.member_id, kind, version,
    )
    return {"kind": kind, "version": version, "accepted": True}


# ---------------------------------------------------------------------------
# [TR038] Scheduled detector — "three 'Too far' feedbacks" is the FR38 example
# itself. Proposes a smaller service_radius_km via migration 010's
# propose_derived_preference() (dispatcher-only, arbitrary member, its own
# 30-day re-propose cooldown). Reports are never read here — this function
# imports nothing from trust_safety, a structural absence, not a filter.
# ---------------------------------------------------------------------------
async def run_preference_detection_pass(pool) -> dict:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            rows = await conn.fetch(
                """SELECT member_id, count(*) AS n
                   FROM vyapar_opportunities.member_opportunity
                   WHERE hidden_reason = 'too_far' AND hidden_at > now() - interval '30 days'
                   GROUP BY member_id HAVING count(*) >= 3"""
            )
            proposed = 0
            for r in rows:
                new_id = await conn.fetchval(
                    "SELECT vyapar_privacy.propose_derived_preference($1, $2, $3::jsonb, $4, $5)",
                    r["member_id"], "max_distance_km", '{"radius_km": 10}',
                    f"{r['n']} recent 'Too far' feedbacks in the last 30 days", "not_interested_pattern",
                )
                if new_id:
                    proposed += 1
    return {"proposed": proposed}
