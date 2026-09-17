"""Public authentication endpoints (07-tech-reqs.md TR13).

Write paths commit before returning so the session row exists before the browser
can make its next request with the new cookie.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, Field, StringConstraints

from app.api.deps import AppSettings, DbSession, OptionalSession, SessionFactory, client_ip
from app.components.identity import interface as identity
from app.config.settings import Settings

router = APIRouter(prefix="/v1/auth", tags=["auth"])

DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class CodeRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=254)


class CodeResponse(BaseModel):
    challenge_id: UUID
    channel: str
    destination_hint: str
    expires_in: int
    resend_in: int
    dev_code: str | None = None


class VerifyRequest(BaseModel):
    challenge_id: UUID
    code: str = Field(pattern=r"^\d{6}$")


class WelcomeRequest(VerifyRequest):
    display_name: DisplayName
    preferred_language: Literal["en", "hi", "te"] = "en"


class PasswordRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class SignOutRequest(BaseModel):
    everywhere: bool = False


def _set_session_cookie(response: Response, settings: Settings, signed_in: identity.SignedIn) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        signed_in.session_token,
        max_age=settings.session_ttl_days * 86400,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _signed_in_body(signed_in: identity.SignedIn) -> dict[str, Any]:
    return {"outcome": "signed_in", "member": signed_in.member.public()}


@router.post("/code", status_code=status.HTTP_202_ACCEPTED, response_model=CodeResponse, response_model_exclude_none=True)
async def request_code(
    body: CodeRequest, request: Request, db: DbSession, factory: SessionFactory, settings: AppSettings
) -> CodeResponse:
    challenge = await identity.start_code_challenge(db, factory, settings, body.identifier, client_ip(request))
    return CodeResponse(
        challenge_id=challenge.challenge_id,
        channel=challenge.channel,
        destination_hint=challenge.destination_hint,
        expires_in=challenge.expires_in,
        resend_in=challenge.resend_in,
        dev_code=challenge.dev_code,
    )


@router.post("/code/verify")
async def verify_code(
    body: VerifyRequest,
    request: Request,
    response: Response,
    db: DbSession,
    factory: SessionFactory,
    settings: AppSettings,
) -> dict[str, Any]:
    signed_in = await identity.verify_code(
        db, factory, settings, body.challenge_id, body.code, request.headers.get("user-agent")
    )
    await db.commit()
    if signed_in is None:
        return {"outcome": "name_required"}
    _set_session_cookie(response, settings, signed_in)
    return _signed_in_body(signed_in)


@router.post("/welcome", status_code=status.HTTP_201_CREATED)
async def welcome(
    body: WelcomeRequest,
    request: Request,
    response: Response,
    db: DbSession,
    factory: SessionFactory,
    settings: AppSettings,
) -> dict[str, Any]:
    signed_in = await identity.complete_welcome(
        db,
        factory,
        settings,
        challenge_id=body.challenge_id,
        code=body.code,
        display_name=body.display_name,
        preferred_language=body.preferred_language,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    _set_session_cookie(response, settings, signed_in)
    return _signed_in_body(signed_in)


@router.post("/password")
async def password_sign_in(
    body: PasswordRequest,
    request: Request,
    response: Response,
    db: DbSession,
    factory: SessionFactory,
    settings: AppSettings,
) -> dict[str, Any]:
    signed_in = await identity.password_sign_in(
        db,
        factory,
        settings,
        raw_identifier=body.identifier,
        password=body.password,
        client_ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    _set_session_cookie(response, settings, signed_in)
    return _signed_in_body(signed_in)


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def sign_out(
    response: Response,
    db: DbSession,
    settings: AppSettings,
    session: OptionalSession,
    body: SignOutRequest | None = None,
) -> None:
    if session is not None:
        await identity.sign_out(db, session.token, everywhere=bool(body and body.everywhere))
        await db.commit()
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )
