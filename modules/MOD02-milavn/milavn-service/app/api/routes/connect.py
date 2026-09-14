"""People discovery endpoints — FR042, FR043, FR044, FR045."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentMember, DbSession, Locale
from app.api.schemas import CardOut
from app.components.connect import interface as connect
from app.components.discovery import interface as discovery
from app.components.trust import interface as trust
from app.i18n import translate

router = APIRouter(prefix="/people", tags=["people"])


@router.get("/reputation/{member_id}")
async def reputation(member_id: UUID, session: DbSession, member: CurrentMember) -> list[str]:
    """[FR037] Qualitative labels only — the raw score is unreachable from any request."""
    return trust.label_text(await trust.reputation_labels(session, member_id=member_id))


@router.get("/suggestions")
async def suggestions(session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR042/FR043] Reason-bearing suggestions only; blocked pairs excluded; no match/like model exists."""
    return [
        {
            "member_id": str(s.member_id),
            "display_name": s.display_name,
            "avatar": s.avatar,
            "reason": s.reason,
            "reason_kind": s.reason_kind,
            "location_label": s.location_label,
            "reputation": s.reputation,
        }
        for s in await connect.suggestions(session, viewer_member_id=member.member_id)
    ]


@router.get("/{member_id}")
async def public_profile(member_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Beyond-MVP person page: identity, bio, interests, reputation labels, locality at THEIR precision,
    circles you share, and the public activities they host. Blocked pairs get a 404, not a hint."""
    page = await connect.public_profile(session, viewer_member_id=member.member_id, member_id=member_id)
    if page is None:
        raise HTTPException(status_code=404, detail=translate("common.notFound", lang))
    v = await discovery.viewer_profile(session, member.member_id)
    from app.components.activity import interface as activity

    occs = []
    for oid in page.pop("hosted_ids", []):
        try:
            occs.append(await activity.get(session, occurrence_id=oid))
        except activity.OccurrenceNotFound:
            continue
    cards = await discovery.build_cards(session, occs, v, rank=False) if occs else []
    page["hosting"] = [CardOut.from_card(c).model_dump(mode="json") for c in cards]
    return page
