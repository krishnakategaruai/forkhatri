#!/usr/bin/env bash
# =============================================================================
# Runs ON THE VM, nightly from cron (installed by server-bootstrap.sh), or by hand.
#
#   /opt/forkhatri/backups/<UTC timestamp>/
#     forkhatri_identity.sql.gz  mangaly.sql.gz  forkhatridb.sql.gz   (pg_dump, plain SQL, gzip)
#     globals.sql.gz            roles, for reference (passwords come from the secrets file)
#     mangaly-media.tar.gz  milavn-media.tar.gz                        (uploaded photos)
#     SHA256SUMS  MANIFEST
#
# Keeps BACKUP_KEEP_DAYS (default 14) days on disk. When all R2_* values are set
# in the secrets file, also copies the backup to Cloudflare R2 with rclone
# (configured from environment variables; no rclone.conf) and keeps 30 days there.
# =============================================================================
set -euo pipefail
BASE=/opt/forkhatri
ENV_FILE="$BASE/shared/.env.production"
COMPOSE="$BASE/current/deploy/scripts/compose.sh"
export FORKHATRI_ENV_FILE="$ENV_FILE"
[ -x "$COMPOSE" ] || { echo "No current release; nothing to back up." >&2; exit 1; }

val() { sed -n "s/^$1='\(.*\)'$/\1/p" "$ENV_FILE"; }
KEEP_DAYS="$(val BACKUP_KEEP_DAYS)"; KEEP_DAYS="${KEEP_DAYS:-14}"
NAME="$(date -u +%Y%m%dT%H%M%SZ)"
DIR="$BASE/backups/$NAME"
umask 077
mkdir -p "$DIR"
log() { echo "$(date -u +%FT%TZ) $*"; }

log "backup $NAME"
for db in forkhatri_identity mangaly forkhatridb; do
  "$COMPOSE" exec -T postgres pg_dump -U postgres -d "$db" --format=plain --no-password | gzip -6 > "$DIR/$db.sql.gz"
  gzip -t "$DIR/$db.sql.gz"
  log "  $db: $(du -h "$DIR/$db.sql.gz" | cut -f1)"
done
"$COMPOSE" exec -T postgres pg_dumpall -U postgres --globals-only --no-password | gzip -6 > "$DIR/globals.sql.gz"
"$COMPOSE" exec -T mangaly-service tar czf - -C /srv/mangaly/mangaly-service/.local-media . > "$DIR/mangaly-media.tar.gz"
"$COMPOSE" exec -T milavn-service tar czf - -C /srv/milavn/milavn-service/.local-media . > "$DIR/milavn-media.tar.gz"

{
  echo "name=$NAME"
  echo "release=$(basename "$(readlink -f "$BASE/current")")"
  echo "postgres=$("$COMPOSE" exec -T postgres postgres --version | tr -d '\r')"
} > "$DIR/MANIFEST"
(cd "$DIR" && sha256sum ./*.gz MANIFEST > SHA256SUMS)
log "  written $(du -sh "$DIR" | cut -f1) to $DIR"

# Local retention.
find "$BASE/backups" -mindepth 1 -maxdepth 1 -type d -mtime +"$KEEP_DAYS" -print -exec rm -rf {} + | sed 's/^/  pruned /'

# Off-server copy to Cloudflare R2 (optional, strongly recommended).
R2_ACCOUNT_ID="$(val R2_ACCOUNT_ID)"; R2_ACCESS_KEY_ID="$(val R2_ACCESS_KEY_ID)"
R2_SECRET_ACCESS_KEY="$(val R2_SECRET_ACCESS_KEY)"; R2_BUCKET="$(val R2_BUCKET)"
if [ -n "$R2_ACCOUNT_ID" ] && [ -n "$R2_ACCESS_KEY_ID" ] && [ -n "$R2_SECRET_ACCESS_KEY" ] && [ -n "$R2_BUCKET" ]; then
  command -v rclone >/dev/null || { log "R2 configured but rclone is not installed (run server-bootstrap.sh)"; exit 1; }
  export RCLONE_CONFIG_R2_TYPE=s3 RCLONE_CONFIG_R2_PROVIDER=Cloudflare RCLONE_CONFIG_R2_REGION=auto \
         RCLONE_CONFIG_R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com" \
         RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
         RCLONE_CONFIG_R2_NO_CHECK_BUCKET=true
  rclone copy "$DIR" "r2:$R2_BUCKET/forkhatri/$NAME" --checksum --retries 5 --low-level-retries 10
  rclone check "$DIR" "r2:$R2_BUCKET/forkhatri/$NAME" --one-way >/dev/null
  log "  copied to r2:$R2_BUCKET/forkhatri/$NAME"
  rclone delete "r2:$R2_BUCKET/forkhatri" --min-age 30d --rmdirs || log "  WARNING: R2 retention cleanup failed"
else
  log "  WARNING: R2 is not configured; this backup exists only on this VM."
fi
log "backup $NAME done"
