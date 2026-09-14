"""Seed known-credential accounts for local development.

These exist so the app can actually be logged into and looked at while it is
being built. They are DEVELOPMENT ONLY:
  * the credentials are printed in plain text below and committed to the repo;
  * the script refuses to run against anything but a local host.

Run:  python -m scripts.seed_test_accounts

Accounts are created ACTIVE with `identifier_verified_at` set, deliberately
skipping FR095's OTP step, which does not exist yet. That is a seeding
shortcut, not a change to the signup rules — `POST /auth/signup` still creates
accounts as `pending_verification`, exactly as TR092 requires.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text

from app.components.identity_bridge.credentials import get_credential_hasher
from app.config.settings import get_settings
from app.db.engine import create_engine, create_session_factory

TEST_ACCOUNTS: list[dict[str, str]] = [
    {
        "label": "candidate",
        "identifier": "+919800000001",
        "kind": "phone",
        "credential": "MangalyTest#2026",
    },
    {
        "label": "family member",
        "identifier": "+919800000002",
        "kind": "phone",
        "credential": "MangalyTest#2026",
    },
    {
        "label": "admin / operator",
        "identifier": "admin@mangaly.test",
        "kind": "email",
        "credential": "MangalyAdmin#2026",
    },
]


async def main() -> None:
    settings = get_settings()

    if settings.db_host not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit(
            f"refusing to seed test credentials against a non-local host: {settings.db_host}"
        )

    hasher = get_credential_hasher()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session, session.begin():
            for spec in TEST_ACCOUNTS:
                identifier = spec["identifier"].lower()
                column = (
                    "email_identifier" if spec["kind"] == "email" else "phone_identifier"
                )

                existing = await session.execute(
                    text(
                        "SELECT id FROM mangaly_identity.lookup_by_identifier(:ident)"
                    ).bindparams(ident=identifier)
                )
                row = existing.first()
                if row is not None:
                    # `07a-db-implementation/seeds.sql` creates two of these
                    # accounts with a literal 'CHANGE_ME_bcrypt_hash' placeholder
                    # and no verified timestamp, so they cannot be logged into.
                    # Overwrite rather than skip — a row that exists but cannot
                    # authenticate is worse than no row, because it looks seeded.
                    #
                    # [TR017] The UPDATE must run WITH an account context bound.
                    # `account_self_only` restricts every row to
                    # `id = mangaly.account_id`, so without this SET LOCAL the
                    # statement matches zero rows and reports success — the exact
                    # silent no-op RLS is known for. Setting the context to the
                    # row we just looked up keeps this working within RLS rather
                    # than bypassing it by connecting as the owner.
                    await session.execute(
                        text("SELECT set_config('mangaly.account_id', :aid, true)").bindparams(
                            aid=str(row[0])
                        )
                    )
                    result = await session.execute(
                        text(
                            """
                            UPDATE mangaly_identity.account
                               SET credential_hash = :hash,
                                   status = 'active',
                                   identifier_verified_at = COALESCE(identifier_verified_at, :now),
                                   updated_at = :now
                             WHERE id = :id
                            """
                        ).bindparams(
                            id=row[0],
                            hash=hasher.hash(spec["credential"]),
                            now=datetime.now(UTC),
                        )
                    )
                    if result.rowcount != 1:
                        # Never report a reset that did not happen.
                        raise SystemExit(
                            f"failed to reset {identifier}: UPDATE affected "
                            f"{result.rowcount} rows (expected 1) — check RLS context"
                        )
                    print(f"  ~ {spec['label']:<18} {identifier}  (credential reset)")
                    continue

                await session.execute(
                    text(
                        f"""
                        INSERT INTO mangaly_identity.account
                            (id, {column}, credential_hash, status, identifier_verified_at)
                        VALUES (:id, :ident, :hash, 'active', :now)
                        """
                    ).bindparams(
                        id=uuid4(),
                        ident=identifier,
                        hash=hasher.hash(spec["credential"]),
                        now=datetime.now(UTC),
                    )
                )
                print(f"  + {spec['label']:<18} {identifier}")
    finally:
        await engine.dispose()

    print("\nSeeded. Log in with:")
    for spec in TEST_ACCOUNTS:
        print(f"  {spec['identifier']:<24} {spec['credential']}   ({spec['label']})")


if __name__ == "__main__":
    asyncio.run(main())
