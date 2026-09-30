# [IMP-B, owner 2026-09-30] How a place and a distance read on a card.
#
# "Madhapur, Hyderabad · 0.0 km away" read wrong twice: everything on Vyapar
# is in the city, so the city name is noise, and "0.0 km" is a measurement
# artefact (two points at the same locality centroid), not a fact a person
# can use. Under 0.5 km a card says "In your area"; above it, "1.8 km away"
# (one decimal under 10 km, whole kilometres from 10 up). The location keeps
# the part a person recognises: the locality, without a trailing city/state.
# Traces to: FR15, FR18 (card fields)
from __future__ import annotations

from app.i18n import translate

NEAR_KM = 0.5
_CITY_SUFFIXES = ("hyderabad", "secunderabad city", "telangana", "india", "ghmc")


def distance_label(distance_km: float | None, lang: str) -> str | None:
    if distance_km is None:
        return None
    if distance_km < NEAR_KM:
        return translate("discover.distance.inYourArea", lang)
    km = f"{distance_km:.1f}" if distance_km < 10 else f"{round(distance_km):d}"
    return translate("discover.distance.away", lang, km=km)


def location_label(location: str | None) -> str | None:
    """"Madhapur, Hyderabad" -> "Madhapur"; "Road 12, Banjara Hills, Hyderabad, Telangana" -> "Road 12, Banjara Hills"."""
    if not location:
        return location
    parts = [p.strip() for p in location.split(",") if p.strip()]
    while len(parts) > 1 and parts[-1].lower() in _CITY_SUFFIXES:
        parts.pop()
    return ", ".join(parts) if parts else location
