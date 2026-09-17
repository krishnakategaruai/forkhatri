#!/usr/bin/env bash
# Run Docker Compose for the ForKhatri stack with the server's secrets file.
#   deploy/scripts/compose.sh ps
#   deploy/scripts/compose.sh logs -f --tail=200 milavn-service
#   deploy/scripts/compose.sh --profile ops run --rm migrate --status
set -euo pipefail
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${FORKHATRI_ENV_FILE:-/opt/forkhatri/shared/.env.production}"
[ -f "$ENV_FILE" ] || ENV_FILE="$DEPLOY_DIR/secrets/.env.production"
[ -f "$ENV_FILE" ] || { echo "No secrets file (expected /opt/forkhatri/shared/.env.production)." >&2; exit 1; }
if [ -z "${RELEASE_ID:-}" ] && [ -f "$DEPLOY_DIR/RELEASE" ]; then RELEASE_ID="$(cat "$DEPLOY_DIR/RELEASE")"; export RELEASE_ID; fi
exec docker compose --project-directory "$DEPLOY_DIR" -f "$DEPLOY_DIR/docker-compose.yml" --env-file "$ENV_FILE" "$@"
