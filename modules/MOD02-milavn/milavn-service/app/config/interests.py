"""Interest taxonomy — the implementation-stage list FR001/BR01 deferred here.

# [FR001, FR007, TR05] One versioned taxonomy, grouped for the onboarding
# chip grid (UX02) and mapped to the eight intent categories the Occurrence
# schema fixes, so an interest tag can contribute to ranking deterministically.
# Traces to: FR001, FR007, FR008, TR01, TR05.
"""

from __future__ import annotations

from typing import Final

# group -> [(tag, label, intent_category)]
INTEREST_TAXONOMY: Final[dict[str, list[tuple[str, str, str]]]] = {
    "Sports & Play": [
        ("badminton", "Badminton", "play"),
        ("cricket", "Cricket", "play"),
        ("football", "Football", "play"),
        ("running", "Running", "play"),
        ("cycling", "Cycling", "play"),
        ("yoga", "Yoga", "play"),
        ("trekking", "Trekking", "explore"),
        ("swimming", "Swimming", "play"),
    ],
    "Social": [
        ("coffee-meetups", "Coffee meetups", "meet"),
        ("board-games", "Board games", "play"),
        ("potluck", "Potluck & food", "eat"),
        ("street-food", "Street food walks", "eat"),
        ("photography-walks", "Photo walks", "explore"),
    ],
    "Culture": [
        ("music", "Music", "celebrate"),
        ("dance", "Dance", "celebrate"),
        ("theatre", "Theatre", "celebrate"),
        ("festivals", "Festivals", "celebrate"),
        ("poetry", "Poetry & literature", "learn"),
    ],
    "Learning": [
        ("coding", "Coding", "learn"),
        ("language-exchange", "Language exchange", "learn"),
        ("book-club", "Book club", "learn"),
        ("workshops", "Workshops", "learn"),
    ],
    "Work & Career": [
        ("networking", "Networking", "work"),
        ("startups", "Startups", "work"),
        ("career", "Career growth", "work"),
    ],
    "Family & Community": [
        ("kids-activities", "Kids activities", "play"),
        ("parenting", "Parenting circles", "meet"),
        ("volunteering", "Volunteering", "help"),
        ("cleanup-drives", "Clean-up drives", "help"),
    ],
}

TAG_TO_CATEGORY: Final[dict[str, str]] = {tag: category for items in INTEREST_TAXONOMY.values() for (tag, _label, category) in items}
TAG_LABELS: Final[dict[str, str]] = {tag: label for items in INTEREST_TAXONOMY.values() for (tag, label, _c) in items}


def taxonomy_payload() -> list[dict]:
    return [
        {
            "group": group,
            "interests": [{"tag": t, "label": lbl, "intent_category": c} for (t, lbl, c) in items],
        }
        for group, items in INTEREST_TAXONOMY.items()
    ]
