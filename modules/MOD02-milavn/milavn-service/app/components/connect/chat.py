"""Messaging — 1:1 and group chats, reactions, presence and live expressions
(owner decision 2026-09-14; DESIGN-DIRECTION-2030.md §6).

Trust-scoped by construction: `milavn_connect.can_message(a, b)` (a shared
circle or a shared activity, and no block either way) gates every
conversation, and all creation goes through the definer helper
`create_conversation` so the rule cannot be bypassed. Messages are read and
written under RLS. Expressions are ephemeral presence (never a video frame:
the camera is analysed on the device and only a word like "smile" leaves it).

The in-process hub fans out events to WebSocket subscribers of a conversation.
One process today; a broker replaces `Hub` when there are several.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.identity_bridge import interface as identity
from app.config.settings import get_settings

EXPRESSIONS = ("smile", "laugh", "surprised", "wink", "thinking", "love", "neutral")
REACTIONS = ("👍", "❤️", "😂", "🔥", "👏", "😮")
_ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class NotAllowed(Exception):
    pass


class NotFound(Exception):
    pass


class InvalidInput(Exception):
    pass


# --- hub (WebSocket fan-out) --------------------------------------------------


class Hub:
    def __init__(self) -> None:
        self._subs: dict[UUID, set[asyncio.Queue]] = {}
        self._member_subs: dict[UUID, set[asyncio.Queue]] = {}
        self._present: dict[UUID, dict[UUID, int]] = {}  # conversation -> member -> open sockets

    def subscribe(self, conversation_id: UUID | None, member_id: UUID) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        if conversation_id is not None:
            self._subs.setdefault(conversation_id, set()).add(q)
            room = self._present.setdefault(conversation_id, {})
            room[member_id] = room.get(member_id, 0) + 1
        self._member_subs.setdefault(member_id, set()).add(q)
        return q

    def unsubscribe(self, conversation_id: UUID | None, member_id: UUID, q: asyncio.Queue) -> None:
        if conversation_id is not None:
            self._subs.get(conversation_id, set()).discard(q)
            room = self._present.get(conversation_id, {})
            if room.get(member_id, 0) <= 1:
                room.pop(member_id, None)
            else:
                room[member_id] -= 1
        self._member_subs.get(member_id, set()).discard(q)

    def present_in(self, conversation_id: UUID) -> set[UUID]:
        """Who has this conversation open right now — "here" in the room (Snapchat's Friends in Chat).
        Distinct from the app-wide heartbeat, which only says someone used Milavn in the last two minutes."""
        return set(self._present.get(conversation_id, {}))

    def publish(self, conversation_id: UUID, event: dict) -> None:
        for q in list(self._subs.get(conversation_id, ())):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def publish_to_members(self, member_ids: list[UUID], event: dict) -> None:
        for m in member_ids:
            for q in list(self._member_subs.get(m, ())):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass


hub = Hub()


# --- models -----------------------------------------------------------------------


@dataclass(slots=True)
class Person:
    member_id: UUID
    display_name: str
    avatar: str | None
    active: bool = False
    expression: str | None = None
    last_seen_at: datetime | None = None


@dataclass(slots=True)
class SharedContext:
    """Why two people can talk (FR096): the next activity they share, else a shared circle. Approximate place only."""

    kind: str  # 'activity' | 'circle'
    title: str
    ref: str  # activity slug or circle id
    starts_at: datetime | None
    locality: str | None


@dataclass(slots=True)
class Conversation:
    id: UUID
    kind: str
    title: str | None
    members: list[Person]
    last_message_at: datetime | None
    last_preview: str | None
    unread: int
    context: SharedContext | None = None


@dataclass(slots=True)
class Message:
    id: UUID
    conversation_id: UUID
    member_id: UUID
    display_name: str
    avatar: str | None
    kind: str
    body: str | None
    media_url: str | None
    expression: str | None
    created_at: datetime
    mine: bool
    reactions: dict[str, list[UUID]] = field(default_factory=dict)


Presence = tuple[bool, str | None, datetime | None]  # active, expression, last_seen_at


async def _person_rows(ids: list[UUID], presence: dict[UUID, Presence]) -> list[Person]:
    names = await identity.display_names_for(ids)
    return [Person(i, names[i].display_name, names[i].avatar, *(presence.get(i, (False, None, None)))) for i in ids]


async def presence_of(session: AsyncSession, ids: list[UUID]) -> dict[UUID, Presence]:
    if not ids:
        return {}
    rows = (
        await session.execute(
            text("SELECT member_id, active, expression, last_seen_at FROM milavn_connect.presence_of(CAST(:ids AS uuid[]))"), {"ids": [str(i) for i in ids]}
        )
    ).all()
    return {r[0]: (bool(r[1]), r[2], r[3]) for r in rows}


async def shared_context(session: AsyncSession, *, me: UUID, other: UUID) -> SharedContext | None:
    row = (
        await session.execute(text("SELECT kind, title, ref, starts_at, locality FROM milavn_connect.shared_context(:me, :other)"), {"me": str(me), "other": str(other)})
    ).first()
    return SharedContext(*row) if row else None


async def can_message(session: AsyncSession, a: UUID, b: UUID) -> bool:
    return bool((await session.execute(text("SELECT milavn_connect.can_message(:a, :b)"), {"a": str(a), "b": str(b)})).scalar_one())


async def is_member(session: AsyncSession, conversation_id: UUID, member_id: UUID) -> bool:
    return bool((await session.execute(text("SELECT milavn_connect.is_conversation_member(:c, :m)"), {"c": str(conversation_id), "m": str(member_id)})).scalar_one())


async def member_ids(session: AsyncSession, conversation_id: UUID) -> list[UUID]:
    rows = (
        await session.execute(
            text("SELECT member_id FROM milavn_connect.conversation_member WHERE conversation_id = :c AND left_at IS NULL"), {"c": str(conversation_id)}
        )
    ).all()
    return [r[0] for r in rows]


# --- conversations ---------------------------------------------------------------


async def open_direct(session: AsyncSession, *, me: UUID, other: UUID) -> UUID:
    if not await can_message(session, me, other):
        raise NotAllowed()
    return (
        await session.execute(text("SELECT milavn_connect.create_conversation('direct', NULL, :me, CAST(:members AS uuid[]))"), {"me": str(me), "members": [str(other)]})
    ).scalar_one()


async def create_group(session: AsyncSession, *, me: UUID, title: str, others: list[UUID]) -> UUID:
    title = (title or "").strip()
    if not title or not others:
        raise InvalidInput()
    for o in others:
        if not await can_message(session, me, o):
            raise NotAllowed()
    return (
        await session.execute(
            text("SELECT milavn_connect.create_conversation('group', :t, :me, CAST(:members AS uuid[]))"),
            {"t": title[:80], "me": str(me), "members": [str(o) for o in others]},
        )
    ).scalar_one()


async def list_conversations(session: AsyncSession, *, me: UUID) -> list[Conversation]:
    rows = (
        await session.execute(
            text(
                "SELECT c.id, c.kind, c.title, c.last_message_at FROM milavn_connect.conversation c "
                "JOIN milavn_connect.conversation_member cm ON cm.conversation_id = c.id AND cm.member_id = :me AND cm.left_at IS NULL "
                "ORDER BY c.last_message_at DESC NULLS LAST, c.created_at DESC LIMIT 100"
            ),
            {"me": str(me)},
        )
    ).all()
    out: list[Conversation] = []
    for cid, kind, title, last_at in rows:
        ids = await member_ids(session, cid)
        others = [i for i in ids if i != me] or ids
        pres = await presence_of(session, others)
        prev = (
            await session.execute(
                text("SELECT kind, body, expression FROM milavn_connect.chat_message WHERE conversation_id = :c AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 1"),
                {"c": str(cid)},
            )
        ).first()
        preview = None
        if prev:
            preview = prev[1] if prev[0] == "text" else ("📷" if prev[0] == "photo" else f"· {prev[2]}")
        unread = int((await session.execute(text("SELECT milavn_connect.unread_count(:c, :m)"), {"c": str(cid), "m": str(me)})).scalar_one() or 0)
        out.append(Conversation(cid, kind, title, await _person_rows(others, pres), last_at, preview, unread))
    return out


async def conversation(session: AsyncSession, *, conversation_id: UUID, me: UUID) -> Conversation:
    row = (await session.execute(text("SELECT id, kind, title, last_message_at FROM milavn_connect.conversation WHERE id = :c"), {"c": str(conversation_id)})).first()
    if row is None:
        raise NotFound()
    ids = await member_ids(session, conversation_id)
    pres = await presence_of(session, ids)
    others = [i for i in ids if i != me]
    context = await shared_context(session, me=me, other=others[0]) if row[1] == "direct" and others else None
    return Conversation(row[0], row[1], row[2], await _person_rows(ids, pres), row[3], None, 0, context)


# --- messages ------------------------------------------------------------------------


def _msg(r, names, me: UUID) -> Message:  # noqa: ANN001
    ident = names[r[2]]
    return Message(r[0], r[1], r[2], ident.display_name, ident.avatar, r[3], r[4], (f"/media/{r[5]}" if r[5] else None), r[6], r[7], r[2] == me)


async def messages(session: AsyncSession, *, conversation_id: UUID, me: UUID, after: datetime | None = None, limit: int = 200) -> list[Message]:
    if not await is_member(session, conversation_id, me):
        raise NotAllowed()
    rows = (
        await session.execute(
            text(
                "SELECT id, conversation_id, member_id, kind, body, media_ref, expression, created_at FROM milavn_connect.chat_message "
                "WHERE conversation_id = :c AND deleted_at IS NULL AND (CAST(:after AS timestamptz) IS NULL OR created_at > CAST(:after AS timestamptz)) "
                "ORDER BY created_at ASC LIMIT :l"
            ),
            {"c": str(conversation_id), "after": after, "l": limit},
        )
    ).all()
    names = await identity.display_names_for([r[2] for r in rows])
    out = [_msg(r, names, me) for r in rows]
    if out:
        rx = (
            await session.execute(
                text("SELECT message_id, emoji, member_id FROM milavn_connect.message_reaction WHERE message_id = ANY(CAST(:ids AS uuid[]))"),
                {"ids": [str(m.id) for m in out]},
            )
        ).all()
        by_id = {m.id: m for m in out}
        for mid, emoji, member in rx:
            by_id[mid].reactions.setdefault(emoji, []).append(member)
    return out


async def send(session: AsyncSession, *, conversation_id: UUID, me: UUID, kind: str, body: str | None, expression: str | None, media_ref: str | None = None) -> Message:
    if kind not in ("text", "photo", "expression"):
        raise InvalidInput()
    if kind == "text" and not (body or "").strip():
        raise InvalidInput()
    if kind == "expression" and expression not in EXPRESSIONS:
        raise InvalidInput()
    if not await is_member(session, conversation_id, me):
        raise NotAllowed()
    mid = uuid4()
    await session.execute(
        text("INSERT INTO milavn_connect.chat_message (id, conversation_id, member_id, kind, body, media_ref, expression) VALUES (:id, :c, :m, :k, :b, :r, :e)"),
        {"id": str(mid), "c": str(conversation_id), "m": str(me), "k": kind, "b": (body or "").strip()[:2000] or None, "r": media_ref, "e": expression},
    )
    await session.execute(text("SELECT milavn_connect.touch_conversation(:c)"), {"c": str(conversation_id)})
    ident = (await identity.display_names_for([me]))[me]
    return Message(
        mid,
        conversation_id,
        me,
        ident.display_name,
        ident.avatar,
        kind,
        (body or "").strip() or None,
        (f"/media/{media_ref}" if media_ref else None),
        expression,
        datetime.now().astimezone(),
        True,
    )


async def store_photo(conversation_id: UUID, photo: UploadFile) -> str:
    ext = _ALLOWED_IMAGE_TYPES.get(photo.content_type or "")
    if ext is None:
        raise InvalidInput()
    root: Path = get_settings().media_root / "chat"
    root.mkdir(parents=True, exist_ok=True)
    name = f"{conversation_id}-{uuid4().hex[:8]}{ext}"
    with (root / name).open("wb") as fh:
        shutil.copyfileobj(photo.file, fh)
    return f"chat/{name}"


async def retract(session: AsyncSession, *, message_id: UUID, me: UUID) -> None:
    await session.execute(text("UPDATE milavn_connect.chat_message SET deleted_at = now() WHERE id = :id AND member_id = :m"), {"id": str(message_id), "m": str(me)})


async def toggle_reaction(session: AsyncSession, *, message_id: UUID, me: UUID, emoji: str) -> bool:
    """Returns True when the reaction is now present, False when removed."""
    if emoji not in REACTIONS:
        raise InvalidInput()
    existing = (
        await session.execute(
            text("SELECT 1 FROM milavn_connect.message_reaction WHERE message_id = :id AND member_id = :m AND emoji = :e"),
            {"id": str(message_id), "m": str(me), "e": emoji},
        )
    ).first()
    if existing:
        await session.execute(
            text("DELETE FROM milavn_connect.message_reaction WHERE message_id = :id AND member_id = :m AND emoji = :e"),
            {"id": str(message_id), "m": str(me), "e": emoji},
        )
        return False
    await session.execute(
        text("INSERT INTO milavn_connect.message_reaction (message_id, member_id, emoji) VALUES (:id, :m, :e) ON CONFLICT DO NOTHING"),
        {"id": str(message_id), "m": str(me), "e": emoji},
    )
    return True


async def mark_read(session: AsyncSession, *, conversation_id: UUID, me: UUID) -> None:
    await session.execute(
        text("UPDATE milavn_connect.conversation_member SET last_read_at = now() WHERE conversation_id = :c AND member_id = :m"),
        {"c": str(conversation_id), "m": str(me)},
    )


async def heartbeat(session: AsyncSession, *, me: UUID, expression: str | None, at_occurrence_id: UUID | None) -> None:
    if expression is not None and expression not in EXPRESSIONS:
        expression = None
    await session.execute(text("SELECT milavn_connect.heartbeat(:m, :e, :o)"), {"m": str(me), "e": expression, "o": str(at_occurrence_id) if at_occurrence_id else None})


async def total_unread(session: AsyncSession, *, me: UUID) -> int:
    rows = (await session.execute(text("SELECT conversation_id FROM milavn_connect.conversation_member WHERE member_id = :m AND left_at IS NULL"), {"m": str(me)})).all()
    total = 0
    for (cid,) in rows:
        total += int((await session.execute(text("SELECT milavn_connect.unread_count(:c, :m)"), {"c": str(cid), "m": str(me)})).scalar_one() or 0)
    return total
