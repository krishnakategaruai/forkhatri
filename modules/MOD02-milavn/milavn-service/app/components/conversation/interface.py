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

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import media_files
from app.components.identity_bridge import interface as identity


class NotAllowed(Exception):
    """The viewer is not part of this thread / circle / was not at the activity."""


class InvalidInput(Exception):
    pass


class UnsupportedMedia(Exception):
    """kind: 'photo' (not a JPEG/PNG/WebP) or 'document' (not an office file / PDF / text)."""

    def __init__(self, kind: str = "photo") -> None:
        super().__init__(kind)
        self.kind = kind


TooLarge = media_files.TooLarge  # re-exported: the routes map it to 413


# Circle posts may carry a document: agendas, checklists, schedules. Office formats and PDF only.
_ALLOWED_DOC_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",
}
MAX_DOC_BYTES = media_files.MAX_DOC_BYTES


@dataclass(frozen=True, slots=True)
class Message:
    id: UUID
    member_id: UUID
    display_name: str
    avatar: str | None
    body: str
    created_at: datetime
    mine: bool
    photo_url: str | None = None
    doc_url: str | None = None
    doc_name: str | None = None


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
    # [B4/B7] What the file IS, not what the browser called it; capped while streaming.
    try:
        ext = media_files.sniff_image(photo)
    except media_files.NotAnImage as exc:
        raise UnsupportedMedia("photo") from exc
    ref = media_files.store(photo, "moments", str(occurrence_id), ext, media_files.MAX_PHOTO_BYTES)
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
            text("SELECT id, member_id, body, created_at, photo_ref, doc_ref, doc_name FROM milavn_circle.circle_post WHERE circle_id = :c AND deleted_at IS NULL ORDER BY created_at DESC LIMIT :l"),
            {"c": str(circle_id), "l": limit},
        )
    ).all()
    hidden = await _blocked_filter(session, viewer_member_id, [r[1] for r in rows])
    names = await identity.display_names_for([r[1] for r in rows])
    return [
        Message(
            r[0], r[1], names[r[1]].display_name, names[r[1]].avatar, r[2], r[3], r[1] == viewer_member_id,
            f"/media/{r[4]}" if r[4] else None, f"/media/{r[5]}" if r[5] else None, r[6],
        )
        for r in rows
        if r[1] not in hidden
    ]


class PostNotFound(Exception):
    pass


async def delete_post(session: AsyncSession, *, circle_id: UUID, post_id: UUID, member_id: UUID) -> None:
    """[B8] The author takes their post back; the circle's organizer or an assistant can take down
    anyone's post (as Facebook / WhatsApp group admins can). Definer function, migration 043.
    [B5] The post's photo and document leave the disk with it."""
    row = (
        await session.execute(
            text("SELECT r_outcome, r_photo_ref, r_doc_ref FROM milavn_circle.delete_circle_post(:c, :p, :m)"),
            {"c": str(circle_id), "p": str(post_id), "m": str(member_id)},
        )
    ).first()
    outcome = row[0] if row else "not_found"
    if outcome == "not_found":
        raise PostNotFound
    if outcome != "deleted":
        raise NotAllowed
    media_files.remove(row[1], row[2])


class OrganizersOnly(NotAllowed):
    """A member, but this is an announcement-style circle where only the organizers post."""


async def check_may_post(session: AsyncSession, circle_id: UUID, member_id: UUID) -> None:
    """Raises NotAllowed (not a member) or OrganizersOnly (posting policy). Shared by board posts
    and polls [B2]: a poll is a post, so an announcement-only circle refuses members' polls too."""
    if await _may_post(session, circle_id, member_id):
        return
    member = (
        await session.execute(text("SELECT milavn_circle.is_active_member(:c, :m)"), {"c": str(circle_id), "m": str(member_id)})
    ).scalar_one()
    raise OrganizersOnly() if member else NotAllowed()


async def _may_post(session: AsyncSession, circle_id: UUID, member_id: UUID) -> bool:
    """Membership, then the circle's posting policy: an announcement-style circle
    ('organizers') accepts posts only from its organizer or an assistant."""
    is_member = (
        await session.execute(
            text("SELECT milavn_circle.is_active_member(:c, :m) OR milavn_circle.is_circle_creator(:c, :m)"),
            {"c": str(circle_id), "m": str(member_id)},
        )
    ).scalar_one()
    if not is_member:
        return False
    row = (
        await session.execute(
            text(
                "SELECT c.posting_policy, m.member_role::text FROM milavn_circle.circle c "
                "LEFT JOIN milavn_circle.circle_membership m ON m.circle_id = c.id AND m.member_id = :m AND m.left_at IS NULL "
                "WHERE c.id = :c"
            ),
            {"c": str(circle_id), "m": str(member_id)},
        )
    ).first()
    if row is None:
        return False
    policy, role = row[0] or "members", row[1]
    return policy != "organizers" or role in ("organizer", "assistant")


async def post_to_board(
    session: AsyncSession, *, circle_id: UUID, member_id: UUID, body: str, photo: UploadFile | None = None, document: UploadFile | None = None
) -> UUID:
    body = (body or "").strip()
    if (not body and photo is None and document is None) or len(body) > 1000:
        raise InvalidInput()
    await check_may_post(session, circle_id, member_id)
    # [B6] Both attachments are validated before either is stored, so a bad document never leaves
    # an orphaned photo on disk (and vice versa).
    photo_ext = doc_ext = None
    if photo is not None:
        try:
            photo_ext = media_files.sniff_image(photo)
        except media_files.NotAnImage as exc:
            raise UnsupportedMedia("photo") from exc
        media_files.check_size(photo, media_files.MAX_PHOTO_BYTES)  # [B7] 10 MB
    if document is not None:
        doc_ext = _ALLOWED_DOC_TYPES.get(document.content_type or "")
        if doc_ext is None:
            raise UnsupportedMedia("document")
        media_files.check_size(document, MAX_DOC_BYTES)
    photo_ref = doc_ref = doc_name = None
    try:
        if photo is not None:
            photo_ref = media_files.store(photo, "circle-posts", str(circle_id), photo_ext, media_files.MAX_PHOTO_BYTES)
        if document is not None:
            doc_ref = media_files.store(document, "circle-docs", str(circle_id), doc_ext, MAX_DOC_BYTES)
            doc_name = Path(document.filename or f"document{doc_ext}").name[:120]
    except BaseException:
        media_files.remove(photo_ref, doc_ref)
        raise
    post_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO milavn_circle.circle_post (id, circle_id, member_id, body, photo_ref, doc_ref, doc_name) "
            "VALUES (:id, :c, :m, :b, :p, :d, :dn)"
        ),
        {"id": str(post_id), "c": str(circle_id), "m": str(member_id), "b": body, "p": photo_ref, "d": doc_ref, "dn": doc_name},
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
