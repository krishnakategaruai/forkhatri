"""Location & Privacy — public interface (`milavn_locationprivacy`).

# [FR038, FR039, FR040, FR041, TR30] Approximate City -> Zone -> Locality
# display; precise location only with an explicit consent grant (no caller
# yet); every location-consuming surface goes through `display_location()`
# and `precision_for()` here — never its own precision check (IA041).
# Traces to: FR038, FR039, FR041, TR29, TR30.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import localities

PRECISION_ORDER = ("city", "zone", "locality", "precise")


@dataclass(frozen=True, slots=True)
class LocationDisplay:
    label: str
    city: str
    zone: str | None
    locality: str | None
    distance_km: float | None
    distance_label: str | None


async def precision_for(session: AsyncSession, *, member_id: UUID) -> str:
    row = (
        await session.execute(
            text("SELECT precision_level::text FROM milavn_locationprivacy.location_precision_setting WHERE member_id = :m"),
            {"m": str(member_id)},
        )
    ).first()
    return row[0] if row else "locality"


async def set_precision(session: AsyncSession, *, member_id: UUID, level: str) -> str:
    if level not in ("city", "zone", "locality"):
        # 'precise' requires an explicit consent grant (FR039) — no feature asks for it yet.
        raise ValueError(level)
    await session.execute(
        text(
            """
            INSERT INTO milavn_locationprivacy.location_precision_setting (member_id, precision_level)
            VALUES (:m, CAST(:lvl AS milavn_locationprivacy.precision_level))
            ON CONFLICT (member_id) DO UPDATE SET precision_level = EXCLUDED.precision_level, updated_at = now()
            """
        ),
        {"m": str(member_id), "lvl": level},
    )
    return level


def apply_precision(city: str, zone: str | None, locality: str | None, level: str) -> tuple[str, str | None, str | None]:
    """[FR041] Never expose more precision than the member's own setting allows."""
    if level == "city":
        return city, None, None
    if level == "zone":
        return city, zone, None
    return city, zone, locality


def display_location(
    *,
    city: str,
    zone: str | None,
    locality: str | None,
    viewer_city: str | None,
    viewer_locality: str | None,
) -> LocationDisplay:
    """[FR038] Locality > Zone > City label, plus an approximate distance from the viewer's locality."""
    label = locality or zone or city
    distance_km: float | None = None
    distance_label: str | None = None
    if viewer_city and viewer_city.lower() == city.lower():
        a = localities.find(viewer_city, viewer_locality)
        b = localities.find(city, locality)
        if a and b:
            distance_km = round(localities.distance_km(a, b), 1)
            if distance_km < 1.0:
                distance_label = "Same locality"
            else:
                distance_label = f"~{distance_km:g} km away"
        elif zone and viewer_locality:
            va = localities.find(viewer_city, viewer_locality)
            if va and va.zone == zone:
                distance_label = f"In {zone}"
    elif viewer_city:
        distance_label = city
    return LocationDisplay(label, city, zone, locality, distance_km, distance_label)
