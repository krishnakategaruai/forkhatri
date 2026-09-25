# [IMP37] Webhook signing and secret storage.
#
# Signature header (Stripe-style, so replayed deliveries can be rejected):
#   X-Vyapar-Signature: t=<unix seconds>,v1=<hex HMAC-SHA256(secret, "<t>." + raw body)>
# The receiver recomputes the HMAC over the exact raw bytes it received,
# compares in constant time, and rejects a timestamp older than a few minutes.
#
# Signing secrets must be recoverable to sign each delivery, so they cannot be
# hashed like access tokens. They are encrypted with AES-256-GCM under
# INTEGRATION_SECRET_KEY (a deployment secret, never in the database) and
# shown to the member exactly once, at creation.
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

SECRET_PREFIX = "whsec_"


def _key() -> bytes:
    return hashlib.sha256(get_settings().integration_secret_key.encode("utf-8")).digest()


def new_secret() -> str:
    return SECRET_PREFIX + secrets.token_urlsafe(32)


def encrypt_secret(secret: str) -> str:
    nonce = os.urandom(12)
    return base64.b64encode(nonce + AESGCM(_key()).encrypt(nonce, secret.encode("utf-8"), b"vyapar-webhook")).decode("ascii")


def decrypt_secret(encoded: str) -> str:
    raw = base64.b64decode(encoded)
    return AESGCM(_key()).decrypt(raw[:12], raw[12:], b"vyapar-webhook").decode("utf-8")


def sign(secret: str, body: bytes, timestamp: int | None = None) -> str:
    t = int(time.time()) if timestamp is None else timestamp
    digest = hmac.new(secret.encode("utf-8"), f"{t}.".encode("ascii") + body, hashlib.sha256).hexdigest()
    return f"t={t},v1={digest}"


def verify(secret: str, body: bytes, header: str, tolerance_seconds: int = 300) -> bool:
    """Reference verifier (the same logic INTEGRATION-GUIDE.md shows receivers)."""
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        t = int(parts["t"])
    except (ValueError, KeyError):
        return False
    if abs(time.time() - t) > tolerance_seconds:
        return False
    expected = hmac.new(secret.encode("utf-8"), f"{t}.".encode("ascii") + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts.get("v1", ""))
