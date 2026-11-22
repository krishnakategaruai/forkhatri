"""Account deletion endpoints (docs/ParentApp/ACCOUNT-DELETION.md, kind A).

    GET  /v1/account/delete/preview       what the member is about to delete, and any blocker
    POST /v1/account/delete/code          send a one-time code to the member's own phone/email (re-authentication)
    POST /v1/account/delete               {confirm: "DELETE", password | challenge_id + code}: close, erase, finish
    GET  /v1/account/deletion/{job_id}    progress and, when finished, the receipt (the job id is the capability:
                                          the member is already signed out by then)
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app import rate_limiting
from app.api.deps import AppSettings, DbSession, RequiredSession, SessionFactory, client_ip
from app.api.routes.auth import CodeResponse, _clear_session_cookie
from app.components.deletion import interface as deletion
from app.components.identity import interface as identity

router = APIRouter(prefix="/v1/account", tags=["account"])


class DeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: Literal["DELETE"]
    password: str | None = Field(default=None, max_length=256)
    challenge_id: UUID | None = None
    code: str | None = Field(default=None, pattern=r"^\d{6}$")


@router.get("/delete/preview")
async def preview(session: RequiredSession, db: DbSession, settings: AppSettings) -> dict[str, Any]:
    out = await deletion.preview(db, settings, session.member.member_id)
    out.update(await identity.reauth_options(db, session.member.member_id))
    return out


@router.post("/delete/code", response_model=CodeResponse, response_model_exclude_none=True, status_code=202)
async def send_code(
    request: Request, session: RequiredSession, db: DbSession, factory: SessionFactory, settings: AppSettings
) -> CodeResponse:
    challenge = await identity.start_reauth_code(db, factory, settings, session.member, client_ip(request))
    return CodeResponse(
        challenge_id=challenge.challenge_id,
        channel=challenge.channel,
        destination_hint=challenge.destination_hint,
        expires_in=challenge.expires_in,
        resend_in=challenge.resend_in,
        dev_code=challenge.dev_code,
    )


@router.post("/delete", status_code=202)
async def delete_account(
    body: DeleteRequest,
    response: Response,
    session: RequiredSession,
    db: DbSession,
    factory: SessionFactory,
    settings: AppSettings,
) -> dict[str, Any]:
    member = session.member
    # Every attempt counts, successful or not: 3 per hour per member.
    await rate_limiting.hit(
        factory, f"account_delete:{member.member_id}", limit=settings.deletion_rate_limit_per_hour, window_seconds=3600
    )
    await identity.check_reauth(
        db, factory, settings, member, password=body.password, challenge_id=body.challenge_id, code=body.code
    )
    job_id = await deletion.start(db, settings, member.member_id)
    await db.commit()
    deletion.launch(factory, settings, job_id)
    _clear_session_cookie(response, settings)
    return {"job_id": str(job_id), "status": "closing"}


@router.get("/deletion/{job_id}")
async def deletion_status(job_id: UUID, factory: SessionFactory) -> dict[str, Any]:
    return await deletion.status_of(factory, job_id)
