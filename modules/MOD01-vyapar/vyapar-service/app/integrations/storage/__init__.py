# [IMP37 — Refactor B] Object storage adapter interface.
#
# Today the one upload endpoint (app/routers/uploads.py, FR11/FR22) writes
# straight to the local `uploads/` folder, which main.py serves at /uploads.
# That router belongs to workstream A and is deliberately not edited here;
# this module defines the seam it (and any new upload path) should call:
#
#     from app.integrations.storage import get_storage
#     url = await get_storage().put(name, data, content_type)
#
# LocalFilesystemStorage reproduces today's behaviour exactly (same folder,
# same /uploads/<name> URL). A host with S3, GCS or its own media service
# implements ObjectStorage.put() and returns it from get_storage().
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"


class ObjectStorage(Protocol):
    async def put(self, name: str, data: bytes, content_type: str | None = None) -> str:
        """Stores the bytes under `name` and returns the URL clients use."""
        ...


class LocalFilesystemStorage:
    def __init__(self, directory: Path = UPLOAD_DIR, public_prefix: str = "/uploads") -> None:
        self.directory = directory
        self.public_prefix = public_prefix.rstrip("/")

    async def put(self, name: str, data: bytes, content_type: str | None = None) -> str:
        if "/" in name or "\\" in name or name.startswith("."):
            raise ValueError("storage names are flat file names")
        self.directory.mkdir(exist_ok=True)
        await asyncio.to_thread((self.directory / name).write_bytes, data)
        return f"{self.public_prefix}/{name}"


_storage: ObjectStorage = LocalFilesystemStorage()


def get_storage() -> ObjectStorage:
    return _storage


def set_storage(storage: ObjectStorage) -> None:
    """For a host wiring its own storage at startup."""
    global _storage
    _storage = storage
