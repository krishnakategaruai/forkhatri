"""Private media — circle photos, documents and covers, chat photos and moments (2026-09-29).

# `/media` used to be one open static folder: anyone holding a URL could fetch an invite-only
# circle's photos and documents, a private chat's photos, or an activity's moments. The URLs stay
# exactly as they were (`/media/<folder>/<file>`, what the database keeps and every response
# returns), but the private folders are answered here, and only to someone allowed to see them:
#   circle-posts, circle-docs   the circle's active members, its creator, moderators
#   circle-albums               [053] album photos: the circle's active members, its creator, moderators
#   circle-covers               anyone for an open circle (discover cards); otherwise the members,
#                               moderators, a pending invitee, or `?invite=<token>` of a working link
#   chat                        the conversation's members (chat_message RLS); a retracted photo is gone
#   moments                     the activity's thread (occurrence_photo RLS: organizers + participants)
# Everything else (profile photos, activity covers, seeded assets) stays public in `PublicMedia`.
# A file the viewer may not see is a 404, never a 403, so its existence is not given away.
# The browser sends the ForKhatri session cookie with <img> requests (same site, either directly
# to the API or through the web app's `/media` rewrite), so the normal member resolution applies.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from app.api.deps import DbSession, OptionalMember
from app.config.settings import get_settings

router = APIRouter(tags=["media"])

PRIVATE_FOLDERS = frozenset({"circle-posts", "circle-docs", "circle-covers", "circle-albums", "chat", "moments"})
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9]{1,5})?$")
_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
}
GATED_CACHE = "private, max-age=300"
OPEN_CACHE = "public, max-age=300"


class PublicMedia(StaticFiles):
    """The static folder minus the private ones. Windows paths are case-insensitive, so the check
    is too (`/media/CIRCLE-POSTS/...` must not slip past the gated routes into the folder)."""

    async def get_response(self, path: str, scope: Scope):  # noqa: ANN201
        first = path.replace("\\", "/").lstrip("/").split("/", 1)[0].lower()
        if first in PRIVATE_FOLDERS:
            raise HTTPException(status_code=404)
        return await super().get_response(path, scope)


def _not_found() -> HTTPException:
    return HTTPException(status_code=404)


def _file(folder: str, name: str) -> Path:
    if not _NAME.match(name):
        raise _not_found()
    root = get_settings().media_root.resolve()
    path = (root / folder / name).resolve()
    if path.parent != (root / folder).resolve() or not path.is_file():
        raise _not_found()
    return path


def _content_disposition(doc_name: str | None, fallback: str) -> str:
    name = (doc_name or fallback).replace("\r", " ").replace("\n", " ")
    ascii_name = re.sub(r'[^\x20-\x7e]|["\\]', "_", name) or fallback
    return f"inline; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name, safe='')}"


def _send(path: Path, *, cache: str, disposition: str | None = None) -> FileResponse:
    headers = {"Cache-Control": cache, "X-Content-Type-Options": "nosniff"}
    if disposition:
        headers["Content-Disposition"] = disposition
    media_type = _TYPES.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media_type, headers=headers)


async def _circle_file(session: DbSession, folder: str, name: str, invite: str | None) -> FileResponse:
    path = _file(folder, name)
    token_hash = hashlib.sha256(invite.encode()).hexdigest() if invite else None
    row = (
        await session.execute(
            text("SELECT kind, doc_name, is_open FROM milavn_circle.circle_media_access(:r, :h)"),
            {"r": f"{folder}/{name}", "h": token_hash},
        )
    ).first()
    expected = {"circle-covers": "cover", "circle-posts": "photo", "circle-docs": "doc", "circle-albums": "album"}[folder]
    if row is None or row[0] != expected:
        raise _not_found()
    if row[0] == "doc":
        return _send(path, cache=GATED_CACHE, disposition=_content_disposition(row[1], name))
    return _send(path, cache=OPEN_CACHE if row[0] == "cover" and row[2] else GATED_CACHE)


@router.api_route("/media/circle-posts/{name}", methods=["GET", "HEAD"], include_in_schema=False)
async def circle_post_photo(name: str, session: DbSession, member: OptionalMember) -> FileResponse:
    return await _circle_file(session, "circle-posts", name, None)


@router.api_route("/media/circle-docs/{name}", methods=["GET", "HEAD"], include_in_schema=False)
async def circle_post_document(name: str, session: DbSession, member: OptionalMember) -> FileResponse:
    return await _circle_file(session, "circle-docs", name, None)


@router.api_route("/media/circle-albums/{name}", methods=["GET", "HEAD"], include_in_schema=False)
async def circle_album_photo(name: str, session: DbSession, member: OptionalMember) -> FileResponse:
    return await _circle_file(session, "circle-albums", name, None)


@router.api_route("/media/circle-covers/{name}", methods=["GET", "HEAD"], include_in_schema=False)
async def circle_cover(name: str, session: DbSession, member: OptionalMember, invite: str | None = None) -> FileResponse:
    return await _circle_file(session, "circle-covers", name, invite)


@router.api_route("/media/chat/{name}", methods=["GET", "HEAD"], include_in_schema=False)
async def chat_photo(name: str, session: DbSession, member: OptionalMember) -> FileResponse:
    path = _file("chat", name)
    # chat_message RLS: only the conversation's members see the row.
    seen = (
        await session.execute(
            text("SELECT 1 FROM milavn_connect.chat_message WHERE media_ref = :r AND deleted_at IS NULL LIMIT 1"), {"r": f"chat/{name}"}
        )
    ).first()
    if seen is None:
        raise _not_found()
    return _send(path, cache=GATED_CACHE)


@router.api_route("/media/moments/{name}", methods=["GET", "HEAD"], include_in_schema=False)
async def moment_photo(name: str, session: DbSession, member: OptionalMember) -> FileResponse:
    path = _file("moments", name)
    # occurrence_photo RLS: the activity's organizers and participants (the same people who see the wall).
    seen = (
        await session.execute(text("SELECT 1 FROM milavn_activity.occurrence_photo WHERE storage_ref = :r LIMIT 1"), {"r": f"moments/{name}"})
    ).first()
    if seen is None:
        raise _not_found()
    return _send(path, cache=GATED_CACHE)
