#!/usr/bin/env bash
# =============================================================================
# Runs ON THE VM for one uploaded release (called by deploy.sh and the GitHub workflow).
#   /opt/forkhatri/releases/<id>/deploy/scripts/remote-release.sh <id> [--seed-dev]
#
# 1. build images one at a time (tagged with the release id)
# 2. start Postgres, run migrations (forward-only)
# 3. start the new release, then check every service through Caddy
# 4. healthy  -> point /opt/forkhatri/current at it, prune old releases (keep 5)
#    unhealthy -> restart the previous release's containers and exit 1
# =============================================================================
set -euo pipefail
ID="${1:?release id}"; shift || true
SEED=false
for arg in "$@"; do case "$arg" in --seed-dev) SEED=true ;; *) echo "unknown option $arg" >&2; exit 2 ;; esac; done

BASE=/opt/forkhatri
REL="$BASE/releases/$ID"
ENV_FILE="$BASE/shared/.env.production"
COMPOSE="$REL/deploy/scripts/compose.sh"
KEEP=5
[ -d "$REL/deploy" ] || { echo "release $REL not found" >&2; exit 1; }
[ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE (deploy.sh uploads it)" >&2; exit 1; }

export RELEASE_ID="$ID" FORKHATRI_ENV_FILE="$ENV_FILE" COMPOSE_PARALLEL_LIMIT=1
echo "$ID" > "$REL/deploy/RELEASE"
PREVIOUS="$(readlink -f "$BASE/current" 2>/dev/null || true)"

step() { echo; echo "==> $*"; }

step "Building images for $ID (sequential, to stay within 12 GB)"
for svc in migrate identity-service mangaly-service milavn-service forkhatri-web mangaly-web milavn-web; do
  echo "--- $svc"
  "$COMPOSE" --profile ops build "$svc"
done

step "Starting Postgres"
"$COMPOSE" up -d --wait postgres

step "Migrating"
"$COMPOSE" --profile ops run --rm migrate
if [ "$SEED" = true ]; then
  step "Loading DEVELOPMENT seed data (explicitly requested)"
  "$COMPOSE" --profile ops run --rm migrate --seed-dev --i-understand-this-loads-development-data
fi

step "Starting release $ID"
"$COMPOSE" up -d --remove-orphans

health() {
  local ok=true path code
  for path in /edge-health /api/identity/health /api/mangaly/health /api/milavn/health / /mangaly /milavn; do
    code="$("$COMPOSE" exec -T caddy wget -q -S -O /dev/null "http://127.0.0.1$path" 2>&1 | awk '/HTTP\//{c=$2} END{print c+0}')"
    case "$path" in
      /edge-health|/api/*) [ "$code" = 200 ] || ok=false ;;
      *) [ "$code" -ge 200 ] && [ "$code" -lt 400 ] || ok=false ;;
    esac
    printf '  %-22s %s\n' "$path" "$code"
  done
  $ok
}

step "Health checks through Caddy"
healthy=false
for attempt in $(seq 1 18); do
  if health; then healthy=true; break; fi
  echo "  not healthy yet (attempt $attempt/18); retrying in 10 s"
  sleep 10
done

if [ "$healthy" != true ]; then
  echo; echo "!! Release $ID is unhealthy. Recent logs:"
  "$COMPOSE" ps || true
  "$COMPOSE" logs --tail=60 identity-service mangaly-service milavn-service forkhatri-web mangaly-web milavn-web caddy || true
  if [ -n "$PREVIOUS" ] && [ -d "$PREVIOUS/deploy" ]; then
    prev_id="$(basename "$PREVIOUS")"
    step "Restoring previous release $prev_id (database migrations are not reversed)"
    RELEASE_ID="$prev_id" "$PREVIOUS/deploy/scripts/compose.sh" up -d --remove-orphans --no-build || true
  fi
  exit 1
fi

ln -sfn "$REL" "$BASE/current"
step "Release $ID is live"

# Keep the newest $KEEP releases (and their images); never the current one.
mapfile -t old < <(ls -1dt "$BASE"/releases/*/ 2>/dev/null | tail -n +$((KEEP + 1)))
for dir in "${old[@]}"; do
  dir="${dir%/}"; old_id="$(basename "$dir")"
  [ "$dir" = "$(readlink -f "$BASE/current")" ] && continue
  echo "pruning release $old_id"
  docker image ls --format '{{.Repository}}:{{.Tag}}' | grep -E "^forkhatri/[a-z-]+:${old_id}$" | xargs -r docker image rm >/dev/null 2>&1 || true
  rm -rf "$dir"
done
docker builder prune -f --filter until=168h >/dev/null 2>&1 || true
