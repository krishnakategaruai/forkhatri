# [Cross-cutting] FastAPI app wiring — one process, modular internally
# (MODULE-ARCHITECTURE-STANDARD §3), each router owning exactly one
# component's routes per 07-tech-reqs.md's component decomposition table.
# Approach: lifespan context manages the single asyncpg pool
# (init/close once, not per-request); CORS is scoped to the exact dev web
# origin (never "*") since credentials/cookies will eventually cross this
# boundary once the real fk_session cookie is wired in.
# Traces to: TR050 and every router's own TR (see each router file)
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import close_pool, get_pool, init_pool
from app.taxonomy_cache import refresh_taxonomy_cache
from app.routers import admin_commercial, admin_ops, campaigns, commercial, dev, discovery, enquiries, events, feed, first_run, listings, member_settings, notifications, opportunities, partnerships, payments, privacy, reviews, trust_safety, verification, workspace
from app.routers.commercial import run_commercial_lifecycle_pass
from app.routers.privacy import run_preference_detection_pass
from app.outbox import run_outbox_dispatch_pass
from app.routers.trust_safety import run_moderation_escalation_pass
from app.routers.listings import sync_credential_refs
from app.routers.notifications import notification_loop
from app.routers.verification import run_verification_expiry_pass, run_verification_image_cleanup

VERIFICATION_CLEANUP_INTERVAL_SECONDS = 3600

CREDENTIAL_SYNC_INTERVAL_SECONDS = 3600  # [TR006] hourly, per its own text


async def credential_sync_loop() -> None:
    while True:
        await asyncio.sleep(CREDENTIAL_SYNC_INTERVAL_SECONDS)
        try:
            await sync_credential_refs(get_pool())
        except Exception:
            import logging

            logging.getLogger(__name__).exception("credential sync pass failed")


async def verification_cleanup_loop() -> None:
    while True:
        await asyncio.sleep(VERIFICATION_CLEANUP_INTERVAL_SECONDS)
        try:
            await run_verification_image_cleanup(get_pool())
            await run_verification_expiry_pass(get_pool())  # [TR010]
            await run_moderation_escalation_pass(get_pool())  # [TR040/TR041]
            await run_commercial_lifecycle_pass(get_pool())  # [TR030/TR031/TR033/TR035/TR054] boosts, entitlement renewal/grace, campaigns
            await run_preference_detection_pass(get_pool())  # [TR038] derived-preference proposals
            await run_outbox_dispatch_pass(get_pool())  # [TR052] Search Bridge stand-in dispatch
            await refresh_taxonomy_cache(get_pool())  # keep the label cache current
        except Exception:
            import logging

            logging.getLogger(__name__).exception("verification image cleanup pass failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await refresh_taxonomy_cache(get_pool())  # [Coordinator bug #2 fix] warm the taxonomy label cache before serving
    # [TR021/TR006/TR008] Genuinely scheduled, not only dev-triggerable
    # endpoints — see each router's own header comment for why.
    notify_task = asyncio.create_task(notification_loop())
    credential_task = asyncio.create_task(credential_sync_loop())
    cleanup_task = asyncio.create_task(verification_cleanup_loop())
    yield
    notify_task.cancel()
    credential_task.cancel()
    cleanup_task.cancel()
    await close_pool()


app = FastAPI(title="Vyapar API", version="0.1.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(first_run.router)
app.include_router(member_settings.router)
# discovery.router's static "/v1/listings/search" path MUST be registered
# before listings.router's "/v1/listings/{listing_id}" — Starlette matches
# routes in registration order, and a dynamic path route registered first
# would otherwise swallow "/v1/listings/search" as if "search" were a
# listing id (a real routing bug, not a style preference).
app.include_router(discovery.router)
app.include_router(listings.router)
# feed.router's static "/v1/opportunities/feed" MUST be registered before
# opportunities.router's "/v1/opportunities/{opportunity_id}" — same
# static-before-dynamic ordering rule as discovery.router/listings.router above.
app.include_router(feed.router)
app.include_router(opportunities.router)
app.include_router(notifications.router)
app.include_router(enquiries.router)
app.include_router(verification.router)
app.include_router(verification.admin_router)
app.include_router(trust_safety.router)
app.include_router(trust_safety.admin_router)
app.include_router(reviews.router)
app.include_router(partnerships.router)
app.include_router(commercial.router)
app.include_router(commercial.admin_router)
app.include_router(payments.router)
app.include_router(workspace.router)
app.include_router(campaigns.router)
app.include_router(admin_commercial.router)
app.include_router(admin_ops.router)
app.include_router(admin_ops.internal_router)
app.include_router(privacy.router)
app.include_router(events.router)
app.include_router(admin_commercial.audit_router)
app.include_router(dev.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
