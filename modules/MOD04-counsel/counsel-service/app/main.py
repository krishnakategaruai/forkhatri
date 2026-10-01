"""Counsel (MOD04) service entrypoint. One FastAPI process, one package per
component, routers registered here only. Runs locally with mock payment and
notification adapters; real providers plug in behind the same interfaces."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import db, identity
from app.api.routes import admin, bookings, discovery, internal, me, offers, payments, provide, requests, room
from app.components import bookings as booking_rules
from app.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("counsel")


async def _housekeeping() -> None:
    from app.components import badges

    tick = 0
    while True:
        try:
            async with db.tx() as conn:
                n = await booking_rules.expire_stale(conn)
                await booking_rules.auto_progress(conn)
                await booking_rules.send_reminders(conn)
                from app.components import purchases
                await purchases.expire(conn)
                # Milestones that depend on time or reviews (tenure, ratings) are recomputed every 10 minutes.
                if tick % 10 == 0:
                    await badges.refresh_all(conn)
                if tick % 60 == 0:
                    from app.components import privacy
                    await privacy.apply_retention(conn)
            from app.components import outbound
            await outbound.dispatch_once()
            tick += 1
            if n:
                log.info("expired %d abandoned checkouts", n)
        except Exception as exc:  # keep the loop alive
            log.warning("housekeeping: %s", exc)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    if s.payment_provider == "mock" and s.api_host not in ("127.0.0.1", "localhost"):
        raise RuntimeError("PAYMENT_PROVIDER=mock is only allowed for a loopback-bound development API")
    if s.api_host not in ("127.0.0.1", "localhost") and "CHANGE_ME" in s.payout_encryption_key:
        raise RuntimeError("PAYOUT_ENCRYPTION_KEY must be set outside local development")
    if s.api_host not in ("127.0.0.1", "localhost") and "CHANGE_ME" in s.file_encryption_key:
        raise RuntimeError("FILE_ENCRYPTION_KEY must be set outside local development")
    await db.open_pool()
    s.storage_path.mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(_housekeeping())
    log.info("Counsel API on %s:%s (db %s)", s.api_host, s.api_port, s.db_name)
    try:
        yield
    finally:
        task.cancel()
        await identity.aclose()
        await db.close_pool()


app = FastAPI(title="Counsel API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=get_settings().cors_allowed_origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

for r in (me.router, discovery.router, provide.router, bookings.router, requests.router, offers.router, payments.router, room.router, admin.router, internal.router):
    app.include_router(r)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": {"code": "internal", "message": "Something went wrong."}})


@app.get("/media/photos/{member_id}/{name}")
async def photo(member_id: str, name: str):
    """Profile photos are public by design (people choose people)."""
    from fastapi.responses import FileResponse

    from app.components import storage

    path = storage.path_for(f"public/photos/{member_id}/{name}")
    if not path.is_file():
        return JSONResponse(status_code=404, content={"detail": {"code": "not_found", "message": "not found"}})
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/")
async def root():
    return {"service": "counsel", "ok": True}
