# [TR006] VerifiedCredential read-only reference with hourly re-sync (FR06).
# Product owner's explicit instruction: "build the read-only reference
# against a dev stand-in for the Identity & Trust credential contract (a
# small local provider seeded with a couple of credentials, behind the
# same interface the real contract will use), including the 'last checked'
# cached state and revocation removal. Mark the provider clearly as a dev
# stand-in."
# Approach: `get_credential(member_id)` is the ONE call site any future
# real Identity & Trust integration replaces — everything in this file is
# an explicitly-labelled placeholder, never presented as real platform
# data. Revocation is simulated via `revoke()`, so the sync job's removal
# behaviour (TR006's own "revocation upstream removes the reference within
# the same 1-hour sync cycle") is actually exercisable in dev, not just
# theoretically correct.
# Traces to: FR06, TR006, SP006
from __future__ import annotations

from datetime import datetime, timezone

# [DEV STAND-IN — NOT the real Identity & Trust platform service] Seeded
# credentials for a couple of members, matching their real seeded
# capabilities so the feature demonstrates plausibly (m_kavita = legal/
# property_law, m_deepak = architecture/interior_design).
_DEV_CREDENTIALS: dict[str, dict] = {
    "m_kavita": {"id": "cred_kavita_bar", "claim": "Enrolled Advocate, Bar Council of Telangana", "issuer": "Bar Council of Telangana"},
    "m_deepak": {"id": "cred_deepak_coa", "claim": "Registered Architect, Council of Architecture", "issuer": "Council of Architecture (India)"},
}
_revoked: set[str] = set()


def get_credential(member_id: str) -> dict | None:
    """[Dev stand-in] Returns the member's claimed credential, or None.
    Structurally identical shape to what a real Identity & Trust read
    contract (ADR-013) would return — the one call site to swap later."""
    if member_id in _revoked:
        return None
    return _DEV_CREDENTIALS.get(member_id)


def revoke(member_id: str) -> None:
    """[Dev-only test hook] Simulates an upstream revocation so the sync
    job's removal behaviour is actually exercisable, not just theoretical."""
    _revoked.add(member_id)


def unrevoke(member_id: str) -> None:
    _revoked.discard(member_id)


def credential_ref_payload(cred: dict) -> dict:
    """[TR006] Exactly {id, claim, issuer, verified_at, last_checked} — no
    room for a MOD04 Counsel ExpertProfile field, per TR006's own
    structural-absence rule."""
    now = datetime.now(timezone.utc).isoformat()
    return {"id": cred["id"], "claim": cred["claim"], "issuer": cred["issuer"], "verified_at": now, "last_checked": now}
