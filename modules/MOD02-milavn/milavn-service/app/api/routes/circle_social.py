"""Circle social endpoints (Phase 2, Step 6; migration 053): photo albums, the per-circle
notification setting, and circles co-hosting an event. Thin layer: rules live in the definer
functions and RLS of 053; this file maps outcomes to honest statuses and translated messages."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, CurrentMember, DbSession, Locale
from app.components.activity import cohost
from app.components.circle import interface as circle
from app.components.circle import social
from app.i18n import translate
from app.media_files import TooLarge
from app.rate_limiting import RateLimitScope, enforce

router = APIRouter(tags=["circle-social"])


# --- Notification setting -------------------------------------------------------------------------


class NotifyLevelRequest(BaseModel):
    level: str  # 'all' | 'highlights' | 'off'


@router.get("/circles/{circle_id}/notify")
async def get_notify(circle_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    return {"level": await social.notify_level(session, circle_id=circle_id, member_id=member.member_id), "levels": list(social.NOTIFY_LEVELS)}


@router.put("/circles/{circle_id}/notify")
async def put_notify(circle_id: UUID, body: NotifyLevelRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        return {"level": await social.set_notify_level(session, circle_id=circle_id, member_id=member.member_id, level=body.level)}
    except social.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["level"]}) from exc
    except social.NotMember as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notMember", lang)) from exc


# --- Albums ------------------------------------------------------------------------------------------


class AlbumRequest(BaseModel):
    name: str = Field(min_length=1, max_length=social.MAX_ALBUM_NAME)


def _album_error(exc: Exception, lang: str) -> HTTPException:
    if isinstance(exc, social.NotMember):
        return HTTPException(status_code=403, detail=translate("circle.notMember", lang))
    if isinstance(exc, social.NotAllowed):
        return HTTPException(status_code=403, detail=translate("album.notAllowed", lang))
    if isinstance(exc, social.DuplicateAlbum):
        return HTTPException(status_code=409, detail=translate("album.duplicate", lang))
    if isinstance(exc, social.InvalidInput):
        return HTTPException(status_code=422, detail={"fields": [exc.field]})
    if isinstance(exc, social.UnsupportedPhoto):
        return HTTPException(status_code=415, detail=translate("moments.unsupported", lang))
    if isinstance(exc, social.TooManyPhotos):
        return HTTPException(status_code=422, detail=translate("media.tooManyPhotos", lang, n=exc.limit))
    if isinstance(exc, TooLarge):
        return HTTPException(status_code=413, detail=translate("media.tooLarge", lang, mb=exc.limit_mb))
    return HTTPException(status_code=404, detail=translate("album.notFound", lang))


_ALBUM_ERRORS = (social.NotMember, social.NotAllowed, social.NotFound, social.DuplicateAlbum, social.InvalidInput, social.UnsupportedPhoto, social.TooManyPhotos, TooLarge)


@router.get("/circles/{circle_id}/albums")
async def list_albums(circle_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """RLS returns nothing to anyone outside the circle."""
    return await social.albums(session, circle_id=circle_id, viewer_member_id=member.member_id)


@router.post("/circles/{circle_id}/albums", status_code=status.HTTP_201_CREATED)
async def create_album(circle_id: UUID, body: AlbumRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        return await social.create_album(session, circle_id=circle_id, member_id=member.member_id, name=body.name)
    except _ALBUM_ERRORS as exc:
        raise _album_error(exc, lang) from exc


@router.get("/circles/{circle_id}/albums/{album_id}")
async def get_album(circle_id: UUID, album_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        return await social.album_photos(session, circle_id=circle_id, album_id=album_id, viewer_member_id=member.member_id)
    except _ALBUM_ERRORS as exc:
        raise _album_error(exc, lang) from exc


@router.post("/circles/{circle_id}/albums/{album_id}/photos", status_code=status.HTTP_201_CREATED)
async def add_album_photos(
    circle_id: UUID,
    album_id: UUID,
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
    settings: AppSettings,
    photos: Annotated[list[UploadFile], File()],
    caption: Annotated[str | None, Form()] = None,
) -> dict:
    await enforce(session, scope=RateLimitScope.PHOTO_UPLOAD, subject=str(member.member_id), limit_max=60, window_seconds=3600)
    try:
        n = await social.add_album_photos(
            session,
            circle_id=circle_id,
            album_id=album_id,
            member_id=member.member_id,
            photos=photos,
            caption=caption,
            max_per_upload=settings.circle_album_max_photos_per_upload,
            max_mb=settings.circle_photo_max_mb,
        )
    except _ALBUM_ERRORS as exc:
        raise _album_error(exc, lang) from exc
    return {"added": n}


@router.delete("/circles/{circle_id}/albums/{album_id}", status_code=204)
async def delete_album(circle_id: UUID, album_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> None:
    """Organizers and assistants only; the album's photos go with it."""
    try:
        await social.remove_album(session, circle_id=circle_id, album_id=album_id, member_id=member.member_id)
    except _ALBUM_ERRORS as exc:
        raise _album_error(exc, lang) from exc


@router.delete("/circles/{circle_id}/albums/{album_id}/photos/{photo_id}", status_code=204)
async def delete_album_photo(circle_id: UUID, album_id: UUID, photo_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> None:
    """The person who added it, or an organizer / assistant."""
    try:
        await social.remove_album_photo(session, circle_id=circle_id, photo_id=photo_id, member_id=member.member_id)
    except _ALBUM_ERRORS as exc:
        raise _album_error(exc, lang) from exc


# --- Co-hosting ---------------------------------------------------------------------------------------


class CohostInviteRequest(BaseModel):
    circle_id: UUID


class CohostResponse(BaseModel):
    accept: bool


def _cohost_error(exc: Exception, lang: str) -> HTTPException:
    if isinstance(exc, cohost.Refused):
        return HTTPException(status_code=409, detail=translate(f"cohost.{exc.reason}", lang))
    if isinstance(exc, cohost.NotAllowed):
        return HTTPException(status_code=403, detail=translate("cohost.notAllowed", lang))
    return HTTPException(status_code=404, detail=translate("cohost.notFound", lang))


@router.get("/occurrences/{occurrence_id}/cohosts")
async def list_cohosts(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """The circles hosting this event together; pending invitations only for the event's hosts."""
    try:
        rows = await cohost.cohosts(session, occurrence_id=occurrence_id, viewer_member_id=member.member_id)
    except cohost.NotFound as exc:
        raise _cohost_error(exc, lang) from exc
    return {"cohosts": rows, "can_invite": await cohost.is_manager(session, occurrence_id=occurrence_id, member_id=member.member_id)}


@router.get("/occurrences/{occurrence_id}/cohost-candidates")
async def cohost_candidates(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale, q: str | None = None) -> list[dict]:
    """Circles the host could invite: their own circles first, then open circles matching `q`."""
    if not await cohost.is_manager(session, occurrence_id=occurrence_id, member_id=member.member_id):
        raise HTTPException(status_code=403, detail=translate("cohost.notAllowed", lang))
    from app.components.activity import interface as activity

    try:
        occ = await activity.get(session, occurrence_id=occurrence_id)
    except activity.OccurrenceNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("cohost.notFound", lang)) from exc
    taken = {r["circle_id"] for r in await cohost.cohosts(session, occurrence_id=occurrence_id, viewer_member_id=member.member_id)}
    if occ.circle_id:
        taken.add(str(occ.circle_id))
    needle = (q or "").strip().lower()
    out: list[dict] = []
    seen: set[str] = set()
    pools = [await circle.mine(session, member_id=member.member_id)]
    if needle:
        pools.append(await circle.discover(session, viewer_member_id=member.member_id, query=needle))
    for pool in pools:
        for c in pool:
            cid = str(c.id)
            if cid in taken or cid in seen or (needle and needle not in c.name.lower()):
                continue
            seen.add(cid)
            out.append(
                {
                    "id": cid,
                    "name": c.name,
                    "member_count": c.member_count,
                    "viewer_role": c.viewer_role,
                    "locality_label": c.locality_locality or c.locality_city,
                    "cover_url": f"/media/{c.cover_ref}" if c.cover_ref else None,
                }
            )
    return out[:20]


@router.post("/occurrences/{occurrence_id}/cohosts", status_code=status.HTTP_201_CREATED)
async def invite_cohost(occurrence_id: UUID, body: CohostInviteRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """status 'invited' (that circle's organizer decides) or 'accepted' (you organize that circle)."""
    await enforce(session, scope=RateLimitScope.MESSAGE_POST, subject=str(member.member_id), limit_max=60, window_seconds=600)
    try:
        outcome = await cohost.invite(session, occurrence_id=occurrence_id, circle_id=body.circle_id, actor_member_id=member.member_id)
    except (cohost.NotFound, cohost.NotAllowed, cohost.Refused) as exc:
        raise _cohost_error(exc, lang) from exc
    return {"status": outcome}


@router.delete("/occurrences/{occurrence_id}/cohosts/{circle_id}", status_code=204)
async def remove_cohost(occurrence_id: UUID, circle_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> None:
    """The event's host withdraws the invitation (or ends the co-hosting); the circle's organizer steps out."""
    try:
        await cohost.remove(session, occurrence_id=occurrence_id, circle_id=circle_id, actor_member_id=member.member_id)
    except (cohost.NotFound, cohost.NotAllowed) as exc:
        raise _cohost_error(exc, lang) from exc


@router.get("/circles/{circle_id}/cohost-invites")
async def circle_cohost_invites(circle_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """Events asking this circle to co-host. Organizer only (empty for anyone else)."""
    return await cohost.invites_for_circle(session, circle_id=circle_id, viewer_member_id=member.member_id)


@router.post("/circles/{circle_id}/cohost-invites/{occurrence_id}/respond")
async def respond_cohost(circle_id: UUID, occurrence_id: UUID, body: CohostResponse, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        return {"status": await cohost.respond(session, occurrence_id=occurrence_id, circle_id=circle_id, actor_member_id=member.member_id, accept=body.accept)}
    except (cohost.NotFound, cohost.NotAllowed) as exc:
        raise _cohost_error(exc, lang) from exc
