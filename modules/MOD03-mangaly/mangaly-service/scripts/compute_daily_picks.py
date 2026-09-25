"""[DEC-V1-030] Daily maintenance: compute "Most compatible today" for every
searchable candidate and store it in `mangaly_discovery.daily_pick`.

A deferred-acceptance (Gale–Shapley) pass over everyone searchable, two
sides by the "Looking for" rule, each person's list ordered by reciprocity
(`components/discovery/stable_matching.py`). Idempotent for the day: the
day's rows are replaced in one transaction, so running it twice leaves one
set of picks. Run it once a day (a scheduler, or by hand):

    python -m scripts.compute_daily_picks            # today
    python -m scripts.compute_daily_picks --date 2026-09-22

Owner connection, deliberately: the pass needs EVERY searchable row, every
block and every open request at once, which no single account context may
read under RLS — the same narrow maintenance exception
`scripts/reindex_discovery.py` documents. The application role never writes
this table (migration 050 grants it SELECT only).

What is read, and all that is read: `discovery_profile_index` (searchable
rows and their `ranking_input_snapshot`), `mangaly_safety.block`, and
`mangaly_connection.connection_request` rows that are pending or accepted.
No view, like, message or visit count exists in any of these, and none is
computed here.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncpg  # noqa: E402

from app.components.discovery.interface import reciprocal_reasons  # noqa: E402
from app.components.discovery.stable_matching import compute_daily_picks  # noqa: E402
from app.config.ranking_weights import RANKING_WEIGHTS_VERSION  # noqa: E402

_OWNER_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"


async def _load(conn: asyncpg.Connection) -> tuple[dict[UUID, dict], set[frozenset], dict[UUID, str]]:
    people: dict[UUID, dict] = {}
    for row in await conn.fetch(
        "SELECT profile_id, ranking_input_snapshot FROM mangaly_discovery.discovery_profile_index WHERE searchable"
    ):
        snapshot = row["ranking_input_snapshot"]
        people[row["profile_id"]] = json.loads(snapshot) if isinstance(snapshot, str) else dict(snapshot or {})

    excluded: set[frozenset] = set()
    for row in await conn.fetch("SELECT blocker_account_id, blocked_account_id FROM mangaly_safety.block"):
        excluded.add(frozenset((row["blocker_account_id"], row["blocked_account_id"])))
    for row in await conn.fetch(
        "SELECT subject_account_id, target_profile_id FROM mangaly_connection.connection_request "
        "WHERE status IN ('pending', 'accepted')"
    ):
        excluded.add(frozenset((row["subject_account_id"], row["target_profile_id"])))

    names = {
        row["account_id"]: row["name"]
        for row in await conn.fetch("SELECT account_id, name FROM mangaly_profile.profile")
    }
    return people, excluded, names


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--dry-run", action="store_true", help="compute and print, write nothing")
    args = parser.parse_args(argv)
    day: date = args.date

    conn = await asyncpg.connect(_OWNER_DSN)
    try:
        people, excluded, names = await _load(conn)
        result = compute_daily_picks(people, day=day, excluded_pairs=excluded)

        rows = [
            (
                p.account_id,
                p.pick_account_id,
                day,
                p.rank,
                json.dumps(reciprocal_reasons(people[p.account_id], people[p.pick_account_id])),
            )
            for p in result.picks
        ]
        if not args.dry_run:
            async with conn.transaction():
                await conn.execute("DELETE FROM mangaly_discovery.daily_pick WHERE pick_date = $1", day)
                await conn.executemany(
                    "INSERT INTO mangaly_discovery.daily_pick "
                    "(account_id, pick_account_id, pick_date, rank, reasons) "
                    "VALUES ($1, $2, $3, $4, CAST($5 AS jsonb))",
                    rows,
                )

        print(f"\nMost compatible today — {day.isoformat()} ({RANKING_WEIGHTS_VERSION})")
        print(f"  searchable pool: {len(people)} ({result.proposers} {result.proposer_gender} proposing, {result.receivers} receiving)")
        print(f"  excluded pairs (blocked / requested / connected): {len(excluded)}")
        for i, (pairs, proposals) in enumerate(zip(result.matched_pairs_by_round, result.proposals_by_round, strict=True), start=1):
            print(f"  round {i}: {pairs} stable pairs, {proposals} proposals")
        with_pick = {p.account_id for p in result.picks if p.rank == 1}
        print(f"  people with a rank-1 pick: {len(with_pick)} of {len(people)}; without: {len(people) - len(with_pick)}")
        print(f"  rows {'computed (dry run)' if args.dry_run else 'written'}: {len(rows)}\n")
        for p in sorted(result.picks, key=lambda p: (names.get(p.account_id, ""), p.rank)):
            if p.rank != 1:
                continue
            why = reciprocal_reasons(people[p.account_id], people[p.pick_account_id])
            print(f"  {names.get(p.account_id, p.account_id):<22} -> {names.get(p.pick_account_id, p.pick_account_id):<22} {[r['key'] for r in why]}")
        print()
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
