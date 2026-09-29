r"""Development-only Admin & Governance Console data. Refuses to run in production.

Appoints, through governance.role_assignment (migration 005):
- Krishna Kategaru (persona `krishna`): owner. For people only, never automated tests.
- Ramesh Khatri (persona `samaj-president`): national president, one-year term.
- Meena Khatri (persona `samaj-secretary`): national secretary, one-year term.
- Milavn Moderator (persona `milavn-moderator`): moderator for Milavn.
and creates a few samaj chapters (Telangana → Hyderabad, Warangal; Andhra Pradesh →
Visakhapatnam) with no office bearers, so appointing one is tested through the console.

Every appointment is written to the audit log as a seed action (actor empty), exactly
as a production bootstrap would be. Idempotent. Self-contained (no `app` import) so the
deployment migrate image can run it alone, after seed_dev_members.py:
    .venv\Scripts\python scripts\seed_dev_governance.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from uuid import UUID

import asyncpg

DEFAULT_IDENTITY_OWNER_DSN = "postgresql://identity_owner:identity_owner_dev_password@localhost:5433/forkhatri_identity"

OWNER = UUID("a0000000-0000-4000-8000-000000000001")
PRESIDENT = UUID("a0000000-0000-4000-8000-000000000011")
SECRETARY = UUID("a0000000-0000-4000-8000-000000000012")
MILAVN_MODERATOR = UUID("99999999-9999-9999-9999-999999999999")

APPOINTMENTS = [
    (OWNER, "owner", "platform", None, None, None),
    (PRESIDENT, "president", "platform", None, None, "365 days"),
    (SECRETARY, "secretary", "platform", None, "General Secretary", "365 days"),
    (MILAVN_MODERATOR, "moderator", "module", "milavn", None, None),
]
CHAPTERS = [
    ("telangana", "Telangana", "state", None),
    ("telangana-hyderabad", "Hyderabad", "city", "telangana"),
    ("telangana-warangal", "Warangal", "city", "telangana"),
    ("andhra-pradesh", "Andhra Pradesh", "state", None),
    ("andhra-pradesh-visakhapatnam", "Visakhapatnam", "city", "andhra-pradesh"),
]


async def main() -> int:
    if os.environ.get("FORKHATRI_ENVIRONMENT", "development") == "production":
        print("Refusing to seed development governance data into production.")
        return 2
    conn = await asyncpg.connect(os.environ.get("IDENTITY_OWNER_DSN", DEFAULT_IDENTITY_OWNER_DSN))
    try:
        if not await conn.fetchval("SELECT to_regclass('governance.role_assignment') IS NOT NULL"):
            print("skipped: migration 005-governance.sql not applied yet")
            return 0
        async with conn.transaction():
            for key, name, kind, parent in CHAPTERS:
                await conn.execute(
                    "INSERT INTO governance.chapter (key, name, kind, parent_key) VALUES ($1, $2, $3, $4) "
                    "ON CONFLICT (key) DO NOTHING",
                    key, name, kind, parent,
                )
            for member_id, role, scope_kind, scope_key, title, term in APPOINTMENTS:
                if not await conn.fetchval("SELECT 1 FROM identity.member WHERE id = $1", member_id):
                    print(f"skipped {role} for {member_id}: member not seeded yet")
                    continue
                exists = await conn.fetchval(
                    "SELECT 1 FROM governance.role_assignment WHERE member_id = $1 AND role = $2 "
                    "AND coalesce(scope_key, '') = coalesce($3, '') AND revoked_at IS NULL",
                    member_id, role, scope_key,
                )
                if exists:
                    continue
                assignment_id = await conn.fetchval(
                    "INSERT INTO governance.role_assignment (member_id, role, scope_kind, scope_key, title, ends_at, grant_note) "
                    "VALUES ($1, $2, $3, $4, $5, CASE WHEN $6::text IS NULL THEN NULL ELSE now() + $6::interval END, "
                    "'Development seed appointment.') RETURNING id",
                    member_id, role, scope_kind, scope_key, title, term,
                )
                await conn.execute(
                    "INSERT INTO governance.audit_event (action, target_member_id, module_key, note, details) "
                    "VALUES ('role.granted', $1, $2, 'Development seed appointment.', $3::jsonb)",
                    member_id, scope_key if scope_kind == "module" else None,
                    json.dumps({"assignment_id": str(assignment_id), "role": role, "scope_kind": scope_kind, "scope_key": scope_key, "seed": True}),
                )
                print(f"appointed {role} ({scope_kind}{':' + scope_key if scope_key else ''}) -> {member_id}")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
