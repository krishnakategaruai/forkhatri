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
    # [Trust pack] a profile whose council forbids public reviews (advocates,
    # architects) has no public counts at all, and so no reputation boost.
    from app.services.profession_rules import verdict_for_row

    listing_rows = [r for r in listing_rows if _has_terms(r) is False or verdict_for_row(r).allow_public_reviews]
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


def _has_terms(row) -> bool:
    try:
        row["categories"], row["capabilities"]
        return True
    except (KeyError, IndexError, TypeError):
        return False


def trust_from_reputation(rep: dict | None) -> float:
    """[FR19/FR28] Reputation feeds trust fit ONLY above the threshold, as a
    recommend ratio (counts, never a star-style score). Below it: exactly 0,
    the same as having no reviews — never a penalty."""
    if not rep or rep["interactions"] < NEW_MEMBER_THRESHOLD:
        return 0.0
    return 0.5 * rep["recommends"] / rep["interactions"]


# ---------------------------------------------------------------------------
# [IMP-B, 2026-09-28] Count-based badges (FR28: counts, never a star score).
# Every badge is a plain threshold over numbers migration 019's
# `badge_inputs()` returns — the rules are listed once, here, so a badge
# can never mean two different things on two screens. The result is cached
# on the member row (`badges`, `badges_computed_at`) and recomputed on read
# once older than `badges_cache_seconds` (nightly-equivalent). `earned_at`
# is kept from the previous cache when a badge is still held, so it records
# when it was first earned, not when the cache last refreshed.
# Traces to: FR28, TR028, FR19 (trust context), FR23 (response time)
# ---------------------------------------------------------------------------
import json
from datetime import datetime, timezone

from pydantic import BaseModel

from app.config import get_settings
from app.i18n import translate

BADGE_KEYS: tuple[str, ...] = (
    "responds_fast", "reliable", "rising", "top_recommended", "verified_business", "repeat_hires",
)

RESPONDS_FAST_MAX_MINUTES = 120
RESPONDS_FAST_MIN_THREADS = 5
RELIABLE_MIN_REVIEWS = 5
RELIABLE_MIN_RATIO = 0.90
RISING_MAX_MEMBER_DAYS = 90
RISING_MIN_RECOMMENDS = 3
TOP_MIN_REVIEWS = 20
TOP_MIN_RATIO = 0.95
REPEAT_HIRES_MIN_HIRERS = 3


class BadgeOut(BaseModel):
    key: str
    label: str
    description: str
    earned_at: str


def compute_badge_keys(inputs: dict, now: datetime | None = None) -> list[str]:
    """Pure rule evaluation over one member's counts (see badge_inputs())."""
    now = now or datetime.now(timezone.utc)
    reviews = int(inputs.get("reviews") or 0)
    recommends = int(inputs.get("recommends") or 0)
    ratio = (recommends / reviews) if reviews else 0.0
    answered = int(inputs.get("answered") or 0)
    median = inputs.get("median_minutes")
    member_since = inputs.get("member_since")
    member_days = (now - member_since).days if member_since else None
    keys: list[str] = []
    if answered >= RESPONDS_FAST_MIN_THREADS and median is not None and median < RESPONDS_FAST_MAX_MINUTES:
        keys.append("responds_fast")
    if reviews >= RELIABLE_MIN_REVIEWS and ratio >= RELIABLE_MIN_RATIO:
        keys.append("reliable")
    if member_days is not None and member_days < RISING_MAX_MEMBER_DAYS and recommends >= RISING_MIN_RECOMMENDS:
        keys.append("rising")
    if reviews >= TOP_MIN_REVIEWS and ratio >= TOP_MIN_RATIO:
        keys.append("top_recommended")
    if inputs.get("verified_business"):
        keys.append("verified_business")
    if int(inputs.get("repeat_hirers") or 0) >= REPEAT_HIRES_MIN_HIRERS:
        keys.append("repeat_hires")
    return keys


def badge_out(key: str, earned_at: str, lang: str) -> BadgeOut:
    return BadgeOut(
        key=key,
        label=translate(f"reputation.badge.{key}.label", lang),
        description=translate(f"reputation.badge.{key}.description", lang),
        earned_at=earned_at,
    )


async def badges_for_members(conn: asyncpg.Connection, member_ids: Sequence[str], lang: str = "en") -> dict[str, list[BadgeOut]]:
    """Keyed by member id. Fresh cache rows are returned as they are; stale
    or never-computed ones are recomputed from live counts and stored."""
    ids = list({m for m in member_ids if m})
    if not ids:
        return {}
    max_age = get_settings().badges_cache_seconds
    cached = await conn.fetch("SELECT * FROM vyapar_identity.member_badges($1::text[], $2)", ids, max_age)
    out: dict[str, list[BadgeOut]] = {}
    stale: dict[str, list[dict]] = {}
    for r in cached:
        raw = r["badges"]
        items = json.loads(raw) if isinstance(raw, str) else list(raw or [])
        if r["fresh"]:
            out[r["member_id"]] = [badge_out(b["key"], b["earned_at"], lang) for b in items if b.get("key") in BADGE_KEYS]
        else:
            stale[r["member_id"]] = items
    if stale:
        now = datetime.now(timezone.utc)
        rows = await conn.fetch("SELECT * FROM vyapar_identity.badge_inputs($1::text[])", list(stale))
        for r in rows:
            previous = {b["key"]: b["earned_at"] for b in stale.get(r["member_id"], []) if "key" in b}
            keys = compute_badge_keys(dict(r), now)
            fresh_items = [{"key": k, "earned_at": previous.get(k) or now.isoformat()} for k in keys]
            await conn.execute("SELECT vyapar_identity.store_badges($1, $2::jsonb)", r["member_id"], json.dumps(fresh_items))
            out[r["member_id"]] = [badge_out(b["key"], b["earned_at"], lang) for b in fresh_items]
    # [Trust pack] no "Reliable", "Top recommended" … on an advocate or architect
    from app.services.profession_rules import restricted_members

    for member in await restricted_members(conn, list(out)):
        out[member] = [b for b in out[member] if b.key in FACT_BADGES]
    return out


# [Trust pack] Badges that are a fact, not a verdict from other people: kept
# on a profile whose council forbids reviews and ranking badges.
FACT_BADGES = frozenset({"verified_business"})


async def badges_for_member(conn: asyncpg.Connection, member_id: str, lang: str = "en") -> list[BadgeOut]:
    return (await badges_for_members(conn, [member_id], lang)).get(member_id, [])


# [IMP-B] Poster context on an opportunity detail read: the opportunities
# owner merges this via `hooks.run_opportunity_enrichers(...)` (see
# app/services/hooks.py); feed cards already carry `poster_badges` directly.
from app.services import hooks as _hooks  # noqa: E402


@_hooks.register_opportunity_enricher
async def enrich_opportunity_with_poster_badges(conn: asyncpg.Connection, ctx, lang: str, opportunity: dict) -> dict:
    poster_id = opportunity.get("poster_id")
    if not poster_id:
        return {}
    return {"poster_badges": [b.model_dump() for b in await badges_for_member(conn, poster_id, lang)]}
