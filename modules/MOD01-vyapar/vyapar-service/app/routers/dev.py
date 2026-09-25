# [Dev-only, not a business FR] Backs the "Choose dev member" switcher the
# task brief explicitly allows (it selects an identity the platform has
# already authenticated in a real deployment — it is not a login form, and
# creates no session/credential). Lists the 16 seeded members so the product
# owner can switch between them while testing.
# Approach: a single read-only GET against vyapar_identity.members, gated so
# it only ever returns non-sensitive display fields (id, display_name,
# locality) — never phone or any other PII — since this list is visible to
# whoever is currently testing, not just the member themself.
# Traces to: task brief's "dev member switcher" instruction (not an FR)
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.db import get_pool
from app.errors import ERROR_RESPONSES

router = APIRouter(prefix="/v1/dev", tags=["dev"], responses=ERROR_RESPONSES)


class DevMemberOut(BaseModel):
    id: str
    display_name: str
    locality: str | None
    is_operator: bool


class SentOut(BaseModel):
    sent: int


class UpdatedOut(BaseModel):
    updated: int


class DevRevokedOut(BaseModel):
    revoked: str


class VerificationJobsOut(BaseModel):
    reminded: int
    expired: int
    images_cleaned: int


class ModerationJobsOut(BaseModel):
    escalated: int
    appeals_delayed: int
    suspension_rows_lifted: int


@router.get("/members", response_model=list[DevMemberOut], operation_id="listDevMembers", summary="List development members (dev only)")
async def list_dev_members() -> list[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Operator context so RLS's members_self_or_operator policy
            # doesn't narrow this to one row — this endpoint is dev-tooling,
            # not a member-facing read, so it deliberately runs before/
            # without a per-caller authz_context. set_config(..., true) is
            # transaction-scoped (SET LOCAL-equivalent) — it must be set
            # and read inside the SAME transaction, or it resets before the
            # SELECT runs (asyncpg auto-wraps each bare statement in its own
            # implicit transaction otherwise).
            await conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")
            rows = await conn.fetch(
                "SELECT id, display_name, locality, is_operator FROM vyapar_identity.members ORDER BY display_name"
            )
    return [dict(r) for r in rows]


# [TR021 — dev-only trigger] Runs the FR21 matcher/digest passes on demand,
# so this session can test notification delivery without waiting for
# NOTIFY_MATCHER_INTERVAL_SECONDS — the real, scheduled `notification_loop()`
# (app/main.py's lifespan) is what runs in a genuine deployment; this is
# strictly a dev convenience on top of it, not a replacement for it.
@router.post("/run-notification-matcher", response_model=SentOut, operation_id="runNotificationMatcher", summary="Run the notification matcher now (dev only)")
async def run_notification_matcher() -> dict:
    from app.services.notifications import run_strong_match_pass

    return {"sent": await run_strong_match_pass(get_pool())}


@router.post("/run-notification-digest", response_model=SentOut, operation_id="runNotificationDigest", summary="Run the notification digest now (dev only)")
async def run_notification_digest() -> dict:
    from app.services.notifications import run_digest_pass

    return {"sent": await run_digest_pass(get_pool())}


# [TR006 — dev-only trigger] Runs the FR06 credential re-sync on demand —
# the real, scheduled `credential_sync_loop()` (app/main.py's lifespan) is
# what runs in a genuine deployment; this is a dev convenience on top.
@router.post("/run-credential-sync", response_model=UpdatedOut, operation_id="runCredentialSync", summary="Run the credential sync now (dev only)")
async def run_credential_sync() -> dict:
    from app.services.listings import sync_credential_refs

    return {"updated": await sync_credential_refs(get_pool())}


@router.post("/revoke-credential/{member_id}", response_model=DevRevokedOut, operation_id="devRevokeCredential", summary="Revoke a member's platform credential (dev only)")
async def dev_revoke_credential(member_id: str) -> dict:
    """[Dev-only test hook] Simulates an upstream Identity & Trust
    revocation so FR06's removal behaviour is actually exercisable."""
    from app import identity_trust_stub

    identity_trust_stub.revoke(member_id)
    return {"revoked": member_id}


# [TR010/TR008 — dev-only trigger] runs the verification expiry/reminder
# pass and the 30-day image cleanup on demand.
@router.post("/run-verification-jobs", response_model=VerificationJobsOut, operation_id="runVerificationJobs", summary="Run verification jobs now (dev only)")
async def run_verification_jobs() -> dict:
    from app.services.verification import run_verification_expiry_pass, run_verification_image_cleanup

    expiry = await run_verification_expiry_pass(get_pool())
    cleaned = await run_verification_image_cleanup(get_pool())
    return {**expiry, "images_cleaned": cleaned}


# [TR040/TR041 — dev-only trigger] escalation / appeal-delay / suspension-lift pass.
@router.post("/run-moderation-jobs", response_model=ModerationJobsOut, operation_id="runModerationJobs", summary="Run moderation jobs now (dev only)")
async def run_moderation_jobs() -> dict:
    from app.services.trust_safety import run_moderation_escalation_pass

    return await run_moderation_escalation_pass(get_pool())


# [TR030/TR031 — dev-only trigger] promotion lifecycle pass (payment window, completion, pause + credit).
@router.post("/run-commercial-jobs", response_model=dict[str, int], operation_id="runCommercialJobs", summary="Run commercial jobs now (dev only)")
async def run_commercial_jobs() -> dict:
    from app.services.commercial import run_commercial_lifecycle_pass

    return await run_commercial_lifecycle_pass(get_pool())
