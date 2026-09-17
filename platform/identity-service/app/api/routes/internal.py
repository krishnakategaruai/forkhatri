"""Internal service-to-service endpoints (07-tech-reqs.md TR14).

Called only by module services, never by browsers. In deployed environments the
`/internal` prefix must additionally be unreachable from the public edge.
"""

from __future__ import annotations

import hmac
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, DbSession
from app.components.identity import interface as identity
from app.errors import DomainError


def not_through_the_edge(request: Request) -> None:
    """Second layer behind the edge's own block (deploy/Caddyfile): module services call
    this API directly on the private network, so a request that passed through a
    reverse proxy (which always adds X-Forwarded-For) is answered as if the route did not exist."""
    if request.headers.get("x-forwarded-for") is not None:
        raise HTTPException(status_code=404)


router = APIRouter(
    prefix="/internal/v1", tags=["internal"], include_in_schema=False, dependencies=[Depends(not_through_the_edge)]
)


def authenticated_service(
    settings: AppSettings,
    x_forkhatri_service: Annotated[str | None, Header()] = None,
    x_forkhatri_service_key: Annotated[str | None, Header()] = None,
) -> str:
    expected = settings.service_keys.get(x_forkhatri_service or "")
    presented = x_forkhatri_service_key or ""
    if expected is None or not hmac.compare_digest(expected.encode("utf-8"), presented.encode("utf-8")):
        raise DomainError("service_unauthorized", "Unknown service credentials.", 401)
    return x_forkhatri_service or ""


CallingService = Annotated[str, Depends(authenticated_service)]


class ResolveRequest(BaseModel):
    session_token: str = Field(min_length=1, max_length=128)


class LookupRequest(BaseModel):
    member_ids: list[UUID] = Field(max_length=200)


@router.post("/sessions/resolve")
async def resolve_session(
    body: ResolveRequest, service: CallingService, db: DbSession, settings: AppSettings
) -> dict[str, Any]:
    resolved = await identity.resolve_session(db, body.session_token)
    if resolved is None:
        raise DomainError("session_invalid", "The session is not valid.", 401)
    await db.commit()
    member, expires_at = resolved
    return member.claims(expires_at, include_identifiers=service in settings.services_receiving_identifiers)


@router.post("/members/lookup")
async def lookup_members(body: LookupRequest, service: CallingService, db: DbSession) -> list[dict[str, Any]]:
    return await identity.lookup_members(db, list(dict.fromkeys(body.member_ids)))
