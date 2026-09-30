# [Profile recommendations — product owner, 2026-09-21: "make sure we are
# prioritizing to show the skills as per person's profile, and like similar
# profiles, we will have other profiles for you"]
#
# One card shape and one matching rule for every place Vyapar recommends a
# business or professional profile:
#   - "Similar profiles" at the end of a profile (listing) page, the profile
#     counterpart of "Similar opportunities" on an opportunity page;
#   - "Profiles that match this" on a poster's own opportunity, so a person
#     who posted a job sees who already has the skills (Upwork's "invite
#     freelancers", without a paid tier).
#
# Matching is by shared skills, ordered by how many overlap, and every card
# carries WHICH skills matched, so the card can say why it is shown
# instead of asking the person to trust an opaque list.
#
# Privacy (FR05): a listing whose owner turned off capability_visible is
# never matched on its skills and never shows them, because matching on
# hidden skills would reveal them. RLS already limits the rows to public,
# active listings; `discoverable = false` listings are excluded too.
# Traces to: FR16, FR19, FR05, FR28, UX09
from __future__ import annotations

import asyncpg
from pydantic import BaseModel

from app.reputation import badges_for_members, reputation_for_listings
from app.taxonomy_cache import labels_for

CARD_LIMIT = 4
CARD_POOL = 40  # candidates re-ordered in Python before the top CARD_LIMIT are shown


class ProfileCard(BaseModel):
    id: str
    kind: str  # business | professional
    name: str
    headline: str | None
    locality: str
    verified: bool
    availability: str | None  # now | this_week | later
    experience_years: int | None
    matched_labels: list[str]  # the skills that caused this recommendation
    other_labels: list[str]  # the profile's remaining skills, for context
    reputation: dict | None = None
    badges: list[dict] = []  # [IMP-B/FR28] owner's count-based badges, localized


async def recommend_profiles(
    conn: asyncpg.Connection,
    *,
    skills: list[str],
    categories: list[str],
    exclude_owner_ids: list[str],
    exclude_listing_id: str | None,
    viewer_locality: str | None,
    require_opportunity_participation: bool,
    lang: str,
) -> list[ProfileCard]:
    if not skills and not categories:
        return []
    rows = await conn.fetch(
        """SELECT l.*,
                  CASE WHEN l.capability_visible
                       THEN cardinality(ARRAY(SELECT unnest(l.capabilities) INTERSECT SELECT unnest($1::text[])))
                       ELSE 0 END AS skill_overlap,
                  cardinality(ARRAY(SELECT unnest(l.categories) INTERSECT SELECT unnest($2::text[]))) AS category_overlap,
                  ($5::text IS NOT NULL AND l.locality ILIKE '%' || $5 || '%') AS near_viewer
             FROM vyapar_listings.listings l
            WHERE l.state IN ('active_unverified', 'active_verified')
              AND l.discoverable
              AND NOT (l.owner_id = ANY($3::text[]))
              AND ($4::uuid IS NULL OR l.id <> $4::uuid)
              AND (NOT $6 OR l.opportunity_participation)
              AND ((l.capability_visible AND l.capabilities && $1::text[]) OR l.categories && $2::text[])
            ORDER BY skill_overlap DESC,
                     category_overlap DESC,
                     (l.state = 'active_verified') DESC,
                     ($5::text IS NOT NULL AND l.locality ILIKE '%' || $5 || '%') DESC,
                     (l.availability = 'now') DESC,
                     l.updated_at DESC
            LIMIT $7""",
        skills, categories, exclude_owner_ids, exclude_listing_id, viewer_locality,
        require_opportunity_participation, CARD_POOL,
    )
    # [Trust pack] A profile whose council forbids advertising (advocates,
    # architects) gets no verified-first or "available now" boost: among
    # equal skill matches it is ordered by nearness to the viewer, then name,
    # exactly as in search. Others keep the SQL order above.
    from app.services.profession_rules import verdict_for_row

    def _key(item):
        index, r = item
        neutral = not verdict_for_row(r).allow_ranking_boost
        return (-r["skill_overlap"], -r["category_overlap"],
                0 if neutral else -int(r["state"] == "active_verified"),
                -int(bool(r["near_viewer"])),
                0 if neutral else -int(r["availability"] == "now"),
                (r["name"] or "").lower() if neutral else "", index)

    rows = [r for _, r in sorted(enumerate(rows), key=_key)][:CARD_LIMIT]
    reputation = await reputation_for_listings(conn, rows)
    owner_badges = await badges_for_members(conn, [r["owner_id"] for r in rows], lang)
    wanted = set(skills)
    cards: list[ProfileCard] = []
    for r in rows:
        caps = list(r["capabilities"]) if r["capability_visible"] else []
        matched = [c for c in caps if c in wanted]
        others = [c for c in caps if c not in wanted]
        cards.append(
            ProfileCard(
                id=str(r["id"]),
                kind=r["kind"],
                name=r["name"],
                headline=r["headline"],
                locality=r["locality"],
                verified=r["verification_state"] in ("verified", "expiring"),
                availability=r["availability"],
                experience_years=r["experience_years"],
                matched_labels=labels_for(matched, lang),
                other_labels=labels_for(others, lang),
                reputation=reputation.get(str(r["id"])),
                badges=[b.model_dump() for b in owner_badges.get(r["owner_id"], [])],
            )
        )
    return cards
