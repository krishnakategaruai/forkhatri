#!/usr/bin/env bash
# Runs ON THE VM. Switch back to the previous (or a named) release without rebuilding.
#   /opt/forkhatri/current/deploy/scripts/rollback.sh            # previous release
#   /opt/forkhatri/current/deploy/scripts/rollback.sh <release>  # a specific one (ls /opt/forkhatri/releases)
# Database migrations are forward-only and are NOT undone; see deploy/README.md "Roll back".
set -euo pipefail
BASE=/opt/forkhatri
current="$(readlink -f "$BASE/current")"
if [ -n "${1:-}" ]; then
  target="$BASE/releases/$1"
else
  target="$(ls -1dt "$BASE"/releases/*/ | sed 's#/$##' | grep -vx "$current" | head -1 || true)"
fi
[ -n "$target" ] && [ -d "$target/deploy" ] || { echo "No release to roll back to." >&2; exit 1; }
id="$(basename "$target")"
for svc in identity-service mangaly-service milavn-service forkhatri-web mangaly-web milavn-web; do
  docker image inspect "forkhatri/$svc:$id" >/dev/null 2>&1 || { echo "Image forkhatri/$svc:$id is gone; redeploy that commit instead." >&2; exit 1; }
done
echo "Rolling back from $(basename "$current") to $id"
RELEASE_ID="$id" FORKHATRI_ENV_FILE="$BASE/shared/.env.production" "$target/deploy/scripts/compose.sh" up -d --remove-orphans --no-build
ln -sfn "$target" "$BASE/current"
echo "Now serving $id."
