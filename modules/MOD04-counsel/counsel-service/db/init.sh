#!/usr/bin/env bash
# Counsel (MOD04) — local/dev database setup. One command: ./init.sh
# Reads DB_* from ../.env (copy ../.env.example first). Idempotent.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
set -a; source ../.env; set +a

ADMIN="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_ADMIN_USER}"
OWNER="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_OWNER_USER} -d ${DB_NAME}"

echo "== database =="
PGPASSWORD="${DB_ADMIN_PASSWORD}" ${ADMIN} -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || PGPASSWORD="${DB_ADMIN_PASSWORD}" ${ADMIN} -c "CREATE DATABASE ${DB_NAME};"

echo "== roles (owner runs migrations; app is the non-owning runtime role) =="
for spec in "${DB_OWNER_USER}:${DB_OWNER_PASSWORD}" "${DB_APP_USER}:${DB_APP_PASSWORD}"; do
  role="${spec%%:*}"; pw="${spec#*:}"
  PGPASSWORD="${DB_ADMIN_PASSWORD}" ${ADMIN} -tc "SELECT 1 FROM pg_roles WHERE rolname='${role}'" | grep -q 1 \
    && PGPASSWORD="${DB_ADMIN_PASSWORD}" ${ADMIN} -c "ALTER ROLE ${role} WITH LOGIN PASSWORD '${pw}';" \
    || PGPASSWORD="${DB_ADMIN_PASSWORD}" ${ADMIN} -c "CREATE ROLE ${role} LOGIN PASSWORD '${pw}';"
done
PGPASSWORD="${DB_ADMIN_PASSWORD}" ${ADMIN} -c "ALTER DATABASE ${DB_NAME} OWNER TO ${DB_OWNER_USER};"
PGPASSWORD="${DB_ADMIN_PASSWORD}" ${ADMIN} -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"

echo "== migrations =="
for f in migrations/*.sql; do
  echo "   $f"
  PGPASSWORD="${DB_OWNER_PASSWORD}" ${OWNER} -v ON_ERROR_STOP=1 -q -f "$f"
done

if [ "${SEED_DB:-false}" = "true" ] && [ -f seeds.sql ]; then
  echo "== seeds =="
  PGPASSWORD="${DB_OWNER_PASSWORD}" ${OWNER} -v ON_ERROR_STOP=1 -q -f seeds.sql
fi
echo "== done: $(PGPASSWORD="${DB_OWNER_PASSWORD}" ${OWNER} -Atc "SELECT count(*) FROM pg_tables WHERE schemaname='counsel'") tables in counsel =="
