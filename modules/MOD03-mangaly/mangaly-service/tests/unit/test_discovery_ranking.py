"""Unit tests for Discovery ranking: the two-way partner-preference term and the
diversity re-rank (DEC-V1-002, TR026, SP026's contract test on representative
result sets). Pure functions only; nothing here touches the database.

Traces to: AgentOutputs/07-tech-reqs.md TR026, AgentOutputs/08-security-performance.md SP026.
"""

from __future__ import annotations

import random
from datetime import date

import pytest

from app.components.discovery.interface import (
    _diversify,
    _preference_checks,
    _score,
    _score_bracket,
    reciprocal_reasons,
    reciprocity,
)
from app.components.discovery.stable_matching import compute_daily_picks, proposer_side
from app.config.matching_engine import PAIR_WEIGHT
from app.config.ranking_weights import MAX_SAME_BRACKET_RUN


def born_years_ago(age: int) -> str:
    return date(date.today().year - age, 1, 1).isoformat()


def person(age: int, locality: str, *, wants_age: tuple[int, int] | None = None) -> dict:
    return {
        "locality": locality,
        "date_of_birth": born_years_ago(age),
        "partner_age_range": {"min": wants_age[0], "max": wants_age[1]} if wants_age else None,
        "evidence_completeness": 0.0,
    }


def rerank(scores: list[float]) -> list[float]:
    return _diversify(sorted(scores, reverse=True), score_of=lambda s: s)


def assert_run_rule_holds(ordered: list[float]) -> None:
    """Every run longer than the limit must be one the re-rank could not break:
    from the first extra item on, nothing from any other bracket was left."""
    brackets = [_score_bracket(s) for s in ordered]
    run = 1
    for i in range(1, len(brackets)):
        run = run + 1 if brackets[i] == brackets[i - 1] else 1
        if run > MAX_SAME_BRACKET_RUN:
            assert all(b == brackets[i] for b in brackets[i:]), (
                f"run of {run} in bracket {brackets[i]} at position {i} "
                "while other brackets remained"
            )


def test_Given_a_long_top_band_When_reranked_Then_no_more_than_three_in_a_row_share_a_bracket():
    ordered = rerank([0.95, 0.94, 0.93, 0.92, 0.91, 0.85, 0.84])

    assert ordered == [0.95, 0.94, 0.93, 0.85, 0.92, 0.91, 0.84]
    assert_run_rule_holds(ordered)


def test_Given_one_bracket_only_When_reranked_Then_order_is_unchanged():
    scores = [0.99, 0.97, 0.95, 0.93, 0.91]

    assert rerank(scores) == scores


def test_Given_a_representative_set_When_reranked_Then_contract_holds_and_nothing_is_lost():
    rng = random.Random(20260915)
    scores = [round(rng.choice([0.92, 0.55, 0.21]) + rng.random() * 0.07, 4) for _ in range(60)]

    ordered = rerank(scores)

    assert sorted(ordered) == sorted(scores)
    assert_run_rule_holds(ordered)
    for bracket in {_score_bracket(s) for s in scores}:
        within = [s for s in ordered if _score_bracket(s) == bracket]
        assert within == sorted(within, reverse=True), "order inside a bracket must not change"


def test_Given_no_stated_preferences_When_checked_Then_nothing_counts_for_or_against():
    assert _preference_checks(person(30, "Hyderabad"), person(31, "Chennai")) == []


def test_Given_a_one_way_fit_When_scored_Then_it_ranks_below_a_two_way_fit():
    viewer = person(35, "Hyderabad", wants_age=(28, 34))
    one_way = person(30, "Pune", wants_age=(25, 29))  # viewer (35) is outside what they want
    two_way = person(30, "Pune", wants_age=(30, 38))  # viewer (35) is what they want

    assert _preference_checks(viewer, one_way) == [1.0]
    assert _preference_checks(one_way, viewer) == [0.0]
    # [DEC-V1-030/031] The engine combines both directions by harmonic mean,
    # each shrunk toward neutral by the prior: one met wish each way is
    # (6 + 3) / 12 = 0.75; a direction that misses (six years outside their
    # range) is 3 / 12 = 0.25, and the harmonic mean pulls the pair down.
    assert _score(viewer, two_way) == pytest.approx(PAIR_WEIGHT * 0.75, abs=0.002)
    assert _score(viewer, one_way) == pytest.approx(PAIR_WEIGHT * 0.375, abs=0.002)
    assert _score(viewer, two_way) > _score(viewer, one_way)


# ---------------------------------------------------------------------------
# [DEC-V1-030] Reciprocity and the daily stable-matching pass
# ---------------------------------------------------------------------------


def test_Given_no_preferences_on_one_side_When_reciprocity_Then_that_side_is_neutral_not_zero():
    # Someone with strict preferences must still see people who said nothing.
    assert reciprocity([1.0, 1.0], []) == pytest.approx(2 * 1.0 * 0.5 / 1.5)
    assert reciprocity([], []) == pytest.approx(0.5)
    assert reciprocity([1.0], [0.0]) == 0.0
    assert reciprocity([1.0], [1.0]) == 1.0


def test_Given_partner_preferences_When_the_other_has_the_facts_Then_height_education_and_diet_are_checked():
    seeker = {
        "partner_height_range": {"min": 165, "max": 180},
        "partner_education": ["masters", "doctorate"],
        "partner_diet": "vegetarian",
    }
    other = {"height_cm": 170, "education_level": "masters", "lifestyle_diet": "non_vegetarian"}

    assert _preference_checks(seeker, other) == [1.0, 1.0, 0.0]
    # A fact the other person never gave counts neither way.
    assert _preference_checks(seeker, {"height_cm": 190}) == [0.0]


def test_Given_a_mutual_fit_When_reasons_are_made_Then_they_are_honest_and_language_neutral():
    me = {**person(30, "Hyderabad, Telangana", wants_age=(28, 34)), "partner_locality": "Hyderabad"}
    them = {**person(32, "Hyderabad, Telangana", wants_age=(26, 31)), "partner_locality": "Bengaluru or Hyderabad"}

    reasons = reciprocal_reasons(me, them)

    assert [r["key"] for r in reasons] == ["mutualFit", "wantsYourCity", "wantsYourAge"]
    assert reasons[1]["city"] == "Hyderabad"
    assert all("score" not in r for r in reasons)


def test_Given_mutual_and_one_way_pairs_When_stable_matched_Then_each_person_is_paired_with_someone_who_wants_them_back():
    def candidate(age: int, gender: str, wants: tuple[int, int]) -> dict:
        return {
            **person(age, "Hyderabad, Telangana", wants_age=wants),
            "gender": gender,
            "looking_for": "bride" if gender == "male" else "groom",
        }

    people = {
        "m1": candidate(30, "male", (25, 29)),  # wants younger — only f2 fits him
        "m2": candidate(34, "male", (28, 36)),
        "f1": candidate(33, "female", (30, 36)),  # m1 is too young for her; m2 fits
        "f2": candidate(27, "female", (28, 34)),  # both men fit her; only m1 wants her back fully
    }

    result = compute_daily_picks(people, day=date(2026, 9, 22), excluded_pairs=set(), rounds=1)

    first = {p.account_id: p.pick_account_id for p in result.picks if p.rank == 1}
    assert first["m1"] == "f2" and first["f2"] == "m1"
    assert first["m2"] == "f1" and first["f1"] == "m2"
    assert result.matched_pairs_by_round == [2]
    assert {result.proposers, result.receivers} == {2}


def test_Given_a_blocked_or_connected_pair_When_stable_matched_Then_they_are_never_paired():
    people = {
        "m1": {**person(30, "Hyderabad", wants_age=(25, 35)), "gender": "male", "looking_for": "bride"},
        "f1": {**person(30, "Hyderabad", wants_age=(25, 35)), "gender": "female", "looking_for": "groom"},
    }

    result = compute_daily_picks(
        people, day=date(2026, 9, 22), excluded_pairs={frozenset(("m1", "f1"))}, rounds=1
    )

    assert result.picks == []


def test_Given_the_looking_for_rule_When_stable_matched_Then_only_people_looking_for_each_other_pair():
    people = {
        "m1": {**person(30, "Hyderabad"), "gender": "male", "looking_for": "bride"},
        "f1": {**person(30, "Hyderabad"), "gender": "female", "looking_for": "bride"},  # not looking for a groom
    }

    assert compute_daily_picks(people, day=date(2026, 9, 22), excluded_pairs=set(), rounds=1).picks == []


def test_Given_two_rounds_When_stable_matched_Then_rank_two_is_a_different_person():
    def candidate(gender: str) -> dict:
        return {**person(30, "Hyderabad", wants_age=(25, 35)), "gender": gender, "looking_for": "bride" if gender == "male" else "groom"}

    people = {"m1": candidate("male"), "m2": candidate("male"), "f1": candidate("female"), "f2": candidate("female")}

    result = compute_daily_picks(people, day=date(2026, 9, 22), excluded_pairs=set(), rounds=2)

    by_rank = {(p.account_id, p.rank): p.pick_account_id for p in result.picks}
    for who in people:
        assert by_rank[(who, 1)] != by_rank[(who, 2)]
    assert result.matched_pairs_by_round == [2, 2]


def test_Given_two_dates_When_the_proposing_side_is_chosen_Then_it_alternates():
    assert proposer_side(date(2026, 9, 22)) != proposer_side(date(2026, 9, 23))
