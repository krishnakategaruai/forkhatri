"""FR110/FR111 — tags validate, returning hosts are an honest reason, new hosts get a labelled fair start, no host floods the top."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.components.activity.interface import Occurrence, invalid_tags
from app.components.discovery.interface import Card, RankingEngine, ViewerProfile, Weights, cap_per_host

NOW = datetime(2026, 9, 15, 6, 0, tzinfo=UTC)
VIEWER = ViewerProfile(uuid4(), "Hyderabad", None, "Madhapur", [], [])


def occ(**overrides: object) -> Occurrence:
    base: dict = {
        "id": uuid4(),
        "activity_id": None,
        "creator_member_id": uuid4(),
        "title": "Morning walk",
        "description": None,
        "intent_category": "explore",
        "time_start": NOW + timedelta(days=1),
        "time_end": None,
        "locality_city": "Hyderabad",
        "locality_zone": None,
        "locality_locality": "Madhapur",
        "capacity": None,
        "cover_image_ref": None,
        "high_risk": False,
        "visibility_scope": "public",
        "circle_id": None,
        "organization_scope_id": None,
        "canonical_url_slug": "occ-x",
        "status": "active",
        "cancelled_at": None,
        "created_at": NOW - timedelta(days=10),
        "recurrence_rule": None,
    }
    base.update(overrides)
    return Occurrence(**base)


def card(host: UUID) -> Card:
    return Card(
        id=uuid4(),
        slug="s",
        title="t",
        intent_category="meet",
        category_label="Meet",
        time_start=NOW,
        time_end=None,
        location_label="Madhapur",
        distance_label=None,
        host_member_id=host,
        host_name="H",
        host_avatar=None,
        going_count=0,
        interested_count=0,
        capacity=None,
        spots_left=None,
        trust_level="community_submitted",
        trust_label="",
        trust_positive=False,
        why_reason="",
        why_factor="",
        viewer_status=None,
        cover_image_url=None,
        visibility_scope="public",
        circle_id=None,
        high_risk=False,
        status="active",
        is_recurring=False,
        lat=None,
        lng=None,
    )


def test_tags_accept_known_values_only() -> None:
    assert invalid_tags(["family_friendly", "elder_friendly"], ["veg", "alcohol_free"]) == []
    assert invalid_tags(["everyone"], None) == ["audience_tags"]
    assert invalid_tags(None, ["veg", "non_veg"]) == ["food_tags"]
    assert invalid_tags(None, ["beer"]) == ["food_tags"]


def test_returning_to_a_host_is_the_honest_reason_and_raises_the_score() -> None:
    engine = RankingEngine(Weights())
    item = occ()
    plain = engine.score(item, VIEWER, trust_level="community_submitted", peers=0, now=NOW)
    back = engine.score(item, VIEWER, trust_level="community_submitted", peers=0, now=NOW, host_times=2, host_held=5, host_name="Priya")
    assert plain is not None and back is not None
    assert back[0] > plain[0]
    assert back[1] == ("reason.host_before", {"host": "Priya"}) and back[2] == "host"


def test_new_host_nearby_gets_a_small_labelled_fair_start_only_when_nearby() -> None:
    engine = RankingEngine(Weights())
    near = occ()
    known = engine.score(near, VIEWER, trust_level="community_submitted", peers=0, now=NOW, host_held=4)
    new = engine.score(near, VIEWER, trust_level="community_submitted", peers=0, now=NOW, host_held=0)
    unknown = engine.score(near, VIEWER, trust_level="community_submitted", peers=0, now=NOW, host_held=None)
    assert known and new and unknown
    assert round(new[0] - known[0], 3) == 0.08 and unknown[0] == known[0]
    far = occ(locality_locality="Secunderabad", locality_city="Pune")
    far_new = engine.score(far, VIEWER, trust_level="community_submitted", peers=0, now=NOW, host_held=0)
    far_known = engine.score(far, VIEWER, trust_level="community_submitted", peers=0, now=NOW, host_held=4)
    assert (far_new is None and far_known is None) or (far_new and far_known and far_new[0] == far_known[0])


def test_no_host_takes_more_than_two_of_the_top_results() -> None:
    a, b = uuid4(), uuid4()
    cards = [card(a), card(a), card(a), card(a), card(b), card(b)]
    ordered = cap_per_host(cards, max_per_host=2, window=10)
    assert [c.host_member_id for c in ordered] == [a, a, b, b, a, a]
    assert {c.id for c in ordered} == {c.id for c in cards}
