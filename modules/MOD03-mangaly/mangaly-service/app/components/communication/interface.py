"""Communication — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach Communication state.

Implements:
  * FR049 / TR049 — private in-platform messaging, available immediately on
    an accepted connection, with zero prior contact-info exchange required.
  * FR050 / DEC-V1-014 — no permanent, conventional chat history. `settings
    .message_retention_days` (default 30, an explicitly documented
    placeholder — FR050's own Confidence note leaves the exact window open
    pending legal/technical design) is enforced as a lazy purge: every
    `list_messages()` call first deletes that conversation's own rows older
    than the window, so a message is genuinely gone from storage, not
    merely hidden from a query, the first time anyone opens the thread
    after it ages out. No separate scheduled job exists yet — a
    little-used conversation could in principle retain slightly-stale
    messages until next opened, an accepted gap given FR050 itself defers
    the exact mechanism to a later technical/legal design pass.

Security findings this module implements as code:
  * SP049 — no rate limit is named in TR049's own text; Step 8 flagged
    messaging as "the highest-value abuse surface in the module," so one is
    applied here anyway.
  * SP051 (Critical) — `message.content`'s only application-level read path
    is its own sender; this module adds no second one. The RLS policy's own
    safety-case-investigation clause is a database-level concern this code
    does not need to (and must not) duplicate or work around.

Deliberate exception to the "never a live cross-schema query" preference
this codebase otherwise follows (`discovery`'s own header comment):
`list_conversations()` joins `mangaly_communication.conversation` directly
against `mangaly_connection.connection_request` in one query. Reconstructing
the same answer through `connection.interface`'s own functions would mean
listing every sent AND incoming connection and then checking each one for a
conversation individually — many more round trips for what is fundamentally
one read. RLS is enforced by Postgres on both tables regardless of which
component's code issued the query, so this does not weaken any authorization
boundary; it only reads two tables' worth of pre-existing rows differently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.communication.models import Conversation, Message
from app.components.connection.models import ConnectionStatus
from app.config.settings import get_settings
from app.events import bus
from app.rate_limiting import limiter

__all__ = [
    "SYSTEM_CONNECTED",
    "ConversationNotAvailable",
    "ConversationSummary",
    "MessageSummary",
    "RateLimited",
    "list_conversations",
    "close_conversation",
    "list_messages",
    "open_conversation_on_accept",
    "send_message",
]

# The system line added when a connection is accepted. A key, not prose: the
# thread renders it in whichever language the reader is using.
SYSTEM_CONNECTED = "system.connected"


class ConversationNotAvailable(Exception):
    """[FR049 failure outcome] Either the connection does not exist/is not
    visible to this caller, or it is not `accepted` yet — messaging is
    blocked pending acceptance, never pending a separate contact-info
    exchange (FR049's own explicit non-requirement)."""


class RateLimited(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(f"retry after {retry_after_seconds}s")
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True, slots=True)
class MessageSummary:
    """`kind` is "member" for something a person wrote, or "system" for a line
    the platform added (migration 026), which has no sender and whose
    `content` is a key the reader's own language is rendered from."""

    id: UUID
    sender_account_id: UUID | None
    content: str
    kind: str
    sent_at: datetime


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    connection_id: UUID
    other_account_id: UUID
    last_message_at: datetime | None


async def _find_conversation_id(session: AsyncSession, *, connection_id: UUID) -> UUID | None:
    return (
        await session.execute(
            select(Conversation.id).where(Conversation.connection_id == connection_id)
        )
    ).scalar_one_or_none()


async def _get_or_create_conversation(session: AsyncSession, *, connection_id: UUID) -> UUID:
    existing = await _find_conversation_id(session, connection_id=connection_id)
    if existing is not None:
        return existing

    conversation_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO mangaly_communication.conversation (id, connection_id) "
            "VALUES (:id, :connection_id) ON CONFLICT (connection_id) DO NOTHING"
        ),
        {"id": conversation_id, "connection_id": connection_id},
    )
    # A concurrent sender may have won the race — re-read rather than assume.
    resolved = await _find_conversation_id(session, connection_id=connection_id)
    assert resolved is not None  # the INSERT above guarantees a row exists now
    return resolved


async def send_message(
    session: AsyncSession, *, sender_account_id: UUID, connection_id: UUID, content: str
) -> UUID:
    """[FR049/TR049] Send a message. Creates the conversation row on first
    use (see this module's own docstring for why that is not done at
    connection-accept time instead)."""
    from app.components.connection import interface as connection_module

    conn = await connection_module.get_request(session, connection_id=connection_id)
    if conn is None or conn.status is not ConnectionStatus.ACCEPTED:
        raise ConversationNotAvailable
    # [2026-09-17] The subject, not whoever pressed send: a family member who sent
    # the request for the candidate is not a party to their private conversation.
    if sender_account_id not in (conn.subject_account_id, conn.target_account_id):
        raise ConversationNotAvailable

    settings = get_settings()
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.MESSAGE_SEND,
            subject=str(sender_account_id),
            limit_max=settings.rate_limit_message_send_max_per_hour,
            window_seconds=3600,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    conversation_id = await _get_or_create_conversation(session, connection_id=connection_id)

    message_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO mangaly_communication.message "
            "(id, conversation_id, sender_account_id, content) "
            "VALUES (:id, :conversation_id, :sender, :content)"
        ),
        {
            "id": message_id,
            "conversation_id": conversation_id,
            "sender": sender_account_id,
            "content": content,
        },
    )
    await bus.publish(
        session,
        schema="mangaly_communication",
        aggregate_id=message_id,
        event_type="MessageSent",
        payload={
            "message_id": str(message_id),
            "conversation_id": str(conversation_id),
            "connection_id": str(connection_id),
            "sender_account_id": str(sender_account_id),
        },
    )
    return message_id


async def list_messages(session: AsyncSession, *, connection_id: UUID) -> list[MessageSummary]:
    """[FR049/FR050] Every message in this connection's thread still inside
    the retention window — `[]` (not an error) when no conversation exists
    yet, since "no messages sent yet" is a normal state, not a failure.

    [DEC-V1-014] Purges this conversation's own aged-out rows before
    reading, every time the thread is opened — see this module's own
    docstring for why a lazy purge rather than a scheduled job. The DELETE
    only ever touches rows in THIS conversation (never a table-wide sweep
    from a read path), so this stays a cheap, indexed, single-conversation
    operation regardless of how many other conversations exist.
    """
    conversation_id = await _find_conversation_id(session, connection_id=connection_id)
    if conversation_id is None:
        return []

    cutoff = datetime.now(UTC) - timedelta(days=get_settings().message_retention_days)
    await session.execute(
        text(
            "DELETE FROM mangaly_communication.message "
            "WHERE conversation_id = :conversation_id AND sent_at < :cutoff"
        ),
        {"conversation_id": conversation_id, "cutoff": cutoff},
    )

    rows = (
        await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at)
        )
    ).scalars()
    return [
        MessageSummary(
            id=m.id,
            sender_account_id=m.sender_account_id,
            content=m.content,
            kind=m.kind,
            sent_at=m.sent_at,
        )
        for m in rows
    ]


async def open_conversation_on_accept(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> None:
    """[FR044/FR049, migration 026] Acceptance opens the private conversation
    and puts one system line in it, so both people — the candidate above all —
    learn the request succeeded in the place they will actually talk, instead
    of having to notice a status word on another screen. Called by
    `connection.interface.accept()`; doing nothing when the caller is not a
    party is the function's own decision, not this caller's."""
    await session.execute(
        text("SELECT mangaly_communication.open_conversation(:connection_id, :account_id, :key)"),
        {"connection_id": connection_id, "account_id": account_id, "key": SYSTEM_CONNECTED},
    )


async def close_conversation(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> None:
    """[FR050/DEC-V1-021] Either person ending the session ends it for both:
    every message they wrote to each other is deleted, immediately, and the
    thread reopens empty. The conversation itself stays (the connection is
    still accepted) with its system line, so the two can start again.

    This is the product owner's "session based and no memory" rule, and it is
    the only retention promise this app can actually keep. What it does NOT do
    is stop the other person capturing the screen first: a browser cannot
    prevent a screenshot, a screen recording or a second phone pointed at the
    display, and the thread says so rather than implying a protection that
    does not exist."""
    from app.components.connection import interface as connection_module

    conn = await connection_module.get_request(session, connection_id=connection_id)
    if conn is None or conn.status is not ConnectionStatus.ACCEPTED:
        raise ConversationNotAvailable
    if account_id not in (conn.subject_account_id, conn.target_account_id):
        raise ConversationNotAvailable

    conversation_id = await _find_conversation_id(session, connection_id=connection_id)
    if conversation_id is None:
        return

    await session.execute(
        text(
            "DELETE FROM mangaly_communication.message "
            "WHERE conversation_id = :conversation_id AND kind = 'member'"
        ),
        {"conversation_id": conversation_id},
    )
    await bus.publish(
        session,
        schema="mangaly_communication",
        aggregate_id=conversation_id,
        event_type="ConversationSessionEnded",
        payload={
            "conversation_id": str(conversation_id),
            "connection_id": str(connection_id),
            "ended_by_account_id": str(account_id),
        },
    )


async def list_conversations(
    session: AsyncSession, *, account_id: UUID
) -> list[ConversationSummary]:
    """[FR049] Every conversation the caller is a party to, most-recently-
    active first — UX21's own "no seriousness/exclusivity ranking, pure
    recency" ordering rule."""
    rows = await session.execute(
        text(
            """
            SELECT
                cr.id AS connection_id,
                CASE WHEN cr.subject_account_id = :account_id
                     THEN cr.target_profile_id ELSE cr.subject_account_id END AS other_account_id,
                (SELECT max(m.sent_at) FROM mangaly_communication.message m
                 WHERE m.conversation_id = c.id) AS last_message_at
            FROM mangaly_connection.connection_request cr
            JOIN mangaly_communication.conversation c ON c.connection_id = cr.id
            WHERE cr.status = 'accepted'
              AND (cr.subject_account_id = :account_id OR cr.target_profile_id = :account_id)
            ORDER BY last_message_at DESC NULLS LAST
            """
        ),
        {"account_id": account_id},
    )
    return [
        ConversationSummary(
            connection_id=row.connection_id,
            other_account_id=row.other_account_id,
            last_message_at=row.last_message_at,
        )
        for row in rows
    ]
