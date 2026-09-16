# [TR008/SP008] Envelope encryption for `verification_records.identifier_enc`
# (FR08's GST/Udyam/PAN/Shops&Establishment identifiers). SP008's own
# Decision, quoted verbatim: "application-layer envelope encryption
# (AES-256-GCM) with the data-encryption key sourced from the deployment's
# secret manager (e.g. VERIFICATION_DOC_ENCRYPTION_KEY), never colocated
# with the database itself; key rotation is a manual, documented Step 13
# runbook item at V1 scale."
# Approach: `cryptography` (PyCA) is the standard, widely-audited Python
# library implementing exactly this algorithm — a NEW dependency this
# session, not previously named by package in Step 7/8, so it is flagged in
# 09a-external-dependencies.md with a supplementary scoped review rather
# than silently absorbed (this project's own shift-left rule). AES-256-GCM
# with a random 96-bit nonce per encryption, stored alongside the
# ciphertext (nonce||ciphertext||tag, base64-encoded) — never a fixed/
# reused nonce, which would break GCM's confidentiality guarantee.
# Traces to: FR08, TR008, SP008
from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


def _key_bytes() -> bytes:
    """[Config-placeholder convention] VERIFICATION_IDENTIFIER_ENCRYPTION_KEY
    is a CHANGE_ME placeholder in dev — padded/truncated to exactly 32
    bytes so AES-256 always has a valid key length even with the
    placeholder value, never a startup crash over a config value nobody
    has replaced yet in local dev."""
    raw = get_settings().verification_identifier_encryption_key.encode("utf-8")
    return (raw * (32 // max(len(raw), 1) + 1))[:32]


def encrypt_identifier(plaintext: str) -> str:
    aesgcm = AESGCM(_key_bytes())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_identifier(encoded: str) -> str:
    raw = base64.b64decode(encoded)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(_key_bytes())
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def mask_identifier(identifier: str) -> str:
    """[TR008] Last 4 characters only, on every non-owner/non-verification-
    operator-facing surface — the ONLY masked form any such response may include."""
    return f"{'•' * max(len(identifier) - 4, 0)}{identifier[-4:]}"
