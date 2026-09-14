"""Communication endpoints — FR049.

Thin HTTP layer over `components/communication/interface.py`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.communication import interface as communication
from app.components.profile import interface as profile
from app.i18n import translate

router = APIRouter(prefix="/messages", tags=["messages"])


class ConversationResponse(BaseModel):
    connection_id: str
    other_account_id: str
    other_name: str | None
    other_photo_url: str | None
    last_message_at: str | None


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[ConversationResponse]:
    """[FR049] Every conversation the caller is a party to, recency-ordered.
    `other_name`/`other_photo_url` are safe to resolve here (unlike
    Discovery's pending-request identification): a conversation only exists
    for an `accepted` connection, which is exactly what unlocks the other
    party's full profile via `candidate_info` (see `connection.interface
    .accept()`) — so this is not a second, wider disclosure path, just a
    friendlier read of the same access the acceptance already granted."""
    rows = await communication.list_conversations(session, account_id=account_id)
    responses = []
    for r in rows:
        other_profile = await profile.view_profile(
            session, viewer_account_id=account_id, target_account_id=r.other_account_id
        )
        responses.append(
            ConversationResponse(
                connection_id=str(r.connection_id),
                other_account_id=str(r.other_account_id),
                other_name=other_profile.name if other_profile else None,
                other_photo_url=other_profile.photo_url if other_profile else None,
                last_message_at=r.last_message_at.isoformat() if r.last_message_at else None,
            )
        )
    return responses


class MessageResponse(BaseModel):
    id: str
    sender_account_id: str
    content: str
    sent_at: str


@router.get("/{connection_id}", response_model=list[MessageResponse])
async def list_messages(
    connection_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> list[MessageResponse]:
    """[FR049] A thread's messages — `[]` when nothing has been sent yet."""
    rows = await communication.list_messages(session, connection_id=connection_id)
    return [
        MessageResponse(
            id=str(m.id), sender_account_id=str(m.sender_account_id), content=m.content,
            sent_at=m.sent_at.isoformat(),
        )
        for m in rows
    ]


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
) -> MessageResponse:
    """[FR049/TR049] Send a message — requires an `accepted` connection, no
    prior contact-info exchange."""
    try:
        message_id = await communication.send_message(
            session, sender_account_id=account_id, connection_id=connection_id, content=body.content
        )
    except communication.ConversationNotAvailable as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=translate("messages.error.notAvailable", lang),
        ) from exc
    except communication.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("messages.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    rows = await communication.list_messages(session, connection_id=connection_id)
    sent = next(m for m in rows if m.id == message_id)
    return MessageResponse(
        id=str(sent.id),
        sender_account_id=str(sent.sender_account_id),
        content=sent.content,
        sent_at=sent.sent_at.isoformat(),
    )
