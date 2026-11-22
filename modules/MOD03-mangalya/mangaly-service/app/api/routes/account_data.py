"""Account deletion endpoints for Mangalya (contract: docs/ParentApp/ACCOUNT-DELETION.md).

    POST /privacy/delete-account-data              the member, from /me (kind B)
    POST /internal/v1/members/{member_id}/erase    the platform, server to server (kind A)

Both are immediate, idempotent and transactional (migration 067). The member
version needs the typed word DELETE and is limited to 3 tries an hour; the
internal one is authenticated with the shared service key and answered as if it
did not exist when it arrives through the public edge.
"""

from __future__ import annotations

import hmac
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.api.deps import AppSettings, AuthenticatedAccount, DbSession
from app.components.lifecycle import erasure
from app.rate_limiting import limiter

router = APIRouter(tags=["account-deletion"])


class DeleteBody(BaseModel):
    confirm: Literal["DELETE"]


@router.post("/privacy/delete-account-data")
async def delete_my_data(
    body: DeleteBody,
    response: Response,
    background: BackgroundTasks,
    session: DbSession,
    account_id: AuthenticatedAccount,
) -> dict[str, Any]:
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.DELETE_ACCOUNT_DATA,
            subject=str(account_id),
            limit_max=3,
            window_seconds=3600,
        )
    except limiter.RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "rate_limited", "message": "Too many attempts. Try again later."},
            headers={"Retry-After": str(exc.result.retry_after_seconds)},
        ) from exc
    try:
        result = await erasure.erase_me(session)
    except erasure.ErasureRefused:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "role_must_be_removed_first",
                    "message": "This account holds a moderator role. Ask an owner to remove it first."},
        ) from None
    # Files go after the database change has committed (a background task runs
    # once the request transaction is closed).
    background.add_task(erasure.remove_files, result)
    response.delete_cookie("mangaly_session", path="/")
    n_files = len(result.get("file_refs") or [])
    return erasure.to_contract(result, n_files)


def platform_caller(
    request: Request,
    settings: AppSettings,
    x_forkhatri_service_key: Annotated[str | None, Header()] = None,
) -> None:
    if request.headers.get("x-forwarded-for") is not None:
        raise HTTPException(status_code=404)
    presented = (x_forkhatri_service_key or "").encode("utf-8")
    if not hmac.compare_digest(settings.platform_service_key.encode("utf-8"), presented):
        raise HTTPException(status_code=401, detail="Unknown service credentials.")


@router.post(
    "/internal/v1/members/{member_id}/erase",
    dependencies=[Depends(platform_caller)],
    include_in_schema=False,
)
async def erase_member(member_id: UUID, request: Request) -> dict[str, Any]:
    # Own transaction so the commit is explicit and files are removed only after it.
    factory = request.app.state.session_factory
    async with factory() as session:
        async with session.begin():
            try:
                result = await erasure.erase_member(session, member_id)
            except erasure.ErasureRefused:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "role_must_be_removed_first"},
                ) from None
    return erasure.to_contract(result, erasure.remove_files(result))
