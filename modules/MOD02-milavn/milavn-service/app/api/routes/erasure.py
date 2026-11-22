"""Account deletion endpoints (docs/ParentApp/ACCOUNT-DELETION.md).

    POST /internal/v1/members/{member_id}/erase   kind A, called by the platform with the service key.
    POST /privacy/delete-account-data             kind B, the signed-in member, body {"confirm": "DELETE"}.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentMember, DbSession
from app.api.routes.insights import platform_caller
from app.components.erasure.interface import ErasePartial, erase_member
from app.rate_limiting import RateLimitExceeded, RateLimitScope, enforce

internal_router = APIRouter(prefix="/internal/v1/members", tags=["internal"], include_in_schema=False)
router = APIRouter(prefix="/privacy", tags=["privacy"])


@internal_router.post("/{member_id}/erase", dependencies=[Depends(platform_caller)])
async def erase_for_platform(member_id: UUID) -> dict[str, Any]:
    try:
        return await erase_member(member_id)
    except ErasePartial:
        return {"module": "milavn", "status": "partial", "deleted": {}, "retained": [], "files_removed": 0}


class DeleteRequest(BaseModel):
    confirm: str


@router.post("/delete-account-data")
async def delete_my_data(body: DeleteRequest, session: DbSession, member: CurrentMember) -> dict[str, Any]:
    """Kind B: everything Milavn holds about the member. Their ForKhatri account stays; they can come back as a new member."""
    if body.confirm != "DELETE":
        raise HTTPException(status_code=422, detail="Type DELETE to confirm.")
    try:
        await enforce(session, scope=RateLimitScope.ACCOUNT_DATA_DELETE, subject=str(member.member_id), limit_max=3, window_seconds=3600)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.", headers={"Retry-After": str(exc.result.retry_after_seconds)}) from exc
    try:
        return await erase_member(member.member_id)
    except ErasePartial as exc:
        raise HTTPException(status_code=503, detail="A refund could not be requested right now. Nothing was deleted; please try again soon.") from exc
