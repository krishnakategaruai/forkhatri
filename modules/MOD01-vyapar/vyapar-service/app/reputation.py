# [TR028] Contextual reputation counts, no aggregate score (FR28).
# Approach: one shared composer every listing read uses (detail, search
# cards, partnership cards) — never a second, independently-coded count.
# Counts come live from migration 005's `reputation_for_listings()` (reviews
# WHERE state='published', revealed per the anti-retaliation rule), so a
# hidden/removed/disputed review drops out on the very next read (SP028
# Class E), not after a batch recompute. "Responds in ~X" is the median of
# the owner's answered enquiries (FR23), only once there are 3 of them.
# Below 3 interactions the listing reads "New on Vyapar" and the ranking
# trust signal ignores reputation entirely — no history is not bad history.
# Traces to: FR28, FR19, FR23, TR028, SP028
from __future__ import annotations

from collections.abc import Sequence

import asyncpg

NEW_MEMBER_THRESHOLD = 3


async def reputation_for_listings(conn: asyncpg.Connection, listing_rows: Sequence[asyncpg.Record]) -> dict[str, dict]:
    """Keyed by listing id (str). Each row must carry `id` and `owner_id`."""
    if not listing_rows:
        return {}
    ids = [r["id"] for r in listing_rows]
    owners = list({r["owner_id"] for r in listing_rows})
    rep_rows = await conn.fetch("SELECT * FROM vyapar_reviews.reputation_for_listings($1::uuid[])", ids)
    minute_rows = await conn.fetch("SELECT * FROM vyapar_enquiries.response_minutes($1::text[])", owners)
    minutes = {r["member_id"]: r["minutes"] for r in minute_rows}
    owner_by_id = {str(r["id"]): r["owner_id"] for r in listing_rows}
    out: dict[str, dict] = {}
    for r in rep_rows:
        listing_id = str(r["listing_id"])
        interactions = r["interactions"]
        out[listing_id] = {
            "interactions": interactions,
            "recommends": r["recommends"],
            "top_tags": list(r["top_tags"]),
            "under_review": r["under_review"],
            "response_minutes": minutes.get(owner_by_id.get(listing_id)),
            "new_on_vyapar": interactions < NEW_MEMBER_THRESHOLD,
        }
    return out


def trust_from_reputation(rep: dict | None) -> float:
    """[FR19/FR28] Reputation feeds trust fit ONLY above the threshold, as a
    recommend ratio (counts, never a star-style score). Below it: exactly 0,
    the same as having no reviews — never a penalty."""
    if not rep or rep["interactions"] < NEW_MEMBER_THRESHOLD:
        return 0.0
    return 0.5 * rep["recommends"] / rep["interactions"]
