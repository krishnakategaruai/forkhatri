"""Communication — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach Communication state.

Implements:
  * FR049 / TR049 — private in-platform messaging, available immediately on
    an accepted connection, with zero prior contact-info exchange required.
  * FR050 / DEC-V1-014 / DEC-V1-021 — no permanent chat history: a lazy
    30-day purge on every read, and (candidate kind only) either person can
    end the session, which clears the thread for both.
  * DEC-V1-024 (rework contract §2, migration 035) — two conversation KINDS
    on one accepted connection:
      - `candidate`: the two candidates only, opened on acceptance;
      - `family`: both candidates plus every active member of both Home
        Circles, opened when either candidate chooses "Involve my family".
    Family members are only ever in `family` conversations. Both kinds carry
    a roster (`conversation_participant`) with per-person `last_read_at`,
    from which `unread_count` is computed, and a `last_message` preview.

Security findings this module implements as code:
  * SP049 — rate limit on sends.
  * SP051 (Critical) — no application-level read path to `message.content`
    beyond a participant of that conversation; RLS decides.

Deliberate exception to the "never a live cross-schema query" preference:
`list_conversations()` joins `conversation` against
`mangaly_connection.connection_request` in one query — RLS is enforced by
Postgres on both tables regardless of which component issued the query.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Final
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.communication.models import Conversation, ConversationParticipant, Message
from app.components.connection.models import ConnectionStatus
from app.config.settings import get_settings
from app.events import bus
from app.rate_limiting import limiter

__all__ = [
    "KINDS",
    "SYSTEM_CONNECTED",
    "SYSTEM_FAMILY_OPENED",
    "ConversationNotAvailable",
    "ConversationSummary",
    "MessageSummary",
    "Person",
    "RateLimited",
    "close_conversation",
    "list_conversations",
    "list_messages",
    "mark_read",
    "open_conversation_on_accept",
    "open_family_conversation",
    "send_message",
    "direct_contacts",
    "open_direct",
    "can_direct",
    "list_direct_conversations",
    "Contact",
    "people",
    "report_conversation",
    "SESSION_IDLE",
    "unread_total",
]

# System lines are keys, not prose: rendered in the reader's own language.
SYSTEM_CONNECTED = "system.connected"
SYSTEM_FAMILY_OPENED = "system.family_opened"

# [Migration 046] `direct`: an ordinary, kept one-to-one chat between two
# people (owner: "general chat for individual account like Instagram / FB").
# A direct thread is addressed by its conversation id, not a connection id.
KINDS: Final[tuple[str, ...]] = ("candidate", "family", "direct")

# [DEC-V1-024] The candidates' chat is a session. Leaving the thread ends it
# (the web client calls close), and as a backstop a session with nothing
# written for this long is over: its messages are deleted on the next read,
# so a tab that died without saying goodbye never leaves a history behind.
SESSION_IDLE: Final[timedelta] = timedelta(minutes=30)


class ConversationNotAvailable(Exception):
    """[FR049 failure outcome] The connection does not exist / is not visible,
    is not `accepted`, the thread of that kind is not open, or the caller is
    not a participant of it."""


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
    sender_name: str | None = None
    sender_role: str | None = None
    # [Migration 044] Exact relation ("mother") and whose side the sender is on.
    sender_relation: str | None = None
    sender_side_account_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class Person:
    """One participant: a candidate, or a circle member with their relation."""

    account_id: UUID
    display_name: str | None
    role: str
    photo_ref: str | None
    last_read_at: datetime | None
    relation: str | None = None
    side_account_id: UUID | None = None
    side_name: str | None = None


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    conversation_id: UUID
    connection_id: UUID
    kind: str
    other_account_id: UUID
    last_message_at: datetime | None
    last_message: MessageSummary | None
    unread_count: int
    participants: list[Person] = field(default_factory=list)


def _check_kind(kind: str) -> str:
    if kind not in KINDS:
        raise ConversationNotAvailable
    return kind


async def _find_conversation_id(
    session: AsyncSession, *, connection_id: UUID, kind: str = "candidate"
) -> UUID | None:
    return (
        await session.execute(
            select(Conversation.id).where(
                Conversation.connection_id == connection_id, Conversation.kind == kind
            )
        )
    ).scalar_one_or_none()


async def _is_participant(session: AsyncSession, *, conversation_id: UUID, account_id: UUID) -> bool:
    row = (
        await session.execute(
            select(ConversationParticipant.id).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    return row is not None


async def _thread_for(
    session: AsyncSession, *, connection_id: UUID, kind: str, account_id: UUID
) -> UUID:
    """The conversation id of `kind` on this connection, if the caller may use it.

    `candidate`: the caller must be one of the two candidates (the subject —
    never a family member who pressed send — or the target). `family`: the
    thread must already be open and the caller on its roster."""
    from app.components.connection import interface as connection_module

    if kind == "direct":
        # `connection_id` carries the direct conversation's own id here.
        row = (
            await session.execute(
                text(
                    "SELECT id FROM mangaly_communication.conversation "
                    "WHERE id = :id AND kind = 'direct'"
                ),
                {"id": connection_id},
            )
        ).scalar_one_or_none()
        if row is None or not await _is_participant(
            session, conversation_id=row, account_id=account_id
        ):
            raise ConversationNotAvailable
        return row

    if kind == "candidate":
        conn = await connection_module.get_request(session, connection_id=connection_id)
        if conn is None or conn.status is not ConnectionStatus.ACCEPTED:
            raise ConversationNotAvailable
        if account_id not in (conn.subject_account_id, conn.target_account_id):
            raise ConversationNotAvailable
        return await _get_or_create_candidate_conversation(session, connection_id=connection_id)

    # Family: the roster is the authority. A parent or relative cannot see
    # the connection row under RLS, but a participant can see the thread.

    conversation_id = await _find_conversation_id(session, connection_id=connection_id, kind="family")
    if conversation_id is None:
        raise ConversationNotAvailable
    if not await _is_participant(session, conversation_id=conversation_id, account_id=account_id):
        raise ConversationNotAvailable
    return conversation_id


async def _get_or_create_candidate_conversation(session: AsyncSession, *, connection_id: UUID) -> UUID:
    existing = await _find_conversation_id(session, connection_id=connection_id, kind="candidate")
    if existing is not None:
        return existing
    conversation_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO mangaly_communication.conversation (id, connection_id, kind) "
            "VALUES (:id, :connection_id, 'candidate') ON CONFLICT (connection_id, kind) DO NOTHING"
        ),
        {"id": conversation_id, "connection_id": connection_id},
    )
    resolved = await _find_conversation_id(session, connection_id=connection_id, kind="candidate")
    assert resolved is not None  # the INSERT above guarantees a row exists now
    await session.execute(
        text("SELECT mangaly_communication.ensure_participants(:id)"), {"id": resolved}
    )
    return resolved


async def send_message(
    session: AsyncSession,
    *,
    sender_account_id: UUID,
    connection_id: UUID,
    content: str,
    kind: str = "candidate",
) -> UUID:
    """[FR049/TR049] Send a message into the `kind` thread of an accepted
    connection. A candidate thread admits the two candidates; a family thread
    admits its roster."""
    _check_kind(kind)
    conversation_id = await _thread_for(
        session, connection_id=connection_id, kind=kind, account_id=sender_account_id
    )
    if kind == "direct":
        others = [
            p.account_id
            for p in await _people(session, conversation_id=conversation_id)
            if p.account_id != sender_account_id
        ]
        if not others or not await can_direct(session, other_account_id=others[0]):
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
    # [DEC-V1-028/SP064] Bounded text detection rides the same transaction:
    # a hit opens an automated report and its case atomically with the send.
    from app.components.safety import interface as safety

    await safety.scan_message(
        session,
        message_id=message_id,
        conversation_id=conversation_id,
        sender_account_id=sender_account_id,
        content=content,
    )
    # Sending is reading: the sender has seen everything up to now.
    await _touch_read(session, conversation_id=conversation_id, account_id=sender_account_id)
    await bus.publish(
        session,
        schema="mangaly_communication",
        aggregate_id=message_id,
        event_type="MessageSent",
        payload={
            "message_id": str(message_id),
            "conversation_id": str(conversation_id),
            "connection_id": str(connection_id),
            "kind": kind,
            "sender_account_id": str(sender_account_id),
        },
    )
    return message_id


async def _touch_read(session: AsyncSession, *, conversation_id: UUID, account_id: UUID) -> None:
    await session.execute(
        text(
            "UPDATE mangaly_communication.conversation_participant SET last_read_at = now() "
            "WHERE conversation_id = :conversation_id AND account_id = :account_id"
        ),
        {"conversation_id": conversation_id, "account_id": account_id},
    )


async def _people(session: AsyncSession, *, conversation_id: UUID) -> list[Person]:
    rows = (
        await session.execute(
            text("SELECT * FROM mangaly_communication.conversation_people(:id)"),
            {"id": conversation_id},
        )
    ).mappings().all()
    # [Migration 047] A parent or relative has a member photo, not profile photos.
    from app.components.profile import interface as profile_module

    extra = await profile_module.member_photo_refs(
        session, account_ids=[r["account_id"] for r in rows if not r["photo_ref"]]
    )
    rows = [
        {**r, "photo_ref": r["photo_ref"] or extra.get(r["account_id"])} for r in rows
    ]
    return [
        Person(
            account_id=r["account_id"],
            display_name=r["display_name"],
            role=r["role"],
            photo_ref=r["photo_ref"],
            last_read_at=r["last_read_at"],
            relation=r["relation"],
            side_account_id=r["side_account_id"],
            side_name=r["side_name"],
        )
        for r in rows
    ]


async def list_messages(
    session: AsyncSession,
    *,
    connection_id: UUID,
    account_id: UUID,
    kind: str = "candidate",
) -> list[MessageSummary]:
    """[FR049/FR050] Every message in this thread still inside the retention
    window — `[]` when the candidate thread has nothing yet. Opening a thread
    marks it read for the caller.

    [DEC-V1-014] Purges this conversation's own aged-out rows before reading
    (see the module docstring). The DELETE only ever touches THIS
    conversation — never a table-wide sweep from a read path."""
    _check_kind(kind)
    try:
        conversation_id = await _thread_for(
            session, connection_id=connection_id, kind=kind, account_id=account_id
        )
    except ConversationNotAvailable:
        if kind == "candidate":
            raise
        raise

    if kind == "candidate":
        # The session backstop, then the retention window (DEC-V1-014).
        await _expire_idle_session(session, conversation_id=conversation_id)
        cutoff = datetime.now(UTC) - timedelta(days=get_settings().message_retention_days)
        await session.execute(
            text(
                "DELETE FROM mangaly_communication.message "
                "WHERE conversation_id = :conversation_id AND sent_at < :cutoff"
            ),
            {"conversation_id": conversation_id, "cutoff": cutoff},
        )
    # [DEC-V1-024] The families' conversation is kept: owner, "parent chat is
    # always a normal chat, completely monitored". It lives as long as the
    # connection does and goes with it (connection end / account erasure).

    rows = (
        await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at)
        )
    ).scalars()
    people = {p.account_id: p for p in await _people(session, conversation_id=conversation_id)}
    await _touch_read(session, conversation_id=conversation_id, account_id=account_id)
    return [
        MessageSummary(
            id=m.id,
            sender_account_id=m.sender_account_id,
            content=m.content,
            kind=m.kind,
            sent_at=m.sent_at,
            sender_name=(p.display_name if (p := people.get(m.sender_account_id)) else None),
            sender_role=(p.role if (p := people.get(m.sender_account_id)) else None),
            sender_relation=(p.relation if (p := people.get(m.sender_account_id)) else None),
            sender_side_account_id=(
                p.side_account_id if (p := people.get(m.sender_account_id)) else None
            ),
        )
        for m in rows
    ]


async def _expire_idle_session(session: AsyncSession, *, conversation_id: UUID) -> None:
    """Delete what the two wrote if nothing has been written for SESSION_IDLE."""
    await session.execute(
        text(
            "DELETE FROM mangaly_communication.message m "
            "WHERE m.conversation_id = :id AND m.kind = 'member' "
            "AND NOT EXISTS (SELECT 1 FROM mangaly_communication.message n "
            "  WHERE n.conversation_id = :id AND n.kind = 'member' AND n.sent_at > :since)"
        ),
        {"id": conversation_id, "since": datetime.now(UTC) - SESSION_IDLE},
    )


async def people(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID, kind: str = "candidate"
) -> list[Person]:
    """Who is in this thread, with relation and side, for its header."""
    _check_kind(kind)
    conversation_id = await _thread_for(
        session, connection_id=connection_id, kind=kind, account_id=account_id
    )
    return await _people(session, conversation_id=conversation_id)


async def report_conversation(
    session: AsyncSession,
    *,
    connection_id: UUID,
    account_id: UUID,
    kind: str,
    reported_account_id: UUID,
    reason: str,
    details: str | None,
) -> UUID:
    """[DEC-V1-024] Report someone from inside a thread. The thread as it
    stands is stored with the report (migration 044): the candidates' chat is
    deleted when its session ends, so evidence is taken now or never."""
    _check_kind(kind)
    conversation_id = await _thread_for(
        session, connection_id=connection_id, kind=kind, account_id=account_id
    )
    report_id = (
        await session.execute(
            text("SELECT mangaly_safety.report_conversation(:c, :r, :cat, :d)"),
            {"c": conversation_id, "r": reported_account_id, "cat": reason, "d": details},
        )
    ).scalar_one_or_none()
    if report_id is None:
        raise ConversationNotAvailable
    await bus.publish(
        session,
        schema="mangaly_safety",
        aggregate_id=report_id,
        event_type="ReportSubmitted",
        payload={
            "report_id": str(report_id),
            "reporter_account_id": str(account_id),
            "reported_account_id": str(reported_account_id),
            "category": reason,
            "conversation_id": str(conversation_id),
        },
    )
    # Classified at once, like every other report, so it reaches the queue.
    from app.components.safety import interface as safety
    from app.config import safety_taxonomy

    await safety.classify_and_escalate(
        session,
        report_id=report_id,
        classification=safety_taxonomy.classify_report_reason(reason),
        category=reason,
        reported_account_id=reported_account_id,
        conversation_id=conversation_id,
    )
    return report_id


async def mark_read(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID, kind: str = "candidate"
) -> None:
    _check_kind(kind)
    conversation_id = await _thread_for(
        session, connection_id=connection_id, kind=kind, account_id=account_id
    )
    await _touch_read(session, conversation_id=conversation_id, account_id=account_id)


async def open_conversation_on_accept(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> None:
    """[FR044/FR049, migrations 026/037] Acceptance opens the candidate
    conversation with one system line. `account_id` is the accepting
    CANDIDATE; a circle member accepting for them (`?for_candidate=`) passes
    the candidate's id, which the function admits under `family_info`."""
    await session.execute(
        text("SELECT mangaly_communication.open_conversation(:connection_id, :account_id, :key)"),
        {"connection_id": connection_id, "account_id": account_id, "key": SYSTEM_CONNECTED},
    )


async def open_family_conversation(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> UUID:
    """[DEC-V1-024] Either candidate opens the family thread ("Involve my
    family"): both candidates and every active member of both circles are on
    the roster from this moment; members who join a circle later are added
    when anyone next lists. Re-opening is harmless. Both sides' circles are
    told (`family_conversation_opened`), except the opener."""
    from app.components.connection import interface as connection_module

    # [Migration 044] A candidate, or a parent/guardian of either candidate,
    # may open it. A parent cannot see the connection row itself under RLS,
    # so the SECURITY DEFINER function checks the connection is accepted and
    # the caller's place, and returns NULL otherwise.

    conversation_id = (
        await session.execute(
            text(
                "SELECT mangaly_communication.open_family_conversation("
                ":connection_id, :account_id, :key)"
            ),
            {"connection_id": connection_id, "account_id": account_id, "key": SYSTEM_FAMILY_OPENED},
        )
    ).scalar_one_or_none()
    if conversation_id is None:
        raise ConversationNotAvailable

    await bus.publish(
        session,
        schema="mangaly_communication",
        aggregate_id=conversation_id,
        event_type="FamilyConversationOpened",
        payload={
            "conversation_id": str(conversation_id),
            "connection_id": str(connection_id),
            "opened_by_account_id": str(account_id),
        },
    )
    from app.components.notification_bridge import interface as notifications

    people_now = await _people(session, conversation_id=conversation_id)
    pair = tuple(p.account_id for p in people_now if p.role == "candidate")
    if len(pair) != 2:
        return conversation_id
    for candidate in pair:
        await notifications.notify_circle(
            session,
            candidate_account_id=candidate,
            kind="family_conversation_opened",
            payload={
                "connection_id": connection_id,
                "opened_by_account_id": account_id,
                "other_account_id": pair[1] if candidate == pair[0] else pair[0],
            },
            link=f"/messages/{connection_id}?kind=family",
            exclude=account_id,
        )
    return conversation_id


async def close_conversation(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> None:
    """[FR050/DEC-V1-021] Either candidate ending the session ends it for both:
    every message they wrote to each other is deleted, immediately, and the
    thread reopens empty. Candidate kind only — a family thread persists for
    the retention window like any group chat (contract: "family persists 30
    days")."""
    conversation_id = await _thread_for(
        session, connection_id=connection_id, kind="candidate", account_id=account_id
    )
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


_LIST_SQL = text(
    """
    SELECT cv.id AS conversation_id,
           cv.connection_id,
           cv.kind,
           CASE WHEN cr.subject_account_id = :ctx THEN cr.target_profile_id
                ELSE cr.subject_account_id END AS other_account_id,
           lm.id AS last_id, lm.sender_account_id AS last_sender, lm.content AS last_content,
           lm.kind AS last_kind, lm.sent_at AS last_sent_at,
           (SELECT count(*) FROM mangaly_communication.message m
             WHERE m.conversation_id = cv.id
               AND m.kind = 'member'
               AND m.sender_account_id IS DISTINCT FROM :me
               AND m.sent_at > COALESCE(
                     (SELECT p.last_read_at FROM mangaly_communication.conversation_participant p
                       WHERE p.conversation_id = cv.id AND p.account_id = :me),
                     '-infinity'::timestamptz)) AS unread_count
      FROM mangaly_communication.conversation cv
      -- [Migration 046] Through a narrow definer read, so a parent on a
      -- families' conversation sees it listed (RLS keeps connection rows
      -- from them).
      JOIN mangaly_communication.thread_connections() cr ON cr.id = cv.connection_id
      LEFT JOIN LATERAL (
            SELECT m.id, m.sender_account_id, m.content, m.kind, m.sent_at
              FROM mangaly_communication.message m
             WHERE m.conversation_id = cv.id
             ORDER BY m.sent_at DESC LIMIT 1
      ) lm ON true
     WHERE cr.status = 'accepted'
       AND (
            (:ctx = :me AND (
                 (cv.kind = 'candidate' AND :me IN (cr.subject_account_id, cr.target_profile_id))
              OR (cv.kind = 'family' AND mangaly_communication.is_participant(cv.id))))
         OR (:ctx <> :me AND cv.kind = 'family'
             AND :ctx IN (cr.subject_account_id, cr.target_profile_id)
             AND mangaly_communication.is_participant(cv.id))
       )
     ORDER BY lm.sent_at DESC NULLS LAST, cv.created_at DESC
    """
)


async def list_conversations(
    session: AsyncSession,
    *,
    account_id: UUID,
    context_account_id: UUID | None = None,
    hidden: set[UUID] | None = None,
) -> list[ConversationSummary]:
    """[FR049] Every conversation the caller may open in this context, most
    recently active first (UX21: pure recency, no ranking).

    Self context: the caller's own candidate threads plus every family thread
    they are on. Family context (`?for_candidate=`): the family threads of
    that candidate's connections the caller is on — late-joining members are
    synced onto the roster first (migration 037). `hidden` removes threads
    with a blocked person on the other side."""
    ctx = context_account_id or account_id
    await session.execute(
        text("SELECT mangaly_communication.sync_family_participants_for(:ctx)"), {"ctx": ctx}
    )
    # The session backstop for every candidate thread of the caller, so a
    # preview never shows words from a session that is already over.
    await session.execute(
        text(
            "DELETE FROM mangaly_communication.message m "
            "USING mangaly_communication.conversation cv, mangaly_connection.connection_request cr "
            "WHERE m.conversation_id = cv.id AND cr.id = cv.connection_id "
            "AND cv.kind = 'candidate' AND m.kind = 'member' "
            "AND :me IN (cr.subject_account_id, cr.target_profile_id) "
            "AND NOT EXISTS (SELECT 1 FROM mangaly_communication.message n "
            "  WHERE n.conversation_id = cv.id AND n.kind = 'member' AND n.sent_at > :since)"
        ),
        {"me": account_id, "since": datetime.now(UTC) - SESSION_IDLE},
    )
    rows = (await session.execute(_LIST_SQL, {"me": account_id, "ctx": ctx})).mappings().all()
    hide = hidden or set()
    result: list[ConversationSummary] = []
    for r in rows:
        if r["other_account_id"] in hide:
            continue
        people = await _people(session, conversation_id=r["conversation_id"])
        if not people:
            # A candidate thread opened on acceptance has no roster until
            # someone first opens it, so the list showed a nameless row.
            # Fill the roster here (idempotent; a no-op for non-parties).
            await session.execute(
                text("SELECT mangaly_communication.ensure_participants(:id)"),
                {"id": r["conversation_id"]},
            )
            people = await _people(session, conversation_id=r["conversation_id"])
        last = None
        if r["last_id"] is not None:
            sender = next((p for p in people if p.account_id == r["last_sender"]), None)
            last = MessageSummary(
                id=r["last_id"],
                sender_account_id=r["last_sender"],
                content=r["last_content"],
                kind=r["last_kind"],
                sent_at=r["last_sent_at"],
                sender_name=sender.display_name if sender else None,
                sender_role=sender.role if sender else None,
            )
        result.append(
            ConversationSummary(
                conversation_id=r["conversation_id"],
                connection_id=r["connection_id"],
                kind=r["kind"],
                other_account_id=r["other_account_id"],
                last_message_at=r["last_sent_at"],
                last_message=last,
                unread_count=int(r["unread_count"] or 0),
                participants=people,
            )
        )
    return result


async def unread_total(session: AsyncSession, *, account_id: UUID) -> int:
    """Unread member messages across every thread the caller can actually open.

    [2026-09-21] The `accepted` join is the point. Without it this counted
    messages in conversations whose connection is no longer live (declined,
    withdrawn), while `list_conversations` filters those threads out — so the
    navigation badge claimed unread messages that the Messages screen could
    not show, and the count never cleared because there was nothing left to
    open. The badge and the list must be answering the same question."""
    return (
        await session.execute(
            text(
                """
                SELECT count(*)
                  FROM mangaly_communication.message m
                  JOIN mangaly_communication.conversation_participant p
                    ON p.conversation_id = m.conversation_id AND p.account_id = :me
                  JOIN mangaly_communication.conversation cv
                    ON cv.id = m.conversation_id
                  JOIN mangaly_connection.connection_request cr
                    ON cr.id = cv.connection_id
                 WHERE cr.status = 'accepted'
                   AND m.kind = 'member'
                   AND m.sender_account_id IS DISTINCT FROM :me
                   AND m.sent_at > COALESCE(p.last_read_at, '-infinity'::timestamptz)
                """
            ),
            {"me": account_id},
        )
    ).scalar_one()



# ---------------------------------------------------------------------------
# [Migration 046 / DEC-V1-026] One-to-one chat
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Contact:
    """Someone the caller may message directly, and how they are linked."""

    account_id: UUID
    display_name: str | None
    photo_ref: str | None
    role: str
    relation: str | None
    side_account_id: UUID | None
    side_name: str | None
    mine: bool


async def direct_contacts(session: AsyncSession) -> list[Contact]:
    """Everyone the caller may message: their own family, and the other
    family of each accepted connection. Never the connected candidate (that
    is the incognito session) and never anyone blocked."""
    rows = (
        await session.execute(text("SELECT * FROM mangaly_communication.direct_contacts()"))
    ).mappings().all()
    from app.components.profile import interface as profile_module

    extra = await profile_module.member_photo_refs(
        session, account_ids=[r["account_id"] for r in rows if not r["photo_ref"]]
    )
    rows = [{**r, "photo_ref": r["photo_ref"] or extra.get(r["account_id"])} for r in rows]
    return [
        Contact(
            account_id=r["account_id"],
            display_name=r["display_name"],
            photo_ref=r["photo_ref"],
            role=r["role"],
            relation=r["relation"],
            side_account_id=r["side_account_id"],
            side_name=r["side_name"],
            mine=bool(r["mine"]),
        )
        for r in rows
    ]


async def open_direct(session: AsyncSession, *, other_account_id: UUID) -> UUID:
    """The one direct thread with this person, created on first use."""
    conversation_id = (
        await session.execute(
            text("SELECT mangaly_communication.open_direct(:o)"), {"o": other_account_id}
        )
    ).scalar_one_or_none()
    if conversation_id is None:
        raise ConversationNotAvailable
    return conversation_id


async def can_direct(session: AsyncSession, *, other_account_id: UUID) -> bool:
    return bool(
        (
            await session.execute(
                text("SELECT mangaly_communication.can_direct(:o)"), {"o": other_account_id}
            )
        ).scalar_one()
    )


_DIRECT_LIST_SQL = text(
    """
    SELECT cv.id AS conversation_id,
           other.account_id AS other_account_id,
           lm.id AS last_id, lm.sender_account_id AS last_sender, lm.content AS last_content,
           lm.kind AS last_kind, lm.sent_at AS last_sent_at,
           (SELECT count(*) FROM mangaly_communication.message m
             WHERE m.conversation_id = cv.id AND m.kind = 'member'
               AND m.sender_account_id IS DISTINCT FROM :me
               AND m.sent_at > COALESCE(mine.last_read_at, '-infinity'::timestamptz)) AS unread_count
      FROM mangaly_communication.conversation cv
      JOIN mangaly_communication.conversation_participant mine
        ON mine.conversation_id = cv.id AND mine.account_id = :me
      JOIN mangaly_communication.conversation_participant other
        ON other.conversation_id = cv.id AND other.account_id <> :me
      LEFT JOIN LATERAL (
            SELECT m.id, m.sender_account_id, m.content, m.kind, m.sent_at
              FROM mangaly_communication.message m
             WHERE m.conversation_id = cv.id
             ORDER BY m.sent_at DESC LIMIT 1
      ) lm ON true
     WHERE cv.kind = 'direct'
       AND lm.id IS NOT NULL
    """
)


async def list_direct_conversations(
    session: AsyncSession, *, account_id: UUID, hidden: set[UUID] | None = None
) -> list[ConversationSummary]:
    """The caller's direct threads that have at least one message, like any
    messenger's inbox (an opened-but-empty thread is not listed)."""
    rows = (await session.execute(_DIRECT_LIST_SQL, {"me": account_id})).mappings().all()
    hide = hidden or set()
    out: list[ConversationSummary] = []
    for r in rows:
        if r["other_account_id"] in hide:
            continue
        people = await _people(session, conversation_id=r["conversation_id"])
        sender = next((p for p in people if p.account_id == r["last_sender"]), None)
        out.append(
            ConversationSummary(
                conversation_id=r["conversation_id"],
                connection_id=r["conversation_id"],
                kind="direct",
                other_account_id=r["other_account_id"],
                last_message_at=r["last_sent_at"],
                last_message=MessageSummary(
                    id=r["last_id"],
                    sender_account_id=r["last_sender"],
                    content=r["last_content"],
                    kind=r["last_kind"],
                    sent_at=r["last_sent_at"],
                    sender_name=sender.display_name if sender else None,
                    sender_role=sender.role if sender else None,
                ),
                unread_count=int(r["unread_count"] or 0),
                participants=people,
            )
        )
    return out
