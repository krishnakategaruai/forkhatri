"""FastAPI dependencies: one request, one database session, one resolved member."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.components.identity import interface as identity
from app.config.settings import Settings, get_settings
from app.errors import DomainError

AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory


SessionFactory = Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)]


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@dataclass(frozen=True, slots=True)
class CurrentSession:
    member: identity.Member
    expires_at: datetime
    token: str


async def get_optional_session(request: Request, db: DbSession, settings: AppSettings) -> CurrentSession | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    resolved = await identity.resolve_session(db, token)
    if resolved is None:
        return None
    member, expires_at = resolved
    return CurrentSession(member, expires_at, token)


OptionalSession = Annotated[CurrentSession | None, Depends(get_optional_session)]


async def get_current_session(session: OptionalSession) -> CurrentSession:
    if session is None:
        raise DomainError("not_signed_in", "Sign in to ForKhatri to continue.", 401)
    return session


RequiredSession = Annotated[CurrentSession, Depends(get_current_session)]


def preferred_language(request: Request, session: CurrentSession | None) -> str:
    if session is not None:
        return session.member.preferred_language
    header = request.headers.get("accept-language", "")
    for part in header.split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in ("en", "hi", "te"):
            return code
    return "en"
