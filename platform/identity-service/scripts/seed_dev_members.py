r"""Development-only members with a known password. Refuses to run in production.

Creates or refreshes:
- Krishna Kategaru (+919999900001, persona `krishna`): the product owner's own
  development account, no module data. Never used by automated tests.
- New Member (+919999900002, persona `new-member`): a fresh member with no module
  data, safe for automated tests. Modules create their own rows on first entry,
  so "fresh" holds only until a test enters a module.
- Lakshmi Reddy (+919999900003): Ananya Reddy's mother, a family member (not a
  candidate) for Mangaly Home Circle tests. Joins Ananya's circle through the app.
And sets the development password on member 11111111-1111-1111-1111-111111111111
(imported; Asha Reddy in Milavn, "Seed Candidate One" in Mangaly).

Development personas (app/dev_tools/personas.py; switch with the entrance's
"Act as" row or scripts/dev_session.py, no password needed): krishna, asha,
new-member, mangaly-family (2222...), milavn-moderator (9999...). This script stays
self-contained (no `app` import) because the deployment migrate image runs it alone.
Module data is never created here.

Run after import_module_identities.py:
    .venv\Scripts\python scripts\seed_dev_members.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from uuid import UUID

import asyncpg
from argon2 import PasswordHasher

DEV_PASSWORD = "ForKhatri-dev-2026"
DEFAULT_IDENTITY_OWNER_DSN = (
    "postgresql://identity_owner:identity_owner_dev_password@localhost:5433/forkhatri_identity"
)
NEW_MEMBERS = [
    {
        "id": UUID("a0000000-0000-4000-8000-000000000001"),
        "name": "Krishna Kategaru",
        "phone": "+919999900001",
        "email": "krishna.dev@forkhatri.test",
        "language": "en",
    },
    {
        "id": UUID("a0000000-0000-4000-8000-000000000002"),
        "name": "New Member",
        "phone": "+919999900002",
        "email": "new.member@forkhatri.test",
        "language": "en",
    },
    {
        # Ananya Reddy's mother: a real signed-up family member, so Mangaly's Home
        # Circle and family-contact flows are tested with an actual parent.
        "id": UUID("a0000000-0000-4000-8000-000000000003"),
        "name": "Lakshmi Reddy",
        "phone": "+919999900003",
        "email": "lakshmi.reddy@forkhatri.test",
        "language": "te",
    },
]
EXISTING_MEMBERS_WITH_DEV_PASSWORD = [UUID("11111111-1111-1111-1111-111111111111")]


async def main() -> int:
    if os.environ.get("FORKHATRI_ENVIRONMENT", "development") == "production":
        print("Refusing to seed development members into production.")
        return 2
    password_hash = PasswordHasher().hash(DEV_PASSWORD)
    conn = await asyncpg.connect(os.environ.get("IDENTITY_OWNER_DSN", DEFAULT_IDENTITY_OWNER_DSN))
    try:
        async with conn.transaction():
            for member in NEW_MEMBERS:
                await conn.execute(
                    "INSERT INTO identity.member (id, display_name, phone_e164, email, preferred_language) "
                    "VALUES ($1, $2, $3, $4, $5) "
                    "ON CONFLICT (id) DO UPDATE SET display_name = EXCLUDED.display_name, updated_at = now()",
                    member["id"],
                    member["name"],
                    member["phone"],
                    member["email"],
                    member["language"],
                )
            for member_id in [m["id"] for m in NEW_MEMBERS] + EXISTING_MEMBERS_WITH_DEV_PASSWORD:
                exists = await conn.fetchval("SELECT 1 FROM identity.member WHERE id = $1", member_id)
                if not exists:
                    print(f"skipped {member_id}: not imported yet (run import_module_identities.py first)")
                    continue
                await conn.execute(
                    "INSERT INTO identity.password_credential (member_id, password_hash) VALUES ($1, $2) "
                    "ON CONFLICT (member_id) DO UPDATE SET password_hash = EXCLUDED.password_hash, updated_at = now()",
                    member_id,
                    password_hash,
                )
                row = await conn.fetchrow(
                    "SELECT display_name, phone_e164 FROM identity.member WHERE id = $1", member_id
                )
                print(f"development sign-in: {row['phone_e164']} / {DEV_PASSWORD}  ({row['display_name']}, {member_id})")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
