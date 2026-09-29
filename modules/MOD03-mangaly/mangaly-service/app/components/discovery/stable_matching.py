"""[DEC-V1-030] The daily "Most compatible today" pass: deferred acceptance
(Gale–Shapley) over everyone searchable, two sides defined by the "Looking
for" rule, preference lists ordered by reciprocity.

Pure functions only — `scripts/compute_daily_picks.py` does the reading and
writing. Nothing here reads, or could read, an engagement signal: the only
input per person is their `ranking_input_snapshot`, and the only per-pair
input is `_score()`'s own reciprocal terms.

Why stable matching, and not "everyone's top-1": with a plain top-1 the
same few people are everyone's first choice and most people's pick is
someone who would never pick them back — the popularity concentration
DEC-V1-002 was written against. Deferred acceptance produces a matching in
which no two people would both rather have each other than the partners they
were given, so each pick is a person for whom YOU are also a good answer.

Fairness of the proposing side: the proposing side gets its best stable
partners, the other side its worst. Rather than favour one gender every day,
the proposing side alternates with the date (see `proposer_side`).
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import TypeVar

from app.components.compatibility import interface as compatibility
from app.config.ranking_weights import DAILY_PICK_LIST_CAP, DAILY_PICK_ROUNDS

K = TypeVar("K", bound=Hashable)

_GENDER_LOOKED_FOR = {"bride": "female", "groom": "male"}


def pair_score(a: dict, b: dict) -> tuple[float, float]:
    """How much `a` should want `b`, from the same AI engine that orders
    Discover (DEC-V1-031), so today's pick and "Picked for you" agree: the
    mutual 1–10 pair score first, then how well `b` fits what `a` asked for
    as the tie-break. [2026-09-28] It used to read the older yes/no checks
    on age, city, height, education and diet only."""
    return compatibility.pair_score(a, b), compatibility.direction_fit(a, b)


def looks_for_each_other(a: dict, b: dict) -> bool:
    """The permanent rule: each side's "Looking for" must name the other's
    gender. Unknown on either side means no."""
    return (
        _GENDER_LOOKED_FOR.get(str(a.get("looking_for") or "")) == b.get("gender")
        and _GENDER_LOOKED_FOR.get(str(b.get("looking_for") or "")) == a.get("gender")
    )


def proposer_side(day: date) -> str:
    """Which gender proposes today. Alternates by day so neither side is
    always the one that gets its best stable partner."""
    return "female" if day.toordinal() % 2 == 0 else "male"


@dataclass
class MatchingRound:
    matched: dict[K, K] = field(default_factory=dict)  # both directions
    proposals_made: int = 0


def deferred_acceptance(
    proposers: Iterable[K],
    preference_of: Callable[[K], list[K]],
    receiver_rank: Callable[[K, K], tuple[float, float]],
) -> MatchingRound:
    """Textbook Gale–Shapley. `preference_of(p)` is p's ordered list (already
    capped); `receiver_rank(r, p)` is how much receiver r wants proposer p —
    higher is better — so a receiver holding `held` swaps to a new proposer
    only when `receiver_rank(r, new) > receiver_rank(r, held)`."""
    lists = {p: list(preference_of(p)) for p in proposers}
    next_index = dict.fromkeys(lists, 0)
    held: dict[K, K] = {}  # receiver -> proposer
    free = [p for p in lists if lists[p]]
    out = MatchingRound()
    while free:
        p = free.pop()
        while next_index[p] < len(lists[p]):
            r = lists[p][next_index[p]]
            next_index[p] += 1
            out.proposals_made += 1
            current = held.get(r)
            if current is None:
                held[r] = p
                break
            if receiver_rank(r, p) > receiver_rank(r, current):
                held[r] = p
                if next_index[current] < len(lists[current]):
                    free.append(current)
                break
        # else: p exhausted their list and stays unmatched this round
    for r, p in held.items():
        out.matched[p] = r
        out.matched[r] = p
    return out


@dataclass(frozen=True)
class Pick:
    account_id: K
    pick_account_id: K
    rank: int


@dataclass
class DailyPicks:
    picks: list[Pick]
    proposer_gender: str
    proposers: int
    receivers: int
    matched_pairs_by_round: list[int]
    proposals_by_round: list[int]


def compute_daily_picks(
    people: dict[K, dict],
    *,
    day: date,
    excluded_pairs: set[frozenset],
    list_cap: int = DAILY_PICK_LIST_CAP,
    rounds: int = DAILY_PICK_ROUNDS,
) -> DailyPicks:
    """`people` maps account id -> `ranking_input_snapshot` for every
    searchable candidate. `excluded_pairs` are pairs that must never be
    matched (blocked either way, or already requested/connected). Returns
    `rounds` ranks of picks: rank 1 is the stable matching, rank n+1 is the
    stable matching once every pair already used in ranks 1..n is excluded —
    the fallbacks Discover walks through when the first is unavailable."""
    gender = proposer_side(day)
    proposers = [k for k, s in people.items() if s.get("gender") == gender]
    receivers = [k for k, s in people.items() if s.get("gender") != gender]

    score_cache: dict[tuple[K, K], tuple[float, float]] = {}

    def score(a: K, b: K) -> tuple[float, float]:
        key = (a, b)
        if key not in score_cache:
            score_cache[key] = pair_score(people[a], people[b])
        return score_cache[key]

    def eligible(a: K, b: K) -> bool:
        return frozenset((a, b)) not in excluded_pairs and looks_for_each_other(people[a], people[b])

    used: set[frozenset] = set()
    picks: list[Pick] = []
    matched_by_round: list[int] = []
    proposals_by_round: list[int] = []

    for rank in range(1, rounds + 1):

        def preference_of(p: K) -> list[K]:
            options = [r for r in receivers if eligible(p, r) and frozenset((p, r)) not in used]
            options.sort(key=lambda r: score(p, r), reverse=True)
            return options[:list_cap]

        result = deferred_acceptance(proposers, preference_of, lambda r, p: score(r, p))
        pairs = {frozenset((p, r)) for p, r in result.matched.items()}
        matched_by_round.append(len(pairs))
        proposals_by_round.append(result.proposals_made)
        if not pairs:
            break
        for a, b in result.matched.items():
            picks.append(Pick(account_id=a, pick_account_id=b, rank=rank))
        used |= pairs

    return DailyPicks(
        picks=picks,
        proposer_gender=gender,
        proposers=len(proposers),
        receivers=len(receivers),
        matched_pairs_by_round=matched_by_round,
        proposals_by_round=proposals_by_round,
    )
