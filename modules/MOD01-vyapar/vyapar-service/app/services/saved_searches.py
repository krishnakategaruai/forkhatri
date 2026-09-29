# [IMP-B, 2026-09-28] Saved opportunity searches with optional alerts (FR18/FR21).
#
# A saved search is the feed's own filter set (the same FeedFilters the feed
# endpoints accept) plus a free-text query, kept per member. `alert=true`
# asks the existing strong-match pass (services/notifications.py) to also
# notify when NEW opportunities match this search — under the same 3/day
# cap and mute rules as every other proactive notification, never a second
# budget. The match itself is computed by app/services/feed.py's query
# builder, so "matches my saved search" means exactly what the feed shows.
# Traces to: FR18, FR21, TR018, TR021, SP021
from __future__ import annotations

import json

import asyncpg
from pydantic import BaseModel, Field

from app.errors import ApiError
from app.identity import AuthzContext
from app.services.feed import FeedFilters

MAX_SAVED_SEARCHES = 20


class SavedSearchIn(BaseModel):
    query: str = Field(default="", max_length=200)
    filters: FeedFilters = Field(default_factory=FeedFilters)
    alert: bool = False
    name: str | None = Field(default=None, max_length=80)


class SavedSearchOut(BaseModel):
    id: str
    name: str | None
    query: str
    filters: FeedFilters
    alert: bool
    last_alerted_at: str | None
    created_at: str


def _row_to_out(row: asyncpg.Record) -> SavedSearchOut:
    raw = row["filters"]
    data = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
    name = data.pop("_name", None)
    return SavedSearchOut(
        id=str(row["id"]), name=name, query=row["query"], filters=FeedFilters(**{k: v for k, v in data.items() if k in FeedFilters.model_fields}),
        alert=row["alert"], last_alerted_at=row["last_alerted_at"].isoformat() if row["last_alerted_at"] else None,
        created_at=row["created_at"].isoformat(),
    )


async def save_search(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: SavedSearchIn) -> SavedSearchOut:
    count = await conn.fetchval("SELECT count(*) FROM vyapar_opportunities.saved_searches WHERE member_id = $1", ctx.member_id)
    if count >= MAX_SAVED_SEARCHES:
        raise ApiError(429, "discover.error.tooManySavedSearches", lang, max=MAX_SAVED_SEARCHES)
    filters = body.filters.model_dump(exclude_none=True, exclude_defaults=True)
    if body.name:
        filters["_name"] = body.name
    row = await conn.fetchrow(
        """INSERT INTO vyapar_opportunities.saved_searches (member_id, query, filters, alert)
           VALUES ($1, $2, $3::jsonb, $4) RETURNING *""",
        ctx.member_id, body.query.strip(), json.dumps(filters), body.alert,
    )
    return _row_to_out(row)


async def list_saved_searches(conn: asyncpg.Connection, ctx: AuthzContext) -> list[SavedSearchOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_opportunities.saved_searches WHERE member_id = $1 ORDER BY created_at DESC", ctx.member_id
    )
    return [_row_to_out(r) for r in rows]


async def delete_saved_search(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, search_id: str) -> dict:
    try:
        status = await conn.execute(
            "DELETE FROM vyapar_opportunities.saved_searches WHERE id = $1 AND member_id = $2", search_id, ctx.member_id
        )
    except asyncpg.DataError:
        raise ApiError(404, "discover.error.savedSearchNotFound", lang)
    if status.split()[-1] == "0":
        raise ApiError(404, "discover.error.savedSearchNotFound", lang)
    return {"deleted": True}


def filters_of(row: asyncpg.Record) -> FeedFilters:
    """For the notification pass: the FeedFilters a saved-search row encodes."""
    return _row_to_out(row).filters
