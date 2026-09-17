"""People discovery endpoints — FR042, FR043, FR044, FR045."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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


class FollowRequest(BaseModel):
    follow: bool = True


@router.post("/{member_id}/follow")
async def follow_host(member_id: UUID, body: FollowRequest, session: DbSession, member: CurrentMember) -> dict:
    """[FR122] Follow a host's calendar (private — the host is not told)."""
    from app.components.activity import interface as activity

    following = await activity.follow_host(session, member_id=member.member_id, host_member_id=member_id, follow=body.follow)
    return {"following": following}


class FreeNowRequest(BaseModel):
    minutes: int = 120  # [FR119] 15 minutes to 4 hours; nothing longer is "right now"
    locality: str | None = None
    note: str | None = None


@router.get("/free-now")
async def free_now(session: DbSession, member: CurrentMember) -> dict:
    """[FR119] Who in my circles is free at the moment, and am I?"""
    return {
        "mine": await connect.my_free_now(session, member_id=member.member_id),
        "people": await connect.free_now_nearby(session, viewer_member_id=member.member_id),
    }


@router.post("/free-now")
async def set_free_now(body: FreeNowRequest, session: DbSession, member: CurrentMember) -> dict:
    return await connect.set_free_now(session, member_id=member.member_id, minutes=body.minutes, locality=body.locality, note=body.note)


@router.delete("/free-now", status_code=204)
async def clear_free_now(session: DbSession, member: CurrentMember) -> None:
    await connect.clear_free_now(session, member_id=member.member_id)


class MeetAgainRequest(BaseModel):
    occurrence_id: UUID
    member_id: UUID
    pick: bool


@router.get("/meet-again/{occurrence_id}")
async def meet_again_candidates(occurrence_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR106] People who were there, for someone who was there; `picked` is only the viewer's own private choice."""
    return await connect.meet_again_candidates(session, occurrence_id=occurrence_id, viewer_member_id=member.member_id)


@router.post("/meet-again")
async def meet_again(body: MeetAgainRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR106] Pick or un-pick. `mutual` is true only when both picked each other — a one-sided pick is never revealed."""
    try:
        mutual = await connect.pick_meet_again(
            session, occurrence_id=body.occurrence_id, chooser_member_id=member.member_id, chosen_member_id=body.member_id, pick=body.pick
        )
    except connect.NotThere as exc:
        raise HTTPException(status_code=404, detail=translate("meet.notThere", lang)) from exc
    return {"picked": body.pick, "mutual": mutual}


@router.get("/connections")
async def connections(session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR106] "You'd both meet again" — mutual picks only, visible to the two people."""
    return await connect.connections(session, viewer_member_id=member.member_id)


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
