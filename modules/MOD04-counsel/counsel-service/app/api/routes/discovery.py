"""Public discovery: expertise areas, search, a provider's profile, slots."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app import db
from app.components import ai, availability, places, providers
from app.errors import not_found
from app.i18n import AREA_NAME_COLUMNS, area_name, request_language
from app.identity import Actor, optional_actor

router = APIRouter(tags=["discovery"])


@router.get("/expertise")
async def expertise(request: Request):
    lang = request_language(request)
    rows = await db.fetch(
        "SELECT a.*, (SELECT count(DISTINCT pe.provider_id) FROM provider_expertise pe JOIN provider p ON p.member_id=pe.provider_id "
        "WHERE pe.area_id=a.id AND p.status='approved') AS providers FROM expertise_area a WHERE a.status='active' ORDER BY a.sort_order")
    return [{"id": r["id"], "name": area_name(dict(r), lang), "regulated": r["regulated"], "providers": r["providers"], "parent_id": r["parent_id"]} for r in rows]


async def _count_impressions(conn, results: list[dict], actor: Actor | None) -> None:
    """One search appearance per consultant per search (not the viewer's own card)."""
    ids = [UUID(c["id"]) for c in results if not (actor and str(actor.member_id) == c["id"])]
    if ids:
        await conn.execute(
            "INSERT INTO search_impression (provider_id, day, count) SELECT unnest($1::uuid[]), current_date, 1 "
            "ON CONFLICT (provider_id, day) DO UPDATE SET count = search_impression.count + 1", ids)


@router.get("/places")
async def city_list(request: Request):
    """Listed cities for "near me" and the consultant's city picker."""
    return {"cities": places.listing(request_language(request)), "nearby_km": places.NEARBY_KM}


@router.get("/search")
async def search(
    request: Request, q: str = "", area: str | None = None, max_price: int | None = Query(default=None, ge=0),
    min_price: int | None = Query(default=None, ge=0), language: str | None = None, verified: bool = False,
    duration_max: int | None = None, sort: str = Query(default="best", pattern="^(" + "|".join(providers.SORTS) + "|price)$"),
    now: bool = False, min_rating: float | None = Query(default=None, ge=1, le=5), near: str | None = None, nearby: bool = False,
    within_hours: int | None = Query(default=None, ge=1, le=168), actor: Actor | None = Depends(optional_actor),
):
    async with db.pool().acquire() as conn:
        results = await providers.search(
            conn, lang=request_language(request), q=q, area=area, max_price_minor=max_price * 100 if max_price else None,
            min_price_minor=min_price * 100 if min_price else None, language=language, verified_only=verified,
            duration_max=duration_max, sort=sort, viewer_id=actor.member_id if actor else None, available_now=now,
            min_rating=min_rating, near=near, nearby_only=nearby, within_hours=within_hours)
        await _count_impressions(conn, results, actor)
    return results


class Need(BaseModel):
    text: str


@router.post("/understand")
async def understand(body: Need, request: Request, actor: Actor | None = Depends(optional_actor)):
    parsed = await ai.understand(body.text[:600])
    async with db.pool().acquire() as conn:
        results = await providers.search(
            conn, lang=request_language(request), q=" ".join(parsed.get("keywords") or []), area=(parsed.get("areas") or [None])[0],
            max_price_minor=(parsed.get("max_price") or 0) * 100 or None, duration_max=parsed.get("duration_max"),
            viewer_id=actor.member_id if actor else None)
        if not results and parsed.get("areas"):
            results = await providers.search(conn, lang=request_language(request), area=parsed["areas"][0], viewer_id=actor.member_id if actor else None)
        if not results and parsed.get("keywords"):
            results = await providers.search(conn, lang=request_language(request), q=parsed["keywords"][0], viewer_id=actor.member_id if actor else None)
        await _count_impressions(conn, results, actor)
    return {"filters": parsed, "results": results}


@router.get("/home")
async def home(request: Request, actor: Actor | None = Depends(optional_actor)):
    lang = request_language(request)
    async with db.pool().acquire() as conn:
        featured = await providers.search(conn, lang=lang, viewer_id=actor.member_id if actor else None, limit=8)
        recent = []
        if actor:
            rows = await conn.fetch(
                "SELECT DISTINCT ON (provider_id) provider_id FROM booking WHERE seeker_id=$1 AND status='completed' ORDER BY provider_id, completed_at DESC LIMIT 6", actor.member_id)
            recent = [c for r in rows if (c := await providers.card(conn, r["provider_id"], lang, actor.member_id))]
        areas = await expertise(request)
    return {"featured": featured, "recent": recent, "areas": [a for a in areas if a["providers"]][:12]}


@router.get("/providers/{provider_id}")
async def provider_profile(provider_id: UUID, request: Request, actor: Actor | None = Depends(optional_actor)):
    async with db.pool().acquire() as conn:
        p = await providers.profile(conn, provider_id, request_language(request), actor.member_id if actor else None)
    if not p or (p["status"] != "approved" and not (actor and (actor.member_id == provider_id or actor.is_admin))):
        raise not_found("provider")
    if p["status"] == "approved" and not (actor and actor.member_id == provider_id):
        # A one-way, per-day key: counts unique viewers without storing who they are.
        who = str(actor.member_id) if actor else f"{request.client.host if request.client else ''}|{request.headers.get('user-agent', '')}"
        key = hashlib.sha256(f"{date.today().isoformat()}|{provider_id}|{who}".encode()).hexdigest()[:32]
        await db.execute("INSERT INTO profile_view (provider_id, viewer_key) VALUES ($1, $2) ON CONFLICT DO NOTHING", provider_id, key)
    return p


@router.get("/services/{service_id}")
async def service(service_id: UUID, request: Request, actor: Actor | None = Depends(optional_actor)):
    lang = request_language(request)
    s = await db.fetchrow(
        f"SELECT s.*, {AREA_NAME_COLUMNS}, a.regulated, m.display_name AS provider_name, p.timezone AS provider_timezone, p.photo_url "
        "FROM service s JOIN expertise_area a ON a.id=s.area_id JOIN provider p ON p.member_id=s.provider_id JOIN member m ON m.member_id=p.member_id WHERE s.id=$1", service_id)
    if not s:
        raise not_found("service")
    d = dict(s)
    d["area_name"] = area_name(d, lang)
    rule = await db.fetchrow("SELECT disclaimer_key, recording_allowed FROM compliance_rule WHERE area_id=$1 ORDER BY (jurisdiction='*') LIMIT 1", d["area_id"])
    d["disclaimer_key"] = rule["disclaimer_key"] if rule else None
    d["packages"] = db.rows(await db.fetch("SELECT id, sessions, price_minor, valid_days FROM package WHERE service_id=$1 AND active ORDER BY sessions", service_id))
    d["follow_up_eligible"] = bool(actor and await db.fetchval(
        "SELECT 1 FROM booking WHERE seeker_id=$1 AND provider_id=$2 AND status='completed'", actor.member_id, d["provider_id"]))
    d["available_now"] = bool(d.get("instant_allowed") and await db.fetchval("SELECT 1 FROM provider WHERE member_id=$1 AND available_until > now()", d["provider_id"]))
    if rule and not rule["recording_allowed"]:
        d["recording_allowed"] = False
    from app.components import money
    async with db.pool().acquire() as conn:
        d["quote"] = (await money.quote(conn, d["price_minor"], d["currency"])).as_dict()
        d["cancellation_policy"] = await money.cancellation_policy(conn)
    return d


@router.get("/services/{service_id}/slots")
async def slots(service_id: UUID, from_date: date | None = Query(default=None, alias="from"), days: int = 14):
    s = await db.fetchrow("SELECT * FROM service WHERE id=$1 AND status='active'", service_id)
    if not s:
        raise not_found("service")
    start = from_date or datetime.now(timezone.utc).date()
    async with db.pool().acquire() as conn:
        out = await availability.slots(conn, s["provider_id"], dict(s), start, min(days, 45))
    return {"slots": [d.isoformat() for d in out], "duration_min": s["duration_min"]}
