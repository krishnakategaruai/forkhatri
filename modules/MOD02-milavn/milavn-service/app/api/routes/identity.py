"""Identity endpoints — dev stand-in for the platform's Identity & Trust Service.

# [FR076-FR080, FR088, TR46, TR47] Sign-up/login/OTP/reset live in the parent
# ForKhatri platform, not here. This router only (a) reports who the current
# request is acting as and (b) in development lists the stub identities the
# web client can switch between. Nothing here stores or verifies credentials.
# Traces to: TR46, TR47, ADR-004.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AppSettings, CurrentMember
from app.components.identity_bridge import interface as identity

router = APIRouter(prefix="/identity", tags=["identity"])


class IdentityResponse(BaseModel):
    member_id: str
    display_name: str
    handle: str
    avatar: str | None
    scopes: list[str]


@router.get("/me", response_model=IdentityResponse)
async def me(member: CurrentMember) -> IdentityResponse:
    return IdentityResponse(
        member_id=str(member.member_id),
        display_name=member.display_name,
        handle=member.handle,
        avatar=member.avatar,
        scopes=list(member.scopes),
    )


@router.get("/dev/members", response_model=list[IdentityResponse])
async def dev_members(settings: AppSettings) -> list[IdentityResponse]:
    if not settings.dev_identity_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return [
        IdentityResponse(
            member_id=str(m.member_id),
            display_name=m.display_name,
            handle=m.handle,
            avatar=m.avatar,
            scopes=list(m.scopes),
        )
        for m in identity.list_dev_members()
    ]
