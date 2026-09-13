#!/usr/bin/env bash
# =============================================================================
# Milavn (MOD02) — local/dev database setup.
# One-command execution: ./init.sh
# Requires: psql on PATH, a running Postgres instance reachable with the
# credentials in .env (copy .env.example to .env first and fill in real
# local values — the CHANGE_ME placeholders are not usable as-is).
#
# Unlike Mangaly's own init.sh (isolated database), this script targets the
# Core Platform monolith's SHARED database (DB_NAME defaults to
# "forkhatridb", the same one Vyapar/Dashboard use) and only ever touches
# milavn_* schemas inside it — it never creates or drops that shared
# database itself, since other modules' data lives there too.
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -f .env ]; then
  echo "No .env found — copying .env.example to .env. Edit DB_* values before re-running if the defaults don't match your local Postgres." >&2
  cp .env.example .env
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

PSQL_ADMIN="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_ADMIN_USER:-postgres}"
PSQL_OWNER="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_OWNER_USER} -d ${DB_NAME}"

echo "== Step 1/5: ensure the shared Core Platform database exists (does NOT create a Milavn-only database) =="
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1 \
  || PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "CREATE DATABASE ${DB_NAME};"

echo "== Step 2/5: provision roles as admin (role creation is cluster-wide, admin-only —"
echo "   migrations never create roles themselves; see schema.sql section 0's comment) =="
# milavn_owner needs LOGIN because migrations run BY CONNECTING AS this role
# directly (see PSQL_OWNER below). It owns every milavn_* object; the
# running application never connects as this role (that's milavn_app,
# below) — this is what MODULE-ARCHITECTURE-STANDARD §4's first named RLS
# failure mode requires (a non-owning application role).
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -tc "SELECT 1 FROM pg_roles WHERE rolname = '${DB_OWNER_USER}'" | grep -q 1 \
  && PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "ALTER ROLE ${DB_OWNER_USER} WITH LOGIN PASSWORD '${DB_OWNER_PASSWORD}' CREATEDB;" \
  || PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "CREATE ROLE ${DB_OWNER_USER} LOGIN PASSWORD '${DB_OWNER_PASSWORD}' CREATEDB;"
# milavn_app is the NON-OWNING runtime role Milavn's FastAPI process actually
# connects as — RLS silently no-ops for a table's owner, so this role is
# created here (LOGIN, no ownership) and never granted ownership of anything
# migrations/001-initial.sql creates.
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -tc "SELECT 1 FROM pg_roles WHERE rolname = '${DB_APP_USER}'" | grep -q 1 \
  && PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "ALTER ROLE ${DB_APP_USER} WITH LOGIN PASSWORD '${DB_APP_PASSWORD}';" \
  || PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "CREATE ROLE ${DB_APP_USER} LOGIN PASSWORD '${DB_APP_PASSWORD}';"
# milavn_owner must be able to connect to the shared database and create
# schemas in it without needing to own the whole database (other modules'
# schemas already live there).
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "GRANT CONNECT, CREATE ON DATABASE ${DB_NAME} TO ${DB_OWNER_USER};"
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_APP_USER};"

echo "== Step 3/5: run migrations in order, as milavn_owner (idempotent — safe to re-run) =="
for f in migrations/*.sql; do
  echo "   applying $f"
  PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -v ON_ERROR_STOP=1 -f "$f"
done

if [ "${SEED_DB:-false}" = "true" ]; then
  echo "== Step 4/5: load seed data (SEED_DB=true) =="
  PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -v ON_ERROR_STOP=1 -f "${SEED_FILE_PATH:-./seeds.sql}"
else
  echo "== Step 4/5: skipping seed data (SEED_DB=false) =="
fi

echo "== Step 5/5: verify =="
echo "-- schemas + table counts --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT schemaname, count(*) AS tables
  FROM pg_tables
  WHERE schemaname LIKE 'milavn_%'
  GROUP BY schemaname
  ORDER BY schemaname;
"
echo "-- RLS enabled per table (rowsecurity = t expected on every privacy-sensitive table) --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT schemaname, tablename, rowsecurity
  FROM pg_tables
  WHERE schemaname LIKE 'milavn_%'
  ORDER BY schemaname, tablename;
"
echo "-- non-owning runtime role check (milavn_app must own ZERO tables; milavn_owner owns all milavn_* tables) --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT tableowner, count(*) FROM pg_tables WHERE schemaname LIKE 'milavn_%' GROUP BY tableowner;
"
echo "-- cross-cutting infra tables present (idempotency, rate-limit, per-component outbox) --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT schemaname||'.'||tablename FROM pg_tables
  WHERE schemaname LIKE 'milavn_%' AND (tablename IN ('idempotency_key','rate_limit_counter') OR tablename = 'outbox_event')
  ORDER BY 1;
"

echo "Done. Milavn's schemas are ready in ${DB_NAME} at ${DB_HOST}:${DB_PORT}."
echo
echo "Rollback / start over (drops ONLY Milavn's own schemas — never the shared database itself):"
echo "  PGPASSWORD=\$DB_OWNER_PASSWORD psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_OWNER_USER} -d ${DB_NAME} -c \"DROP SCHEMA IF EXISTS milavn_profile, milavn_discovery, milavn_activity, milavn_circle, milavn_trust, milavn_locationprivacy, milavn_connect, milavn_publicpage, milavn_notification, milavn_safety, milavn_platform CASCADE;\""
echo "  then re-run ./init.sh"
