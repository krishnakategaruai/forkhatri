"""Circle photo albums and the per-circle notification setting (Phase 2, Step 6; migration 053).

Albums: any member names an album and adds photos to it; the uploader, an organizer or an assistant
removes a photo; an organizer or assistant removes an album. Album photos are private circle media
(`circle-albums/`, served only through `circle_media_access`). Visibility is RLS; removals are
definer functions that also hand back the file refs so they leave the disk.

Notification setting: each member chooses, per circle, 'all' (every new post plus the highlights),
'highlights' (announcements, new events and questions only) or 'off'. The dispatcher reads it
through `milavn_circle.circle_notify_recipients`, so it is honoured server-side for every kind.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import media_files
from app.components.identity_bridge import interface as identity

NOTIFY_LEVELS = ("all", "highlights", "off")
DEFAULT_NOTIFY_LEVEL = "all"
MAX_ALBUM_NAME = 60
MAX_CAPTION = 200


class NotMember(Exception):
    pass


class NotAllowed(Exception):
    pass


class NotFound(Exception):
    pass


class InvalidInput(Exception):
    def __init__(self, field: str) -> None:
        super().__init__(field)
        self.field = field


class DuplicateAlbum(Exception):
    pass


class UnsupportedPhoto(Exception):
    pass


class TooManyPhotos(Exception):
    def __init__(self, limit: int) -> None:
        super().__init__(limit)
        self.limit = limit


async def _is_member(session: AsyncSession, circle_id: UUID, member_id: UUID) -> bool:
    return bool(
        (await session.execute(text("SELECT milavn_circle.is_active_member(:c, :m)"), {"c": str(circle_id), "m": str(member_id)})).scalar_one()
    )


async def _role(session: AsyncSession, circle_id: UUID, member_id: UUID) -> str | None:
    return (await session.execute(text("SELECT milavn_circle.current_role_of(:c, :m)"), {"c": str(circle_id), "m": str(member_id)})).scalar_one_or_none()


# --- Notification setting ----------------------------------------------------------------------


async def notify_level(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> str:
    row = (
        await session.execute(
            text("SELECT level FROM milavn_circle.circle_notify_setting WHERE circle_id = :c AND member_id = :m"),
            {"c": str(circle_id), "m": str(member_id)},
        )
    ).first()
    return row[0] if row else DEFAULT_NOTIFY_LEVEL


async def set_notify_level(session: AsyncSession, *, circle_id: UUID, member_id: UUID, level: str) -> str:
    if level not in NOTIFY_LEVELS:
        raise InvalidInput("level")
    if not await _is_member(session, circle_id, member_id):
        raise NotMember
    await session.execute(
        text(
            "INSERT INTO milavn_circle.circle_notify_setting (circle_id, member_id, level) VALUES (:c, :m, :l) "
            "ON CONFLICT (circle_id, member_id) DO UPDATE SET level = EXCLUDED.level, updated_at = now()"
        ),
        {"c": str(circle_id), "m": str(member_id), "l": level},
    )
    return level


# --- Albums -------------------------------------------------------------------------------------


async def albums(session: AsyncSession, *, circle_id: UUID, viewer_member_id: UUID) -> list[dict]:
    """Every album, newest activity first, with a few covers. RLS returns nothing to outsiders."""
    rows = (
        await session.execute(
            text(
                "SELECT a.id, a.name, a.created_by_member_id, a.created_at, "
                "  (SELECT count(*) FROM milavn_circle.circle_album_photo p WHERE p.album_id = a.id) AS n, "
                "  (SELECT array_agg(x.storage_ref) FROM (SELECT storage_ref FROM milavn_circle.circle_album_photo p "
                "      WHERE p.album_id = a.id ORDER BY p.created_at DESC LIMIT 4) x) AS covers, "
                "  greatest(a.created_at, (SELECT max(created_at) FROM milavn_circle.circle_album_photo p WHERE p.album_id = a.id)) AS last_at "
                "FROM milavn_circle.circle_album a WHERE a.circle_id = :c ORDER BY last_at DESC"
            ),
            {"c": str(circle_id)},
        )
    ).all()
    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "mine": r[2] == viewer_member_id,
            "created_at": r[3].isoformat(),
            "photo_count": int(r[4]),
            "covers": [f"/media/{ref}" for ref in (r[5] or [])],
        }
        for r in rows
    ]


async def create_album(session: AsyncSession, *, circle_id: UUID, member_id: UUID, name: str) -> dict:
    clean = " ".join((name or "").split())
    if not clean or len(clean) > MAX_ALBUM_NAME:
        raise InvalidInput("name")
    if not await _is_member(session, circle_id, member_id):
        raise NotMember
    album_id = uuid4()
    try:
        async with session.begin_nested():
            await session.execute(
                text("INSERT INTO milavn_circle.circle_album (id, circle_id, name, created_by_member_id) VALUES (:id, :c, :n, :m)"),
                {"id": str(album_id), "c": str(circle_id), "n": clean, "m": str(member_id)},
            )
    except IntegrityError as exc:
        raise DuplicateAlbum from exc
    return {"id": str(album_id), "name": clean, "mine": True, "created_at": datetime.now().astimezone().isoformat(), "photo_count": 0, "covers": []}


async def album_photos(session: AsyncSession, *, circle_id: UUID, album_id: UUID, viewer_member_id: UUID) -> dict:
    head = (
        await session.execute(
            text("SELECT id, name, created_by_member_id FROM milavn_circle.circle_album WHERE id = :a AND circle_id = :c"),
            {"a": str(album_id), "c": str(circle_id)},
        )
    ).first()
    if head is None:
        raise NotFound
    rows = (
        await session.execute(
            text(
                "SELECT id, member_id, storage_ref, caption, created_at FROM milavn_circle.circle_album_photo "
                "WHERE album_id = :a ORDER BY created_at DESC LIMIT 300"
            ),
            {"a": str(album_id)},
        )
    ).all()
    hidden: set[UUID] = set()
    for who in {r[1] for r in rows}:
        if who != viewer_member_id and (
            await session.execute(text("SELECT milavn_safety.is_blocked_either_way(:a, :b)"), {"a": str(viewer_member_id), "b": str(who)})
        ).scalar_one():
            hidden.add(who)
    names = await identity.display_names_for([r[1] for r in rows])
    return {
        "id": str(head[0]),
        "name": head[1],
        "mine": head[2] == viewer_member_id,
        "photos": [
            {
                "id": str(r[0]),
                "url": f"/media/{r[2]}",
                "caption": r[3],
                "created_at": r[4].isoformat(),
                "mine": r[1] == viewer_member_id,
                "added_by": names[r[1]].display_name,
            }
            for r in rows
            if r[1] not in hidden
        ],
    }


async def add_album_photos(
    session: AsyncSession, *, circle_id: UUID, album_id: UUID, member_id: UUID, photos: list[UploadFile], caption: str | None, max_per_upload: int, max_mb: int
) -> int:
    """Add several photos at once. All are checked before any is stored."""
    photos = [p for p in photos if p is not None]
    if not photos:
        raise InvalidInput("photos")
    if len(photos) > max_per_upload:
        raise TooManyPhotos(max_per_upload)
    if not await _is_member(session, circle_id, member_id):
        raise NotMember
    if (await session.execute(text("SELECT 1 FROM milavn_circle.circle_album WHERE id = :a AND circle_id = :c"), {"a": str(album_id), "c": str(circle_id)})).first() is None:
        raise NotFound
    cap = max_mb * media_files.MB
    checked: list[tuple[UploadFile, str]] = []
    for p in photos:
        try:
            ext = media_files.sniff_image(p)
        except media_files.NotAnImage as exc:
            raise UnsupportedPhoto from exc
        media_files.check_size(p, cap)
        checked.append((p, ext))
    refs: list[str] = []
    note = (caption or "").strip()[:MAX_CAPTION] or None
    try:
        for p, ext in checked:
            refs.append(media_files.store(p, "circle-albums", str(circle_id), ext, cap))
        for ref in refs:
            await session.execute(
                text("INSERT INTO milavn_circle.circle_album_photo (album_id, circle_id, member_id, storage_ref, caption) VALUES (:a, :c, :m, :r, :cap)"),
                {"a": str(album_id), "c": str(circle_id), "m": str(member_id), "r": ref, "cap": note},
            )
    except BaseException:
        media_files.remove(*refs)
        raise
    return len(refs)


async def remove_album_photo(session: AsyncSession, *, circle_id: UUID, photo_id: UUID, member_id: UUID) -> None:
    row = (
        await session.execute(
            text("SELECT r_outcome, r_ref FROM milavn_circle.remove_album_photo(:c, :p, :m)"),
            {"c": str(circle_id), "p": str(photo_id), "m": str(member_id)},
        )
    ).first()
    outcome = row[0] if row else "not_found"
    if outcome == "not_found":
        raise NotFound
    if outcome != "removed":
        raise NotAllowed
    media_files.remove(row[1])


async def remove_album(session: AsyncSession, *, circle_id: UUID, album_id: UUID, member_id: UUID) -> None:
    row = (
        await session.execute(
            text("SELECT r_outcome, r_refs FROM milavn_circle.remove_circle_album(:c, :a, :m)"),
            {"c": str(circle_id), "a": str(album_id), "m": str(member_id)},
        )
    ).first()
    outcome = row[0] if row else "not_found"
    if outcome == "not_found":
        raise NotFound
    if outcome != "removed":
        raise NotAllowed
    media_files.remove(*(row[1] or []))


async def is_manager(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> bool:
    return (await _role(session, circle_id, member_id)) in ("organizer", "assistant")
