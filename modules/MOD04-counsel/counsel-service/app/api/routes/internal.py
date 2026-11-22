"""Service-to-service endpoints called by the ForKhatri platform with Counsel's
service key (the same key Counsel uses to call the platform). Used when a member
deletes their whole ForKhatri account: the platform asks each module to export
or erase that member's data."""

from __future__ import annotations

import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, Header

from app import db
from app.components import privacy
from app.errors import DomainError
from app.settings import get_settings

router = APIRouter(prefix="/internal/v1", tags=["internal"], include_in_schema=False)


def platform_only(x_forkhatri_service: str | None = Header(default=None), x_forkhatri_service_key: str | None = Header(default=None)) -> None:
    s = get_settings()
    if x_forkhatri_service != "identity" or not hmac.compare_digest((x_forkhatri_service_key or "").encode(), s.platform_service_key.encode()):
        raise DomainError("service_unauthorized", "Unknown service credentials.", 401)


@router.get("/members/{member_id}/deletion-check", dependencies=[Depends(platform_only)])
async def check(member_id: UUID):
    async with db.pool().acquire() as conn:
        return {"blockers": await privacy.blockers(conn, member_id)}


@router.post("/members/{member_id}/erase", dependencies=[Depends(platform_only)])
async def erase(member_id: UUID):
    return await privacy.erase_member(member_id, "forkhatri_account_deleted")


@router.get("/members/{member_id}/export", dependencies=[Depends(platform_only)])
async def export(member_id: UUID):
    async with db.tx() as conn:
        return await privacy.export(conn, member_id)
