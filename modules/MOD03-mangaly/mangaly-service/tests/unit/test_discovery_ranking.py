"""Unit tests for Discovery ranking: the two-way partner-preference term and the
diversity re-rank (DEC-V1-002, TR026, SP026's contract test on representative
result sets). Pure functions only; nothing here touches the database.

Traces to: AgentOutputs/07-tech-reqs.md TR026, AgentOutputs/08-security-performance.md SP026.
"""

from __future__ import annotations

import random
from datetime import date

from app.components.discovery.interface import (
    _diversify,
    _preference_checks,
    _score,
    _score_bracket,
)
from app.config.ranking_weights import MAX_SAME_BRACKET_RUN, PARTNER_PREFERENCE_WEIGHT


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
    assert _score(viewer, one_way) == 0.5 * PARTNER_PREFERENCE_WEIGHT
    assert _score(viewer, two_way) == PARTNER_PREFERENCE_WEIGHT
