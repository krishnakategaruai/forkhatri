"""MangalyService application entrypoint.

# [TR017/SP017] A deployment whose runtime role owns tables must fail at boot,
# not serve traffic with every RLS policy silently disabled.
# Approach: SP017's own threshold for the non-owning-role check is "an automated
# check in CI/CD deploy pipeline (not just a one-time manual query) — re-run on
# every deploy, not only at initial setup". Running it in the lifespan startup
# hook satisfies that in the strongest available way: it runs on every process
# start in every environment, including ones no CI pipeline touched, and it
# refuses to come up rather than degrading quietly.
#
# One FastAPI process, one package per component (CODING-GUIDE.md §2). Routers
# are registered here and nowhere else; `app/api/` holds routers only, with no
# business logic.
# Traces to: TR017, SP017, SP104, CODING-GUIDE.md §2.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    communication,
    connection,
    discovery,
    home_circle,
    media,
    profile,
)
from app.config.settings import get_settings
from app.db.engine import (
    assert_non_owning_role,
    create_engine,
    create_session_factory,
    set_process_session_factory,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings)

    # Release-blocking configuration confirmation, checked at boot. Raises
    # NonOwningRoleViolation and aborts startup if the role owns any table.
    await assert_non_owning_role(engine)

    if settings.db_pool_mode == "transaction":
        # [SP017 / BLK-08-01] Transaction-mode pooling is the case where a plain
        # `SET` leaks context across requests. This service only ever uses
        # `SET LOCAL` (see app/db/session.py), so the mode is safe — but SP017
        # requires that be proven against a real pooler, not asserted. Log it
        # loudly so an operator who flips this flag sees the open blocker.
        logger.warning(
            "DB_POOL_MODE=transaction. SET LOCAL-only discipline is enforced in code, "
            "but SP017/BLK-08-01 requires an integration test against the real pooler "
            "before this configuration is release-approved."
        )

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    set_process_session_factory(app.state.session_factory)
    logger.info(
        "MangalyService started against %s:%s/%s",
        settings.db_host,
        settings.db_port,
        settings.db_name,
    )
    try:
        yield
    finally:
        # [ForKhatri TR15] The Identity Bridge's shared HTTP client to the
        # platform Identity & Trust Service.
        from app.components.identity_bridge import interface as identity

        await identity.aclose_platform_client()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MangalyService",
        description=(
            "MOD03 Mangaly — matrimonial module. One process, one package per "
            "component (architecture.md §2)."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # [SP090] The web client is a separate origin in development, and the
    # session cookie is HttpOnly, so credentialed CORS is required for it to be
    # sent at all. Origins are an explicit allow-list — never "*", which the
    # spec forbids alongside credentials anyway.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Idempotency-Key", "X-Mangaly-Language"],
    )

    # Feature routers are registered here as each TR lands.
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(home_circle.router)
    app.include_router(discovery.router)
    app.include_router(connection.router)
    app.include_router(communication.router)
    app.include_router(media.router)

    return app


app = create_app()
