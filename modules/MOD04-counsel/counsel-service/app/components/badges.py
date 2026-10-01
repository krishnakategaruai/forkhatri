"""Consultant milestone badges.

Badges are earned from work on Counsel, never bought and never granted by
hand. Every badge has an exact rule over real numbers (completed
consultations, distinct and repeat clients, reviews, reliability, verified
checks, hours, tenure), so a badge can always be explained. An award keeps the
date it was first earned and the numbers at that moment; later drops (a bad
month) do not revoke history, but the *current* standing is recomputed.

Standing (new → rising → established → senior → distinguished) summarises the
milestones. It is the input for future premium price ranges and awards; it
never changes a price by itself (pricing stays the consultant's decision).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.components import notifications

PROFESSIONAL_CHECKS = {"qualification", "certification", "registration"}


@dataclass(frozen=True)
class Badge:
    id: str
    metric: str                 # key in the metrics dict
    levels: tuple[int, ...]     # thresholds; one level per threshold
    min_reviews: int = 0        # quality badges need enough reviews to mean something


BADGES: tuple[Badge, ...] = (
    Badge("consultations", "completed", (1, 10, 50, 100, 250, 500)),
    Badge("clients", "clients", (10, 50, 150)),
    Badge("repeat_trust", "repeat_clients", (3, 10, 25)),
    Badge("highly_rated", "rating_x10", (48,), min_reviews=10),
    Badge("on_time", "punctuality_x10", (48,), min_reviews=10),
    Badge("reliable", "reliable_run", (20, 50)),
    Badge("hours", "hours", (10, 50, 100, 250)),
    Badge("verified_professional", "professional_checks", (1,)),
    Badge("tenure", "years", (1, 3, 5)),
)

STANDING_ORDER = ("new", "rising", "established", "senior", "distinguished")


async def metrics(conn, provider_id: UUID) -> dict:
    r = await conn.fetchrow(
        """
        SELECT
          (SELECT count(*) FROM booking WHERE provider_id=$1 AND status='completed')                                   AS completed,
          (SELECT count(DISTINCT seeker_id) FROM booking WHERE provider_id=$1 AND status='completed')                  AS clients,
          (SELECT count(*) FROM (SELECT seeker_id FROM booking WHERE provider_id=$1 AND status='completed'
                                  GROUP BY seeker_id HAVING count(*) > 1) x)                                            AS repeat_clients,
          (SELECT coalesce(sum(duration_min),0) FROM booking WHERE provider_id=$1 AND status='completed')                AS minutes,
          (SELECT count(*) FROM review WHERE provider_id=$1 AND NOT hidden)                                             AS reviews,
          (SELECT avg(overall) FROM review WHERE provider_id=$1 AND NOT hidden)                                         AS rating,
          (SELECT avg(punctuality) FROM review WHERE provider_id=$1 AND NOT hidden)                                     AS punctuality,
          (SELECT created_at FROM provider WHERE member_id=$1)                                                          AS since
        """, provider_id)
    # Reliability run: completed consultations since the consultant last cancelled or missed one.
    last_fault = await conn.fetchval(
        "SELECT max(coalesce(cancelled_at, starts_at)) FROM booking WHERE provider_id=$1 AND status IN ('cancelled_by_provider','no_show_provider')", provider_id)
    run = await conn.fetchval(
        "SELECT count(*) FROM booking WHERE provider_id=$1 AND status='completed' AND ($2::timestamptz IS NULL OR starts_at > $2)", provider_id, last_fault)
    checks = {x["dimension"] for x in await conn.fetch("SELECT dimension FROM verification WHERE provider_id=$1", provider_id)}
    since = r["since"] or datetime.now(timezone.utc)
    return {
        "completed": r["completed"], "clients": r["clients"], "repeat_clients": r["repeat_clients"],
        "hours": int(r["minutes"] // 60), "reviews": r["reviews"],
        "rating_x10": int(round(float(r["rating"]) * 10)) if r["rating"] is not None else 0,
        "punctuality_x10": int(round(float(r["punctuality"]) * 10)) if r["punctuality"] is not None else 0,
        "reliable_run": run,
        "professional_checks": 1 if ("identity" in checks and checks & PROFESSIONAL_CHECKS) else 0,
        "years": int((datetime.now(timezone.utc) - since).days // 365),
    }


def earned_levels(m: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for b in BADGES:
        if m["reviews"] < b.min_reviews:
            continue
        level = sum(1 for th in b.levels if m[b.metric] >= th)
        if level:
            out[b.id] = level
    return out


def standing(m: dict) -> str:
    """A plain summary for ranking, admin and future premium ranges."""
    c, rating_ok = m["completed"], (m["reviews"] >= 10 and m["rating_x10"] >= 45) or m["reviews"] < 10
    if c >= 250 and m["repeat_clients"] >= 25 and m["reviews"] >= 10 and m["rating_x10"] >= 47:
        return "distinguished"
    if c >= 100 and m["repeat_clients"] >= 10 and rating_ok:
        return "senior"
    if c >= 25 and rating_ok:
        return "established"
    if c >= 1:
        return "rising"
    return "new"


def next_milestones(m: dict, earned: dict[str, int]) -> list[dict]:
    """The nearest unearned level of each badge, with progress, for the consultant's dashboard."""
    out = []
    for b in BADGES:
        lvl = earned.get(b.id, 0)
        if lvl >= len(b.levels):
            continue
        target = b.levels[lvl]
        have = m[b.metric]
        needs = max(0, b.min_reviews - m["reviews"])
        # A quality badge first needs enough reviews; until then, progress is the review count.
        progress = (m["reviews"] / b.min_reviews) if needs else (min(1.0, have / target) if target else 0)
        out.append({"id": b.id, "level": lvl + 1, "target": target, "have": have, "reviews": m["reviews"], "min_reviews": b.min_reviews,
                    "needs_reviews": needs, "progress": progress})
    out.sort(key=lambda x: -x["progress"])
    return out[:4]


async def refresh(conn, provider_id: UUID, notify: bool = True) -> dict:
    """Recompute; award new levels (dated now, with the numbers), update standing."""
    m = await metrics(conn, provider_id)
    earned = earned_levels(m)
    have = {(r["badge_id"], r["level"]) for r in await conn.fetch("SELECT badge_id, level FROM badge_award WHERE provider_id=$1", provider_id)}
    new = []
    for bid, lvl in earned.items():
        for level in range(1, lvl + 1):
            if (bid, level) not in have:
                await conn.execute("INSERT INTO badge_award (provider_id, badge_id, level, evidence) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING",
                                   provider_id, bid, level, m)
                new.append((bid, level))
    st = standing(m)
    await conn.execute("UPDATE provider SET standing=$2 WHERE member_id=$1 AND standing IS DISTINCT FROM $2", provider_id, st)
    if notify:
        for bid, level in new:
            threshold = next(b.levels[level - 1] for b in BADGES if b.id == bid)
            await notifications.notify(conn, provider_id, "badge.earned", {"badge_id": bid, "level": level, "n": threshold})
    return {"metrics": m, "earned": earned, "standing": st, "new": new}


async def refresh_all(conn) -> None:
    for r in await conn.fetch("SELECT member_id FROM provider WHERE status='approved'"):
        await refresh(conn, r["member_id"])


async def for_display(conn, provider_id: UUID) -> list[dict]:
    """Current (highest) level of each earned badge, oldest first."""
    rows = await conn.fetch(
        "SELECT badge_id, max(level) AS level, min(awarded_at) AS since FROM badge_award WHERE provider_id=$1 GROUP BY badge_id ORDER BY min(awarded_at)", provider_id)
    thresholds = {b.id: b.levels for b in BADGES}
    return [{"id": r["badge_id"], "level": r["level"], "threshold": thresholds.get(r["badge_id"], (0,))[r["level"] - 1] if r["badge_id"] in thresholds else None,
             "since": r["since"].isoformat()} for r in rows]


# Order for the one or two badges shown on a card: the most telling first.
CARD_PRIORITY = ("highly_rated", "repeat_trust", "consultations", "reliable", "on_time", "verified_professional", "hours", "clients", "tenure")
