"""Profile photo delivery — FR006.

Every request is authorized by `profile.media_path_for_viewer()`. A voice
introduction and any non-main photo are served only to the owner or to an
accepted connection; a searchable candidate's MAIN photo is also served to any
signed-in member (DEC-V1-016), which is what Discover shows. Anyone else,
signed in or not, gets 404 — the same answer as a missing file.
"""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import AuthenticatedAccount, DbSession
from app.components.profile import interface as profile

router = APIRouter(prefix="/media", tags=["media"])

# Photos, and a voice introduction (migration 029).
_FILENAME = re.compile(r"[0-9a-f-]{36}\.(jpg|png|webp|webm|ogg|m4a|mp3)")


@router.get("/{profile_id}/{filename}")
async def get_media(
    profile_id: UUID, filename: str, session: DbSession, account_id: AuthenticatedAccount
) -> FileResponse:
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not _FILENAME.fullmatch(filename):
        raise not_found
    path = await profile.media_path_for_viewer(
        session, viewer_account_id=account_id, storage_ref=f"local://{profile_id}/{filename}"
    )
    if path is None or not path.is_file():
        raise not_found
    return FileResponse(path, headers={"Cache-Control": "private, no-store"})
