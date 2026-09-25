"""Safety endpoints (rework contract §3): block / unblock / report.

Thin HTTP layer over `components/safety/interface.py`. Blocking is personal
to the caller's own account (never context-scoped): it is the person who
does not want contact, whichever candidate they act for.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.authorization import interface as authz
from app.components.authorization.context import Action
from app.components.profile import interface as profile
from app.components.safety import interface as safety
from app.i18n import translate

router = APIRouter(prefix="/safety", tags=["safety"])


class BlockResponse(BaseModel):
    blocked_account_id: str
    created_at: str


@router.get("/blocks", response_model=list[BlockResponse])
async def list_blocks(session: DbSession, account_id: AuthenticatedAccount) -> list[BlockResponse]:
    await authz.resolve_self(session, account_id=account_id, action=Action.READ)
    rows = await safety.list_blocks(session, blocker_account_id=account_id)
    return [
        BlockResponse(blocked_account_id=str(r.blocked_account_id), created_at=r.created_at.isoformat())
        for r in rows
    ]


@router.post("/block/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def block(
    profile_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[Contract §3] Block a person: they vanish from both sides' Discover,
    lists and request sending; any pending request between the two ends."""
    await authz.resolve_self(session, account_id=account_id, action=Action.WRITE)
    blocked = await profile.resolve_account_id(session, profile_id)
    try:
        await safety.block(session, blocker_account_id=account_id, blocked_account_id=blocked)
    except safety.CannotBlockSelf as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("safety.error.cannotBlockSelf", lang),
        ) from exc


@router.delete("/block/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock(profile_id: UUID, session: DbSession, account_id: AuthenticatedAccount) -> None:
    await authz.resolve_self(session, account_id=account_id, action=Action.WRITE)
    blocked = await profile.resolve_account_id(session, profile_id)
    await safety.unblock(session, blocker_account_id=account_id, blocked_account_id=blocked)


class ReportRequest(BaseModel):
    profile_id: str
    reason: str = Field(min_length=1, max_length=64)
    details: str | None = Field(default=None, max_length=2000)


class ReportResponse(BaseModel):
    report_id: str
    message: str


@router.post("/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def report(
    body: ReportRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> ReportResponse:
    """[TR063] Report a person. Reasons: `harassment | fake_profile |
    inappropriate_content | scam_or_money | already_married | underage | other`."""
    await authz.resolve_self(session, account_id=account_id, action=Action.WRITE)
    reported = await profile.resolve_account_id(session, UUID(body.profile_id))
    try:
        report_id = await safety.report(
            session,
            reporter_account_id=account_id,
            reported_account_id=reported,
            reason=body.reason,
            details=body.details,
        )
    except safety.InvalidReason as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("safety.error.invalidReason", lang),
        ) from exc
    return ReportResponse(report_id=str(report_id), message=translate("safety.report.received", lang))
