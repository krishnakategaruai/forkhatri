"""Password hashing, session tokens and one-time-code MACs (TR12, TR19)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# Verified against when no account exists so both paths cost one Argon2id verify.
_TIMING_EQUALISER_HASH = _hasher.hash("forkhatri-timing-equaliser")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    if stored_hash is None:
        try:
            _hasher.verify(_TIMING_EQUALISER_HASH, f"{password}\x00")
        except VerificationError:
            pass
        return False
    try:
        return _hasher.verify(stored_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(stored_hash: str) -> bool:
    return _hasher.check_needs_rehash(stored_hash)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def new_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def otp_mac(pepper: str, challenge_id: UUID, code: str) -> str:
    return hmac.new(pepper.encode("utf-8"), f"{challenge_id}:{code}".encode(), hashlib.sha256).hexdigest()


def constant_time_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
