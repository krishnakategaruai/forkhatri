"""Providers: the public card and profile, reputation, and deterministic
search + explainable ranking (relevance + trust + reliability + suitability).
No LLM or vector store is needed for normal discovery."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID

from app import db
from app.components import places
from app.i18n import area_name

VERIFICATION_DIMENSIONS = ("identity", "contact", "experience", "qualification", "certification", "registration", "business", "portfolio")


def _fold(s: str) -> str:
    return re.sub(r"[^a-z0-9ऀ-ॿఀ-౿ ]+", " ", (s or "").lower()).strip()


async def reputation(conn, provider_id: UUID) -> dict:
    r = await conn.fetchrow(
        """
        SELECT
          (SELECT count(*) FROM booking WHERE provider_id=$1 AND status='completed')                          AS completed,
          (SELECT count(DISTINCT seeker_id) FROM booking WHERE provider_id=$1 AND status='completed')         AS clients,
          (SELECT count(*) FROM (SELECT seeker_id FROM booking WHERE provider_id=$1 AND status='completed'
                                 GROUP BY seeker_id HAVING count(*)>1) x)                                     AS repeat_clients,
          (SELECT count(*) FROM booking WHERE provider_id=$1 AND status IN ('cancelled_by_provider','no_show_provider')) AS provider_cancels,
          (SELECT count(*) FROM booking WHERE provider_id=$1 AND status NOT IN ('pending_payment','expired'))  AS total,
          (SELECT round(avg(overall)::numeric,1) FROM review WHERE provider_id=$1 AND NOT hidden)              AS rating,
          (SELECT count(*) FROM review WHERE provider_id=$1 AND NOT hidden)                                     AS review_count,
          (SELECT round(avg(expertise)::numeric,1) FROM review WHERE provider_id=$1 AND NOT hidden)             AS r_expertise,
          (SELECT round(avg(communication)::numeric,1) FROM review WHERE provider_id=$1 AND NOT hidden)         AS r_communication,
          (SELECT round(avg(professionalism)::numeric,1) FROM review WHERE provider_id=$1 AND NOT hidden)       AS r_professionalism,
          (SELECT round(avg(punctuality)::numeric,1) FROM review WHERE provider_id=$1 AND NOT hidden)           AS r_punctuality
        """,
        provider_id,
    )
    total = r["total"] or 0
    reliability = round(100 * (1 - (r["provider_cancels"] or 0) / total)) if total else None
    return {
        "completed": r["completed"], "clients": r["clients"], "repeat_clients": r["repeat_clients"],
        "reliability_percent": reliability,
        "rating": float(r["rating"]) if r["rating"] is not None else None, "review_count": r["review_count"],
        "dimensions": {
            "expertise": float(r["r_expertise"]) if r["r_expertise"] else None,
            "communication": float(r["r_communication"]) if r["r_communication"] else None,
            "professionalism": float(r["r_professionalism"]) if r["r_professionalism"] else None,
            "punctuality": float(r["r_punctuality"]) if r["r_punctuality"] else None,
        },
    }


async def verifications(conn, provider_id: UUID) -> list[str]:
    return [r["dimension"] for r in await conn.fetch("SELECT dimension FROM verification WHERE provider_id=$1 ORDER BY dimension", provider_id)]


async def expertise_of(conn, provider_id: UUID, lang: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT a.id, a.name_en, a.name_hi, a.name_te, a.regulated, pe.years, pe.is_primary FROM provider_expertise pe JOIN expertise_area a ON a.id=pe.area_id "
        "WHERE pe.provider_id=$1 ORDER BY pe.is_primary DESC, pe.years DESC", provider_id)
    return [{"id": r["id"], "name": area_name(dict(r), lang), "years": r["years"], "primary": r["is_primary"], "regulated": r["regulated"]} for r in rows]


async def next_slot(conn, provider_id: UUID):
    from datetime import date
    from app.components import availability
    svc = await conn.fetchrow("SELECT * FROM service WHERE provider_id=$1 AND status='active' ORDER BY price_minor LIMIT 1", provider_id)
    if not svc:
        return None
    s = await availability.slots(conn, provider_id, dict(svc), date.today(), 14)
    return s[0].isoformat() if s else None


REPLY_MIN_SAMPLES = 2


async def reply_hours(conn, provider_id: UUID) -> float | None:
    """Median hours a consultant takes to answer time requests and paid questions
    over the last 180 days (GrowthMentor shows each mentor's average response
    time). Shown only with at least REPLY_MIN_SAMPLES answers, so one lucky
    reply does not become a promise."""
    r = await conn.fetchrow(
        """
        SELECT count(*) AS n, percentile_cont(0.5) WITHIN GROUP (ORDER BY h) AS median FROM (
          SELECT extract(epoch FROM decided_at - created_at) / 3600 AS h FROM time_request
           WHERE provider_id=$1 AND decided_at IS NOT NULL AND status IN ('accepted','declined') AND created_at > now() - interval '180 days'
          UNION ALL
          SELECT extract(epoch FROM q.answered_at - q.created_at) / 3600 FROM question q JOIN purchase pu ON pu.id=q.purchase_id
           WHERE pu.provider_id=$1 AND q.answered_at IS NOT NULL AND q.created_at > now() - interval '180 days'
        ) x
        """, provider_id)
    if not r or (r["n"] or 0) < REPLY_MIN_SAMPLES or r["median"] is None:
        return None
    return round(float(r["median"]), 1)


async def card(conn, provider_id: UUID, lang: str, viewer_id: UUID | None = None) -> dict | None:
    p = await conn.fetchrow("SELECT p.*, m.display_name FROM provider p JOIN member m ON m.member_id=p.member_id WHERE p.member_id=$1", provider_id)
    if not p:
        return None
    rep = await reputation(conn, provider_id)
    svc = await conn.fetchrow("SELECT min(price_minor) AS from_minor, count(*) AS n FROM service WHERE provider_id=$1 AND status='active'", provider_id)
    ex = await expertise_of(conn, provider_id, lang)
    saved = bool(await conn.fetchval("SELECT 1 FROM saved_provider WHERE member_id=$1 AND provider_id=$2", viewer_id, provider_id)) if viewer_id else False
    from app.components import badges as badge_rules
    earned = await badge_rules.for_display(conn, provider_id)
    top = sorted(earned, key=lambda b: badge_rules.CARD_PRIORITY.index(b["id"]) if b["id"] in badge_rules.CARD_PRIORITY else 99)[:2]
    return {
        "id": str(provider_id), "name": p["display_name"], "headline": p["headline"], "photo_url": p["photo_url"],
        "city": places.label(p["city"], lang), "city_id": places.resolve(p["city"]), "country": p["country"], "languages": p["languages"], "status": p["status"],
        "expertise": ex, "verified": await verifications(conn, provider_id),
        "rating": rep["rating"], "review_count": rep["review_count"], "completed": rep["completed"],
        "from_minor": svc["from_minor"], "service_count": svc["n"], "currency": p["currency"],
        "next_slot": await next_slot(conn, provider_id), "saved": saved,
        "badges": top, "standing": p["standing"], "reply_hours": await reply_hours(conn, provider_id),
        "approved_at": p["reviewed_at"].isoformat() if p["reviewed_at"] else None,
        "available_now": bool(p["available_until"] and p["available_until"] > datetime.now(timezone.utc)
                              and await conn.fetchval("SELECT 1 FROM service WHERE provider_id=$1 AND status='active' AND instant_allowed", provider_id)),
    }


async def profile(conn, provider_id: UUID, lang: str, viewer_id: UUID | None = None) -> dict | None:
    c = await card(conn, provider_id, lang, viewer_id)
    if not c:
        return None
    p = await conn.fetchrow("SELECT * FROM provider WHERE member_id=$1", provider_id)
    services = db.rows(await conn.fetch(
        "SELECT s.*, a.name_en, a.name_hi, a.name_te FROM service s JOIN expertise_area a ON a.id=s.area_id WHERE s.provider_id=$1 AND s.status='active' ORDER BY s.price_minor", provider_id))
    for s in services:
        s["area_name"] = area_name(s, lang)
        s["id"] = str(s["id"]); s["provider_id"] = str(s["provider_id"])
        for k in ("name_en", "name_hi", "name_te"):
            s.pop(k, None)
    evidence = db.rows(await conn.fetch(
        "SELECT id, kind, title, issuer, year_from, year_to, status FROM provider_evidence WHERE provider_id=$1 ORDER BY kind, year_from DESC NULLS LAST", provider_id))
    for e in evidence:
        e["id"] = str(e["id"])
    reviews = db.rows(await conn.fetch(
        "SELECT r.id, r.overall, r.body, r.created_at, m.display_name AS reviewer FROM review r LEFT JOIN member m ON m.member_id=r.reviewer_id "
        "WHERE r.provider_id=$1 AND NOT r.hidden ORDER BY r.created_at DESC LIMIT 20", provider_id))
    for r in reviews:
        r["id"] = str(r["id"]); r["created_at"] = r["created_at"].isoformat()
    rep = await reputation(conn, provider_id)
    rules = db.rows(await conn.fetch("SELECT weekday, start_time::text, end_time::text, kind FROM availability_rule WHERE provider_id=$1 ORDER BY weekday, start_time", provider_id))
    from app.components import badges as badge_rules
    c["badges"] = await badge_rules.for_display(conn, provider_id)
    return {**c, "intro": p["intro"], "timezone": p["timezone"], "links": p["links"], "services": services,
            "evidence": evidence, "reviews": reviews, "reputation": rep, "weekly": rules}


# --- Search ----------------------------------------------------------------------

# Bayesian average for "Top rated": every consultant starts with PRIOR_REVIEWS
# imaginary reviews at the platform's average, so one 5-star review cannot beat
# two hundred reviews at 4.8 (the IMDb top-list method).
PRIOR_REVIEWS = 5
SORTS = ("best", "rating", "consultations", "price_asc", "price_desc", "soonest", "newest", "experience", "nearest")


def bayes(avg: float | None, n: int, prior_mean: float) -> float:
    return (PRIOR_REVIEWS * prior_mean + (avg or 0) * n) / (PRIOR_REVIEWS + n)


async def search(conn, *, lang: str, q: str = "", area: str | None = None, max_price_minor: int | None = None,
                 language: str | None = None, verified_only: bool = False, duration_max: int | None = None,
                 sort: str = "best", viewer_id: UUID | None = None, limit: int = 40, available_now: bool = False,
                 min_price_minor: int | None = None, min_rating: float | None = None, near: str | None = None,
                 nearby_only: bool = False, within_hours: int | None = None) -> list[dict]:
    sort = "price_asc" if sort == "price" else sort
    near = places.resolve(near)
    if sort == "nearest" and not near:
        sort = "best"
    rows = await conn.fetch(
        """
        SELECT p.member_id, m.display_name, p.headline, p.intro, p.languages, p.city, p.reviewed_at,
               array_remove(array_agg(DISTINCT pe.area_id), NULL) AS areas,
               array_remove(array_agg(DISTINCT a.name_en || ' ' || a.name_hi || ' ' || a.name_te), NULL) AS area_names,
               array_remove(array_agg(DISTINCT s.title || ' ' || s.description), NULL) AS service_text,
               min(s.price_minor) AS from_minor, min(s.duration_min) AS min_duration,
               (SELECT coalesce(sum(years),0) FROM provider_expertise x WHERE x.provider_id=p.member_id) AS years,
               (SELECT count(*) FROM verification v WHERE v.provider_id=p.member_id) AS vcount,
               (SELECT count(*) FROM booking b WHERE b.provider_id=p.member_id AND b.status='completed') AS completed,
               (SELECT avg(overall) FROM review r WHERE r.provider_id=p.member_id AND NOT r.hidden) AS rating,
               (SELECT count(*) FROM review r WHERE r.provider_id=p.member_id AND NOT r.hidden) AS reviews,
               (SELECT count(*) FROM booking b WHERE b.provider_id=p.member_id AND b.status IN ('cancelled_by_provider','no_show_provider')) AS pcancels
        FROM provider p
        JOIN member m ON m.member_id = p.member_id
        JOIN service s ON s.provider_id = p.member_id AND s.status = 'active'
        LEFT JOIN provider_expertise pe ON pe.provider_id = p.member_id
        LEFT JOIN expertise_area a ON a.id = pe.area_id
        WHERE p.status = 'approved'
        GROUP BY p.member_id, m.display_name
        """
    )
    prior_mean = float(await conn.fetchval("SELECT coalesce(avg(overall), 4.0) FROM review WHERE NOT hidden"))
    terms = [t for t in _fold(q).split() if len(t) > 1]
    scored = []
    facts: dict = {}
    for r in rows:
        if area and area not in (r["areas"] or []):
            continue
        if max_price_minor and (r["from_minor"] or 0) > max_price_minor:
            continue
        if min_price_minor and (r["from_minor"] or 0) < min_price_minor:
            continue
        if language and language not in (r["languages"] or []):
            continue
        if verified_only and (r["vcount"] or 0) == 0:
            continue
        if duration_max and (r["min_duration"] or 999) > duration_max:
            continue
        if min_rating and (r["rating"] is None or float(r["rating"]) < min_rating):
            continue
        dist = places.distance_km(near, r["city"]) if near else None
        if nearby_only and (dist is None or dist > places.NEARBY_KM):
            continue
        hay = _fold(" ".join([r["display_name"], r["headline"], r["intro"], " ".join(r["area_names"] or []), " ".join(r["service_text"] or [])]))
        relevance = 0.0
        if terms:
            hits = sum(1 for t in terms if t in hay)
            if hits == 0:
                continue
            relevance = hits / len(terms)
        weighted = bayes(float(r["rating"]) if r["rating"] is not None else None, r["reviews"] or 0, prior_mean)
        trust = min((r["vcount"] or 0) / 4, 1.0)
        experience = min((r["years"] or 0) / 15, 1.0)
        proven = min((r["completed"] or 0) / 20, 1.0)
        satisfaction = max(0.0, (weighted - 3) / 2)
        total = (r["completed"] or 0) + (r["pcancels"] or 0)
        reliability = 1 - (r["pcancels"] or 0) / total if total else 0.7
        score = 0.35 * relevance + 0.2 * trust + 0.15 * experience + 0.1 * proven + 0.1 * satisfaction + 0.1 * reliability
        why = []
        if relevance >= 0.99 and terms: why.append("matches_all_terms")
        if (r["vcount"] or 0) >= 2: why.append("well_verified")
        if (r["years"] or 0) >= 8: why.append("experienced")
        if (r["completed"] or 0) >= 5: why.append("proven")
        if reliability >= 0.95 and total >= 3: why.append("reliable")
        facts[r["member_id"]] = {"weighted": weighted, "reviews": r["reviews"] or 0, "completed": r["completed"] or 0,
                                 "price": r["from_minor"] or 0, "years": r["years"] or 0, "dist": dist,
                                 "approved": r["reviewed_at"].timestamp() if r["reviewed_at"] else 0}
        scored.append((score, r["member_id"], why[:2]))

    def f(pid):
        return facts[pid]

    keys = {
        "rating": lambda x: (-f(x[1])["weighted"], -f(x[1])["reviews"]),
        "consultations": lambda x: (-f(x[1])["completed"], -x[0]),
        "price_asc": lambda x: (f(x[1])["price"], -x[0]),
        "price_desc": lambda x: (-f(x[1])["price"], -x[0]),
        "newest": lambda x: (-f(x[1])["approved"], -x[0]),
        "experience": lambda x: (-f(x[1])["years"], -x[0]),
        "nearest": lambda x: (f(x[1])["dist"] if f(x[1])["dist"] is not None else 1e9, -x[0]),
    }
    scored.sort(key=keys.get(sort, lambda x: -x[0]))
    # Time-based filters and "soonest" need each consultant's next open time, so
    # they are applied on the built cards rather than in SQL.
    needs_all = sort == "soonest" or bool(within_hours) or available_now
    out = []
    now = datetime.now(timezone.utc)
    for _, pid, why in (scored if needs_all else scored[:limit]):
        c = await card(conn, pid, lang, viewer_id)
        if not c:
            continue
        if available_now and not c["available_now"]:
            continue
        if within_hours and not c["available_now"] and not (
                c["next_slot"] and (datetime.fromisoformat(c["next_slot"]) - now).total_seconds() <= within_hours * 3600):
            continue
        c["why"] = why
        c["distance_km"] = f(pid)["dist"]
        out.append(c)
    if sort == "soonest":
        far = datetime.max.replace(tzinfo=timezone.utc)
        out.sort(key=lambda c: now if c["available_now"] else (datetime.fromisoformat(c["next_slot"]) if c["next_slot"] else far))
    return out[:limit]
