"""Wedding arrangements endpoints (migration 062), all `?for_candidate=` scoped:

- `GET  /wedding/stages?ids=`             — the stage of each accepted match
- `POST /wedding/{connection_id}/stage`    — either family moves the stage
- `GET  /wedding/{connection_id}/places`   — partners and real places for one
                                             category, near one centre

Thin HTTP layer over `components/wedding/interface.py`.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.wedding import interface as wedding
from app.components.wedding.catalogue import CATEGORIES, STAGE_CATEGORIES, STAGES

router = APIRouter(prefix="/wedding", tags=["wedding"])


async def _context(session: DbSession, account_id: UUID, for_candidate: UUID | None) -> UUID:
    try:
        return await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc


async def _match(session: DbSession, connection_id: UUID, ctx: UUID) -> wedding.Match:
    try:
        return await wedding.get_match(session, connection_id=connection_id, account_id=ctx)
    except wedding.NotYourMatch as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


class StageResponse(BaseModel):
    connection_id: str
    stage: str
    categories: list[str]
    updated_by_me: bool
    updated_at: str | None


def _stage_response(connection_id: UUID, s: dict, account_id: UUID) -> StageResponse:
    return StageResponse(
        connection_id=str(connection_id),
        stage=s["stage"],
        categories=list(STAGE_CATEGORIES[s["stage"]]),
        updated_by_me=s["updated_by_account_id"] == account_id,
        updated_at=s["updated_at"].isoformat() if s["updated_at"] else None,
    )


@router.get("/stages", response_model=list[StageResponse])
async def list_stages(
    session: DbSession,
    account_id: AuthenticatedAccount,
    ids: Annotated[list[UUID] | None, Query()] = None,
    for_candidate: UUID | None = None,
) -> list[StageResponse]:
    ctx = await _context(session, account_id, for_candidate)
    mine = []
    for cid in (ids or [])[:50]:
        try:
            await wedding.get_match(session, connection_id=cid, account_id=ctx)
            mine.append(cid)
        except wedding.NotYourMatch:
            continue
    stages = await wedding.stages_for(session, connection_ids=mine)
    return [_stage_response(cid, stages[cid], account_id) for cid in mine]


class StageUpdate(BaseModel):
    stage: str


@router.post("/{connection_id}/stage", response_model=StageResponse)
async def update_stage(
    connection_id: UUID,
    body: StageUpdate,
    session: DbSession,
    account_id: AuthenticatedAccount,
    for_candidate: UUID | None = None,
) -> StageResponse:
    if body.stage not in STAGES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    ctx = await _context(session, account_id, for_candidate)
    match = await _match(session, connection_id, ctx)
    # Recorded as the person who tapped it — a parent, or the candidate.
    await wedding.set_stage(session, match=match, stage=body.stage, by_account_id=account_id)
    return _stage_response(
        connection_id, await wedding.stage_of(session, connection_id=connection_id), account_id
    )


@router.get("/{connection_id}/places")
async def places(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    category: str,
    near: str | None = None,
    for_candidate: UUID | None = None,
) -> dict:
    if category not in CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    ctx = await _context(session, account_id, for_candidate)
    match = await _match(session, connection_id, ctx)
    return await wedding.suggestions(session, match=match, category=category, near=near, lang=lang)
