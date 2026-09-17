# [Coordinator browser-check bug #2 fix] Every listing/opportunity card was
# rendering raw `taxonomy_terms.slug` values ("software_it", "gst_filing")
# instead of the localized display name — the join to `taxonomy_terms` for
# display purposes had never actually been built anywhere.
# Approach: a small in-process cache (the whole table is a few dozen rows,
# rarely changes) refreshed at startup and on every admin taxonomy edit
# (`admin_ops.py`), so a lookup is a plain dict access with no per-card query
# fan-out. `label_for()` never raises and never shows a raw slug: an unmapped
# slug is humanized (underscores to spaces) as a last resort rather than
# surfaced verbatim.
# Traces to: FR04, FR18 (card fields), TR048 (5-minute taxonomy refresh —
# this cache refreshes immediately on edit, well inside that budget)
from __future__ import annotations

import asyncpg

_CACHE: dict[str, dict[str, str]] = {}


async def refresh_taxonomy_cache(pool: asyncpg.Pool) -> None:
    global _CACHE
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT slug, name_en, name_hi, name_te FROM vyapar_listings.taxonomy_terms WHERE status != 'merged'"
        )
    _CACHE = {r["slug"]: {"en": r["name_en"], "hi": r["name_hi"] or r["name_en"], "te": r["name_te"] or r["name_en"]} for r in rows}


def label_for(slug: str, lang: str = "en") -> str:
    entry = _CACHE.get(slug)
    if entry is None:
        return slug.replace("_", " ")  # unmapped label — humanized, never the raw slug with underscores
    return entry.get(lang) or entry["en"]


def labels_for(slugs: list[str], lang: str = "en") -> list[str]:
    return [label_for(s, lang) for s in slugs]
