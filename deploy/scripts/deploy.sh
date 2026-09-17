#!/usr/bin/env bash
# =============================================================================
# ForKhatri deploy — run from the owner's Windows machine (Git Bash), or from CI.
#
#   deploy/scripts/deploy.sh                 # upload this working tree as a new release, build, migrate, go live
#   deploy/scripts/deploy.sh --bootstrap     # first time only: prepare a fresh Ubuntu 24.04 VM, then deploy
#   deploy/scripts/deploy.sh --seed-dev      # also load DEVELOPMENT members and data (never on a real launch)
#   deploy/scripts/deploy.sh --rollback [id] # switch back to the previous (or named) release
#   deploy/scripts/deploy.sh --logs [svc]    # follow logs (all services, or one)
#   deploy/scripts/deploy.sh --status        # containers, releases, disk, memory
#   deploy/scripts/deploy.sh --backup-now    # run the backup immediately
#   deploy/scripts/deploy.sh --ssh           # open a shell on the VM
#
# Server and user come from deploy/secrets/owner-inputs.env (SERVER_IP, SERVER_USER).
# SSH key: ~/.ssh/forkhatri_oracle (override with FORKHATRI_SSH_KEY).
# CI mode (--ci): SERVER_IP/SERVER_USER from the environment, key already loaded,
# secrets already on the server (they are never stored in GitHub).
# Needs only ssh and tar (both ship with Git for Windows); rsync is not required.
# =============================================================================
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SECRETS="$REPO_ROOT/deploy/secrets"
ACTION=deploy; ARG=""; SEED=""; CI=false
while [ $# -gt 0 ]; do
  case "$1" in
    --bootstrap) ACTION=bootstrap ;;
    --seed-dev) SEED=--seed-dev ;;
    --rollback) ACTION=rollback; [[ "${2:-}" != --* && -n "${2:-}" ]] && { ARG="$2"; shift; } ;;
    --logs) ACTION=logs; [[ "${2:-}" != --* && -n "${2:-}" ]] && { ARG="$2"; shift; } ;;
    --status) ACTION=status ;;
    --backup-now) ACTION=backup ;;
    --ssh) ACTION=ssh ;;
    --ci) CI=true ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

input() { sed -n "s/^$1=\(.*\)$/\1/p" "$SECRETS/owner-inputs.env" 2>/dev/null | tr -d '\r' | sed "s/^['\"]//; s/['\"]$//" | tail -1; }
if [ "$CI" = true ]; then
  : "${SERVER_IP:?SERVER_IP is required in CI}" "${SERVER_USER:?SERVER_USER is required in CI}"
  SSH_OPTS=(-o BatchMode=yes -o ServerAliveInterval=30)
else
  SERVER_IP="$(input SERVER_IP)"; SERVER_USER="$(input SERVER_USER)"
  [ -n "$SERVER_IP" ] && [ -n "$SERVER_USER" ] || { echo "Set SERVER_IP and SERVER_USER in deploy/secrets/owner-inputs.env" >&2; exit 1; }
  KEY="${FORKHATRI_SSH_KEY:-$HOME/.ssh/forkhatri_oracle}"
  [ -f "$KEY" ] || { echo "SSH key not found: $KEY" >&2; exit 1; }
  SSH_OPTS=(-i "$KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30)
fi
TARGET="$SERVER_USER@$SERVER_IP"
remote() { ssh "${SSH_OPTS[@]}" "$TARGET" "$@"; }
remote_tty() { ssh -t "${SSH_OPTS[@]}" "$TARGET" "$@"; }

upload_secrets() {
  [ "$CI" = true ] && return 0
  "$REPO_ROOT/deploy/scripts/generate-secrets.sh" >/dev/null
  echo "==> uploading secrets (not printed)"
  remote 'umask 077; mkdir -p /opt/forkhatri/shared && cat > /opt/forkhatri/shared/.env.production.new && mv -f /opt/forkhatri/shared/.env.production.new /opt/forkhatri/shared/.env.production' \
    < "$SECRETS/.env.production"
}

release_id() {
  local sha="nogit" dirty=""
  if git -C "$REPO_ROOT" rev-parse --short=10 HEAD >/dev/null 2>&1; then
    sha="$(git -C "$REPO_ROOT" rev-parse --short=10 HEAD)"
    [ -n "$(git -C "$REPO_ROOT" status --porcelain -- platform modules deploy 2>/dev/null)" ] && dirty="-dirty"
  fi
  echo "$(date -u +%Y%m%dT%H%M%SZ)-$sha$dirty"
}

upload_release() {
  local id="$1"
  echo "==> uploading release $id"
  (cd "$REPO_ROOT" && tar -czf - \
      --exclude=node_modules --exclude='.next' --exclude='.next-*' --exclude=.venv --exclude=__pycache__ \
      --exclude=.pytest_cache --exclude=.ruff_cache --exclude=.mypy_cache --exclude='*.egg-info' \
      --exclude=.logs --exclude='*.log' --exclude=.local-media --exclude='*.tsbuildinfo' \
      --exclude=.env --exclude=.env.local --exclude=.env.production --exclude=.env.local-test \
      --exclude=deploy/secrets --exclude=tests \
      deploy \
      platform/identity-service \
      platform/forkhatri-web \
      modules/MOD03-mangaly/mangaly-service modules/MOD03-mangaly/mangaly-web modules/MOD03-mangaly/07a-db-implementation/migrations \
      modules/MOD02-milavn/milavn-service modules/MOD02-milavn/milavn-web modules/MOD02-milavn/07a-db-implementation/migrations \
      modules/MOD02-milavn/07a-db-implementation/seeds.sql modules/MOD02-milavn/07a-db-implementation/seeds-dev.sql) \
    | remote "set -e; mkdir -p /opt/forkhatri/releases/$id && tar -xzf - -C /opt/forkhatri/releases/$id && chmod +x /opt/forkhatri/releases/$id/deploy/scripts/*.sh"
}

case "$ACTION" in
  bootstrap)
    echo "==> preparing $TARGET (needs sudo on the VM)"
    remote 'cat > /tmp/forkhatri-server-bootstrap.sh' < "$REPO_ROOT/deploy/scripts/server-bootstrap.sh"
    remote_tty 'sudo bash /tmp/forkhatri-server-bootstrap.sh && rm -f /tmp/forkhatri-server-bootstrap.sh'
    upload_secrets
    id="$(release_id)"; upload_release "$id"
    # sg: the docker group membership added by the bootstrap is not active in this session yet.
    remote "sg docker -c '/opt/forkhatri/releases/$id/deploy/scripts/remote-release.sh $id $SEED'"
    ;;
  deploy)
    upload_secrets
    id="$(release_id)"; upload_release "$id"
    remote "/opt/forkhatri/releases/$id/deploy/scripts/remote-release.sh $id $SEED"
    ;;
  rollback) remote "/opt/forkhatri/current/deploy/scripts/rollback.sh $ARG" ;;
  logs) remote_tty "/opt/forkhatri/current/deploy/scripts/compose.sh logs -f --tail=200 $ARG" ;;
  status)
    remote 'set -e; echo "current: $(basename "$(readlink -f /opt/forkhatri/current)")"; echo "releases:"; ls -1t /opt/forkhatri/releases | head; /opt/forkhatri/current/deploy/scripts/compose.sh ps; echo; free -h; df -h / | tail -1; docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"'
    ;;
  backup) remote '/opt/forkhatri/current/deploy/scripts/backup.sh' ;;
  ssh) remote_tty ;;
esac
