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

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config.settings import get_settings

_LOCAL_MEDIA_ROOT = Path(__file__).resolve().parents[3] / ".local-media"
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_BYTES = 8 * 1024 * 1024  # 8 MiB — generous for a phone photo, bounded regardless


class UnsupportedMedia(ValueError):
    """Raised for a content-type or size this endpoint does not accept."""


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

    content_type = upload.content_type or ""
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMedia(f"unsupported content type: {content_type!r}")

    data = await upload.read()
    if not data:
        raise UnsupportedMedia("empty file")
    if len(data) > _MAX_BYTES:
        raise UnsupportedMedia(f"file exceeds {_MAX_BYTES} bytes")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[content_type]
    directory = _LOCAL_MEDIA_ROOT / str(profile_id)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    (directory / filename).write_bytes(data)

    return f"local://{profile_id}/{filename}"


def resolve_url(storage_ref: str) -> str:
    """[TR006 stand-in] Resolve a `storage_ref` to something a client can load.

    Local-disk implementation returns a path under this service's own static
    mount (see `main.py`) with NO expiry and NO scoping — this is explicitly
    NOT TR006's time-bound signed URL, which is that tech req's own future
    implementation once a real Object Storage vendor is selected. Fine for
    local development; must not ship to production as-is.
    """
    if not storage_ref.startswith("local://"):
        raise ValueError(f"unrecognised storage_ref: {storage_ref!r}")
    return f"/media/{storage_ref.removeprefix('local://')}"
