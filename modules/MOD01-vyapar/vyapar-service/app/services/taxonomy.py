# [Backend A, 2026-09-28] The taxonomy tree as a product surface: every
# category with its capabilities (skills / roles), each with a localized
# label and a one-line plain-language description (migration 018). Served
# from the in-process cache that `taxonomy_cache.py` already keeps warm, so
# a call is a dict walk, never a query. The web app's onboarding, the
# opportunity composer's skill picker and an agent reasoning about "what
# kinds of work exist here" all read this one tree.
# Traces to: FR01, FR04, FR44, FR48, TR048
from __future__ import annotations

from pydantic import BaseModel, Field

from app import taxonomy_cache


class TaxonomyTermOut(BaseModel):
    slug: str = Field(description="Stable identifier, the value stored on listings and opportunities")
    label: str = Field(description="Display name in the caller's language")
    description: str | None = Field(default=None, description="One plain-language line in the caller's language")


class TaxonomyCategoryOut(TaxonomyTermOut):
    icon: str | None = None
    children: list[TaxonomyTermOut] = []


class TaxonomyTreeOut(BaseModel):
    language: str
    categories: list[TaxonomyCategoryOut]


def get_taxonomy_tree(lang: str) -> TaxonomyTreeOut:
    out: list[TaxonomyCategoryOut] = []
    for cat in taxonomy_cache.categories():
        children: list[TaxonomyTermOut] = []
        for slug in taxonomy_cache.children_of(cat.slug):
            term = taxonomy_cache.term_for("capability", slug)
            if term is None:
                continue
            children.append(TaxonomyTermOut(slug=slug, label=term.name(lang), description=term.description(lang)))
        children.sort(key=lambda t: t.label.casefold())
        out.append(
            TaxonomyCategoryOut(
                slug=cat.slug, label=cat.name(lang), description=cat.description(lang), icon=cat.icon, children=children
            )
        )
    out.sort(key=lambda c: c.label.casefold())
    return TaxonomyTreeOut(language=lang, categories=out)
