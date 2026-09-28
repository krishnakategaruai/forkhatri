"""Facts for ForKhatri's Members dashboard (/insights, open to every signed-in member).

    GET /internal/v1/insights/members

Called only by the platform Identity & Trust Service, server to server, never by
a browser. The caller proves itself with the same shared key Milavn presents to
the platform (`PLATFORM_SERVICE_KEY`), and a request that came through the public
edge (it carries X-Forwarded-For) is answered as if the route did not exist.
Only member id and city leave Milavn (migration 039); the browser sees counts.
"""

from __future__ import annotations

import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import text

from app.api.deps import AppSettings, DbSession

router = APIRouter(prefix="/internal/v1/insights", tags=["internal"], include_in_schema=False)


def platform_caller(
    request: Request,
    settings: AppSettings,
    x_forkhatri_service_key: Annotated[str | None, Header()] = None,
) -> None:
    if request.headers.get("x-forwarded-for") is not None:
        raise HTTPException(status_code=404)
    presented = (x_forkhatri_service_key or "").encode("utf-8")
    if not hmac.compare_digest(settings.platform_service_key.encode("utf-8"), presented):
        raise HTTPException(status_code=401, detail="Unknown service credentials.")


@router.get("/members", dependencies=[Depends(platform_caller)])
async def member_facts(db: DbSession) -> dict[str, Any]:
    rows = (await db.execute(text("SELECT member_id, city FROM milavn_profile.platform_member_facts()"))).all()
    return {"module": "milavn", "people": [{"member_id": str(m), "city": c} for m, c in rows]}
