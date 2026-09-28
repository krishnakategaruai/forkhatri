"""Put a member's city on the map: free-text city → a known place with coordinates.

Modules store city as the member typed or picked it ("Hyderabad, Telangana",
"Bangalore", "Kochi"). This resolves it against the bundled GeoNames subset
(data/places.tsv, see data/ATTRIBUTION.md): the first comma part is the place,
the remaining parts narrow it by state or country. Ties go to India (the
product is India-first, so a bare "Hyderabad" is Telangana's, not Sindh's) and
then to the larger place.
"""

from __future__ import annotations

import csv
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "places.tsv"

# Country words people add after a city, mapped to ISO 3166-1 alpha-2.
_COUNTRY_WORDS = {
    "india": "IN", "bharat": "IN", "usa": "US", "us": "US", "united states": "US", "america": "US",
    "uk": "GB", "united kingdom": "GB", "england": "GB", "canada": "CA", "australia": "AU",
    "uae": "AE", "dubai": "AE", "singapore": "SG", "new zealand": "NZ", "germany": "DE",
}


@dataclass(frozen=True, slots=True)
class Place:
    name: str
    region: str
    cc: str
    lat: float
    lon: float
    population: int


def fold(value: str) -> str:
    stripped = "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))
    return " ".join(stripped.lower().replace(".", " ").split())


@lru_cache(maxsize=1)
def _index() -> dict[str, list[Place]]:
    index: dict[str, list[Place]] = {}
    with DATA.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            place = Place(row["name"], row["region"], row["cc"], float(row["lat"]), float(row["lon"]), int(row["population"]))
            keys = {fold(row["name"]), fold(row["ascii"])}
            keys.update(fold(a) for a in row["alternates"].split("|") if a)
            for key in keys:
                if key:
                    index.setdefault(key, []).append(place)
    return index


@lru_cache(maxsize=4096)
def resolve(text: str | None) -> Place | None:
    if not text or not text.strip():
        return None
    parts = [fold(p) for p in text.split(",") if p.strip()]
    if not parts:
        return None
    index = _index()
    candidates = index.get(parts[0]) or index.get(fold(text)) or []
    if not candidates:
        return None
    hints = parts[1:]
    country_hint = next((_COUNTRY_WORDS[h] for h in hints if h in _COUNTRY_WORDS), None)
    region_hints = {h for h in hints if h not in _COUNTRY_WORDS}

    def score(place: Place) -> tuple[int, int, int, int]:
        return (
            1 if region_hints and fold(place.region) in region_hints else 0,
            1 if country_hint and place.cc == country_hint else 0,
            1 if place.cc == "IN" else 0,
            place.population,
        )

    return max(candidates, key=score)
