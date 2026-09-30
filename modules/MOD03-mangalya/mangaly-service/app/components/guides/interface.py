"""Guides — short articles (and later videos) on using Mangalya well
(migration 063). Read-only here; guides are added in the database.

Each guide holds its text in every language it has been written in; a
reader gets their own language, or English when a guide has not been
translated yet.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["get_guide", "list_guides"]

_COLUMNS = "slug, category, minutes, video_url, action_href, content"


def _localised(row: Any, lang: str, *, full: bool) -> dict[str, Any]:
    content = row["content"] or {}
    body = content.get(lang) or content.get("en") or {}
    out = {
        "slug": row["slug"],
        "category": row["category"],
        "minutes": row["minutes"],
        "has_video": bool(row["video_url"]),
        "title": body.get("title", ""),
        "summary": body.get("summary", ""),
        "language": lang if lang in content else "en",
    }
    if full:
        out["sections"] = body.get("sections", [])
        out["video_url"] = row["video_url"]
        out["action_href"] = row["action_href"]
    return out


async def list_guides(session: AsyncSession, *, lang: str) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                f"SELECT {_COLUMNS} FROM mangaly_content.guide"
                " WHERE published ORDER BY sort_order, slug"
            )
        )
    ).mappings()
    return [_localised(r, lang, full=False) for r in rows]


async def get_guide(session: AsyncSession, *, slug: str, lang: str) -> dict[str, Any] | None:
    row = (
        (
            await session.execute(
                text(
                    f"SELECT {_COLUMNS} FROM mangaly_content.guide WHERE published AND slug = :slug"
                ),
                {"slug": slug},
            )
        )
        .mappings()
        .first()
    )
    return _localised(row, lang, full=True) if row else None
