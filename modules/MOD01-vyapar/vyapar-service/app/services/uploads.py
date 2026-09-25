# [Critique agent finding, fixed here] "Upload a screenshot" (opportunity
# entry, FR11) and the enquiry composer's attachment (FR22) both only ever
# accepted a pasted image URL — an honest, working substitute the codebase's
# own comments already declared as such, but genuinely unusable for FR11's
# own named scenario ("forward a WhatsApp screenshot"), since a member has
# no URL to paste for a photo sitting in their gallery. This is the ONE
# real file-upload implementation for the whole module — every screen that
# needs "attach a file" calls it, never a second, independently-coded upload
# path. Dev-environment storage is the local filesystem (no object-storage
# vendor account exists in this environment, the same honest gap already
# declared for verification-document images and privacy exports); files are
# served back statically from /uploads, mounted in main.py. Storage goes
# through the host-pluggable `app.integrations.storage` seam (IMP37): its
# default LocalFilesystemStorage writes the same folder and returns the same
# /uploads/<name> URL, and a host with S3/GCS supplies its own adapter
# without any change here or in any caller.
# Traces to: FR11, FR22
from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel

from app.identity import AuthzContext
from app.integrations.storage import get_storage

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_BYTES = 5 * 1024 * 1024  # [UX12's own 5 MB attachment limit, reused here]
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


class UploadOut(BaseModel):
    url: str
    size: int


def check_extension(filename: str | None) -> str:
    """Rejects an unsupported type before any bytes are read."""
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=422, detail="unsupported_file_type")
    return ext


async def store_upload(ctx: AuthzContext, filename: str | None, data: bytes, content_type: str | None = None) -> UploadOut:
    ext = check_extension(filename)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")
    # member id is sanitized into the filename only as a debugging aid in
    # this dev environment — never trusted as an access-control boundary;
    # the returned URL is a plain static path, same disclosure model as
    # every other attachment_url already stored in the DB.
    safe_member = re.sub(r"[^a-zA-Z0-9_]", "", ctx.member_id)[:32]
    name = f"{safe_member}-{uuid.uuid4().hex}{ext}"
    url = await get_storage().put(name, data, content_type)
    return UploadOut(url=url, size=len(data))
