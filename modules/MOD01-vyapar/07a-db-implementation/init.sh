#!/usr/bin/env bash
# =============================================================================
# Vyapar (MOD01) — local/dev database setup.
# One-command execution: ./init.sh
# Requires: psql on PATH, a running Postgres instance reachable with the
# credentials in .env (copy .env.example to .env first and fill in real
# local values — the CHANGE_ME placeholders are not usable as-is).
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

echo "== Step 1/5: create database (if it doesn't already exist) =="
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1 \
  || PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "CREATE DATABASE ${DB_NAME};"

echo "== Step 2/5: provision roles as admin (role creation is a cluster-wide,"
echo "   admin-only operation — migrations never create roles themselves) =="
# vyapar_owner needs LOGIN because migrations run BY CONNECTING AS this role
# directly (see PSQL_OWNER below) — "non-application-facing" means
# vyapar-service itself never connects as this role, not "cannot log in."
# RLS applies to vyapar_app because it owns none of the tables this role creates.
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -tc "SELECT 1 FROM pg_roles WHERE rolname = '${DB_OWNER_USER}'" | grep -q 1 \
  && PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "ALTER ROLE ${DB_OWNER_USER} WITH LOGIN PASSWORD '${DB_OWNER_PASSWORD}' CREATEDB;" \
  || PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "CREATE ROLE ${DB_OWNER_USER} LOGIN PASSWORD '${DB_OWNER_PASSWORD}' CREATEDB;"
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "ALTER DATABASE ${DB_NAME} OWNER TO ${DB_OWNER_USER};"
# [MODULE-ARCHITECTURE-STANDARD §4] vyapar_app is the NON-OWNING runtime role
# vyapar-service actually connects as — created here (LOGIN, no ownership)
# and never granted ownership of anything migrations/001-initial.sql creates.
PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -tc "SELECT 1 FROM pg_roles WHERE rolname = '${DB_APP_USER}'" | grep -q 1 \
  && PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "ALTER ROLE ${DB_APP_USER} WITH LOGIN PASSWORD '${DB_APP_PASSWORD}';" \
  || PGPASSWORD="${DB_ADMIN_PASSWORD:-}" ${PSQL_ADMIN} -c "CREATE ROLE ${DB_APP_USER} LOGIN PASSWORD '${DB_APP_PASSWORD}';"

echo "== Step 3/5: run migrations in order, as vyapar_owner (idempotent — safe to re-run) =="
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
  WHERE schemaname LIKE 'vyapar_%'
  GROUP BY schemaname
  ORDER BY schemaname;
"
echo "-- RLS enabled per table (rowsecurity = t expected on every business/identity table) --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT schemaname, tablename, rowsecurity
  FROM pg_tables
  WHERE schemaname LIKE 'vyapar_%'
  ORDER BY schemaname, tablename;
"
echo "-- non-owning runtime role check (vyapar_app must own ZERO tables; vyapar_owner owns all) --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT tableowner, count(*) FROM pg_tables WHERE schemaname LIKE 'vyapar_%' GROUP BY tableowner;
"
echo "-- cross-cutting infra tables present (idempotency, rate-limit, outbox x3) --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT schemaname||'.'||tablename FROM pg_tables
  WHERE tablename IN ('idempotency_key','rate_limit_counter') OR tablename = 'outbox_event'
  ORDER BY 1;
"
echo "-- seed row counts (spot check against 07a-er-model.md's stated minimums) --"
PGPASSWORD="${DB_OWNER_PASSWORD}" ${PSQL_OWNER} -c "
  SELECT 'members' AS t, count(*) FROM vyapar_identity.members
  UNION ALL SELECT 'listings', count(*) FROM vyapar_listings.listings
  UNION ALL SELECT 'opportunities', count(*) FROM vyapar_opportunities.opportunities
  UNION ALL SELECT 'enquiries', count(*) FROM vyapar_enquiries.enquiries
  UNION ALL SELECT 'reviews', count(*) FROM vyapar_reviews.reviews
  UNION ALL SELECT 'promotions', count(*) FROM vyapar_commercial.promotions
  ORDER BY 1;
"

echo "Done. Vyapar DB is ready at ${DB_URL}"
echo
echo "Rollback / start over:"
echo "  PGPASSWORD=\$DB_ADMIN_PASSWORD psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_ADMIN_USER:-postgres} -c \"DROP DATABASE ${DB_NAME};\""
echo "  then re-run ./init.sh"
