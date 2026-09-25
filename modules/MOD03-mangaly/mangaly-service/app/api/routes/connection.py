"""Connection endpoints — FR042/FR043/FR044/FR045, and the rework's
context-scoped lists, on-behalf sending, `sent_by` and withdraw (contract §3).

Thin HTTP layer over `components/connection/interface.py`. Mounted twice by
`main.py`: under `/connections` (existing clients) and `/connection` (the
rework contract) — one router, no prefix here.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.connection import interface as connection
from app.components.discovery import interface as discovery
from app.components.profile import interface as profile
from app.components.safety import interface as safety
from app.i18n import translate

router = APIRouter(tags=["connections"])


def _not_found(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=translate("connection.error.notFound", lang),
    )


async def _context(session: DbSession, account_id: UUID, for_candidate: UUID | None) -> UUID:
    try:
        return await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc


async def _decider_context(
    session: DbSession, account_id: UUID, for_candidate: UUID | None, lang: str
) -> UUID:
    """[Owner, 2026-09-21] A request to a candidate may be accepted or declined
    by the candidate, or by their mother, father or guardian — not by every
    member of the circle. Siblings and relatives see requests; parents decide
    alongside the candidate."""
    if for_candidate is not None and for_candidate != account_id:
        from app.components.home_circle import interface as home_circle

        contexts = await home_circle.list_member_contexts(session, account_id=account_id)
        mine = next((c for c in contexts if c.candidate_account_id == for_candidate), None)
        if mine is None or mine.relationship_type.value not in ("parent", "guardian"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=translate("connection.error.onlyParentsDecide", lang),
            )
    return await _context(session, account_id, for_candidate)


class SendRequest(BaseModel):
    """[FR042] The target and, when a circle member sends for their candidate,
    who it is for. Ids may be profile ids (contract) or account ids (older
    screens); both are resolved."""

    target_account_id: str | None = None
    target_profile_id: str | None = None
    on_behalf_of_account_id: str | None = None
    on_behalf_of_profile_id: str | None = None
    for_candidate: str | None = None


class SentByResponse(BaseModel):
    relationship: str
    display_name: str | None
    candidate_name: str | None


class SnippetOut(BaseModel):
    locality: str | None = None
    education_level: str | None = None
    profession: str | None = None
    photo_url: str | None = None
    age: int | None = None
    # The first name, only when they chose to show it openly (migration 043).
    open_name: str | None = None


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
    # [Contract §2] "Sent by Ananya's mother": relation + the member's name;
    # the candidate's own name only where identity is already disclosed.
    sent_by: SentByResponse | None = None
    subject_name: str | None = None
    target_name: str | None = None
    subject: SnippetOut | None = None


async def _to_response(
    session: DbSession, c: connection.ConnectionSummary, *, with_snippet: bool = False
) -> ConnectionResponse:
    on_behalf_str = str(c.on_behalf_of_profile_id) if c.on_behalf_of_profile_id else None
    info = await connection.sender_info(session, connection_id=c.id)
    sent_by = None
    if info is not None and info.relationship != "self":
        sent_by = SentByResponse(
            relationship=info.relationship,
            display_name=info.acting_name,
            candidate_name=info.subject_name,
        )
    subject = None
    if with_snippet:
        snippet = await discovery.get_snippet(session, account_id=c.subject_account_id)
        card = (await discovery.cards_for(session, account_ids=[c.subject_account_id])).get(
            c.subject_account_id
        )
        opened = (await discovery.open_cards_for(session, account_ids=[c.subject_account_id])).get(
            c.subject_account_id
        )
        if snippet or card:
            subject = SnippetOut(
                open_name=(opened.first_name or None) if opened else None,
                locality=snippet.locality if snippet else None,
                education_level=snippet.education_level if snippet else None,
                profession=snippet.profession if snippet else None,
                photo_url=card.photo_url if card else None,
                age=card.age if card else None,
            )
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
        sent_by=sent_by,
        subject_name=info.subject_name if info else None,
        target_name=info.target_name if info else None,
        subject=subject,
    )


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def send_request(
    body: SendRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> ConnectionResponse:
    """[FR042/TR042, DEC-V1-022] Send a connection request — for yourself, or
    for a candidate whose Home Circle you belong to (any relation)."""
    raw_target = body.target_profile_id or body.target_account_id
    if not raw_target:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("connection.error.invalidTarget", lang),
        )
    target_account_id = await profile.resolve_account_id(session, UUID(raw_target))
    raw_behalf = body.on_behalf_of_profile_id or body.on_behalf_of_account_id or body.for_candidate
    try:
        context_account_id = await authz.resolve_context_account(
            session,
            acting_account_id=account_id,
            for_candidate=UUID(raw_behalf) if raw_behalf else None,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=translate("connection.error.onBehalfNotAllowed", lang),
        ) from exc
    try:
        connection_id = await connection.send_request(
            session,
            acting_account_id=account_id,
            target_account_id=target_account_id,
            on_behalf_of_account_id=(
                context_account_id if context_account_id != account_id else None
            ),
        )
    except connection.InvalidTarget as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("connection.error.invalidTarget", lang),
        ) from exc
    except connection.OnBehalfRoleNotAllowed as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "on_behalf_parents_only", "message": translate("connection.error.onBehalfParentsOnly", lang)},
        ) from exc
    except connection.RequestCooldown as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": f"cooldown_{exc.reason}",
                "until": exc.until.date().isoformat(),
                "message": translate(
                    f"connection.error.cooldown_{exc.reason}",
                    lang,
                    date=exc.until.strftime("%d/%m/%Y"),
                ),
            },
        ) from exc
    except connection.NotLookingFor as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "not_looking_for", "message": translate("connection.error.notLookingFor", lang)},
        ) from exc
    except connection.AlreadyPending as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("connection.error.alreadyPending", lang),
        ) from exc
    except connection.AlreadyConnected as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("connection.error.alreadyConnected", lang),
        ) from exc
    except connection.Blocked as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "blocked", "message": translate("connection.error.blocked", lang)},
        ) from exc
    except connection.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("connection.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except connection.OnBehalfNotAllowed as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=translate("connection.error.onBehalfNotAllowed", lang),
        ) from exc

    result = await connection.get_request(session, connection_id=connection_id)
    assert result is not None
    return await _to_response(session, result)


@router.get("/incoming", response_model=list[ConnectionResponse])
async def list_incoming(
    session: DbSession, account_id: AuthenticatedAccount, for_candidate: UUID | None = None
) -> list[ConnectionResponse]:
    """[FR043] Pending requests addressed to the context candidate (the caller,
    or the candidate their circle helps). Blocked people are absent."""
    ctx = await _context(session, account_id, for_candidate)
    hidden = await safety.blocked_ids(session, account_id=ctx)
    rows = await connection.list_incoming(session, account_id=ctx)
    return [
        await _to_response(session, r, with_snippet=True)
        for r in rows
        if r.subject_account_id not in hidden
    ]


@router.get("/sent", response_model=list[ConnectionResponse])
async def list_sent(
    session: DbSession, account_id: AuthenticatedAccount, for_candidate: UUID | None = None
) -> list[ConnectionResponse]:
    """[FR045] Every request sent in the context candidate's name, any status."""
    ctx = await _context(session, account_id, for_candidate)
    hidden = await safety.blocked_ids(session, account_id=ctx)
    rows = await connection.list_sent(session, account_id=ctx)
    return [
        await _to_response(session, r)
        for r in rows
        if r.target_account_id not in hidden and r.subject_account_id == ctx
    ]


@router.get("/{connection_id}", response_model=ConnectionResponse | None)
async def get_connection(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    for_candidate: UUID | None = None,
) -> ConnectionResponse | None:
    """[FR043] One request's full detail for the review screen."""
    await _context(session, account_id, for_candidate)
    result = await connection.get_request(session, connection_id=connection_id)
    return await _to_response(session, result, with_snippet=True) if result else None


@router.post("/{connection_id}/accept", status_code=status.HTTP_204_NO_CONTENT)
async def accept(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    for_candidate: UUID | None = None,
) -> None:
    """[FR043/FR044] Accept — grants each party visibility into the other's
    full profile. A circle member may accept for their candidate."""
    ctx = await _decider_context(session, account_id, for_candidate, lang)
    try:
        await connection.accept(
            session, connection_id=connection_id, account_id=ctx, acting_account_id=account_id
        )
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc


@router.post("/{connection_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    for_candidate: UUID | None = None,
) -> None:
    """[FR043] Decline."""
    ctx = await _decider_context(session, account_id, for_candidate, lang)
    try:
        await connection.decline(
            session, connection_id=connection_id, account_id=ctx, acting_account_id=account_id
        )
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc


@router.post("/{connection_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    for_candidate: UUID | None = None,
) -> None:
    """[Contract §3] Take back a pending request sent in the candidate's name."""
    ctx = await _context(session, account_id, for_candidate)
    try:
        await connection.withdraw(
            session, connection_id=connection_id, account_id=ctx, acting_account_id=account_id
        )
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
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    for_candidate: UUID | None = None,
) -> SharingResponse:
    """[FR046/FR047] Per-category sharing in both directions for one accepted connection.

    [Owner, 2026-09-25] With `for_candidate`, a parent or guardian of that
    candidate reads what the match has shared with the candidate — contact
    reaches parents only through the match's own sharing. Read-only: the
    candidate's own share controls (`mine`) are not returned to them."""
    ctx = await _decider_context(session, account_id, for_candidate, lang)
    try:
        result = await connection.sharing_overview(
            session, connection_id=connection_id, account_id=ctx
        )
    except connection.ConnectionNotFound as exc:
        raise _not_found(lang) from exc
    family_mine, family_theirs = await connection.family_contact_overview(
        session, connection_id=connection_id, account_id=ctx
    )
    own_controls = ctx == account_id
    return SharingResponse(
        connection_id=str(result.connection_id),
        other_account_id=str(result.other_account_id),
        mine=[*(_share_state(s) for s in result.mine), _share_state(family_mine)] if own_controls else [],
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
    """[FR046/TR046] Share or stop sharing one category."""
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
    """[FR048/TR048] Ask one Home Circle member to approve sharing their phone."""
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
