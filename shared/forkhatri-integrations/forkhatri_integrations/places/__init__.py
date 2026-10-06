"""Places: live India place search (state, district, city, area) behind one interface.

    from forkhatri_integrations import places
    provider = places.get_provider(settings.places_provider, base_url=..., user_agent=..., email=...)
    hits = await provider.search("kondap", language="en")
    point = await provider.geocode("Shilpakala Vedika, HITEC City, Hyderabad")   # an exact venue, street level

Adapters now: "none" (switched off, raises PlacesNotConfigured) and "nominatim"
(free OpenStreetMap data; public or self-hosted). A paid geocoder later is one file
plus `register_provider(name, factory)`; no module code changes.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .nominatim import NominatimSearch, parse_place
from .types import GeoPoint, Place, PlaceSearch, PlacesError, PlacesNotConfigured, PlacesUnavailable

__all__ = ["GeoPoint", "Place", "PlaceSearch", "PlacesError", "PlacesNotConfigured", "PlacesUnavailable", "NominatimSearch", "parse_place",
           "get_provider", "register_provider", "available_providers"]


class NotConfiguredPlaces:
    name = "none"

    async def search(self, query: str, *, language: str = "en", limit: int = 8) -> list[Place]:
        raise PlacesNotConfigured("place search is not switched on")

    async def reverse(self, lat: float, lon: float, *, language: str = "en") -> Place | None:
        raise PlacesNotConfigured("place search is not switched on")

    async def geocode(self, address: str, *, language: str = "en") -> GeoPoint | None:
        raise PlacesNotConfigured("place search is not switched on")


_FACTORIES: dict[str, Callable[..., PlaceSearch]] = {
    "none": lambda **_: NotConfiguredPlaces(),
    "nominatim": lambda base_url="", user_agent="", email="", country_codes="in", **_: NominatimSearch(base_url, user_agent, email, country_codes),
}
_cache: dict[tuple, PlaceSearch] = {}


def register_provider(name: str, factory: Callable[..., PlaceSearch]) -> None:
    _FACTORIES[name] = factory
    for key in [k for k in _cache if k[0] == name]:
        del _cache[key]


def available_providers() -> list[str]:
    return sorted(_FACTORIES)


def get_provider(name: str | None, **options: Any) -> PlaceSearch:
    """Built once per set of options, so the adapter's cache and rate limit are shared. Unknown or empty name = off."""
    name = (name or "none").strip().lower()
    if name not in _FACTORIES or (name == "nominatim" and not options.get("base_url")):
        name = "none"
    key = (name, tuple(sorted((k, str(v)) for k, v in options.items())))
    if key not in _cache:
        _cache[key] = _FACTORIES[name](**options)
    return _cache[key]
