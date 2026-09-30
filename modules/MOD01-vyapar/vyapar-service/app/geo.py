# [IMP-B, owner 2026-09-30] Places a person types, turned into coordinates.
#
# "ameerpet" typed into Businesses search used to become a text chip that
# matched almost nothing; posts carried a location string but no lat/lng, so
# "near you" and radius could not measure them. This is a small gazetteer of
# the Hyderabad localities members actually use (centroids, about 0.5 km
# accurate — plenty for "within 5 km"). `resolve_place()` finds a known
# locality inside any text, spelling-tolerant ("Kukatpalli", "L.B. Nagar",
# "hitec city"). It is data, not a vendor: when Vyapar serves another city,
# add its localities here or swap `resolve_place` for a geocoding adapter.
# Traces to: FR15 (radius filter), FR18/FR19 (location fit)
from __future__ import annotations

from dataclasses import dataclass

from app.text_fold import fold


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lng: float


_PLACES: list[tuple[str, float, float, tuple[str, ...]]] = [
    ("Kukatpally", 17.4948, 78.3996, ("kphb",)),
    ("Ameerpet", 17.4375, 78.4483, ()),
    ("Madhapur", 17.4483, 78.3915, ()),
    ("Hitech City", 17.4435, 78.3772, ("hitec city", "hi-tech city", "hitex")),
    ("Dilsukhnagar", 17.3688, 78.5247, ("dilsuk nagar", "dsnr")),
    ("Himayatnagar", 17.4020, 78.4840, ("himayat nagar",)),
    ("Secunderabad", 17.4399, 78.4983, ("secundrabad",)),
    ("Gachibowli", 17.4401, 78.3489, ()),
    ("Banjara Hills", 17.4156, 78.4347, ()),
    ("Jubilee Hills", 17.4325, 78.4073, ()),
    ("Uppal", 17.4056, 78.5591, ()),
    ("LB Nagar", 17.3457, 78.5522, ("l b nagar", "lbnagar")),
    ("Miyapur", 17.4968, 78.3614, ()),
    ("Begumpet", 17.4447, 78.4676, ()),
    ("Charminar", 17.3616, 78.4747, ("old city",)),
    ("Kondapur", 17.4622, 78.3568, ()),
    ("Abids", 17.3900, 78.4750, ()),
    ("Koti", 17.3850, 78.4867, ()),
    ("Nampally", 17.3890, 78.4690, ()),
    ("Mehdipatnam", 17.3950, 78.4400, ()),
    ("Tarnaka", 17.4270, 78.5400, ()),
    ("Malakpet", 17.3720, 78.5050, ()),
    ("Kothapet", 17.3680, 78.5430, ()),
    ("Attapur", 17.3700, 78.4300, ()),
    ("Manikonda", 17.4050, 78.3860, ()),
    ("Nizampet", 17.5150, 78.3860, ()),
    ("Kompally", 17.5360, 78.4850, ()),
    ("ECIL", 17.4700, 78.5700, ("a s rao nagar",)),
    ("Somajiguda", 17.4240, 78.4580, ()),
    ("Panjagutta", 17.4260, 78.4510, ("punjagutta",)),
    ("Shamshabad", 17.2500, 78.4000, ()),
    ("Chanda Nagar", 17.4930, 78.3280, ("chandanagar",)),
    ("Bachupally", 17.5420, 78.3850, ()),
    ("Sainikpuri", 17.4900, 78.5500, ()),
]

# folded name -> Place; longer names first so "banjara hills" beats "hills"
_INDEX: list[tuple[str, Place]] = sorted(
    [(fold(n), Place(name, lat, lng)) for name, lat, lng, alts in _PLACES for n in (name, *alts)],
    key=lambda kv: -len(kv[0]),
)


def resolve_place(text: str | None) -> Place | None:
    """The known locality named in `text` (whole words), else None."""
    f = f" {fold(text)} "
    if not f.strip():
        return None
    for key, place in _INDEX:
        if f" {key} " in f:
            return place
    return None


def place_words(text: str | None) -> set[str]:
    """Folded words of the place found in `text` (to take them out of a text query)."""
    place = resolve_place(text)
    if place is None:
        return set()
    for key, p in _INDEX:
        if p == place and f" {key} " in f" {fold(text)} ":
            return set(key.split())
    return set()


def nearest_place(lat: float, lng: float, max_km: float = 15.0) -> tuple[Place, float] | None:
    """[Backend A, 2026-09-30] The known locality nearest to a position (the
    browser's "use my current location"), with its distance, or None beyond
    `max_km`. Equirectangular distance: accurate to metres at city scale."""
    import math

    best: tuple[Place, float] | None = None
    for name, plat, plng, _alts in _PLACES:
        x = math.radians(plng - lng) * math.cos(math.radians((plat + lat) / 2))
        y = math.radians(plat - lat)
        d = 6371.0 * math.hypot(x, y)
        if d <= max_km and (best is None or d < best[1]):
            best = (Place(name, plat, plng), d)
    return best
