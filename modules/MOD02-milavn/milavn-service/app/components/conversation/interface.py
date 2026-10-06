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


# Circle posts carry photos and files (agendas, checklists, schedules). [053] Which file types, how
# many and how large come from configuration (settings.circle_*); see attachment_limits().


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
    # [049] Circle board only: announcement / pin, reactions (emoji -> member ids) and comments.
    is_announcement: bool = False
    pinned: bool = False
    reactions: dict | None = None
    comments: tuple = ()
    # [053] Every photo and file on the post (older posts: their single photo / document).
    photos: tuple = ()
    docs: tuple = ()  # ({"url", "name", "size"}, ...)


@dataclass(frozen=True, slots=True)
class Comment:
    id: UUID
    member_id: UUID
    display_name: str
    avatar: str | None
    body: str
    created_at: datetime
    mine: bool


# [049] "Reactions, not likes" (milavn-social-decisions): a small fixed set, same as migration 049's CHECK.
POST_REACTIONS = ("❤️", "👏", "😂", "🙏", "🎉")
MAX_PINS = 3
MAX_COMMENT_LEN = 500


def board_order_key(pinned_at: datetime | None, created_at: datetime) -> tuple:
    """Pinned posts first (most recently pinned on top), then everything else newest first."""
    if pinned_at is not None:
        return (0, -pinned_at.timestamp())
    return (1, -created_at.timestamp())


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
    # [049] Pinned posts always come back (even when older than the newest `limit`), and first.
    rows = (
        await session.execute(
            text(
                "SELECT id, member_id, body, created_at, photo_ref, doc_ref, doc_name, is_announcement, pinned_at FROM milavn_circle.circle_post "
                "WHERE circle_id = :c AND deleted_at IS NULL "
                "ORDER BY (pinned_at IS NOT NULL) DESC, created_at DESC LIMIT :l"
            ),
            {"c": str(circle_id), "l": limit},
        )
    ).all()
    rows = sorted(rows, key=lambda r: board_order_key(r[8], r[3]))
    post_ids = [str(r[0]) for r in rows]
    reactions: dict[UUID, dict[str, list[str]]] = {}
    media: dict[UUID, list[tuple]] = {}
    comment_rows: list = []
    if post_ids:
        for pid, emoji, who in (
            await session.execute(
                text("SELECT post_id, emoji, member_id FROM milavn_circle.circle_post_reaction WHERE post_id = ANY(CAST(:ids AS uuid[])) ORDER BY created_at"),
                {"ids": post_ids},
            )
        ).all():
            reactions.setdefault(pid, {}).setdefault(emoji, []).append(str(who))
        for pid, kind, ref, fname, size in (
            await session.execute(
                text(
                    "SELECT post_id, kind, storage_ref, file_name, byte_size FROM milavn_circle.circle_post_media "
                    "WHERE post_id = ANY(CAST(:ids AS uuid[])) ORDER BY post_id, position"
                ),
                {"ids": post_ids},
            )
        ).all():
            media.setdefault(pid, []).append((kind, ref, fname, size))
        comment_rows = (
            await session.execute(
                text(
                    "SELECT id, post_id, member_id, body, created_at FROM milavn_circle.circle_post_comment "
                    "WHERE post_id = ANY(CAST(:ids AS uuid[])) AND deleted_at IS NULL ORDER BY created_at"
                ),
                {"ids": post_ids},
            )
        ).all()
    people = [r[1] for r in rows] + [c[2] for c in comment_rows]
    hidden = await _blocked_filter(session, viewer_member_id, people)
    names = await identity.display_names_for(people)
    comments: dict[UUID, list[Comment]] = {}
    for c in comment_rows:
        if c[2] in hidden:
            continue
        comments.setdefault(c[1], []).append(Comment(c[0], c[2], names[c[2]].display_name, names[c[2]].avatar, c[3], c[4], c[2] == viewer_member_id))
    out: list[Message] = []
    for r in rows:
        if r[1] in hidden:
            continue
        photos = ([f"/media/{r[4]}"] if r[4] else []) + [f"/media/{m[1]}" for m in media.get(r[0], []) if m[0] == "photo"]
        docs = ([{"url": f"/media/{r[5]}", "name": r[6], "size": None}] if r[5] else []) + [
            {"url": f"/media/{m[1]}", "name": m[2], "size": m[3]} for m in media.get(r[0], []) if m[0] == "doc"
        ]
        out.append(
            Message(
                r[0], r[1], names[r[1]].display_name, names[r[1]].avatar, r[2], r[3], r[1] == viewer_member_id,
                photos[0] if photos else None, docs[0]["url"] if docs else None, docs[0]["name"] if docs else None,
                bool(r[7]), r[8] is not None, reactions.get(r[0], {}), tuple(comments.get(r[0], [])),
                tuple(photos), tuple(docs),
            )
        )
    return out


class PinLimit(Exception):
    """[049] Already three pinned posts: unpin one first."""


class AnnouncementNoReplies(Exception):
    """[049] Members react to an announcement; they do not reply to it."""


class CommentNotFound(Exception):
    pass


async def pin_post(session: AsyncSession, *, circle_id: UUID, post_id: UUID, member_id: UUID, pinned: bool) -> None:
    outcome = (
        await session.execute(
            text("SELECT milavn_circle.pin_circle_post(:c, :p, :m, :pin)"),
            {"c": str(circle_id), "p": str(post_id), "m": str(member_id), "pin": pinned},
        )
    ).scalar_one()
    if outcome == "not_found":
        raise PostNotFound
    if outcome == "limit":
        raise PinLimit
    if outcome not in ("pinned", "unpinned"):
        raise NotAllowed


async def toggle_post_reaction(session: AsyncSession, *, circle_id: UUID, post_id: UUID, member_id: UUID, emoji: str) -> bool:
    """True when the reaction is now on, False when it was taken back."""
    if emoji not in POST_REACTIONS:
        raise InvalidInput()
    outcome = (
        await session.execute(
            text("SELECT milavn_circle.toggle_post_reaction(:c, :p, :m, :e)"),
            {"c": str(circle_id), "p": str(post_id), "m": str(member_id), "e": emoji},
        )
    ).scalar_one()
    if outcome == "not_found":
        raise PostNotFound
    if outcome not in ("added", "removed"):
        raise NotAllowed
    return outcome == "added"


async def add_comment(session: AsyncSession, *, circle_id: UUID, post_id: UUID, member_id: UUID, body: str) -> UUID:
    body = (body or "").strip()
    if not body or len(body) > MAX_COMMENT_LEN:
        raise InvalidInput()
    row = (
        await session.execute(
            text("SELECT r_outcome, r_comment_id FROM milavn_circle.add_post_comment(:c, :p, :m, :b)"),
            {"c": str(circle_id), "p": str(post_id), "m": str(member_id), "b": body},
        )
    ).first()
    outcome = row[0] if row else "not_found"
    if outcome == "not_found":
        raise PostNotFound
    if outcome == "announcement":
        raise AnnouncementNoReplies
    if outcome != "added":
        raise NotAllowed
    return row[1]


async def delete_comment(session: AsyncSession, *, circle_id: UUID, comment_id: UUID, member_id: UUID) -> None:
    outcome = (
        await session.execute(
            text("SELECT milavn_circle.delete_post_comment(:c, :x, :m)"),
            {"c": str(circle_id), "x": str(comment_id), "m": str(member_id)},
        )
    ).scalar_one()
    if outcome == "not_found":
        raise CommentNotFound
    if outcome != "deleted":
        raise NotAllowed


class PostNotFound(Exception):
    pass


async def delete_post(session: AsyncSession, *, circle_id: UUID, post_id: UUID, member_id: UUID) -> None:
    """[B8] The author takes their post back; the circle's organizer or an assistant can take down
    anyone's post (as Facebook / WhatsApp group admins can). Definer function, migration 043.
    [B5] The post's photo and document leave the disk with it. [053] So do its extra attachments
    (read first, while the post is still live and visible to the actor)."""
    extra = (
        await session.execute(
            text("SELECT storage_ref FROM milavn_circle.circle_post_media WHERE post_id = :p AND circle_id = :c"),
            {"p": str(post_id), "c": str(circle_id)},
        )
    ).scalars().all()
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
    media_files.remove(row[1], row[2], *extra)


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


async def _is_manager(session: AsyncSession, circle_id: UUID, member_id: UUID) -> bool:
    role = (await session.execute(text("SELECT milavn_circle.current_role_of(:c, :m)"), {"c": str(circle_id), "m": str(member_id)})).scalar_one_or_none()
    return role in ("organizer", "assistant")


class TooMany(Exception):
    """[053] More photos or files than one post may carry (circle_post_max_photos / _files)."""

    def __init__(self, kind: str, limit: int) -> None:
        super().__init__(kind)
        self.kind = kind
        self.limit = limit


def attachment_limits() -> dict:
    """[053] What one circle post may carry, from configuration — the composer shows the same."""
    from app.config.settings import get_settings

    st = get_settings()
    return {
        "max_photos": st.circle_post_max_photos,
        "max_files": st.circle_post_max_files,
        "photo_mb": st.circle_photo_max_mb,
        "file_mb": st.circle_file_max_mb,
        "file_types": [t.lower().lstrip(".") for t in st.circle_file_types],
        "album_max_per_upload": st.circle_album_max_photos_per_upload,
    }


async def post_to_board(
    session: AsyncSession,
    *,
    circle_id: UUID,
    member_id: UUID,
    body: str,
    photos: list[UploadFile] | None = None,
    documents: list[UploadFile] | None = None,
    announcement: bool = False,
) -> UUID:
    """A post: words, and/or several photos and files ([053] limits and types from configuration).
    Every attachment is checked before any is stored, so a bad one never leaves the others behind."""
    photos = [p for p in (photos or []) if p is not None]
    documents = [d for d in (documents or []) if d is not None]
    body = (body or "").strip()
    if (not body and not photos and not documents) or len(body) > 1000:
        raise InvalidInput()
    limits = attachment_limits()
    if len(photos) > limits["max_photos"]:
        raise TooMany("photo", limits["max_photos"])
    if len(documents) > limits["max_files"]:
        raise TooMany("document", limits["max_files"])
    await check_may_post(session, circle_id, member_id)
    # [049] Announcements are the organizer's / an assistant's voice only.
    if announcement and not await _is_manager(session, circle_id, member_id):
        raise OrganizersOnly()
    photo_max = limits["photo_mb"] * media_files.MB
    file_max = limits["file_mb"] * media_files.MB
    checked: list[tuple[str, UploadFile, str, int]] = []  # (kind, upload, ext, cap)
    for p in photos:
        try:
            ext = media_files.sniff_image(p)
        except media_files.NotAnImage as exc:
            raise UnsupportedMedia("photo") from exc
        media_files.check_size(p, photo_max)
        checked.append(("photo", p, ext, photo_max))
    for d in documents:
        try:
            ext = media_files.sniff_document(d, limits["file_types"])
        except media_files.NotADocument as exc:
            raise UnsupportedMedia("document") from exc
        media_files.check_size(d, file_max)
        checked.append(("doc", d, ext, file_max))
    stored: list[tuple[str, str, str | None, int]] = []  # (kind, ref, name, size)
    try:
        for kind, up, ext, cap in checked:
            folder = "circle-posts" if kind == "photo" else "circle-docs"
            ref = media_files.store(up, folder, str(circle_id), ext, cap)
            name = Path(up.filename or f"document{ext}").name[:120] if kind == "doc" else None
            stored.append((kind, ref, name, media_files.upload_size(up)))
    except BaseException:
        media_files.remove(*[x[1] for x in stored])
        raise
    post_id = uuid4()
    try:
        await session.execute(
            text(
                "INSERT INTO milavn_circle.circle_post (id, circle_id, member_id, body, is_announcement, attachment_count) "
                "VALUES (:id, :c, :m, :b, :a, :n)"
            ),
            {"id": str(post_id), "c": str(circle_id), "m": str(member_id), "b": body, "a": announcement, "n": len(stored)},
        )
        for i, (kind, ref, name, size) in enumerate(stored):
            await session.execute(
                text(
                    "INSERT INTO milavn_circle.circle_post_media (post_id, circle_id, kind, storage_ref, file_name, byte_size, position) "
                    "VALUES (:p, :c, :k, :r, :n, :s, :i)"
                ),
                {"p": str(post_id), "c": str(circle_id), "k": kind, "r": ref, "n": name, "s": size, "i": i},
            )
    except BaseException:
        media_files.remove(*[x[1] for x in stored])
        raise
    from app.events import bus

    if announcement:
        # [049] An announcement goes to the top of Posts: it takes a pin, releasing the oldest pins
        # when all three are in use. Then every member is told, in their own language.
        pins = (
            await session.execute(
                text("SELECT id FROM milavn_circle.circle_post WHERE circle_id = :c AND pinned_at IS NOT NULL AND deleted_at IS NULL ORDER BY pinned_at ASC"),
                {"c": str(circle_id)},
            )
        ).scalars().all()
        for old in pins_to_release(len(pins), pins):
            await pin_post(session, circle_id=circle_id, post_id=old, member_id=member_id, pinned=False)
        await pin_post(session, circle_id=circle_id, post_id=post_id, member_id=member_id, pinned=True)
        await bus.publish(
            session,
            schema="milavn_circle",
            event_type="circle.announcement_posted",
            aggregate_id=circle_id,
            payload={"circle_id": circle_id, "post_id": post_id, "member_id": member_id},
        )
    else:
        # [053] An ordinary post: members whose setting for this circle is "all" hear about it, grouped.
        await bus.publish(
            session,
            schema="milavn_circle",
            event_type="circle.post_created",
            aggregate_id=circle_id,
            payload={"circle_id": circle_id, "post_id": post_id, "member_id": member_id},
        )
    return post_id


def pins_to_release(count: int, oldest_first: list) -> list:
    """[049] Which existing pins a new announcement pushes out so at most MAX_PINS stay pinned."""
    return list(oldest_first[: max(0, count - (MAX_PINS - 1))])


# --- Circle-mates going -------------------------------------------------------


async def circle_peers(session: AsyncSession, *, occurrence_id: UUID, viewer_member_id: UUID) -> list[dict]:
    """People from the viewer's own circles who are going. They already share a circle with the
    viewer, so naming them reveals nothing the circle's member list does not (FR040 stays intact)."""
    rows = (await session.execute(text("SELECT milavn_activity.circle_peer_ids(:o, :m)"), {"o": str(occurrence_id), "m": str(viewer_member_id)})).all()
    ids = [r[0] for r in rows]
    hidden = await _blocked_filter(session, viewer_member_id, ids)
    names = await identity.display_names_for(ids)
    return [{"member_id": str(i), "display_name": names[i].display_name, "avatar": names[i].avatar} for i in ids if i not in hidden]
