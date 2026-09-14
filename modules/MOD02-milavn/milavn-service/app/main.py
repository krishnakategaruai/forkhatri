"""Milavn service entrypoint.

# [architecture.md §2, MODULE-ARCHITECTURE-STANDARD §3/§4] One FastAPI
# process, one package per component; routers registered here and nowhere
# else. Boot refuses to serve if the runtime DB role owns any milavn table,
# because every RLS policy would then be a silent no-op.
# Traces to: TR16, TR-CROSSCUT-03, architecture.md §3.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import identity, profile
from app.config.settings import get_settings
from app.db.engine import (
    assert_non_owning_role,
    create_engine,
    create_session_factory,
    get_process_session_factory,
    set_process_session_factory,
)
from app.idempotency import IdempotencyConflict
from app.rate_limiting import RateLimitExceeded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings)
    await assert_non_owning_role(engine)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    set_process_session_factory(app.state.session_factory)
    from app.components.notification import interface as notification  # subscribers

    notification.register_subscribers()
    # [TR17/TR52] The two scheduled jobs this module owns (24h reminders,
    # co-participation circle suggestions). No platform scheduler is named
    # yet, so they run as an in-process loop; a platform job runner can call
    # the same functions later.
    jobs = asyncio.create_task(_scheduled_jobs())
    logger.info("Milavn service started against %s:%s/%s", settings.db_host, settings.db_port, settings.db_name)
    try:
        yield
    finally:
        jobs.cancel()
        await engine.dispose()


async def _scheduled_jobs() -> None:
    from app.components.circle import interface as circle
    from app.components.notification import interface as notification

    tick = 0
    while True:
        try:
            await asyncio.sleep(600)
            sent = await notification.send_reminders()
            if sent:
                logger.info("reminders sent: %s", sent)
            tick += 1
            if tick % 6 == 0:  # hourly
                factory = get_process_session_factory()
                async with factory() as s, s.begin():
                    from app.db.session import set_internal_service_context

                    await set_internal_service_context(s)
                    created = await circle.run_suggestion_job(s)
                    if created:
                        logger.info("circle suggestions created: %s", created)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — a failed run retries next interval (TR17)
            logger.exception("scheduled job failed")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Milavn",
        description="MOD02 Milavn — real-world participation network. One package per component (architecture.md §2).",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "module": "MOD02-milavn"}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Idempotency-Key", "X-Milavn-Language", "X-Milavn-Member-Id"],
    )

    @app.middleware("http")
    async def bind_language(request: Request, call_next):  # noqa: ANN001, ANN202
        # [FR002/ADR-010] One language per request, readable anywhere below.
        from app.i18n import current_language, resolve_language

        token = current_language.set(resolve_language(request.headers.get("x-milavn-language") or request.headers.get("accept-language")))
        try:
            return await call_next(request)
        finally:
            current_language.reset(token)

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limited(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        from app.i18n import resolve_language, translate

        lang = resolve_language(request.headers.get("x-milavn-language"))
        secs = exc.result.retry_after_seconds
        return JSONResponse(
            status_code=429,
            content={"detail": translate("common.rateLimited", lang, seconds=secs)},
            headers={"Retry-After": str(secs)},
        )

    @app.exception_handler(IdempotencyConflict)
    async def _idem_conflict(request: Request, exc: IdempotencyConflict) -> JSONResponse:
        from app.i18n import resolve_language, translate

        lang = resolve_language(request.headers.get("x-milavn-language"))
        return JSONResponse(status_code=409, content={"detail": translate("common.idempotencyConflict", lang)})

    app.include_router(identity.router)
    app.include_router(profile.router)
    _include_feature_routers(app)

    media_root: Path = settings.media_root
    media_root.mkdir(exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_root), name="media")
    return app


def _include_feature_routers(app: FastAPI) -> None:
    """Feature routers land here as each FR is implemented (09-implementation.md)."""
    from app.api.routes import discovery

    app.include_router(discovery.router)
    try:
        from app.api.routes import occurrences

        app.include_router(occurrences.router)
    except ImportError:
        pass
    for name in ("circles", "calendar", "trust", "privacy", "connect", "public", "notifications", "organizer", "safety", "feedback", "admin", "conversation", "chat"):
        try:
            module = __import__(f"app.api.routes.{name}", fromlist=["router"])
        except ImportError:
            continue
        app.include_router(module.router)
        for extra in ("presence_router", "ws_router"):
            if hasattr(module, extra):
                app.include_router(getattr(module, extra))


app = create_app()
