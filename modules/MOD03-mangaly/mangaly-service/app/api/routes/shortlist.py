"""Shortlist endpoints (rework contract §3): `GET /shortlist`,
`POST/DELETE /shortlist/{profile_id}`, all `?for_candidate=` scoped.

Thin HTTP layer over `components/shortlist/interface.py`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.discovery import interface as discovery
from app.components.profile import interface as profile
from app.components.safety import interface as safety
from app.components.shortlist import interface as shortlist

router = APIRouter(prefix="/shortlist", tags=["shortlist"])


async def _context(session: DbSession, account_id: UUID, for_candidate: UUID | None) -> UUID:
    try:
        return await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc


class ShortlistEntryResponse(BaseModel):
    candidate_account_id: str
    saved_by_account_id: str
    saved_by_me: bool
    note: str | None
    created_at: str
    locality: str | None = None
    education_level: str | None = None
    profession: str | None = None
    photo_url: str | None = None
    age: int | None = None


@router.get("", response_model=list[ShortlistEntryResponse])
async def list_shortlist(
    session: DbSession, account_id: AuthenticatedAccount, for_candidate: UUID | None = None
) -> list[ShortlistEntryResponse]:
    ctx = await _context(session, account_id, for_candidate)
    hidden = await safety.blocked_ids(session, account_id=ctx)
    entries = await shortlist.list_entries(session, candidate_account_id=ctx, exclude=hidden)
    ids = [e.saved_account_id for e in entries]
    cards = await discovery.cards_for(session, account_ids=ids)
    out = []
    for e in entries:
        snippet = await discovery.get_snippet(session, account_id=e.saved_account_id)
        card = cards.get(e.saved_account_id)
        out.append(
            ShortlistEntryResponse(
                candidate_account_id=str(e.saved_account_id),
                saved_by_account_id=str(e.saved_by_account_id),
                saved_by_me=e.saved_by_account_id == account_id,
                note=e.note,
                created_at=e.created_at.isoformat(),
                locality=snippet.locality if snippet else None,
                education_level=snippet.education_level if snippet else None,
                profession=snippet.profession if snippet else None,
                photo_url=card.photo_url if card else None,
                age=card.age if card else None,
            )
        )
    return out


class ShortlistBody(BaseModel):
    note: str | None = None


@router.post("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_shortlist(
    profile_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    for_candidate: UUID | None = None,
    body: ShortlistBody | None = None,
) -> None:
    ctx = await _context(session, account_id, for_candidate)
    saved = await profile.resolve_account_id(session, profile_id)
    await shortlist.add(
        session,
        acting_account_id=account_id,
        candidate_account_id=ctx,
        saved_account_id=saved,
        note=body.note if body else None,
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_shortlist(
    profile_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    for_candidate: UUID | None = None,
) -> None:
    ctx = await _context(session, account_id, for_candidate)
    saved = await profile.resolve_account_id(session, profile_id)
    await shortlist.remove(session, candidate_account_id=ctx, saved_account_id=saved)
