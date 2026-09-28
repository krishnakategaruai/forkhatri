"""Facts for ForKhatri's Members dashboard (/insights, open to every signed-in member).

    GET /internal/v1/insights/members

Called only by the platform Identity & Trust Service, server to server, never by
a browser. The caller proves itself with the same shared key Mangaly presents to
the platform (`PLATFORM_SERVICE_KEY`), and a request that came through the public
edge (it carries X-Forwarded-For) is answered as if the route did not exist.

The platform turns these rows into totals; the browser only ever receives counts.
See migration 057 for exactly which columns leave Mangaly.
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
    rows = (await db.execute(text("SELECT * FROM mangaly_operations.platform_member_facts()"))).mappings()
    people = [
        {
            "member_id": str(r["account_id"]),
            "kind": r["kind"],
            "gender": r["gender"],
            "date_of_birth": r["date_of_birth"].isoformat() if r["date_of_birth"] else None,
            "city": r["city"],
            "profile_status": r["profile_status"],
            "looking_for": r["looking_for"],
            "marital_status": r["marital_status"],
            "mother_tongue": r["mother_tongue"],
        }
        for r in rows
    ]
    return {"module": "mangaly", "people": people}
