"""[049] Pure rules behind circle-post pins and the activity chat's closing time."""

from datetime import datetime, timedelta, timezone

from app.components.connect.chat import is_closed_at
from app.components.conversation.interface import MAX_PINS, POST_REACTIONS, board_order_key, pins_to_release

T0 = datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)


def test_pinned_posts_come_first_then_newest():
    rows = [
        ("old-pinned", T0 - timedelta(days=5), T0 - timedelta(days=9)),
        ("new", None, T0),
        ("older", None, T0 - timedelta(hours=1)),
        ("recent-pin", T0 - timedelta(days=1), T0 - timedelta(days=20)),
    ]
    ordered = [r[0] for r in sorted(rows, key=lambda r: board_order_key(r[1], r[2]))]
    assert ordered == ["recent-pin", "old-pinned", "new", "older"]


def test_announcement_releases_oldest_pins_to_stay_within_three():
    assert MAX_PINS == 3
    assert pins_to_release(0, []) == []
    assert pins_to_release(2, ["a", "b"]) == []
    assert pins_to_release(3, ["a", "b", "c"]) == ["a"]
    assert pins_to_release(4, ["a", "b", "c", "d"]) == ["a", "b"]


def test_reaction_set_is_small_and_fixed():
    assert len(POST_REACTIONS) == 5 and len(set(POST_REACTIONS)) == 5


def test_activity_chat_closes_after_its_closing_time():
    closes = T0 + timedelta(hours=24)
    assert is_closed_at(None) is False
    assert is_closed_at(closes, now=T0) is False
    assert is_closed_at(closes, now=closes) is True
    assert is_closed_at(closes, now=closes + timedelta(minutes=1)) is True
