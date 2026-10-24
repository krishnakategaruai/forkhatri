"""Interest taxonomy — the implementation-stage list FR001/BR01 deferred here.

# [FR001, FR007, TR05] One versioned taxonomy, grouped for the interest picker
# and mapped to the eight intent categories the Occurrence schema fixes, so an
# interest tag can contribute to ranking deterministically.
# [2026-10-06, ONBOARDING-REDESIGN §9] Interests are no longer asked in the first
# run; they are optional and asked later. The picker shows nine broad groups
# (each with a stable `key` the web app translates), the group "Spiritual &
# temple" was added (Satsang, Bhajan, Yatra, Temple visit, Seva), and a member
# may add their own interest ("Other — add your own"), stored as `other:<text>`
# in the member's own words. Tags are what is stored; groups are presentation,
# so regrouping never changes any member's saved interests.
# Traces to: FR001, FR003, FR007, FR008, TR01, TR05.
"""

from __future__ import annotations

from typing import Final

# group key -> (English group label, [(tag, English label, intent_category)])
INTEREST_GROUPS: Final[dict[str, tuple[str, list[tuple[str, str, str]]]]] = {
    "spiritual": (
        "Spiritual & temple",
        [
            ("satsang", "Satsang", "celebrate"),
            ("bhajan", "Bhajan", "celebrate"),
            ("yatra", "Yatra", "explore"),
            ("temple-visit", "Temple visit", "explore"),
            ("seva", "Seva", "help"),
        ],
    ),
    "sports": (
        "Sports & fitness",
        [
            ("badminton", "Badminton", "play"),
            ("cricket", "Cricket", "play"),
            ("football", "Football", "play"),
            ("running", "Running", "play"),
            ("cycling", "Cycling", "play"),
            ("yoga", "Yoga", "play"),
            ("swimming", "Swimming", "play"),
        ],
    ),
    "outdoors": (
        "Walks & treks",
        [
            ("trekking", "Trekking", "explore"),
            ("photography-walks", "Photo walks", "explore"),
        ],
    ),
    "culture": (
        "Music & culture",
        [
            ("music", "Music", "celebrate"),
            ("dance", "Dance", "celebrate"),
            ("theatre", "Theatre", "celebrate"),
            ("festivals", "Festivals", "celebrate"),
            ("poetry", "Poetry & literature", "learn"),
        ],
    ),
    "food": (
        "Food & get-togethers",
        [
            ("coffee-meetups", "Coffee meetups", "meet"),
            ("potluck", "Potluck & food", "eat"),
            ("street-food", "Street food walks", "eat"),
            ("board-games", "Board games", "play"),
        ],
    ),
    "learning": (
        "Learning",
        [
            ("coding", "Coding", "learn"),
            ("language-exchange", "Language exchange", "learn"),
            ("book-club", "Book club", "learn"),
            ("workshops", "Workshops", "learn"),
        ],
    ),
    "work": (
        "Work & career",
        [
            ("networking", "Networking", "work"),
            ("startups", "Startups", "work"),
            ("career", "Career growth", "work"),
        ],
    ),
    "family": (
        "Family & kids",
        [
            ("kids-activities", "Kids activities", "play"),
            ("parenting", "Parenting circles", "meet"),
        ],
    ),
    "volunteering": (
        "Seva & volunteering",
        [
            ("volunteering", "Volunteering", "help"),
            ("cleanup-drives", "Clean-up drives", "help"),
        ],
    ),
}

# Kept with its old shape (English group label -> items) for every existing reader (nl.py and others).
INTEREST_TAXONOMY: Final[dict[str, list[tuple[str, str, str]]]] = {label: items for (label, items) in INTEREST_GROUPS.values()}

TAG_TO_CATEGORY: Final[dict[str, str]] = {tag: category for items in INTEREST_TAXONOMY.values() for (tag, _label, category) in items}
TAG_LABELS: Final[dict[str, str]] = {tag: label for items in INTEREST_TAXONOMY.values() for (tag, label, _c) in items}

# "Other — add your own": the member's own words, kept as written (trimmed), never lower-cased.
OTHER_PREFIX: Final[str] = "other:"
OTHER_MAX_CHARS: Final[int] = 40
OTHER_MAX_COUNT: Final[int] = 5
INTERESTS_MAX_COUNT: Final[int] = 40


def interest_label(tag: str) -> str:
    """The English label for a taxonomy tag, or the member's own words for an `other:` interest."""
    if tag.startswith(OTHER_PREFIX):
        return tag[len(OTHER_PREFIX) :]
    return TAG_LABELS.get(tag, tag)


class InvalidInterests(ValueError):
    def __init__(self, bad: list[str]) -> None:
        super().__init__(f"invalid interests: {bad}")
        self.bad = bad


def normalise_interests(values: list[str], *, already_saved: set[str] | frozenset[str] = frozenset()) -> list[str]:
    """[FR003] Validate a member's chosen interests: known taxonomy tags, plus at most five
    `other:<own words>` entries of 1-40 characters. A tag the member already has is always
    accepted as it is (older free tags stay removable and keepable). Duplicates collapse;
    order is kept. Raises InvalidInterests naming what was not accepted."""
    out: list[str] = []
    seen: set[str] = set()
    bad: list[str] = []
    others = 0
    for raw in values:
        v = (raw or "").strip()
        if not v:
            continue
        if v in already_saved:
            if v.lower() in seen:
                continue
            seen.add(v.lower())
            out.append(v)
            continue
        if v.lower().startswith(OTHER_PREFIX):
            words = " ".join(v[len(OTHER_PREFIX) :].split())
            if not words or len(words) > OTHER_MAX_CHARS:
                bad.append(v)
                continue
            tag = f"{OTHER_PREFIX}{words}"
            key = tag.lower()
            if key in seen:
                continue
            others += 1
            if others > OTHER_MAX_COUNT:
                bad.append(v)
                continue
        else:
            tag = v.lower()
            key = tag
            if tag not in TAG_LABELS:
                bad.append(v)
                continue
            if key in seen:
                continue
        seen.add(key)
        out.append(tag)
    if len(out) > INTERESTS_MAX_COUNT:
        bad.extend(out[INTERESTS_MAX_COUNT:])
    if bad:
        raise InvalidInterests(bad)
    return out


def taxonomy_payload() -> list[dict]:
    return [
        {
            "key": key,
            "group": label,
            "interests": [{"tag": t, "label": lbl, "intent_category": c} for (t, lbl, c) in items],
        }
        for key, (label, items) in INTEREST_GROUPS.items()
    ]
