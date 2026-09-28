"""Profile attribute vocabulary and the two viewing lenses (DEC-V1-023).

# [Rework contract 2026-09-17 §2/§3] The profile is one set of EAV rows
# (`profile_attribute(category, key, state, value)`); what varies by role is
# only the SHAPE it is read in:
#   * `biodata` — the conventional Indian matrimony sheet, sections in the
#     order Shaadi.com / Jeevansathi / BharatMatrimony use: Basics, Religion &
#     community, Education & career, Family, Lifestyle, Horoscope, About,
#     Partner expectations. For a family member evaluating a match.
#   * `story`   — Hinge-style: photo, identity card, prompt, photo, short
#     section, prompt… interleaved. For a candidate reading a candidate.
# Both lenses read the same rows through the same disclosure rules.
#
# `CATEGORY_KEYS` is the write-side vocabulary `PATCH /profile/{category}`
# validates against. New categories from the contract are added; the
# categories the existing editor already writes keep their keys, so nothing
# that saves today stops saving. Keys are validated, not values: values are
# JSON and the editor owns their shape (a prompt is `{q, a}`, an age range is
# `{min, max}`).
"""

from __future__ import annotations

from typing import Final

CATEGORY_KEYS: Final[dict[str, frozenset[str]]] = {
    # Existing categories (the current editor writes these).
    "education": frozenset({"highest_education_level", "education_level", "field_of_study"}),
    "profession": frozenset({"occupation", "profession", "employer"}),
    "marital_history": frozenset({"marital_status", "marital_history", "have_children"}),
    "relocation": frozenset({"relocation_willingness"}),
    "partner_preference": frozenset(
        {
            "looking_for", "age_range", "locality", "height_range", "education", "diet", "notes",
            # [DEC-V1-031] The matchmaker: the family's own words and what was
            # understood from them ({text, items}), and the wanted value and
            # importance on each 1–10 scale ({scale: {want, importance}}).
            "brief",
            "scales",
        }
    ),
    "lifestyle": frozenset({"diet", "hobbies", "smoking", "drinking"}),
    "food_travel_hobbies": frozenset({"hobbies", "food", "travel"}),
    "communication_style": frozenset({"style"}),
    "independence": frozenset({"preference"}),
    "family_involvement_expectations": frozenset({"level"}),
    "career_children_living_financial": frozenset(
        {"wants_children", "living_arrangement", "financial_outlook", "career_plans"}
    ),
    "pets": frozenset({"preference"}),
    # [DEC-V1-031] How the candidate rates themselves, 1–10, on the six
    # matchmaker scales (config/matching_engine.SCALES). Private: read only by
    # the engine, never shown to another member. Candidate only.
    "self_scales": frozenset(
        {"faith", "tradition", "family_closeness", "career", "social", "active"}
    ),
    "in_my_words": frozenset({"prompt_1", "prompt_2", "prompt_3"}),
    "self_expression": frozenset({"about_me", "i_value", "weekend"}),
    # [Migration 043] What a candidate shows before any connection, beyond the
    # fixed card: their first name, and all their photos. Closed by default.
    "openly": frozenset({"first_name", "photos"}),
    # Contract §3 — new or extended.
    # `about`: the formal introduction families write on a biodata ("Aditi is
    # a data scientist in Chennai…"). Biodata, not a prompt — so a parent who
    # created the profile may write it (DEC-V1-019).
    "basics": frozenset({"about", "height_cm", "mother_tongue", "marital_status", "have_children"}),
    "community": frozenset({"gotra", "sub_community", "native_place", "religion", "caste"}),
    "education_career": frozenset(
        {"highest_education_level", "college", "occupation", "employer", "income_band"}
    ),
    "family": frozenset(
        {
            "family_type",
            "family_values",
            "father_occupation",
            "mother_occupation",
            "brothers",
            "sisters",
            "lives_with_parents",
            "about_family",
        }
    ),
    "horoscope": frozenset(
        {
            "matching_required",
            "manglik",
            "rashi",
            "nakshatra",
            "birth_time",
            # [2026-09-27] How sure the family is of the time, and the chosen
            # place's coordinates and time zone (server-resolved; see
            # components/profile/horoscope_fields.py).
            "birth_time_accuracy",
            "birth_place",
            "birth_place_geo",
            # [2026-09-27] Which traditional matching the family follows:
            # ashtakoota (36 gunas), porutham (10 poruthams) or both.
            "matching_system",
        }
    ),
    # [BR07/FR033, baseline §12] The short game-like assessment. Ten
    # forced-choice items, each storing which of two poles the member chose.
    #
    # The dimensions are not invented. They come from the instruments that
    # actually predict marital outcomes: Olson's Circumplex model, whose
    # cohesion and flexibility axes are the backbone of PREPARE/ENRICH
    # (1,200+ published papers); PREPARE/ENRICH's own SCOPE personality
    # scales; and Gottman's findings on how a conflict starts and whether a
    # repair attempt is accepted.
    #
    # Values are pole keys, never numbers. §12 says this is "not a clinical
    # diagnosis", and §3/§4.8 forbid a score — so nothing here is ever summed,
    # ranked or turned into a percentage. Each answer is a word about how
    # someone is, shown beside the reader's own word for the same question.
    "outlook": frozenset(
        {
            "conflict_timing",
            "repair",
            "closeness",
            "planning",
            "family_voice",
            "deciding",
            "money",
            "people",
            "change",
            "work",
        }
    ),
}

# Partner preferences that stay private (matching filters, never shown).
PRIVATE_KEYS: Final[frozenset[tuple[str, str]]] = frozenset({("partner_preference", "looking_for")})

# One fact may be written under more than one (category, key) — the older
# editor's slot and the contract's. Reads take the first that has a value.
FACT_SOURCES: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    "about": (("basics", "about"),),
    "height_cm": (("basics", "height_cm"),),
    "mother_tongue": (("basics", "mother_tongue"),),
    "marital_status": (("basics", "marital_status"), ("marital_history", "marital_status")),
    "have_children": (("basics", "have_children"), ("marital_history", "have_children")),
    "relocation_willingness": (("relocation", "relocation_willingness"),),
    "gotra": (("community", "gotra"),),
    "sub_community": (("community", "sub_community"),),
    "native_place": (("community", "native_place"),),
    "highest_education_level": (
        ("education", "highest_education_level"),
        ("education_career", "highest_education_level"),
    ),
    "college": (("education_career", "college"),),
    "occupation": (("profession", "occupation"), ("education_career", "occupation")),
    "employer": (("education_career", "employer"), ("profession", "employer")),
    "income_band": (("education_career", "income_band"),),
    "family_type": (("family", "family_type"),),
    "family_values": (("family", "family_values"),),
    "father_occupation": (("family", "father_occupation"),),
    "mother_occupation": (("family", "mother_occupation"),),
    "brothers": (("family", "brothers"),),
    "sisters": (("family", "sisters"),),
    "lives_with_parents": (("family", "lives_with_parents"),),
    "about_family": (("family", "about_family"),),
    "family_involvement": (("family_involvement_expectations", "level"),),
    "diet": (("lifestyle", "diet"),),
    "smoking": (("lifestyle", "smoking"),),
    "drinking": (("lifestyle", "drinking"),),
    "hobbies": (("food_travel_hobbies", "hobbies"), ("lifestyle", "hobbies")),
    "pets": (("pets", "preference"),),
    "communication_style": (("communication_style", "style"),),
    "independence": (("independence", "preference"),),
    "wants_children": (("career_children_living_financial", "wants_children"),),
    "manglik": (("horoscope", "manglik"),),
    "rashi": (("horoscope", "rashi"),),
    "nakshatra": (("horoscope", "nakshatra"),),
    "birth_time": (("horoscope", "birth_time"),),
    "birth_time_accuracy": (("horoscope", "birth_time_accuracy"),),
    "birth_place": (("horoscope", "birth_place"),),
    "horoscope_matching": (("horoscope", "matching_required"),),
    "partner_age_range": (("partner_preference", "age_range"),),
    "partner_locality": (("partner_preference", "locality"),),
    "partner_notes": (("partner_preference", "notes"),),
}

# Biodata lens: section key -> facts, in the contract's order. `name`, `age`,
# `gender`, `locality` come from the profile row, not from attributes.
BIODATA_SECTIONS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "basics",
        (
            "name",
            "age",
            "gender",
            "height_cm",
            "marital_status",
            "have_children",
            "mother_tongue",
            "locality",
            "relocation_willingness",
        ),
    ),
    ("religion_community", ("gotra", "sub_community", "native_place")),
    (
        "education_career",
        ("highest_education_level", "college", "occupation", "employer", "income_band"),
    ),
    (
        "family",
        (
            "family_type",
            "family_values",
            "father_occupation",
            "mother_occupation",
            "brothers",
            "sisters",
            "lives_with_parents",
            "family_involvement",
            "about_family",
        ),
    ),
    (
        "lifestyle",
        ("diet", "hobbies", "pets", "communication_style", "independence", "wants_children"),
    ),
    ("horoscope", ("manglik", "rashi", "nakshatra", "birth_time", "birth_time_accuracy", "birth_place", "horoscope_matching")),
    ("about", ("about",)),  # prompts are appended as items at read time
    ("partner_expectations", ("partner_age_range", "partner_locality", "partner_notes")),
)

# Story lens: the short sections shown between prompts and photos.
STORY_SECTIONS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("basics", ("height_cm", "marital_status", "mother_tongue", "diet", "relocation_willingness")),
    ("family", ("family_type", "family_values", "family_involvement", "lives_with_parents")),
    ("lifestyle", ("hobbies", "pets", "communication_style", "independence", "wants_children")),
    ("religion_community", ("gotra", "sub_community", "native_place", "manglik")),
)

# Facts whose stored value is a code with a localised display text.
ENUM_FACTS: Final[frozenset[str]] = frozenset(
    {
        "marital_status",
        "have_children",
        "relocation_willingness",
        "highest_education_level",
        "income_band",
        "family_type",
        "family_values",
        "lives_with_parents",
        "family_involvement",
        "diet",
        "pets",
        "communication_style",
        "independence",
        "wants_children",
        "manglik",
        "rashi",
        "nakshatra",
        "birth_time_accuracy",
        "horoscope_matching",
        "gender",
    }
)
