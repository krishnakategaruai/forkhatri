# [IMP-B, critique L14, 2026-09-29] What a member can do, for relevance.
#
# People describe themselves in two places: the skills they picked at first
# run (`members.capabilities`) and the business or professional profiles they
# publish (`listings.capabilities` / `listings.categories`). A CA who set up
# "Khatri & Associates" but skipped the first-run chips has an empty member
# row, and Discover used to treat her as having no skills at all: no "For
# you", and a "Pay ₹20,000+" row of electrician and baker jobs.
#
# This is the ONE place that answers "what can this viewer do": the union of
# the member's own skills and those on every ACTIVE listing they own (a draft
# or suspended profile doesn't speak for them; archived is gone). Every
# relevance read uses it: feed ranking and rows, "Why this?", the opportunity
# detail's skill match and similar list, and calls_from = matching_only.
# Reading another schema's rows here is Discovery's documented read path
# (07-tech-reqs.md: Discovery owns no tables and reads through the owners'
# rows under RLS; a member always sees their own listings).
# Traces to: FR19, FR20, FR18, critique L14
from __future__ import annotations

import asyncpg

ACTIVE_LISTING_STATES = ("active_unverified", "active_verified")


async def viewer_skills(conn: asyncpg.Connection, member_id: str) -> tuple[list[str], list[str]]:
    """(capabilities, categories) for a member: own skills + active listings'."""
    row = await conn.fetchrow(
        """SELECT m.capabilities AS own,
                  COALESCE((SELECT array_agg(DISTINCT c)
                              FROM vyapar_listings.listings l, unnest(l.capabilities) c
                             WHERE l.owner_id = m.id AND l.state = ANY($2::text[])), '{}') AS listing_caps,
                  COALESCE((SELECT array_agg(DISTINCT c)
                              FROM vyapar_listings.listings l, unnest(l.categories) c
                             WHERE l.owner_id = m.id AND l.state = ANY($2::text[])), '{}') AS listing_cats
             FROM vyapar_identity.members m WHERE m.id = $1""",
        member_id, list(ACTIVE_LISTING_STATES),
    )
    if row is None:
        return [], []
    caps: list[str] = []
    for c in list(row["own"] or []) + list(row["listing_caps"] or []):
        if c not in caps:
            caps.append(c)
    return caps, sorted(set(row["listing_cats"] or []))


async def viewer_capabilities(conn: asyncpg.Connection, member_id: str) -> list[str]:
    return (await viewer_skills(conn, member_id))[0]
