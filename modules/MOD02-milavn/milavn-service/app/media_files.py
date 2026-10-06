"""Local-disk media shared by circle covers, circle posts and moments.

# [Functional test pass 2026-09-28, B4/B5/B6/B7] Uploaded files were trusted by the browser's
# `content_type`, written in full before any size check, and never removed when the post, cover
# or circle they belonged to went away. Everything that stores or removes a media file goes
# through here so those rules hold everywhere:
#   * an image is recognised by its first bytes (JPEG / PNG / WebP), never by the label;
#   * the size cap is enforced while streaming, so an oversized upload never lands on disk whole;
#   * removal takes the `folder/name` refs kept in the database and refuses anything that would
#     step outside the media root.
# [045] Serving: circle posts/documents/covers, chat photos and moments are private and answered
# only to people allowed to see them (app/api/routes/media.py); the rest of `/media` stays public.
# Every upload (circle posts and covers, moments, chat photos, profile photos, activity covers)
# now goes through sniff_image + store.
"""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

MB = 1024 * 1024
MAX_PHOTO_BYTES = 10 * MB
MAX_COVER_BYTES = 5 * MB
MAX_DOC_BYTES = 10 * MB
_CHUNK = 64 * 1024


class TooLarge(Exception):
    def __init__(self, limit_bytes: int) -> None:
        super().__init__(limit_bytes)
        self.limit_mb = limit_bytes // MB


class NotAnImage(Exception):
    pass


def sniff_image(upload) -> str:  # noqa: ANN001 — a Starlette UploadFile
    """The real image type from the file's first bytes: '.jpg', '.png' or '.webp'."""
    fh = upload.file
    head = fh.read(12)
    fh.seek(0)
    if head[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    raise NotAnImage


class NotADocument(Exception):
    pass


# [053] What each accepted file type must look like in its first bytes. A type the configuration
# lists that is not here is refused, so a new type needs a deliberate entry.
_OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # old Office (.doc / .xls / .ppt)
_ZIP = b"PK\x03\x04"  # Office Open XML (.docx / .xlsx / .pptx)
_DOC_MAGIC: dict[str, bytes | None] = {
    "pdf": b"%PDF-",
    "doc": _OLE, "xls": _OLE, "ppt": _OLE,
    "docx": _ZIP, "xlsx": _ZIP, "pptx": _ZIP,
    "txt": None, "csv": None,  # plain text: no NUL bytes, valid UTF-8
}


def sniff_document(upload, allowed: list[str]) -> str:  # noqa: ANN001
    """[053] The document's extension ('.pdf', ...) when its name is an allowed type AND its first
    bytes match that type. Raises NotADocument otherwise."""
    name = (getattr(upload, "filename", None) or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in {a.lower().lstrip(".") for a in allowed} or ext not in _DOC_MAGIC:
        raise NotADocument
    fh = upload.file
    head = fh.read(4096)
    fh.seek(0)
    magic = _DOC_MAGIC[ext]
    if magic is None:
        if not head or b"\x00" in head:
            raise NotADocument
        try:
            head.decode("utf-8")
        except UnicodeDecodeError as exc:  # a multi-byte character cut at 4096 is still text
            if exc.start < len(head) - 3:
                raise NotADocument from exc
    elif not head.startswith(magic):
        raise NotADocument
    return f".{ext}"


def upload_size(upload) -> int:  # noqa: ANN001
    """Size without reading it into memory (the spooled temp file is seekable)."""
    fh = upload.file
    fh.seek(0, 2)
    size = fh.tell()
    fh.seek(0)
    return size


def check_size(upload, max_bytes: int) -> None:  # noqa: ANN001
    if upload_size(upload) > max_bytes:
        raise TooLarge(max_bytes)


def store(upload, folder: str, prefix: str, ext: str, max_bytes: int, *, name: str | None = None) -> str:  # noqa: ANN001
    """Stream to `<media_root>/<folder>/<prefix>-<random><ext>` (or exactly `name` when given),
    stopping at `max_bytes`. Returns the ref kept in the database (`folder/name`)."""
    root: Path = get_settings().media_root / folder
    root.mkdir(parents=True, exist_ok=True)
    name = name or f"{prefix}-{uuid4().hex[:8]}{ext}"
    target = root / name
    written = 0
    upload.file.seek(0)
    try:
        with target.open("wb") as out:
            while chunk := upload.file.read(_CHUNK):
                written += len(chunk)
                if written > max_bytes:
                    raise TooLarge(max_bytes)
                out.write(chunk)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return f"{folder}/{name}"


def remove(*refs: str | None) -> None:
    """Delete stored files by their refs; missing files and foreign paths are ignored."""
    root = get_settings().media_root.resolve()
    for ref in refs:
        if not ref:
            continue
        try:
            path = (root / ref).resolve()
            if root not in path.parents:
                continue
            path.unlink(missing_ok=True)
        except OSError as exc:  # a locked file on Windows must not fail the request
            logger.warning("could not remove media %s: %s", ref, exc)
