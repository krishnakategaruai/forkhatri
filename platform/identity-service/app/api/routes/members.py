"""Signed-in member endpoints (07-tech-reqs.md TR13)."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import DbSession, RequiredSession
from app.components.identity import interface as identity
from app.errors import DomainError

router = APIRouter(prefix="/v1", tags=["member"])


class MemberPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=80)
    preferred_language: Literal["en", "hi", "te"] | None = None


@router.get("/session")
async def current_session(session: RequiredSession) -> dict[str, Any]:
    return {"member": session.member.public(), "expires_at": session.expires_at.isoformat()}


@router.patch("/me")
async def update_me(body: MemberPatch, session: RequiredSession, db: DbSession) -> dict[str, Any]:
    changes: dict[str, str | None] = {}
    for name in body.model_fields_set:
        value = getattr(body, name)
        if isinstance(value, str):
            value = value.strip()
        if name in ("display_name", "preferred_language") and not value:
            raise DomainError("validation_failed", f"{name} cannot be empty.", 422)
        changes[name] = value or None
    member = await identity.update_member(db, session.member.member_id, changes)
    await db.commit()
    return member.public()
