"""Bookings from either side, the conversation attached to each booking,
reviews, disputes and reports."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app import db, identity
from app.components import audit, availability, bookings, notifications, workspace
from app.errors import DomainError, forbidden, not_found
from app.identity import Actor, current_actor

router = APIRouter(tags=["bookings"])


class BookingIn(BaseModel):
    service_id: UUID
    starts_at: datetime
    brief: str = Field(default="", max_length=1500)
    timezone: str = "Asia/Kolkata"


def _serialise(b: dict, names: dict[str, str], viewer: UUID) -> dict:
    d = {k: v for k, v in b.items() if k != "checkout"}
    d["provider_name"] = names.get(str(b["provider_id"]), "")
    d["seeker_name"] = names.get(str(b["seeker_id"]), "")
    d["role"] = "seeker" if b["seeker_id"] == viewer else "provider"
    if "checkout" in b:
        d["checkout"] = b["checkout"]
    return d


@router.post("/bookings", status_code=201)
async def create(body: BookingIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        svc = await conn.fetchrow("SELECT * FROM service WHERE id=$1 AND status='active'", body.service_id)
        if not svc:
            raise not_found("service")
        if await conn.fetchval("SELECT 1 FROM block WHERE (member_id=$1 AND blocked_id=$2) OR (member_id=$2 AND blocked_id=$1)", actor.member_id, svc["provider_id"]):
            raise forbidden("This consultant is not available to you.")
        starts = body.starts_at
        if starts.tzinfo is None:
            raise DomainError("timezone_required", "Send the start time with a time zone.", 422)
        if not await availability.is_free(conn, svc["provider_id"], dict(svc), starts):
            raise DomainError("slot_unavailable", "That time is not available.", 409)
        b = await bookings.create(conn, seeker_id=actor.member_id, service=dict(svc), starts_at=starts, brief=body.brief, seeker_tz=body.timezone)
    names = await identity.display_names([b["provider_id"], b["seeker_id"]])
    return _serialise(b, names, actor.member_id)


class PayIn(BaseModel):
    proof: dict = {}


@router.post("/bookings/{booking_id}/pay")
async def pay(booking_id: UUID, body: PayIn, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        b = await bookings.confirm_payment(conn, booking_id=booking_id, actor_id=actor.member_id, proof=body.proof)
    names = await identity.display_names([b["provider_id"], b["seeker_id"]])
    return _serialise(b, names, actor.member_id)


@router.get("/bookings")
async def list_mine(scope: Literal["upcoming", "past", "all"] = "all", role: Literal["any", "seeker", "provider"] = "any",
                    actor: Actor = Depends(current_actor)):
    where = {"upcoming": "AND (b.status IN ('confirmed','in_progress') OR (b.status='pending_payment' AND b.pay_by IS NOT NULL)) AND b.ends_at > now()",
             "past": "AND NOT (b.status IN ('pending_payment','confirmed','in_progress') AND b.ends_at > now())", "all": ""}[scope]
    who = {"any": "(b.seeker_id=$1 OR b.provider_id=$1)", "seeker": "b.seeker_id=$1", "provider": "b.provider_id=$1"}[role]
    rows = db.rows(await db.fetch(
        f"SELECT b.*, p.photo_url AS provider_photo, (b.recap IS NOT NULL AND b.recap <> '') AS has_recap FROM booking b "
        f"LEFT JOIN provider p ON p.member_id=b.provider_id WHERE {who} AND b.status <> 'expired' {where} "
        f"ORDER BY b.starts_at {'ASC' if scope == 'upcoming' else 'DESC'} LIMIT 100",
        actor.member_id))
    ids = {r["provider_id"] for r in rows} | {r["seeker_id"] for r in rows}
    names = await identity.display_names(list(ids))
    reviewed = {r["booking_id"] for r in await db.fetch("SELECT booking_id FROM review WHERE reviewer_id=$1", actor.member_id)}
    out = []
    for r in rows:
        r.pop("recap", None)  # the list only needs to know a recap exists
        d = _serialise(r, names, actor.member_id)
        d["reviewed"] = r["id"] in reviewed
        d["unread"] = 0
        out.append(d)
    return out


@router.get("/bookings/{booking_id}/timeline")
async def timeline(booking_id: UUID, actor: Actor = Depends(current_actor)):
    """What has happened on this booking, oldest first, from the rows that record it:
    the booking, payment and refund ledger, reminders, room joins, completion, recap,
    cancellation, no-show, review, dispute and payout. Nothing is inferred."""
    b = await bookings.get(db, booking_id)
    role = bookings.participant(b, actor.member_id)
    me = actor.member_id
    ev: list[dict] = []

    def add(kind: str, at, who: str | None = None, **params):
        if at:
            ev.append({"kind": kind, "at": at, "who": who, "params": params})

    def side(member_id) -> str | None:
        if member_id is None:
            return None
        return "you" if member_id == me else "other"

    tr = await db.fetchrow("SELECT created_at, decided_at FROM time_request WHERE booking_id=$1", booking_id)
    if tr:
        add("time_requested", tr["created_at"], side(b["seeker_id"]))
        add("time_accepted", tr["decided_at"], side(b["provider_id"]))
    elif b["created_at"] <= b["starts_at"]:  # sample rows loaded after the fact carry no booking moment
        add("booked_package" if b["purchase_id"] else "booked", b["created_at"], side(b["seeker_id"]))
    for a in await db.fetch("SELECT actor_id, action, detail, at FROM audit_log WHERE target_kind='booking' AND target_id=$1 "
                            "AND action IN ('payment.succeeded','booking.no_show') ORDER BY at", str(booking_id)):
        if a["action"] == "payment.succeeded":
            add("paid", a["at"], side(a["actor_id"]), amount_minor=b["gross_minor"])
        else:
            add(b["status"] if b["status"].startswith("no_show") else "no_show", a["at"], side(a["actor_id"]))
    add("reminder_day", b.get("reminded_24h_at"))
    add("reminder_now", b.get("reminded_15m_at"))
    for j in await db.fetch("SELECT member_id, min(at) AS at FROM session_event WHERE booking_id=$1 AND kind='joined' GROUP BY member_id", booking_id):
        add("joined", j["at"], side(j["member_id"]))
    if b["status"] == "completed":
        add("completed", b["completed_at"])
    add("recap", b.get("recap_at"))
    if b["cancelled_at"]:
        add(b["status"] if b["status"].startswith("cancelled") else "cancelled", b["cancelled_at"], side(b["cancelled_by"]))
    for r in await db.fetch("SELECT amount_minor, created_at FROM ledger_entry WHERE booking_id=$1 AND kind='refund' ORDER BY created_at", booking_id):
        add("refunded", r["created_at"], amount_minor=-r["amount_minor"])
    rv = await db.fetchrow("SELECT overall, created_at FROM review WHERE booking_id=$1", booking_id)
    if rv:
        add("reviewed", rv["created_at"], side(b["seeker_id"]), overall=rv["overall"])
    for d in await db.fetch("SELECT opened_by, status, created_at, decided_at, refund_minor FROM dispute WHERE booking_id=$1 ORDER BY created_at", booking_id):
        add("dispute_opened", d["created_at"], side(d["opened_by"]))
        if d["status"] != "open":
            add("dispute_decided", d["decided_at"], status=d["status"], amount_minor=d["refund_minor"])
    if role == "provider" and b["payout_id"]:
        paid = await db.fetchval("SELECT paid_at FROM payout WHERE id=$1", b["payout_id"])
        add("payout", paid, amount_minor=b["provider_payable_minor"] - b["refund_minor"])
    ev.sort(key=lambda e: e["at"])
    return {"events": ev, "currency": b["currency"]}


@router.get("/bookings/{booking_id}")
async def get_one(booking_id: UUID, actor: Actor = Depends(current_actor)):
    b = await bookings.get(db, booking_id)
    bookings.participant(b, actor.member_id)
    names = await identity.display_names([b["provider_id"], b["seeker_id"]])
    d = _serialise(b, names, actor.member_id)
    d["reviewed"] = bool(await db.fetchval("SELECT 1 FROM review WHERE booking_id=$1", booking_id))
    d["review"] = dict(r) if (r := await db.fetchrow("SELECT overall, expertise, communication, professionalism, punctuality, body FROM review WHERE booking_id=$1", booking_id)) else None
    d["dispute"] = dict(r) if (r := await db.fetchrow("SELECT id, status, reason, resolution, refund_minor, created_at FROM dispute WHERE booking_id=$1 ORDER BY created_at DESC LIMIT 1", booking_id)) else None
    d["provider_photo"] = await db.fetchval("SELECT photo_url FROM provider WHERE member_id=$1", b["provider_id"])
    d["follow_ups"] = db.rows(await db.fetch(
        "SELECT id, sessions, price_minor, valid_days FROM package WHERE service_id=$1 AND active ORDER BY sessions", b["service_id"]))         if b["status"] == "completed" and b["seeker_id"] == actor.member_id else []
    d["service_price_minor"] = await db.fetchval("SELECT price_minor FROM service WHERE id=$1", b["service_id"])
    return d


class Reason(BaseModel):
    reason: str = Field(default="", max_length=500)


@router.post("/bookings/{booking_id}/cancel")
async def cancel(booking_id: UUID, body: Reason, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        b = await bookings.cancel(conn, booking_id=booking_id, actor_id=actor.member_id, reason=body.reason)
    await workspace.broadcast(booking_id, {"type": "booking", "status": b["status"]})
    return {"status": b["status"], "refund_minor": b["refund_minor"]}


@router.post("/bookings/{booking_id}/complete")
async def complete(booking_id: UUID, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        b = await bookings.complete(conn, booking_id=booking_id, actor_id=actor.member_id)
    await workspace.broadcast(booking_id, {"type": "booking", "status": b["status"]})
    return {"status": b["status"]}


@router.post("/bookings/{booking_id}/no-show")
async def no_show(booking_id: UUID, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        b = await bookings.no_show(conn, booking_id=booking_id, actor_id=actor.member_id)
    await workspace.broadcast(booking_id, {"type": "booking", "status": b["status"]})
    return {"status": b["status"], "refund_minor": b["refund_minor"]}


# --- Conversation (pre- and post-booking, same thread) ----------------------------------

@router.get("/bookings/{booking_id}/messages")
async def messages(booking_id: UUID, after: int = 0, actor: Actor = Depends(current_actor)):
    b = await bookings.get(db, booking_id)
    bookings.participant(b, actor.member_id)
    rows = db.rows(await db.fetch("SELECT id, sender_id, kind, body, file_id, created_at FROM message WHERE booking_id=$1 AND id > $2 ORDER BY id LIMIT 200", booking_id, after))
    return rows


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


@router.post("/bookings/{booking_id}/messages", status_code=201)
async def send_message(booking_id: UUID, body: MessageIn, actor: Actor = Depends(current_actor)):
    b = await bookings.get(db, booking_id)
    role = bookings.participant(b, actor.member_id)
    if b["status"] in ("expired",):
        raise DomainError("closed", "This conversation is closed.", 409)
    async with db.tx() as conn:
        row = await conn.fetchrow("INSERT INTO message (booking_id, sender_id, kind, body) VALUES ($1,$2,'chat',$3) RETURNING id, sender_id, kind, body, file_id, created_at", booking_id, actor.member_id, body.body)
        other = b["provider_id"] if role == "seeker" else b["seeker_id"]
        if not workspace.room(booking_id).sockets.get(str(other)):
            await notifications.notify(conn, other, "message.new", {"title": b["service_title"], "from": actor.display_name}, booking_id)
    msg = dict(row)
    await workspace.broadcast(booking_id, {"type": "chat", "message": msg})
    return msg


# --- Review ----------------------------------------------------------------------------

class ReviewIn(BaseModel):
    overall: int = Field(ge=1, le=5)
    expertise: int = Field(ge=1, le=5)
    communication: int = Field(ge=1, le=5)
    professionalism: int = Field(ge=1, le=5)
    punctuality: int = Field(ge=1, le=5)
    body: str = Field(default="", max_length=1500)


@router.post("/bookings/{booking_id}/review", status_code=201)
async def review(booking_id: UUID, body: ReviewIn, actor: Actor = Depends(current_actor)):
    b = await bookings.get(db, booking_id)
    if b["seeker_id"] != actor.member_id:
        raise forbidden("Only the person who booked can review.")
    if b["status"] != "completed":
        raise DomainError("not_completed", "Reviews open after the consultation is completed.", 409)
    async with db.tx() as conn:
        try:
            await conn.execute(
                "INSERT INTO review (booking_id, provider_id, reviewer_id, overall, expertise, communication, professionalism, punctuality, body) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)",
                booking_id, b["provider_id"], actor.member_id, body.overall, body.expertise, body.communication, body.professionalism, body.punctuality, body.body)
        except Exception:
            raise DomainError("already_reviewed", "You already reviewed this consultation.", 409) from None
        await notifications.notify(conn, b["provider_id"], "review.received", {"overall": body.overall, "title": b["service_title"]}, booking_id)
        from app.components import badges
        await badges.refresh(conn, b["provider_id"])
    return {"ok": True}


# --- Dispute & report ----------------------------------------------------------------------

@router.post("/bookings/{booking_id}/dispute", status_code=201)
async def dispute(booking_id: UUID, body: Reason, actor: Actor = Depends(current_actor)):
    b = await bookings.get(db, booking_id)
    bookings.participant(b, actor.member_id)
    if b["status"] in ("pending_payment", "expired"):
        raise DomainError("not_disputable", "Nothing to dispute yet.", 409)
    async with db.tx() as conn:
        if await conn.fetchval("SELECT 1 FROM dispute WHERE booking_id=$1 AND status='open'", booking_id):
            raise DomainError("dispute_open", "A dispute is already open.", 409)
        row = await conn.fetchrow("INSERT INTO dispute (booking_id, opened_by, reason) VALUES ($1,$2,$3) RETURNING id", booking_id, actor.member_id, body.reason or "unspecified")
        await audit.record(conn, actor.member_id, "dispute.opened", "booking", booking_id)
    return {"id": str(row["id"])}


class ReportIn(BaseModel):
    target_kind: Literal["provider", "service", "booking", "message", "member"]
    target_id: str
    reason: str = Field(max_length=80)
    detail: str = Field(default="", max_length=1000)


@router.post("/reports", status_code=201)
async def report(body: ReportIn, actor: Actor = Depends(current_actor)):
    row = await db.fetchrow("INSERT INTO report (reporter_id, target_kind, target_id, reason, detail) VALUES ($1,$2,$3,$4,$5) RETURNING id",
                            actor.member_id, body.target_kind, body.target_id, body.reason, body.detail)
    return {"id": str(row["id"])}
