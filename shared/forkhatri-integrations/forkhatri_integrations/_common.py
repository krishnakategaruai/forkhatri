"""Small helpers shared by the parts of this library (not part of the public interface)."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping

PLACEHOLDER = "CHANGE_ME"


def is_placeholder(value: str | None) -> bool:
    return not value or value.startswith(PLACEHOLDER)


def sign(secret: str, body: bytes) -> str:
    """HMAC-SHA256 hex over the raw body, the scheme most Indian gateways use."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def signature_ok(secret: str, body: bytes, signature: str | None) -> bool:
    if is_placeholder(secret) or not signature:
        return False
    return hmac.compare_digest(sign(secret, body), signature)


def lower_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    return {k.lower(): v for k, v in (headers or {}).items()}


def mask(address: str) -> str:
    """A log-safe hint of a phone number or email: never log the full destination."""
    if "@" in address:
        name, _, domain = address.partition("@")
        return f"{name[:1]}***@{domain}"
    digits = address.strip()
    return f"{digits[:3]}***{digits[-2:]}" if len(digits) > 5 else "***"
