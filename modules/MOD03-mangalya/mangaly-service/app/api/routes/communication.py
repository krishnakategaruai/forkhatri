"""Communication endpoints — FR049, and the rework's two conversation kinds
(DEC-V1-024, contract §2/§3).

Thin HTTP layer over `components/communication/interface.py`. Mounted twice
by `main.py`: under `/messages` (existing clients) and `/conversations` (the
rework contract) — one router, no prefix here. A thread is addressed by its
connection id plus `?kind=candidate|family` (default candidate).
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.communication import interface as communication
from app.components.profile import interface as profile
from app.components.safety import interface as safety
from app.i18n import translate

router = APIRouter(tags=["messages"])

Kind = Literal["candidate", "family", "direct"]


class MessageResponse(BaseModel):
    id: str
    sender_account_id: str | None
    sender_name: str | None = None
    sender_role: str | None = None
    sender_relation: str | None = None
    sender_side_account_id: str | None = None
    content: str
    kind: str
    sent_at: str


class ParticipantResponse(BaseModel):
    account_id: str
    display_name: str | None
    role: str
    photo_url: str | None
    is_me: bool
    relation: str | None = None
    side_account_id: str | None = None
    side_name: str | None = None


class ConversationResponse(BaseModel):
    connection_id: str
    conversation_id: str
    kind: str
    other_account_id: str
    other_name: str | None
    other_photo_url: str | None
    last_message_at: str | None
    last_message: MessageResponse | None
    unread_count: int
    participants: list[ParticipantResponse]


def _message(m: communication.MessageSummary) -> MessageResponse:
    return MessageResponse(
        id=str(m.id),
        sender_account_id=str(m.sender_account_id) if m.sender_account_id else None,
        sender_name=m.sender_name,
        sender_role=m.sender_role,
        sender_relation=m.sender_relation,
        sender_side_account_id=str(m.sender_side_account_id) if m.sender_side_account_id else None,
        content=m.content,
        kind=m.kind,
        sent_at=m.sent_at.isoformat(),
    )


def _not_available(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=translate("messages.error.notAvailable", lang),
    )


class ContactResponse(BaseModel):
    account_id: str
    display_name: str | None
    photo_url: str | None
    role: str
    relation: str | None = None
    side_account_id: str | None = None
    side_name: str | None = None
    mine: bool


@router.get("/direct/contacts", response_model=list[ContactResponse])
async def direct_contacts(session: DbSession, account_id: AuthenticatedAccount) -> list[ContactResponse]:
    """[DEC-V1-026] Who the caller may message one-to-one."""
    rows = await communication.direct_contacts(session)
    return [
        ContactResponse(
            account_id=str(c.account_id),
            display_name=c.display_name,
            photo_url=profile.resolve_photo_url(c.photo_ref) if c.photo_ref else None,
            role=c.role,
            relation=c.relation,
            side_account_id=str(c.side_account_id) if c.side_account_id else None,
            side_name=c.side_name,
            mine=c.mine,
        )
        for c in rows
    ]


class DirectOpenRequest(BaseModel):
    account_id: UUID


class DirectOpenResponse(BaseModel):
    conversation_id: str
    kind: str = "direct"


@router.post("/direct/open", response_model=DirectOpenResponse)
async def direct_open(
    body: DirectOpenRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> DirectOpenResponse:
    """[DEC-V1-026] Open (or find) the one-to-one chat with this person."""
    try:
        conversation_id = await communication.open_direct(
            session, other_account_id=body.account_id
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc
    return DirectOpenResponse(conversation_id=str(conversation_id))


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    session: DbSession, account_id: AuthenticatedAccount, for_candidate: UUID | None = None
) -> list[ConversationResponse]:
    """[FR049, contract §3] Every conversation the caller may open in this
    context, with `kind`, `unread_count` and a `last_message` preview."""
    try:
        ctx = await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    hidden = await safety.blocked_ids(session, account_id=ctx)
    rows = await communication.list_conversations(
        session, account_id=account_id, context_account_id=ctx, hidden=hidden
    )
    if for_candidate is None:
        # [Migration 046] The caller's own one-to-one chats, newest first
        # together with the connection threads.
        rows = rows + await communication.list_direct_conversations(
            session, account_id=account_id, hidden=hidden
        )
        rows.sort(
            key=lambda r: r.last_message_at.timestamp() if r.last_message_at else 0.0,
            reverse=True,
        )
    responses = []
    for r in rows:
        other = next((p for p in r.participants if p.account_id == r.other_account_id), None)
        responses.append(
            ConversationResponse(
                connection_id=str(r.connection_id),
                conversation_id=str(r.conversation_id),
                kind=r.kind,
                other_account_id=str(r.other_account_id),
                other_name=other.display_name if other else None,
                other_photo_url=(
                    profile.resolve_photo_url(other.photo_ref) if other and other.photo_ref else None
                ),
                last_message_at=r.last_message_at.isoformat() if r.last_message_at else None,
                last_message=_message(r.last_message) if r.last_message else None,
                unread_count=r.unread_count,
                participants=[
                    ParticipantResponse(
                        account_id=str(p.account_id),
                        display_name=p.display_name,
                        role=p.role,
                        photo_url=profile.resolve_photo_url(p.photo_ref) if p.photo_ref else None,
                        is_me=p.account_id == account_id,
                        relation=p.relation,
                        side_account_id=str(p.side_account_id) if p.side_account_id else None,
                        side_name=p.side_name,
                    )
                    for p in r.participants
                ],
            )
        )
    return responses


class FamilyOpenResponse(BaseModel):
    conversation_id: str
    kind: str = "family"


@router.post("/{connection_id}/family/open", response_model=FamilyOpenResponse)
async def open_family(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> FamilyOpenResponse:
    """[DEC-V1-024] "Involve my family": either candidate opens the family
    thread; both circles join. Re-opening returns the same thread."""
    try:
        conversation_id = await communication.open_family_conversation(
            session, connection_id=connection_id, account_id=account_id
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc
    return FamilyOpenResponse(conversation_id=str(conversation_id))


@router.get("/{connection_id}", response_model=list[MessageResponse])
async def list_messages(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    kind: Kind = "candidate",
) -> list[MessageResponse]:
    """[FR049] A thread's messages — `[]` when nothing has been sent yet.
    Opening the thread marks it read for the caller."""
    try:
        rows = await communication.list_messages(
            session, connection_id=connection_id, account_id=account_id, kind=kind
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc
    return [_message(m) for m in rows]


@router.post("/{connection_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    kind: Kind = "candidate",
) -> None:
    try:
        await communication.mark_read(
            session, connection_id=connection_id, account_id=account_id, kind=kind
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc


@router.post("/{connection_id}/close", status_code=status.HTTP_204_NO_CONTENT)
async def close_conversation(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR050/DEC-V1-021] End the candidate session: everything the two wrote
    is deleted for both. Not applicable to a family thread."""
    try:
        await communication.close_conversation(
            session, connection_id=connection_id, account_id=account_id
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc


class SendMessageRequest(BaseModel):
    content: str


@router.post(
    "/{connection_id}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def send_message(
    connection_id: UUID,
    body: SendMessageRequest,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    kind: Kind = "candidate",
) -> MessageResponse:
    """[FR049/TR049] Send a message into the candidate or family thread."""
    content = body.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("messages.error.empty", lang),
        )
    try:
        message_id = await communication.send_message(
            session,
            sender_account_id=account_id,
            connection_id=connection_id,
            content=content,
            kind=kind,
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc
    except communication.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("messages.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    rows = await communication.list_messages(
        session, connection_id=connection_id, account_id=account_id, kind=kind
    )
    sent = next(m for m in rows if m.id == message_id)
    return _message(sent)


@router.get("/{connection_id}/people", response_model=list[ParticipantResponse])
async def thread_people(
    connection_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    kind: Kind = "candidate",
) -> list[ParticipantResponse]:
    """[DEC-V1-024] Everyone in the thread, with exact relation and side."""
    try:
        rows = await communication.people(
            session, connection_id=connection_id, account_id=account_id, kind=kind
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc
    return [
        ParticipantResponse(
            account_id=str(p.account_id),
            display_name=p.display_name,
            role=p.role,
            photo_url=profile.resolve_photo_url(p.photo_ref) if p.photo_ref else None,
            is_me=p.account_id == account_id,
            relation=p.relation,
            side_account_id=str(p.side_account_id) if p.side_account_id else None,
            side_name=p.side_name,
        )
        for p in rows
    ]


class ThreadReportRequest(BaseModel):
    reported_account_id: UUID
    reason: str
    details: str | None = None


class ThreadReportResponse(BaseModel):
    report_id: str
    message: str


@router.post(
    "/{connection_id}/report",
    response_model=ThreadReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def report_in_thread(
    connection_id: UUID,
    body: ThreadReportRequest,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    kind: Kind = "candidate",
) -> ThreadReportResponse:
    """[DEC-V1-024] Report from a thread; the thread is kept with the report."""
    if body.reason not in safety.REPORT_REASONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("safety.error.invalidReason", lang),
        )
    try:
        report_id = await communication.report_conversation(
            session,
            connection_id=connection_id,
            account_id=account_id,
            kind=kind,
            reported_account_id=body.reported_account_id,
            reason=body.reason,
            details=(body.details or "")[:2000] or None,
        )
    except communication.ConversationNotAvailable as exc:
        raise _not_available(lang) from exc
    return ThreadReportResponse(
        report_id=str(report_id), message=translate("safety.report.received", lang)
    )
