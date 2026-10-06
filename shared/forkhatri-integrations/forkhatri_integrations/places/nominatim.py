"""Nominatim (OpenStreetMap) adapter, India only.

Works against the public server or a self-hosted one (`base_url`). It follows the
public usage policy: a real User-Agent identifying the app, at most one request
per second, and cached answers. Standard library only (urllib in a worker thread).
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from typing import Any

from .types import GeoPoint, Place, PlacesUnavailable

_AREA = {"suburb", "neighbourhood", "neighborhood", "quarter", "city_district", "borough", "locality", "residential"}
_CITY = {"city", "town", "village", "municipality", "hamlet", "isolated_dwelling"}
_DISTRICT = {"state_district", "county", "district"}
_WARD = re.compile(r"^ward\s+\d+\s+", re.IGNORECASE)


def _kind(result: dict[str, Any]) -> str | None:
    if result.get("category") not in ("place", "boundary"):
        return None
    t = str(result.get("addresstype") or result.get("type") or "")
    if t == "state":
        return "state"
    if t in _DISTRICT:
        return "district"
    if t in _CITY:
        return "city"
    if t in _AREA:
        return "area"
    return None


def parse_place(result: dict[str, Any]) -> Place | None:
    kind = _kind(result)
    if kind is None:
        return None
    addr = result.get("address") or {}
    if str(addr.get("country_code", "in")).lower() != "in":
        return None
    t = str(result.get("addresstype") or result.get("type") or "")
    name = (result.get("name") or addr.get(t) or "").strip()
    if kind == "area":
        name = _WARD.sub("", name).strip()  # OSM often names a Hyderabad area "Ward 107 Madhapur"
    if not name:
        return None
    state = addr.get("state")
    district = addr.get("state_district") or (addr.get("county") if kind == "district" else None)
    settlement = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
    if kind in ("state", "district"):
        city, zone, locality = name, None, None
    elif kind == "city":
        city, zone, locality = name, (district if district and district != name else None), None
    else:
        city = settlement or district or state or name
        zone, locality = (district if district and district != city else None), name
    parts: list[str] = []
    for p in (name, city, zone if kind in ("city", "area") else None, state):
        if p and p not in parts:
            parts.append(p)
    try:
        lat, lon = float(result["lat"]), float(result["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    return Place(kind, name, city, zone, locality, state, lat, lon, ", ".join(parts), f"{result.get('osm_type', '')}{result.get('osm_id', '')}")


class NominatimSearch:
    name = "nominatim"

    def __init__(self, base_url: str, user_agent: str, email: str = "", country_codes: str = "in", timeout: float = 8.0,
                 cache_seconds: int = 86400, cache_size: int = 1000, min_interval: float = 1.1) -> None:
        self._base = base_url.rstrip("/")
        self._agent = user_agent
        self._email = email
        self._cc = country_codes
        self._timeout = timeout
        self._ttl = cache_seconds
        self._size = cache_size
        self._gap = min_interval
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock: asyncio.Lock | None = None
        self._last = 0.0

    def _get_sync(self, path: str, params: dict[str, str]) -> Any:
        if self._email:
            params = {**params, "email": self._email}
        req = urllib.request.Request(f"{self._base}/{path}?{urllib.parse.urlencode(params)}", headers={"User-Agent": self._agent, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 - base_url comes from module settings
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            raise PlacesUnavailable(str(exc)) from exc

    async def _fetch(self, path: str, params: dict[str, str]) -> Any:
        key = path + "?" + urllib.parse.urlencode(sorted(params.items()))
        hit = self._cache.get(key)
        if hit and time.monotonic() - hit[0] < self._ttl:
            self._cache.move_to_end(key)
            return hit[1]
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:  # one request at a time, at most one per second (usage policy)
            hit = self._cache.get(key)
            if hit and time.monotonic() - hit[0] < self._ttl:
                return hit[1]
            wait = self._gap - (time.monotonic() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                data = await asyncio.to_thread(self._get_sync, path, params)
            finally:
                self._last = time.monotonic()
        self._cache[key] = (time.monotonic(), data)
        while len(self._cache) > self._size:
            self._cache.popitem(last=False)
        return data

    async def search(self, query: str, *, language: str = "en", limit: int = 8) -> list[Place]:
        q = " ".join(query.split())
        if len(q) < 2:
            return []
        data = await self._fetch("search", {"q": q, "format": "jsonv2", "addressdetails": "1", "countrycodes": self._cc,
                                            "limit": str(min(max(limit, 1) * 2, 20)), "accept-language": language})
        out: list[Place] = []
        seen: set[str] = set()
        for item in data if isinstance(data, list) else []:
            p = parse_place(item)
            if p and p.label not in seen:
                seen.add(p.label)
                out.append(p)
        return out[:limit]

    async def reverse(self, lat: float, lon: float, *, language: str = "en") -> Place | None:
        # zoom 14 = suburb level; rounded so nearby callers share a cache entry
        data = await self._fetch("reverse", {"lat": f"{lat:.3f}", "lon": f"{lon:.3f}", "format": "jsonv2", "addressdetails": "1", "zoom": "14", "accept-language": language})
        if not isinstance(data, dict) or "address" not in data:
            return None
        addr = data["address"]
        if str(addr.get("country_code", "")).lower() != "in":
            return None
        area = addr.get("suburb") or addr.get("neighbourhood") or addr.get("quarter") or addr.get("city_district")
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or addr.get("state_district") or addr.get("state")
        if not city:
            return None
        name = area or city
        synthetic = {"category": "place", "addresstype": "suburb" if area else "city", "name": name, "address": {**addr}, "lat": data.get("lat", lat),
                     "lon": data.get("lon", lon), "osm_type": data.get("osm_type", ""), "osm_id": data.get("osm_id", "")}
        return parse_place(synthetic)

    async def geocode(self, address: str, *, language: str = "en") -> GeoPoint | None:
        """The best single point for a full address (any kind of place: a building, a hall, a street), India only."""
        q = " ".join(address.split())
        if len(q) < 3:
            return None
        data = await self._fetch("search", {"q": q, "format": "jsonv2", "addressdetails": "1", "countrycodes": self._cc, "limit": "1", "accept-language": language})
        if not isinstance(data, list) or not data:
            return None
        item = data[0]
        if str((item.get("address") or {}).get("country_code", "in")).lower() != "in":
            return None
        try:
            return GeoPoint(float(item["lat"]), float(item["lon"]), str(item.get("display_name") or q))
        except (KeyError, TypeError, ValueError):
            return None
