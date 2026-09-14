"""DEC-V1-001's three-tier profile field assignment, as configuration.

# [TR001/TR003/TR005] Which fields belong to which completeness tier is one
# named list, not a rule each component re-derives.
# Approach: `07a-er-model.md` deliberately did NOT make tier membership a
# database column ("avoids a second, potentially-drifting source of truth"), so
# it has to live somewhere in application config — here. TR003's shared
# `is_discoverable()` gate and TR005's completeness display both read these
# exact tuples, which is what makes the TR003/TR027 non-divergence contract test
# testable at all: there is only one list to diverge from.
# Traces to: TR001, TR003, TR005, TR027, SP001, SP003, DEC-V1-001.
"""

from __future__ import annotations

from typing import Final

# --- Existence tier: the minimum to save a profile at all ---------------------
# These map onto first-class, indexed columns on `mangaly_profile.profile`
# (plus at least one `mangaly_profile.profile_media` row), NOT onto
# `profile_attribute` rows. Phone/identifier already exists from sign-up
# (TR092), so it is deliberately absent here.
EXISTENCE_TIER_COLUMNS: Final[tuple[str, ...]] = (
    "name",
    "date_of_birth",
    "gender",
    "city_locality",
)
EXISTENCE_TIER_REQUIRES_AT_LEAST_ONE_PHOTO: Final[bool] = True


# --- Discoverability tier: the minimum to clear BR06's Discovery gate ---------
# Stored as (category, attribute_key) pairs against `profile_attribute`.
DISCOVERABILITY_TIER_ATTRIBUTES: Final[tuple[tuple[str, str], ...]] = (
    ("education", "highest_education_level"),
    ("profession", "occupation"),
    ("marital_history", "marital_status"),
    ("relocation", "relocation_willingness"),
)

# DEC-V1-001 requires "at least one partner-preference field (age range OR
# locality)" — an any-of requirement, not an all-of one, so it is modelled
# separately rather than folded into the tuple above where it would silently
# become mandatory-both.
DISCOVERABILITY_TIER_PARTNER_PREFERENCE_ANY_OF: Final[tuple[tuple[str, str], ...]] = (
    ("partner_preference", "age_range"),
    ("partner_preference", "locality"),
)


# --- Enhanced-matching tier: optional, improves Compatibility richness only ----
# DEC-V1-001 defines this tier as "everything else", so it is expressed as the
# open category set rather than an exhaustive key list — anything not in the two
# tiers above is enhanced-matching by construction, and therefore can never gate
# anything (TR004).
ENHANCED_MATCHING_CATEGORIES: Final[tuple[str, ...]] = (
    "lifestyle",
    "food_travel_hobbies",
    "communication_style",
    "independence",
    "family_involvement_expectations",
    "career_children_living_financial",
    "pets",
    "horoscope",
)
