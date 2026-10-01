"""The provider's own side: profile, expertise, evidence, verification
status, services, availability, bookings, earnings and payouts."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel, Field

from app import db
from app.components import audit, bookings, notifications, places, providers, storage
from app.errors import DomainError, not_found
from app.i18n import area_name, request_language
from app.identity import Actor, current_actor

router = APIRouter(prefix="/provide", tags=["provide"])


async def _own(actor: Actor) -> dict:
    p = await db.fetchrow("SELECT * FROM provider WHERE member_id=$1", actor.member_id)
    if not p:
        raise DomainError("not_a_provider", "Set up your consultant profile first.", 404)
    return dict(p)


class ProfileIn(BaseModel):
    headline: str = Field(max_length=120)
    intro: str = Field(default="", max_length=2000)
    city: str | None = Field(default=None, max_length=80)
    country: str = "IN"
    timezone: str = "Asia/Kolkata"
    languages: list[str] = ["en"]
    links: dict[str, str] = {}
    photo_url: str | None = None
    expertise: list[dict] = []   # [{id, years, primary}]


@router.get("/profile")
async def get_profile(request: Request, actor: Actor = Depends(current_actor)):
    p = await db.fetchrow("SELECT * FROM provider WHERE member_id=$1", actor.member_id)
    if not p:
        return None
    lang = request_language(request)
    async with db.pool().acquire() as conn:
        d = dict(p)
        d["expertise"] = await providers.expertise_of(conn, actor.member_id, lang)
        d["verified"] = await providers.verifications(conn, actor.member_id)
        d["evidence"] = db.rows(await conn.fetch(
            "SELECT id, kind, title, issuer, year_from, year_to, reference_no, status, review_note, document_name, (document_url IS NOT NULL) AS has_document "
            "FROM provider_evidence WHERE provider_id=$1 ORDER BY kind, created_at", actor.member_id))
        d["display_name"] = actor.display_name
        req = await conn.fetch(
            "SELECT DISTINCT unnest(required_dimensions) AS dim FROM compliance_rule c JOIN provider_expertise pe ON pe.area_id=c.area_id "
            "WHERE pe.provider_id=$1 AND (c.jurisdiction=$2 OR c.jurisdiction='*')", actor.member_id, d["country"])
        d["required_dimensions"] = sorted({r["dim"] for r in req})
        return d


@router.put("/profile")
async def put_profile(body: ProfileIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        existing = await conn.fetchrow("SELECT status FROM provider WHERE member_id=$1", actor.member_id)
        await conn.execute(
            """
            INSERT INTO provider (member_id, headline, intro, city, country, timezone, languages, links, photo_url)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (member_id) DO UPDATE SET headline=$2, intro=$3, city=$4, country=$5, timezone=$6, languages=$7, links=$8,
              photo_url=coalesce($9, provider.photo_url), updated_at=now()
            """,
            actor.member_id, body.headline, body.intro, places.label((body.city or "").strip() or None, "en"), body.country, body.timezone, body.languages, body.links, body.photo_url,
        )
        await conn.execute("DELETE FROM provider_expertise WHERE provider_id=$1", actor.member_id)
        for i, e in enumerate(body.expertise[:8]):
            if await conn.fetchval("SELECT 1 FROM expertise_area WHERE id=$1 AND status='active'", e.get("id")):
                await conn.execute(
                    "INSERT INTO provider_expertise (provider_id, area_id, years, is_primary) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING",
                    actor.member_id, e["id"], int(e.get("years") or 0), bool(e.get("primary", i == 0)))
        if not existing:
            await audit.record(conn, actor.member_id, "provider.created", "provider", actor.member_id)
    return {"ok": True}


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), actor: Actor = Depends(current_actor)):
    await _own(actor)
    data = await file.read()
    ext = storage.check(file.content_type or "", data, storage.IMAGE_TYPES, 5)
    key = storage.save(f"public/photos/{actor.member_id}", data, ext)
    url = "/media/" + key.removeprefix("public/")
    await db.execute("UPDATE provider SET photo_url=$2, updated_at=now() WHERE member_id=$1", actor.member_id, url)
    return {"photo_url": url}


class EvidenceIn(BaseModel):
    kind: Literal["experience", "qualification", "certification", "registration", "business", "portfolio"]
    title: str = Field(max_length=160)
    issuer: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    reference_no: str | None = None
    document_url: str | None = None


@router.post("/evidence")
async def add_evidence(body: EvidenceIn, actor: Actor = Depends(current_actor)):
    await _own(actor)
    row = await db.fetchrow(
        "INSERT INTO provider_evidence (provider_id, kind, title, issuer, year_from, year_to, reference_no, document_url) VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *",
        actor.member_id, body.kind, body.title, body.issuer, body.year_from, body.year_to, body.reference_no, body.document_url)
    return dict(row)


@router.post("/evidence/{evidence_id}/document")
async def upload_document(evidence_id: UUID, file: UploadFile = File(...), actor: Actor = Depends(current_actor)):
    """Private proof for a piece of evidence (certificate, registration). Seen only
    by its owner and ForKhatri reviewers, never shown on the public profile."""
    ev = await db.fetchrow("SELECT id FROM provider_evidence WHERE id=$1 AND provider_id=$2", evidence_id, actor.member_id)
    if not ev:
        raise not_found("evidence")
    data = await file.read()
    ext = storage.check(file.content_type or "", data, storage.DOCUMENT_TYPES, 10)
    key, _ = storage.save_private(f"private/evidence/{actor.member_id}", data, ext)
    async with db.tx() as conn:
        await conn.execute("UPDATE provider_evidence SET document_url=$2, document_name=$3, document_mime=$4, document_encrypted=true, status='submitted' WHERE id=$1",
                           evidence_id, key, (file.filename or "document")[:120], file.content_type)
        await audit.record(conn, actor.member_id, "evidence.document_uploaded", "provider", actor.member_id, {"evidence_id": str(evidence_id)})
    return {"ok": True, "document_name": file.filename}


@router.get("/evidence/{evidence_id}/document")
async def own_document(evidence_id: UUID, actor: Actor = Depends(current_actor)):
    ev = await db.fetchrow("SELECT document_url, document_name, document_mime, document_encrypted FROM provider_evidence WHERE id=$1 AND provider_id=$2", evidence_id, actor.member_id)
    if not ev or not ev["document_url"]:
        raise not_found("document")
    return storage.serve(ev["document_url"], ev["document_encrypted"], ev["document_mime"], ev["document_name"])


@router.delete("/evidence/{evidence_id}")
async def delete_evidence(evidence_id: UUID, actor: Actor = Depends(current_actor)):
    await db.execute("DELETE FROM provider_evidence WHERE id=$1 AND provider_id=$2", evidence_id, actor.member_id)
    return {"ok": True}


@router.post("/submit")
async def submit_for_review(actor: Actor = Depends(current_actor)):
    p = await _own(actor)
    if not p["headline"]:
        raise DomainError("incomplete", "Add a headline before submitting.", 422)
    n = await db.fetchval("SELECT count(*) FROM provider_expertise WHERE provider_id=$1", actor.member_id)
    if not n:
        raise DomainError("incomplete", "Add at least one area of expertise.", 422)
    async with db.tx() as conn:
        await conn.execute("UPDATE provider SET status='pending_review', submitted_at=now(), updated_at=now() WHERE member_id=$1 AND status IN ('draft','changes_requested')", actor.member_id)
        await audit.record(conn, actor.member_id, "provider.submitted", "provider", actor.member_id)
    return {"status": "pending_review"}


class ExpertiseRequestIn(BaseModel):
    name: str = Field(max_length=80)
    parent_id: str | None = None
    note: str | None = None


@router.post("/expertise-requests")
async def request_expertise(body: ExpertiseRequestIn, actor: Actor = Depends(current_actor)):
    row = await db.fetchrow("INSERT INTO expertise_request (proposed_by, name, parent_id, note) VALUES ($1,$2,$3,$4) RETURNING *",
                            actor.member_id, body.name, body.parent_id, body.note)
    return dict(row)


@router.get("/expertise-requests")
async def my_expertise_requests(actor: Actor = Depends(current_actor)):
    return db.rows(await db.fetch("SELECT * FROM expertise_request WHERE proposed_by=$1 ORDER BY created_at DESC", actor.member_id))


# --- Services --------------------------------------------------------------------

class ServiceIn(BaseModel):
    title: str = Field(max_length=100)
    description: str = Field(default="", max_length=2000)
    outcomes: list[str] = []
    area_id: str
    duration_min: int = Field(ge=15, le=240)
    price_minor: int = Field(gt=0)
    formats: list[str] = ["video"]
    min_notice_hours: int = Field(default=12, ge=0, le=168)
    max_advance_days: int = Field(default=30, ge=1, le=90)
    buffer_min: int = Field(default=10, ge=0, le=60)
    recording_allowed: bool = False
    allow_custom_time: bool = False
    status: Literal["active", "paused", "archived"] = "active"


@router.get("/services")
async def my_services(request: Request, actor: Actor = Depends(current_actor)):
    lang = request_language(request)
    rows = await db.fetch("SELECT s.*, a.name_en, a.name_hi, a.name_te FROM service s JOIN expertise_area a ON a.id=s.area_id WHERE s.provider_id=$1 AND s.status<>'archived' ORDER BY s.created_at", actor.member_id)
    out = []
    for r in rows:
        d = dict(r); d["area_name"] = area_name(d, lang); out.append(d)
    return out


async def _check_compliance(conn, provider_id: UUID, area_id: str) -> None:
    country = await conn.fetchval("SELECT country FROM provider WHERE member_id=$1", provider_id)
    rule = await conn.fetchrow("SELECT required_dimensions FROM compliance_rule WHERE area_id=$1 AND jurisdiction IN ($2,'*') ORDER BY (jurisdiction='*') LIMIT 1", area_id, country)
    if not rule:
        return
    have = set(await providers.verifications(conn, provider_id))
    missing = [d for d in rule["required_dimensions"] if d not in have]
    if missing:
        raise DomainError("verification_required", "This area needs verification before you can publish a service.", 422, missing=missing)


@router.post("/services")
async def create_service(body: ServiceIn, actor: Actor = Depends(current_actor)):
    p = await _own(actor)
    async with db.tx() as conn:
        if body.status == "active":
            await _check_compliance(conn, actor.member_id, body.area_id)
        row = await conn.fetchrow(
            """INSERT INTO service (provider_id, area_id, title, description, outcomes, duration_min, price_minor, currency, formats,
               min_notice_hours, max_advance_days, buffer_min, recording_allowed, status, allow_custom_time)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) RETURNING *""",
            actor.member_id, body.area_id, body.title, body.description, body.outcomes, body.duration_min, body.price_minor, p["currency"],
            body.formats, body.min_notice_hours, body.max_advance_days, body.buffer_min, body.recording_allowed, body.status, body.allow_custom_time)
        await audit.record(conn, actor.member_id, "service.created", "service", row["id"], {"price_minor": body.price_minor})
    return dict(row)


@router.put("/services/{service_id}")
async def update_service(service_id: UUID, body: ServiceIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        old = await conn.fetchrow("SELECT * FROM service WHERE id=$1 AND provider_id=$2", service_id, actor.member_id)
        if not old:
            raise not_found("service")
        if body.status == "active":
            await _check_compliance(conn, actor.member_id, body.area_id)
        row = await conn.fetchrow(
            """UPDATE service SET area_id=$3, title=$4, description=$5, outcomes=$6, duration_min=$7, price_minor=$8, formats=$9,
               min_notice_hours=$10, max_advance_days=$11, buffer_min=$12, recording_allowed=$13, status=$14, allow_custom_time=$15, updated_at=now()
               WHERE id=$1 AND provider_id=$2 RETURNING *""",
            service_id, actor.member_id, body.area_id, body.title, body.description, body.outcomes, body.duration_min, body.price_minor,
            body.formats, body.min_notice_hours, body.max_advance_days, body.buffer_min, body.recording_allowed, body.status, body.allow_custom_time)
        if old["price_minor"] != body.price_minor:
            await audit.record(conn, actor.member_id, "service.price_changed", "service", service_id, {"from": old["price_minor"], "to": body.price_minor})
    return dict(row)


# --- Availability ------------------------------------------------------------------

class RuleIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time | None = None
    kind: Literal["window", "slot"] = "window"


class ExceptionIn(BaseModel):
    on_date: date
    start_time: time | None = None
    end_time: time | None = None
    available: bool = False
    note: str | None = None


@router.get("/availability")
async def availability_get(actor: Actor = Depends(current_actor)):
    rules = db.rows(await db.fetch("SELECT id, weekday, start_time::text, end_time::text, kind FROM availability_rule WHERE provider_id=$1 ORDER BY weekday, start_time", actor.member_id))
    ex = db.rows(await db.fetch("SELECT id, on_date, start_time::text, end_time::text, available, note FROM availability_exception WHERE provider_id=$1 AND on_date >= current_date ORDER BY on_date", actor.member_id))
    tz = await db.fetchval("SELECT timezone FROM provider WHERE member_id=$1", actor.member_id)
    return {"rules": rules, "exceptions": ex, "timezone": tz}


@router.put("/availability/rules")
async def availability_put(rules: list[RuleIn], actor: Actor = Depends(current_actor)):
    await _own(actor)
    async with db.tx() as conn:
        await conn.execute("DELETE FROM availability_rule WHERE provider_id=$1", actor.member_id)
        for r in rules:
            end = r.end_time
            if r.kind == "slot":
                # A fixed slot is one exact start time; the stored end only satisfies the row check.
                end = (datetime.combine(date.today(), r.start_time) + timedelta(minutes=1)).time() if r.start_time < time(23, 59) else time(23, 59, 59)
            elif end is None or end <= r.start_time:
                raise DomainError("invalid_window", "End must be after start.", 422)
            await conn.execute("INSERT INTO availability_rule (provider_id, weekday, start_time, end_time, kind) VALUES ($1,$2,$3,$4,$5)",
                               actor.member_id, r.weekday, r.start_time, end, r.kind)
    return {"ok": True}


@router.post("/availability/exceptions")
async def exception_add(body: ExceptionIn, actor: Actor = Depends(current_actor)):
    await _own(actor)
    row = await db.fetchrow("INSERT INTO availability_exception (provider_id, on_date, start_time, end_time, available, note) VALUES ($1,$2,$3,$4,$5,$6) RETURNING id",
                            actor.member_id, body.on_date, body.start_time, body.end_time, body.available, body.note)
    return {"id": str(row["id"])}


@router.delete("/availability/exceptions/{exception_id}")
async def exception_delete(exception_id: UUID, actor: Actor = Depends(current_actor)):
    await db.execute("DELETE FROM availability_exception WHERE id=$1 AND provider_id=$2", exception_id, actor.member_id)
    return {"ok": True}


# --- Dashboard, earnings, payouts -------------------------------------------------------

@router.get("/dashboard")
async def dashboard(request: Request, actor: Actor = Depends(current_actor)):
    p = await _own(actor)
    async with db.pool().acquire() as conn:
        rep = await providers.reputation(conn, actor.member_id)
        upcoming = db.rows(await conn.fetch(
            "SELECT b.id, b.service_title, b.starts_at, b.ends_at, b.status, b.brief, m.display_name AS seeker_name FROM booking b LEFT JOIN member m ON m.member_id=b.seeker_id "
            "WHERE b.provider_id=$1 AND (b.status IN ('confirmed','in_progress') OR (b.status='pending_payment' AND b.pay_by IS NOT NULL)) AND b.ends_at > now() ORDER BY b.starts_at LIMIT 10", actor.member_id))
        earnings = await conn.fetchrow(
            """SELECT coalesce(sum(CASE WHEN status='completed' THEN provider_payable_minor - refund_minor END),0) AS earned,
                      coalesce(sum(CASE WHEN payout_status='eligible' THEN provider_payable_minor - refund_minor END),0) AS pending_payout,
                      coalesce(sum(CASE WHEN payout_status='paid' THEN provider_payable_minor - refund_minor END),0) AS paid_out,
                      coalesce(sum(CASE WHEN status='completed' AND completed_at > now() - interval '30 days' THEN provider_payable_minor - refund_minor END),0) AS last_30
               FROM booking WHERE provider_id=$1""", actor.member_id)
        verified = await providers.verifications(conn, actor.member_id)
        services = await conn.fetchval("SELECT count(*) FROM service WHERE provider_id=$1 AND status='active'", actor.member_id)
        rules = await conn.fetchval("SELECT count(*) FROM availability_rule WHERE provider_id=$1", actor.member_id)
    from app.components import badges as badge_rules
    async with db.pool().acquire() as conn:
        m = await badge_rules.metrics(conn, actor.member_id)
        earned_now = badge_rules.earned_levels(m)
        badge_view = {"earned": await badge_rules.for_display(conn, actor.member_id), "next": badge_rules.next_milestones(m, earned_now),
                      "standing": badge_rules.standing(m)}
        from app.components import insights as insight_rules
        found = {"visibility": await insight_rules.visibility(conn, actor.member_id), "strength": await insight_rules.strength(conn, actor.member_id),
                 "rank": await insight_rules.rank(conn, actor.member_id, request_language(request)) if p["status"] == "approved" else None,
                 "reply_hours": await providers.reply_hours(conn, actor.member_id)}
    open_questions = db.rows(await db.fetch(
        "SELECT p.id, s.title, q.body, q.due_at, m.display_name AS buyer_name FROM purchase p JOIN question q ON q.purchase_id=p.id JOIN service s ON s.id=q.service_id "
        "LEFT JOIN member m ON m.member_id=p.buyer_id WHERE p.provider_id=$1 AND p.kind='question' AND p.status='active' ORDER BY q.due_at", actor.member_id))
    return {"available_until": p["available_until"], "open_questions": open_questions, "badges": badge_view, "status": p["status"], "review_note": p["review_note"], "reputation": rep, "upcoming": upcoming, "earnings": dict(earnings),
            "verified": verified, "active_services": services, "has_availability": rules > 0, "currency": p["currency"],
            "found": found}


@router.get("/earnings")
async def earnings(actor: Actor = Depends(current_actor)):
    await _own(actor)
    rows = db.rows(await db.fetch(
        "SELECT b.id, b.service_title, b.starts_at, b.status, b.gross_minor, b.platform_fee_minor, b.refund_minor, b.provider_payable_minor, b.payout_status, b.currency, m.display_name AS seeker_name "
        "FROM booking b LEFT JOIN member m ON m.member_id=b.seeker_id WHERE b.provider_id=$1 AND b.status NOT IN ('pending_payment','expired') ORDER BY b.starts_at DESC LIMIT 100", actor.member_id))
    payouts = db.rows(await db.fetch("SELECT * FROM payout WHERE provider_id=$1 ORDER BY created_at DESC", actor.member_id))
    return {"bookings": rows, "payouts": payouts}


class PayoutMethodIn(BaseModel):
    kind: Literal["upi", "bank"]
    holder_name: str = Field(min_length=2, max_length=80)
    upi_id: str | None = Field(default=None, max_length=80)
    account_number: str | None = Field(default=None, max_length=24)
    ifsc: str | None = Field(default=None, max_length=11)


@router.get("/payout-method")
async def payout_method(actor: Actor = Depends(current_actor)):
    r = await db.fetchrow("SELECT kind, holder_name, ifsc, last4, updated_at FROM payout_method WHERE provider_id=$1", actor.member_id)
    return dict(r) if r else None


@router.put("/payout-method")
async def set_payout_method(body: PayoutMethodIn, actor: Actor = Depends(current_actor)):
    import re as _re
    from app.components import privacy
    await _own(actor)
    if body.kind == "upi":
        if not body.upi_id or not _re.fullmatch(r"[A-Za-z0-9.\-_]{2,64}@[A-Za-z]{2,32}", body.upi_id):
            raise DomainError("invalid_upi", "Enter a UPI id like name@bank.", 422)
        secret, last4, ifsc = body.upi_id, body.upi_id.split("@")[0][-4:], None
    else:
        acct = (body.account_number or "").replace(" ", "")
        if not _re.fullmatch(r"\d{9,18}", acct):
            raise DomainError("invalid_account", "Enter a 9–18 digit account number.", 422)
        if not body.ifsc or not _re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", body.ifsc.upper()):
            raise DomainError("invalid_ifsc", "Enter a valid IFSC code.", 422)
        secret, last4, ifsc = acct, acct[-4:], body.ifsc.upper()
    async with db.tx() as conn:
        await conn.execute(
            "INSERT INTO payout_method (provider_id, kind, holder_name, secret, ifsc, last4) VALUES ($1,$2,$3,$4,$5,$6) "
            "ON CONFLICT (provider_id) DO UPDATE SET kind=$2, holder_name=$3, secret=$4, ifsc=$5, last4=$6, updated_at=now()",
            actor.member_id, body.kind, body.holder_name, privacy.encrypt(secret), ifsc, last4)
        await audit.record(conn, actor.member_id, "payout_method.changed", "provider", actor.member_id, {"kind": body.kind, "last4": last4})
    return {"ok": True, "last4": last4}


@router.post("/payouts")
async def payout(actor: Actor = Depends(current_actor)):
    await _own(actor)
    async with db.tx() as conn:
        return await bookings.request_payout(conn, actor.member_id)
