# [TR045] POST /v1/events — the batched, client-observable half of FR45's
# event list (impression, detail-view scroll, search executed with
# zero-result flag, share, notification opened/muted, setup step abandoned).
# Approach: one endpoint, a bounded batch (defends against a single request
# growing unbounded), each event validated against the same `Level` enum the
# server-side `emit_event()` uses, and the same consent check applied per
# event (never a per-batch shortcut that could smuggle a behavioral event
# past a withdrawn consent). `member_id` never leaves this process — the
# response never echoes it back, and the stored row only ever has the
# pseudonym.
# Traces to: FR45, TR045
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db import get_conn
from app.events import Level, emit_event
from app.identity import AuthzContext, resolve_authz_context
import asyncpg

router = APIRouter(prefix="/v1/events", tags=["events"])

MAX_BATCH = 50


class ClientEvent(BaseModel):
    event: str = Field(min_length=1, max_length=80)
    level: Level
    object_id: str | None = None
    surface: str | None = None
    props: dict = Field(default_factory=dict)


class EventBatchIn(BaseModel):
    events: list[ClientEvent] = Field(min_length=1, max_length=MAX_BATCH)


@router.post("")
async def submit_events(
    body: EventBatchIn,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    accepted = 0
    for e in body.events:
        await emit_event(conn, member_id=ctx.member_id, event=e.event, level=e.level, object_id=e.object_id, surface=e.surface, props=e.props)
        accepted += 1
    return {"accepted": accepted}
