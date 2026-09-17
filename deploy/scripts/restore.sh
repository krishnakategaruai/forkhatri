#!/usr/bin/env bash
# =============================================================================
# Runs ON THE VM. Restores databases (and media) from a backup made by backup.sh.
#
#   restore.sh --list                         # local backups, and R2 backups when configured
#   restore.sh <name>                         # from /opt/forkhatri/backups/<name>
#   restore.sh <name> --from-r2               # download r2:<bucket>/forkhatri/<name> first
#   restore.sh <name> --only mangaly          # one database (forkhatri_identity | mangaly | forkhatridb)
#   restore.sh <name> --skip-media            # databases only
#   add --yes to skip the confirmation prompt
#
# Order: verify checksums -> stop the apps -> for each database: drop, recreate
# with its owner, load the dump -> run migrations (re-applies grants and any
# migration newer than the backup) -> restore media -> start the apps.
# =============================================================================
set -euo pipefail
BASE=/opt/forkhatri
ENV_FILE="$BASE/shared/.env.production"
COMPOSE="$BASE/current/deploy/scripts/compose.sh"
export FORKHATRI_ENV_FILE="$ENV_FILE"
val() { sed -n "s/^$1='\(.*\)'$/\1/p" "$ENV_FILE"; }

r2_env() {
  local id key secret
  id="$(val R2_ACCOUNT_ID)"; key="$(val R2_ACCESS_KEY_ID)"; secret="$(val R2_SECRET_ACCESS_KEY)"; R2_BUCKET="$(val R2_BUCKET)"
  [ -n "$id" ] && [ -n "$key" ] && [ -n "$secret" ] && [ -n "$R2_BUCKET" ] || return 1
  export RCLONE_CONFIG_R2_TYPE=s3 RCLONE_CONFIG_R2_PROVIDER=Cloudflare RCLONE_CONFIG_R2_REGION=auto \
         RCLONE_CONFIG_R2_ENDPOINT="https://${id}.r2.cloudflarestorage.com" \
         RCLONE_CONFIG_R2_ACCESS_KEY_ID="$key" RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$secret" RCLONE_CONFIG_R2_NO_CHECK_BUCKET=true
}

NAME=""; FROM_R2=false; ONLY=""; MEDIA=true; YES=false
while [ $# -gt 0 ]; do
  case "$1" in
    --list)
      echo "Local:"; ls -1 "$BASE/backups" 2>/dev/null | sed 's/^/  /'
      if r2_env; then echo "R2 ($R2_BUCKET):"; rclone lsf "r2:$R2_BUCKET/forkhatri/" --dirs-only | sed 's#/$##; s/^/  /'; fi
      exit 0 ;;
    --from-r2) FROM_R2=true ;;
    --only) ONLY="${2:?database}"; shift ;;
    --skip-media) MEDIA=false ;;
    --yes) YES=true ;;
    -*) echo "unknown option $1" >&2; exit 2 ;;
    *) NAME="$1" ;;
  esac
  shift
done
[ -n "$NAME" ] || { echo "usage: restore.sh <backup-name> [--from-r2] [--only db] [--skip-media] [--yes]" >&2; exit 2; }
DIR="$BASE/backups/$NAME"

if [ "$FROM_R2" = true ]; then
  r2_env || { echo "R2_* values are not set in $ENV_FILE" >&2; exit 1; }
  mkdir -p "$DIR"
  rclone copy "r2:$R2_BUCKET/forkhatri/$NAME" "$DIR" --checksum --retries 5
fi
[ -f "$DIR/SHA256SUMS" ] || { echo "backup $DIR not found or incomplete" >&2; exit 1; }
(cd "$DIR" && sha256sum -c --quiet SHA256SUMS) || { echo "checksum mismatch in $DIR" >&2; exit 1; }

DBS=(forkhatri_identity mangaly forkhatridb)
[ -n "$ONLY" ] && DBS=("$ONLY")
declare -A OWNER=([forkhatri_identity]=identity_owner [mangaly]=mangaly_owner [forkhatridb]=postgres)

if [ "$YES" != true ]; then
  echo "This REPLACES ${DBS[*]} with backup $NAME$([ "$MEDIA" = true ] && [ -z "$ONLY" ] && echo ' and replaces uploaded media')."
  read -r -p "Type RESTORE to continue: " answer
  [ "$answer" = RESTORE ] || { echo "cancelled"; exit 1; }
fi

APPS=(caddy forkhatri-web mangaly-web milavn-web mangaly-service milavn-service identity-service)
echo "==> stopping apps"
"$COMPOSE" up -d --wait postgres
"$COMPOSE" stop "${APPS[@]}"

# Roles must exist before a dump that references them is loaded (fresh VM case).
"$COMPOSE" --profile ops run --rm migrate >/dev/null

for db in "${DBS[@]}"; do
  owner="${OWNER[$db]:?unknown database $db}"
  echo "==> restoring $db"
  "$COMPOSE" exec -T postgres psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
    -c "DROP DATABASE IF EXISTS \"$db\" WITH (FORCE)" \
    -c "CREATE DATABASE \"$db\" OWNER \"$owner\" ENCODING 'UTF8' TEMPLATE template0"
  gunzip -c "$DIR/$db.sql.gz" | "$COMPOSE" exec -T postgres psql -v ON_ERROR_STOP=1 -q -U postgres -d "$db" >/dev/null
done

echo "==> migrations and grants"
"$COMPOSE" --profile ops run --rm migrate

if [ "$MEDIA" = true ] && [ -z "$ONLY" ]; then
  echo "==> media"
  "$COMPOSE" run --rm --no-deps -T --entrypoint sh mangaly-service -c 'find /srv/mangaly/mangaly-service/.local-media -mindepth 1 -delete; tar xzf - -C /srv/mangaly/mangaly-service/.local-media' < "$DIR/mangaly-media.tar.gz"
  "$COMPOSE" run --rm --no-deps -T --entrypoint sh milavn-service -c 'find /srv/milavn/milavn-service/.local-media -mindepth 1 -delete; tar xzf - -C /srv/milavn/milavn-service/.local-media' < "$DIR/milavn-media.tar.gz"
fi

echo "==> starting apps"
"$COMPOSE" up -d
echo "Restored $NAME."
