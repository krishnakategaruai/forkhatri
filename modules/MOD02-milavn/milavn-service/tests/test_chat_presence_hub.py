"""FR096/FR097 — "here" in a chat room is the set of members with that conversation open.

Proves the in-process hub counts sockets per member, so a second tab (or a
development double-mount) closing does not mark a person as gone, and that
presence in one conversation never leaks into another. No database needed.
"""

from __future__ import annotations

from uuid import uuid4

from app.components.connect.chat import Hub


def test_member_is_here_while_any_socket_is_open() -> None:
    hub, conv, asha = Hub(), uuid4(), uuid4()
    first = hub.subscribe(conv, asha)
    second = hub.subscribe(conv, asha)
    assert hub.present_in(conv) == {asha}
    hub.unsubscribe(conv, asha, first)
    assert hub.present_in(conv) == {asha}
    hub.unsubscribe(conv, asha, second)
    assert hub.present_in(conv) == set()


def test_presence_is_per_conversation() -> None:
    hub, room, other_room, asha, priya = Hub(), uuid4(), uuid4(), uuid4(), uuid4()
    hub.subscribe(room, asha)
    hub.subscribe(other_room, priya)
    assert hub.present_in(room) == {asha}
    assert hub.present_in(other_room) == {priya}


def test_inbox_socket_is_not_presence_in_any_room() -> None:
    hub, room, asha = Hub(), uuid4(), uuid4()
    q = hub.subscribe(None, asha)
    assert hub.present_in(room) == set()
    hub.unsubscribe(None, asha, q)
    assert hub.present_in(room) == set()
