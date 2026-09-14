"""One-off maintenance: (re)build `discovery_profile_index` for every
existing profile.

Needed because `seed_dev_accounts.py` inserts `profile`/`profile_attribute`
rows directly via SQL (bypassing `profile.interface`, which is the only
normal call path that triggers `discovery.interface.refresh_index()`) — so
seeded accounts never got an index row through the ordinary application
flow. A real user's profile is always indexed automatically the moment they
save it or edit a category; this script exists only to catch up rows that
were seeded directly, and to give an operator a way to rebuild the index
from scratch if it were ever suspected of drifting.

Run: python -m scripts.reindex_discovery
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncpg  # noqa: E402

from app.components.discovery import interface as discovery  # noqa: E402
from app.db.engine import create_engine, create_session_factory  # noqa: E402
from app.db.session import set_account_context  # noqa: E402

# Owner connection ONLY to enumerate every profile's account id — the normal
# `mangaly_app` role is correctly RLS-constrained and returns zero rows for
# an unscoped SELECT with no account context bound yet (that constraint is
# exactly why this script exists: bypassing it here is an explicit, narrow,
# one-off maintenance exception, not a pattern any application code path
# uses). The actual per-profile refresh below still goes through the normal
# `mangaly_app`-rooted session with the account context correctly bound.
_OWNER_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"


async def _list_account_ids() -> list[UUID]:
    conn = await asyncpg.connect(_OWNER_DSN)
    try:
        rows = await conn.fetch("SELECT account_id FROM mangaly_profile.profile")
        return [row["account_id"] for row in rows]
    finally:
        await conn.close()


async def main() -> int:
    engine = create_engine()
    session_factory = create_session_factory(engine)

    account_ids = await _list_account_ids()

    print(f"\nReindexing {len(account_ids)} profile(s) into mangaly_discovery...\n")
    for account_id in account_ids:
        async with session_factory() as session, session.begin():
            # Each profile's own attribute/category reads are self-scoped
            # (RLS), so the account context must be bound to THAT account,
            # not left unset, before calling into `profile.interface`.
            await set_account_context(session, account_id)
            await discovery.refresh_index(session, account_id=account_id)
        print(f"  indexed {account_id}")

    print("\nDone.\n")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
