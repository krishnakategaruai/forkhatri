"""Members dashboard endpoint.

    GET /v1/insights   how many members ForKhatri has, where they live, women
                       and men, ages: totals only, never a person

Open to every signed-in member (owner, 2026-09-27: "let everyone know, I don't
think this contains sensitive data"). The figures are aggregates; no name,
contact detail or profile ever leaves this endpoint.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.deps import AppSettings, DbSession, RequiredSession
from app.components.insights import interface as insights

router = APIRouter(prefix="/v1", tags=["insights"])


@router.get("/insights")
async def member_insights(_: RequiredSession, db: DbSession, settings: AppSettings) -> dict[str, Any]:
    return await insights.build(db, settings)
