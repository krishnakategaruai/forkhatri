"""Photo/video storage — the one seam between this component and Object Storage.

[Config-placeholder convention] `OBJECT_STORAGE_*` in `.env.example` is still
`CHANGE_ME` — no real Object Storage vendor is configured yet. Rather than
leave photo upload unbuildable until that credential exists, this module
implements a REAL local-disk backend behind the same `storage_ref` contract
TR006 already fixed: a component never sees a filesystem path or an S3 key
directly, only an opaque ref this module resolves. Swapping in real Object
Storage later means changing this one file, not the profile component, the
API layer, or the database column (`profile_media.storage_ref` is already a
plain `text` column with no format baked in).

TR006's time-bound signed-URL requirement applies to the READ path (issuing a
viewer a URL) and is that tech req's own scope, not this one's — this module
only covers the WRITE path FR001 needs (saving a photo at profile-creation
time). `resolve_url()` below is deliberately named to make it obvious where
TR006's actual signed-URL logic replaces this local stand-in.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config.settings import get_settings

_LOCAL_MEDIA_ROOT = Path(__file__).resolve().parents[3] / ".local-media"
_log = logging.getLogger(__name__)
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_BYTES = 8 * 1024 * 1024  # 8 MiB — generous for a phone photo, bounded regardless
# A voice introduction is short by design; the browser records webm/mp4.
_ALLOWED_AUDIO_TYPES = {
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
}
_MAX_AUDIO_BYTES = 5 * 1024 * 1024  # 5 MiB — about a minute of speech, bounded regardless


class UnsupportedMedia(ValueError):
    """Raised for a content-type or size this endpoint does not accept."""


def _sniff_image_type(data: bytes) -> str:
    if data[:3] == bytes([0xFF, 0xD8, 0xFF]):
        return "image/jpeg"
    if data[:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return ""


async def save_photo(profile_id: uuid.UUID, upload: UploadFile) -> str:
    """Persist an uploaded photo, returning an opaque `storage_ref`.

    Local-disk implementation: validates content-type and a hard size cap
    (SP001-adjacent input validation — an unbounded upload is its own abuse
    surface), then writes to `.local-media/<profile_id>/<uuid>.<ext>`.
    """
    settings = get_settings()
    if settings.object_storage_access_key != "CHANGE_ME":
        # A real Object Storage credential exists but this module was never
        # updated to use it — fail loudly rather than silently keep writing to
        # local disk once a real backend is actually configured.
        raise NotImplementedError(
            "OBJECT_STORAGE_ACCESS_KEY is configured but storage.py still only "
            "implements the local-disk stand-in — wire the real backend here."
        )

    data = await upload.read()
    if not data:
        raise UnsupportedMedia("empty file")
    if len(data) > _MAX_BYTES:
        raise UnsupportedMedia(f"file exceeds {_MAX_BYTES} bytes")
    # Phones and some browsers label a photo "image/jpg", "application/octet-stream"
    # or nothing at all, so the picture's own first bytes decide what it is.
    content_type = _sniff_image_type(data)
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMedia(f"unsupported content type: {upload.content_type!r}")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[content_type]
    directory = _LOCAL_MEDIA_ROOT / str(profile_id)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    (directory / filename).write_bytes(data)

    return f"local://{profile_id}/{filename}"


async def save_voice(profile_id: uuid.UUID, upload: UploadFile) -> str:
    """Persist a recorded voice introduction, returning an opaque `storage_ref`.

    Same contract and same local-disk stand-in as `save_photo()`; only the
    accepted content types and the size cap differ."""
    settings = get_settings()
    if settings.object_storage_access_key != "CHANGE_ME":
        raise NotImplementedError(
            "OBJECT_STORAGE_ACCESS_KEY is configured but storage.py still only "
            "implements the local-disk stand-in — wire the real backend here."
        )

    content_type = (upload.content_type or "").split(";")[0].strip()
    ext = _ALLOWED_AUDIO_TYPES.get(content_type)
    if ext is None:
        raise UnsupportedMedia(f"unsupported content type: {content_type!r}")

    data = await upload.read()
    if not data:
        raise UnsupportedMedia("empty recording")
    if len(data) > _MAX_AUDIO_BYTES:
        raise UnsupportedMedia(f"recording exceeds {_MAX_AUDIO_BYTES} bytes")

    directory = _LOCAL_MEDIA_ROOT / str(profile_id)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    (directory / filename).write_bytes(data)

    return f"local://{profile_id}/{filename}"


def resolve_url(storage_ref: str) -> str:
    """[TR006 stand-in] Resolve a `storage_ref` to something a client can load.

    Local-disk implementation returns a path served by `api/routes/media.py`,
    which checks the viewer's authorization on every request (FR006). A real
    Object Storage backend replaces this with TR006's short-lived signed URL.
    """
    if not storage_ref.startswith("local://"):
        raise ValueError(f"unrecognised storage_ref: {storage_ref!r}")
    return f"/media/{storage_ref.removeprefix('local://')}"


def local_path(storage_ref: str) -> Path:
    """The file behind a local `storage_ref`, refusing anything outside the media root."""
    if not storage_ref.startswith("local://"):
        raise ValueError(f"unrecognised storage_ref: {storage_ref!r}")
    root = _LOCAL_MEDIA_ROOT.resolve()
    path = (root / storage_ref.removeprefix("local://")).resolve()
    if root not in path.parents:
        raise ValueError(f"storage_ref escapes the media root: {storage_ref!r}")
    return path


def delete_stored_file(storage_ref: str | None) -> None:
    """[D17, 2026-10-06] Remove the file behind a `storage_ref` whose row is gone.

    Called only after the database change that dropped or replaced the row has
    committed (see `profile.interface._delete_file_after_commit`). A file that
    is already missing is fine; a ref that is not local, or that would point
    outside the media root, is left alone. A failure is logged (by ref only,
    never by content) and never surfaces to the member: the row change has
    already succeeded."""
    if not storage_ref or not storage_ref.startswith("local://"):
        return
    try:
        path = local_path(storage_ref)
    except ValueError:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        _log.warning("could not delete stored media file for ref %s", storage_ref)


_MEDIA_DIR_RE = __import__("re").compile(r"^(offline-)?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def remove_member_files(refs: list[str], dirs: list[str]) -> int:
    """[Account deletion, 2026-11-22] Remove every stored file behind `refs`, then
    the media folders named after the erased ids (`dirs`), returning how many files
    were removed. Called only after the database erase has committed. Anything that
    is not a local ref or a plain id-named folder directly under the media root is
    ignored; a failure is logged and never surfaces (the rows are already gone)."""
    import shutil

    removed = 0
    for ref in refs:
        if not ref or not ref.startswith("local://"):
            continue
        try:
            path = local_path(ref)
            if path.is_file():
                path.unlink()
                removed += 1
        except (ValueError, OSError):
            _log.warning("could not delete stored media file for ref %s", ref)
    root = _LOCAL_MEDIA_ROOT.resolve()
    for name in dirs:
        if not _MEDIA_DIR_RE.match(name or ""):
            continue
        folder = (root / name)
        if not folder.is_dir():
            continue
        try:
            removed += sum(1 for f in folder.rglob("*") if f.is_file())
            shutil.rmtree(folder)
        except OSError:
            _log.warning("could not delete media folder %s", name)
    return removed
