"""ForKhatri Identity & Trust Service entrypoint (ARCHITECTURE.md ADR-004).

Run without `--reload` on Windows (an orphaned reloader child keeps serving
stale code); restart the process after code changes.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import account, admin, auth, insights, internal, members, modules
from app.config.settings import Settings, get_settings
from app.db.engine import assert_non_owning_role, create_engine, create_session_factory
from app.errors import DomainError
from app.rate_limiting import RateLimitExceeded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("identity")

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings)
    await assert_non_owning_role(engine)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    logger.info("Identity service started against %s:%s/%s", settings.db_host, settings.db_port, settings.db_name)
    expiry = asyncio.create_task(_end_due_suspensions(app.state.session_factory))
    from app.components.deletion import interface as deletion

    erasure = asyncio.create_task(deletion.retry_loop(app.state.session_factory, settings))
    try:
        yield
    finally:
        expiry.cancel()
        erasure.cancel()
        await engine.dispose()


async def _end_due_suspensions(factory) -> None:  # noqa: ANN001
    """Suspensions with an end date end on their own (governance ADR-012); checked every minute."""
    from app.components.governance import interface as governance

    while True:
        try:
            async with factory() as db:
                ended = await governance.expire_due_suspensions(db)
                await db.commit()
            if ended:
                logger.info("Ended %s suspension(s) that reached their end date.", ended)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - a failed sweep retries next minute
            logger.exception("Suspension expiry sweep failed")
        await asyncio.sleep(60)


def _app_path(request: Request) -> str:
    """The path as this app routes it. Behind the deployment edge the service runs with
    `--root-path /api/identity`, and `request.url.path` then carries that prefix; a
    prefix-sensitive check on the raw URL would silently never match (found in the
    deployment rehearsal: the Origin guard was skipped)."""
    path = request.url.path
    root = request.scope.get("root_path") or ""
    if root and (path == root or path.startswith(root + "/")):
        path = path[len(root):] or "/"
    return path


def _error(status_code: int, code: str, message: str, **extra: object) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": {"code": code, "message": message, **extra}})


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="ForKhatri Identity & Trust Service",
        description="Canonical member identity, sessions and the module registry. Contract: docs/ParentApp/07-tech-reqs.md.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def origin_guard(request: Request, call_next):  # noqa: ANN001, ANN202
        # [TR20] The session cookie's SameSite policy (configurable, "lax" by
        # default) is the first CSRF layer; this Origin allow-list is the second.
        path = _app_path(request)
        origin = request.headers.get("origin")
        if (
            request.method in _UNSAFE_METHODS
            and path.startswith(("/v1/", "/dev/v1/"))
            and origin is not None
            and origin not in settings.cors_allowed_origins
        ):
            return _error(403, "origin_not_allowed", "This origin may not call the ForKhatri identity API.")
        response = await call_next(request)
        if path.startswith(("/v1/", "/internal/", "/dev/")):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Accept-Language"],
        expose_headers=["Retry-After"],
    )

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return _error(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limited(_: Request, exc: RateLimitExceeded) -> JSONResponse:
        response = _error(
            429, "rate_limited", "Too many attempts. Please wait a moment.", retry_after=exc.retry_after_seconds
        )
        response.headers["Retry-After"] = str(exc.retry_after_seconds)
        return response

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [".".join(str(p) for p in err.get("loc", ())[1:]) for err in exc.errors()]
        return _error(422, "validation_failed", "Some details are missing or invalid.", fields=fields)

    @app.get("/health", tags=["ops"])
    async def health(request: Request) -> dict[str, str]:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "service": "identity"}

    app.include_router(auth.router)
    app.include_router(members.router)
    app.include_router(account.router)
    app.include_router(modules.router)
    app.include_router(internal.router)
    app.include_router(insights.router)
    app.include_router(admin.router)
    if settings.dev_tools_active:
        # Imported only here: the package is not shipped in the production image (.dockerignore).
        from app.dev_tools.router import router as dev_router

        app.include_router(dev_router)
        logger.warning("Development tools are mounted at /dev/v1 (ENVIRONMENT=development, DEV_TOOLS_ENABLED=true).")
    return app


app = create_app()
