"""Large events with tickets: ticket types, discount codes, organizer contact, QR check-in (Step 3 of
PLAN-places-events-groups.md).

Builds on the paid spots in `payments.py` (hold, pay, waitlist, refund cutoff) and `components/ticketing`; nothing
there is replaced. Every rule is enforced in the database (migration 052) and again here; the web screens only
present what these endpoints already decided.
"""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote as urlquote
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, CurrentMember, DbSession, Locale
from app.components.activity import interface as activity
from app.components.authorization import interface as authz
from app.components.identity_bridge import interface as identity
from app.components.ticketing import interface as ticketing
from app.i18n import translate

router = APIRouter(prefix="/occurrences/{occurrence_id}", tags=["tickets"])

_CODE = re.compile(r"^[A-Za-z0-9_-]{3,24}$")


class QuoteRequest(BaseModel):
    ticket_type_id: UUID | None = None
    code: str | None = Field(default=None, max_length=40)


class TicketTypeBody(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    price_paise: int = Field(ge=100, le=10_000_000)
    quota: int = Field(ge=1, le=100_000)
    active: bool | None = None


class DiscountCodeBody(BaseModel):
    code: str = Field(min_length=3, max_length=24)
    kind: str  # percent | fixed
    value: int = Field(gt=0)  # percent 1..90, or paise (at least 100)
    max_uses: int | None = Field(default=None, ge=1, le=100_000)
    expires_at: datetime | None = None


class DiscountActiveBody(BaseModel):
    active: bool


class ContactBody(BaseModel):
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=120)
    visibility: str = "confirmed"  # confirmed | public
    offer_counsel: bool = False


class CheckinTicketBody(BaseModel):
    code: str = Field(min_length=4, max_length=80)


def _normalise_code(raw: str) -> str:
    """The QR carries `FKT:<code>`; people type it with spaces or dashes in groups. Accept all of those."""
    c = raw.strip()
    if c.upper().startswith("FKT:"):
        c = c[4:]
    return re.sub(r"[\s-]+", "", c).lower()


_REFUSED_STATUS = {"not_allowed": 403, "not_found": 404, "cancelled": 409, "locked": 409, "quota_below_sold": 409, "too_many": 409, "duplicate": 409, "invalid": 422}


def _refused(exc: ticketing.OrganizerWriteRefused, lang: str) -> HTTPException:
    if exc.reason == "not_allowed":
        return HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang))
    if exc.reason == "not_found":
        return HTTPException(status_code=404, detail=translate("occurrence.notFound", lang))
    return HTTPException(status_code=_REFUSED_STATUS.get(exc.reason, 409), detail=translate(f"tix.err.{exc.reason}", lang))


async def _require_organizer(session: DbSession, occurrence_id: UUID, member: CurrentMember, lang: str) -> None:
    try:
        await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=member.member_id)
    except authz.NotFound as exc:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc


def _counsel_url(settings: AppSettings, organizer_member_id: UUID) -> str | None:
    """The Counsel link comes only from configuration; nothing here names a host."""
    base = (settings.counsel_booking_url or "").strip()
    if not base.lower().startswith(("https://", "http://")):
        return None
    return base.replace("{member_id}", urlquote(str(organizer_member_id), safe=""))


# --- member side ----------------------------------------------------------------------------------------------------


@router.get("/ticketing")
async def event_ticketing(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale, settings: AppSettings) -> dict:
    """Everything the event page's ticket section needs: types with seats left, the organizer's contact if this member may see it."""
    try:
        occ = await activity.get(session, occurrence_id=occurrence_id)
    except activity.OccurrenceNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc
    types = await ticketing.ticket_types(session, occurrence_id)
    spots_left = None
    if occ.capacity is not None:
        spots_left = max(occ.capacity - await activity.spots_taken(session, occurrence_id) - await activity.held_spot_count(session, occurrence_id), 0)
    out_types = []
    for tt in types:
        if not tt.active:
            continue
        left = tt.left if spots_left is None else min(tt.left, spots_left)  # the whole event's capacity always applies
        out_types.append({"id": str(tt.id), "name": tt.name, "price_paise": tt.price_paise, "left": left, "sold_out": left <= 0})
    contact = await activity.get_contact(session, occurrence_id=occurrence_id, member_id=member.member_id)
    shared = await activity.contact_visibility(session, occurrence_id)
    counsel = _counsel_url(settings, occ.creator_member_id) if await activity.offers_counsel(session, occurrence_id) else None
    return {
        "tiered": bool(types),
        "types": out_types,
        "contact": {"phone": contact["phone"], "email": contact["email"]} if contact else None,
        "contact_after_booking": bool(shared == "confirmed" and not contact),
        "counsel_url": counsel,
    }


@router.post("/ticket/quote")
async def ticket_quote(occurrence_id: UUID, body: QuoteRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """What this booking would cost with this ticket type and code. Nothing is held or charged."""
    q = await ticketing.quote(session, occurrence_id=occurrence_id, ticket_type_id=body.ticket_type_id, code=body.code)
    if q.error:
        raise HTTPException(status_code=409 if q.error == "sold_out" else 422, detail=translate(f"tix.quote.{q.error}", lang))
    return {"list_price_paise": q.list_price_paise, "discount_paise": q.discount_paise, "amount_paise": q.amount_paise}


# --- organizer side -------------------------------------------------------------------------------------------------


@router.get("/ticket-admin")
async def ticket_admin(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Organizer view: ticket types with sales and check-ins, discount codes with use, and the contact settings. Counts only."""
    await _require_organizer(session, occurrence_id, member, lang)
    contact = await activity.get_contact(session, occurrence_id=occurrence_id, member_id=member.member_id)
    return {
        "types": await ticketing.sales_by_type(session, occurrence_id=occurrence_id, actor=member.member_id),
        "codes": await ticketing.discount_codes(session, occurrence_id=occurrence_id, actor=member.member_id),
        "contact": {
            "phone": contact["phone"] if contact else None,
            "email": contact["email"] if contact else None,
            "visibility": contact["visibility"] if contact else "confirmed",
            "offer_counsel": await activity.offers_counsel(session, occurrence_id),
        },
    }


@router.post("/ticket-types", status_code=201)
async def add_ticket_type(occurrence_id: UUID, body: TicketTypeBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await ticketing.save_ticket_type(
            session, occurrence_id=occurrence_id, actor=member.member_id, type_id=None, name=body.name, price_paise=body.price_paise, quota=body.quota, active=True
        )
    except ticketing.OrganizerWriteRefused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.patch("/ticket-types/{type_id}")
async def edit_ticket_type(occurrence_id: UUID, type_id: UUID, body: TicketTypeBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await ticketing.save_ticket_type(
            session, occurrence_id=occurrence_id, actor=member.member_id, type_id=type_id, name=body.name, price_paise=body.price_paise, quota=body.quota, active=body.active
        )
    except ticketing.OrganizerWriteRefused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.delete("/ticket-types/{type_id}")
async def remove_ticket_type(occurrence_id: UUID, type_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Removes a type nobody booked; a type with bookings is switched off instead (no new sales, every ticket keeps its record)."""
    try:
        await ticketing.remove_ticket_type(session, occurrence_id=occurrence_id, actor=member.member_id, type_id=type_id)
    except ticketing.OrganizerWriteRefused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.post("/discount-codes", status_code=201)
async def add_discount_code(occurrence_id: UUID, body: DiscountCodeBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    if not _CODE.match(body.code) or body.kind not in ("percent", "fixed"):
        raise HTTPException(status_code=422, detail=translate("tix.err.invalid", lang))
    if (body.kind == "percent" and not 1 <= body.value <= 90) or (body.kind == "fixed" and not 100 <= body.value <= 10_000_000):
        raise HTTPException(status_code=422, detail=translate("tix.err.invalid", lang))
    try:
        await ticketing.save_discount_code(
            session, occurrence_id=occurrence_id, actor=member.member_id, code=body.code, kind=body.kind, value=body.value, max_uses=body.max_uses, expires_at=body.expires_at
        )
    except ticketing.OrganizerWriteRefused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.patch("/discount-codes/{code_id}")
async def toggle_discount_code(occurrence_id: UUID, code_id: UUID, body: DiscountActiveBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await ticketing.set_discount_active(session, occurrence_id=occurrence_id, actor=member.member_id, code_id=code_id, active=body.active)
    except ticketing.OrganizerWriteRefused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.put("/contact")
async def put_contact(occurrence_id: UUID, body: ContactBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await activity.set_contact(
            session,
            occurrence_id=occurrence_id,
            actor_member_id=member.member_id,
            phone=body.phone,
            email=body.email,
            visibility=body.visibility,
            offer_counsel=body.offer_counsel,
        )
    except activity.OccurrenceNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    except activity.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return {"ok": True}


@router.post("/checkin/ticket")
async def checkin_ticket(occurrence_id: UUID, body: CheckinTicketBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """The organizer scans (or types) an attendee's ticket code. Only a paid ticket for THIS event checks someone in, once."""
    await _require_organizer(session, occurrence_id, member, lang)
    found = await ticketing.ticket_for_checkin(session, occurrence_id=occurrence_id, actor=member.member_id, code=_normalise_code(body.code))
    if found.result == "not_allowed":
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang))
    if found.result == "not_found" or found.member_id is None:
        raise HTTPException(status_code=404, detail=translate("tix.scan.notFound", lang))
    if found.result == "not_valid":
        raise HTTPException(status_code=409, detail=translate("tix.scan.notValid", lang))
    name = (await identity.display_names_for([found.member_id]))[found.member_id].display_name
    if found.participation_status in ("checked_in", "attended"):
        return {"result": "already", "name": name, "type_name": found.type_name}
    try:
        await activity.mark_attendance(session, occurrence_id=occurrence_id, actor_member_id=member.member_id, member_id=found.member_id, outcome="checked_in")
    except activity.OccurrenceNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("tix.scan.notFound", lang)) from exc
    return {"result": "checked_in", "name": name, "type_name": found.type_name}
