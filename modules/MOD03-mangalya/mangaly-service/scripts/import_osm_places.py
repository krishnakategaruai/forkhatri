"""Copy OpenStreetMap places for wedding arrangements into Mangalya's own
table (`mangaly_wedding.osm_place`, migration 062).

The app never calls OpenStreetMap while a family waits: the public Overpass
server allows about a hundred queries a day for a service and must not be an
app backend. Run this weekly per city instead (a Geofabrik extract replaces
it once there are many cities). One Overpass query per city, every category
at once; each place is sorted into a category by `catalogue.classify`.

Data © OpenStreetMap contributors, ODbL — the app shows that credit under
every list of places.

Run (owner role, it writes a table the app can only read):
    MANGALY_OWNER_DSN=postgresql://… python -m scripts.import_osm_places Hyderabad Bengaluru
With no city names it imports every city a member lives in.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncpg  # noqa: E402
import httpx  # noqa: E402

from app.components.places import interface as places  # noqa: E402
from app.components.wedding import catalogue  # noqa: E402
from app.components.wedding.interface import resolve_place  # noqa: E402

# The main server first, then a public mirror when it is overloaded.
OVERPASS_URLS = os.environ.get(
    "OVERPASS_URLS",
    "https://overpass-api.de/api/interpreter,https://overpass.kumi.systems/api/interpreter,"
    "https://overpass.private.coffee/api/interpreter",
).split(",")
# Overpass refuses anonymous clients; say who we are.
USER_AGENT = "Mangalya-wedding-places-import/1.0 (ForKhatri)"
IMPORT_RADIUS_KM = 25


def _query(filters: tuple[str, ...], lat: float, lon: float) -> str:
    # A box around the city: far cheaper for the server than a radius search.
    dlat = IMPORT_RADIUS_KM / 111.0
    dlon = IMPORT_RADIUS_KM / (111.0 * math.cos(math.radians(lat)))
    area = f"({lat - dlat:.4f},{lon - dlon:.4f},{lat + dlat:.4f},{lon + dlon:.4f})"
    body = "".join(f"{f}{area};" for f in filters)
    return f"[out:json][timeout:90];({body});out center tags;"


async def _fetch(client: httpx.AsyncClient, query: str) -> list[dict]:
    """One query, trying each server; an answer carrying an error remark is
    a failure, not an empty city."""
    last: Exception | None = None
    for attempt in range(3):
        for url in OVERPASS_URLS:
            try:
                resp = await client.post(url.strip(), data={"data": query})
                resp.raise_for_status()
                body = resp.json()
                remark = (body.get("remark") or "").lower()
                if "error" in remark or "timed out" in remark:
                    raise httpx.HTTPError(body["remark"][:200])
                return body.get("elements", [])
            except (httpx.HTTPError, ValueError) as exc:
                last = exc
        # Busy or rate-limited: wait longer each round before trying again.
        await asyncio.sleep(30 * (attempt + 1))
    raise httpx.HTTPError(f"every Overpass server failed: {last}")


def _address(tags: dict[str, str]) -> str | None:
    parts = [tags.get(k) for k in ("addr:housenumber", "addr:street", "addr:suburb", "addr:city")]
    text = ", ".join(p for p in parts if p)
    return text or tags.get("addr:full")


_UPSERT = """INSERT INTO mangaly_wedding.osm_place
     (osm_ref, category, name, latitude, longitude, city, address, cuisine,
      vegetarian, phone, website, opening_hours, names, photo, imported_at)
   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14, now())
   ON CONFLICT (osm_ref) DO UPDATE SET
     category = EXCLUDED.category, name = EXCLUDED.name,
     latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude,
     city = EXCLUDED.city, address = EXCLUDED.address, cuisine = EXCLUDED.cuisine,
     vegetarian = EXCLUDED.vegetarian, phone = EXCLUDED.phone,
     website = EXCLUDED.website, opening_hours = EXCLUDED.opening_hours,
     names = EXCLUDED.names, photo = EXCLUDED.photo, imported_at = now()"""


def _row(e: dict, city: str) -> tuple | None:
    """One OSM element as an `osm_place` row, in the category `classify`
    gives it (a "convention" that also serves food is a hall)."""
    tags = e.get("tags") or {}
    category = catalogue.classify(tags)
    lat = e.get("lat", (e.get("center") or {}).get("lat"))
    lon = e.get("lon", (e.get("center") or {}).get("lon"))
    if category is None or lat is None or lon is None:
        return None
    return (
        f"{e['type']}/{e['id']}",
        category,
        tags["name"].strip(),
        lat,
        lon,
        city,
        _address(tags),
        tags.get("cuisine"),
        tags.get("diet:vegetarian"),
        tags.get("phone") or tags.get("contact:phone"),
        tags.get("website") or tags.get("contact:website"),
        tags.get("opening_hours"),
        # The same place's name in each app language, when mappers gave it.
        json.dumps({k: tags[f"name:{k}"] for k in ("en", "hi", "te") if tags.get(f"name:{k}")})
        or None,
        _photo(tags),
    )


def _photo(tags: dict[str, str]) -> str | None:
    """A Commons photo of this place ("File:…"), when OSM links one. Other
    image links are left alone: their licence is unknown."""
    value = tags.get("wikimedia_commons", "")
    if value.startswith("File:"):
        return value
    m = re.search(r"commons\.wikimedia\.org/wiki/(File:[^?#]+)", tags.get("image", ""))
    return urllib.parse.unquote(m.group(1)).replace("_", " ") if m else None


async def _member_cities(conn: asyncpg.Connection) -> list[str]:
    rows = await conn.fetch("SELECT DISTINCT city_locality FROM mangaly_profile.profile")
    names: set[str] = set()
    for r in rows:
        place = resolve_place(r["city_locality"] or "", city_level=True)
        if place is not None:
            names.add(place.name)
    return sorted(names)


async def import_city(conn: asyncpg.Connection, client: httpx.AsyncClient, city: str) -> int:
    hits = places.search(city, limit=1)
    if not hits:
        print(f"  {city}: not in the places list, skipped")
        return 0
    p = hits[0]
    # One small query per category: a single query for everything times out
    # on the shared server. Each category is saved as soon as it arrives, and
    # one that fails keeps its previous copy instead of emptying the city.
    total = 0
    counts: dict[str, int] = {}
    for i, cat in enumerate(catalogue.CATEGORIES.values()):
        if i:
            await asyncio.sleep(8)
        try:
            found = await _fetch(client, _query(cat.filters, p.latitude, p.longitude))
        except httpx.HTTPError as exc:
            print(f"    {cat.key}: failed ({str(exc)[:120]}); previous copy kept", flush=True)
            continue
        rows = [r for r in (_row(e, p.name) for e in found) if r is not None]
        async with conn.transaction():
            # A place removed from OSM since the last run leaves Mangalya too.
            await conn.execute(
                "DELETE FROM mangaly_wedding.osm_place WHERE city = $1 AND category = $2",
                p.name,
                cat.key,
            )
            await conn.executemany(_UPSERT, rows)
        for r in rows:
            counts[r[1]] = counts.get(r[1], 0) + 1
        total += len(rows)
        print(f"    {cat.key}: {len(found)} found, {len(rows)} saved", flush=True)
    print(f"  {p.name}: {total} places {dict(sorted(counts.items()))}", flush=True)
    return total


async def main(argv: list[str]) -> int:
    dsn = os.environ.get("MANGALY_OWNER_DSN")
    if not dsn:
        print("Set MANGALY_OWNER_DSN to the owner role's connection string.")
        return 2
    conn = await asyncpg.connect(dsn)
    try:
        cities = argv or await _member_cities(conn)
        print(f"Importing {len(cities)} cities: {', '.join(cities)}")
        async with httpx.AsyncClient(timeout=120, headers={"User-Agent": USER_AGENT}) as client:
            for i, city in enumerate(cities):
                if i:
                    await asyncio.sleep(5)  # be gentle with the shared server
                try:
                    await import_city(conn, client, city)
                except httpx.HTTPError as exc:
                    print(f"  {city}: Overpass failed ({exc}); the previous copy is kept")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
