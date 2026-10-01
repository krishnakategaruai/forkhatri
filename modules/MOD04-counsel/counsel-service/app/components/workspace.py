"""Consultation workspace realtime hub.

One WebSocket per participant per booking. The hub relays:
  * WebRTC signalling (offer/answer/ice) between the two parties — media is
    peer-to-peer in the browser (open-source WebRTC, no vendor);
  * chat messages (persisted), shared-note edits (persisted, last-writer wins
    with a version), action items, file notices, presence, recording consent
    and recording state, screen-share state.
The hub owns no media and stores no media."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class Room:
    def __init__(self) -> None:
        self.sockets: dict[str, set[WebSocket]] = defaultdict(set)   # member_id -> sockets
        self.recording = False
        self.sharing: str | None = None                              # member_id sharing screen

    def members(self) -> list[str]:
        return [m for m, s in self.sockets.items() if s]


_rooms: dict[str, Room] = {}
_lock = asyncio.Lock()


def room(booking_id: UUID | str) -> Room:
    key = str(booking_id)
    if key not in _rooms:
        _rooms[key] = Room()
    return _rooms[key]


async def join(booking_id, member_id: str, ws: WebSocket) -> Room:
    r = room(booking_id)
    r.sockets[member_id].add(ws)
    return r


async def leave(booking_id, member_id: str, ws: WebSocket) -> None:
    r = room(booking_id)
    r.sockets[member_id].discard(ws)
    if r.sharing == member_id and not r.sockets[member_id]:
        r.sharing = None
    if not any(r.sockets.values()):
        _rooms.pop(str(booking_id), None)


async def broadcast(booking_id, payload: dict, exclude: WebSocket | None = None) -> None:
    r = _rooms.get(str(booking_id))
    if not r:
        return
    data = json.dumps(payload, default=str)
    dead = []
    for member, sockets in r.sockets.items():
        for s in list(sockets):
            if s is exclude:
                continue
            try:
                await s.send_text(data)
            except Exception:
                dead.append((member, s))
    for member, s in dead:
        r.sockets[member].discard(s)


async def send_to(booking_id, member_id: str, payload: dict) -> None:
    r = _rooms.get(str(booking_id))
    if not r:
        return
    data = json.dumps(payload, default=str)
    for s in list(r.sockets.get(member_id, ())):
        try:
            await s.send_text(data)
        except Exception:
            r.sockets[member_id].discard(s)
