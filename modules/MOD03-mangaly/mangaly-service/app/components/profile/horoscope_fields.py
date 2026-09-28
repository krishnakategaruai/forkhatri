"""Horoscope fields — what a kundli needs, checked when it is saved.

A Guna Milan is only as good as its inputs, so the horoscope category is the
one profile category whose values are validated, not only its keys:

  * `birth_time`          "HH:MM", 24-hour local time at the place of birth.
  * `birth_time_accuracy` how sure the family is of that time:
                          exact | about_15 | about_30 | about_60 | about_120 |
                          unknown. "unknown" withdraws `birth_time` (a stored
                          time nobody vouches for would be treated as real).
  * `birth_place_geo`     sent as {"place_id": "..."}; the server replaces it
                          with the place's name, coordinates and IANA time
                          zone from the bundled list, and writes the readable
                          label into `birth_place`. Coordinates and zone never
                          come from the browser.
  * `nakshatra`, `rashi`  one of the fixed keys the editor offers.

Owner decision (2026-09-27): birth time and place of birth are part of the
public biodata — families check kundlis before connecting — so nothing here
hides them; this module only makes sure they are right.
"""

from __future__ import annotations

import re
from typing import Any, Final

from app.components.places import interface as places

__all__ = ["InvalidAttributeValue", "normalize"]

TIME_RE: Final = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
ACCURACY: Final = frozenset({"exact", "about_15", "about_30", "about_60", "about_120", "unknown"})
NAKSHATRAS: Final = (
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha",
    "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati",
)
MATCHING_SYSTEMS: Final = frozenset({"ashtakoota", "porutham", "both"})
RASHIS: Final = (
    "mesh", "vrishabh", "mithun", "kark", "simha", "kanya", "tula", "vrishchik", "dhanu", "makar", "kumbh", "meen",
)

# Uncertainty in minutes either side, for the calculation service.
ACCURACY_MINUTES: Final[dict[str, int | None]] = {
    "exact": 0, "about_15": 15, "about_30": 30, "about_60": 60, "about_120": 120, "unknown": None,
}


class InvalidAttributeValue(Exception):
    """A value the field cannot hold. Names the field only, never the value."""

    def __init__(self, category: str, key: str, reason: str) -> None:
        super().__init__(f"{category}.{key}: {reason}")
        self.category = category
        self.key = key
        self.reason = reason


def _bad(key: str, reason: str) -> InvalidAttributeValue:
    return InvalidAttributeValue("horoscope", key, reason)


def normalize(attributes: dict[str, tuple[Any, Any]], value_state: Any, declined_state: Any) -> dict[str, tuple[Any, Any]]:
    """Validate and complete a horoscope PATCH. `attributes` maps key → (state, value)."""
    out = dict(attributes)

    def value_of(key: str) -> Any:
        state, value = out.get(key, (None, None))
        return value if state == value_state else None

    if "birth_time" in out and out["birth_time"][0] == value_state:
        v = out["birth_time"][1]
        if not isinstance(v, str) or not TIME_RE.match(v.strip()):
            raise _bad("birth_time", "must be HH:MM (24-hour)")
        out["birth_time"] = (value_state, v.strip())

    if "birth_time_accuracy" in out and out["birth_time_accuracy"][0] == value_state:
        v = out["birth_time_accuracy"][1]
        if v not in ACCURACY:
            raise _bad("birth_time_accuracy", "unknown option")
        if v == "unknown":
            out["birth_time"] = (declined_state, None)
        elif value_of("birth_time") is None and "birth_time" in out:
            raise _bad("birth_time", "a time is needed unless the time is unknown")

    if "birth_place_geo" in out:
        state, v = out["birth_place_geo"]
        if state == value_state:
            place_id = v.get("place_id") if isinstance(v, dict) else None
            place = places.get(str(place_id)) if place_id is not None else None
            if place is None:
                raise _bad("birth_place_geo", "choose a place from the list")
            out["birth_place_geo"] = (value_state, place.to_geo())
            out["birth_place"] = (value_state, place.label)
        else:
            out["birth_place"] = (state, None)
    elif "birth_place" in out and out["birth_place"][0] == value_state:
        # A typed place with no chosen match cannot be used for a chart.
        raise _bad("birth_place", "choose a place from the list")
    elif "birth_place" in out:
        out["birth_place_geo"] = (out["birth_place"][0], None)

    for key, allowed in (("nakshatra", NAKSHATRAS), ("rashi", RASHIS), ("matching_system", tuple(MATCHING_SYSTEMS))):
        if key in out and out[key][0] == value_state and out[key][1] not in allowed:
            raise _bad(key, "unknown option")

    return out
