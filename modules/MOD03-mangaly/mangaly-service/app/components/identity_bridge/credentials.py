"""Argon2id credential hashing, and the equivalent-cost dummy verification.

# [SP092/SP104] Credential storage is Argon2id with the parameters pinned in
# `.env.example` — never a fast general-purpose hash, never unsalted.
# Approach: argon2-cffi's `PasswordHasher`, constructed from
# `CREDENTIAL_HASH_TIME_COST` / `_MEMORY_COST_KB` / `_PARALLELISM` rather than
# from library defaults, so the deployed cost is the one Step 8 signed off on
# and is changeable without a code change. SP104's threshold treats the ~250-500 ms
# verification cost as "a security property, not a latency regression".
#
# [SP093 — the timing oracle] Login MUST perform an equivalent-cost dummy
# verification when no account exists.
# Approach: SP093 is explicit that an identical response body is "necessary but
# not sufficient... the stronger the hashing, the louder the leak" — if the
# expensive verify only runs when an account exists, a non-existent identifier
# returns measurably faster and the timing difference re-reveals exactly what
# the identical body hid. `verify_or_dummy()` is therefore the ONLY verification
# entry point: it takes an `Optional[stored_hash]` and, when that is None,
# verifies the supplied credential against a fixed decoy hash generated with the
# *same* parameters. Both paths do one real Argon2id verification. There is no
# separate `verify()` a handler could call on the found-account branch only,
# which is what makes the parity structural instead of a thing someone
# remembered to do.
#
# The decoy hash is generated once at import time from a random secret, not
# hardcoded: a constant decoy shipped in source would let an attacker recognise
# it, and a decoy generated per call would itself add a distinguishable cost.
# Traces to: TR092, TR093, SP092, SP093, SP104, v1-decisions.md (Argon2id note).
"""

from __future__ import annotations

import logging
import secrets

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions
from argon2.low_level import Type

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class CredentialTooWeak(ValueError):
    """[SP092 tampering row] Server-side credential-strength rejection at signup.

    [ADR-010] Carries an i18n key + params rather than a preformatted English
    string, so the HTTP layer can localize it for the caller's language instead
    of an exception message becoming API response text in whatever language the
    code that raised it happened to be written in.
    """

    def __init__(self, key: str, **params: object) -> None:
        super().__init__(key)
        self.key = key
        self.params = params


class CredentialHasher:
    """Argon2id hashing with Step 8's pinned parameters and SP093's dummy-verify path."""

    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if settings.credential_hash_algorithm != "argon2id":
            raise ValueError(
                f"CREDENTIAL_HASH_ALGORITHM is {settings.credential_hash_algorithm!r}; "
                "this module only implements argon2id (SP092/SP104)."
            )
        self._settings = settings
        self._hasher = PasswordHasher(
            time_cost=settings.credential_hash_time_cost,
            memory_cost=settings.credential_hash_memory_cost_kb,
            parallelism=settings.credential_hash_parallelism,
            type=Type.ID,  # Argon2id specifically, not Argon2i or Argon2d.
        )
        # Fixed for the process lifetime, from a random secret. See block above.
        self._decoy_hash = self._hasher.hash(secrets.token_urlsafe(32))

    def hash(self, credential: str) -> str:
        return self._hasher.hash(credential)

    def validate_strength(self, credential: str) -> None:
        """Minimal, server-side strength check (SP092 tampering row).

        Deliberately a length floor plus a "not entirely one character class"
        check rather than a composition ruleset: current guidance (NIST SP
        800-63B) favours length over composition rules, and no source document
        in this module specifies a composition policy — inventing one here would
        be a decision this step does not own.
        """
        if len(credential) < self._settings.min_credential_length:
            raise CredentialTooWeak(
                "auth.error.credentialTooShort", min=self._settings.min_credential_length
            )
        if len(set(credential)) < 4:
            raise CredentialTooWeak("auth.error.credentialTooRepetitive")

    def verify_or_dummy(self, stored_hash: str | None, supplied: str) -> bool:
        """[SP093] Verify, doing equal work whether or not the account exists.

        `stored_hash=None` means "no such account": the same Argon2id
        verification still runs, against the decoy, and the result is discarded.
        Callers pass the lookup result straight in; they never branch on
        existence before deciding whether to hash.
        """
        target = stored_hash if stored_hash is not None else self._decoy_hash
        try:
            self._hasher.verify(target, supplied)
        except argon2_exceptions.VerificationError:
            return False
        except argon2_exceptions.InvalidHashError:
            # A malformed stored hash is a data problem, not a wrong password.
            # Still return False (never raise into the response) so the failure
            # is indistinguishable from any other failed login.
            logger.error("stored credential hash is malformed; treating as a failed login")
            return False
        # Never report success for the decoy path, whatever the comparison did.
        return stored_hash is not None

    def needs_rehash(self, stored_hash: str) -> bool:
        return self._hasher.check_needs_rehash(stored_hash)


_hasher: CredentialHasher | None = None


def get_credential_hasher() -> CredentialHasher:
    """Process-wide hasher. Built once — the decoy hash must be stable."""
    global _hasher
    if _hasher is None:
        _hasher = CredentialHasher()
    return _hasher
