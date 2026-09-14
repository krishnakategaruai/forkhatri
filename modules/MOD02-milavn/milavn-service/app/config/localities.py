"""Approximate locality hierarchy (City -> Zone -> Locality) with centroids.

# [FR038, TR29, BR09] Milavn never stores an exact address — only the
# approximate hierarchy. This table is the development stand-in for the
# external geocoding/locality service TR29 names (OpenCage, config
# placeholder): it resolves a locality name to its zone/city and to an
# approximate centroid used for Map mode pins (UX05) and rough distances.
# Traces to: FR038, FR041, TR29, TR03.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Final


@dataclass(frozen=True, slots=True)
class Locality:
    city: str
    zone: str
    locality: str
    lat: float
    lng: float


LOCALITIES: Final[list[Locality]] = [
    Locality("Hyderabad", "West Zone", "Jubilee Hills", 17.4325, 78.4073),
    Locality("Hyderabad", "West Zone", "Banjara Hills", 17.4156, 78.4347),
    Locality("Hyderabad", "West Zone", "Madhapur", 17.4483, 78.3915),
    Locality("Hyderabad", "West Zone", "Gachibowli", 17.4401, 78.3489),
    Locality("Hyderabad", "West Zone", "Kondapur", 17.4622, 78.3568),
    Locality("Hyderabad", "West Zone", "Hitech City", 17.4435, 78.3772),
    Locality("Hyderabad", "West Zone", "Manikonda", 17.4022, 78.3767),
    Locality("Hyderabad", "West Zone", "Kukatpally", 17.4849, 78.4138),
    Locality("Hyderabad", "West Zone", "Miyapur", 17.4969, 78.3612),
    Locality("Hyderabad", "Central Zone", "Ameerpet", 17.4375, 78.4483),
    Locality("Hyderabad", "Central Zone", "Somajiguda", 17.4239, 78.4586),
    Locality("Hyderabad", "Central Zone", "Begumpet", 17.4440, 78.4676),
    Locality("Hyderabad", "Central Zone", "Punjagutta", 17.4276, 78.4514),
    Locality("Hyderabad", "Central Zone", "Abids", 17.3909, 78.4757),
    Locality("Hyderabad", "North Zone", "Secunderabad", 17.4399, 78.4983),
    Locality("Hyderabad", "North Zone", "Kompally", 17.5387, 78.4863),
    Locality("Hyderabad", "North Zone", "Alwal", 17.5045, 78.5124),
    Locality("Hyderabad", "North Zone", "Bowenpally", 17.4746, 78.4844),
    Locality("Hyderabad", "East Zone", "Uppal", 17.4056, 78.5591),
    Locality("Hyderabad", "East Zone", "Tarnaka", 17.4278, 78.5346),
    Locality("Hyderabad", "East Zone", "LB Nagar", 17.3457, 78.5522),
    Locality("Hyderabad", "East Zone", "Dilsukhnagar", 17.3688, 78.5247),
    Locality("Hyderabad", "South Zone", "Charminar", 17.3616, 78.4747),
    Locality("Hyderabad", "South Zone", "Mehdipatnam", 17.3949, 78.4394),
    Locality("Hyderabad", "South Zone", "Tolichowki", 17.4009, 78.4147),
    Locality("Hyderabad", "South Zone", "Attapur", 17.3699, 78.4283),
    Locality("Warangal", "Central", "Hanamkonda", 18.0100, 79.5600),
    Locality("Warangal", "Central", "Kazipet", 17.9722, 79.5000),
    Locality("Vijayawada", "Central", "Benz Circle", 16.4989, 80.6555),
    Locality("Vijayawada", "West", "Gollapudi", 16.5453, 80.5807),
    Locality("Visakhapatnam", "Central", "MVP Colony", 17.7408, 83.3346),
    Locality("Visakhapatnam", "North", "Madhurawada", 17.8163, 83.3607),
]

_BY_NAME: Final[dict[tuple[str, str], Locality]] = {(loc.city.lower(), loc.locality.lower()): loc for loc in LOCALITIES}


def find(city: str, locality: str | None) -> Locality | None:
    if not locality:
        return None
    return _BY_NAME.get((city.lower(), locality.lower()))


def cities() -> list[str]:
    seen: list[str] = []
    for loc in LOCALITIES:
        if loc.city not in seen:
            seen.append(loc.city)
    return seen


def hierarchy_payload() -> list[dict]:
    out: dict[str, dict[str, list[dict]]] = {}
    for loc in LOCALITIES:
        out.setdefault(loc.city, {}).setdefault(loc.zone, []).append({"locality": loc.locality, "lat": loc.lat, "lng": loc.lng})
    return [{"city": city, "zones": [{"zone": z, "localities": locs} for z, locs in zones.items()]} for city, zones in out.items()]


def distance_km(a: Locality, b: Locality) -> float:
    lat1, lng1, lat2, lng2 = map(radians, (a.lat, a.lng, b.lat, b.lng))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


def nearest(lat: float, lng: float) -> Locality:
    probe = Locality("", "", "", lat, lng)
    return min(LOCALITIES, key=lambda loc: distance_km(loc, probe))
