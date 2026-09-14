"""Notification endpoints — FR051-FR055, FR086."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentMember, DbSession
from app.components.notification import interface as notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PreferenceRequest(BaseModel):
    notification_class: str
    muted: bool
    frequency: str | None = None


@router.get("")
async def inbox(session: DbSession, member: CurrentMember) -> dict:
    entries = await notification.inbox(session, member_id=member.member_id)
    return {
        "unread": sum(1 for e in entries if e.read_at is None),
        "entries": [
            {
                "id": str(e.id),
                "class": e.notification_class,
                "title": e.title,
                "body": e.body,
                "deep_link": e.deep_link,
                "occurrence_id": str(e.source_occurrence_id) if e.source_occurrence_id else None,
                "read_at": e.read_at.isoformat() if e.read_at else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ],
    }


@router.get("/unread-count")
async def unread(session: DbSession, member: CurrentMember) -> dict:
    return {"unread": await notification.unread_count(session, member_id=member.member_id)}


@router.post("/read")
async def mark_all_read(session: DbSession, member: CurrentMember) -> dict:
    await notification.mark_read(session, member_id=member.member_id, entry_id=None)
    return {"ok": True}


@router.post("/{entry_id}/read")
async def mark_read(entry_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    await notification.mark_read(session, member_id=member.member_id, entry_id=entry_id)
    return {"ok": True}


@router.delete("/{entry_id}")
async def dismiss(entry_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    await notification.dismiss(session, member_id=member.member_id, entry_id=entry_id)
    return {"ok": True}


@router.get("/preferences")
async def get_preferences(session: DbSession, member: CurrentMember) -> dict:
    return await notification.preferences(session, member_id=member.member_id)


@router.put("/preferences")
async def set_preference(body: PreferenceRequest, session: DbSession, member: CurrentMember) -> dict:
    """[FR051/FR054] Important can never be muted; other classes are user-controlled."""
    try:
        await notification.set_preference(session, member_id=member.member_id, notification_class=body.notification_class, muted=body.muted, frequency=body.frequency)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="this class cannot be changed") from exc
    return await notification.preferences(session, member_id=member.member_id)
