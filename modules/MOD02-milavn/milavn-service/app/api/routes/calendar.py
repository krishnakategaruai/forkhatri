"""Calendar endpoints — FR026 (personal), FR027 (circle), FR028 (organization/community), FR029 (public)."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.api.deps import CurrentMember, DbSession, Locale, OptionalMember
from app.api.schemas import CardOut
from app.components.activity import interface as activity
from app.components.discovery import interface as discovery
from app.i18n import translate

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _window(start: datetime | None, days: int) -> tuple[datetime, datetime]:
    s = start or datetime.now(discovery.IST).replace(hour=0, minute=0, second=0, microsecond=0)
    return s, s + timedelta(days=days)


@router.get("/personal", response_model=list[CardOut])
async def personal(session: DbSession, member: CurrentMember, start: datetime | None = None, days: int = Query(default=30, le=90)) -> list[CardOut]:
    """[FR026] Only what I've RSVP'd to (or host), in one place."""
    s, e = _window(start, days)
    mine = await activity.my_participations(session, member_id=member.member_id)
    v = await discovery.viewer_profile(session, member.member_id)
    occs = []
    for occ_id, st in mine.items():
        if st in ("cancelled", "no_show"):
            continue
        try:
            o = await activity.get(session, occurrence_id=occ_id)
        except activity.OccurrenceNotFound:
            continue
        if s <= o.time_start < e:
            occs.append(o)
    hosted = await activity.list_visible(session, city=None, start=s, end=e, creator_member_id=member.member_id)
    seen = {o.id for o in occs}
    occs.extend(o for o in hosted if o.id not in seen)
    occs.sort(key=lambda o: o.time_start)
    return [CardOut.from_card(c) for c in await discovery.build_cards(session, occs, v, rank=False)]


@router.get("/circle/{circle_id}", response_model=list[CardOut])
async def circle_calendar(
    circle_id: UUID, session: DbSession, member: CurrentMember, start: datetime | None = None, days: int = Query(default=30, le=90)
) -> list[CardOut]:
    """[FR027] Circle-scoped; RLS hides a circle's private occurrences from non-members."""
    s, e = _window(start, days)
    v = await discovery.viewer_profile(session, member.member_id)
    occs = await activity.list_visible(session, city=None, start=s, end=e, circle_id=circle_id)
    return [CardOut.from_card(c) for c in await discovery.build_cards(session, occs, v, rank=False)]


@router.get("/organization/{organization_scope_id}", response_model=list[CardOut])
async def organization_calendar(
    organization_scope_id: UUID, session: DbSession, member: CurrentMember, start: datetime | None = None, days: int = Query(default=60, le=120)
) -> list[CardOut]:
    """[FR028] Organization scope (minimal tag, TR23)."""
    s, e = _window(start, days)
    v = await discovery.viewer_profile(session, member.member_id)
    occs = await activity.list_visible(session, city=None, start=s, end=e, organization_scope_id=organization_scope_id)
    return [CardOut.from_card(c) for c in await discovery.build_cards(session, occs, v, rank=False)]


@router.get("/community", response_model=list[CardOut])
async def community_calendar(
    session: DbSession, member: CurrentMember, lang: Locale, start: datetime | None = None, days: int = Query(default=30, le=90)
) -> list[CardOut]:
    """[FR028] Community scope = the viewer's city, community/public-visible."""
    s, e = _window(start, days)
    v = await discovery.viewer_profile(session, member.member_id)
    if v is None:
        raise HTTPException(status_code=409, detail=translate("profile.notFound", lang))
    occs = [o for o in await activity.list_visible(session, city=v.city, start=s, end=e) if o.visibility_scope in ("community", "public")]
    return [CardOut.from_card(c) for c in await discovery.build_cards(session, occs, v, rank=False)]


@router.get("/public", response_model=list[CardOut])
async def public_calendar(
    session: DbSession, member: OptionalMember, city: str = Query(...), start: datetime | None = None, days: int = Query(default=30, le=90)
) -> JSONResponse:
    """[FR029] Public-marked items only — works without login."""
    s, e = _window(start, days)
    occs = await activity.list_visible(session, city=city, start=s, end=e, scope="public")
    v = await discovery.viewer_profile(session, member.member_id) if member else None
    cards = await discovery.build_cards(session, occs, v, rank=False)
    return JSONResponse([CardOut.from_card(c).model_dump(mode="json") for c in cards])
