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
    identity_level: int = 0

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


_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def origin_allowed(origin: str | None, settings: Settings) -> bool:
    """A cookie-authenticated call must come from a Milavn web origin (or carry no Origin: server-side fetches)."""
    return origin is None or origin in settings.cors_allowed_origins


async def resolve_member_identity(cookies: dict[str, str], header_member_id: str | None, settings: Settings) -> identity.MemberIdentity | None:
    """The one place a request's acting member is identified (HTTP and WebSocket).

    [ParentApp TR15] `fk_session` first, resolved by the platform through the
    Identity Bridge; the legacy `X-Milavn-Member-Id` stand-in only when
    `dev_identity_enabled` is explicitly on. Raises
    `identity.IdentityServiceUnavailable` when the platform cannot answer."""
    token = cookies.get(settings.platform_session_cookie)
    if token:
        ident = await identity.resolve_session(token)
        if ident is not None:
            return ident
    if settings.dev_identity_enabled:
        raw = header_member_id or cookies.get("milavn_member")
        try:
            return identity.resolve_dev(UUID(raw)) if raw else None
        except ValueError:
            return None
    return None


async def get_optional_member(
    request: Request,
    session: DbSession,
    x_milavn_member_id: Annotated[str | None, Header()] = None,
) -> MemberContext | None:
    settings = get_settings()
    try:
        ident = await resolve_member_identity(request.cookies, x_milavn_member_id, settings)
    except identity.IdentityServiceUnavailable as exc:
        # [TR15.3] Fail closed: never fall back to anonymous or a default member.
        from app.i18n import resolve_language, translate

        lang = resolve_language(request.headers.get("x-milavn-language") or request.headers.get("accept-language"))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=translate("auth.identityUnavailable", lang)) from exc
    if ident is not None and request.method in _UNSAFE_METHODS and not origin_allowed(request.headers.get("origin"), settings):
        # Cookie credentials ride along on any same-site request; state changes must come from our own web app.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="origin_not_allowed")
    if ident is None:
        # [FR046/FR029] Anonymous request: bind the nil member so RLS predicates
        # evaluate (a missing variable is a uuid cast error, not "no rows") and
        # only public/community rows match.
        await set_member_context(session, ANONYMOUS_MEMBER_ID, [])
        return None
    await set_member_context(session, ident.member_id, list(ident.scopes))
    return MemberContext(ident.member_id, ident.display_name, ident.handle, ident.avatar, ident.scopes, ident.identity_level)


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
