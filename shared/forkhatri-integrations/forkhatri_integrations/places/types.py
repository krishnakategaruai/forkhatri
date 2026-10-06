"""Place search types (India place data: state, district, city, area)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class PlacesError(Exception):
    pass


class PlacesNotConfigured(PlacesError):
    """No place-search provider is switched on."""


class PlacesUnavailable(PlacesError):
    """The provider could not answer right now (timeout, 5xx, rate limit)."""


@dataclass(frozen=True, slots=True)
class Place:
    """One approximate place. Never a street address: areas only."""

    kind: str  # "state" | "district" | "city" | "area"
    name: str
    city: str  # the settlement (or district / state for coarse picks)
    zone: str | None  # the district
    locality: str | None  # the area inside the city, for kind "area"
    state: str | None
    lat: float  # centre of the place
    lon: float
    label: str  # one line for a suggestion list, with enough context to tell namesakes apart
    ref: str  # the vendor's id, for audit only


@dataclass(frozen=True, slots=True)
class GeoPoint:
    """One exact point for a full address (a venue). Unlike Place, this may be street level: callers decide who sees it."""

    lat: float
    lon: float
    label: str  # the provider's display name for what it found


class PlaceSearch(Protocol):
    name: str

    async def search(self, query: str, *, language: str = "en", limit: int = 8) -> list[Place]: ...

    async def reverse(self, lat: float, lon: float, *, language: str = "en") -> Place | None: ...

    async def geocode(self, address: str, *, language: str = "en") -> GeoPoint | None: ...
