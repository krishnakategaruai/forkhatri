"""The six-month rule for profiles made for someone who never used them.

Product owner, 2026-09-21: "we should delete unused accounts for almost 6
months." A profile a parent made for their son or daughter (DEC-V1-019) that
the child never signs in to take over is removed 180 days after it was made:

  * day 173 — the person who made it is told, in-app, that it will be removed
    in 7 days unless the child signs in (`profile_removal_notice`). DPDP Rules
    2025, Third Schedule, requires notice at least 48 hours before an erasure
    for inactivity; a week gives a family real time to act.
  * day 180, and at least 48 hours after that notice — the profile is erased
    (`mangaly_profile.erase_made_for_profile`, migration 042) and the member the
    ForKhatri platform provisioned for the child is retired, but only if nobody
    ever used it (identity level 0, no password, never signed in).

A profile the child has taken over is never touched: it is theirs, and their
own activity governs it (DEC-V1-010).

Dry run unless `--apply`. `--as-of YYYY-MM-DD` evaluates the rule as if on
that date, for checking what a run would do.

    python -m scripts.retire_unused_made_for_profiles             # dry run
    python -m scripts.retire_unused_made_for_profiles --apply     # scheduled job
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import asyncpg
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings  # noqa: E402

DB_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
REMOVE_AFTER = timedelta(days=180)
NOTICE_BEFORE = timedelta(days=7)
MIN_NOTICE = timedelta(hours=48)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="act; without it nothing changes")
    parser.add_argument("--as-of", type=date.fromisoformat, help="evaluate as if on this date (dry runs)")
    args = parser.parse_args()
    if args.apply and args.as_of:
        print("--as-of is for dry runs only.")
        return 2
    now = datetime.combine(args.as_of, time(12), tzinfo=UTC) if args.as_of else datetime.now(UTC)

    settings = get_settings()
    conn = await asyncpg.connect(DB_DSN)
    try:
        rows = await conn.fetch(
            """
            SELECT p.account_id, p.name, p.created_at, p.created_by_account_id, p.removal_notice_at
              FROM mangaly_profile.profile p
             WHERE p.created_by_account_id IS NOT NULL
               AND p.claimed_at IS NULL
             ORDER BY p.created_at
            """
        )
        print(f"{len(rows)} profile(s) made for someone and not yet taken over (as of {now:%Y-%m-%d}).")
        noticed = erased = 0
        for r in rows:
            age = now - r["created_at"]
            due_notice = age >= REMOVE_AFTER - NOTICE_BEFORE and r["removal_notice_at"] is None
            due_erase = (
                age >= REMOVE_AFTER
                and r["removal_notice_at"] is not None
                and now - r["removal_notice_at"] >= MIN_NOTICE
            )
            if due_notice:
                print(f"  notice  {r['name']} — made {age.days} days ago; tell the maker it goes in 7 days")
                if args.apply:
                    await conn.execute(
                        "SELECT mangaly_notification.notify(CAST($1 AS uuid[]), NULL, "
                        "'profile_removal_notice', CAST($2 AS jsonb), '/me')",
                        [str(r["created_by_account_id"])],
                        json.dumps({"name": r["name"].split(" ")[0], "days": 7}),
                    )
                    await conn.execute(
                        "UPDATE mangaly_profile.profile SET removal_notice_at = now() WHERE account_id = $1",
                        r["account_id"],
                    )
                noticed += 1
            elif due_erase:
                print(f"  erase   {r['name']} — made {age.days} days ago, notice given; never taken over")
                if args.apply:
                    async with conn.transaction():
                        await conn.fetchval(
                            "SELECT mangaly_profile.erase_made_for_profile($1)", r["account_id"]
                        )
                    async with httpx.AsyncClient(
                        base_url=settings.platform_identity_url,
                        headers={
                            "X-ForKhatri-Service": settings.platform_service_name,
                            "X-ForKhatri-Service-Key": settings.platform_service_key,
                        },
                        timeout=10,
                    ) as client:
                        answer = await client.post(
                            f"/internal/v1/members/{r['account_id']}/retire-provisioned"
                        )
                        print(f"          platform member removed: {answer.json().get('removed')}")
                erased += 1
            else:
                print(f"  keep    {r['name']} — made {age.days} days ago")
        print(f"{'Did' if args.apply else 'Would'}: {noticed} notice(s), {erased} removal(s).")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
