"""Discovery endpoints — FR004, FR005, FR006, FR007, FR008, FR009, FR033."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import CurrentMember, DbSession, Locale
from app.api.schemas import CardOut
from app.components.circle import interface as circle
from app.components.discovery import interface as discovery
from app.i18n import translate

router = APIRouter(prefix="/discovery", tags=["discovery"])


class AroundYouResponse(BaseModel):
    today: list[CardOut]
    tomorrow: list[CardOut]
    weekend: list[CardOut]
    later: list[CardOut]
    circles: list[dict]
    viewer_locality: str


async def _viewer(session, member, lang, lat: float | None = None, lng: float | None = None):  # noqa: ANN001
    v = await discovery.viewer_profile(session, member.member_id)
    if v is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "profile_required", "message": translate("profile.notFound", lang)})
    if lat is not None and lng is not None:
        # "Here, right now": a one-shot device position snapped to the nearest approximate locality (FR038).
        # It changes what this request shows; the stored profile locality is untouched, nothing is persisted.
        from dataclasses import replace

        from app.config import localities

        near = localities.nearest(lat, lng)
        v = replace(v, city=near.city, zone=near.zone, locality=near.locality)
    return v


@router.get("/around-you", response_model=AroundYouResponse)
async def around_you(session: DbSession, member: CurrentMember, lang: Locale, lat: float | None = None, lng: float | None = None) -> AroundYouResponse:
    """[FR004] Today / Tomorrow / This Weekend, ranked (FR007) with a real reason (FR008). `lat`/`lng` = "use where I am" for this request only."""
    v = await _viewer(session, member, lang, lat, lng)
    groups = await discovery.around_you(session, v)
    mine = await circle.mine(session, member_id=member.member_id)
    return AroundYouResponse(
        today=[CardOut.from_card(c) for c in groups["today"]],
        tomorrow=[CardOut.from_card(c) for c in groups["tomorrow"]],
        weekend=[CardOut.from_card(c) for c in groups["weekend"]],
        later=[CardOut.from_card(c) for c in groups["later"]],
        circles=[{"id": str(c.id), "name": c.name, "circle_type": c.circle_type, "member_count": c.member_count} for c in mine],
        viewer_locality=v.locality or v.zone or v.city,
    )


@router.get("/calendar", response_model=list[CardOut])
async def calendar(session: DbSession, member: CurrentMember, lang: Locale, date: datetime = Query(...)) -> list[CardOut]:  # noqa: B008
    """[FR005] Calendar mode keeps the locality/interest context."""
    v = await _viewer(session, member, lang)
    return [CardOut.from_card(c) for c in await discovery.calendar_day(session, v, date)]


@router.get("/search", response_model=list[CardOut])
async def search(
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
    q: str | None = None,
    category: str | None = None,
    scope: str | None = None,
    when: str | None = Query(default=None, pattern="^(today|tomorrow|weekend|week)$"),
    distance: str | None = Query(default=None, pattern="^(locality|zone|city)$"),
    safe_only: bool | None = None,
) -> list[CardOut]:
    """[FR005/FR009] Search mode with common filters by default; advanced filters on request."""
    v = await _viewer(session, member, lang)
    cards = await discovery.search(
        session,
        v,
        query=q,
        category=category,
        scope=scope,
        when=when,
        distance=distance,
        high_risk=(False if safe_only else None),
    )
    return [CardOut.from_card(c) for c in cards]


@router.get("/understand")
async def understand(q: str, member: CurrentMember) -> dict:
    """Natural-language search: echo what was understood as filters + chips (deterministic, see discovery/nl.py)."""
    from app.components.discovery import nl

    u = nl.understand(q)
    return {"category": u.category, "when": u.when, "distance": u.distance, "q": u.query, "chips": u.chips}


@router.get("/smart-fill")
async def smart_fill(text: str, session: DbSession, member: CurrentMember) -> dict:
    """One sentence -> a draft activity (category, title, when, where, how many). Never creates anything."""
    from app.components.discovery import nl

    v = await discovery.viewer_profile(session, member.member_id)
    d = nl.smart_fill(text, default_city=v.city if v else None)
    return {
        "category": d.category,
        "title": d.title,
        "time_start": d.time_start,
        "locality_city": d.locality_city,
        "locality_locality": d.locality_locality,
        "capacity": d.capacity,
        "matched": d.matched,
    }


@router.get("/digest")
async def digest(session: DbSession, member: CurrentMember, lang: Locale, lat: float | None = None, lng: float | None = None) -> dict:
    """[thesis §67 'immediately understand'] A short personal read of the week, composed from real counts: what is near,
    how many circle-mates are going, what the person has already said yes to. Sentences, not a feed."""
    v = await _viewer(session, member, lang, lat, lng)
    groups = await discovery.around_you(session, v)
    cards = [c for k in ("today", "tomorrow", "weekend", "later") for c in groups[k]]
    going = [c for c in cards if c.viewer_status in ("going", "checked_in")]
    with_peers = [c for c in cards if c.why_factor == "social"]
    lines: list[str] = []
    if going:
        nxt = min(going, key=lambda c: c.time_start)
        lines.append(translate("digest.going", lang, n=len(going), title=nxt.title))
    if groups["today"]:
        lines.append(translate("digest.today", lang, n=len(groups["today"])))
    elif groups["tomorrow"]:
        lines.append(translate("digest.tomorrow", lang, n=len(groups["tomorrow"])))
    if with_peers:
        lines.append(translate("digest.peers", lang, n=len(with_peers)))
    if not lines:
        lines.append(translate("digest.quiet", lang, locality=v.locality or v.zone or v.city))
    return {"lines": lines[:3], "locality": v.locality or v.zone or v.city}


@router.get("/map", response_model=list[CardOut])
async def map_mode(session: DbSession, member: CurrentMember, lang: Locale) -> list[CardOut]:
    """[FR005] Map mode — pins at approximate locality centroids only (FR038)."""
    v = await _viewer(session, member, lang)
    return [CardOut.from_card(c) for c in await discovery.map_pins(session, v)]
