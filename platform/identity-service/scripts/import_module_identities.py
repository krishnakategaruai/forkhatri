"""Import existing module identities into the platform member table (07-tech-reqs.md TR23).

- Every `active` Mangaly account becomes a member with the same id, phone, email
  and Argon2id password hash (the member keeps their password).
- `pending_verification` Mangaly accounts are not imported: the identifier was
  never proven.
- Milavn development identities become members with the same ids and names.
- Where both sources hold the same id, the result is one member: identifiers
  from Mangaly, display name from Milavn.

Idempotent: existing members and credentials are left untouched.

    set MANGALY_SOURCE_DSN=postgresql://<user>:<password>@localhost:5433/mangaly
    .venv\\Scripts\\python scripts\\import_module_identities.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import asyncpg

SERVICE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = SERVICE_DIR.parents[1]
DEFAULT_IDENTITY_OWNER_DSN = (
    "postgresql://identity_owner:identity_owner_dev_password@localhost:5433/forkhatri_identity"
)
DEFAULT_MILAVN_IDENTITIES = REPO_DIR / "modules/MOD02-milavn/milavn-service/app/config/dev_identities.json"
LANGUAGES = {"en", "hi", "te"}


async def read_mangaly(dsn: str) -> dict[str, dict[str, Any]]:
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            "SELECT a.id, a.phone_identifier, a.email_identifier, a.credential_hash, "
            "       p.name, p.language_preference "
            "FROM mangaly_identity.account a "
            "LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id "
            "WHERE a.status = 'active' ORDER BY a.created_at"
        )
    finally:
        await conn.close()
    return {
        str(r["id"]): {
            "phone": r["phone_identifier"],
            "email": r["email_identifier"].lower() if r["email_identifier"] else None,
            "password_hash": r["credential_hash"],
            "name": r["name"],
            "language": r["language_preference"] if r["language_preference"] in LANGUAGES else "en",
            "level": 1,
            "source": "mangaly",
        }
        for r in rows
    }


def read_milavn(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        m["member_id"]: {"name": m["display_name"], "handle": m["handle"], "level": int(m.get("identity_level", 1))}
        for m in data["members"]
    }


def merge(mangaly: dict[str, dict[str, Any]], milavn: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged = {member_id: dict(record) for member_id, record in mangaly.items()}
    for member_id, record in milavn.items():
        target = merged.get(member_id)
        if target is None:
            merged[member_id] = {
                "phone": None,
                "email": f"{record['handle']}@milavn.dev.forkhatri.test",
                "password_hash": None,
                "name": record["name"],
                "language": "en",
                "level": record["level"],
                "source": "milavn",
            }
            continue
        target["name"] = record["name"]
        target["level"] = max(target["level"], record["level"])
        target["source"] = "mangaly+milavn"
    return merged


async def write_members(dsn: str, merged: dict[str, dict[str, Any]]) -> None:
    conn = await asyncpg.connect(dsn)
    created, existing, credentials = 0, 0, 0
    conflicts: list[str] = []
    try:
        for member_id, record in merged.items():
            name = (record["name"] or "ForKhatri member").strip()[:80]
            try:
                async with conn.transaction():
                    inserted = await conn.fetchval(
                        "INSERT INTO identity.member (id, display_name, phone_e164, email, preferred_language, identity_level) "
                        "VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO NOTHING RETURNING id",
                        UUID(member_id),
                        name,
                        record["phone"],
                        record["email"],
                        record["language"],
                        record["level"],
                    )
                    if inserted is None:
                        existing += 1
                    else:
                        created += 1
                    password_hash = record["password_hash"]
                    if password_hash and password_hash.startswith("$argon2id$"):
                        status = await conn.execute(
                            "INSERT INTO identity.password_credential (member_id, password_hash) VALUES ($1, $2) "
                            "ON CONFLICT (member_id) DO NOTHING",
                            UUID(member_id),
                            password_hash,
                        )
                        if status.endswith(" 1"):
                            credentials += 1
            except (asyncpg.UniqueViolationError, asyncpg.CheckViolationError) as exc:
                conflicts.append(f"{member_id} ({record['source']}): {str(exc).splitlines()[0]}")
    finally:
        await conn.close()

    print(f"source records: {len(merged)}")
    print(f"members created: {created}; already present: {existing}; password credentials imported: {credentials}")
    print(f"conflicts needing a human decision: {len(conflicts)}")
    for line in conflicts:
        print(f"  - {line}")


async def main() -> int:
    mangaly_dsn = os.environ.get("MANGALY_SOURCE_DSN")
    if not mangaly_dsn:
        print("Set MANGALY_SOURCE_DSN to a role that can read mangaly_identity.account and mangaly_profile.profile.")
        return 2
    identity_dsn = os.environ.get("IDENTITY_OWNER_DSN", DEFAULT_IDENTITY_OWNER_DSN)
    milavn_path = Path(os.environ.get("MILAVN_DEV_IDENTITIES", str(DEFAULT_MILAVN_IDENTITIES)))

    mangaly = await read_mangaly(mangaly_dsn)
    milavn = read_milavn(milavn_path) if milavn_path.exists() else {}
    print(f"mangaly active accounts: {len(mangaly)}; milavn development identities: {len(milavn)}")
    await write_members(identity_dsn, merge(mangaly, milavn))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
