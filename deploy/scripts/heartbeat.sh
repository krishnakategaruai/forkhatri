#!/usr/bin/env bash
# Runs ON THE VM from cron every 5 minutes (installed by server-bootstrap.sh).
#
# Oracle reclaims an Always Free VM only when, over 7 days, CPU (95th percentile),
# network AND memory (A1 shapes) are ALL below 20%. The running stack keeps memory
# above that on its own; this heartbeat is deliberately light: it proves the site
# answers end to end (Caddy locally, and the public URL through the tunnel), writes
# a short log, and restarts the stack after 3 consecutive local failures.
# It never burns CPU. Converting the account to Pay As You Go removes the risk entirely.
set -uo pipefail
BASE=/opt/forkhatri
LOG="$BASE/logs/heartbeat.log"
STATE="$BASE/logs/.heartbeat-failures"
COMPOSE="$BASE/current/deploy/scripts/compose.sh"
mkdir -p "$BASE/logs"
[ -x "$COMPOSE" ] || exit 0

stamp="$(date -u +%FT%TZ)"
local_ok=false public_code=skip
if "$COMPOSE" exec -T caddy wget -q -O /dev/null http://127.0.0.1/api/identity/health >/dev/null 2>&1; then local_ok=true; fi
domain="$(sed -n "s/^DOMAIN='\(.*\)'$/\1/p" "$BASE/shared/.env.production" 2>/dev/null)"
if [ -n "$domain" ]; then
  public_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "https://$domain/api/identity/health" || echo 000)"
fi

failures="$(cat "$STATE" 2>/dev/null || echo 0)"
if [ "$local_ok" = true ]; then failures=0; else failures=$((failures + 1)); fi
echo "$failures" > "$STATE"
echo "$stamp local=$local_ok public=$public_code failures=$failures" >> "$LOG"

if [ "$failures" -ge 3 ]; then
  echo "$stamp restarting stack after $failures failed checks" >> "$LOG"
  "$COMPOSE" up -d >> "$LOG" 2>&1 || true
  echo 0 > "$STATE"
fi
tail -n 2000 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
