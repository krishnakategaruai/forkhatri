# ForKhatri runbook (as built, 2026-11-22)

Document status: AS BUILT on 2026-11-22. Sources: `scripts/dev.mjs`, `scripts/tunnel.mjs`, `scripts/start-tunnels.ps1`,
`deploy/README.md`, `deploy/scripts/*.sh`, `deploy/Caddyfile`, `deploy/docker-compose.yml`, `.github/workflows/deploy.yml`.
Secrets are named, never written here. Architecture: `docs/architecture.md`.

Important: production has never been run (no Docker on the build machine). Treat section 3 as the designed procedure
and read "Known failures" before the first real deploy.

## Contents

1. [Development: start, stop, status](#1-development-start-stop-status)
2. [Development: public tunnels for phones](#2-development-public-tunnels-for-phones)
3. [Production deploy](#3-production-deploy)
4. [Health checks](#4-health-checks)
5. [Backups, restore, rollback](#5-backups-restore-rollback)
6. [Secrets handling](#6-secrets-handling)
7. [Edge (Caddy) and containers](#7-edge-caddy-and-containers)
8. [Common failures and fixes](#8-common-failures-and-fixes)

## 1. Development: start, stop, status

Prerequisites: PostgreSQL running on port 5433; each Python service has its `.venv`; each web app has `node_modules`.

| Task | Command (repository root) |
|---|---|
| Start everything | `npm run dev` (runs `node scripts/dev.mjs`) |
| Only platform | `npm run dev:platform` |
| One module plus platform | `npm run dev:mangalya`, `dev:milavn`, `dev:vyapar`, `dev:counsel` |
| Any subset | `npm run dev -- --only=platform,milavn` (groups: platform, mangalya, milavn, vyapar, counsel; or a process name) |
| What is listening | `npm run dev:status` |

Behaviour: logs from every process share one terminal with coloured prefixes. A port already in use is left alone and
reported "already running" (several sessions share the repository). Missing `.venv` or `node_modules` is reported, not fatal.
Python APIs run without `--reload`, so restart them after a code change. Ctrl+C stops only the processes the script started.

Ports: identity 8100, entrance 3100, Mangalya API 8000 and web 3000, horoscope 8013, Milavn API 8001 and web 3001,
Vyapar API 8011 and web 3011, Counsel API 8014 and web 3014, Postgres 5433.

Rules for operators and agents (owner rules): restart dev services yourself when a change needs it, only on the known ports; never
kill by image name (a broad `python.exe` kill has taken down other services); never close another session's Chrome.

Known drift: `scripts/dev.mjs` names Mangalya folders `mangalya-service` and `mangalya-web`, which do not exist (real names
`mangaly-service`, `mangaly-web`), so `npm run dev` reports them missing. Workaround: start them by hand from their folders
(`.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; `npm run dev`), or use `npm run dev:tunnel`.

Development sign-in: http://localhost:3100, avatar then "Act as (development)"; personas asha, new-member, mangalya-family,
mangalya-parent, milavn-moderator (krishna is the owner's, people only). Tests: `platform/identity-service/scripts/dev_session.py <persona> --storage-state <file>`.
Password sign-in for end-to-end checks: see `CLAUDE.md`.

## 2. Development: public tunnels for phones

Needs `cloudflared` (Windows: `winget install Cloudflare.cloudflared`). Do not run together with `npm run dev`.

| Task | Command |
|---|---|
| Start (foreground, Ctrl+C reverts everything) | `npm run dev:tunnel` |
| Start hidden in background (Windows) | `powershell -ExecutionPolicy Bypass -File scripts\start-tunnels.ps1` |
| Status and public links | `scripts\start-tunnels.ps1 -Status` (links also in `scripts\.tunnel.log`) |
| Run in this window | `scripts\start-tunnels.ps1 -Foreground` |
| Stop | `scripts\start-tunnels.ps1 -Stop` |

`start-tunnels.ps1` first frees ports 8100, 3100, 8000, 3000, 8001, 3001, 8011, 3011, 8014, 3014, 8013 (it kills what listens there),
deletes each web app's `.next` cache, then starts `scripts/tunnel.mjs`. Every run produces new random `*.trycloudflare.com` links, one per service.
Env files are rewritten inside marked blocks and reverted on a clean exit. If stopped by force, run `npm run dev` once and confirm localhost works
(or check the marked blocks in each `.env`/`.env.local`). Details: `docs/architecture.md` section 12.

## 3. Production deploy

Target: one Oracle Cloud Always Free Ampere VM (Ubuntu 24.04 aarch64, 2 OCPU, 12 GB) behind a Cloudflare Tunnel.
Run from Git Bash on the owner's machine. Full account setup (Oracle, Cloudflare, Resend, R2) is in `deploy/README.md`
and summarised in `docs/ParentApp/DEPLOYMENT.md`.

Inputs (names only) in git-ignored `deploy/secrets/owner-inputs.env`: `DOMAIN`, `CLOUDFLARE_TUNNEL_TOKEN`, `RESEND_API_KEY`, `EMAIL_FROM`,
`SERVER_IP`, `SERVER_USER`, optional `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`.

First deploy:

1. `cp deploy/secrets/owner-inputs.env.example deploy/secrets/owner-inputs.env` and fill it.
2. `bash deploy/scripts/generate-secrets.sh` (writes `deploy/secrets/.env.production`; prints names only; `--rotate` renews; `--local-test` for a rehearsal).
3. `bash deploy/scripts/deploy.sh --bootstrap` (once per VM: updates, Docker, swap, UFW SSH-only, SSH keys only, `/opt/forkhatri`, rclone, cron for backup at 21:00 UTC and heartbeat every 5 minutes; then deploys).
4. First build takes about 15 to 25 minutes. Open `https://<DOMAIN>`.
5. `bash deploy/scripts/deploy.sh --seed-dev` only for a private trial (loads development members; never for a real launch).

Everyday:

| Task | Command |
|---|---|
| Deploy the working tree | `bash deploy/scripts/deploy.sh` |
| Status (containers, releases, memory, disk) | `bash deploy/scripts/deploy.sh --status` |
| Logs | `bash deploy/scripts/deploy.sh --logs` or `--logs milavn-service` |
| Back up now | `bash deploy/scripts/deploy.sh --backup-now` |
| Rollback | `bash deploy/scripts/deploy.sh --rollback` or `--rollback <release-id>` |
| Shell on VM | `bash deploy/scripts/deploy.sh --ssh` |
| On the VM: compose wrapper | `/opt/forkhatri/current/deploy/scripts/compose.sh ps` (also `logs --tail=100 caddy`, `--profile ops run --rm migrate --status`) |

How a deploy works (`deploy.sh` then `remote-release.sh`): stream folders to `/opt/forkhatri/releases/<UTC time>-<git sha>`; upload
`.env.production` to `/opt/forkhatri/shared/` (mode 600); build images tagged with the release id; start Postgres; run `migrate`; `docker compose up -d`;
health checks (`/edge-health`, three `/api/*/health`, `/`, `/mangaly`, `/milavn`). Healthy: `current` points at the new release and releases beyond the newest 5
are pruned. Unhealthy: the previous release is restarted and the deploy fails.

Migrations (`deploy/migrate/migrate.py`): idempotent; creates six roles and three databases, applies each `*.sql` in name order as the owner role,
records SHA-256 in `forkhatri_deploy.applied_migration` (a changed recorded file is reported, never re-run), verifies no runtime role owns a table.
Flags: `--status`, `--baseline`, `--seed-dev --i-understand-this-loads-development-data`.

Push-to-deploy (`.github/workflows/deploy.yml`): runs on push to `main` touching `platform/**`, `modules/MOD02-milavn/**`, `modules/MOD03-mangaly/**` (drift: should be `MOD03-mangalya`),
`deploy/**` or the workflow; or by hand (input `seed_dev`). Never for pull requests or forks. Uses environment `production`, concurrency group `deploy-production`, 60-minute limit,
and runs `bash deploy/scripts/deploy.sh --ci`. Repository secrets: `SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`, optional `SSH_KNOWN_HOSTS`. Application secrets stay on the VM.
A manual first deploy must exist so `/opt/forkhatri/shared/.env.production` is present.

Local rehearsal with Docker: `LOCAL_PORT=8080 bash deploy/scripts/generate-secrets.sh --local-test`, then
`docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.local-test.yml --env-file deploy/secrets/.env.local-test up -d --build`.

## 4. Health checks

| What | Check |
|---|---|
| Identity (dev) | `GET http://localhost:8100/health` |
| Module APIs (dev) | each answers on its port (Milavn and Mangalya `/health` through the Caddy prefix in production; Vyapar and Counsel: unverified path, check `/openapi.json`) |
| Web apps (dev) | any HTTP answer on `/` (the launcher treats 404 as up) |
| Hub and registry | `GET http://localhost:8100/v1/modules` lists six modules |
| Production edge | `https://<DOMAIN>/edge-health` returns `ok` |
| Production APIs | `https://<DOMAIN>/api/identity/health`, `/api/mangaly/health`, `/api/milavn/health` |
| Heartbeat log | `/opt/forkhatri/logs/heartbeat.log` (every 5 minutes; restarts the stack after 3 consecutive local failures) |
| Backup log | `/opt/forkhatri/logs/backup.log` |
| Everything | `bash deploy/scripts/deploy.sh --status` |

## 5. Backups, restore, rollback

Backups (`backup.sh`, nightly 21:00 UTC = 02:30 IST, or `--backup-now`): `/opt/forkhatri/backups/<UTC timestamp>/` with
`forkhatri_identity.sql.gz`, `mangaly.sql.gz`, `forkhatridb.sql.gz`, `globals.sql.gz`, `mangaly-media.tar.gz`, `milavn-media.tar.gz`, `SHA256SUMS`, `MANIFEST`.
Kept 14 days on disk (`BACKUP_KEEP_DAYS`); copied to R2 (`r2:<bucket>/forkhatri/<name>`, verified, 30 days) when all `R2_*` values are set.
Vyapar and Counsel databases are NOT in the backup (not deployed).

Restore on the same VM (`deploy.sh --ssh` first):

```
/opt/forkhatri/current/deploy/scripts/restore.sh --list
/opt/forkhatri/current/deploy/scripts/restore.sh <name>                 # everything
/opt/forkhatri/current/deploy/scripts/restore.sh <name> --only mangaly  # one database (forkhatri_identity | mangaly | forkhatridb)
/opt/forkhatri/current/deploy/scripts/restore.sh <name> --skip-media    # databases only
```

Order: verify checksums, stop apps, drop and recreate each database with its owner, load dumps, re-run migrations, restore media, start apps. `--from-r2` downloads first; `--yes` skips confirmation.

New VM after loss: create VM, update `SERVER_IP`, `deploy.sh --bootstrap` with the same secrets file, `deploy.sh --ssh`, `restore.sh --list`, `restore.sh <name> --from-r2`.
The tunnel token is unchanged so the address returns. Keep `owner-inputs.env` and `.env.production` in a password manager.

Rollback: `deploy.sh --rollback [id]` restarts the previous release's images without rebuilding (fails if an image was pruned). Migrations are forward-only and are not undone;
after a destructive migration, restore the backup taken before it.

## 6. Secrets handling

Names only. Files: `deploy/secrets/owner-inputs.env` (human inputs) and `deploy/secrets/.env.production` (generated; on the VM at `/opt/forkhatri/shared/.env.production`, mode 600), both git-ignored.
Generated names (not values): `POSTGRES_PASSWORD`, `IDENTITY_OWNER_PASSWORD`, `IDENTITY_APP_PASSWORD`, `MANGALY_OWNER_PASSWORD`, `MANGALY_APP_PASSWORD`, `MILAVN_OWNER_PASSWORD`, `MILAVN_APP_PASSWORD`, `OTP_PEPPER`, `MANGALY_SERVICE_KEY`, `MILAVN_SERVICE_KEY`.
Also used: `RESEND_API_KEY`, `EMAIL_FROM`, `CLOUDFLARE_TUNNEL_TOKEN`, `PUBLIC_ORIGIN`, `SESSION_COOKIE_NAME`, `BACKUP_KEEP_DAYS`, image tag overrides.
GitHub repository secrets: `SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`. SSH keys: `~/.ssh/forkhatri_oracle` (owner) and a separate `forkhatri_github_deploy` key (CI).
Rules: never paste values into chat or commits; the identity service refuses to start in production with development tools on, `DEV_EXPOSE_OTP` on, CHANGE_ME or short secrets (under 32 characters), a non `__Host-` cookie name, or console delivery providers.
Rotate: `generate-secrets.sh --rotate` then `deploy.sh` (database passwords re-synced; members stay signed in; codes requested in the last 5 minutes stop working).

## 7. Edge (Caddy) and containers

`deploy/Caddyfile`: listens on `:80` (override `CADDY_PORT`), no automatic TLS (Cloudflare terminates), `request_body max_size 25MB`, security headers, one ordered `route` block.
Order matters: `/edge-health`, then 404 rules for `/internal*` and API docs, then `handle_path` for `/api/identity|mangaly|milavn/*` (prefix stripped), `respond /api/* 404`, then zones `/mangaly`, `/milavn`, then default zone. Upstream overrides by env: `IDENTITY_UPSTREAM`, `MANGALY_API_UPSTREAM`, `MILAVN_API_UPSTREAM`, `MANGALY_WEB_UPSTREAM`, `MILAVN_WEB_UPSTREAM`, `ENTRANCE_WEB_UPSTREAM`.
`docker-compose.yml`: services postgres (limit 2048 MB), migrate (profile `ops`, one-shot), identity-service, mangaly-service, milavn-service, forkhatri-web, mangaly-web, milavn-web, caddy (fixed address 172.28.10.10), cloudflared; networks `app` (172.28.10.0/24) and `edge`; volumes `pgdata`, `mangaly-media`, `milavn-media`. Containers read-only, `cap_drop: ALL`, `no-new-privileges`, logs 10 MB x 5.
Validate Caddy: `caddy validate --config deploy/Caddyfile` (needs the env upstream defaults).

## 8. Common failures and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `npm run dev` says Mangalya folders "do not exist" | folder-name drift in `scripts/dev.mjs` | start Mangalya by hand (section 1) or correct the names in the script |
| "already running" for a port | another session owns it | leave it; check with `npm run dev:status`; stop only your own |
| Duplicate or stale API after code change | Python APIs run without reload | restart that API; on Windows never rely on uvicorn `--reload` (orphan child keeps the socket) |
| Web build error about `next/font/google` | stale `.next` cache | delete `.next` in that web app (`start-tunnels.ps1` does it) |
| Hub shows "can't be reached" or an insights number is 0 | module API not running or not in `MODULE_API_URLS` | start the module; Mangalya Home needs the horoscope service on 8013 |
| Signed in on the hub, signed out in a module (tunnels) | each tunnel hostname is a separate site | use the handoff via the hub tile; hostnames change every run |
| After a tunnel run, localhost sign-in broken | env blocks not reverted | run `npm run dev` once, or inspect the marked blocks in `platform/identity-service/.env` and each `.env.local` |
| Phone code request returns `delivery_unavailable` | no SMS provider in production | use password or email; connect a provider later (`SMS_PROVIDER=shared`) |
| Code requests fail with 429 | rate limit (5 per identifier, 30 per IP per 15 minutes) | wait; locally raise limits in identity `.env` |
| Identity refuses to start in production | production guard in `settings.py` | read the printed list of problems; fix the named settings |
| Module returns 503 | identity unreachable; modules fail closed | check identity `/health`, `deploy.sh --logs identity-service` |
| `/api/identity/internal/...` returns 404 from outside | by design | call it only on the private network with the service key |
| Deploy fails on Mangalya path | `MOD03-mangaly` vs `MOD03-mangalya` drift in `deploy.sh`, compose, `migrate.py`, Dockerfile | rename the references before the first real deploy |
| Deploy rolled back automatically | a health check failed | `deploy.sh --logs <service>`; fix; redeploy |
| `Image forkhatri/<svc>:<id> is gone` on rollback | old image pruned | redeploy that commit |
| VM unreachable, backups gone | Always Free VM reclaimed | restore from R2 onto a new VM (section 5); convert the account to Pay As You Go; set R2 backups |
| Chat or reminders duplicated | more than one Milavn process | run exactly one Milavn API process |
| Rate limit blocks a whole event hall | many members share one mobile IP | raise the per-IP limits (known risk C15 in `docs/Critique/CRITIQUE-platform.md`) |


## 9. Account deletion and tunnels (added 2026-11-22)

### Run and verify a deletion
1. Use a throwaway member only (never the built-in personas or krishna). Create data in the modules through the normal product flows.
2. Start the member's deletion from the hub account sheet ("Delete my ForKhatri account"), or through the API: `POST /v1/account/delete` with `confirm: "DELETE"` and the password. The member is signed out everywhere at once.
3. Check the receipt at `GET /v1/account/deletion/{job_id}`: each module should be `done`. Asking a module again returns `nothing_to_delete`.
4. Check identity: no member, session, password or entry rows remain; the old session answers 401.

### Stuck or failed deletions
- The member is already signed out and cannot sign in. Identity retries failed modules every 30 s with backoff (30 s doubling to 6 h) for 7 days.
- The admin console Modules page lists stuck deletions with a Retry button (`GET /v1/admin/deletions/stuck`, `POST /v1/admin/deletions/{job_id}/retry`).
- A module shown as `failed: not_configured` has no URL: set `ERASE_MODULE_API_URLS` (falls back to `ADMIN_MODULE_API_URLS`, then `MODULE_API_URLS`) and retry. A 404 means the module lacks the erase endpoint (restart it on the current code).
- A deletion is refused with 409 `admin_role_held` while the member holds an admin role: remove the role first.
- Keep `DELETION_TOMBSTONE_PEPPER` secret and stable.

### Tunnel launcher (`scripts/start-tunnels.ps1`)
- `powershell -ExecutionPolicy Bypass -File scripts\start-tunnels.ps1` starts every server and a public cloudflared tunnel, hidden in the background, and prints the links.
- `-Status` shows what is running and the public links (also in `scripts\.tunnel.log`).
- `-Stop` stops tunnels and servers and puts the env files back to localhost.
- `-Foreground` runs in the current window; Ctrl+C stops everything cleanly.
- It first stops anything listening on ForKhatri's ports and deletes each web app's `.next` cache.

### Mangalya web in development
Mangalya web runs `next dev --webpack` (set in `modules/MOD03-mangalya/mangaly-web/package.json`) because Turbopack's `next/font` bug caused 500 errors. Do not switch it back to Turbopack.
