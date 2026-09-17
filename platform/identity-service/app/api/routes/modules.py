"""Module registry endpoints (07-tech-reqs.md TR13, TR18)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Path, Request

from app.api.deps import AppSettings, DbSession, OptionalSession, RequiredSession, preferred_language
from app.components.registry import interface as registry

router = APIRouter(prefix="/v1/modules", tags=["modules"])


@router.get("")
async def list_modules(
    request: Request, db: DbSession, settings: AppSettings, session: OptionalSession
) -> list[dict[str, Any]]:
    return await registry.list_modules(
        db,
        language=preferred_language(request, session),
        member_id=session.member.member_id if session else None,
        entry_urls=settings.module_entry_urls,
    )


@router.post("/{key}/enter")
async def enter_module(
    db: DbSession,
    settings: AppSettings,
    session: RequiredSession,
    key: str = Path(pattern=r"^[a-z][a-z0-9_]{1,30}$"),
) -> dict[str, str]:
    entry_url = await registry.enter_module(
        db, member_id=session.member.member_id, key=key, entry_urls=settings.module_entry_urls
    )
    await db.commit()
    return {"entry_url": entry_url}
