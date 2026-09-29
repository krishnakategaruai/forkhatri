"""[TR17, B12] Circle-formation grouping: only people who have ALL met each other become a group."""

from uuid import UUID

from app.components.circle.interface import suggestion_groups


def _ids(n: int) -> list[UUID]:
    return [UUID(int=i + 1) for i in range(n)]


def test_busy_person_does_not_chain_two_unrelated_groups() -> None:
    # A meets B and C (yoga) and D and E (chess); the two sets never met each other.
    a, b, c, d, e = _ids(5)
    pairs = [(a, b, 3), (a, c, 3), (b, c, 3), (a, d, 2), (a, e, 2), (d, e, 2)]
    groups = [set(g) for g in suggestion_groups(pairs, set())]
    assert {a, b, c} in groups
    assert {a, d, e} in groups
    assert all(len(g) == 3 for g in groups)  # never one five-person "group" of strangers


def test_pairs_alone_never_make_a_group() -> None:
    a, b, c = _ids(3)
    assert suggestion_groups([(a, b, 5), (b, c, 5)], set()) == []  # a chain, not a clique


def test_already_suggested_pairs_are_not_proposed_again() -> None:
    a, b, c = _ids(3)
    pairs = [(a, b, 2), (a, c, 2), (b, c, 2)]
    assert len(suggestion_groups(pairs, set())) == 1
    assert suggestion_groups(pairs, {frozenset((a, b))}) == []


def test_clique_grows_while_everyone_has_met() -> None:
    a, b, c, d = _ids(4)
    pairs = [(x, y, 2) for i, x in enumerate((a, b, c, d)) for y in (a, b, c, d)[i + 1 :]]
    assert [set(g) for g in suggestion_groups(pairs, set())] == [{a, b, c, d}]
