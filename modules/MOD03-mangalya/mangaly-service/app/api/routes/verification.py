"""Verification endpoints — the live face match (DEC-V1-016, DEC-V1-025).

Thin HTTP layer over `components/trust/interface.py`. Every endpoint acts on
the signed-in person only: `/verification` is outside the `X-Mangalya-Manage`
paths (`api/deps.py`), so a parent filling in a child's profile is still
themselves here — a face check is never done on someone else's behalf.

No endpoint ever returns the distance the browser measured, or any score:
the member learns pass or fail, and when.
"""

from __future__ import annotations

from uuid import UUID

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.profile import interface as profile
from app.components.trust import interface as trust
from app.i18n import translate

router = APIRouter(prefix="/verification", tags=["verification"])


class VerificationStatusResponse(BaseModel):
    verified: bool
    verified_at: datetime | None
    expires_at: datetime | None
    consent_given: bool
    has_profile: bool
    # False when the person has no profile, so no photos of themselves to be
    # compared with; the screen then says so instead of opening the camera.
    has_photos: bool


class FaceMatchRequest(BaseModel):
    # Unbundled consent: it must be given on this request itself.
    consent: Literal[True]
    # The WORST photo's best-face Euclidean distance, as measured in the
    # browser. Never stored and never echoed back.
    distance: float = Field(..., ge=0.0, le=4.0)
    liveness_passed: bool
    photos_compared: int = Field(..., ge=0, le=20)


class FaceMatchResponse(BaseModel):
    passed: bool
    verified: bool
    verified_at: datetime | None
    expires_at: datetime | None


async def _photos_to_compare(session: DbSession, account_id: UUID) -> list[str]:
    """A candidate's own profile photos; for a parent or relative with no
    candidate profile, their member photo (migration 047)."""
    own = await profile.list_own_photos(session, account_id=account_id)
    if own is not None:
        return [p.url for p in own]
    member = await profile.get_member_profile(session, account_id=account_id)
    return [member.photo_url] if member and member.photo_url else []


async def _status(
    session: DbSession, account_id: AuthenticatedAccount
) -> VerificationStatusResponse:
    s = await trust.face_match_status(session, account_id=account_id)
    photos = await _photos_to_compare(session, account_id) if s.has_profile else None
    return VerificationStatusResponse(
        verified=s.verified,
        verified_at=s.verified_at,
        expires_at=s.expires_at,
        consent_given=s.consent_at is not None,
        has_profile=s.has_profile,
        has_photos=bool(photos),
    )


@router.get("/me", response_model=VerificationStatusResponse)
async def my_verification(
    session: DbSession, account_id: AuthenticatedAccount
) -> VerificationStatusResponse:
    """Whether the caller's photos are confirmed as them, since when, and
    whether their face-match consent is on record."""
    return await _status(session, account_id)


@router.post("/face-match", response_model=FaceMatchResponse)
async def face_match(
    body: FaceMatchRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> FaceMatchResponse:
    """Record one face-match attempt. The server applies the threshold."""
    photos = await _photos_to_compare(session, account_id)
    if not photos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "no_photos", "message": translate("verification.error.noPhotos", lang)},
        )
    try:
        passed, s = await trust.record_face_match(
            session,
            account_id=account_id,
            distance=body.distance,
            liveness_passed=body.liveness_passed,
            photos_compared=body.photos_compared,
            photos_on_profile=len(photos),
        )
    except trust.FaceMatchRateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "rate_limited",
                "message": translate("verification.error.rateLimited", lang),
            },
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except trust.NoPhotosToCompare as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "no_photos", "message": translate("verification.error.noPhotos", lang)},
        ) from exc
    return FaceMatchResponse(
        passed=passed, verified=s.verified, verified_at=s.verified_at, expires_at=s.expires_at
    )


@router.post("/withdraw", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw(session: DbSession, account_id: AuthenticatedAccount) -> None:
    """Withdraw face-match consent. The confirmation it supported is removed."""
    await trust.withdraw_face_match(session, account_id=account_id)
