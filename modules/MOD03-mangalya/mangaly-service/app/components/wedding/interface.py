"""Wedding arrangements — what two families who have accepted each other can
plan next, and real places near them for it (migration 062).

A connection has a stage, set by either family: the first meeting, the
families have agreed, the wedding date is fixed. Each stage offers only the
kinds of place that help at it (`catalogue.STAGE_CATEGORIES`).

Places come from two sources, never mixed:
  * Mangalya partners with an offer — shown first, each labelled as a
    partner offer (the E-Commerce Rules and ASCI require paid or arranged
    placement to say so).
  * OpenStreetMap places copied into `osm_place` by
    `scripts/import_osm_places.py`, nearest first. Nobody pays for these.

Location: families' home addresses are never used. The search centres on
the town each candidate gave on their profile (or halfway between the two
when they live in the same area), resolved through the places list.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.places import interface as places
from app.components.wedding.catalogue import CATEGORIES, STAGE_CATEGORIES, STAGES

__all__ = [
    "Match",
    "NotYourMatch",
    "get_match",
    "resolve_place",
    "set_stage",
    "stage_of",
    "stages_for",
    "suggestions",
]

DEFAULT_STAGE: Final = "first_meeting"
# Two candidates this close are "in the same area": the first meeting is
# suggested halfway between them.
SAME_AREA_KM: Final = 60.0
MAX_PLACES: Final = 30


# Where two families first meet should be a sit-down place: street carts,
# stalls and quick-service counters are left out of those two categories.
MEETING_CATEGORIES: Final = ("cafe", "restaurant")
_CASUAL: Final = re.compile(
    r"\bbandi\b|fast ?food|\bdhaba\b|\bmess\b|\bstall\b|\bcart\b|\bcanteen\b"
    r"|juice|chaat|pan shop|tiffin|\bkiosk\b|tea ?point|chai ?point",
    re.IGNORECASE,
)


def _commons_photo(file: str | None) -> dict[str, str | None]:
    """A place's own Commons photo at card size, and the page that credits it."""
    if not file or not file.startswith("File:"):
        return {"photo": None, "photo_source": None}
    name = quote(file[5:].replace(" ", "_"))
    return {
        "photo": f"https://commons.wikimedia.org/wiki/Special:FilePath/{name}?width=640",
        "photo_source": f"https://commons.wikimedia.org/wiki/File:{name}",
    }


def _place_name(name: str, names: Any, lang: str) -> str:
    """The reader's language, then English, then the name as mapped."""
    if isinstance(names, dict):
        return names.get(lang) or names.get("en") or name
    return name


def _rank(p: dict[str, Any]) -> float:
    """Nearest first, said on screen as it is: a place a kilometre further
    away still comes first when it is vegetarian (many families prefer it)
    or lists how to reach it (phone or website) and when it is open —
    a sign the place is established. Nobody can pay to move in this list."""
    bonus = 0.0
    bonus += 1.0 if p["vegetarian"] else 0.0
    bonus += 1.0 if (p["phone"] or p["website"]) else 0.0
    bonus += 0.5 if p["opening_hours"] else 0.0
    bonus += 0.5 if p["cuisine"] else 0.0
    return p["distance_km"] - bonus


class NotYourMatch(Exception):
    """The connection is not an accepted one the caller is part of."""


@dataclass(frozen=True, slots=True)
class Match:
    connection_id: UUID
    me: UUID
    other: UUID


def resolve_place(city_locality: str, *, city_level: bool = False) -> places.Place | None:
    """The Indian place a profile's "Madhapur, Hyderabad" names. The most
    specific part that is a known place wins; with `city_level`, the biggest
    (the city, for grouping imports)."""
    found: list[places.Place] = []
    for part in (p.strip() for p in city_locality.split(",")):
        if not part:
            continue
        for hit in places.search(part, limit=3):
            if hit.country_code == "IN" and hit.name.lower() == part.lower():
                found.append(hit)
                break
    if not found:
        return None
    return max(found, key=lambda p: p.population) if city_level else found[0]


def _km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    x = math.radians(b_lon - a_lon) * math.cos(math.radians((a_lat + b_lat) / 2))
    y = math.radians(b_lat - a_lat)
    return 6371.0 * math.hypot(x, y)


async def get_match(session: AsyncSession, *, connection_id: UUID, account_id: UUID) -> Match:
    row = (
        (
            await session.execute(
                text(
                    "SELECT subject_account_id, target_profile_id, status::text AS status"
                    " FROM mangaly_connection.connection_request WHERE id = :id"
                ),
                {"id": connection_id},
            )
        )
        .mappings()
        .first()
    )
    if (
        row is None
        or row["status"] != "accepted"
        or account_id not in (row["subject_account_id"], row["target_profile_id"])
    ):
        raise NotYourMatch
    other = (
        row["target_profile_id"]
        if row["subject_account_id"] == account_id
        else row["subject_account_id"]
    )
    return Match(connection_id=connection_id, me=account_id, other=other)


async def stage_of(session: AsyncSession, *, connection_id: UUID) -> dict[str, Any]:
    return (await stages_for(session, connection_ids=[connection_id]))[connection_id]


async def stages_for(
    session: AsyncSession, *, connection_ids: list[UUID]
) -> dict[UUID, dict[str, Any]]:
    out: dict[UUID, dict[str, Any]] = {
        c: {"stage": DEFAULT_STAGE, "updated_by_account_id": None, "updated_at": None}
        for c in connection_ids
    }
    if not connection_ids:
        return out
    rows = (
        await session.execute(
            text(
                "SELECT connection_id, stage, updated_by_account_id, updated_at"
                " FROM mangaly_wedding.connection_stage WHERE connection_id = ANY(:ids)"
            ),
            {"ids": connection_ids},
        )
    ).mappings()
    for r in rows:
        out[r["connection_id"]] = {
            "stage": r["stage"],
            "updated_by_account_id": r["updated_by_account_id"],
            "updated_at": r["updated_at"],
        }
    return out


async def set_stage(
    session: AsyncSession, *, match: Match, stage: str, by_account_id: UUID
) -> None:
    if stage not in STAGES:
        raise ValueError(stage)
    await session.execute(
        text(
            "INSERT INTO mangaly_wedding.connection_stage"
            " (connection_id, stage, updated_by_account_id, updated_at)"
            " VALUES (:c, :s, :by, now())"
            " ON CONFLICT (connection_id) DO UPDATE SET stage = EXCLUDED.stage,"
            " updated_by_account_id = EXCLUDED.updated_by_account_id, updated_at = now()"
        ),
        {"c": match.connection_id, "s": stage, "by": by_account_id},
    )


async def _localities(session: AsyncSession, ids: list[UUID]) -> dict[UUID, str]:
    """Each candidate's town as they gave it — the discovery row first (a
    match can read it), their own profile row otherwise."""
    out: dict[UUID, str] = {}
    for sql in (
        "SELECT profile_id AS id, locality FROM mangaly_discovery.discovery_profile_index"
        " WHERE profile_id = ANY(:ids)",
        "SELECT account_id AS id, city_locality AS locality FROM mangaly_profile.profile"
        " WHERE account_id = ANY(:ids)",
    ):
        for r in (await session.execute(text(sql), {"ids": ids})).mappings():
            if r["locality"] and r["id"] not in out:
                out[r["id"]] = r["locality"]
    return out


@dataclass(frozen=True, slots=True)
class _Centre:
    kind: str  # "between" | "mine" | "theirs"
    label: str
    lat: float
    lon: float


async def _centres(session: AsyncSession, match: Match) -> list[_Centre]:
    towns = await _localities(session, [match.me, match.other])
    mine = resolve_place(towns.get(match.me, ""))
    theirs = resolve_place(towns.get(match.other, ""))
    centres: list[_Centre] = []
    if (
        mine
        and theirs
        and _km(mine.latitude, mine.longitude, theirs.latitude, theirs.longitude) <= SAME_AREA_KM
    ):
        label = mine.name if mine.id == theirs.id else f"{mine.name} – {theirs.name}"
        centres.append(
            _Centre(
                "between",
                label,
                (mine.latitude + theirs.latitude) / 2,
                (mine.longitude + theirs.longitude) / 2,
            )
        )
    if mine and theirs and mine.id == theirs.id:
        return centres  # one town: "halfway" is the whole answer
    if mine:
        centres.append(_Centre("mine", mine.name, mine.latitude, mine.longitude))
    if theirs and (not mine or theirs.id != mine.id):
        centres.append(_Centre("theirs", theirs.name, theirs.latitude, theirs.longitude))
    return centres


def _text(value: Any, lang: str) -> str | None:
    if not isinstance(value, dict):
        return None
    return value.get(lang) or value.get("en")


async def suggestions(
    session: AsyncSession, *, match: Match, category: str, near: str | None, lang: str
) -> dict[str, Any]:
    if category not in CATEGORIES:
        raise ValueError(category)
    centres = await _centres(session, match)
    chosen = next((c for c in centres if c.kind == near), centres[0] if centres else None)
    result: dict[str, Any] = {
        "category": category,
        "centres": [{"kind": c.kind, "label": c.label} for c in centres],
        "centre": {"kind": chosen.kind, "label": chosen.label} if chosen else None,
        "partners": [],
        "places": [],
    }
    if chosen is None:
        return result
    radius = CATEGORIES[category].radius_km
    # A bounding box first (index-friendly), exact distance after.
    dlat = radius / 111.0
    dlon = radius / (111.0 * max(math.cos(math.radians(chosen.lat)), 0.2))
    box = {
        "cat": category,
        "lat0": chosen.lat - dlat,
        "lat1": chosen.lat + dlat,
        "lon0": chosen.lon - dlon,
        "lon1": chosen.lon + dlon,
    }
    partner_rows = (
        await session.execute(
            text(
                "SELECT p.id, p.name, p.latitude, p.longitude, p.address, p.phone, p.website,"
                " p.photo_url,"
                " p.verified_at, o.title, o.terms, o.discount_percent, o.valid_until"
                " FROM mangaly_wedding.partner p"
                " JOIN mangaly_wedding.partner_offer o ON o.partner_id = p.id AND o.active"
                "  AND (o.valid_from IS NULL OR o.valid_from <= current_date)"
                "  AND (o.valid_until IS NULL OR o.valid_until >= current_date)"
                " WHERE p.active AND p.category = :cat"
                "  AND p.latitude BETWEEN :lat0 AND :lat1 AND p.longitude BETWEEN :lon0 AND :lon1"
            ),
            box,
        )
    ).mappings()
    partners = []
    for r in partner_rows:
        km = _km(chosen.lat, chosen.lon, r["latitude"], r["longitude"])
        if km > radius:
            continue
        partners.append(
            {
                "id": str(r["id"]),
                "name": r["name"],
                "distance_km": round(km, 1),
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "address": r["address"],
                "phone": r["phone"],
                "website": r["website"],
                "photo": r["photo_url"],
                "verified": r["verified_at"] is not None,
                "offer": _text(r["title"], lang),
                "terms": _text(r["terms"], lang),
                "discount_percent": r["discount_percent"],
                "valid_until": r["valid_until"].isoformat() if r["valid_until"] else None,
            }
        )
    partners.sort(key=lambda p: p["distance_km"])
    result["partners"] = partners

    place_rows = (
        await session.execute(
            text(
                "SELECT osm_ref, name, names, latitude, longitude, address, cuisine,"
                " vegetarian, phone, photo,"
                " website, opening_hours, imported_at FROM mangaly_wedding.osm_place"
                " WHERE category = :cat"
                "  AND latitude BETWEEN :lat0 AND :lat1 AND longitude BETWEEN :lon0 AND :lon1"
            ),
            box,
        )
    ).mappings()
    found = []
    newest: datetime | None = None
    for r in place_rows:
        km = _km(chosen.lat, chosen.lon, r["latitude"], r["longitude"])
        if km > radius or (category in MEETING_CATEGORIES and _CASUAL.search(r["name"])):
            continue
        newest = max(newest, r["imported_at"]) if newest else r["imported_at"]
        found.append(
            {
                "ref": r["osm_ref"],
                "name": _place_name(r["name"], r["names"], lang),
                "distance_km": round(km, 1),
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "address": r["address"],
                "cuisine": r["cuisine"],
                "vegetarian": r["vegetarian"] in ("yes", "only"),
                "phone": r["phone"],
                "website": r["website"],
                "opening_hours": r["opening_hours"],
                **_commons_photo(r["photo"]),
            }
        )
    found.sort(key=_rank)
    result["places"] = found[:MAX_PLACES]
    result["places_updated"] = newest.date().isoformat() if newest else None
    return result


def stage_categories() -> dict[str, tuple[str, ...]]:
    return dict(STAGE_CATEGORIES)
