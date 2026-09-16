# [TR032] Provider performance events (FR32): impression, detail view, save,
# enquiry, confirmed outcome — the five counts a provider report shows.
# Approach: one tiny writer every surface calls. `member_id` is always stored
# as NULL — FR32 reports never show member identity, so the data isn't
# collected in the first place (minimisation beats filtering later).
# `sponsored` records whether this event happened in a paid slot / while the
# target was boosted, which is what the boosted-vs-organic split counts.
# Traces to: FR32, TR032, SP032, FR30
from __future__ import annotations

from collections.abc import Iterable

import asyncpg


async def boosted_ids(conn: asyncpg.Connection, target_kind: str, target_ids: Iterable[str]) -> set[str]:
    ids = [str(t) for t in target_ids]
    if not ids:
        return set()
    rows = await conn.fetch("SELECT target_id FROM vyapar_commercial.active_boosts($1, $2::uuid[])", target_kind, ids)
    return {str(r["target_id"]) for r in rows}


async def log_events(
    conn: asyncpg.Connection,
    target_kind: str,
    target_ids: Iterable[str],
    kind: str,
    surface: str,
    sponsored_ids: set[str] | None = None,
) -> None:
    """`sponsored_ids=None` means "sponsored if the target is boosted right
    now" (views, saves, enquiries, outcomes); pass an explicit set for list
    impressions, where the slot itself decides (organic slot = empty set)."""
    ids = [str(t) for t in target_ids if t]
    if not ids:
        return
    if sponsored_ids is None:
        sponsored_ids = await boosted_ids(conn, target_kind, ids)
    await conn.executemany(
        "INSERT INTO vyapar_commercial.impressions (target_kind, target_id, member_id, surface, sponsored, kind) VALUES ($1, $2, NULL, $3, $4, $5)",
        [(target_kind, tid, surface, tid in sponsored_ids, kind) for tid in ids],
    )
