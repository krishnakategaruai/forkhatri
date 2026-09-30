"""Guides endpoints (migration 063): `GET /guides`, `GET /guides/{slug}`,
in the reader's language (`X-Mangalya-Language`), English otherwise.

Signed-in members only, like every other screen; nothing here is private.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.guides import interface as guides

router = APIRouter(prefix="/guides", tags=["guides"])


@router.get("")
async def list_guides(
    session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> list[dict]:
    return await guides.list_guides(session, lang=lang)


@router.get("/{slug}")
async def get_guide(
    slug: str, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict:
    guide = await guides.get_guide(session, slug=slug, lang=lang)
    if guide is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return guide
