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
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.i18n import resolve_language


def get_locale(
    x_mangaly_language: Annotated[str | None, Header()] = None,
    accept_language: Annotated[str | None, Header()] = None,
) -> str:
    """[ADR-010] Resolve the caller's language for localized responses.

    `X-Mangaly-Language` takes priority — it carries the frontend's actual
    resolved i18next language (the user's saved choice, per
    `mangaly-web/lib/i18n/provider.tsx`), which is more specific than the
    browser's `Accept-Language` and is what should win once a user has made an
    explicit choice. `Accept-Language` remains the fallback for any caller that
    does not send the custom header (a script, a future non-web client).
    """
    return resolve_language(x_mangaly_language or accept_language)


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
    """Read the session token from the HttpOnly cookie, or a bearer header.

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


async def get_authenticated_account(
    session: DbSession,
    token: Annotated[str | None, Depends(get_current_session_token)],
) -> UUID:
    """Resolve the caller's account and bind `mangaly.account_id` for this transaction.

    [TR090/TR101] Validation is a real lookup against `mangaly_identity.session`
    (not revoked, not expired). [TR017/SP017] On success the Identity Bridge
    binds the context with SET LOCAL inside THIS transaction, which is the only
    scope where it is meaningful and the only thing that stops a pooled
    connection inheriting it.

    Fails closed: every failure mode returns the same 401.
    """
    # Imported here rather than at module scope: `deps` is imported by every
    # router, and a top-level import would make this low-level wiring module
    # depend on a component package at import time.
    from app.components.identity_bridge import interface as identity

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account_id = await identity.validate_session(session, token)
    if account_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return account_id


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
