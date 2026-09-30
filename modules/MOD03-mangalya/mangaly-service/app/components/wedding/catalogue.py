"""What Mangalya suggests at each stage, and how each kind of place is found
in OpenStreetMap.

The stages follow the journey families already know: pelli choopulu (the
first meeting), nischitartham (the families agree), then the muhurtham is
fixed and the wedding is arranged. Only what helps at a stage is shown at
it: a first meeting needs a calm café, not a function hall.

OSM tags are from the research note
(modules/MOD03-mangalya/research/wedding-services-partners.md, §6). Decorators
and cooks are barely mapped in India, so those lean on florists and caterers
now and on Mangalya partners later.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final

__all__ = ["CATEGORIES", "STAGES", "STAGE_CATEGORIES", "Category", "classify", "overpass_filters"]

STAGES: Final = ("first_meeting", "families_agreed", "wedding_fixed")

Tags = Mapping[str, str]


def _name_has(pattern: str) -> Callable[[Tags], bool]:
    rx = re.compile(pattern, re.IGNORECASE)
    return lambda t: bool(rx.search(t.get("name", "")))


_HALL_NAME = (
    r"function hall|convention|banquet|kalyana ?mandap|marriage hall"
    r"|kalyanamandapam|gardens? function"
)


@dataclass(frozen=True, slots=True)
class Category:
    key: str
    radius_km: float
    # Overpass selectors (without the area clause) used by the import script.
    filters: tuple[str, ...]
    # The same rules in Python, to sort one mixed Overpass answer into categories.
    match: Callable[[Tags], bool]


CATEGORIES: Final[dict[str, Category]] = {
    c.key: c
    for c in (
        Category(
            "cafe",
            6,
            ('nwr["amenity"="cafe"]["name"]',),
            lambda t: t.get("amenity") == "cafe",
        ),
        Category(
            "restaurant",
            6,
            ('nwr["amenity"="restaurant"]["name"]',),
            lambda t: t.get("amenity") == "restaurant",
        ),
        Category(
            "hall",
            25,
            (
                'nwr["amenity"~"^(events_venue|conference_centre)$"]["name"]',
                f'nwr["amenity"="community_centre"]["name"~"{_HALL_NAME}|hall",i]',
                # A name search over every named building is too slow for the
                # shared server; halls are nearly always tagged as an amenity.
                f'nwr["amenity"]["name"~"{_HALL_NAME}",i]',
            ),
            lambda t: (
                t.get("amenity") in ("events_venue", "conference_centre")
                or (t.get("amenity") == "community_centre" and _name_has(_HALL_NAME + "|hall")(t))
                or _name_has(_HALL_NAME)(t)
            ),
        ),
        Category(
            "photographer",
            25,
            ('nwr["craft"="photographer"]["name"]', 'nwr["shop"="photo"]["name"]'),
            lambda t: t.get("craft") == "photographer" or t.get("shop") == "photo",
        ),
        Category(
            "jewellery",
            15,
            ('nwr["shop"="jewelry"]["name"]',),
            lambda t: t.get("shop") == "jewelry",
        ),
        Category(
            "clothes",
            15,
            ('nwr["shop"="clothes"]["name"~"saree|sari|silk|pattu|wedding|bridal|sherwani",i]',),
            lambda t: (
                t.get("shop") == "clothes"
                and _name_has(r"saree|sari|silk|pattu|wedding|bridal|sherwani")(t)
            ),
        ),
        Category(
            "decoration",
            25,
            ('nwr["shop"~"^(florist|party)$"]["name"]',),
            lambda t: t.get("shop") in ("florist", "party"),
        ),
        Category(
            "caterer",
            30,
            ('nwr["craft"="caterer"]["name"]',),
            lambda t: t.get("craft") == "caterer",
        ),
        Category(
            "beauty",
            12,
            ('nwr["shop"="beauty"]["name"]',),
            lambda t: t.get("shop") == "beauty",
        ),
        Category(
            "car_rental",
            30,
            ('nwr["amenity"="car_rental"]["name"]',),
            lambda t: t.get("amenity") == "car_rental",
        ),
    )
}

# What each stage offers, in the order families need it.
STAGE_CATEGORIES: Final[dict[str, tuple[str, ...]]] = {
    "first_meeting": ("cafe", "restaurant"),
    "families_agreed": ("hall", "jewellery", "clothes", "photographer", "caterer"),
    "wedding_fixed": ("hall", "decoration", "photographer", "caterer", "beauty", "car_rental"),
}


def classify(tags: Tags) -> str | None:
    """The first category an OSM element belongs to; halls win over the rest
    so a "convention" restaurant-and-hall lands with the halls."""
    if not tags.get("name"):
        return None
    order = ("hall", *[k for k in CATEGORIES if k != "hall"])
    for key in order:
        if CATEGORIES[key].match(tags):
            return key
    return None


def overpass_filters() -> list[str]:
    return [f for c in CATEGORIES.values() for f in c.filters]
