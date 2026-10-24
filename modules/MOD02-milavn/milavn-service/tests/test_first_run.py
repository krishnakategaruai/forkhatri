"""First-run redesign (ONBOARDING-REDESIGN-2026-10.md §9, 2026-10-06): a place is the only first-run answer,
interests are optional and editable (add and remove, own words allowed), the Spiritual & temple group exists,
a new profile starts at Zone precision without touching existing members, a quiet Home widens to nearby cities
and online events, and smart fill reads day names in Hindi and Telugu."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.components.activity.interface import Occurrence
from app.components.discovery import nl
from app.components.discovery.interface import ViewerProfile, pick_wider
from app.components.profile import interface as profile
from app.config.interests import (
    INTEREST_GROUPS,
    TAG_LABELS,
    InvalidInterests,
    interest_label,
    normalise_interests,
    taxonomy_payload,
)

IST = ZoneInfo("Asia/Kolkata")

# Every tag members could pick before the redesign must still exist (saved interests stay meaningful).
OLD_TAGS = {
    "badminton", "cricket", "football", "running", "cycling", "yoga", "trekking", "swimming", "coffee-meetups", "board-games",
    "potluck", "street-food", "photography-walks", "music", "dance", "theatre", "festivals", "poetry", "coding",
    "language-exchange", "book-club", "workshops", "networking", "startups", "career", "kids-activities", "parenting",
    "volunteering", "cleanup-drives",
}


# --- FR001: place only -------------------------------------------------------------------------------------------


def test_place_alone_is_a_complete_first_run() -> None:
    city, tags = profile.validate_onboarding("Hyderabad", [])
    assert (city, tags) == ("Hyderabad", [])


def test_missing_place_is_named() -> None:
    with pytest.raises(profile.MissingRequiredFields) as exc:
        profile.validate_onboarding("  ", ["music"])
    assert exc.value.fields == ["locality_city"]


def test_older_clients_sending_interests_still_work() -> None:
    assert profile.validate_onboarding("Pune", [" Yoga", "trekking", "yoga"]) == ("Pune", ["trekking", "yoga"])


# --- Taxonomy: Spiritual & temple, nine groups, nothing lost -----------------------------------------------------


def test_spiritual_group_and_all_old_tags() -> None:
    spiritual = [t for t, _l, _c in INTEREST_GROUPS["spiritual"][1]]
    assert spiritual == ["satsang", "bhajan", "yatra", "temple-visit", "seva"]
    assert OLD_TAGS <= set(TAG_LABELS)
    assert len(INTEREST_GROUPS) == 9
    payload = taxonomy_payload()
    assert payload[0]["key"] == "spiritual" and payload[0]["group"] == "Spiritual & temple"
    assert all({"key", "group", "interests"} <= set(g) for g in payload)


# --- FR003: interests editable, own words allowed ----------------------------------------------------------------


def test_interests_normalise_keep_own_words() -> None:
    got = normalise_interests(["Satsang", "other:  Kolam   drawing ", "satsang", "OTHER:kolam drawing"])
    assert got == ["satsang", "other:Kolam drawing"]
    assert interest_label("other:Kolam drawing") == "Kolam drawing"
    assert interest_label("temple-visit") == "Temple visit"
    assert normalise_interests([]) == []


def test_interests_reject_unknown_and_too_many_own() -> None:
    with pytest.raises(InvalidInterests) as exc:
        normalise_interests(["music", "not-a-tag"])
    assert exc.value.bad == ["not-a-tag"]
    with pytest.raises(InvalidInterests):
        normalise_interests([f"other:thing {i}" for i in range(6)])
    with pytest.raises(InvalidInterests):
        normalise_interests(["other:" + "x" * 41])


# --- Q4: new profiles start at Zone; a place-only save never touches interests -----------------------------------


class _Result:
    def __init__(self, row: object = None) -> None:
        self._row = row
        self.rowcount = 1

    def first(self) -> object:
        return self._row

    def all(self) -> list:
        return []


class _Row:
    def __init__(self, member_id: object) -> None:
        self.member_id = member_id
        self.locality_city = "Hyderabad"
        self.locality_zone = None
        self.locality_locality = "Dilsukh Nagar"
        self.locality_state = "Telangana"
        self.locality_lat = 17.37
        self.locality_lng = 78.53
        self.language_preference = "te"
        self.bio = None
        self.storage_ref = None


class _FakeSession:
    def __init__(self, member_id: object) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.member_id = member_id

    async def execute(self, stmt: object, params: dict | None = None) -> _Result:
        sql = str(stmt)
        self.calls.append((sql, params or {}))
        if "FROM milavn_profile.member_profile p" in sql:
            return _Result(_Row(self.member_id))
        return _Result()


def test_new_profile_zone_default_and_no_interest_wipe() -> None:
    member = uuid4()
    session = _FakeSession(member)
    summary = asyncio.run(
        profile.save_onboarding(
            session,  # type: ignore[arg-type]
            member_id=member, locality_city="Hyderabad", locality_zone=None, locality_locality="Dilsukh Nagar",
            interests=[], language_preference="te", locality_state="Telangana", locality_lat=17.3688, locality_lng=78.5247,
        )
    )
    sqls = [s for s, _p in session.calls]
    assert not any("DELETE FROM milavn_profile.member_interest" in s for s in sqls)
    precision = [(s, p) for s, p in session.calls if "location_precision_setting" in s]
    assert len(precision) == 1
    sql, params = precision[0]
    assert "ON CONFLICT (member_id) DO NOTHING" in sql  # an existing member's own choice is never changed
    assert params["lvl"] == profile.NEW_PROFILE_PRECISION == "zone"
    lang = [p for s, p in session.calls if "INSERT INTO milavn_profile.member_profile" in s][0]["lang"]
    assert lang == "te"  # the member's ForKhatri language, never replaced by English
    assert summary.interests == []


# --- Q5: a quiet Home widens, labelled -----------------------------------------------------------------------------

NOW = datetime(2026, 10, 6, 6, 0, tzinfo=UTC)


def occ(city: str, lat: float | None, lng: float | None, mode: str = "in_person", days: int = 1) -> Occurrence:
    return Occurrence(
        id=uuid4(), activity_id=None, creator_member_id=uuid4(), title="Evening walk", description=None, intent_category="explore",
        time_start=NOW + timedelta(days=days), time_end=None, locality_city=city, locality_zone=None, locality_locality=None,
        capacity=None, cover_image_ref=None, high_risk=False, visibility_scope="public", circle_id=None, organization_scope_id=None,
        canonical_url_slug="s", status="active", cancelled_at=None, created_at=NOW, recurrence_rule=None,
        locality_lat=lat, locality_lng=lng, attendance_mode=mode,
    )


def test_pick_wider_nearby_and_online() -> None:
    viewer = ViewerProfile(uuid4(), "Hyderabad", None, "Dilsukh Nagar", [], [], 17.37, 78.53)
    own = occ("Hyderabad", 17.4, 78.4)
    near = occ("Sangareddy", 17.62, 78.08, days=3)  # ~55 km
    far = occ("Chennai", 13.08, 80.27)  # ~520 km
    online_far = occ("Chennai", 13.0, 80.25, mode="online", days=2)
    own_online = occ("Hyderabad", None, None, mode="online")  # already on Home in the member's own city
    no_coords = occ("Warangal", None, None)
    nearby, online = pick_wider([own, near, far, online_far, own_online, no_coords], viewer)
    assert [o.id for o, _km in nearby] == [near.id]
    assert 40 < nearby[0][1] < 70
    assert [o.id for o in online] == [online_far.id]
    nearby2, online2 = pick_wider([near, online_far], viewer, exclude_ids={near.id})
    assert nearby2 == [] and [o.id for o in online2] == [online_far.id]


# --- Smart fill reads Indian day names (Ravi's "रविवार" landed on tomorrow) ----------------------------------------


@pytest.mark.parametrize("text", ["रविवार शाम 6 बजे सत्संग", "ఆదివారం సాయంత్రం 6 గంటలకు భజన", "satsang sunday 6pm"])
def test_smart_fill_reads_sunday(text: str) -> None:
    wednesday_evening = datetime(2026, 10, 7, 20, 0, tzinfo=IST)  # a Wednesday, after 6 pm
    d = nl.smart_fill(text, now=wednesday_evening)
    assert d.time_start is not None
    start = datetime.fromisoformat(d.time_start)
    assert start.weekday() == 6 and start.date() == datetime(2026, 10, 11).date()
    assert len(d.matched) == len({m.lower() for m in d.matched})  # no duplicate chips


def test_interests_keep_a_tag_the_member_already_has() -> None:
    assert normalise_interests(["old-free-tag", "music"], already_saved=frozenset({"old-free-tag"})) == ["old-free-tag", "music"]
