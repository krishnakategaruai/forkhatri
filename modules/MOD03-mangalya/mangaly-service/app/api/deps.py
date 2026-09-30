"""FastAPI dependencies — the wiring between a request and the foundations.

# [TR017/SP017] One request = one transaction = one authorization context.
# Approach: because every RLS session variable is transaction-local (`SET
# LOCAL`), the transaction boundary IS the authorization boundary. So the
# request-scoped dependency yields a session with a transaction ALREADY OPEN,
# rather than letting each handler open its own: a handler that opened a second
# transaction would silently run it with no `mangaly.authz_context` set, and
# every RLS-protected query inside it would return zero rows — a fail-quiet
# shape that looks like "no data" rather than like a bug.
#
# `get_db_session` commits on clean exit and rolls back on any exception, which
# is what makes the transactional outbox (`app/events/bus.py`) atomic with the
# state change: both are in this one transaction.
#
# `get_authenticated_account` now performs REAL session validation against
# `mangaly_identity.session` via the Identity Bridge (TR090/TR101, landed with
# FR092/FR093). It still fails closed: any token that is malformed, unknown,
# expired or revoked yields 401 rather than a default account.
# Traces to: TR017, TR102, SP017, SP102, SP104.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.i18n import resolve_language


def get_locale(
    # [Owner walkthrough, 2026-09-29] Renamed from x_mangaly_language: FastAPI
    # derives the wire header name from this parameter's own spelling
    # (x_mangaly_language -> "X-Mangaly-Language"), so it had silently
    # stopped matching the "X-Mangalya-Language" header the frontend has sent
    # since the MOD03 "Mangaly" -> "Mangalya" rename. Every server-rendered
    # string (match reasons, plan features, notifications) fell back to
    # Accept-Language — usually English — regardless of the member's chosen
    # language, while client-rendered text kept translating correctly through
    # its own, unrelated i18next path. That split is what made the bug hard
    # to spot: most of a screen was in the right language and a few strings
    # on the same screen were not.
    x_mangalya_language: Annotated[str | None, Header()] = None,
    accept_language: Annotated[str | None, Header()] = None,
) -> str:
    """[ADR-010] Resolve the caller's language for localized responses.

    `X-Mangalya-Language` takes priority — it carries the frontend's actual
    resolved i18next language (the user's saved choice, per
    `mangaly-web/lib/i18n/provider.tsx`), which is more specific than the
    browser's `Accept-Language` and is what should win once a user has made an
    explicit choice. `Accept-Language` remains the fallback for any caller that
    does not send the custom header (a script, a future non-web client).
    """
    return resolve_language(x_mangalya_language or accept_language)


Locale = Annotated[str, Depends(get_locale)]


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield one session with one open transaction for the whole request."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        async with session.begin():
            yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_session_token(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    """Read the INTERIM session token from the HttpOnly cookie, or a bearer header.

    [2026-09-14] Legacy only: honoured solely when `interim_identity_enabled`
    is true. The ForKhatri `fk_session` cookie is read in
    `get_authenticated_account`.

    [SP090] The cookie is the real transport for browsers — it is HttpOnly so
    page JS cannot read it. The bearer header is accepted too so that tests and
    non-browser clients have a path that does not depend on a cookie jar.
    """
    cookie = request.cookies.get("mangaly_session")
    if cookie:
        return cookie
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def _not_authenticated() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


@dataclass(frozen=True, slots=True)
class AuthenticatedSessionInfo:
    """The caller's account plus, for a ForKhatri session, when it expires."""

    account_id: UUID
    expires_at: datetime | None
    display_name: str | None = None
    preferred_language: str | None = None
    # [ADR-012] Platform admin scopes (shared console), e.g. "mangaly.moderate".
    admin_scopes: tuple[str, ...] = ()


async def get_authenticated_session(
    request: Request,
    session: DbSession,
    settings: AppSettings,
    legacy_token: Annotated[str | None, Depends(get_current_session_token)],
) -> AuthenticatedSessionInfo:
    """Resolve the caller's account and bind `mangaly.account_id` for this transaction.

    [ForKhatri TR15, 2026-09-14] The ForKhatri session cookie is read FIRST and
    is the only credential in normal operation: the Identity Bridge resolves it
    against the platform Identity & Trust Service, ensures the member-link row
    and binds the RLS context with SET LOCAL inside THIS transaction
    [TR017/SP017]. When the cookie is present, its answer is final — a legacy
    token cannot rescue an invalid platform session.

    The interim `mangaly_session`/bearer path is reachable only when
    `interim_identity_enabled` is true (automated tests; TR15 step 5).

    Fails closed: 401 when not signed in, 503 when the identity service cannot
    answer (never a default account), 403 when the link row cannot be made.
    """
    # Imported here rather than at module scope: `deps` is imported by every
    # router, and a top-level import would make this low-level wiring module
    # depend on a component package at import time.
    from app.components.identity_bridge import interface as identity

    platform_token = request.cookies.get(settings.platform_session_cookie_name)
    if platform_token:
        try:
            resolved = await identity.resolve_platform_session(session, platform_token)
            await _refuse_if_suspended(session, resolved.account_id, request)
            return AuthenticatedSessionInfo(
                resolved.account_id,
                resolved.expires_at,
                resolved.display_name,
                resolved.preferred_language,
                resolved.admin_scopes,
            )
        except identity.PlatformSessionInvalid:
            raise _not_authenticated() from None
        except identity.PlatformIdentityUnavailable:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "identity_unavailable",
                    "message": "ForKhatri sign-in is temporarily unavailable. Please try again.",
                },
                headers={"Retry-After": "5"},
            ) from None
        except identity.PlatformLinkRefused as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": exc.code,
                    "message": "This ForKhatri account cannot open Mangalya right now. "
                    "Please contact support.",
                },
            ) from None

    if settings.interim_identity_enabled and legacy_token:
        account_id = await identity.validate_session(session, legacy_token)
        if account_id is not None:
            await _refuse_if_suspended(session, account_id, request)
            return AuthenticatedSessionInfo(account_id, None)

    raise _not_authenticated()


async def _refuse_if_suspended(session: AsyncSession, account_id: UUID, request: Request) -> None:
    """[DEC-V1-028] A moderator-suspended account is refused on every request
    with a translated 403. One indexed SECURITY DEFINER lookup (migration 048),
    so the cost is a primary-key-shaped read, not a policy evaluation."""
    from sqlalchemy import text

    suspended = (
        await session.execute(
            text("SELECT mangaly_operations.is_suspended(:id)"), {"id": account_id}
        )
    ).scalar_one()
    if suspended:
        from app.i18n import translate

        lang = resolve_language(
            request.headers.get("x-mangalya-language") or request.headers.get("accept-language")
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "account_suspended", "message": translate("safety.error.suspended", lang)},
        )


AuthenticatedSession = Annotated[AuthenticatedSessionInfo, Depends(get_authenticated_session)]


# [DEC-V1-019] Paths a parent may act on for a profile they created and the
# candidate has not taken over yet: the profile itself and its photos. Nothing
# else — not requests, not messages, not the candidate's own words — ever runs
# as the candidate on someone else's behalf.
_MANAGE_PATH_PREFIXES = ("/profile", "/media")
_MANAGE_EXCLUDED = ("/profile/managed", "/profile/claim")


async def get_authenticated_account(
    caller: AuthenticatedSession, request: Request, session: DbSession
) -> UUID:
    """The caller's account id. FastAPI caches `get_authenticated_session` per
    request, so a route using both resolves the session once.

    With `X-Mangalya-Manage: <candidate id>` on a /profile or /media request, a
    parent editing a profile they created (and which is not yet claimed) acts
    as that candidate for this one request: `can_manage()` is checked in the
    database, then both RLS variables are rebound to the candidate. Any other
    path, or a failed check, ignores the header entirely.

    [Owner walkthrough, 2026-09-29] Was reading "x-mangaly-manage" — one more
    header spelling the MOD03 rename left behind while the frontend already
    sent "X-Mangalya-Manage" (`lib/api.ts`). This override never fired: a
    parent editing a not-yet-claimed child profile was silently editing their
    OWN account instead, the same shape of bug as the language header above.
    """
    target = request.headers.get("x-mangalya-manage")
    path = request.url.path
    if not target or not path.startswith(_MANAGE_PATH_PREFIXES) or path.startswith(_MANAGE_EXCLUDED):
        return caller.account_id
    from sqlalchemy import text

    from app.db.session import set_account_context, set_authz_context

    try:
        candidate = UUID(target)
    except ValueError:
        return caller.account_id
    allowed = (
        await session.execute(
            text("SELECT mangaly_profile.can_manage(:creator, :candidate)"),
            {"creator": caller.account_id, "candidate": candidate},
        )
    ).scalar_one()
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not managed by you")
    await set_account_context(session, candidate)
    await set_authz_context(session, candidate)
    request.state.managing_for = candidate
    return candidate


AuthenticatedAccount = Annotated[UUID, Depends(get_authenticated_account)]


def get_idempotency_key(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> str | None:
    """[TR102] Read the client-generated key.

    Returned as-is (including None). Endpoints in TR102's named list declare it
    as required at the router; the guard does not silently tolerate its absence.
    """
    return idempotency_key


IdempotencyKeyHeader = Annotated[str | None, Depends(get_idempotency_key)]
