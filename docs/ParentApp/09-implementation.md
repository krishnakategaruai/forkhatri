---
project: ForKhatri
artifact: Parent Application Implementation
step: 9
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Implementation

Contract: `07-tech-reqs.md`. Decisions and research: `00c-identity-and-entrance-decisions.md`.

## Revision history

| Date | Change |
|---|---|
| 2026-09-13 | Static demo shell in `web/parent-app/` (demo session, no real identity). |
| 2026-09-14 | Real implementation: Identity & Trust Service, ForKhatri web entrance, Mangaly and Milavn moved onto the ForKhatri session. `web/parent-app/` kept as the superseded prototype. |
| 2026-09-14 | Deployment kit for one Oracle Always Free Ampere VM behind a Cloudflare Tunnel (`deploy/`): per-app Dockerfiles, Caddy edge, URL-based migration runner, Resend email delivery and `delivery_unavailable`, env-driven `basePath` in both module web apps, backups to disk and R2, push-to-deploy. Rehearsed natively (no Docker on this machine); nothing deployed. |

## What runs (development)

| Component | Path | Port |
|---|---|---|
| Identity & Trust Service (FastAPI, database `forkhatri_identity`) | `platform/identity-service/` | 8100 |
| ForKhatri web entrance (Next.js 16.3.5, mobile-first) | `platform/forkhatri-web/` | 3100 |
| Mangaly web / API | `modules/MOD03-mangaly/` | 3000 / 8000 |
| Milavn web / API | `modules/MOD02-milavn/` | 3001 / 8001 |

Development sign-in: `+919800000001` (Asha Reddy, data in Mangaly and Milavn) or
`+919999900001` (Krishna, no module data), password `ForKhatri-dev-2026`.

## Implemented

### Identity & Trust Service
- Canonical member holding basic identity only (name, verified phone/email, language, verification level). `home_locality` was removed by migration 003 under the product-owner rule that profiles live in modules.
- Code sign-in with sign-up folded in, and a password path. Anti-enumeration, resend interval, attempt limits, a database rate limiter, and an `Origin` allow-list.
- One opaque `HttpOnly` session cookie `fk_session`; tokens stored only as SHA-256 digests.
- Module registry and member entry index; internal session-resolve and member-lookup APIs for module services.
- Identity import: 23 active Mangaly accounts (password hashes preserved) and 9 Milavn development identities, merged into 30 members with no conflicts.

### ForKhatri web entrance
- **Sign-in (arrival):** conversational, one question at a time: identifier, then code, then name for new members, with a password alternative; en/hi/te; `return_to` allow-list. Its visual design is the owner-approved first version and was deliberately left unchanged by the hub redesign.
- **Hub (signed in), minimalist redesign after owner review:**
  - Near-black surface with one saffron accent. No glass, glows, gradient orb or mesh background.
  - Greeting and a plain "What would you like to do?" entry that understands intents in en/hi/te.
  - "Open now" list of enterable modules; "Coming to ForKhatri" as compact, screen-reader-announced tiles.
  - Every module is visible on a phone's first screen without scrolling: measured in Chrome at 360×740, the last module ends at 656px.
  - Opens at the top, with a solid header: bell immediately left of the avatar, avatar right-most, no tab bar.
  - Research behind the redesign: `platform/forkhatri-web/DESIGN-NOTES.md`.
- **Devotional emblem:** ForKhatri's own original emblem of Bhagwan Kartavirya Sahasrarjun (`public/assets/devotional/sahasrarjun-emblem.svg`: temple arch, a halo of a thousand arms, mukut, lotus pedestal, no face). It appears beside the greeting on the signed-in hub only, with his name in en/hi/te, and is not interactive. A Wikimedia Commons painting was assessed and not used because its licence claim is doubtful; see `ATTRIBUTION.md`.
- **Account sheet:** name, masked phone/email, language, sign out and sign out on all devices, and a note that module profiles are managed inside each module.
- **Offline state:** cached registry and Retry.

### Modules
- **Mangaly:** interim credential routes return `410 moved_to_forkhatri`; login/sign-up/OTP/reset screens redirect to the entrance. `mangaly_identity.account` is now the member-link table (migration 014, `ensure_platform_account`). Every screen shows a retry state when a service is unreachable. Record: `modules/MOD03-mangaly/AgentOutputs/09-implementation.md`, `v1-decisions.md` DEC-V1-015.
- **Milavn:** the `X-Milavn-Member-Id` development identity is disabled by default; the Identity Bridge resolves `fk_session` (30-second cache, fails closed with 503); the chat WebSocket uses the cookie; there is a way back to the ForKhatri hub. Record: `modules/MOD02-milavn/AgentOutputs/09-implementation.md` IMP25.

## Verification

| Check | Evidence |
|---|---|
| Identity service unit tests | 19 passed |
| Identity service live contract tests | 9 passed against :8100 |
| Entrance browser checks (Playwright) | 100/100, then 51/51 and 24/24 after the final fixes |
| Mangaly | pytest 65 passed; 11/11 live identity checks; 18/18 outage checks |
| Milavn | pytest 15 passed; 19/19 live identity checks |
| Owner walkthrough, Chrome DevTools MCP, 390×844 | Password sign-in sets `fk_session` HttpOnly/SameSite=Lax and it is not readable by JS; enter Mangaly without re-login; signed-out Milavn `/circles` → entrance → back to `/circles`; Milavn API calls carry only the cookie; sign-out → identity and Milavn return 401; signed-out Mangaly `/me` → entrance |
| Hub redesign, Chrome DevTools MCP | 390×844 and 360×740 (all modules above the fold, `scrollY` 0, solid header, no third-party photo loaded, coming-soon list announced); 1440×900 desktop |

## Deployment kit (2026-09-14)

Target: one Oracle Cloud Always Free VM (Ubuntu 24.04 aarch64, 2 OCPU / 12 GB), Cloudflare
Tunnel, one public origin. Owner guide: `deploy/README.md`. Nothing was deployed and no cloud
account was created.

### What was built

| Area | Files | Notes |
|---|---|---|
| Images (linux/amd64 + arm64, non-root, listen on `$PORT`) | `Dockerfile` + `.dockerignore` in `platform/identity-service`, `platform/forkhatri-web`, `modules/MOD03-mangaly/{mangaly-service,mangaly-web}`, `modules/MOD02-milavn/{milavn-service,milavn-web}`; `deploy/migrate/Dockerfile` | `python:3.12-slim-bookworm` / `node:22-alpine`; Next.js `output: "standalone"` only when `NEXT_OUTPUT_STANDALONE=1`; `NEXT_PUBLIC_*` are build args |
| Stack | `deploy/docker-compose.yml`, `deploy/docker-compose.local-test.yml` | Postgres 18 (volume on `/var/lib/postgresql`), migrate job (profile `ops`), 3 services, 3 web zones, Caddy, cloudflared; no published ports; memory limits total 5.1 GB; read-only containers, `no-new-privileges`, `cap_drop: ALL` |
| Edge | `deploy/Caddyfile` | `/`, `/mangaly/*`, `/milavn/*` to zones; `/api/{identity,mangaly,milavn}/*` prefix stripped, services run with `--root-path`; chat WebSocket; `/internal*` and API docs 404; client IP only from `CF-Connecting-IP` |
| Database | `deploy/migrate/migrate.py`, `deploy/migrate/seeds/mangaly-dev.sql` | Any Postgres URL incl. `sslmode=require`; creates six roles and three databases (CONNECT revoked from PUBLIC), applies migrations as owner roles with a SHA-256 ledger (`forkhatri_deploy.applied_migration`), verifies runtime roles own no tables; development seed only with `--seed-dev --i-understand-this-loads-development-data` |
| Secrets | `deploy/secrets/owner-inputs.env.example`, `deploy/.env.production.example`, `deploy/scripts/generate-secrets.sh` | Owner supplies DOMAIN, tunnel token, Resend key, EMAIL_FROM, server IP/user, optional R2 keys; 10 secrets generated (64 hex chars), kept on re-run, `--rotate`, values never printed |
| Server | `deploy/scripts/{server-bootstrap,deploy,remote-release,rollback,compose,backup,restore,heartbeat}.sh` | Bootstrap: Docker, 4 GB swap, UFW SSH-only, SSH keys only, unattended upgrades, cron; deploy over SSH with `~/.ssh/forkhatri_oracle` (tar, no rsync); releases with health checks and automatic fallback; nightly `pg_dump` + media, 14 days on disk, R2 via rclone when configured; restore also from R2 |
| CI | `.github/workflows/deploy.yml` | Manual or push to `main`; never pull requests or forks; secrets SERVER_IP, SERVER_USER, SSH_PRIVATE_KEY (+ SSH_KNOWN_HOSTS) |
| Identity service | `app/components/identity/delivery.py`, `app/config/settings.py`, `app/components/identity/interface.py`, `app/api/routes/internal.py`, `app/main.py` | Resend email provider (challenge id as `Idempotency-Key`); `sms_provider="disabled"` accepted in production; `503 delivery_unavailable` before a challenge is created, and a failed send rolls the challenge back; `LOCAL_HTTP_TEST` rehearsal-only cookie exception; `/internal` answers 404 to requests carrying `X-Forwarded-For`; Origin guard and `no-store` now compare the path without `root_path` |
| Entrance web | `lib/i18n.ts`, `next.config.ts` | `delivery_unavailable` message in en/hi/te |
| Module web apps | Mangaly: `next.config.ts`, `lib/platform.ts`, `components/EntranceRedirect.tsx`. Milavn: `next.config.ts`, `lib/base-path.ts` (new), `lib/api.ts`, `app/a/[slug]/page.tsx`, `app/create/page.tsx`, `components/DetailClient.tsx`, `components/AppChrome.tsx` | `basePath`/`assetPrefix` from `NEXT_PUBLIC_BASE_PATH` (unset in dev); `/assets/...`, share links, QR codes, calendar URLs and `return_to` go through base-path helpers; server-side fetch uses `MILAVN_API_INTERNAL_URL` |
| Contract | `07-tech-reqs.md` | `delivery_unavailable` code, TR19 providers, TR12 rehearsal exception, TR14 edge block, TR22 adopted routing |

### Verification

Docker is not installed on this machine (`docker` not found, no WSL), so images were not built
and Compose was not run. Instead the production topology was rehearsed natively with the same
Caddyfile, production settings and production web builds:

| Check | Evidence |
|---|---|
| Migrations on a fresh Postgres 18 cluster over TLS (`sslmode=require`, port 5499) | 32 files applied; second run applied 0; `--status` 0 pending; runtime roles own 0 of 7 / 61 / 41 tables; `identity_app` refused CONNECT to `mangaly` |
| Development seed | Refused without the confirmation flag; with it: Mangaly and Milavn seeds, 10 platform members, dev sign-in for `+919800000001` and `+919999900001` |
| Production web builds with base paths (isolated copies, `npm ci`, standalone) | Entrance, Mangaly (`/mangaly`) and Milavn (`/milavn`) built with TypeScript passing; ESLint on changed files: 0 errors |
| Caddy 2.11.4 `validate` | Valid. It found two bugs that were fixed before the run: `handle` takes one path, and `handle`/`handle_path` run before `respond` unless wrapped in `route` (the 404 rules had been skipped) |
| Routing through `http://localhost:18080` | Health 200 for all three APIs through their prefixes; `/`, `/mangaly`, `/milavn` 200; all `_next` chunks, fonts, `/milavn/assets/*` and the devotional emblem 200 |
| `/internal` not public | 404 for `/internal/...`, `/api/identity/internal/...`, upper case, `%69nternal`, `%2F`, `//`, `./`, `..`; API docs 404; direct call with `X-Forwarded-For` 404, without it 401 (key checked) |
| Client IP | Rate-limit key used `CF-Connecting-IP` (203.0.113.9); a spoofed `X-Forwarded-For` was ignored |
| Delivery (production mode) | Phone code → `503 delivery_unavailable`; email code → Resend-shaped request (bearer key, idempotency key, six-digit code, no `dev_code` in the response) |
| Browser (Chrome DevTools MCP, isolated context) | Friendly `delivery_unavailable` message shown; password sign-in → hub "Good evening, Asha"; `fk_session` HttpOnly (not visible to JS); Mangaly `/mangaly/me` signed in, no failed requests; Milavn home signed in with avatars and covers from `/milavn/assets`; chat WebSocket `ws://…/api/milavn/ws/chat` opened from the page with the cookie |
| WebSocket script | Cookie + same origin: open; foreign origin: 403; no cookie: 403 |
| Sign-out | Identity, Milavn and Mangaly all 401 on the first poll after sign-out; signed-out `/milavn/circles` and `/mangaly/me` redirect to `/?return_to=…` |
| Identity tests | 37 unit tests (incl. new `test_delivery.py`, `test_origin_guard.py`) + 9 live contract tests through `/api/identity` = 46 passed. The live run found that `--root-path` disabled the TR20 Origin guard (foreign Origin got 200); fixed in `app/main.py`, re-verified 403 in production mode |
| `generate-secrets.sh` (scratch copy) | Missing file and missing keys named; CRLF input accepted; partial R2 rejected; 10 secrets generated, kept on re-run, changed with `--rotate`; no value printed; `--local-test` writes `fk_session`/http |
| Dev servers | 3000, 3001, 3100, 8000, 8001, 8100 answered 200 throughout; rehearsal processes and the temporary cluster stopped afterwards |

Not run: Docker image builds (amd64 or arm64), Compose, cloudflared, Postgres-in-Docker, the
bootstrap/deploy/backup/restore scripts (checked with `bash -n` only), the GitHub workflow, real
Resend sending, and the Oracle VM itself.

### Findings outside this slice

- `modules/MOD03-mangaly/07a-db-implementation/seeds.sql` fails on the current schema
  (migration 005 made `relationship_type` NOT NULL). Left unchanged; the kit uses its own copy.
- Milavn must run as a single process (in-memory chat hub and scheduled jobs).
- Uploaded media stay on Docker volumes (backed up), not object storage.

## Known gaps and open items

- Contract gaps awaiting the owner's decision: password reset/change endpoints, cross-module account deletion, Vyapar read-only browsing during an identity outage, first-time flag in session claims, a platform OTP capability for modules, duplicate language preference in modules, code invalidation on resend, and service-to-service credentials in ARCHITECTURE.md.
- Production composition: module web apps still need `basePath`/`assetPrefix` for Next.js Multi-Zones; cookie must become `__Host-fk_session`; real SMS/email providers and service keys.
- Milavn: roles still come from a JSON file; the old browser scenario scripts use the retired header; light theme shown under a dark system preference.
- Mangaly: the stale `mangaly_session` cookie is not cleared from browsers; old credential tables await a reviewed cleanup migration.
- Devotional emblem: the community may later provide or commission a full devotional painting with written permission.

## Development tools (2026-09-15)

- Identity service `/dev/v1` member switcher, development only and refused by the production guard (`app/dev_tools/`, `07-tech-reqs.md` "Development tools").
- Personas: krishna (owner, never in automated tests), asha, new-member, mangaly-family, mangaly-parent (Lakshmi Reddy, added to the development seed by the Mangaly workstream), milavn-moderator.
- Entrance "Act as (development)" in the account sheet, plus a small link on the sign-in screen; compiled out of production builds (`components/dev/DevActAs.tsx`).
- Test helper `scripts/dev_session.py` writes a Playwright storageState or prints a Cookie header.
- Identity service unit tests: 49 passed (including 12 for the development tools); ruff clean.

