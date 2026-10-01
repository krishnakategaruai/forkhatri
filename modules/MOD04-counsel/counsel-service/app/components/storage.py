"""StorageProvider boundary. Local disk under STORAGE_ROOT for development;
an object-store adapter can replace `save`/`path_for` without touching callers.
Public objects (profile photos) live under `public/`; everything else is
private and only served through an authorised route.

Private files (consultation files, recordings, verification documents) are
scanned for malware and encrypted at rest with AES-256-GCM before they touch
the disk. Files saved before encryption existed stay readable (the row keeps an
`encrypted` flag)."""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
import socket
import struct
from pathlib import Path
from urllib.parse import quote

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.responses import FileResponse, Response

from app.errors import DomainError
from app.settings import get_settings

log = logging.getLogger("counsel.storage")

IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
DOCUMENT_TYPES = {**IMAGE_TYPES, "application/pdf": ".pdf"}


def _root() -> Path:
    return get_settings().storage_path


def save(prefix: str, data: bytes, ext: str) -> str:
    key = f"{prefix}/{secrets.token_hex(10)}{ext}"
    path = _root() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return key


def path_for(key: str) -> Path:
    path = (_root() / key).resolve()
    if _root().resolve() not in path.parents:
        raise DomainError("not_found", "not found", 404)
    return path


def check(mime: str, data: bytes, allowed: dict[str, str], max_mb: int) -> str:
    if mime not in allowed:
        raise DomainError("file_type", "That file type is not allowed.", 422)
    if len(data) > max_mb * 1024 * 1024:
        raise DomainError("file_too_large", f"Files up to {max_mb} MB.", 422)
    # Cheap content sniffing so a renamed executable is not accepted as an image/PDF.
    magic = {"image/jpeg": b"\xff\xd8", "image/png": b"\x89PNG", "image/webp": b"RIFF", "application/pdf": b"%PDF"}
    if mime in magic and not data.startswith(magic[mime]):
        raise DomainError("file_type", "The file does not match its type.", 422)
    return allowed[mime]


# --- Encryption at rest ---------------------------------------------------------------

_MAGIC = b"CF1"   # format marker: CF1 | 12-byte nonce | AES-GCM ciphertext+tag


def _key() -> bytes:
    raw = get_settings().file_encryption_key
    if not raw or "CHANGE_ME" in raw:
        # Development fallback derived from the service key; FILE_ENCRYPTION_KEY is
        # required outside loopback development (checked in main at start-up).
        return hashlib.sha256(("counsel-files:" + get_settings().platform_service_key).encode()).digest()
    return base64.urlsafe_b64decode(raw)


def encrypt_bytes(data: bytes) -> bytes:
    nonce = os.urandom(12)
    return _MAGIC + nonce + AESGCM(_key()).encrypt(nonce, data, None)


def decrypt_bytes(blob: bytes) -> bytes:
    if not blob.startswith(_MAGIC):
        raise DomainError("file_unreadable", "This file cannot be opened.", 500)
    return AESGCM(_key()).decrypt(blob[3:15], blob[15:], None)


# --- Malware scanning -----------------------------------------------------------------

def scan(data: bytes) -> str:
    """Returns 'clean' or 'not_scanned'; raises if the file is infected.
    MALWARE_SCANNER=none (default) skips; clamav streams to a local clamd."""
    s = get_settings()
    if s.malware_scanner != "clamav":
        return "not_scanned"
    try:
        with socket.create_connection((s.clamd_host, s.clamd_port), timeout=30) as sock:
            sock.sendall(b"zINSTREAM\0")
            for i in range(0, len(data), 1 << 16):
                chunk = data[i:i + (1 << 16)]
                sock.sendall(struct.pack(">I", len(chunk)) + chunk)
            sock.sendall(struct.pack(">I", 0))
            reply = b""
            while not reply.endswith(b"\0"):
                part = sock.recv(4096)
                if not part:
                    break
                reply += part
    except OSError as e:
        # Scanning is switched on but the scanner is down: refuse rather than store an unchecked file.
        log.warning("clamd unavailable: %s", e)
        raise DomainError("scan_unavailable", "Files cannot be checked right now. Please try again shortly.", 503)
    text = reply.rstrip(b"\0").decode(errors="replace")
    if text.endswith("FOUND"):
        log.warning("malware blocked: %s", text)
        raise DomainError("file_infected", "This file looks unsafe and was not uploaded.", 422)
    if not text.endswith("OK"):
        raise DomainError("scan_unavailable", "Files cannot be checked right now. Please try again shortly.", 503)
    return "clean"


def save_private(prefix: str, data: bytes, ext: str = "") -> tuple[str, str]:
    """Scan, encrypt and store. Returns (storage key, scan status)."""
    status = scan(data)
    return save(prefix, encrypt_bytes(data), ext), status


def serve(key: str, encrypted: bool, mime: str, name: str) -> Response:
    """Send a private file (decrypting when needed) as a download."""
    path = path_for(key)
    if not path.exists():
        raise DomainError("not_found", "not found", 404)
    if not encrypted:
        return FileResponse(path, media_type=mime, filename=name)
    return Response(decrypt_bytes(path.read_bytes()), media_type=mime,
                    headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(name)})
