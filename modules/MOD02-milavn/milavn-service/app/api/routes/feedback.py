"""Post-event feedback endpoints — FR066, FR067, FR068, FR069."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import CurrentMember, DbSession, IdempotencyKeyHeader, Locale
from app.components.activity import interface as activity
from app.components.trust import interface as trust
from app.i18n import translate
from app.idempotency import idempotent

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    occurrence_id: UUID
    rating: int | None = Field(default=None, ge=1, le=5)
    comments: str | None = None


@router.get("/prompt/{occurrence_id}")
async def prompt(occurrence_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    """[FR066] Optional prompt only after the member attended; never a precondition for anything (FR068)."""
    st = await activity.viewer_status(session, occurrence_id, member.member_id)
    done = await trust.feedback_exists(session, occurrence_id=occurrence_id, member_id=member.member_id)
    return {"eligible": st in ("attended", "checked_in"), "already_submitted": done}


@router.post("", status_code=201)
async def submit(body: FeedbackRequest, session: DbSession, member: CurrentMember, lang: Locale, idem: IdempotencyKeyHeader) -> JSONResponse:
    st = await activity.viewer_status(session, body.occurrence_id, member.member_id)
    if st not in ("attended", "checked_in"):
        raise HTTPException(status_code=409, detail=translate("feedback.notAttended", lang))
    occ = await activity.get(session, occurrence_id=body.occurrence_id)
    async with idempotent(
        session, actor_member_id=member.member_id, idempotency_key=idem, endpoint="POST /feedback", request_payload=body.model_dump(mode="json")
    ) as outcome:
        if not outcome.replayed:
            await trust.submit_feedback(
                session,
                occurrence_id=body.occurrence_id,
                member_id=member.member_id,
                organizer_member_id=occ.creator_member_id,
                rating=body.rating,
                comments=body.comments,
            )
            outcome.set_result(201, {"ok": True})
    return JSONResponse(outcome.response, status_code=outcome.status_code)
