"""ForKhatri database provisioning and migrations (deployment kit, 2026-09-14).

Works against any PostgreSQL 18 reachable by URL: the Postgres container on the
VM, a local cluster, or a managed server (TLS via `?sslmode=require`). Nothing
here assumes Docker. Use a direct (unpooled) connection: role and database
creation and multi-statement migrations are not safe through a transaction pooler.

What it does, every run (idempotent):

1. Creates or updates the six login roles with the passwords from the
   environment (owner + non-owning app role per service,
   MODULE-ARCHITECTURE-STANDARD §4). Updating keeps the database in step with
   `deploy/secrets/.env.production`.
2. Creates the three databases (ADR-002 isolation): `forkhatri_identity`
   (owner identity_owner), `mangaly` (owner mangaly_owner) and the shared Core
   Platform database `forkhatridb` (owned by the admin role; milavn_owner may
   create its own schemas). CONNECT is revoked from PUBLIC, so a service role
   can only connect to its own database.
3. Applies every not-yet-applied `*.sql` file, in file-name order, as that
   database's owner role, and records it in `forkhatri_deploy.applied_migration`
   with its SHA-256. A recorded file whose content changed is reported, never re-run.
4. Verifies that no runtime role owns a table (RLS would silently not apply).

Development data is loaded only with both `--seed-dev` and
`--i-understand-this-loads-development-data`. It is never part of a normal run.

Environment:
    DATABASE_ADMIN_URL          postgresql://postgres:<pw>@postgres:5432/postgres[?sslmode=require]
    IDENTITY_OWNER_PASSWORD, IDENTITY_APP_PASSWORD
    MANGALY_OWNER_PASSWORD,  MANGALY_APP_PASSWORD
    MILAVN_OWNER_PASSWORD,   MILAVN_APP_PASSWORD
    FORKHATRI_REPO_ROOT         optional; defaults to two folders above this file

Usage:
    python deploy/migrate/migrate.py                 # provision + migrate
    python deploy/migrate/migrate.py --status        # show applied / pending, change nothing
    python deploy/migrate/migrate.py --baseline      # adopt an existing database: record files as applied without running them
    python deploy/migrate/migrate.py --seed-dev --i-understand-this-loads-development-data

Secrets are never printed.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import asyncpg

REPO_ROOT = Path(os.environ.get("FORKHATRI_REPO_ROOT") or Path(__file__).resolve().parents[2])
LEDGER_SCHEMA = "forkhatri_deploy"
REQUIRED_EXTENSIONS = ("pgcrypto", "pg_trgm")


@dataclass(frozen=True)
class Target:
    key: str
    database: str
    owner: str
    app: str
    owns_database: bool
    migrations: Path
    schema_like: tuple[str, ...]
    dev_seeds: tuple[Path, ...] = ()

    def password(self, role: str) -> str:
        name = f"{role.upper()}_PASSWORD"
        value = os.environ.get(name, "")
        if len(value) < 16 or "CHANGE_ME" in value:
            raise SystemExit(f"{name} is missing or too short (run deploy/scripts/generate-secrets.sh).")
        return value


TARGETS = (
    Target(
        key="identity",
        database=os.environ.get("IDENTITY_DB_NAME", "forkhatri_identity"),
        owner="identity_owner",
        app="identity_app",
        owns_database=True,
        migrations=REPO_ROOT / "platform/identity-service/db/migrations",
        schema_like=("identity", "registry", "platform"),
    ),
    Target(
        key="mangaly",
        database=os.environ.get("MANGALY_DB_NAME", "mangaly"),
        owner="mangaly_owner",
        app="mangaly_app",
        owns_database=True,
        migrations=REPO_ROOT / "modules/MOD03-mangaly/07a-db-implementation/migrations",
        schema_like=("mangaly%",),
        # The module's seeds.sql predates migration 005; the kit ships a compatible copy.
        dev_seeds=(REPO_ROOT / "deploy/migrate/seeds/mangaly-dev.sql",),
    ),
    Target(
        key="milavn",
        database=os.environ.get("MILAVN_DB_NAME", "forkhatridb"),
        owner="milavn_owner",
        app="milavn_app",
        owns_database=False,
        migrations=REPO_ROOT / "modules/MOD02-milavn/07a-db-implementation/migrations",
        schema_like=("milavn%",),
        dev_seeds=(
            REPO_ROOT / "modules/MOD02-milavn/07a-db-implementation/seeds.sql",
            REPO_ROOT / "modules/MOD02-milavn/07a-db-implementation/seeds-dev.sql",
        ),
    ),
)


def log(message: str) -> None:
    print(message, flush=True)


def admin_url() -> str:
    url = os.environ.get("DATABASE_ADMIN_URL", "")
    if not url.startswith(("postgres://", "postgresql://")):
        raise SystemExit("DATABASE_ADMIN_URL must be a postgresql:// URL.")
    return url


def url_for(base: str, *, database: str, user: str | None = None, password: str | None = None) -> str:
    """Same host, port and query (sslmode…) as the admin URL; other database and credentials."""
    parts = urlsplit(base)
    netloc = parts.netloc
    if user is not None:
        host = netloc.rsplit("@", 1)[-1]
        netloc = f"{quote(user, safe='')}:{quote(password or '', safe='')}@{host}"
    return urlunsplit((parts.scheme, netloc, "/" + quote(database, safe=""), parts.query, ""))


def redacted(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.rsplit("@", 1)[-1]
    return f"{host}{parts.path}"


async def connect(url: str, attempts: int = 30) -> asyncpg.Connection:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return await asyncpg.connect(url, timeout=10, statement_cache_size=0)
        except (OSError, asyncpg.CannotConnectNowError, asyncpg.ConnectionDoesNotExistError, TimeoutError) as exc:
            last = exc
            if attempt == 0:
                log(f"waiting for {redacted(url)} …")
            await asyncio.sleep(2)
    raise SystemExit(f"could not connect to {redacted(url)}: {type(last).__name__}")


async def ensure_role(conn: asyncpg.Connection, role: str, password: str) -> None:
    exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = $1", role)
    verb = "ALTER" if exists else "CREATE"
    statement = await conn.fetchval(
        "SELECT format('%s ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', $1::text, $2::text, $3::text)",
        verb,
        role,
        password,
    )
    await conn.execute(statement)
    log(f"role {role}: {'updated' if exists else 'created'}")


async def ensure_database(conn: asyncpg.Connection, target: Target) -> None:
    ident = await conn.fetchval("SELECT quote_ident($1)", target.database)
    owner = await conn.fetchval("SELECT quote_ident($1)", target.owner)
    app = await conn.fetchval("SELECT quote_ident($1)", target.app)
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target.database)
    if not exists:
        if target.owns_database:
            await conn.execute(f"CREATE DATABASE {ident} OWNER {owner} ENCODING 'UTF8' TEMPLATE template0")
        else:
            await conn.execute(f"CREATE DATABASE {ident} ENCODING 'UTF8' TEMPLATE template0")
        log(f"database {target.database}: created")
    else:
        log(f"database {target.database}: exists")
    if target.owns_database:
        await conn.execute(f"ALTER DATABASE {ident} OWNER TO {owner}")
        await conn.execute(f"REVOKE ALL ON DATABASE {ident} FROM PUBLIC")
        await conn.execute(f"GRANT CONNECT ON DATABASE {ident} TO {owner}, {app}")
    else:
        # Shared Core Platform database: Milavn owns only its own schemas in it.
        await conn.execute(f"REVOKE ALL ON DATABASE {ident} FROM PUBLIC")
        await conn.execute(f"GRANT CONNECT, CREATE ON DATABASE {ident} TO {owner}")
        await conn.execute(f"GRANT CONNECT ON DATABASE {ident} TO {app}")


async def prepare_database(url: str, target: Target) -> None:
    """Admin-side work inside the database: trusted extensions and the migration ledger."""
    conn = await connect(url)
    try:
        for extension in REQUIRED_EXTENSIONS if target.key != "identity" else ():
            await conn.execute(f"CREATE EXTENSION IF NOT EXISTS {extension}")
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {LEDGER_SCHEMA}")
        await conn.execute(f"REVOKE ALL ON SCHEMA {LEDGER_SCHEMA} FROM PUBLIC")
        await conn.execute(
            f"CREATE TABLE IF NOT EXISTS {LEDGER_SCHEMA}.applied_migration ("
            " filename text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())"
        )
    finally:
        await conn.close()


def sql_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise SystemExit(f"migrations folder not found: {folder}")
    return sorted(folder.glob("*.sql"), key=lambda p: p.name)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def apply_files(
    admin_db_url: str, owner_url: str, target: Target, files: list[tuple[str, Path]], *, baseline: bool, status: bool
) -> int:
    admin = await connect(admin_db_url)
    applied_now = 0
    try:
        recorded = {r["filename"]: r["sha256"] for r in await admin.fetch(f"SELECT filename, sha256 FROM {LEDGER_SCHEMA}.applied_migration")}
        owner: asyncpg.Connection | None = None
        try:
            for ledger_name, path in files:
                sha = digest(path)
                if ledger_name in recorded:
                    if recorded[ledger_name] != sha:
                        log(f"  WARNING {target.database}: {ledger_name} changed after it was applied; not re-run")
                    continue
                if status:
                    log(f"  pending {target.database}: {ledger_name}")
                    continue
                if not baseline:
                    if owner is None:
                        owner = await connect(owner_url)
                    log(f"  applying {target.database}: {ledger_name}")
                    await owner.execute(path.read_text(encoding="utf-8"))
                await admin.execute(
                    f"INSERT INTO {LEDGER_SCHEMA}.applied_migration (filename, sha256) VALUES ($1, $2)", ledger_name, sha
                )
                applied_now += 1
        finally:
            if owner is not None:
                await owner.close()
    finally:
        await admin.close()
    return applied_now


async def verify_non_owning(admin_db_url: str, target: Target) -> None:
    conn = await connect(admin_db_url)
    try:
        patterns = list(target.schema_like)
        rows = await conn.fetch(
            "SELECT tableowner, count(*) AS n FROM pg_tables WHERE schemaname LIKE ANY($1::text[]) GROUP BY tableowner",
            patterns,
        )
        by_owner = {r["tableowner"]: r["n"] for r in rows}
        owned = by_owner.get(target.app, 0)
        tables = sum(by_owner.values())
    finally:
        await conn.close()
    if owned:
        raise SystemExit(f"{target.app} owns {owned} table(s) in {target.database}; RLS would be bypassed.")
    log(f"verified {target.database}: {tables} tables, runtime role {target.app} owns none")


def run_identity_seed(base: str) -> None:
    identity = next(t for t in TARGETS if t.key == "identity")
    mangaly = next(t for t in TARGETS if t.key == "mangaly")
    env = {
        **os.environ,
        "FORKHATRI_ENVIRONMENT": "development",
        "IDENTITY_OWNER_DSN": url_for(base, database=identity.database, user=identity.owner, password=identity.password(identity.owner)),
        "MANGALY_SOURCE_DSN": url_for(base, database=mangaly.database, user=mangaly.owner, password=mangaly.password(mangaly.owner)),
        "MILAVN_DEV_IDENTITIES": str(REPO_ROOT / "modules/MOD02-milavn/milavn-service/app/config/dev_identities.json"),
    }
    for script in ("import_module_identities.py", "seed_dev_members.py"):
        log(f"seed: platform/identity-service/scripts/{script}")
        subprocess.run([sys.executable, str(REPO_ROOT / "platform/identity-service/scripts" / script)], env=env, check=True)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--status", action="store_true", help="report pending files; change nothing")
    parser.add_argument("--baseline", action="store_true", help="record migration files as applied without running them")
    parser.add_argument("--seed-dev", action="store_true", help="load development seed data and development members")
    parser.add_argument("--i-understand-this-loads-development-data", dest="confirm_seed", action="store_true")
    args = parser.parse_args()
    if args.seed_dev and not args.confirm_seed:
        raise SystemExit("--seed-dev loads development accounts with a published password. Add --i-understand-this-loads-development-data.")

    base = admin_url()
    admin = await connect(base)
    try:
        log(f"connected to {redacted(base)} as admin (server {admin.get_server_version().major})")
        if not args.status:
            for target in TARGETS:
                await ensure_role(admin, target.owner, target.password(target.owner))
                await ensure_role(admin, target.app, target.password(target.app))
            for target in TARGETS:
                await ensure_database(admin, target)
    finally:
        await admin.close()

    total = 0
    for target in TARGETS:
        admin_db_url = url_for(base, database=target.database)
        owner_url = url_for(base, database=target.database, user=target.owner, password=target.password(target.owner))
        if not args.status:
            await prepare_database(admin_db_url, target)
        files = [(p.name, p) for p in sql_files(target.migrations)]
        total += await apply_files(admin_db_url, owner_url, target, files, baseline=args.baseline, status=args.status)
        if args.seed_dev and target.dev_seeds:
            seeds = [(f"seed-dev:{p.name}", p) for p in target.dev_seeds]
            total += await apply_files(admin_db_url, owner_url, target, seeds, baseline=False, status=args.status)
        if not args.status:
            await verify_non_owning(admin_db_url, target)

    if args.seed_dev and not args.status:
        run_identity_seed(base)
    log(f"done: {total} file(s) {'pending' if args.status else ('recorded' if args.baseline else 'applied')}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
