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
from app.components.governance import interface as governance
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
    claims = member.claims(expires_at, include_identifiers=service in settings.services_receiving_identifiers)
    # Module permissions the samaj appointed this member to in the Admin & Governance
    # Console (e.g. "milavn.moderate"). Modules map them onto their own chokepoint.
    claims["admin_scopes"] = await governance.module_scopes_for(db, member.member_id)
    return claims


class ProvisionRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=32)
    display_name: str = Field(min_length=1, max_length=80)
    preferred_language: str = Field(default="en", pattern="^(en|hi|te)$")


@router.post("/members/provision", status_code=201)
async def provision_member(
    body: ProvisionRequest, service: CallingService, db: DbSession, settings: AppSettings
) -> dict[str, Any]:
    """A module creates a not-yet-joined member for a mobile number (a parent
    creating their child's profile). Only services trusted with identifiers may;
    an existing member's number is refused, never reused."""
    if service not in settings.services_receiving_identifiers:
        raise DomainError("service_forbidden", "This service may not provision members.", 403)
    try:
        member_id, phone_e164 = await identity.provision_member(
            db, raw_phone=body.phone, display_name=body.display_name, preferred_language=body.preferred_language
        )
    except identity.MemberExists:
        raise DomainError("member_exists", "That number already belongs to a ForKhatri member.", 409) from None
    except identity.InvalidIdentifier as exc:
        raise DomainError("identifier_invalid", str(exc), 422) from exc
    await db.commit()
    return {"member_id": str(member_id), "phone_e164": phone_e164}


@router.post("/members/{member_id}/retire-provisioned")
async def retire_provisioned(
    member_id: UUID, service: CallingService, db: DbSession, settings: AppSettings
) -> dict[str, Any]:
    """The six-month rule (owner, 2026-09-21): a member provisioned for someone
    who never used it is removed. Used members are never touched."""
    if service not in settings.services_receiving_identifiers:
        raise DomainError("service_forbidden", "This service may not retire members.", 403)
    removed = await identity.retire_provisioned_member(db, member_id)
    await db.commit()
    return {"removed": removed}


@router.post("/members/lookup")
async def lookup_members(body: LookupRequest, service: CallingService, db: DbSession) -> list[dict[str, Any]]:
    return await identity.lookup_members(db, list(dict.fromkeys(body.member_ids)))
