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
# [Backend A, 2026-09-28] The cache now also holds each term's kind, parent
# and one-line description (migration 018), so the two-level tree
# (category -> capabilities) is served from the same refresh and the same
# dict, never a second query path. `label_for`/`labels_for` are unchanged.
# Traces to: FR04, FR18 (card fields), FR44, FR48, TR048 (5-minute taxonomy
# refresh — this cache refreshes immediately on edit, well inside that budget)
from __future__ import annotations

from dataclasses import dataclass, field

import asyncpg

from app.i18n import DEFAULT_LANGUAGE


@dataclass
class TaxonomyTerm:
    id: int
    kind: str  # category | capability
    slug: str
    status: str  # active | unmapped | merged
    icon: str | None
    parent_slug: str | None
    names: dict[str, str] = field(default_factory=dict)  # lang -> name (English always present)
    descriptions: dict[str, str] = field(default_factory=dict)  # lang -> description (may be empty)

    def name(self, lang: str) -> str:
        return self.names.get(lang) or self.names[DEFAULT_LANGUAGE]

    def description(self, lang: str) -> str | None:
        return self.descriptions.get(lang) or self.descriptions.get(DEFAULT_LANGUAGE)


_CACHE: dict[str, dict[str, str]] = {}
_TERMS: dict[tuple[str, str], TaxonomyTerm] = {}  # (kind, slug) -> term
_CHILDREN: dict[str, list[str]] = {}  # category slug -> capability slugs, ordered by English name


async def refresh_taxonomy_cache(pool: asyncpg.Pool) -> None:
    global _CACHE, _TERMS, _CHILDREN
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT t.id, t.kind, t.slug, t.status, t.icon, t.name_en, t.name_hi, t.name_te,
                      t.description_en, t.description_hi, t.description_te, p.slug AS parent_slug
                 FROM vyapar_listings.taxonomy_terms t
                 LEFT JOIN vyapar_listings.taxonomy_terms p ON p.id = t.parent_id
                WHERE t.status != 'merged'
                ORDER BY t.kind, t.name_en"""
        )
    cache: dict[str, dict[str, str]] = {}
    terms: dict[tuple[str, str], TaxonomyTerm] = {}
    children: dict[str, list[str]] = {}
    for r in rows:
        names = {"en": r["name_en"], "hi": r["name_hi"] or r["name_en"], "te": r["name_te"] or r["name_en"]}
        descriptions = {k: v for k, v in (("en", r["description_en"]), ("hi", r["description_hi"]), ("te", r["description_te"])) if v}
        term = TaxonomyTerm(
            id=r["id"], kind=r["kind"], slug=r["slug"], status=r["status"], icon=r["icon"],
            parent_slug=r["parent_slug"], names=names, descriptions=descriptions,
        )
        terms[(r["kind"], r["slug"])] = term
        # Label lookup is by slug alone (a category and a capability may share a
        # slug, e.g. "events"); the capability wins the label, as before.
        if r["slug"] not in cache or r["kind"] == "capability":
            cache[r["slug"]] = names
        if r["kind"] == "capability" and r["parent_slug"] and r["status"] == "active":
            children.setdefault(r["parent_slug"], []).append(r["slug"])
    _CACHE, _TERMS, _CHILDREN = cache, terms, children


def label_for(slug: str, lang: str = "en") -> str:
    entry = _CACHE.get(slug)
    if entry is None:
        return slug.replace("_", " ")  # unmapped label — humanized, never the raw slug with underscores
    return entry.get(lang) or entry["en"]


def labels_for(slugs: list[str], lang: str = "en") -> list[str]:
    return [label_for(s, lang) for s in slugs]


def term_for(kind: str, slug: str) -> TaxonomyTerm | None:
    return _TERMS.get((kind, slug))


def categories() -> list[TaxonomyTerm]:
    """Active categories, ordered by English name."""
    return [t for (kind, _), t in _TERMS.items() if kind == "category" and t.status == "active"]


def children_of(category_slug: str) -> list[str]:
    """Active capability slugs under one category (empty when unknown)."""
    return list(_CHILDREN.get(category_slug, []))


def description_for(kind: str, slug: str, lang: str = "en") -> str | None:
    term = _TERMS.get((kind, slug))
    return term.description(lang) if term else None
