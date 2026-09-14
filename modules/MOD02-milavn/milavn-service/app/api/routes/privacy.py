"""Location & privacy endpoints — FR039, FR041."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentMember, DbSession
from app.components.locationprivacy import interface as locpriv

router = APIRouter(prefix="/privacy", tags=["privacy"])


class PrecisionRequest(BaseModel):
    precision_level: str  # city | zone | locality


@router.get("/location")
async def get_location_privacy(session: DbSession, member: CurrentMember) -> dict:
    return {"precision_level": await locpriv.precision_for(session, member_id=member.member_id), "precise_consent": False}


@router.put("/location")
async def set_location_privacy(body: PrecisionRequest, session: DbSession, member: CurrentMember) -> dict:
    """[FR041] Never more precise than the member chooses; 'precise' needs a consent grant (FR039) no feature asks for yet."""
    try:
        level = await locpriv.set_precision(session, member_id=member.member_id, level=body.precision_level)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="precise location requires explicit consent for a specific feature") from exc
    return {"precision_level": level, "precise_consent": False}
