"""Module registry component — public interface (07-tech-reqs.md TR18).

Every member may enter every available module; `member_module_entry` is an
index for ordering and "continue" affordances, not an access-control list.
Module tiers and roles belong to the modules themselves (TR11).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import LANGUAGES
from app.errors import DomainError


async def list_modules(
    db: AsyncSession, *, language: str, member_id: UUID | None, entry_urls: dict[str, str]
) -> list[dict[str, Any]]:
    lang = language if language in LANGUAGES else "en"
    rows = await db.execute(
        text(
            f"SELECT m.key, m.name, m.tagline_{lang} AS tagline, m.availability, m.accent, e.last_entered_at "
            "FROM registry.module m "
            "LEFT JOIN registry.member_module_entry e "
            "  ON e.module_key = m.key AND e.member_id = CAST(:member_id AS uuid) "
            "ORDER BY m.sort_order"
        ),
        {"member_id": member_id},
    )
    return [
        {
            "key": r.key,
            "name": r.name,
            "tagline": r.tagline,
            "availability": r.availability,
            "entry_url": entry_urls.get(r.key) if r.availability == "available" else None,
            "accent": r.accent,
            "last_entered_at": r.last_entered_at.isoformat() if r.last_entered_at else None,
        }
        for r in rows
    ]


async def enter_module(db: AsyncSession, *, member_id: UUID, key: str, entry_urls: dict[str, str]) -> str:
    availability = await db.scalar(text("SELECT availability FROM registry.module WHERE key = :key"), {"key": key})
    if availability is None:
        raise DomainError("module_unknown", "That module does not exist.", 404)
    entry_url = entry_urls.get(key)
    if availability != "available" or not entry_url:
        raise DomainError("module_unavailable", "That module is not open yet.", 409)
    await db.execute(
        text(
            "INSERT INTO registry.member_module_entry (member_id, module_key) VALUES (:member_id, :key) "
            "ON CONFLICT (member_id, module_key) DO UPDATE "
            "SET last_entered_at = now(), entry_count = registry.member_module_entry.entry_count + 1"
        ),
        {"member_id": member_id, "key": key},
    )
    return entry_url
