"""Places — search and look up a place of birth.

A kundli needs the birthplace's coordinates and the time zone it kept on the
day of birth. The browser never supplies those: it sends the id of a place it
found through `search`, and the server resolves the id here, so a stored
latitude, longitude and IANA zone always come from this list.

Data: `data/places.tsv`, built by `scripts/build_places.py` from GeoNames
(CC BY 4.0, see `data/ATTRIBUTION.md`): every Indian place of 5,000+ people,
places of 15,000+ elsewhere, Indian district towns under the names families
use. A village is not in the list; the hint beside the field says to choose
the nearest town, which moves the ascendant by a fraction of a degree.
"""

from __future__ import annotations

import csv
import unicodedata
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path
from typing import Any, Final

__all__ = ["Place", "get", "search"]

_DATA: Final = Path(__file__).parent / "data" / "places.tsv"


@dataclass(frozen=True, slots=True)
class Place:
    id: str
    name: str
    region: str
    country_code: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    population: int

    @property
    def label(self) -> str:
        """"Visakhapatnam, Andhra Pradesh, India"; the region is skipped when it repeats the name."""
        parts = [self.name]
        if self.region and self.region.lower() != self.name.lower():
            parts.append(self.region)
        parts.append(self.country)
        return ", ".join(parts)

    def to_geo(self) -> dict[str, Any]:
        """What is stored beside `horoscope.birth_place`: everything a chart needs."""
        d = asdict(self)
        d.pop("population")
        d["label"] = self.label
        return d


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(c for c in decomposed if c.isalnum() and not unicodedata.combining(c)).lower()


@cache
def _load() -> tuple[list[Place], list[tuple[str, ...]], dict[str, Place]]:
    places: list[Place] = []
    keys: list[tuple[str, ...]] = []
    with _DATA.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            p = Place(
                id=row["id"],
                # Indian places read as families write them ("Bhimavaram",
                # not the transliteration "Bhīmavaram"); elsewhere the
                # local spelling ("São Paulo") is kept.
                name=row["ascii"] if row["cc"] == "IN" else row["name"],
                region=row["region"],
                country_code=row["cc"],
                country=row["country"],
                latitude=float(row["lat"]),
                longitude=float(row["lon"]),
                timezone=row["tz"],
                population=int(row["population"] or 0),
            )
            places.append(p)
            names = {row["name"], row["ascii"], *[a for a in row["alternates"].split("|") if a]}
            keys.append(tuple(sorted({_fold(n) for n in names if n})))
    return places, keys, {p.id: p for p in places}


def get(place_id: str) -> Place | None:
    return _load()[2].get(str(place_id))


def search(query: str, *, limit: int = 8) -> list[Place]:
    """Places whose name (or a common spelling) starts with the query.

    Ordered: exact name first, then India before elsewhere (most members are
    born in India), then by population. A trailing ", state" or ", country"
    in the query narrows by region or country."""
    raw = (query or "").strip()
    if not raw:
        return []
    head, _, tail = raw.partition(",")
    q = _fold(head)
    qualifier = _fold(tail)
    if len(q) < 2:
        return []
    places, keys, _ = _load()
    found: list[tuple[tuple[int, int, int], Place]] = []
    for p, names in zip(places, keys, strict=True):
        if not any(n.startswith(q) for n in names):
            continue
        if qualifier and not (_fold(p.region).startswith(qualifier) or _fold(p.country).startswith(qualifier) or _fold(p.country_code) == qualifier):
            continue
        exact = 0 if q in names else 1
        india = 0 if p.country_code == "IN" else 1
        found.append(((exact, india, -p.population), p))
    found.sort(key=lambda x: x[0])
    return [p for _, p in found[: max(1, min(limit, 20))]]
