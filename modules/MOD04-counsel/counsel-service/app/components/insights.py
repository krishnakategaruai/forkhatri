"""How a consultant is found, and what would help them be found more.

Built from the discovery research (1 Oct 2026):
  * Fiverr and Upwork show sellers a funnel of search impressions, profile
    clicks and orders; Counsel shows appearances in search, unique profile
    views and bookings for the last 30 days, against the 30 days before.
  * Upwork requires a 100% complete profile before its Rising Talent and Top
    Rated badges; Counsel shows a profile strength score whose items are the
    same signals the search ranking and filters use.
  * Zocdoc publishes how its search orders results; Counsel tells the
    consultant their current place in their main area and what moves it.
Every number is computed from real rows; nothing is estimated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.components import places, providers


async def visibility(conn, provider_id: UUID) -> dict:
    r = await conn.fetchrow(
        """
        SELECT
          (SELECT coalesce(sum(count),0) FROM search_impression WHERE provider_id=$1 AND day > current_date - 30)  AS impressions,
          (SELECT coalesce(sum(count),0) FROM search_impression WHERE provider_id=$1 AND day <= current_date - 30 AND day > current_date - 60) AS impressions_prev,
          (SELECT count(*) FROM profile_view WHERE provider_id=$1 AND day > current_date - 30)                     AS views,
          (SELECT count(*) FROM profile_view WHERE provider_id=$1 AND day <= current_date - 30 AND day > current_date - 60) AS views_prev,
          (SELECT count(*) FROM booking WHERE provider_id=$1 AND created_at > now() - interval '30 days'
                                          AND status NOT IN ('pending_payment','expired'))                          AS bookings,
          (SELECT count(*) FROM booking WHERE provider_id=$1 AND created_at <= now() - interval '30 days' AND created_at > now() - interval '60 days'
                                          AND status NOT IN ('pending_payment','expired'))                          AS bookings_prev
        """, provider_id)
    d = dict(r)
    d["conversion_percent"] = round(100 * d["bookings"] / d["views"]) if d["views"] else None
    return d


async def rank(conn, provider_id: UUID, lang: str) -> dict | None:
    """The consultant's place in "Best match" for their main area, as a seeker sees it."""
    area = await conn.fetchrow(
        "SELECT pe.area_id FROM provider_expertise pe WHERE pe.provider_id=$1 ORDER BY pe.is_primary DESC, pe.years DESC LIMIT 1", provider_id)
    if not area:
        return None
    ids = [c["id"] for c in await providers.search(conn, lang=lang, area=area["area_id"], limit=500)]
    if str(provider_id) not in ids:
        return {"area_id": area["area_id"], "position": None, "of": len(ids)}
    return {"area_id": area["area_id"], "position": ids.index(str(provider_id)) + 1, "of": len(ids)}


async def strength(conn, provider_id: UUID) -> dict:
    """Profile strength: each item is something search, filters or seekers use."""
    p = await conn.fetchrow("SELECT * FROM provider WHERE member_id=$1", provider_id)
    n = await conn.fetchrow(
        """
        SELECT
          (SELECT count(*) FROM verification WHERE provider_id=$1)                                    AS verified,
          (SELECT count(*) FROM provider_evidence WHERE provider_id=$1 AND status <> 'rejected')       AS evidence,
          (SELECT count(*) FROM service WHERE provider_id=$1 AND status='active')                      AS services,
          (SELECT count(*) FROM availability_rule WHERE provider_id=$1)                                AS rules,
          (SELECT count(*) FROM service WHERE provider_id=$1 AND status='active'
                                          AND (question_price_minor IS NOT NULL OR instant_allowed))   AS extras,
          (SELECT count(*) FROM review WHERE provider_id=$1 AND NOT hidden)                            AS reviews
        """, provider_id)
    next_slot = await providers.next_slot(conn, provider_id)
    soon = bool(next_slot and (datetime.fromisoformat(next_slot) - datetime.now(timezone.utc)).days < 7)
    links = [v for v in (p["links"] or {}).values() if v]
    items = [
        ("photo", bool(p["photo_url"]), "/provide/profile"),
        ("headline", len((p["headline"] or "").strip()) >= 40, "/provide/profile"),
        ("intro", len((p["intro"] or "").strip()) >= 300, "/provide/profile"),
        ("city", places.resolve(p["city"]) is not None, "/provide/profile"),
        ("languages", len(p["languages"] or []) >= 2, "/provide/profile"),
        ("evidence", n["evidence"] >= 2, "/provide/profile#evidence"),
        ("verified", n["verified"] >= 2, "/provide/profile#evidence"),
        ("links", len(links) >= 1, "/provide/profile"),
        ("service", n["services"] >= 1, "/provide/services"),
        ("slot_soon", soon, "/provide/availability"),
        ("extras", n["extras"] >= 1, "/provide/services"),
    ]
    done = sum(1 for _, ok, _ in items if ok)
    return {
        "percent": round(100 * done / len(items)),
        "items": [{"id": i, "done": ok, "href": href} for i, ok, href in items],
        "reviews": n["reviews"], "prior_reviews": providers.PRIOR_REVIEWS,
    }
