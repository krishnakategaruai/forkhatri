# [Refactor A, 2026-09-21] Cursor pagination for list operations.
# Why: an agent or an external system walking a member's enquiries,
# opportunities or notifications needs a stable way to fetch the next page,
# and the plain list routes the web app uses today return one unpaged array.
# Pagination is added beside them, never instead of them: each paged list
# has its own `/page` route returning `{items, next_cursor}`, so the existing
# response shapes (and the web app) are untouched.
# The cursor is opaque to clients. Most lists page over the same ordered
# result the plain route returns (an offset cursor); the notification inbox,
# whose plain route stops at 50, pages with a keyset cursor on
# (created_at, id) so older notifications are reachable.
# Traces to: REFACTOR-PLAN.md §A (cursor pagination)
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel, Field

from app.errors import ApiError

T = TypeVar("T")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = Field(default=None, description="Pass back as `cursor` to fetch the next page; null on the last page")


def encode_cursor(data: dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":"), default=str).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str | None, lang: str) -> dict[str, Any] | None:
    if not cursor:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if not isinstance(data, dict):
            raise ValueError
        return data
    except (ValueError, TypeError, UnicodeDecodeError):
        raise ApiError(422, "common.error.invalidCursor", lang)


def paginate(items: Sequence[T], limit: int, cursor: str | None, lang: str) -> Page[T]:
    """Offset cursor over an already-ordered result."""
    data = decode_cursor(cursor, lang) or {}
    offset = data.get("o", 0)
    if not isinstance(offset, int) or offset < 0:
        raise ApiError(422, "common.error.invalidCursor", lang)
    window = list(items[offset:offset + limit])
    more = offset + limit < len(items)
    return Page[Any](items=window, next_cursor=encode_cursor({"o": offset + limit}) if more else None)


def keyset_after(cursor: str | None, lang: str) -> tuple[datetime | None, str | None]:
    """Decodes a (created_at, id) keyset cursor."""
    data = decode_cursor(cursor, lang)
    if data is None:
        return None, None
    try:
        return datetime.fromisoformat(data["t"]), str(data["i"])
    except (KeyError, ValueError, TypeError):
        raise ApiError(422, "common.error.invalidCursor", lang)


def keyset_cursor(created_at: datetime, row_id: Any) -> str:
    return encode_cursor({"t": created_at.isoformat(), "i": str(row_id)})
