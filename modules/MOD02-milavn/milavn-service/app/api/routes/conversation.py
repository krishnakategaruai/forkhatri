"""Conversation & Moments endpoints (beyond-MVP product pass).

Occurrence thread (participants + organizers), moments (photos by people who
were there), circle board (members). Thin layer over
`components/conversation/interface.py`; visibility is enforced by RLS +
definer helpers from migration 013, re-checked here only to return a clean
403 instead of an empty result.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentMember, DbSession, IdempotencyKeyHeader, Locale
from app.components.conversation import interface as conversation
from app.i18n import translate
from app.idempotency import idempotent
from app.rate_limiting import RateLimitScope, enforce

router = APIRouter(tags=["conversation"])


class MessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    announcement: bool = False  # [049] circle board: organizer / assistant only


class PinRequest(BaseModel):
    pinned: bool


class PostReactionRequest(BaseModel):
    emoji: str


class CommentRequest(BaseModel):
    body: str = Field(min_length=1, max_length=500)


def _msg(m: conversation.Message) -> dict:
    return {
        "id": str(m.id),
        "member_id": str(m.member_id),
        "display_name": m.display_name,
        "avatar": m.avatar,
        "body": m.body,
        "created_at": m.created_at.isoformat(),
        "mine": m.mine,
        "photo_url": m.photo_url,
        "doc_url": m.doc_url,
        "doc_name": m.doc_name,
        "is_announcement": m.is_announcement,
        "pinned": m.pinned,
        "reactions": m.reactions or {},
        "comments": [
            {
                "id": str(c.id),
                "member_id": str(c.member_id),
                "display_name": c.display_name,
                "avatar": c.avatar,
                "body": c.body,
                "created_at": c.created_at.isoformat(),
                "mine": c.mine,
            }
            for c in m.comments
        ],
    }


def _photo(p: conversation.Photo) -> dict:
    return {
        "id": str(p.id),
        "member_id": str(p.member_id),
        "display_name": p.display_name,
        "url": p.url,
        "caption": p.caption,
        "created_at": p.created_at.isoformat(),
        "mine": p.mine,
    }


@router.get("/occurrences/{occurrence_id}/messages")
async def list_messages(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        msgs = await conversation.list_messages(session, occurrence_id=occurrence_id, viewer_member_id=member.member_id)
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("thread.notParticipant", lang)) from exc
    return {"messages": [_msg(m) for m in msgs]}


@router.post("/occurrences/{occurrence_id}/messages", status_code=status.HTTP_201_CREATED)
async def post_message(occurrence_id: UUID, body: MessageRequest, session: DbSession, member: CurrentMember, lang: Locale, idem: IdempotencyKeyHeader) -> dict:
    await enforce(session, scope=RateLimitScope.MESSAGE_POST, subject=str(member.member_id), limit_max=60, window_seconds=600)
    try:
        async with idempotent(
            session,
            actor_member_id=member.member_id,
            idempotency_key=idem,
            endpoint="POST /occurrences/messages",
            request_payload={"o": str(occurrence_id), "b": body.body},
        ) as outcome:
            if not outcome.replayed:
                mid = await conversation.post_message(session, occurrence_id=occurrence_id, member_id=member.member_id, body=body.body)
                outcome.set_result(201, {"id": str(mid)})
        return outcome.response
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("thread.notParticipant", lang)) from exc
    except conversation.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["body"]}) from exc


@router.delete("/occurrences/{occurrence_id}/messages/{message_id}", status_code=204)
async def delete_message(occurrence_id: UUID, message_id: UUID, session: DbSession, member: CurrentMember) -> None:
    await conversation.delete_message(session, message_id=message_id, member_id=member.member_id)


@router.get("/occurrences/{occurrence_id}/photos")
async def list_photos(occurrence_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    photos = await conversation.list_photos(session, occurrence_id=occurrence_id, viewer_member_id=member.member_id)
    can_add = await conversation.was_there(session, occurrence_id=occurrence_id, member_id=member.member_id)
    # [FR113] Before sharing, people who were there see who asked not to be in photos.
    opt_outs = await conversation.photo_opt_outs(session, occurrence_id=occurrence_id, viewer_member_id=member.member_id) if can_add else []
    return {"photos": [_photo(p) for p in photos], "can_add": can_add, "opt_outs": opt_outs}


class PhotoPreference(BaseModel):
    prefer_not_pictured: bool


@router.post("/occurrences/{occurrence_id}/photos/{photo_id}/remove", status_code=204)
async def remove_photo_of_me(occurrence_id: UUID, photo_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> None:
    """[FR113] "I'm in this photo — remove it": taken down at once for everyone; the uploader is told."""
    if not await conversation.request_photo_removal(session, occurrence_id=occurrence_id, photo_id=photo_id, member_id=member.member_id):
        raise HTTPException(status_code=404, detail=translate("moments.notFound", lang))


@router.get("/moments/preference")
async def get_photo_preference(session: DbSession, member: CurrentMember) -> dict:
    return {"prefer_not_pictured": await conversation.photo_preference(session, member_id=member.member_id)}


@router.put("/moments/preference")
async def put_photo_preference(body: PhotoPreference, session: DbSession, member: CurrentMember) -> dict:
    """[FR113] "Please don't include me in photos" — shown to people sharing photos from activities you went to."""
    return {"prefer_not_pictured": await conversation.set_photo_preference(session, member_id=member.member_id, prefer_not_pictured=body.prefer_not_pictured)}


@router.post("/occurrences/{occurrence_id}/photos", status_code=status.HTTP_201_CREATED)
async def add_photo(
    occurrence_id: UUID,
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
    photo: Annotated[UploadFile, File()],
    caption: Annotated[str | None, Form()] = None,
) -> dict:
    await enforce(session, scope=RateLimitScope.PHOTO_UPLOAD, subject=str(member.member_id), limit_max=30, window_seconds=3600)
    try:
        p = await conversation.add_photo(session, occurrence_id=occurrence_id, member_id=member.member_id, photo=photo, caption=caption)
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("moments.notThere", lang)) from exc
    except conversation.UnsupportedMedia as exc:
        raise HTTPException(status_code=415, detail=translate("moments.unsupported", lang)) from exc
    except conversation.TooLarge as exc:
        raise HTTPException(status_code=413, detail=translate("media.tooLarge", lang, mb=exc.limit_mb)) from exc
    return _photo(p)


@router.delete("/occurrences/{occurrence_id}/photos/{photo_id}", status_code=204)
async def delete_photo(occurrence_id: UUID, photo_id: UUID, session: DbSession, member: CurrentMember) -> None:
    await conversation.delete_photo(session, photo_id=photo_id, member_id=member.member_id)


@router.get("/circles/{circle_id}/posts")
async def list_posts(circle_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    posts = await conversation.list_posts(session, circle_id=circle_id, viewer_member_id=member.member_id)
    return {"posts": [_msg(m) for m in posts], "reactions": list(conversation.POST_REACTIONS), "max_pins": conversation.MAX_PINS}


@router.post("/circles/{circle_id}/posts", status_code=status.HTTP_201_CREATED)
async def post_to_board(circle_id: UUID, body: MessageRequest, session: DbSession, member: CurrentMember, lang: Locale, idem: IdempotencyKeyHeader) -> dict:
    await enforce(session, scope=RateLimitScope.MESSAGE_POST, subject=str(member.member_id), limit_max=60, window_seconds=600)
    try:
        async with idempotent(
            session, actor_member_id=member.member_id, idempotency_key=idem, endpoint="POST /circles/posts", request_payload={"c": str(circle_id), "b": body.body, "a": body.announcement}
        ) as outcome:
            if not outcome.replayed:
                pid = await conversation.post_to_board(session, circle_id=circle_id, member_id=member.member_id, body=body.body, announcement=body.announcement)
                outcome.set_result(201, {"id": str(pid)})
        return outcome.response
    except conversation.OrganizersOnly as exc:
        raise HTTPException(status_code=403, detail=translate("circle.organizersPost", lang)) from exc
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notMember", lang)) from exc
    except conversation.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["body"]}) from exc


@router.post("/circles/{circle_id}/posts/media", status_code=status.HTTP_201_CREATED)
async def post_photo_to_board(
    circle_id: UUID,
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
    photo: UploadFile | None = File(default=None),
    document: UploadFile | None = File(default=None),
    body: str = Form(default=""),
    announcement: bool = Form(default=False),
) -> dict:
    """An Instagram/FB-style post with a photo and/or a document; the write-up is optional."""
    await enforce(session, scope=RateLimitScope.MESSAGE_POST, subject=str(member.member_id), limit_max=60, window_seconds=600)
    if photo is None and document is None:
        raise HTTPException(status_code=422, detail={"fields": ["photo", "document"]})
    try:
        pid = await conversation.post_to_board(session, circle_id=circle_id, member_id=member.member_id, body=body, photo=photo, document=document, announcement=announcement)
    except conversation.OrganizersOnly as exc:
        raise HTTPException(status_code=403, detail=translate("circle.organizersPost", lang)) from exc
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notMember", lang)) from exc
    except conversation.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["body"]}) from exc
    except conversation.UnsupportedMedia as exc:
        key = "media.unsupportedDocument" if exc.kind == "document" else "moments.unsupported"
        raise HTTPException(status_code=415, detail=translate(key, lang)) from exc
    except conversation.TooLarge as exc:
        raise HTTPException(status_code=413, detail=translate("media.tooLarge", lang, mb=exc.limit_mb)) from exc
    return {"id": str(pid)}


@router.delete("/circles/{circle_id}/posts/{post_id}", status_code=204)
async def delete_board_post(circle_id: UUID, post_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> None:
    """[B8] Take back your own post — or, as the circle's organizer or an assistant, take down anyone's."""
    try:
        await conversation.delete_post(session, circle_id=circle_id, post_id=post_id, member_id=member.member_id)
    except conversation.PostNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.postNotFound", lang)) from exc
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notYourPost", lang)) from exc


# --- [049] Pins, reactions, comments on circle posts ------------------------------------------


@router.post("/circles/{circle_id}/posts/{post_id}/pin")
async def pin_board_post(circle_id: UUID, post_id: UUID, body: PinRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Organizers and assistants pin (at most three) or unpin a post."""
    try:
        await conversation.pin_post(session, circle_id=circle_id, post_id=post_id, member_id=member.member_id, pinned=body.pinned)
    except conversation.PostNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.postNotFound", lang)) from exc
    except conversation.PinLimit as exc:
        raise HTTPException(status_code=409, detail=translate("circle.pinLimit", lang, n=conversation.MAX_PINS)) from exc
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("circle.organizersOnly", lang)) from exc
    return {"pinned": body.pinned}


@router.post("/circles/{circle_id}/posts/{post_id}/reactions")
async def react_to_post(circle_id: UUID, post_id: UUID, body: PostReactionRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Toggle one reaction from the fixed set (reactions, not likes)."""
    try:
        on = await conversation.toggle_post_reaction(session, circle_id=circle_id, post_id=post_id, member_id=member.member_id, emoji=body.emoji)
    except conversation.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["emoji"]}) from exc
    except conversation.PostNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.postNotFound", lang)) from exc
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notMember", lang)) from exc
    return {"reacted": on}


@router.post("/circles/{circle_id}/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
async def comment_on_post(circle_id: UUID, post_id: UUID, body: CommentRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Any member comments (the posting policy only limits new posts); announcements take no replies."""
    await enforce(session, scope=RateLimitScope.MESSAGE_POST, subject=str(member.member_id), limit_max=60, window_seconds=600)
    try:
        cid = await conversation.add_comment(session, circle_id=circle_id, post_id=post_id, member_id=member.member_id, body=body.body)
    except conversation.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["body"]}) from exc
    except conversation.PostNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.postNotFound", lang)) from exc
    except conversation.AnnouncementNoReplies as exc:
        raise HTTPException(status_code=409, detail=translate("circle.announcementNoReplies", lang)) from exc
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notMember", lang)) from exc
    return {"id": str(cid)}


@router.delete("/circles/{circle_id}/posts/{post_id}/comments/{comment_id}", status_code=204)
async def delete_post_comment(circle_id: UUID, post_id: UUID, comment_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> None:
    """The comment's author, or the circle's organizer / an assistant."""
    try:
        await conversation.delete_comment(session, circle_id=circle_id, comment_id=comment_id, member_id=member.member_id)
    except conversation.CommentNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.commentNotFound", lang)) from exc
    except conversation.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notYourComment", lang)) from exc
