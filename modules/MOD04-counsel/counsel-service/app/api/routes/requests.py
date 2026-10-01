"""Custom time requests. When a consultant enables them on a service, a seeker
may propose a time outside the listed slots. The consultant accepts (the time
is held as an unpaid booking for 24 hours and the seeker pays) or declines
with a note. Double booking is still refused by the booking constraint."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app import db, identity
from app.components import audit, availability, bookings, notifications
from app.errors import DomainError, forbidden, not_found
from app.identity import Actor, current_actor

router = APIRouter(tags=["time-requests"])

HOLD = timedelta(hours=24)


class RequestIn(BaseModel):
    starts_at: datetime
    brief: str = Field(default="", max_length=1500)
    note: str = Field(default="", max_length=500)
    timezone: str = "Asia/Kolkata"


@router.post("/services/{service_id}/time-requests", status_code=201)
async def propose(service_id: UUID, body: RequestIn, actor: Actor = Depends(current_actor)):
    if body.starts_at.tzinfo is None:
        raise DomainError("timezone_required", "Send the start time with a time zone.", 422)
    async with db.tx() as conn:
        s = await conn.fetchrow("SELECT * FROM service WHERE id=$1 AND status='active'", service_id)
        if not s:
            raise not_found("service")
        if not s["allow_custom_time"]:
            raise DomainError("custom_time_off", "This consultant only takes the listed times.", 409)
        if s["provider_id"] == actor.member_id:
            raise DomainError("own_service", "You cannot book your own service.")
        now = datetime.now(timezone.utc)
        if body.starts_at < now + timedelta(hours=s["min_notice_hours"]) or body.starts_at > now + timedelta(days=s["max_advance_days"]):
            raise DomainError("outside_window", "Pick a time within the consultant's booking window.", 422)
        if await availability.conflicts(conn, s["provider_id"], body.starts_at, s["duration_min"], s["buffer_min"]):
            raise DomainError("slot_taken", "The consultant is already booked then.", 409)
        if await conn.fetchval("SELECT count(*) FROM time_request WHERE seeker_id=$1 AND provider_id=$2 AND status='pending'", actor.member_id, s["provider_id"]) >= 3:
            raise DomainError("too_many_requests", "You already have requests waiting with this consultant.", 429)
        row = await conn.fetchrow(
            "INSERT INTO time_request (service_id, provider_id, seeker_id, starts_at, seeker_timezone, brief, note) VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id",
            service_id, s["provider_id"], actor.member_id, body.starts_at, body.timezone, body.brief, body.note)
        await notifications.notify(conn, s["provider_id"], "time_request.new", {"title": s["title"], "from": actor.display_name, "starts_at": body.starts_at.isoformat()})
    return {"id": str(row["id"])}


@router.get("/time-requests")
async def mine(actor: Actor = Depends(current_actor)):
    await db.execute("UPDATE time_request SET status='expired' WHERE status='pending' AND starts_at < now()")
    rows = db.rows(await db.fetch(
        "SELECT r.*, s.title, s.duration_min, s.price_minor, s.currency FROM time_request r JOIN service s ON s.id=r.service_id "
        "WHERE r.seeker_id=$1 OR r.provider_id=$1 ORDER BY (r.status='pending') DESC, r.starts_at LIMIT 100", actor.member_id))
    names = await identity.display_names([r["seeker_id"] for r in rows] + [r["provider_id"] for r in rows])
    for r in rows:
        r["role"] = "provider" if r["provider_id"] == actor.member_id else "seeker"
        r["seeker_name"] = names.get(str(r["seeker_id"]), "")
        r["provider_name"] = names.get(str(r["provider_id"]), "")
    return rows


async def _own_request(conn, request_id: UUID, actor: Actor, role: str) -> dict:
    r = await conn.fetchrow("SELECT * FROM time_request WHERE id=$1", request_id)
    if not r:
        raise not_found("request")
    if (role == "provider" and r["provider_id"] != actor.member_id) or (role == "seeker" and r["seeker_id"] != actor.member_id):
        raise forbidden()
    if r["status"] != "pending":
        raise DomainError("not_pending", "This request was already answered.", 409)
    return dict(r)


@router.post("/time-requests/{request_id}/accept")
async def accept(request_id: UUID, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        r = await _own_request(conn, request_id, actor, "provider")
        s = dict(await conn.fetchrow("SELECT * FROM service WHERE id=$1", r["service_id"]))
        if await availability.conflicts(conn, s["provider_id"], r["starts_at"], s["duration_min"], s["buffer_min"]):
            raise DomainError("slot_taken", "You are already booked at that time.", 409)
        b = await bookings.create(conn, seeker_id=r["seeker_id"], service=s, starts_at=r["starts_at"], brief=r["brief"], seeker_tz=r["seeker_timezone"])
        pay_by = min(datetime.now(timezone.utc) + HOLD, r["starts_at"])
        await conn.execute("UPDATE booking SET pay_by=$2 WHERE id=$1", b["id"], pay_by)
        await conn.execute("UPDATE time_request SET status='accepted', decided_at=now(), booking_id=$2 WHERE id=$1", request_id, b["id"])
        await notifications.notify(conn, r["seeker_id"], "time_request.accepted", {"title": s["title"], "starts_at": r["starts_at"].isoformat()}, b["id"])
        await audit.record(conn, actor.member_id, "time_request.accepted", "booking", b["id"])
    return {"booking_id": str(b["id"])}


class Reply(BaseModel):
    reply: str = Field(default="", max_length=500)


@router.post("/time-requests/{request_id}/decline")
async def decline(request_id: UUID, body: Reply, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        r = await _own_request(conn, request_id, actor, "provider")
        await conn.execute("UPDATE time_request SET status='declined', reply=$2, decided_at=now() WHERE id=$1", request_id, body.reply)
        title = await conn.fetchval("SELECT title FROM service WHERE id=$1", r["service_id"])
        await notifications.notify(conn, r["seeker_id"], "time_request.declined", {"title": title, "reply": body.reply})
    return {"status": "declined"}


@router.post("/time-requests/{request_id}/withdraw")
async def withdraw(request_id: UUID, actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        await _own_request(conn, request_id, actor, "seeker")
        await conn.execute("UPDATE time_request SET status='withdrawn', decided_at=now() WHERE id=$1", request_id)
    return {"status": "withdrawn"}
