"""Packages, paid questions, instant availability, recap and calendar files."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app import db, identity
from app.components import availability, bookings, purchases
from app.errors import DomainError, not_found
from app.identity import Actor, current_actor
from app.settings import get_settings

router = APIRouter(tags=["offers"])


# --- Packages (consultant) ------------------------------------------------------------

class PackageIn(BaseModel):
    # Follow-ups: 1–3 check-ins on the same problem, not a course.
    sessions: int = Field(ge=1, le=3)
    price_minor: int = Field(gt=0)
    valid_days: int = Field(default=60, ge=30, le=90)
    active: bool = True


@router.get("/services/{service_id}/packages")
async def service_packages(service_id: UUID):
    """Follow-up offers of a service (shown to people who have completed a consultation on it)."""
    return db.rows(await db.fetch("SELECT id, sessions, price_minor, valid_days FROM package WHERE service_id=$1 AND active ORDER BY sessions", service_id))


@router.post("/provide/services/{service_id}/packages", status_code=201)
async def add_package(service_id: UUID, body: PackageIn, actor: Actor = Depends(current_actor)):
    svc = await db.fetchrow("SELECT price_minor FROM service WHERE id=$1 AND provider_id=$2", service_id, actor.member_id)
    if not svc:
        raise not_found("service")
    if body.price_minor >= svc["price_minor"] * body.sessions:
        raise DomainError("package_not_cheaper", "Follow-ups should cost less than booking the same sessions one by one.", 422)
    row = await db.fetchrow("INSERT INTO package (service_id, sessions, price_minor, valid_days, active) VALUES ($1,$2,$3,$4,$5) RETURNING id",
                            service_id, body.sessions, body.price_minor, body.valid_days, body.active)
    return {"id": str(row["id"])}


@router.delete("/provide/packages/{package_id}")
async def remove_package(package_id: UUID, actor: Actor = Depends(current_actor)):
    await db.execute("UPDATE package SET active=false WHERE id=$1 AND service_id IN (SELECT id FROM service WHERE provider_id=$2)", package_id, actor.member_id)
    return {"ok": True}


class QuestionSettings(BaseModel):
    question_price_minor: int | None = Field(default=None, gt=0)
    question_answer_days: int = Field(default=3, ge=1, le=7)
    instant_allowed: bool = False


@router.put("/provide/services/{service_id}/offers")
async def service_offers(service_id: UUID, body: QuestionSettings, actor: Actor = Depends(current_actor)):
    n = await db.execute("UPDATE service SET question_price_minor=$3, question_answer_days=$4, instant_allowed=$5, updated_at=now() WHERE id=$1 AND provider_id=$2",
                         service_id, actor.member_id, body.question_price_minor, body.question_answer_days, body.instant_allowed)
    if n.endswith("0"):
        raise not_found("service")
    return {"ok": True}


# --- Buying and using ------------------------------------------------------------------

@router.post("/packages/{package_id}/buy", status_code=201)
async def buy(package_id: UUID, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        p = await purchases.buy_package(conn, buyer_id=actor.member_id, package_id=package_id)
    return {"id": str(p["id"]), "checkout": p["checkout"]}


class PayIn(BaseModel):
    proof: dict = {}


@router.post("/purchases/{purchase_id}/pay")
async def pay(purchase_id: UUID, body: PayIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        p = await purchases.pay(conn, purchase_id=purchase_id, actor_id=actor.member_id, proof=body.proof)
    return {"id": str(p["id"]), "status": p["status"]}


@router.get("/purchases")
async def my_purchases(actor: Actor = Depends(current_actor)):
    rows = db.rows(await db.fetch(
        """SELECT p.*, s.title, s.duration_min, q.body AS question, q.answer, q.due_at, q.answered_at
           FROM purchase p JOIN service s ON s.id=p.service_id LEFT JOIN question q ON q.purchase_id=p.id
           WHERE (p.buyer_id=$1 OR p.provider_id=$1) AND p.status <> 'cancelled' ORDER BY p.created_at DESC LIMIT 100""", actor.member_id))
    names = await identity.display_names([r["buyer_id"] for r in rows] + [r["provider_id"] for r in rows])
    for r in rows:
        r["role"] = "provider" if r["provider_id"] == actor.member_id else "buyer"
        r["buyer_name"] = names.get(str(r["buyer_id"]), ""); r["provider_name"] = names.get(str(r["provider_id"]), "")
        r.pop("external_ref", None)
    return rows


@router.post("/purchases/{purchase_id}/cancel")
async def cancel_package(purchase_id: UUID, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        p = await conn.fetchrow("SELECT buyer_id, kind, status FROM purchase WHERE id=$1", purchase_id)
        if not p or p["buyer_id"] != actor.member_id or p["kind"] != "package" or p["status"] != "active":
            raise DomainError("not_cancellable", "This package cannot be cancelled.", 409)
        amount = await purchases.refund_unused(conn, purchase_id, "cancelled_by_buyer", actor.member_id)
    return {"refund_minor": amount}


class SessionIn(BaseModel):
    starts_at: datetime
    brief: str = Field(default="", max_length=1500)
    timezone: str = "Asia/Kolkata"


@router.post("/purchases/{purchase_id}/book", status_code=201)
async def book_session(purchase_id: UUID, body: SessionIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        p = await conn.fetchrow("SELECT service_id FROM purchase WHERE id=$1", purchase_id)
        if not p:
            raise not_found("package")
        svc = dict(await conn.fetchrow("SELECT * FROM service WHERE id=$1", p["service_id"]))
        if not await availability.is_free(conn, svc["provider_id"], svc, body.starts_at):
            raise DomainError("slot_unavailable", "That time is not available.", 409)
        purchase = await purchases.use_session(conn, purchase_id, actor.member_id, svc["id"])
        b = await bookings.create(conn, seeker_id=actor.member_id, service=svc, starts_at=body.starts_at, brief=body.brief, seeker_tz=body.timezone, purchase=purchase)
    return {"id": str(b["id"]), "status": b["status"]}


# --- Questions -------------------------------------------------------------------------

class AskIn(BaseModel):
    body: str = Field(min_length=10, max_length=3000)


@router.post("/services/{service_id}/questions", status_code=201)
async def ask(service_id: UUID, body: AskIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        p = await purchases.ask(conn, buyer_id=actor.member_id, service_id=service_id, body=body.body)
    return {"id": str(p["id"]), "checkout": p["checkout"]}


class AnswerIn(BaseModel):
    answer: str = Field(min_length=10, max_length=6000)


@router.post("/purchases/{purchase_id}/answer")
async def answer(purchase_id: UUID, body: AnswerIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        await purchases.answer(conn, purchase_id=purchase_id, provider_id=actor.member_id, text=body.answer)
    return {"ok": True}


# --- Available now ---------------------------------------------------------------------

class NowIn(BaseModel):
    minutes: int = Field(ge=0, le=240)


@router.post("/provide/available-now")
async def available_now(body: NowIn, actor: Actor = Depends(current_actor)):
    until = datetime.now(timezone.utc) + timedelta(minutes=body.minutes) if body.minutes else None
    n = await db.execute("UPDATE provider SET available_until=$2 WHERE member_id=$1 AND status='approved'", actor.member_id, until)
    if n.endswith("0"):
        raise DomainError("not_approved", "Only approved consultants can go online.", 409)
    return {"available_until": until.isoformat() if until else None}


# --- Recap and calendar -------------------------------------------------------------------

@router.post("/bookings/{booking_id}/recap")
async def recap(booking_id: UUID, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        b = await bookings.get(conn, booking_id)
        bookings.participant(b, actor.member_id)
        text = await bookings.build_recap(conn, booking_id)
    return {"recap": text}


def _ics_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


@router.get("/bookings/{booking_id}/calendar.ics")
async def calendar(booking_id: UUID, actor: Actor = Depends(current_actor)):
    b = await db.fetchrow("SELECT * FROM booking WHERE id=$1", booking_id)
    if not b:
        raise not_found("booking")
    bookings.participant(dict(b), actor.member_id)
    names = await identity.display_names([b["provider_id"], b["seeker_id"]])
    other = names[str(b["provider_id"] if b["seeker_id"] == actor.member_id else b["seeker_id"])]
    fmt = "%Y%m%dT%H%M%SZ"
    url = f"{get_settings().web_origin}/room/{booking_id}"
    ics = "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ForKhatri//Counsel//EN", "METHOD:PUBLISH", "BEGIN:VEVENT",
        f"UID:{booking_id}@counsel.forkhatri", f"DTSTAMP:{datetime.now(timezone.utc).strftime(fmt)}",
        f"DTSTART:{b['starts_at'].astimezone(timezone.utc).strftime(fmt)}", f"DTEND:{b['ends_at'].astimezone(timezone.utc).strftime(fmt)}",
        f"SUMMARY:{_ics_escape(b['service_title'] + ' · ' + other)}", f"DESCRIPTION:{_ics_escape('Join: ' + url)}", f"URL:{url}",
        "BEGIN:VALARM", "TRIGGER:-PT15M", "ACTION:DISPLAY", "DESCRIPTION:Counsel consultation", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR", ""])
    return Response(ics, media_type="text/calendar", headers={"Content-Disposition": f'attachment; filename="counsel-{str(booking_id)[:8]}.ics"'})
