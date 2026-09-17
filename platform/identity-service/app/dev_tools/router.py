"""Development member switcher, `/dev/v1` (docs/ParentApp/07-tech-reqs.md "Development tools").

Mounted only when `Settings.dev_tools_active` (ENVIRONMENT=development,
DEV_TOOLS_ENABLED=true, LOCAL_HTTP_TEST off); production refuses to start with
DEV_TOOLS_ENABLED=true. The TR20 Origin guard applies to every write here.

- Browser mode (no dev token header): opens a real session and sets the normal
  session cookie exactly like sign-in. The token never appears in the body. The
  browser's previous session, if any, is revoked (this browser only, never
  "everywhere").
- Test mode (`X-ForKhatri-Dev-Token` equal to DEV_TOOLS_TOKEN): no cookie; the
  body carries `session_token` so a non-browser test can set the cookie itself.
  The owner's account is refused in this mode (tests never act as the owner).
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.deps import AppSettings, DbSession, OptionalSession
from app.api.routes.auth import _set_session_cookie
from app.components.identity import interface as identity
from app.components.identity.secrets import constant_time_equal
from app.config.settings import Settings
from app.dev_tools.personas import BY_KEY, OWNER_MEMBER_ID, PERSONAS
from app.errors import DomainError

router = APIRouter(prefix="/dev/v1", tags=["development"])

MIN_TOKEN_LENGTH = 32


class DevSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    persona: str | None = Field(default=None, min_length=1, max_length=40)
    member_id: UUID | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> DevSessionRequest:
        if (self.persona is None) == (self.member_id is None):
            raise ValueError("Send either persona or member_id.")
        return self


def _token_accepted(settings: Settings, presented: str) -> bool:
    configured = settings.dev_tools_token
    if len(configured) < MIN_TOKEN_LENGTH:
        return False
    return constant_time_equal(presented, configured)


@router.get("/personas")
async def list_personas(db: DbSession) -> list[dict[str, Any]]:
    members = await identity.members_by_id(db, [persona.member_id for persona in PERSONAS])
    return [
        {
            "key": persona.key,
            "member_id": str(persona.member_id),
            "display_name": members[persona.member_id].display_name,
            "description": persona.description,
            "for_automated_tests": persona.for_automated_tests,
        }
        for persona in PERSONAS
        if persona.member_id in members
    ]


@router.post("/sessions")
async def open_session(
    body: DevSessionRequest,
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
    current: OptionalSession,
    dev_token: Annotated[str | None, Header(alias="X-ForKhatri-Dev-Token")] = None,
) -> dict[str, Any]:
    test_mode = dev_token is not None
    if test_mode and not _token_accepted(settings, dev_token or ""):
        raise DomainError("dev_token_invalid", "The development token is missing, too short or wrong.", 403)

    if body.persona is not None:
        persona = BY_KEY.get(body.persona)
        if persona is None:
            raise DomainError("persona_unknown", f"Unknown persona. Known: {', '.join(BY_KEY)}.", 404)
        member_id = persona.member_id
    else:
        member_id = body.member_id  # type: ignore[assignment]

    if test_mode and member_id == OWNER_MEMBER_ID:
        raise DomainError("owner_reserved", "Automated tests never act as the owner's account.", 403)

    signed_in = await identity.open_development_session(db, settings, member_id, request.headers.get("user-agent"))
    result: dict[str, Any] = {"outcome": "signed_in", "member": signed_in.member.public()}

    if test_mode:
        await db.commit()
        return {
            **result,
            "session_token": signed_in.session_token,
            "cookie_name": settings.session_cookie_name,
            "expires_at": signed_in.expires_at.isoformat(),
        }

    if current is not None:
        await identity.sign_out(db, current.token, everywhere=False)
    await db.commit()
    _set_session_cookie(response, settings, signed_in)
    return result
