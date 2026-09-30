# [Trust pack, 2026-09-30 — VISION-2040 item 5] Profession-aware profiles.
#
# Why: the Bar Council of India's Rule 36 forbids advocates to advertise or
# solicit work (the BCI acted against JustDial and Sulekha listings for it),
# and the Council of Architecture bars architects from advertising and from
# offering discounts. A marketplace that lets them buy promotion, collect
# public reviews and rank above each other breaks those rules for them. ICAI
# lets chartered accountants advertise non-assurance services from 1 Apr 2026.
#
# How: the rules are DATA (vyapar_listings.profession_rules, migration 028),
# keyed by taxonomy term, never code per member. A profile (listing) falls
# under a rule when one of its categories, skills, or a skill's parent
# category matches; when several match, the most restrictive answer wins for
# each switch. Everything here reads an in-process cache refreshed at startup
# and hourly (same pattern as app/taxonomy_cache.py).
#
# Where each switch is enforced (one call site each):
#   allow_promotion      commercial._eligible_target -> 403 promotion_not_permitted_for_profession
#   allow_public_reviews reputation.reputation_for_listings (no counts), reputation.badges_for_members
#                        (no reputation badges), reviews.list_listing_reviews / create_review
#   allow_ranking_boost  discovery.search_listings (no trust/reputation boost, no Sponsored slot,
#                        neutral distance-then-name order among equals)
#   allow_public_prices  packages (hidden from others, owner cannot add), listing `rates` hidden
#   permitted fields     listings._row_to_out for a non-owner (public_view below)
# Traces to: FR01, FR16, FR19, FR28, FR30, VISION-2040 item 5
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import asyncpg
from pydantic import BaseModel, Field

from app.i18n import translate
from app.taxonomy_cache import term_for


@dataclass(frozen=True)
class ProfessionRule:
    id: int
    term_kind: str
    term_slug: str
    profession: str
    regulator: str
    rule_reference: str
    allow_promotion: bool
    allow_public_reviews: bool
    allow_ranking_boost: bool
    allow_public_prices: bool
    permitted_profile_fields: tuple[str, ...] | None
    note_key: str | None
    rules_checked_on: date
    source_url: str | None

    @property
    def restricted(self) -> bool:
        return not (self.allow_promotion and self.allow_public_reviews and self.allow_ranking_boost
                    and self.allow_public_prices and self.permitted_profile_fields is None)


@dataclass(frozen=True)
class Verdict:
    """The combined answer for one profile (the most restrictive of its rules)."""
    rules: tuple[ProfessionRule, ...] = field(default_factory=tuple)

    @property
    def primary(self) -> ProfessionRule | None:
        restricted = [r for r in self.rules if r.restricted]
        return (restricted or list(self.rules) or [None])[0]

    def _all(self, attr: str) -> bool:
        return all(getattr(r, attr) for r in self.rules)

    @property
    def allow_promotion(self) -> bool:
        return self._all("allow_promotion")

    @property
    def allow_public_reviews(self) -> bool:
        return self._all("allow_public_reviews")

    @property
    def allow_ranking_boost(self) -> bool:
        return self._all("allow_ranking_boost")

    @property
    def allow_public_prices(self) -> bool:
        return self._all("allow_public_prices")

    @property
    def restricted(self) -> bool:
        return any(r.restricted for r in self.rules)

    @property
    def permitted_profile_fields(self) -> frozenset[str] | None:
        sets = [frozenset(r.permitted_profile_fields) for r in self.rules if r.permitted_profile_fields is not None]
        if not sets:
            return None
        out = sets[0]
        for s in sets[1:]:
            out &= s
        return out


NO_RULE = Verdict()
_RULES: dict[tuple[str, str], ProfessionRule] = {}


async def refresh_profession_rules(pool: asyncpg.Pool) -> None:
    global _RULES
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM vyapar_listings.profession_rules WHERE active ORDER BY id")
    _RULES = {
        (r["term_kind"], r["term_slug"]): ProfessionRule(
            id=r["id"], term_kind=r["term_kind"], term_slug=r["term_slug"], profession=r["profession"], regulator=r["regulator"],
            rule_reference=r["rule_reference"], allow_promotion=r["allow_promotion"], allow_public_reviews=r["allow_public_reviews"],
            allow_ranking_boost=r["allow_ranking_boost"], allow_public_prices=r["allow_public_prices"],
            permitted_profile_fields=tuple(r["permitted_profile_fields"]) if r["permitted_profile_fields"] is not None else None,
            note_key=r["note_key"], rules_checked_on=r["rules_checked_on"], source_url=r["source_url"],
        )
        for r in rows
    }


def all_rules() -> list[ProfessionRule]:
    return list(_RULES.values())


def verdict_for(categories: list[str] | None, capabilities: list[str] | None) -> Verdict:
    if not _RULES:
        return NO_RULE
    keys: list[tuple[str, str]] = [("category", c) for c in (categories or [])]
    for cap in capabilities or []:
        keys.append(("capability", cap))
        term = term_for("capability", cap)
        if term is not None and term.parent_slug:
            keys.append(("category", term.parent_slug))
    seen: dict[int, ProfessionRule] = {}
    for k in keys:
        rule = _RULES.get(k)
        if rule is not None:
            seen.setdefault(rule.id, rule)
    return Verdict(tuple(sorted(seen.values(), key=lambda r: (not r.restricted, r.id)))) if seen else NO_RULE


def _field(row, key: str):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def verdict_for_row(row) -> Verdict:
    """For a listings row (asyncpg.Record or dict) carrying categories and capabilities."""
    return verdict_for(list(_field(row, "categories") or []), list(_field(row, "capabilities") or []))


async def verdict_for_listing(conn: asyncpg.Connection, listing_id) -> Verdict:
    try:
        row = await conn.fetchrow("SELECT categories, capabilities FROM vyapar_listings.listings WHERE id = $1", listing_id)
    except asyncpg.DataError:
        row = None
    return verdict_for_row(row) if row is not None else NO_RULE


async def restricted_members(conn: asyncpg.Connection, member_ids: list[str], attr: str = "allow_public_reviews") -> set[str]:
    """Members whose live profile falls under a rule that turns `attr` off."""
    ids = [m for m in set(member_ids) if m]
    if not ids or not _RULES:
        return set()
    rows = await conn.fetch(
        """SELECT owner_id, categories, capabilities FROM vyapar_listings.listings
            WHERE owner_id = ANY($1::text[]) AND state IN ('draft','submitted','active_unverified','active_verified')""", ids)
    return {r["owner_id"] for r in rows if not getattr(verdict_for_row(r), attr)}


# ---------------------------------------------------------------------------
# What a profile says about its profession (ListingOut.profession)
# ---------------------------------------------------------------------------
class ProfessionOut(BaseModel):
    profession: str = Field(description="advocate | architect | chartered_accountant")
    profession_label: str
    regulator: str = Field(description="The council, as a proper name")
    restricted: bool = Field(description="True when the council limits what the profile may show or buy")
    allow_promotion: bool
    allow_public_reviews: bool
    allow_ranking_boost: bool
    allow_public_prices: bool
    permitted_fields: list[str] | None = Field(description="ListingOut fields a non-owner sees; null = every field")
    hidden_fields: list[str] = Field(default_factory=list, description="Fields this viewer does not see because of the rule (owner: what others do not see)")
    contact_label: str = Field(description='The neutral action label, e.g. "Contact"')
    note: str | None = Field(default=None, description="Localized 'information only' or wording note")
    rule_reference: str
    rules_checked_on: str
    source_url: str | None = None


# ListingOut fields a council-restricted profile never shows to others, unless
# the rule lists them as permitted.
FILTERABLE_FIELDS = ("headline", "description", "business_headline", "business_description", "rates",
                     "evidence_links", "intent_state", "availability")


def profession_out(verdict: Verdict, lang: str, *, hidden: list[str] | None = None) -> ProfessionOut | None:
    rule = verdict.primary
    if rule is None:
        return None
    permitted = verdict.permitted_profile_fields
    return ProfessionOut(
        profession=rule.profession,
        profession_label=translate(f"listings.profession.name.{rule.profession}", lang),
        regulator=rule.regulator,
        restricted=verdict.restricted,
        allow_promotion=verdict.allow_promotion,
        allow_public_reviews=verdict.allow_public_reviews,
        allow_ranking_boost=verdict.allow_ranking_boost,
        allow_public_prices=verdict.allow_public_prices,
        permitted_fields=sorted(permitted) if permitted is not None else None,
        hidden_fields=hidden or [],
        contact_label=translate("listings.profession.contact" if verdict.restricted else "listings.profession.contactDefault", lang),
        note=translate(f"listings.{rule.note_key}", lang) if rule.note_key else None,
        rule_reference=rule.rule_reference,
        rules_checked_on=rule.rules_checked_on.isoformat(),
        source_url=rule.source_url,
    )


def hidden_fields_for(verdict: Verdict) -> list[str]:
    permitted = verdict.permitted_profile_fields
    hidden = [] if permitted is None else [f for f in FILTERABLE_FIELDS if f not in permitted]
    if not verdict.allow_public_prices and "rates" not in hidden:
        hidden.append("rates")
    return hidden


def apply_public_view(out, verdict: Verdict, *, is_owner: bool, lang: str) -> None:
    """Strips what the council does not allow from a ListingOut shown to
    someone other than its owner. The owner sees everything, plus
    `profession.hidden_fields` so their editor can say what others do not see."""
    if not verdict.rules:
        return
    hidden = hidden_fields_for(verdict)
    out.profession = profession_out(verdict, lang, hidden=hidden).model_dump() if verdict.primary else None
    if is_owner:
        return
    for name in hidden:
        if name in ("evidence_links",):
            setattr(out, name, [])
        else:
            setattr(out, name, None)
    if not verdict.allow_public_reviews:
        out.reputation = None
    if not verdict.allow_ranking_boost:
        out.sponsored = False
    if not verdict.allow_public_prices:
        out.packages = []


class ProfessionRuleOut(BaseModel):
    term_kind: str
    term_slug: str
    term_label: str
    profession: str
    profession_label: str
    regulator: str
    allow_promotion: bool
    allow_public_reviews: bool
    allow_ranking_boost: bool
    allow_public_prices: bool
    permitted_fields: list[str] | None
    note: str | None
    rule_reference: str
    rules_checked_on: str
    source_url: str | None


def list_rules_out(lang: str) -> list[ProfessionRuleOut]:
    from app.taxonomy_cache import label_for

    def term_label(r: ProfessionRule) -> str:
        term = term_for(r.term_kind, r.term_slug)  # the category's own name, not a same-slug skill's
        return term.name(lang) if term is not None else label_for(r.term_slug, lang)

    return [
        ProfessionRuleOut(
            term_kind=r.term_kind, term_slug=r.term_slug, term_label=term_label(r), profession=r.profession,
            profession_label=translate(f"listings.profession.name.{r.profession}", lang), regulator=r.regulator,
            allow_promotion=r.allow_promotion, allow_public_reviews=r.allow_public_reviews, allow_ranking_boost=r.allow_ranking_boost,
            allow_public_prices=r.allow_public_prices,
            permitted_fields=list(r.permitted_profile_fields) if r.permitted_profile_fields is not None else None,
            note=translate(f"listings.{r.note_key}", lang) if r.note_key else None, rule_reference=r.rule_reference,
            rules_checked_on=r.rules_checked_on.isoformat(), source_url=r.source_url,
        )
        for r in all_rules()
    ]
