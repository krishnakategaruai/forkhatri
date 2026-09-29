"""The AI matching engine's vocabulary, tables and weights (DEC-V1-031).

# [DEC-V1-031, owner 2026-09-27] Matching reads three things a member gives:
#   1. their own words ("Strict vegetarian, Hyderabad or Bengaluru, height
#      doesn't matter much"), understood into the items below, each with an
#      importance from 1 to 10 the family can adjust — 10 means it must be met;
#   2. six 1–10 scales about themselves (candidate only);
#   3. the same six scales for the partner they want, each with an importance.
# The engine compares one side's facts and self-ratings with the other side's
# wishes, in BOTH directions, and returns a 1–10 score that orders Discover.
# The number is never shown to a member (baseline §3/§4.8, PRODUCT-GUARDRAILS
# "never a public numeric score"); members see a word ("Strong match") and
# the factual reasons. Popularity weight stays 0 (DEC-V1-002): nothing here
# reads who viewed, liked or messaged whom.
#
# Every value below is a versioned setting, not a literal at a call site.
"""

from __future__ import annotations

from typing import Final

ENGINE_VERSION: Final[str] = "v3-2026-09-27"

# --- What the understood items may speak about -------------------------------
# A closed vocabulary: the AI's answer is validated against it, so a word the
# engine cannot check never becomes a silent rule.
DIETS: Final[tuple[str, ...]] = ("vegetarian", "eggetarian", "vegan", "non_vegetarian")
HABIT_LEVELS: Final[tuple[str, ...]] = ("never", "occasionally", "regularly")
EDUCATION_LEVELS: Final[tuple[str, ...]] = ("high_school", "bachelors", "masters", "doctorate")
INCOME_BANDS: Final[tuple[str, ...]] = ("under_5", "5_10", "10_20", "20_40", "40_plus")
MOTHER_TONGUES: Final[tuple[str, ...]] = (
    "telugu", "tamil", "kannada", "hindi", "punjabi", "marathi", "gujarati", "english", "other",
)
SUB_COMMUNITIES: Final[tuple[str, ...]] = ("khatri", "arora", "sood", "bhatia", "other")
FAMILY_TYPES: Final[tuple[str, ...]] = ("joint", "nuclear", "extended")
FAMILY_VALUES: Final[tuple[str, ...]] = ("traditional", "moderate", "liberal")
MANGLIK: Final[tuple[str, ...]] = ("yes", "no", "partial")
RELOCATION: Final[tuple[str, ...]] = ("yes", "no", "open_to_discussion")

# field -> (kind, allowed values). "range" items carry min/max; "place" items
# carry free-text city names; "tags" items carry free-text hobbies.
ITEM_FIELDS: Final[dict[str, tuple[str, tuple[str, ...]]]] = {
    "age": ("range", ()),
    "height_cm": ("range", ()),
    "locality": ("place", ()),
    "relocation": ("enum", RELOCATION),
    "diet": ("enum", DIETS),
    "smoking": ("enum", HABIT_LEVELS),
    "drinking": ("enum", HABIT_LEVELS),
    "education": ("enum", EDUCATION_LEVELS),
    "income_band": ("enum", INCOME_BANDS),
    "mother_tongue": ("enum", MOTHER_TONGUES),
    "sub_community": ("enum", SUB_COMMUNITIES),
    "family_type": ("enum", FAMILY_TYPES),
    "family_values": ("enum", FAMILY_VALUES),
    "manglik": ("enum", MANGLIK),
    "hobbies": ("tags", ()),
}
# Fields where the listed values are a floor: "at least a master's" also
# accepts a doctorate; "never/occasionally drinks" is a ceiling instead.
ORDERED_FLOOR: Final[dict[str, tuple[str, ...]]] = {
    "education": EDUCATION_LEVELS,
    "income_band": INCOME_BANDS,
}
ORDERED_CEILING: Final[dict[str, tuple[str, ...]]] = {
    "smoking": HABIT_LEVELS,
    "drinking": HABIT_LEVELS,
}

MUST_HAVE: Final[int] = 10  # importance that removes anyone who does not meet it
DEFAULT_IMPORTANCE: Final[int] = 6
MAX_ITEMS: Final[int] = 20
MAX_BRIEF_CHARS: Final[int] = 1500

# --- The six 1–10 scales -----------------------------------------------------
# One question each, asked about yourself and about the partner you want.
# Chosen to NOT repeat the ten outlook choices (DEC-V1-017), which stay
# candidate-to-candidate after a connection; these are family-level axes an
# Indian match is usually weighed on, each a spectrum with no better end.
SCALES: Final[tuple[str, ...]] = (
    "faith",             # 1 rarely practise … 10 daily prayer and rituals
    "tradition",         # 1 modern outlook … 10 traditional outlook
    "family_closeness",  # 1 independent household … 10 live close to / with family
    "career",            # 1 career is one part of life … 10 career is central
    "social",            # 1 quiet evenings at home … 10 out with people often
    "active",            # 1 relaxed … 10 very active, sport and fitness
)
SCALE_MIN: Final[int] = 1
SCALE_MAX: Final[int] = 10

# --- What matters (asked once at setup, editable later) ----------------------
# [Owner, 2026-09-28] Besides their own words, a family says how much each of
# these matters, 1–10. A theme that matters becomes a "like us" wish built
# from the seeker's OWN facts (nothing re-asked): "same roots" at 8 means
# "speaks our mother tongue, from our community", importance 8. A field the
# family already spoke about in their words keeps their words. 10 is a must,
# the same as everywhere else. Horoscope has no field here: it orders the
# Discover rows and the family's own filter decides who is removed.
PRIORITY_THEMES: Final[dict[str, tuple[str, ...]]] = {
    "horoscope": (),
    "roots": ("mother_tongue", "sub_community"),
    "near": ("locality",),
    "life": ("diet", "hobbies"),
    "family_view": ("family_values", "family_type"),
    "education": ("education",),
}

# --- Horoscope row in Discover ------------------------------------------------
# Traditional thresholds: 18 of 36 gunas is the usual minimum for a match.
HOROSCOPE_SHELF_MIN_GUNA: Final[float] = 18.0
GUNA_MAX: Final[int] = 36

# --- Compatibility tables ----------------------------------------------------
# Diet, read as "how livable is a shared kitchen": a vegetarian home and a
# non-vegetarian partner is the classic hard mismatch; eggetarian sits close
# to vegetarian. Rows are what one side IS, columns what the other side IS.
DIET_COMPAT: Final[dict[str, dict[str, float]]] = {
    "vegetarian": {"vegetarian": 1.0, "vegan": 1.0, "eggetarian": 0.6, "non_vegetarian": 0.2},
    "vegan": {"vegan": 1.0, "vegetarian": 0.8, "eggetarian": 0.4, "non_vegetarian": 0.1},
    "eggetarian": {"eggetarian": 1.0, "vegetarian": 1.0, "vegan": 0.9, "non_vegetarian": 0.6},
    "non_vegetarian": {"non_vegetarian": 1.0, "eggetarian": 1.0, "vegetarian": 0.9, "vegan": 0.8},
}
# Family values: neighbours on the traditional–liberal line half-agree.
FAMILY_VALUES_COMPAT: Final[dict[tuple[str, str], float]] = {
    ("traditional", "moderate"): 0.5,
    ("moderate", "liberal"): 0.5,
    ("traditional", "liberal"): 0.0,
}

# --- Distance ----------------------------------------------------------------
# Full credit within the same metro, then a smooth Gaussian fall-off:
# exp(-((d - full)/scale)^2) gives ~0.9 at 100 km, ~0.5 at 200 km, ~0.05 at 400 km.
DISTANCE_FULL_KM: Final[float] = 30.0
DISTANCE_SCALE_KM: Final[float] = 210.0
# Someone who said they would relocate never falls below this for distance.
RELOCATION_FLOOR: Final[float] = 0.6
# A "nearby" reason is shown for a different city within this distance.
NEARBY_REASON_KM: Final[float] = 80.0

# --- Implicit terms (the member said nothing, but their own facts speak) ----
# A vegetarian who never mentioned diet still lives in a vegetarian kitchen.
IMPLICIT_DIET_IMPORTANCE: Final[int] = 3
# Where someone lives always matters a little, even unstated.
IMPLICIT_DISTANCE_IMPORTANCE: Final[int] = 3

# --- Final blend and the words members see -----------------------------------
# The pair score is the harmonic mean of both directions (a one-way fit never
# passes as mutual, DEC-V1-030); profile evidence breaks near-ties.
PAIR_WEIGHT: Final[float] = 0.85
EVIDENCE_WEIGHT: Final[float] = 0.15
NEUTRAL_FIT: Final[float] = 0.5
# Shrinkage toward neutral: every direction starts as if PRIOR_WEIGHT of
# importance had already been checked at NEUTRAL_FIT. One met wish is then a
# modest signal, many met wishes a strong one — so "Strong match" needs real
# evidence, not a single stated age range that everyone happens to meet.
PRIOR_WEIGHT: Final[float] = 6.0
# 1–10 thresholds for the word shown; below GOOD shows no word at all —
# "weak match" would judge a person, which the product never does. Set from
# the real spread of development pairs (2026-09-27: median 7.6, top decile
# 8.2) so the word stays selective — roughly the top sixth "Strong", the next
# third "Good" — rather than decorating every tile.
LABEL_STRONG: Final[float] = 8.0
LABEL_GOOD: Final[float] = 7.5
