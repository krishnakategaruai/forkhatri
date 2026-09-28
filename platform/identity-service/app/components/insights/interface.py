"""Members dashboard: who ForKhatri's members are and where they live, as totals.

The platform keeps basic identity only (migration 003), so the dashboard is put
together from three places, each owner answering for its own data:

  * the platform itself — members, when they joined, when they were last seen,
    phone or email, app language, which modules they have entered, and the
    country of their phone number;
  * Mangaly — gender, date of birth and city of candidates, and the city of
    parents and relatives who have their own "My profile";
  * Milavn — city.

Module facts are fetched per request, server to server, and are never stored
here. A person is counted once: a member's location is their Mangaly candidate
city, else their Mangaly "My profile" city, else their Milavn city, else (for the
country only) their phone number's country. Everything returned is a count.
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.insights import places
from app.config.settings import Settings

logger = logging.getLogger(__name__)

# ITU calling codes for the countries Indian families most often live in.
# Longest prefix wins; +1 is shared by the US and Canada and is shown as the US.
_CALLING_CODES = {
    "91": "IN", "1": "US", "44": "GB", "61": "AU", "64": "NZ", "65": "SG", "60": "MY", "971": "AE",
    "966": "SA", "974": "QA", "968": "OM", "965": "KW", "973": "BH", "49": "DE", "33": "FR", "31": "NL",
    "353": "IE", "41": "CH", "46": "SE", "47": "NO", "45": "DK", "39": "IT", "34": "ES", "32": "BE",
    "27": "ZA", "254": "KE", "255": "TZ", "256": "UG", "230": "MU", "679": "FJ", "977": "NP", "94": "LK",
    "880": "BD", "852": "HK", "81": "JP", "82": "KR", "86": "CN", "7": "RU", "55": "BR", "52": "MX",
}

AGE_BANDS = ((18, 24), (25, 29), (30, 34), (35, 39), (40, 49), (50, 59), (60, 200))
MODULE_NAMES = {"mangaly": "Mangaly", "milavn": "Milavn", "vyapar": "Vyapar"}


def country_of_phone(phone_e164: str | None) -> str | None:
    if not phone_e164 or not phone_e164.startswith("+"):
        return None
    digits = phone_e164[1:]
    for length in (3, 2, 1):
        cc = _CALLING_CODES.get(digits[:length])
        if cc:
            return cc
    return None


def age_on(born: date, today: date) -> int:
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def band_label(age: int) -> str | None:
    for low, high in AGE_BANDS:
        if low <= age <= high:
            return f"{low}+" if high >= 200 else f"{low}-{high}"
    return None


async def _module_facts(client: httpx.AsyncClient, settings: Settings, module: str, base_url: str) -> dict[str, Any]:
    key = settings.service_keys.get(module)
    if not key:
        return {"module": module, "ok": False, "error": "no_service_key", "people": []}
    try:
        response = await client.get(
            f"{base_url.rstrip('/')}/internal/v1/insights/members",
            headers={"X-ForKhatri-Service": "platform", "X-ForKhatri-Service-Key": key},
        )
        response.raise_for_status()
        return {"module": module, "ok": True, "people": response.json().get("people", [])}
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("insights: %s did not answer: %s", module, exc)
        return {"module": module, "ok": False, "error": "unreachable", "people": []}


async def build(db: AsyncSession, settings: Settings) -> dict[str, Any]:
    now = datetime.now(UTC)
    today = now.date()

    members = (
        await db.execute(
            text(
                """
                SELECT m.id, m.phone_e164, m.email, m.preferred_language, m.identity_level, m.status, m.created_at,
                       (SELECT max(s.last_seen_at) FROM identity.session s WHERE s.member_id = m.id) AS last_seen_at
                  FROM identity.member m
                 WHERE m.status <> 'deleted'
                """
            )
        )
    ).mappings().all()
    entries = (await db.execute(text("SELECT member_id, module_key FROM registry.member_module_entry"))).all()

    async with httpx.AsyncClient(timeout=settings.insights_timeout_seconds) as client:
        answers = await asyncio.gather(
            *(_module_facts(client, settings, module, url) for module, url in settings.module_api_urls.items())
        )

    # A module that holds a service key but has no API URL configured is reported,
    # so a missing number is visible on the dashboard instead of silently absent.
    answers = [
        *answers,
        *(
            {"module": module, "ok": False, "error": "not_configured", "people": []}
            for module in settings.service_keys
            if module in MODULE_NAMES and module != "vyapar" and module not in settings.module_api_urls
        ),
    ]
    member_ids = {str(m["id"]) for m in members}
    by_module: dict[str, list[dict[str, Any]]] = {a["module"]: [p for p in a["people"] if p.get("member_id") in member_ids] for a in answers}

    # --- totals -----------------------------------------------------------
    joined = [m for m in members if m["identity_level"] >= 1]
    totals = {
        "members": len(members),
        "joined": len(joined),
        "not_yet_joined": len(members) - len(joined),
        "suspended": sum(1 for m in members if m["status"] == "suspended"),
        "new_7d": sum(1 for m in members if m["created_at"] >= now - timedelta(days=7)),
        "new_30d": sum(1 for m in members if m["created_at"] >= now - timedelta(days=30)),
        "active_7d": sum(1 for m in members if m["last_seen_at"] and m["last_seen_at"] >= now - timedelta(days=7)),
        "active_30d": sum(1 for m in members if m["last_seen_at"] and m["last_seen_at"] >= now - timedelta(days=30)),
    }

    # Growth: members on each day (cumulative) and new per day, from the day
    # before the first sign-up (so the chart never opens on a long flat line),
    # at most two years back. The page picks its own range from this.
    per_day = Counter(m["created_at"].astimezone(UTC).date() for m in members)
    first = min(per_day, default=today)
    start = max(first - timedelta(days=1), today - timedelta(days=729))
    running = sum(n for d, n in per_day.items() if d < start)
    growth = []
    for i in range((today - start).days + 1):
        day = start + timedelta(days=i)
        running += per_day.get(day, 0)
        growth.append({"date": day.isoformat(), "new": per_day.get(day, 0), "total": running})

    sign_in = Counter(
        "both" if m["phone_e164"] and m["email"] else "phone" if m["phone_e164"] else "email" for m in members
    )
    languages = Counter(m["preferred_language"] for m in members)

    # Modules: anyone who has entered it or has a profile in it.
    module_people: dict[str, set[str]] = defaultdict(set)
    for member_id, module_key in entries:
        if str(member_id) in member_ids:
            module_people[module_key].add(str(member_id))
    for module, people in by_module.items():
        module_people[module].update(p["member_id"] for p in people)
    modules = [
        {"key": k, "name": MODULE_NAMES.get(k, k.title()), "members": len(v)}
        for k, v in sorted(module_people.items(), key=lambda kv: -len(kv[1]))
    ]

    # --- demographics (Mangaly candidates: the only place gender and age exist) ---
    candidates = [p for p in by_module.get("mangaly", []) if p.get("kind") == "candidate"]
    gender = Counter((p.get("gender") or "unknown") for p in candidates)
    age_matrix: dict[str, Counter[str]] = defaultdict(Counter)
    ages_by_gender: dict[str, list[int]] = defaultdict(list)
    for p in candidates:
        if not p.get("date_of_birth"):
            continue
        age = age_on(date.fromisoformat(p["date_of_birth"]), today)
        label = band_label(age)
        g = p.get("gender") or "unknown"
        if label:
            age_matrix[label][g] += 1
        ages_by_gender[g].append(age)
    age_bands = [
        {"band": band_label(low) or "", "by_gender": dict(age_matrix.get(band_label(low) or "", {}))}
        for low, _ in AGE_BANDS
    ]

    def median(values: list[int]) -> float | None:
        if not values:
            return None
        s = sorted(values)
        mid = len(s) // 2
        return float(s[mid]) if len(s) % 2 else (s[mid - 1] + s[mid]) / 2

    all_ages = [a for v in ages_by_gender.values() for a in v]
    age_summary = {
        "median": median(all_ages),
        "youngest": min(all_ages) if all_ages else None,
        "oldest": max(all_ages) if all_ages else None,
        "median_by_gender": {g: median(v) for g, v in ages_by_gender.items()},
    }

    # --- locations: one place per member ------------------------------------
    city_text: dict[str, str] = {}
    for p in by_module.get("mangaly", []):
        if p.get("kind") == "candidate" and p.get("city"):
            city_text[p["member_id"]] = p["city"]
    for p in by_module.get("mangaly", []):
        if p.get("kind") == "member" and p.get("city"):
            city_text.setdefault(p["member_id"], p["city"])
    for p in by_module.get("milavn", []):
        if p.get("city"):
            city_text.setdefault(p["member_id"], p["city"])

    candidate_gender = {p["member_id"]: (p.get("gender") or "unknown") for p in candidates}
    cities: dict[tuple[str, str, str], dict[str, Any]] = {}
    states: Counter[str] = Counter()
    countries: dict[str, Counter[str]] = defaultdict(Counter)
    unresolved: Counter[str] = Counter()
    located = 0
    for m in members:
        mid = str(m["id"])
        place = places.resolve(city_text.get(mid))
        if place is not None:
            located += 1
            key = (place.name, place.region, place.cc)
            entry = cities.setdefault(
                key,
                {"name": place.name, "region": place.region, "cc": place.cc, "lat": place.lat, "lon": place.lon, "members": 0, "by_gender": Counter()},
            )
            entry["members"] += 1
            if mid in candidate_gender:
                entry["by_gender"][candidate_gender[mid]] += 1
            if place.cc == "IN" and place.region:
                states[place.region] += 1
            countries[place.cc]["city"] += 1
            continue
        if city_text.get(mid):
            unresolved[city_text[mid].strip()] += 1
        cc = country_of_phone(m["phone_e164"])
        if cc:
            countries[cc]["phone"] += 1
        else:
            countries["??"]["unknown"] += 1

    return {
        "generated_at": now.isoformat(),
        "totals": totals,
        "growth": growth,
        "sign_in": dict(sign_in),
        "languages": dict(languages),
        "modules": modules,
        "gender": {"candidates": len(candidates), "counts": dict(gender)},
        "age": {"bands": age_bands, **age_summary},
        "candidates": {
            "looking_for": dict(Counter(p.get("looking_for") or "unknown" for p in candidates)),
            "marital_status": dict(Counter(p.get("marital_status") or "unknown" for p in candidates)),
            "mother_tongue": dict(Counter(p.get("mother_tongue") or "unknown" for p in candidates)),
        },
        "location": {
            "located": located,
            "cities": sorted(
                ({**c, "by_gender": dict(c["by_gender"])} for c in cities.values()), key=lambda c: -c["members"]
            ),
            "india_states": [{"state": s, "members": n} for s, n in states.most_common()],
            "countries": sorted(
                (
                    {"cc": cc, "members": sum(c.values()), "from_city": c["city"], "from_phone": c["phone"]}
                    for cc, c in countries.items()
                    if cc != "??"
                ),
                key=lambda c: -c["members"],
            ),
            "country_unknown": countries["??"]["unknown"] if "??" in countries else 0,
            "unresolved": [{"text": t, "members": n} for t, n in unresolved.most_common(20)],
        },
        "sources": [
            {"module": "platform", "ok": True},
            *({"module": a["module"], "ok": a["ok"], "error": a.get("error")} for a in answers),
        ],
    }
