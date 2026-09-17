"""FR103/FR104 — what the reminders say. Kind, factual, never a penalty; the member's own plan is repeated back."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.components.notification.interface import reminder_copy

IST = timezone(timedelta(hours=5, minutes=30))
START = datetime(2026, 9, 20, 7, 0, tzinfo=IST)
BASE = {"title": "Sunday badminton", "time_start": START, "locality": "Jubilee Hills", "plan_travel": None, "plan_with": None, "waitlisted": 0, "paid": False}


def test_three_days_names_the_day_time_and_place() -> None:
    head, body = reminder_copy("three_days", **BASE)
    assert head == "In 3 days: Sunday badminton"
    assert "Sun 20 Sep" in body and "7:00 AM" in body and "Jubilee Hills" in body


def test_still_coming_frames_a_freed_spot_as_someone_else_joining() -> None:
    _, none_waiting = reminder_copy("still_coming", **BASE)
    _, one_waiting = reminder_copy("still_coming", **{**BASE, "waitlisted": 1})
    _, many_waiting = reminder_copy("still_coming", **{**BASE, "waitlisted": 3})
    assert "helps the host plan" in none_waiting
    assert "the person on the waitlist can join" in one_waiting
    assert "one of the 3 people waiting can join" in many_waiting
    for body in (none_waiting, one_waiting, many_waiting):
        assert "refund" not in body
        for word in ("penalty", "no-show", "reliab", "score"):
            assert word not in body.lower()


def test_still_coming_points_paid_spots_to_the_refund_rule() -> None:
    _, body = reminder_copy("still_coming", **{**BASE, "paid": True})
    assert body.endswith("Your refund rule is on the activity page.")


def test_two_hours_repeats_the_members_own_plan() -> None:
    head, body = reminder_copy("two_hours", **{**BASE, "plan_travel": "metro_bus", "plan_with": "alone"})
    assert head == "Starts at 7:00 AM: Sunday badminton"
    assert "You planned to come by metro or bus." in body
    assert "Say hello to the host" in body
    _, bare = reminder_copy("two_hours", **BASE)
    assert bare == "In Jubilee Hills."


def test_three_days_welcomes_someone_back_after_a_missed_date() -> None:
    _, back = reminder_copy("three_days", **{**BASE, "missed_last": True})
    _, usual = reminder_copy("three_days", **BASE)
    assert back.startswith("We missed you last time; glad you're coming.")
    assert not usual.startswith("We missed")
    assert "streak" not in back.lower()


def test_unknown_kind_is_refused() -> None:
    with pytest.raises(ValueError):
        reminder_copy("tomorrow", **BASE)
