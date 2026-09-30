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
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import close_pool, get_pool, init_pool
from app.taxonomy_cache import refresh_taxonomy_cache
from app.routers import admin_commercial, admin_ops, campaigns, commercial, dev, discovery, enquiries, events, feed, first_run, listings, member_settings, notifications, opportunities, partnerships, payments, privacy, reviews, taxonomy, trust_safety, uploads, verification, workspace
from app.routers.commercial import run_commercial_lifecycle_pass
from app.routers.privacy import run_preference_detection_pass
from app.outbox import run_outbox_dispatch_pass
from app.services.opportunities import run_opportunity_expiry_pass  # [Backend A] posts past their last date
from app.routers.trust_safety import run_moderation_escalation_pass
from app.routers.listings import sync_credential_refs
from app.routers.notifications import notification_loop
from app.routers.verification import run_verification_expiry_pass, run_verification_image_cleanup
from app.services.contracts import run_contract_auto_release_pass
from app.services.profession_rules import refresh_profession_rules  # [Trust pack]
from app.services.trust_jobs import run_trust_pass  # [Trust pack]
from app.services.taste import run_taste_refresh_pass  # [Recommendations that learn]
# [IMP37 — Refactor B] integration edges: token/webhook API, middleware, webhook dispatch loop
from app.routers import integrations as integrations_router
# [IMP-B] contact control, service packages, saved searches, badges
from app.routers import badges as badges_router
from app.routers import contact as contact_router
from app.routers import packages as packages_router
from app.routers import saved_searches as saved_searches_router
from app.integrations import http_middleware as integration_middleware
from app.integrations.webhooks.dispatcher import webhook_loop

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
            await run_contract_auto_release_pass(get_pool())  # 14-day auto-release of submitted milestones
            await run_opportunity_expiry_pass(get_pool())  # [Backend A] active -> expired when the last date passes
            await refresh_taxonomy_cache(get_pool())  # keep the label cache current
            await run_trust_pass(get_pool())  # [Trust pack] paid on time, applicants waiting, council rules, credential expiry
            await run_taste_refresh_pass(get_pool())  # [Recommendations that learn] decay + actions since the last read
        except Exception:
            import logging

            logging.getLogger(__name__).exception("verification image cleanup pass failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await refresh_taxonomy_cache(get_pool())  # [Coordinator bug #2 fix] warm the taxonomy label cache before serving
    await refresh_profession_rules(get_pool())  # [Trust pack] council rules per taxonomy term
    # [TR021/TR006/TR008] Genuinely scheduled, not only dev-triggerable
    # endpoints — see each router's own header comment for why.
    notify_task = asyncio.create_task(notification_loop())
    credential_task = asyncio.create_task(credential_sync_loop())
    cleanup_task = asyncio.create_task(verification_cleanup_loop())
    webhook_task = asyncio.create_task(webhook_loop())  # [IMP37] outbound webhook fan-out + delivery
    yield
    notify_task.cancel()
    credential_task.cancel()
    cleanup_task.cancel()
    webhook_task.cancel()
    await close_pool()


app = FastAPI(title="Vyapar API", version="0.1.0", lifespan=lifespan)

from app.errors import register_error_handlers  # noqa: E402  [Refactor A] error envelope

register_error_handlers(app)

settings = get_settings()
# [IMP37] Idempotency-Key replay + per-token write audit. Installed BEFORE
# CORS so CORS stays outermost and replayed/refused responses keep CORS headers.
integration_middleware.install(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router)
# [FR11/FR22, one real upload implementation] served back statically — dev
# environment has no object-storage vendor, same honest gap already
# declared for verification-document images.
app.mount("/uploads", StaticFiles(directory=uploads.UPLOAD_DIR), name="uploads")

app.include_router(first_run.router)
app.include_router(taxonomy.router)  # [Backend A] categories -> skills tree, localized
from app.routers import profile as profile_router  # noqa: E402  [Backend A] one profile per member
app.include_router(profile_router.router)
app.include_router(member_settings.router)
# discovery.router's static "/v1/listings/search" path MUST be registered
# before listings.router's "/v1/listings/{listing_id}" — Starlette matches
# routes in registration order, and a dynamic path route registered first
# would otherwise swallow "/v1/listings/search" as if "search" were a
# listing id (a real routing bug, not a style preference).
app.include_router(discovery.router)
# [IMP-B] "/v1/listings/contact-preferences" is static — same rule as search above.
app.include_router(contact_router.router)
app.include_router(listings.router)
app.include_router(packages_router.router)
# feed.router's static "/v1/opportunities/feed" MUST be registered before
# opportunities.router's "/v1/opportunities/{opportunity_id}" — same
# static-before-dynamic ordering rule as discovery.router/listings.router above.
app.include_router(feed.router)
app.include_router(saved_searches_router.router)  # [IMP-B] static "/v1/opportunities/saved-searches"
app.include_router(opportunities.router)
app.include_router(badges_router.router)  # [IMP-B] /v1/members/{id}/badges
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
app.include_router(integrations_router.router)  # [IMP37] tokens, webhooks, /me
from app.routers import contracts as contracts_router  # noqa: E402  [Workstream D] contracts & milestone payments
app.include_router(contracts_router.router)
from app.routers import ai as ai_router  # noqa: E402  [IMP42 — Workstream C] AI drafts, shortlist, tips, proposal help
app.include_router(ai_router.router)
from app.routers import admin_console as admin_console_router  # noqa: E402  [IMP-ADMIN] ADR-012 Admin & Governance Console views
app.include_router(admin_console_router.router)
from app.routers import trust_pack as trust_pack_router  # noqa: E402  [Trust pack] VISION-2040 items 1-5
app.include_router(trust_pack_router.router)
from app.routers import voice as voice_router  # noqa: E402  [Voice interview] one question at a time, read back, draft
app.include_router(voice_router.router)
from app.routers import taste as taste_router  # noqa: E402  [Recommendations that learn] getMyTaste, resetMyTaste, moreLikeThis
app.include_router(taste_router.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
