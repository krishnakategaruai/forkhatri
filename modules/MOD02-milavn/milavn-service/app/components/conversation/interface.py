"""Conversation & Moments — beyond-MVP capabilities added in the Step 9 product pass.

Validated behaviours the thesis asks us to copy (§57): Meetup's event chat
and photos, WhatsApp's simple coordination, Strava's "repeated activity
creates identity". Kept the Milavn way:

- An occurrence **thread** is only for the organizer(s) and the people who
  RSVP'd; nobody else can read it, so attendance stays private (FR040).
- **Moments** (photos) can be added only by people who were actually there
  (checked in / attended / organizer) and are visible to the same thread.
- A circle **board** is members-only (FR023).
- Blocked pairs never see each other's messages (FR062).
- This is coordination, not a social feed: no likes, no reactions, no
  threads-of-threads (thesis §3 "not a social-media feed").

Every visibility rule is a definer helper in migration 013, so the API code
here trusts RLS and only adds the block filter and the display names.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.identity_bridge import interface as identity
from app.config.settings import get_settings


class NotAllowed(Exception):
    """The viewer is not part of this thread / circle / was not at the activity."""


class InvalidInput(Exception):
    pass


class UnsupportedMedia(Exception):
    pass


_ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@dataclass(frozen=True, slots=True)
class Message:
    id: UUID
    member_id: UUID
    display_name: str
    avatar: str | None
    body: str
    created_at: datetime
    mine: bool


@dataclass(frozen=True, slots=True)
class Photo:
    id: UUID
    member_id: UUID
    display_name: str
    url: str
    caption: str | None
    created_at: datetime
    mine: bool


# --- Occurrence thread --------------------------------------------------------


async def can_view_thread(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> bool:
    return bool((await session.execute(text("SELECT milavn_activity.can_view_thread(:o, :m)"), {"o": str(occurrence_id), "m": str(member_id)})).scalar_one())


async def was_there(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> bool:
    return bool((await session.execute(text("SELECT milavn_activity.was_there(:o, :m)"), {"o": str(occurrence_id), "m": str(member_id)})).scalar_one())


async def _blocked_filter(session: AsyncSession, viewer: UUID, authors: list[UUID]) -> set[UUID]:
    hidden: set[UUID] = set()
    for a in set(authors):
        if a == viewer:
            continue
        if (await session.execute(text("SELECT milavn_safety.is_blocked_either_way(:a, :b)"), {"a": str(viewer), "b": str(a)})).scalar_one():
            hidden.add(a)
    return hidden


async def list_messages(session: AsyncSession, *, occurrence_id: UUID, viewer_member_id: UUID, limit: int = 200) -> list[Message]:
    if not await can_view_thread(session, occurrence_id=occurrence_id, member_id=viewer_member_id):
        raise NotAllowed()
    rows = (
        await session.execute(
            text(
                "SELECT id, member_id, body, created_at FROM milavn_activity.occurrence_message "
                "WHERE occurrence_id = :o AND deleted_at IS NULL ORDER BY created_at ASC LIMIT :l"
            ),
            {"o": str(occurrence_id), "l": limit},
        )
    ).all()
    hidden = await _blocked_filter(session, viewer_member_id, [r[1] for r in rows])
    names = await identity.display_names_for([r[1] for r in rows])
    return [Message(r[0], r[1], names[r[1]].display_name, names[r[1]].avatar, r[2], r[3], r[1] == viewer_member_id) for r in rows if r[1] not in hidden]


async def post_message(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID, body: str) -> UUID:
    body = (body or "").strip()
    if not body or len(body) > 1000:
        raise InvalidInput()
    if not await can_view_thread(session, occurrence_id=occurrence_id, member_id=member_id):
        raise NotAllowed()
    message_id = uuid4()
    await session.execute(
        text("INSERT INTO milavn_activity.occurrence_message (id, occurrence_id, member_id, body) VALUES (:id, :o, :m, :b)"),
        {"id": str(message_id), "o": str(occurrence_id), "m": str(member_id), "b": body},
    )
    return message_id


async def delete_message(session: AsyncSession, *, message_id: UUID, member_id: UUID) -> None:
    # RLS lets a person retract only their own message.
    await session.execute(
        text("UPDATE milavn_activity.occurrence_message SET deleted_at = now() WHERE id = :id AND member_id = :m"),
        {"id": str(message_id), "m": str(member_id)},
    )


# --- Moments ------------------------------------------------------------------


async def list_photos(session: AsyncSession, *, occurrence_id: UUID, viewer_member_id: UUID) -> list[Photo]:
    if not await can_view_thread(session, occurrence_id=occurrence_id, member_id=viewer_member_id):
        return []
    rows = (
        await session.execute(
            text(
                "SELECT id, member_id, storage_ref, caption, created_at FROM milavn_activity.occurrence_photo "
                "WHERE occurrence_id = :o AND removed_at IS NULL ORDER BY created_at DESC LIMIT 60"
            ),
            {"o": str(occurrence_id)},
        )
    ).all()
    hidden = await _blocked_filter(session, viewer_member_id, [r[1] for r in rows])
    names = await identity.display_names_for([r[1] for r in rows])
    return [Photo(r[0], r[1], names[r[1]].display_name, f"/media/{r[2]}", r[3], r[4], r[1] == viewer_member_id) for r in rows if r[1] not in hidden]


async def add_photo(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID, photo: UploadFile, caption: str | None) -> Photo:
    if not await was_there(session, occurrence_id=occurrence_id, member_id=member_id):
        raise NotAllowed()
    ext = _ALLOWED_IMAGE_TYPES.get(photo.content_type or "")
    if ext is None:
        raise UnsupportedMedia(photo.content_type or "unknown")
    root: Path = get_settings().media_root / "moments"
    root.mkdir(parents=True, exist_ok=True)
    name = f"{occurrence_id}-{uuid4().hex[:8]}{ext}"
    with (root / name).open("wb") as fh:
        shutil.copyfileobj(photo.file, fh)
    ref = f"moments/{name}"
    photo_id = uuid4()
    cap = (caption or "").strip()[:200] or None
    await session.execute(
        text("INSERT INTO milavn_activity.occurrence_photo (id, occurrence_id, member_id, storage_ref, caption) VALUES (:id, :o, :m, :r, :c)"),
        {"id": str(photo_id), "o": str(occurrence_id), "m": str(member_id), "r": ref, "c": cap},
    )
    me = (await identity.display_names_for([member_id]))[member_id]
    return Photo(photo_id, member_id, me.display_name, f"/media/{ref}", cap, datetime.now().astimezone(), True)


async def delete_photo(session: AsyncSession, *, photo_id: UUID, member_id: UUID) -> None:
    await session.execute(text("DELETE FROM milavn_activity.occurrence_photo WHERE id = :id AND member_id = :m"), {"id": str(photo_id), "m": str(member_id)})


# --- Photo privacy (FR113) ------------------------------------------------------


def short_name(full: str) -> str:
    """First name and last initial: enough to recognise someone you just met, no more."""
    parts = full.split()
    return parts[0] if len(parts) < 2 else f"{parts[0]} {parts[-1][0]}."


async def photo_preference(session: AsyncSession, *, member_id: UUID) -> bool:
    row = (await session.execute(text("SELECT prefer_not_pictured FROM milavn_activity.photo_preference WHERE member_id = :m"), {"m": str(member_id)})).first()
    return bool(row and row[0])


async def set_photo_preference(session: AsyncSession, *, member_id: UUID, prefer_not_pictured: bool) -> bool:
    await session.execute(
        text(
            "INSERT INTO milavn_activity.photo_preference (member_id, prefer_not_pictured) VALUES (:m, :p) "
            "ON CONFLICT (member_id) DO UPDATE SET prefer_not_pictured = EXCLUDED.prefer_not_pictured, updated_at = now()"
        ),
        {"m": str(member_id), "p": prefer_not_pictured},
    )
    return prefer_not_pictured


async def photo_opt_outs(session: AsyncSession, *, occurrence_id: UUID, viewer_member_id: UUID) -> list[str]:
    """Names of people who were there and asked not to be in photos — shown before someone who was there shares one."""
    rows = (await session.execute(text("SELECT member_id FROM milavn_activity.photo_opt_outs(:o, :v)"), {"o": str(occurrence_id), "v": str(viewer_member_id)})).all()
    names = await identity.display_names_for([r[0] for r in rows])
    return sorted(short_name(names[r[0]].display_name) for r in rows)


async def request_photo_removal(session: AsyncSession, *, occurrence_id: UUID, photo_id: UUID, member_id: UUID) -> bool:
    """Take a photo down at once (consent to take is not consent to publish). The uploader is told, never who asked."""
    uploader = (await session.execute(text("SELECT milavn_activity.request_photo_removal(:p, :m)"), {"p": str(photo_id), "m": str(member_id)})).scalar_one_or_none()
    if uploader is None:
        return False
    if uploader != member_id:
        from app.events import bus

        await bus.publish(
            session,
            schema="milavn_activity",
            event_type="photo.removed",
            aggregate_id=occurrence_id,
            payload={"occurrence_id": occurrence_id, "uploader_member_id": uploader},
        )
    return True


# --- Circle board -------------------------------------------------------------


async def list_posts(session: AsyncSession, *, circle_id: UUID, viewer_member_id: UUID, limit: int = 100) -> list[Message]:
    # RLS returns nothing for non-members; the route turns "not a member" into an empty board.
    rows = (
        await session.execute(
            text("SELECT id, member_id, body, created_at FROM milavn_circle.circle_post WHERE circle_id = :c AND deleted_at IS NULL ORDER BY created_at DESC LIMIT :l"),
            {"c": str(circle_id), "l": limit},
        )
    ).all()
    hidden = await _blocked_filter(session, viewer_member_id, [r[1] for r in rows])
    names = await identity.display_names_for([r[1] for r in rows])
    return [Message(r[0], r[1], names[r[1]].display_name, names[r[1]].avatar, r[2], r[3], r[1] == viewer_member_id) for r in rows if r[1] not in hidden]


async def post_to_board(session: AsyncSession, *, circle_id: UUID, member_id: UUID, body: str) -> UUID:
    body = (body or "").strip()
    if not body or len(body) > 1000:
        raise InvalidInput()
    is_member = (
        await session.execute(
            text("SELECT milavn_circle.is_active_member(:c, :m) OR milavn_circle.is_circle_creator(:c, :m)"),
            {"c": str(circle_id), "m": str(member_id)},
        )
    ).scalar_one()
    if not is_member:
        raise NotAllowed()
    post_id = uuid4()
    await session.execute(
        text("INSERT INTO milavn_circle.circle_post (id, circle_id, member_id, body) VALUES (:id, :c, :m, :b)"),
        {"id": str(post_id), "c": str(circle_id), "m": str(member_id), "b": body},
    )
    return post_id


# --- Circle-mates going -------------------------------------------------------


async def circle_peers(session: AsyncSession, *, occurrence_id: UUID, viewer_member_id: UUID) -> list[dict]:
    """People from the viewer's own circles who are going. They already share a circle with the
    viewer, so naming them reveals nothing the circle's member list does not (FR040 stays intact)."""
    rows = (await session.execute(text("SELECT milavn_activity.circle_peer_ids(:o, :m)"), {"o": str(occurrence_id), "m": str(viewer_member_id)})).all()
    ids = [r[0] for r in rows]
    hidden = await _blocked_filter(session, viewer_member_id, ids)
    names = await identity.display_names_for(ids)
    return [{"member_id": str(i), "display_name": names[i].display_name, "avatar": names[i].avatar} for i in ids if i not in hidden]
