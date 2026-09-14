"""Connection endpoints — FR042/FR043/FR044/FR045.

Thin HTTP layer over `components/connection/interface.py`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.connection import interface as connection
from app.i18n import translate

router = APIRouter(prefix="/connections", tags=["connections"])


def _not_found(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=translate("connection.error.notFound", lang),
    )


class SendRequest(BaseModel):
    target_account_id: str
    on_behalf_of_profile_id: str | None = None


class ConnectionResponse(BaseModel):
    id: str
    acting_account_id: str
    on_behalf_of_profile_id: str | None
    target_account_id: str
    status: str
    requested_at: str
    decided_at: str | None


def _to_response(c: connection.ConnectionSummary) -> ConnectionResponse:
    on_behalf_str = str(c.on_behalf_of_profile_id) if c.on_behalf_of_profile_id else None
    return ConnectionResponse(
        id=str(c.id),
        acting_account_id=str(c.acting_account_id),
        on_behalf_of_profile_id=on_behalf_str,
        target_account_id=str(c.target_account_id),
        status=c.status.value,
        requested_at=c.requested_at.isoformat(),
        decided_at=c.decided_at.isoformat() if c.decided_at else None,
    )


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def send_request(
    body: SendRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> ConnectionResponse:
    """[FR042/TR042] Send a connection request."""
    try:
        connection_id = await connection.send_request(
            session,
            acting_account_id=account_id,
            target_account_id=UUID(body.target_account_id),
            on_behalf_of_profile_id=(
                UUID(body.on_behalf_of_profile_id) if body.on_behalf_of_profile_id else None
            ),
        )
    except connection.InvalidTarget as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("connection.error.invalidTarget", lang),
        ) from exc
    except connection.AlreadyPending as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("connection.error.alreadyPending", lang),
        ) from exc
    except connection.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("connection.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except connection.UnauthorizedOnBehalfOf as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=translate("connection.error.unauthorizedOnBehalfOf", lang),
        ) from exc

    result = await connection.get_request(session, connection_id=connection_id)
    assert result is not None
    return _to_response(result)


@router.get("/incoming", response_model=list[ConnectionResponse])
async def list_incoming(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[ConnectionResponse]:
    """[FR043] Pending requests addressed to the caller."""
    rows = await connection.list_incoming(session, account_id=account_id)
    return [_to_response(r) for r in rows]


@router.get("/sent", response_model=list[ConnectionResponse])
async def list_sent(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[ConnectionResponse]:
    """[FR045] Every connection the caller has sent, any status."""
    rows = await connection.list_sent(session, account_id=account_id)
    return [_to_response(r) for r in rows]


@router.get("/{connection_id}", response_model=ConnectionResponse | None)
async def get_connection(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> ConnectionResponse | None:
    """[FR043] One request's full detail for the review screen."""
    result = await connection.get_request(session, connection_id=connection_id)
    return _to_response(result) if result else None


@router.post("/{connection_id}/accept", status_code=status.HTTP_204_NO_CONTENT)
async def accept(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR043/FR044] Accept — grants each party visibility into the other's
    full profile (see `interface.accept()`'s docstring)."""
    try:
        await connection.accept(session, connection_id=connection_id, account_id=account_id)
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc


@router.post("/{connection_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR043] Decline."""
    try:
        await connection.decline(session, connection_id=connection_id, account_id=account_id)
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc
