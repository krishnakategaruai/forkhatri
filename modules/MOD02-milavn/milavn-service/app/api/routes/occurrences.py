"""Occurrence endpoints — FR010-FR019, FR056-FR059, FR063, FR064.

Thin HTTP layer over `components/activity/interface.py` and Discovery's card
builder. Every client-queueable mutation here honours `Idempotency-Key`
(TR-CROSSCUT-01) and the shared rate limiter (TR-CROSSCUT-02).
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, CurrentMember, DbSession, IdempotencyKeyHeader, Locale
from app.api.schemas import CardOut
from app.components.activity import interface as activity
from app.components.authorization import interface as authz
from app.components.conversation import interface as conversation
from app.components.discovery import interface as discovery
from app.components.identity_bridge import interface as identity
from app.components.ticketing import interface as ticketing
from app.components.trust import interface as trust
from app.config import icebreakers
from app.i18n import translate
from app.idempotency import idempotent
from app.rate_limiting import RateLimitScope, enforce

router = APIRouter(prefix="/occurrences", tags=["occurrences"])

SAFETY_GUIDELINES = [
    "Tell someone where you're going and when you expect to be back.",
    "Meet at the stated public place first; the organizer's identity is visible to you as an RSVP'd participant.",
    "Carry water, basic first aid, and a charged phone.",
    "If anything feels off, leave — and report it from the activity page.",
]


class CreateOccurrenceRequest(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    intent_category: str
    time_start: datetime
    time_end: datetime | None = None
    locality_city: str
    locality_zone: str | None = None
    locality_locality: str | None = None
    description: str | None = None
    capacity: int | None = None
    visibility_scope: str = "public"
    circle_id: UUID | None = None
    organization_scope_id: UUID | None = None
    high_risk: bool = False
    recurrence_rule: dict | None = None
    cover_image_media_id: UUID | None = None
    price_paise: int | None = None  # [FR102] None = free
    refund_cutoff_hours: int = 24
    audience_tags: list[str] = Field(default_factory=list)  # [FR110] family_friendly | elder_friendly | beginner_friendly
    food_tags: list[str] = Field(default_factory=list)  # [FR110] veg | jain_options | non_veg | alcohol_free
    max_guests_per_member: int = 0  # [FR114] how many people each person may bring (free activities only)


class UpdateOccurrenceRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    intent_category: str | None = None
    time_start: datetime | None = None
    time_end: datetime | None = None
    locality_city: str | None = None
    locality_zone: str | None = None
    locality_locality: str | None = None
    capacity: int | None = None
    high_risk: bool | None = None
    visibility_scope: str | None = None
    circle_id: UUID | None = None
    cover_image_media_id: UUID | None = None
    price_paise: int | None = None
    refund_cutoff_hours: int | None = None
    audience_tags: list[str] | None = None
    food_tags: list[str] | None = None
    max_guests_per_member: int | None = None


class ParticipationRequest(BaseModel):
    status: str  # interested | going | cancelled
    guests: int | None = None  # [FR114] how many people they are bringing


class PlanRequest(BaseModel):
    travel: str | None = None  # walk | two_wheeler | car | cab_auto | metro_bus
    company: str | None = None  # alone | friend | family


class RegularRequest(BaseModel):
    keep: bool


class AnnouncementRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class MemberRefRequest(BaseModel):
    member_id: UUID


class AttendanceRequest(BaseModel):
    member_id: UUID
    outcome: str  # checked_in | attended | no_show


class CheckinRequest(BaseModel):
    token: str


class CancelRequest(BaseModel):
    reason: str | None = None


def _404(lang: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translate("occurrence.notFound", lang))


async def _card(session, occ, member) -> CardOut:  # noqa: ANN001
    v = await discovery.viewer_profile(session, member.member_id)
    cards = await discovery.build_cards(session, [occ], v, rank=v is not None)
    if not cards:
        cards = await discovery.build_cards(session, [occ], v, rank=False)
    return CardOut.from_card(cards[0])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_occurrence(
    body: CreateOccurrenceRequest,
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
    settings: AppSettings,
    idem: IdempotencyKeyHeader,
) -> JSONResponse:
    """[FR010/FR011/FR013/FR014] Minimal creation (what/when/where/how-many); shareable link immediately."""
    await enforce(
        session,
        scope=RateLimitScope.OCCURRENCE_CREATE,
        subject=str(member.member_id),
        limit_max=settings.rate_limit_create_max,
        window_seconds=settings.rate_limit_create_window_seconds,
    )
    async with idempotent(
        session, actor_member_id=member.member_id, idempotency_key=idem, endpoint="POST /occurrences", request_payload=body.model_dump(mode="json")
    ) as outcome:
        if not outcome.replayed:
            try:
                occ = await activity.create(
                    session,
                    creator_member_id=member.member_id,
                    creator_identity_level=member.identity_level,
                    title=body.title,
                    intent_category=body.intent_category,
                    time_start=body.time_start,
                    time_end=body.time_end,
                    locality_city=body.locality_city,
                    locality_zone=body.locality_zone,
                    locality_locality=body.locality_locality,
                    description=body.description,
                    capacity=body.capacity,
                    visibility_scope=body.visibility_scope,
                    circle_id=body.circle_id,
                    organization_scope_id=body.organization_scope_id,
                    high_risk=body.high_risk,
                    cover_image_media_id=body.cover_image_media_id,
                    recurrence_rule=body.recurrence_rule,
                    price_paise=body.price_paise,
                    refund_cutoff_hours=body.refund_cutoff_hours,
                    audience_tags=body.audience_tags,
                    food_tags=body.food_tags,
                    max_guests_per_member=body.max_guests_per_member,
                )
            except activity.InvalidInput as exc:
                raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
            card = await _card(session, occ, member)
            outcome.set_result(201, {**card.model_dump(mode="json"), "share_url": f"/a/{occ.canonical_url_slug}"})
    return JSONResponse(outcome.response, status_code=outcome.status_code)


@router.post("/{occurrence_id}/series", status_code=status.HTTP_201_CREATED)
async def add_series_occurrence(
    occurrence_id: UUID,
    body: CreateOccurrenceRequest,
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
) -> dict:
    """[FR011] Add another dated occurrence under an existing recurring Activity."""
    try:
        parent = await activity.get(session, occurrence_id=occurrence_id)
        await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=member.member_id)
    except (activity.OccurrenceNotFound, authz.NotFound) as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    if parent.activity_id is None:
        raise HTTPException(status_code=409, detail="not a recurring activity")
    occ = await activity.create(
        session,
        creator_member_id=member.member_id,
        creator_identity_level=member.identity_level,
        title=body.title or parent.title,
        intent_category=body.intent_category or parent.intent_category,
        time_start=body.time_start,
        time_end=body.time_end,
        locality_city=body.locality_city or parent.locality_city,
        locality_zone=body.locality_zone or parent.locality_zone,
        locality_locality=body.locality_locality or parent.locality_locality,
        description=body.description or parent.description,
        capacity=body.capacity if body.capacity is not None else parent.capacity,
        visibility_scope=body.visibility_scope or parent.visibility_scope,
        circle_id=body.circle_id or parent.circle_id,
        high_risk=body.high_risk or parent.high_risk,
        activity_id=parent.activity_id,
        price_paise=body.price_paise if body.price_paise is not None else parent.price_paise,
        refund_cutoff_hours=body.refund_cutoff_hours if "refund_cutoff_hours" in body.model_fields_set else parent.refund_cutoff_hours,
    )
    return (await _card(session, occ, member)).model_dump(mode="json")


@router.get("/mine")
async def my_occurrences(session: DbSession, member: CurrentMember) -> dict:
    """[FR026 input, FR013] What I'm going to and what I host."""
    mine = await activity.my_participations(session, member_id=member.member_id)
    v = await discovery.viewer_profile(session, member.member_id)
    going: list[CardOut] = []
    for occ_id, st in mine.items():
        if st in ("cancelled", "no_show"):
            continue
        try:
            occ = await activity.get(session, occurrence_id=occ_id)
        except activity.OccurrenceNotFound:
            continue
        cards = await discovery.build_cards(session, [occ], v, rank=False)
        if cards:
            going.append(CardOut.from_card(cards[0]))
    hosted_occs = await activity.list_visible(session, city=None, start=None, end=None, creator_member_id=member.member_id, include_cancelled=True)
    hosted = [CardOut.from_card(c) for c in await discovery.build_cards(session, hosted_occs, v, rank=False)]
    going.sort(key=lambda c: c.time_start)
    hosted.sort(key=lambda c: c.time_start)
    return {"participating": [c.model_dump(mode="json") for c in going], "hosting": [c.model_dump(mode="json") for c in hosted]}


@router.get("/by-slug/{slug}")
async def get_by_slug(slug: str, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Authenticated detail by canonical slug (circle-scoped items have no public page, FR050)."""
    try:
        occ = await activity.get_by_slug(session, slug=slug)
    except activity.OccurrenceNotFound as exc:
        raise _404(lang) from exc
    return await get_occurrence(occ.id, session, member, lang)


@router.get("/{occurrence_id}")
async def get_occurrence(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR006 + FR063/FR064] Detail: card + description + organizer identity for RSVP'd + safety block."""
    try:
        occ = await activity.get(session, occurrence_id=occurrence_id)
    except activity.OccurrenceNotFound as exc:
        raise _404(lang) from exc
    card = await _card(session, occ, member)
    role = await authz.occurrence_role(session, occurrence_id=occurrence_id, member_id=member.member_id)
    is_organizer = role in (authz.OccurrenceRole.ORGANIZER, authz.OccurrenceRole.CO_ORGANIZER)
    host_ident = (await identity.display_names_for([occ.creator_member_id]))[occ.creator_member_id]
    org_trust = await trust.trust_for(session, subject_type="organizer", subject_id=occ.creator_member_id)
    org_labels = trust.label_text(await trust.reputation_labels(session, member_id=occ.creator_member_id))
    cos = await activity.co_organizers(session, occurrence_id=occurrence_id) if is_organizer else []
    co_names = await identity.display_names_for(cos)
    series = None
    if occ.activity_id:
        series = await activity.series_summary(session, activity_id=occ.activity_id)
        upcoming = await activity.upcoming_in_series(session, activity_id=occ.activity_id, exclude=occ.id)
        series["upcoming_list"] = [{"id": str(u.id), "slug": u.canonical_url_slug, "time_start": u.time_start.isoformat()} for u in upcoming]
        series["recurrence_rule"] = occ.recurrence_rule
        # [FR112] The member's own recent attendance and whether their spot is kept each time.
        series["regular"] = await activity.is_regular(session, member_id=member.member_id, activity_id=occ.activity_id)
        attended, total = await activity.recent_attendance(session, member_id=member.member_id, activity_id=occ.activity_id)
        series["my_recent"] = {"attended": attended, "total": total}
    # [FR063] identity/location/capacity visible to RSVP'd participants (and organizers).
    rsvpd = role != authz.OccurrenceRole.VIEWER
    plan = await activity.my_plan(session, occurrence_id=occurrence_id, member_id=member.member_id)
    now = datetime.now(UTC)
    # [FR103] Ask "still coming?" in place during the last 28 hours, until answered.
    still_coming_due = bool(plan and plan.confirmed_at is None and card.viewer_status == "going" and now < occ.time_start <= now + timedelta(hours=28))
    return {
        **card.model_dump(mode="json"),
        "description": occ.description,
        "share_url": f"/a/{occ.canonical_url_slug}",
        "viewer_role": role.value,
        "organizer": {
            "member_id": str(occ.creator_member_id),
            "display_name": host_ident.display_name,
            "avatar": host_ident.avatar,
            "trust_label": org_trust.label,
            "trust_positive": org_trust.positive,
            "reputation": org_labels,
            "identity_visible": rsvpd,
        },
        "co_organizers": [{"member_id": str(m), "display_name": co_names[m].display_name} for m in cos],
        "announcements": [
            {
                "id": str(a["id"]),
                "message": a["message"],
                "created_at": a["created_at"].isoformat(),
                "by": (await identity.display_names_for([a["organizer_member_id"]]))[a["organizer_member_id"]].display_name,
            }
            for a in await activity.list_announcements(session, occurrence_id=occurrence_id)
        ],
        "safety_guidelines": SAFETY_GUIDELINES if occ.high_risk else [],
        "circle_peers": await conversation.circle_peers(session, occurrence_id=occurrence_id, viewer_member_id=member.member_id),
        "thread_access": await conversation.can_view_thread(session, occurrence_id=occurrence_id, member_id=member.member_id),
        "was_there": await conversation.was_there(session, occurrence_id=occurrence_id, member_id=member.member_id),
        "series": series,
        "cancelled_at": occ.cancelled_at.isoformat() if occ.cancelled_at else None,
        "time_zone": "Asia/Kolkata",
        "refund_cutoff_hours": occ.refund_cutoff_hours,
        "my_plan": {"travel": plan.travel, "company": plan.company, "confirmed_at": plan.confirmed_at.isoformat() if plan.confirmed_at else None} if plan else None,
        "still_coming_due": still_coming_due,
        # [FR114] What the host allows, what this member is bringing, and how many guests in total.
        "max_guests_per_member": occ.max_guests_per_member,
        "my_guests": await activity.my_guest_count(session, occurrence_id=occurrence_id, member_id=member.member_id),
        "guest_total": await activity.guest_total(session, occurrence_id),
        # [FR108] Someone going to their first activity gets a "what to expect" card (never shown to the host).
        "first_time": bool(plan and not is_organizer and await activity.is_first_timer(session, member_id=member.member_id, before=occ.time_start)),
        # [FR107] Whether this attendee has already thanked the host.
        "thanked": await trust.has_thanked(session, occurrence_id=occurrence_id, member_id=member.member_id),
    }


@router.patch("/{occurrence_id}")
async def update_occurrence(occurrence_id: UUID, body: UpdateOccurrenceRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR012] Edit; material time/place changes notify participants (FR017).
    [FR102] Price and refund window lock once anyone is paying or has paid, so nobody's terms change under them."""
    changes = body.model_dump(exclude_unset=True)
    if "price_paise" in changes or "refund_cutoff_hours" in changes:
        try:
            current = await activity.get(session, occurrence_id=occurrence_id)
        except activity.OccurrenceNotFound as exc:
            raise _404(lang) from exc
        changed = ("price_paise" in changes and changes["price_paise"] != current.price_paise) or (
            changes.get("refund_cutoff_hours") is not None and changes["refund_cutoff_hours"] != current.refund_cutoff_hours
        )
        if changed and await ticketing.open_ticket_count(session, occurrence_id) > 0:
            raise HTTPException(status_code=409, detail=translate("payments.priceLocked", lang))
    try:
        occ, material = await activity.update(session, occurrence_id=occurrence_id, actor_member_id=member.member_id, changes=changes)
    except activity.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    except (activity.OccurrenceNotFound, authz.NotFound) as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    except activity.OccurrenceCancelled as exc:
        raise HTTPException(status_code=409, detail=translate("occurrence.cancelled", lang)) from exc
    return {**(await _card(session, occ, member)).model_dump(mode="json"), "material_change": material}


@router.post("/{occurrence_id}/cancel")
async def cancel_occurrence(occurrence_id: UUID, body: CancelRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR012/FR017] Cancel; every participant gets an Important-class notice."""
    try:
        occ = await activity.cancel(session, occurrence_id=occurrence_id, actor_member_id=member.member_id, reason=body.reason)
    except (activity.OccurrenceNotFound, authz.NotFound) as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    return (await _card(session, occ, member)).model_dump(mode="json")


@router.post("/{occurrence_id}/participation")
async def set_participation(
    occurrence_id: UUID,
    body: ParticipationRequest,
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
    settings: AppSettings,
    idem: IdempotencyKeyHeader,
) -> JSONResponse:
    """[FR015/FR016/FR058] One-tap Interested/Going; capacity-aware waitlist; idempotent."""
    await enforce(
        session,
        scope=RateLimitScope.PARTICIPATION_TOGGLE,
        subject=str(member.member_id),
        limit_max=settings.rate_limit_participation_max,
        window_seconds=settings.rate_limit_participation_window_seconds,
    )
    async with idempotent(
        session, actor_member_id=member.member_id, idempotency_key=idem, endpoint=f"POST /occurrences/{occurrence_id}/participation", request_payload=body.model_dump()
    ) as outcome:
        if not outcome.replayed:
            # [FR102] A paid spot is given back through /ticket/withdraw, where the refund rule applies.
            if body.status in ("cancelled", "interested") and await ticketing.has_paid_spot(session, occurrence_id=occurrence_id, member_id=member.member_id):
                raise HTTPException(status_code=409, detail=translate("payments.useWithdraw", lang))
            try:
                res = await activity.set_participation(session, occurrence_id=occurrence_id, member_id=member.member_id, desired=body.status, guests=body.guests)
            except activity.PaymentRequired as exc:
                raise HTTPException(status_code=409, detail=translate("payments.required", lang)) from exc
            except activity.NoRoomForGuests as exc:
                raise HTTPException(status_code=409, detail=translate("guest.noRoom", lang)) from exc
            except activity.OccurrenceEnded as exc:
                raise HTTPException(status_code=409, detail=translate("occurrence.ended", lang)) from exc
            except activity.AlreadyAttended as exc:
                raise HTTPException(status_code=409, detail=translate("occurrence.alreadyAttended", lang)) from exc
            except activity.OccurrenceNotFound as exc:
                raise _404(lang) from exc
            except activity.OccurrenceCancelled as exc:
                raise HTTPException(status_code=409, detail=translate("occurrence.cancelled", lang)) from exc
            except activity.InvalidInput as exc:
                raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
            outcome.set_result(
                200,
                {
                    "status": res.status,
                    "waitlist_position": res.waitlist_position,
                    "going_count": res.going_count,
                    "guests": res.guests,
                    "spots_left": res.spots_left,
                    "message": translate("occurrence.full", lang) if res.status == "waitlisted" else None,
                },
            )
    return JSONResponse(outcome.response, status_code=outcome.status_code)


@router.get("/{occurrence_id}/conversation-cards")
async def conversation_cards(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR118] A few prompts for the people who are actually there, from about an hour before it
    starts until it ends. Not shown to someone who is only looking at the page."""
    try:
        occ = await activity.get(session, occurrence_id=occurrence_id)
    except activity.OccurrenceNotFound as exc:
        raise _404(lang) from exc
    status_now = await activity.viewer_status(session, occurrence_id, member.member_id)
    is_organizer = occ.creator_member_id == member.member_id
    if not is_organizer and status_now not in ("going", "checked_in", "attended"):
        return {"cards": [], "active": False}
    now = datetime.now(UTC)
    ends = occ.time_end or (occ.time_start + timedelta(hours=3))
    active = occ.time_start - timedelta(hours=1) <= now <= ends
    return {"cards": icebreakers.cards_for(intent_category=occ.intent_category, seed=str(occ.id)), "active": active}


@router.post("/{occurrence_id}/regular")
async def keep_my_spot(occurrence_id: UUID, body: RegularRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR112] "Keep a spot for me each time" for a free series — opt in or out; nothing happens without this tap."""
    try:
        occ = await activity.get(session, occurrence_id=occurrence_id)
    except activity.OccurrenceNotFound as exc:
        raise _404(lang) from exc
    if occ.activity_id is None:
        raise HTTPException(status_code=409, detail=translate("regular.notSeries", lang))
    if body.keep and occ.price_paise is not None:
        raise HTTPException(status_code=409, detail=translate("regular.paid", lang))
    if body.keep and occ.creator_member_id == member.member_id:
        raise HTTPException(status_code=409, detail=translate("regular.notSeries", lang))
    # A spot is kept only for someone who has actually come before, so newcomers are never crowded out by strangers' holds.
    if body.keep and (await activity.recent_attendance(session, member_id=member.member_id, activity_id=occ.activity_id))[0] < 1:
        raise HTTPException(status_code=409, detail=translate("regular.notYet", lang))
    kept = await activity.set_regular(session, member_id=member.member_id, activity_id=occ.activity_id, keep=body.keep)
    return {"regular": body.keep, "kept": kept}


@router.put("/{occurrence_id}/plan")
async def set_attendance_plan(occurrence_id: UUID, body: PlanRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR105] How I'm getting there and who with — one tap, optional, repeated back in the reminder before it starts."""
    try:
        plan = await activity.set_plan(session, occurrence_id=occurrence_id, member_id=member.member_id, travel=body.travel, company=body.company)
    except activity.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    except activity.NotParticipating as exc:
        raise HTTPException(status_code=409, detail=translate("plan.notGoing", lang)) from exc
    return {"travel": plan.travel, "company": plan.company, "confirmed_at": plan.confirmed_at.isoformat() if plan.confirmed_at else None}


@router.post("/{occurrence_id}/confirm")
async def confirm_still_coming(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR103] "Still coming" — the kind counterpart to freeing a spot."""
    try:
        at = await activity.confirm_attendance(session, occurrence_id=occurrence_id, member_id=member.member_id)
    except activity.NotParticipating as exc:
        raise HTTPException(status_code=409, detail=translate("plan.notGoing", lang)) from exc
    return {"confirmed_at": at.isoformat()}


@router.get("/{occurrence_id}/attendees")
async def attendees(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> list[dict]:
    """[FR056] Organizer/co-organizer only."""
    try:
        rows = await activity.attendees(session, occurrence_id=occurrence_id, actor_member_id=member.member_id)
    except authz.NotFound as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    names = await identity.display_names_for([a.member_id for a in rows])
    return [
        {
            "member_id": str(a.member_id),
            "display_name": names[a.member_id].display_name,
            "avatar": names[a.member_id].avatar,
            "status": a.status,
            "waitlist_position": a.waitlist_position,
            "checked_in_at": a.checked_in_at.isoformat() if a.checked_in_at else None,
            "company": a.company,
            "first_time": a.first_time,
            "guests": a.guests,
        }
        for a in rows
    ]


@router.get("/{occurrence_id}/after")
async def after_the_activity(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR107] Host only: how many came, first-timers, "would come again", and the thank-you notes sent to them."""
    try:
        await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=member.member_id)
    except authz.NotFound as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    notes = await trust.thanks_received(session, occurrence_id=occurrence_id)
    names = await identity.display_names_for([m for m, _ in notes])
    return {
        **(await activity.after_summary(session, occurrence_id=occurrence_id)),
        "thanks": [{"from": names[m].display_name, "message": msg} for m, msg in notes],
    }


@router.post("/{occurrence_id}/announcements", status_code=201)
async def announce(occurrence_id: UUID, body: AnnouncementRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR057] Organizer update reaches every current participant."""
    try:
        update_id = await activity.announce(session, occurrence_id=occurrence_id, actor_member_id=member.member_id, message=body.message)
    except authz.NotFound as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    except activity.DuplicateAnnouncement as exc:
        raise HTTPException(status_code=409, detail=translate("occurrence.duplicateAnnouncement", lang)) from exc
    return {"id": str(update_id)}


@router.post("/{occurrence_id}/co-organizers", status_code=201)
async def grant_co_organizer(occurrence_id: UUID, body: MemberRefRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR059] Delegate; revocable."""
    try:
        await activity.grant_co_organizer(session, occurrence_id=occurrence_id, actor_member_id=member.member_id, member_id=body.member_id)
    except authz.NotFound as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    return {"ok": True}


@router.delete("/{occurrence_id}/co-organizers/{member_id}")
async def revoke_co_organizer(occurrence_id: UUID, member_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await activity.revoke_co_organizer(session, occurrence_id=occurrence_id, actor_member_id=member.member_id, member_id=member_id)
    except authz.NotFound as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    return {"ok": True}


@router.post("/{occurrence_id}/attendance")
async def mark_attendance(occurrence_id: UUID, body: AttendanceRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR018 manual check-in / FR019 no-show] Organizer marks; never an automated penalty."""
    try:
        outcome = await activity.mark_attendance(session, occurrence_id=occurrence_id, actor_member_id=member.member_id, member_id=body.member_id, outcome=body.outcome)
    except (authz.NotFound, activity.OccurrenceNotFound) as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    except activity.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return {"status": outcome}


@router.post("/{occurrence_id}/complete")
async def complete(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await activity.complete(session, occurrence_id=occurrence_id, actor_member_id=member.member_id)
    except authz.NotFound as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    return {"ok": True}


@router.post("/{occurrence_id}/checkin/token")
async def checkin_token(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale, settings: AppSettings) -> dict:
    """[FR018] Organizer issues a short-lived QR token (optional, scale-gated).

    The QR encodes a plain URL to the activity page with `?checkin=<token>`, so
    a participant scans it with the phone camera — no in-app scanner needed —
    and the page redeems the token (UX08's "unceremonious" check-in)."""
    try:
        token, expires = await activity.issue_checkin_token(session, occurrence_id=occurrence_id, actor_member_id=member.member_id)
        occ = await activity.get(session, occurrence_id=occurrence_id)
    except (authz.NotFound, activity.OccurrenceNotFound) as exc:
        raise _404(lang) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    return {"token": token, "expires_at": expires.isoformat(), "qr_payload": f"{settings.web_base_url}/a/{occ.canonical_url_slug}?checkin={token}"}


@router.post("/{occurrence_id}/checkin")
async def checkin(occurrence_id: UUID, body: CheckinRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        st = await activity.redeem_checkin_token(session, occurrence_id=occurrence_id, member_id=member.member_id, token=body.token)
    except activity.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    except activity.OccurrenceNotFound as exc:
        raise _404(lang) from exc
    return {"status": st}


@router.post("/cover", status_code=201)
async def upload_cover(settings: AppSettings, member: CurrentMember, photo: UploadFile = File(...)) -> dict:  # noqa: B008
    """[FR013] Optional cover image (local-disk stand-in for Object Storage); never blocks creation."""
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(photo.content_type or "")
    if ext is None:
        raise HTTPException(status_code=422, detail="unsupported image type")
    media_id = uuid4()
    root: Path = settings.media_root / "covers"
    root.mkdir(parents=True, exist_ok=True)
    with (root / f"{media_id}.jpg").open("wb") as fh:
        shutil.copyfileobj(photo.file, fh)
    return {"media_id": str(media_id), "url": f"/media/covers/{media_id}.jpg"}
