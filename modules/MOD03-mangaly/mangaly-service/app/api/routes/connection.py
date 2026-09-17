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
    # [FR042] The candidate this request is for, when a Home Circle member sends it.
    on_behalf_of_account_id: str | None = None


class ConnectionResponse(BaseModel):
    id: str
    acting_account_id: str
    subject_account_id: str
    sent_by_family: bool
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
        subject_account_id=str(c.subject_account_id),
        sent_by_family=c.acting_account_id != c.subject_account_id,
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
            on_behalf_of_account_id=(
                UUID(body.on_behalf_of_account_id) if body.on_behalf_of_account_id else None
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
    except connection.OnBehalfNotAllowed as exc:
        # Not authorized to act for that candidate — never downgraded to a request
        # from the caller themselves, which would misattribute it (BR15).
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=translate("connection.error.onBehalfNotAllowed", lang),
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


class ShareStateResponse(BaseModel):
    category: str
    shared_at: str | None
    value: str | None
    available: bool
    pending: str | None = None


class SharingResponse(BaseModel):
    connection_id: str
    other_account_id: str
    mine: list[ShareStateResponse]
    theirs: list[ShareStateResponse]


class ShareRequest(BaseModel):
    shared: bool


def _share_state(s: connection.ShareState) -> ShareStateResponse:
    return ShareStateResponse(
        category=s.category,
        shared_at=s.shared_at.isoformat() if s.shared_at else None,
        value=s.value,
        available=s.available,
        pending=s.pending,
    )


@router.get("/{connection_id}/sharing", response_model=SharingResponse)
async def get_sharing(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> SharingResponse:
    """[FR046/FR047] Per-category sharing in both directions for one accepted connection."""
    try:
        result = await connection.sharing_overview(
            session, connection_id=connection_id, account_id=account_id
        )
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc
    family_mine, family_theirs = await connection.family_contact_overview(
        session, connection_id=connection_id, account_id=account_id
    )
    return SharingResponse(
        connection_id=str(result.connection_id),
        other_account_id=str(result.other_account_id),
        mine=[*(_share_state(s) for s in result.mine), _share_state(family_mine)],
        theirs=[
            _share_state(s) for s in [*result.theirs, *([family_theirs] if family_theirs else [])]
        ],
    )


@router.patch("/{connection_id}/share/{category}", response_model=ShareStateResponse)
async def set_share(
    connection_id: UUID,
    category: str,
    body: ShareRequest,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> ShareStateResponse:
    """[FR046/TR046] Share or stop sharing one category. Sending the same
    state twice changes nothing, so a retried request is harmless."""
    try:
        result = await connection.set_share(
            session,
            connection_id=connection_id,
            account_id=account_id,
            category=category,
            shared=body.shared,
        )
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc
    except connection.ShareUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("connection.error.shareUnavailable", lang),
        ) from exc
    return _share_state(result)


class FamilyContactBody(BaseModel):
    membership_id: UUID


@router.post("/{connection_id}/share/family-contact", response_model=ShareStateResponse)
async def request_family_contact(
    connection_id: UUID,
    body: FamilyContactBody,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> ShareStateResponse:
    """[FR048/TR048] Ask one Home Circle member to approve sharing their phone
    with this connection. Nothing is shared until they approve."""
    try:
        result = await connection.request_family_contact(
            session,
            connection_id=connection_id,
            account_id=account_id,
            membership_id=body.membership_id,
        )
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc
    except connection.NotAHomeCircleMember as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("connection.error.notAMember", lang),
        ) from exc
    return _share_state(result)


@router.delete("/{connection_id}/share/family-contact", response_model=ShareStateResponse)
async def withdraw_family_contact(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> ShareStateResponse:
    """Stop sharing a family contact with this connection."""
    try:
        result = await connection.withdraw_family_contact(
            session, connection_id=connection_id, account_id=account_id
        )
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc
    return _share_state(result)
