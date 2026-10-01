"""Administration: provider review, granular verification, expertise
requests, reports, disputes, transactions and platform settings."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app import db, identity
from app.components import audit, bookings as bk, money, notifications, providers, storage
from app.errors import DomainError, not_found
from app.i18n import request_language
from app.identity import Actor, admin_actor

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_actor)])


@router.get("/overview")
async def overview():
    r = await db.fetchrow(
        """SELECT
          (SELECT count(*) FROM provider WHERE status='pending_review') AS pending_providers,
          (SELECT count(*) FROM provider WHERE status='approved') AS approved_providers,
          (SELECT count(*) FROM expertise_request WHERE status='pending') AS pending_expertise,
          (SELECT count(*) FROM report WHERE status='open') AS open_reports,
          (SELECT count(*) FROM dispute WHERE status='open') AS open_disputes,
          (SELECT count(*) FROM booking WHERE status='completed') AS completed,
          (SELECT coalesce(sum(gross_minor),0) FROM booking WHERE status IN ('completed','confirmed','in_progress')) AS gtv_minor,
          (SELECT coalesce(sum(platform_fee_minor),0) FROM booking WHERE status='completed') AS fee_minor,
          (SELECT coalesce(sum(refund_minor),0) FROM booking) AS refunds_minor,
          (SELECT count(*) FROM booking WHERE status IN ('cancelled_by_seeker','cancelled_by_provider')) AS cancelled,
          (SELECT count(*) FROM booking WHERE status IN ('no_show_seeker','no_show_provider')) AS no_shows""")
    return dict(r)


@router.get("/providers")
async def list_providers(request: Request, status: str = "pending_review"):
    lang = request_language(request)
    rows = await db.fetch("SELECT p.member_id, p.headline, p.status, p.standing, p.submitted_at, p.country, m.display_name FROM provider p JOIN member m ON m.member_id=p.member_id WHERE p.status=$1 ORDER BY p.submitted_at NULLS LAST", status)
    out = []
    async with db.pool().acquire() as conn:
        for r in rows:
            d = dict(r)
            d["expertise"] = await providers.expertise_of(conn, r["member_id"], lang)
            d["verified"] = await providers.verifications(conn, r["member_id"])
            out.append(d)
    return out


@router.get("/providers/{provider_id}")
async def provider_detail(provider_id: UUID, request: Request):
    lang = request_language(request)
    p = await db.fetchrow("SELECT p.*, m.display_name FROM provider p JOIN member m ON m.member_id=p.member_id WHERE p.member_id=$1", provider_id)
    if not p:
        raise not_found("provider")
    async with db.pool().acquire() as conn:
        d = dict(p)
        d["expertise"] = await providers.expertise_of(conn, provider_id, lang)
        d["verified"] = await providers.verifications(conn, provider_id)
        d["evidence"] = db.rows(await conn.fetch(
            "SELECT id, kind, title, issuer, year_from, year_to, reference_no, status, review_note, document_name, (document_url IS NOT NULL) AS has_document "
            "FROM provider_evidence WHERE provider_id=$1 ORDER BY kind, created_at", provider_id))
        d["services"] = db.rows(await conn.fetch("SELECT id, title, area_id, duration_min, price_minor, status FROM service WHERE provider_id=$1", provider_id))
        d["reputation"] = await providers.reputation(conn, provider_id)
        d["badge_history"] = db.rows(await conn.fetch("SELECT badge_id, level, awarded_at, evidence FROM badge_award WHERE provider_id=$1 ORDER BY awarded_at", provider_id))
        req = await conn.fetch("SELECT DISTINCT unnest(required_dimensions) AS dim FROM compliance_rule c JOIN provider_expertise pe ON pe.area_id=c.area_id WHERE pe.provider_id=$1 AND (c.jurisdiction=$2 OR c.jurisdiction='*')", provider_id, d["country"])
        d["required_dimensions"] = sorted({r["dim"] for r in req})
        d["audit"] = db.rows(await conn.fetch("SELECT action, actor_id, detail, at FROM audit_log WHERE target_kind='provider' AND target_id=$1 ORDER BY at DESC LIMIT 30", str(provider_id)))
    return d


class Decision(BaseModel):
    decision: Literal["approve", "changes_requested", "suspend", "reinstate"]
    note: str = Field(default="", max_length=1000)


@router.post("/providers/{provider_id}/decide")
async def decide(provider_id: UUID, body: Decision, actor: Actor = Depends(admin_actor)):
    status = {"approve": "approved", "changes_requested": "changes_requested", "suspend": "suspended", "reinstate": "approved"}[body.decision]
    async with db.tx() as conn:
        if not await conn.fetchval("SELECT 1 FROM provider WHERE member_id=$1", provider_id):
            raise not_found("provider")
        await conn.execute("UPDATE provider SET status=$2, review_note=$3, reviewed_at=now(), reviewed_by=$4, updated_at=now() WHERE member_id=$1", provider_id, status, body.note, actor.member_id)
        if status == "suspended":
            await conn.execute("UPDATE service SET status='paused' WHERE provider_id=$1 AND status='active'", provider_id)
        await audit.record(conn, actor.member_id, f"provider.{body.decision}", "provider", provider_id, {"note": body.note})
        await notifications.notify(conn, provider_id, f"provider.{status}", {"note": body.note})
    return {"status": status}


class VerifyIn(BaseModel):
    dimension: Literal["identity", "contact", "experience", "qualification", "certification", "registration", "business", "portfolio"]
    verified: bool
    note: str = ""


@router.post("/providers/{provider_id}/verify")
async def verify(provider_id: UUID, body: VerifyIn, actor: Actor = Depends(admin_actor)):
    async with db.tx() as conn:
        if body.verified:
            await conn.execute("INSERT INTO verification (provider_id, dimension, verified_by, note) VALUES ($1,$2,$3,$4) ON CONFLICT (provider_id, dimension) DO UPDATE SET verified_at=now(), verified_by=$3, note=$4",
                               provider_id, body.dimension, actor.member_id, body.note)
        else:
            await conn.execute("DELETE FROM verification WHERE provider_id=$1 AND dimension=$2", provider_id, body.dimension)
        await audit.record(conn, actor.member_id, "verification." + ("granted" if body.verified else "revoked"), "provider", provider_id, {"dimension": body.dimension, "note": body.note})
        return {"verified": await providers.verifications(conn, provider_id)}


class EvidenceDecision(BaseModel):
    status: Literal["verified", "rejected", "submitted"]
    note: str = ""


@router.post("/evidence/{evidence_id}/decide")
async def decide_evidence(evidence_id: UUID, body: EvidenceDecision, actor: Actor = Depends(admin_actor)):
    async with db.tx() as conn:
        row = await conn.fetchrow("UPDATE provider_evidence SET status=$2, review_note=$3, reviewed_by=$4, reviewed_at=now() WHERE id=$1 RETURNING provider_id, kind", evidence_id, body.status, body.note, actor.member_id)
        if not row:
            raise not_found("evidence")
        await audit.record(conn, actor.member_id, f"evidence.{body.status}", "provider", row["provider_id"], {"evidence_id": str(evidence_id), "kind": row["kind"]})
    return {"status": body.status}


@router.get("/evidence/{evidence_id}/document")
async def evidence_document(evidence_id: UUID, actor: Actor = Depends(admin_actor)):
    ev = await db.fetchrow("SELECT provider_id, document_url, document_name, document_mime, document_encrypted FROM provider_evidence WHERE id=$1", evidence_id)
    if not ev or not ev["document_url"]:
        raise not_found("document")
    # Sensitive document access is always audited.
    async with db.tx() as conn:
        await audit.record(conn, actor.member_id, "evidence.document_viewed", "provider", ev["provider_id"], {"evidence_id": str(evidence_id)})
    return storage.serve(ev["document_url"], ev["document_encrypted"], ev["document_mime"], ev["document_name"])


@router.get("/expertise-requests")
async def expertise_requests():
    rows = db.rows(await db.fetch("SELECT * FROM expertise_request WHERE status='pending' ORDER BY created_at"))
    names = await identity.display_names([r["proposed_by"] for r in rows])
    for r in rows:
        r["proposed_by_name"] = names.get(str(r["proposed_by"]), "")
    return rows


class ExpertiseDecision(BaseModel):
    approve: bool
    id: str | None = None        # slug when approving
    name_en: str | None = None
    name_hi: str | None = None
    name_te: str | None = None
    regulated: bool = False


@router.post("/expertise-requests/{request_id}/decide")
async def decide_expertise(request_id: UUID, body: ExpertiseDecision, actor: Actor = Depends(admin_actor)):
    async with db.tx() as conn:
        req = await conn.fetchrow("SELECT * FROM expertise_request WHERE id=$1 AND status='pending'", request_id)
        if not req:
            raise not_found("request")
        created = None
        if body.approve:
            slug = (body.id or req["name"]).lower().strip()
            slug = "".join(c if c.isalnum() else "-" for c in slug).strip("-")[:40]
            if not slug:
                raise DomainError("invalid_slug", "Give the area an identifier.", 422)
            await conn.execute("INSERT INTO expertise_area (id, parent_id, name_en, name_hi, name_te, regulated, sort_order) VALUES ($1,$2,$3,$4,$5,$6,500) "
                               "ON CONFLICT (id) DO UPDATE SET status='active', name_en=EXCLUDED.name_en, name_hi=EXCLUDED.name_hi, name_te=EXCLUDED.name_te",
                               slug, req["parent_id"], body.name_en or req["name"], body.name_hi or body.name_en or req["name"], body.name_te or body.name_en or req["name"], body.regulated)
            created = slug
            await conn.execute("INSERT INTO provider_expertise (provider_id, area_id) SELECT member_id, $2 FROM provider WHERE member_id=$1 ON CONFLICT DO NOTHING", req["proposed_by"], slug)
        await conn.execute("UPDATE expertise_request SET status=$2, decided_by=$3, decided_at=now(), created_area=$4 WHERE id=$1",
                           request_id, "approved" if body.approve else "rejected", actor.member_id, created)
        await notifications.notify(conn, req["proposed_by"], "expertise." + ("approved" if body.approve else "rejected"), {"name": req["name"]})
        await audit.record(conn, actor.member_id, "expertise_request.decided", "expertise_request", request_id, {"approved": body.approve, "area": created})
    return {"ok": True, "area": created}


class AreaIn(BaseModel):
    name_en: str
    name_hi: str
    name_te: str
    regulated: bool = False
    status: Literal["active", "disabled"] = "active"
    parent_id: str | None = None


@router.put("/expertise/{area_id}")
async def upsert_area(area_id: str, body: AreaIn, actor: Actor = Depends(admin_actor)):
    await db.execute("INSERT INTO expertise_area (id, parent_id, name_en, name_hi, name_te, regulated, status, sort_order) VALUES ($1,$2,$3,$4,$5,$6,$7,500) "
                     "ON CONFLICT (id) DO UPDATE SET parent_id=$2, name_en=$3, name_hi=$4, name_te=$5, regulated=$6, status=$7",
                     area_id, body.parent_id, body.name_en, body.name_hi, body.name_te, body.regulated, body.status)
    return {"ok": True}


@router.get("/reports")
async def reports(status: str = "open"):
    rows = db.rows(await db.fetch("SELECT * FROM report WHERE status=$1 ORDER BY created_at", status))
    names = await identity.display_names([r["reporter_id"] for r in rows])
    for r in rows:
        r["reporter_name"] = names.get(str(r["reporter_id"]), "")
    return rows


class ReportDecision(BaseModel):
    status: Literal["actioned", "dismissed"]


@router.post("/reports/{report_id}/decide")
async def decide_report(report_id: UUID, body: ReportDecision, actor: Actor = Depends(admin_actor)):
    await db.execute("UPDATE report SET status=$2, decided_by=$3, decided_at=now() WHERE id=$1", report_id, body.status, actor.member_id)
    return {"ok": True}


@router.get("/disputes")
async def disputes(status: str = "open"):
    rows = db.rows(await db.fetch(
        "SELECT d.*, b.service_title, b.gross_minor, b.refund_minor, b.currency, b.status AS booking_status, b.seeker_id, b.provider_id, b.starts_at "
        "FROM dispute d JOIN booking b ON b.id=d.booking_id WHERE d.status=$1 ORDER BY d.created_at", status))
    names = await identity.display_names([r["seeker_id"] for r in rows] + [r["provider_id"] for r in rows] + [r["opened_by"] for r in rows])
    for r in rows:
        r["seeker_name"] = names.get(str(r["seeker_id"]), ""); r["provider_name"] = names.get(str(r["provider_id"]), ""); r["opened_by_name"] = names.get(str(r["opened_by"]), "")
    return rows


class DisputeDecision(BaseModel):
    refund_percent: int = Field(ge=0, le=100)
    resolution: str = Field(max_length=1000)


@router.post("/disputes/{dispute_id}/decide")
async def decide_dispute(dispute_id: UUID, body: DisputeDecision, actor: Actor = Depends(admin_actor)):
    async with db.tx() as conn:
        d = await conn.fetchrow("SELECT * FROM dispute WHERE id=$1 AND status='open'", dispute_id)
        if not d:
            raise not_found("dispute")
        b = await bk.get(conn, d["booking_id"])
        refundable_percent = max(0, 100 - round(100 * b["refund_minor"] / b["gross_minor"])) if b["gross_minor"] else 0
        pct = min(body.refund_percent, refundable_percent)
        refunded = await bk._refund(conn, b, pct, f"dispute {dispute_id}") if pct else 0
        status = "refunded" if pct >= refundable_percent and pct > 0 else ("partially_refunded" if pct else "closed")
        await conn.execute("UPDATE dispute SET status=$2, resolution=$3, refund_minor=$4, decided_by=$5, decided_at=now() WHERE id=$1", dispute_id, status, body.resolution, refunded, actor.member_id)
        if refunded:
            await conn.execute("UPDATE booking SET payout_status = CASE WHEN payout_status='eligible' AND provider_payable_minor - refund_minor <= 0 THEN 'none' ELSE payout_status END WHERE id=$1", b["id"])
        for m in (b["seeker_id"], b["provider_id"]):
            await notifications.notify(conn, m, "dispute.decided", {"title": b["service_title"], "refund_minor": refunded}, b["id"])
        await audit.record(conn, actor.member_id, "dispute.decided", "booking", b["id"], {"refund_percent": pct, "refunded_minor": refunded})
    return {"status": status, "refunded_minor": refunded}


@router.get("/transactions")
async def transactions(limit: int = 100):
    rows = db.rows(await db.fetch(
        "SELECT id, service_title, provider_id, seeker_id, starts_at, status, gross_minor, platform_fee_minor, refund_minor, provider_payable_minor, payout_status, currency, created_at "
        "FROM booking WHERE status <> 'expired' ORDER BY created_at DESC LIMIT $1", limit))
    names = await identity.display_names([r["provider_id"] for r in rows] + [r["seeker_id"] for r in rows])
    for r in rows:
        r["provider_name"] = names.get(str(r["provider_id"]), ""); r["seeker_name"] = names.get(str(r["seeker_id"]), "")
    return rows


@router.get("/settings")
async def settings_get():
    return {r["key"]: r["value"] for r in await db.fetch("SELECT key, value FROM platform_setting ORDER BY key")}


class SettingIn(BaseModel):
    value: dict | list | int | float | str | bool


@router.put("/settings/{key}")
async def settings_put(key: str, body: SettingIn, actor: Actor = Depends(admin_actor)):
    if key not in ("platform_fee_percent", "cancellation_policy", "payout_hold_hours", "review_window_days", "retention_recording_days", "retention_file_days"):
        raise DomainError("unknown_setting", "Unknown setting.", 422)
    async with db.tx() as conn:
        await conn.execute("INSERT INTO platform_setting (key, value) VALUES ($1,$2) ON CONFLICT (key) DO UPDATE SET value=$2", key, body.value)
        await audit.record(conn, actor.member_id, "setting.changed", "setting", key, {"value": body.value})
    return {"ok": True}


@router.get("/audit")
async def audit_log(limit: int = 100):
    return db.rows(await db.fetch("SELECT * FROM audit_log ORDER BY id DESC LIMIT $1", limit))
