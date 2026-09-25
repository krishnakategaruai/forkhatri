# [TR045] POST /v1/events — HTTP front door only; batching and per-event
# consent checks live in app/services/events.py.
# Traces to: FR45, TR045
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import events as svc
from app.services.events import EventBatchIn, EventsAcceptedOut  # noqa: F401

router = APIRouter(prefix="/v1/events", tags=["events"], responses=ERROR_RESPONSES)


@router.post("", response_model=EventsAcceptedOut, operation_id="submitEvents", summary="Submit client interaction events")
async def submit_events(
    body: EventBatchIn,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> EventsAcceptedOut:
    return await svc.submit_events(conn, ctx, body)
