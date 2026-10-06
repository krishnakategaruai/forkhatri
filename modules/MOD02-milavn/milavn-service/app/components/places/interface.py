"""Places port — live India place search through the shared utility (FR038, TR29, BR09).

# Milavn keeps only an approximate place: a state, district, city or area and the
# centre of it. The vendor (free OpenStreetMap data today) sits behind
# `forkhatri_integrations.places`, so swapping it is a settings change. This file
# holds the one place Milavn reads those settings, plus the distance maths that
# used to live beside the hardcoded locality list.
# Traces to: FR038, FR041, FR081, TR29.
"""

from __future__ import annotations

from dataclasses import asdict
from math import asin, cos, radians, sin, sqrt

from forkhatri_integrations import places as shared_places

from app.config.settings import get_settings

PlacesNotConfigured = shared_places.PlacesNotConfigured
PlacesUnavailable = shared_places.PlacesUnavailable

# India, with a margin: anything outside is not a place a member can pick.
_LAT = (6.0, 38.0)
_LNG = (67.0, 98.5)


def provider() -> shared_places.PlaceSearch:
    s = get_settings()
    return shared_places.get_provider(s.places_provider, base_url=s.places_base_url, user_agent=s.places_user_agent, email=s.places_contact_email)


def _payload(p: shared_places.Place) -> dict:
    d = asdict(p)
    d.pop("ref", None)
    # What a pick sets: the approximate place fields the profile, events and circles store.
    return {**d, "locality_city": p.city, "locality_zone": p.zone, "locality_locality": p.locality, "locality_state": p.state}


# Place names are stored, matched and compared as text across members, so they are always fetched in
# English whatever the member's screen language (a Telugu and a Hindi member must meet at the same "Hyderabad").
_STORED_LANGUAGE = "en"


async def search(query: str, lang: str) -> list[dict]:
    q = query.strip()[:80]
    if len(q) < 2:
        return []
    return [_payload(p) for p in await provider().search(q, language=_STORED_LANGUAGE)]


async def nearest(lat: float, lng: float, lang: str) -> dict | None:
    if not (_LAT[0] <= lat <= _LAT[1] and _LNG[0] <= lng <= _LNG[1]):
        return None
    p = await provider().reverse(lat, lng, language=_STORED_LANGUAGE)
    return _payload(p) if p else None


# A venue pin further than this from the event's chosen area is a wrong match (a namesake in another city), not a pin.
_VENUE_MAX_KM_FROM_AREA = 40.0


async def geocode_venue(address: str, near_lat: float | None, near_lng: float | None) -> tuple[float, float] | None:
    """The exact map point for an event's full venue address (Phase 2 Step 5), or None.

    Tries the whole address, then without its first part (house / door numbers often defeat OpenStreetMap), then
    without the first two. A hit must lie in India and, when the event has an area, near it. Never raises: no pin
    only means the directions open on the address text instead."""
    parts = [p.strip() for p in address.replace("\n", ",").split(",") if p.strip()]
    tries = [", ".join(parts[i:]) for i in range(min(3, len(parts))) if len(parts) - i >= 2 or i == 0]
    for q in tries:
        try:
            hit = await provider().geocode(q[:300], language=_STORED_LANGUAGE)
        except shared_places.PlacesError:
            return None
        if hit is None or not (_LAT[0] <= hit.lat <= _LAT[1] and _LNG[0] <= hit.lon <= _LNG[1]):
            continue
        if near_lat is not None and near_lng is not None and distance_km(near_lat, near_lng, hit.lat, hit.lon) > _VENUE_MAX_KM_FROM_AREA:
            continue
        return round(hit.lat, 6), round(hit.lon, 6)
    return None


def approximate_centre(lat: float | None, lng: float | None) -> tuple[float | None, float | None]:
    """BR09: only an approximate centre is ever stored (two decimals is about a kilometre); anything outside India is dropped."""
    if lat is None or lng is None or not (_LAT[0] <= lat <= _LAT[1] and _LNG[0] <= lng <= _LNG[1]):
        return None, None
    return round(lat, 2), round(lng, 2)


def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    a, b, c, d = map(radians, (lat1, lng1, lat2, lng2))
    h = sin((c - a) / 2) ** 2 + cos(a) * cos(c) * sin((d - b) / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))
