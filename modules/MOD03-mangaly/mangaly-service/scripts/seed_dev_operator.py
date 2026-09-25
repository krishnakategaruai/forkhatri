"""Seed the one development moderator (DEC-V1-028).

Grants the `moderator` role to exactly one account so the moderation console
(`/ops`) has someone who can open it in development:

  1. the ForKhatri persona `milavn-moderator` (member id
     99999999-9999-9999-9999-999999999999) IF it already has a Mangaly account;
  2. otherwise the account behind +919800000001 (`asha`).

Also grants the `safety_abuse` case-type scope (TR076: a role names its case
type explicitly; there is no "all cases" scope). Idempotent. Connects as
`mangaly_owner` because these are administrative rows, never application
writes.

Run: python -m scripts.seed_dev_operator
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import asyncpg

DB_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
MILAVN_MODERATOR = UUID("99999999-9999-9999-9999-999999999999")
FALLBACK_PHONE = "+919800000001"


async def main() -> None:
    conn = await asyncpg.connect(DB_DSN)
    try:
        account_id = await conn.fetchval(
            "SELECT id FROM mangaly_identity.account WHERE id = $1", MILAVN_MODERATOR
        )
        chosen = "milavn-moderator"
        if account_id is None:
            account_id = await conn.fetchval(
                "SELECT id FROM mangaly_identity.account WHERE phone_identifier = $1", FALLBACK_PHONE
            )
            chosen = FALLBACK_PHONE
        if account_id is None:
            raise SystemExit("neither persona has a Mangaly account yet; sign in once first")
        await conn.execute(
            """
            INSERT INTO mangaly_operations.operator (account_id, roles, granted_by)
            VALUES ($1, ARRAY['moderator']::text[], NULL)
            ON CONFLICT (account_id) DO UPDATE
               SET roles = (SELECT ARRAY(SELECT DISTINCT unnest(mangaly_operations.operator.roles || ARRAY['moderator']::text[])))
            """,
            account_id,
        )
        await conn.execute(
            """
            INSERT INTO mangaly_operations.operator_role_scope (operator_account_id, case_type_scope)
            VALUES ($1, 'safety_abuse')
            ON CONFLICT (operator_account_id, case_type_scope) DO NOTHING
            """,
            account_id,
        )
        name = await conn.fetchval(
            "SELECT display_name FROM mangaly_identity.account WHERE id = $1", account_id
        )
        print(f"moderator: {chosen} -> {account_id} ({name})")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
