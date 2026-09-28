"""Horoscope profile fields: validation on save and the place-of-birth list."""

from __future__ import annotations

import pytest

from app.components.places import interface as places
from app.components.profile.horoscope_fields import InvalidAttributeValue, normalize

V, D = "value", "declined"


def run(attrs: dict) -> dict:
    return normalize(attrs, V, D)


def test_time_must_be_24_hour_hh_mm() -> None:
    assert run({"birth_time": (V, " 07:05 ")})["birth_time"] == (V, "07:05")
    for bad in ("7 pm", "7:05", "24:00", "07:60", "0705", 705):
        with pytest.raises(InvalidAttributeValue) as e:
            run({"birth_time": (V, bad)})
        assert e.value.key == "birth_time"
        assert str(bad) not in str(e.value)


def test_unknown_accuracy_withdraws_the_time() -> None:
    out = run({"birth_time": (V, "07:05"), "birth_time_accuracy": (V, "unknown")})
    assert out["birth_time"] == (D, None)


def test_accuracy_needs_a_time_unless_unknown() -> None:
    with pytest.raises(InvalidAttributeValue):
        run({"birth_time": (D, None), "birth_time_accuracy": (V, "about_30")})
    with pytest.raises(InvalidAttributeValue):
        run({"birth_time_accuracy": (V, "roughly")})


def test_place_is_resolved_on_the_server() -> None:
    vizag = places.search("vizag")[0]
    out = run({"birth_place_geo": (V, {"place_id": vizag.id, "latitude": 0, "timezone": "UTC"})})
    geo = out["birth_place_geo"][1]
    assert geo["timezone"] == "Asia/Kolkata"
    assert abs(geo["latitude"] - 17.7) < 0.2
    assert out["birth_place"] == (V, "Visakhapatnam, Andhra Pradesh, India")


def test_typed_place_without_a_choice_is_refused() -> None:
    with pytest.raises(InvalidAttributeValue):
        run({"birth_place": (V, "somewhere near guntur")})
    with pytest.raises(InvalidAttributeValue):
        run({"birth_place_geo": (V, {"place_id": "no-such-place"})})


def test_declining_the_place_declines_both() -> None:
    out = run({"birth_place": (D, None)})
    assert out["birth_place_geo"] == (D, None)


def test_nakshatra_and_rashi_are_keys() -> None:
    assert run({"nakshatra": (V, "purva_phalguni"), "rashi": (V, "kark")})["nakshatra"] == (V, "purva_phalguni")
    with pytest.raises(InvalidAttributeValue):
        run({"nakshatra": (V, "Magha star")})


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("vizag", "Visakhapatnam, Andhra Pradesh, India"),
        ("madras", "Chennai, Tamil Nadu, India"),
        ("bombay", "Mumbai, Maharashtra, India"),
        ("hyd", "Hyderabad, Telangana, India"),
        ("hyderabad, sindh", "Hyderabad, Sindh, Pakistan"),
        ("london", "London, England, United Kingdom"),
    ],
)
def test_search_finds_what_families_type(query: str, expected: str) -> None:
    assert places.search(query)[0].label == expected


def test_search_carries_time_zones_abroad() -> None:
    assert places.search("new york")[0].timezone == "America/New_York"
    assert places.search("dubai")[0].timezone == "Asia/Dubai"


# --- birth details sent to the horoscope service ---------------------------

from app.components.horoscope.interface import _birth_details  # noqa: E402
from app.components.profile.models import FieldState  # noqa: E402


def _attrs(**values: object) -> dict:
    return {k: (FieldState.VALUE, v) for k, v in values.items()}


def test_birth_details_follow_how_sure_the_time_is() -> None:
    geo = places.search("vizag")[0].to_geo()
    exact = _birth_details("1996-04-12", _attrs(birth_time="06:42", birth_time_accuracy="exact", birth_place_geo=geo))
    assert exact is not None
    assert exact["birthTimePrecision"] == "EXACT"
    assert exact["timezone"] == "Asia/Kolkata"
    approx = _birth_details("1996-04-12", _attrs(birth_time="06:42", birth_time_accuracy="about_30", birth_place_geo=geo))
    assert approx is not None
    assert (approx["birthTimePrecision"], approx["birthTimeUncertaintyMinutes"]) == ("APPROXIMATE", 30)
    unknown = _birth_details("1996-04-12", _attrs(birth_time_accuracy="unknown", birth_place_geo=geo))
    assert unknown is not None
    assert (unknown["birthTime"], unknown["birthTimePrecision"]) == (None, "UNKNOWN")


def test_no_chosen_place_means_no_chart_never_a_guessed_zone() -> None:
    assert _birth_details("1996-04-12", _attrs(birth_time="06:42", birth_place="Vizag")) is None
