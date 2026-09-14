"""FastAPI dependencies — one request = one transaction = one member context.

# [TR-CROSSCUT-03, TR16] Because every RLS session variable is transaction-
# local (`SET LOCAL`), the transaction boundary IS the authorization boundary.
# Approach: the request-scoped session yields with a transaction already open;
# `get_current_member` resolves the acting member through the Identity Bridge
# and binds `milavn.member_id` (and `milavn.permission_scope` for moderators)
# inside that same transaction. Handlers receive an already-resolved
# `MemberContext`, never a raw id they authorise themselves. After a clean
# commit, in-process subscribers run for the events the transaction published.
# Traces to: TR-CROSSCUT-03, TR-CROSSCUT-04, TR16, architecture.md §3.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.identity_bridge import interface as identity
from app.config.settings import Settings, get_settings
from app.db.session import set_member_context
from app.events import bus
from app.i18n import resolve_language


def get_locale(
    x_milavn_language: Annotated[str | None, Header()] = None,
    accept_language: Annotated[str | None, Header()] = None,
) -> str:
    return resolve_language(x_milavn_language or accept_language)


Locale = Annotated[str, Depends(get_locale)]
ANONYMOUS_MEMBER_ID = UUID("00000000-0000-0000-0000-000000000000")
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.session_factory
    async with factory() as session:
        async with session.begin():
            yield session
        # Transaction committed (or rolled back on exception, in which case we
        # never reach here): fan out the events it published.
        await bus.dispatch_pending(session)


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@dataclass(frozen=True, slots=True)
class MemberContext:
    member_id: UUID
    display_name: str
    handle: str
    avatar: str | None
    scopes: tuple[str, ...]

    @property
    def is_moderator(self) -> bool:
        return "milavn.moderate" in self.scopes


def _read_member_header(request: Request, header: str | None) -> UUID | None:
    raw = header or request.cookies.get("milavn_member")
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


async def get_optional_member(
    request: Request,
    session: DbSession,
    x_milavn_member_id: Annotated[str | None, Header()] = None,
) -> MemberContext | None:
    member_id = _read_member_header(request, x_milavn_member_id)
    ident = identity.resolve(member_id) if member_id else None
    if ident is None:
        # [FR046/FR029] Anonymous request: bind the nil member so RLS predicates
        # evaluate (a missing variable is a uuid cast error, not "no rows") and
        # only public/community rows match.
        await set_member_context(session, ANONYMOUS_MEMBER_ID, [])
        return None
    await set_member_context(session, ident.member_id, list(ident.scopes))
    return MemberContext(ident.member_id, ident.display_name, ident.handle, ident.avatar, ident.scopes)


OptionalMember = Annotated[MemberContext | None, Depends(get_optional_member)]


async def get_current_member(member: OptionalMember, lang: Locale) -> MemberContext:
    if member is None:
        from app.i18n import translate

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=translate("auth.notAuthenticated", lang),
        )
    return member


CurrentMember = Annotated[MemberContext, Depends(get_current_member)]


async def get_moderator(member: CurrentMember, lang: Locale) -> MemberContext:
    if not member.is_moderator:
        from app.i18n import translate

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=translate("auth.forbidden", lang))
    return member


Moderator = Annotated[MemberContext, Depends(get_moderator)]


def get_idempotency_key(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> str | None:
    return idempotency_key


IdempotencyKeyHeader = Annotated[str | None, Depends(get_idempotency_key)]
