"""Unit tests for the AI matching engine and the matchmaker's keyword reader
(DEC-V1-031). Pure functions only; no database, no network (the keyword
reader is what runs when no Claude key is configured).
"""

from __future__ import annotations

import asyncio
from datetime import date

import pytest

from app.components.compatibility.engine import (
    direction_fit,
    fails_must,
    item_fit,
    label_for,
    pair_score,
    wishes,
)
from app.components.compatibility.understand import clean_items, clean_scales, understand

HYDERABAD = {"lat": 17.385, "lon": 78.4867}
SECUNDERABAD = {"lat": 17.4399, "lon": 78.4983}
VIJAYAWADA = {"lat": 16.5062, "lon": 80.648}
DELHI = {"lat": 28.6139, "lon": 77.209}


def born(age: int) -> str:
    return date(date.today().year - age, 1, 1).isoformat()


def person(**facts: object) -> dict:
    base = {"date_of_birth": born(29), "evidence_completeness": 0.0}
    return {**base, **facts}


def brief(*items: dict) -> list[dict]:
    return list(items)


# --- Must-haves -------------------------------------------------------------


def test_Given_a_must_have_vegetarian_When_the_other_is_non_vegetarian_Then_they_are_left_out():
    seeker = person(partner_brief=brief({"field": "diet", "values": ["vegetarian"], "importance": 10}))

    assert fails_must(seeker, person(lifestyle_diet="non_vegetarian"))
    assert not fails_must(seeker, person(lifestyle_diet="vegetarian"))


def test_Given_a_must_have_When_the_other_left_the_field_blank_Then_they_are_not_removed():
    # Unlike a Hinge dealbreaker, a blank never hides anyone.
    seeker = person(partner_brief=brief({"field": "drinking", "values": ["never"], "importance": 10}))

    assert not fails_must(seeker, person())


def test_Given_a_must_live_in_city_When_the_other_would_relocate_Then_they_stay():
    seeker = person(partner_brief=brief({"field": "locality", "values": ["Hyderabad"], "importance": 10}))

    assert fails_must(seeker, person(locality="Delhi", relocation_willingness="no"))
    assert not fails_must(seeker, person(locality="Delhi", relocation_willingness="yes"))


# --- Soft wishes, importance and the scales ---------------------------------


def test_Given_eggetarian_against_a_vegetarian_wish_When_soft_Then_partial_credit_not_zero():
    wish = wishes(person(partner_brief=brief({"field": "diet", "values": ["vegetarian"], "importance": 6})))[0]

    assert item_fit(wish, person(lifestyle_diet="eggetarian")) == pytest.approx(0.6)
    assert item_fit(wish, person(lifestyle_diet="non_vegetarian")) == pytest.approx(0.2)


def test_Given_at_least_masters_When_the_other_has_a_doctorate_Then_it_counts_as_met():
    wish = wishes(person(partner_brief=brief({"field": "education", "values": ["masters"], "importance": 7})))[0]

    assert item_fit(wish, person(education_level="doctorate")) == 1.0
    assert item_fit(wish, person(education_level="bachelors")) == pytest.approx(0.4)


def test_Given_social_drinking_accepted_When_the_other_drinks_regularly_Then_it_is_one_step_over():
    wish = wishes(person(partner_brief=brief({"field": "drinking", "values": ["never", "occasionally"], "importance": 7})))[0]

    assert item_fit(wish, person(drinking="occasionally")) == 1.0
    assert item_fit(wish, person(drinking="regularly")) == pytest.approx(0.3)


def test_Given_an_important_and_an_unimportant_wish_When_scored_Then_importance_decides_the_weight():
    seeker = person(
        partner_brief=brief(
            {"field": "diet", "values": ["vegetarian"], "importance": 10},
            {"field": "height_cm", "min": 175, "importance": 2},
        )
    )
    short_vegetarian = person(lifestyle_diet="vegetarian", height_cm=160)
    tall_non_vegetarian = person(lifestyle_diet="non_vegetarian", height_cm=180)

    assert direction_fit(seeker, short_vegetarian) > direction_fit(seeker, tall_non_vegetarian)


def test_Given_scales_When_self_ratings_are_close_to_what_is_wanted_Then_the_fit_is_higher():
    seeker = person(partner_scales={"faith": {"want": 8, "importance": 9}, "career": {"want": 5, "importance": 3}})

    close = person(self_scales={"faith": 8, "career": 9})
    far = person(self_scales={"faith": 2, "career": 5})

    assert direction_fit(seeker, close) > direction_fit(seeker, far)


# --- Distance ---------------------------------------------------------------


def test_Given_Secunderabad_When_Hyderabad_is_wanted_Then_it_is_near_not_a_miss():
    seeker = person(partner_brief=brief({"field": "locality", "values": ["Hyderabad"], "importance": 7, "geo": [HYDERABAD]}))
    wish = wishes(seeker)[0]

    assert item_fit(wish, person(locality="Secunderabad", geo=SECUNDERABAD)) == 1.0
    vijayawada = item_fit(wish, person(locality="Vijayawada", geo=VIJAYAWADA))
    delhi = item_fit(wish, person(locality="Delhi", geo=DELHI))
    assert 0.3 < vijayawada < 0.8
    assert delhi < 0.01


def test_Given_no_stated_place_When_both_have_coordinates_Then_distance_still_counts_a_little():
    me = person(locality="Hyderabad", geo=HYDERABAD)

    assert direction_fit(me, person(locality="Secunderabad", geo=SECUNDERABAD)) > direction_fit(
        me, person(locality="Delhi", geo=DELHI)
    )


# --- Both directions, the 1–10 score and the word ----------------------------


def test_Given_a_one_way_fit_When_paired_Then_the_score_is_low_even_if_one_side_loves_it():
    wants_veg = person(lifestyle_diet="vegetarian", partner_brief=brief({"field": "diet", "values": ["vegetarian"], "importance": 9}))
    wants_nonveg = person(lifestyle_diet="vegetarian", partner_brief=brief({"field": "diet", "values": ["non_vegetarian"], "importance": 9}))
    other = person(lifestyle_diet="vegetarian", partner_brief=brief({"field": "diet", "values": ["vegetarian"], "importance": 9}))

    assert pair_score(wants_veg, other) > pair_score(wants_nonveg, other)
    assert 1.0 <= pair_score(wants_nonveg, other) <= 10.0


def test_Given_scores_When_labelled_Then_only_strong_or_good_words_never_weak():
    assert label_for(8.2) == "strong"
    assert label_for(7.7) == "good"
    assert label_for(6.5) is None
    assert label_for(3.0) is None


def test_Given_no_matchmaker_brief_When_older_preferences_exist_Then_they_still_count():
    legacy = person(partner_age_range={"min": 26, "max": 30}, partner_diet=["vegetarian"])

    assert [w.field for w in wishes(legacy)] == ["age", "diet"]


# --- Validation of what the AI (or anyone) sends ----------------------------


def test_Given_invented_fields_or_values_When_cleaned_Then_they_are_dropped():
    items = clean_items(
        [
            {"field": "caste_rank", "values": ["high"], "importance": 10},
            {"field": "diet", "values": ["vegetarian", "keto"], "importance": 42},
            {"field": "age", "min": 35, "max": 27, "importance": 7},
        ]
    )

    assert items == [
        {"field": "diet", "importance": 10, "values": ["vegetarian"]},
        {"field": "age", "importance": 7, "min": 27, "max": 35},
    ]
    assert clean_scales({"faith": {"want": 14, "importance": 0}, "looks": {"want": 9}}) == {
        "faith": {"want": 10, "importance": 1}
    }


# --- The keyword reader (no API key) ----------------------------------------


def understood(words: str) -> dict[str, dict]:
    result = asyncio.run(understand(words))
    assert result.source == "basic"
    return {i["field"]: i for i in result.items}


def test_Given_firm_and_loose_words_When_read_Then_importance_follows_how_firmly_it_was_said():
    items = understood("Must be strictly vegetarian. Age 26 to 30. Height doesn't matter much. Prefer a masters degree.")

    assert items["diet"]["values"] == ["vegetarian"] and items["diet"]["importance"] == 10
    assert (items["age"]["min"], items["age"]["max"]) == (26, 30)
    assert items["education"]["importance"] == 5
    assert "height_cm" not in items


def test_Given_Hindi_and_Telugu_words_When_read_Then_diet_and_language_are_understood():
    assert understood("शाकाहारी ज़रूर")["diet"]["values"] == ["vegetarian"]
    assert understood("తెలుగు అమ్మాయి, శాకాహారం")["mother_tongue"]["values"] == ["telugu"]


def test_Given_a_city_When_read_Then_it_gets_coordinates_from_the_server_list():
    items = understood("Should live in Hyderabad or Bengaluru, doesn't drink")

    assert set(items["locality"]["values"]) == {"Hyderabad", "Bengaluru"}
    assert len(items["locality"]["geo"]) == 2
    assert items["drinking"]["values"] == ["never"]


# --- "How you fit each other" -----------------------------------------------


def test_Given_two_people_When_broken_down_Then_my_list_is_full_and_theirs_is_topics_I_meet_only():
    from app.components.compatibility.engine import breakdown

    me = person(
        lifestyle_diet="vegetarian",
        education_level="masters",
        partner_brief=brief(
            {"field": "diet", "values": ["vegetarian"], "importance": 10},
            {"field": "drinking", "values": ["never"], "importance": 7},
        ),
    )
    them = person(
        lifestyle_diet="eggetarian",
        partner_brief=brief(
            {"field": "diet", "values": ["vegetarian"], "importance": 9},
            {"field": "education", "values": ["doctorate"], "importance": 8},
        ),
    )

    fit = breakdown(me, them)

    assert [(y["field"], y["status"], y["must"]) for y in fit["yours"]] == [
        ("diet", "close", True),
        ("drinking", "unknown", False),
    ]
    # I meet their diet wish; I miss their education wish — which must not
    # be revealed, and neither may its value or how many wishes they have.
    assert fit["theirs_met"] == ["diet"]
    assert "doctorate" not in str(fit)
