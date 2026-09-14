"""Safety endpoints — FR061 (report), FR062 (block), FR087 (contact support reuses report)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import AppSettings, CurrentMember, DbSession, IdempotencyKeyHeader, Locale
from app.components.identity_bridge import interface as identity
from app.components.safety import interface as safety
from app.i18n import translate
from app.idempotency import idempotent
from app.rate_limiting import RateLimitScope, enforce

router = APIRouter(prefix="/safety", tags=["safety"])


class ReportRequest(BaseModel):
    subject_type: str
    subject_id: UUID
    reason_category: str
    description: str | None = None


class BlockRequest(BaseModel):
    member_id: UUID


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def submit_report(body: ReportRequest, session: DbSession, member: CurrentMember, lang: Locale, settings: AppSettings, idem: IdempotencyKeyHeader) -> JSONResponse:
    """[FR061] Report; rate-limited and idempotent; audited in the same transaction."""
    await enforce(
        session,
        scope=RateLimitScope.REPORT_SUBMIT,
        subject=str(member.member_id),
        limit_max=settings.rate_limit_report_max,
        window_seconds=settings.rate_limit_report_window_seconds,
    )
    async with idempotent(
        session, actor_member_id=member.member_id, idempotency_key=idem, endpoint="POST /safety/reports", request_payload=body.model_dump(mode="json")
    ) as outcome:
        if not outcome.replayed:
            try:
                r = await safety.submit_report(
                    session,
                    reporter_member_id=member.member_id,
                    subject_type=body.subject_type,
                    subject_id=body.subject_id,
                    reason=body.reason_category,
                    description=body.description,
                )
            except safety.InvalidReport as exc:
                raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
            outcome.set_result(201, {"id": str(r.id), "status": r.status})
    return JSONResponse(outcome.response, status_code=outcome.status_code)


@router.get("/reports/mine")
async def my_reports(session: DbSession, member: CurrentMember) -> list[dict]:
    return [
        {
            "id": str(r.id),
            "subject_type": r.subject_type,
            "subject_id": str(r.subject_id),
            "reason": r.reason_category,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in await safety.my_reports(session, member_id=member.member_id)
    ]


@router.post("/blocks", status_code=201)
async def block(body: BlockRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR062] Block; enforced at every contact/appearance surface via the shared helper."""
    try:
        await safety.block(session, blocking_member_id=member.member_id, blocked_member_id=body.member_id)
    except safety.InvalidReport as exc:
        raise HTTPException(status_code=422, detail=translate("block.self", lang)) from exc
    return {"ok": True}


@router.delete("/blocks/{member_id}")
async def unblock(member_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    await safety.unblock(session, blocking_member_id=member.member_id, blocked_member_id=member_id)
    return {"ok": True}


@router.get("/blocks")
async def my_blocks(session: DbSession, member: CurrentMember) -> list[dict]:
    ids = await safety.my_blocks(session, member_id=member.member_id)
    names = identity.display_names_for(ids)
    return [{"member_id": str(m), "display_name": names[m].display_name, "avatar": names[m].avatar} for m in ids]
