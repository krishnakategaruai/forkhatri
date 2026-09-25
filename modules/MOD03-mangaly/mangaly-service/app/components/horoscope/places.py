"""Birth place -> latitude/longitude, from a bundled list of Indian places.

`data/indian_places.csv` holds the large cities of India plus every district
headquarters of Telangana, Andhra Pradesh, Karnataka, Tamil Nadu, Kerala,
Maharashtra, Punjab, Delhi and Gujarat (columns: name, state, lat, lon,
aliases). Coordinates are town centres to two decimals: a 0.01 deg error is
about 1 km, which moves the Lagna by well under an arc-minute.

The profile field `horoscope.birth_place` is free text, so matching is by a
normalised form: lower-case, ASCII letters and digits only, no spaces or
punctuation ("Vizag", "Visakhapatnam", "VISAKHAPATNAM " and "Vishakapatnam"
all resolve), with the common alternative spellings listed as aliases in the
CSV. A trailing state or country ("Guntur, Andhra Pradesh", "Pune, India")
is stripped before matching. An unknown place gives None and the chart is
computed without a Lagna, saying so.

Every Indian place is in Asia/Kolkata (IST, UTC+5:30, no daylight saving),
which is why the CSV carries no timezone column.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Final

_DATA: Final = Path(__file__).parent / "data" / "indian_places.csv"
_NON_ALNUM: Final = re.compile(r"[^a-z0-9]+")
_TRAILING_QUALIFIERS: Final = (
    "india",
    "bharat",
    "telangana",
    "andhrapradesh",
    "andhra",
    "ap",
    "karnataka",
    "tamilnadu",
    "tn",
    "kerala",
    "maharashtra",
    "punjab",
    "delhi",
    "newdelhi",
    "gujarat",
    "district",
    "dist",
    "city",
    "town",
)


@dataclass(frozen=True, slots=True)
class Place:
    name: str
    state: str
    lat: float
    lon: float


def normalise(text: str) -> str:
    return _NON_ALNUM.sub("", text.strip().lower())


@cache
def _index() -> dict[str, Place]:
    index: dict[str, Place] = {}
    with _DATA.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            place = Place(
                name=row["name"].strip(),
                state=row["state"].strip(),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
            )
            keys = [place.name] + [a for a in (row.get("aliases") or "").split("|") if a.strip()]
            for key in keys:
                index.setdefault(normalise(key), place)
    return index


def lookup(birth_place: str | None) -> Place | None:
    """The place a person typed, if we know it; None otherwise."""
    if not birth_place or not birth_place.strip():
        return None
    index = _index()
    # "Guntur, Andhra Pradesh" -> try the first comma-separated part first.
    candidates = [birth_place]
    if "," in birth_place:
        candidates.append(birth_place.split(",")[0])
    for candidate in candidates:
        key = normalise(candidate)
        if key in index:
            return index[key]
        # "hyderabadtelangana" -> strip a known trailing qualifier and retry.
        for qualifier in _TRAILING_QUALIFIERS:
            if key.endswith(qualifier) and len(key) > len(qualifier) + 2:
                stripped = key[: -len(qualifier)]
                if stripped in index:
                    return index[stripped]
    return None


def known_place_count() -> int:
    return len({p.name for p in _index().values()})
