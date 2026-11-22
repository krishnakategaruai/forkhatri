---
project: ForKhatri
artifact: Parent Application Implementation
step: 9
status: As built, updated
updated: 2026-11-22
---

# Parent Application Implementation

Contract: `07-tech-reqs.md`. Decisions and research: `00c-identity-and-entrance-decisions.md`.

## Revision history

| Date | Change |
|---|---|
| 2026-09-13 | Static demo shell in `web/parent-app/` (demo session, no real identity). |
| 2026-09-14 | Real implementation: Identity & Trust Service, ForKhatri web entrance, Mangaly and Milavn moved onto the ForKhatri session. `web/parent-app/` kept as the superseded prototype. |
| 2026-09-14 | Deployment kit for one Oracle Always Free Ampere VM behind a Cloudflare Tunnel (`deploy/`): per-app Dockerfiles, Caddy edge, URL-based migration runner, Resend email delivery and `delivery_unavailable`, env-driven `basePath` in both module web apps, backups to disk and R2, push-to-deploy. Rehearsed natively (no Docker on this machine); nothing deployed. |

## Document status (2026-11-22)

Scope: AS BUILT. This file is the implementation record of the platform (identity service, entrance
and hub, admin console, shared integrations, deployment kit, launchers). Sections dated 2026-09-14
below are kept as history; where they drifted, "As built on 2026-11-22", "Known drift" and
"What is NOT built" say what is true today. Whole-system view: `docs/architecture.md`.
Operations: `docs/RUNBOOK.md`. Terms: `docs/GLOSSARY.md`. Deployment: `docs/ParentApp/DEPLOYMENT.md`.

## As built on 2026-11-22

### Folder structure and key files

| Area | Path | What is in it |
|---|---|---|
| Identity & Trust Service (FastAPI) | `platform/identity-service/` | `app/main.py` (app factory, Origin guard, routers), `app/api/routes/{auth,members,modules,internal,insights,admin}.py`, `app/components/{identity,registry,governance,insights}/`, `app/config/settings.py`, `app/dev_tools/{router,personas}.py`, `app/rate_limiting/`, `db/000-bootstrap.sql`, `db/migrations/001` to `007`, `scripts/{dev_session,seed_dev_members,seed_dev_governance,import_module_identities,build_insight_places}.py`, `tests/` |
| Entrance, hub, admin console, insights (Next.js) | `platform/forkhatri-web/` | `app/` (`page.tsx` arrival and hub, `account`, `admin/*`, `insights`), `components/` (`Arrival`, `Entrance`, `Hub`, `AccountSheet`, `CommandOrb`, `DevotionalPortrait`, `Offline`, `Sheet`, `Splash`, `admin/`, `insights/`, `dev/DevActAs.tsx`), `lib/` (`api`, `i18n`, `intent`, `return-to` with `fk_handoff`, `admin-api`, `admin-i18n`, `insights-i18n`, `theme`), `next.config.ts` |
| Shared integrations (Python, standard library only) | `shared/forkhatri-integrations/forkhatri_integrations/` | `payments`, `messaging`, `delivery`, `places` (OpenStreetMap Nominatim adapter added 2026-10-06), tests, `BACKLOG.md` |
| Launchers | `scripts/dev.mjs`, `scripts/tunnel.mjs`, `scripts/start-tunnels.ps1`, `scripts/check_locale_parity.py` | `npm run dev`, `npm run dev:tunnel`, Windows wrapper for tunnels, locale parity check |
| Deployment kit | `deploy/` | `docker-compose.yml`, `docker-compose.local-test.yml`, `Caddyfile`, `migrate/{Dockerfile,migrate.py,seeds}`, `scripts/*.sh`, `secrets/owner-inputs.env.example`; CI in `.github/workflows/deploy.yml` |

### Identity service API as built (public edge `/api/identity/*`; interactive docs at `/docs` on port 8100 in development)

| Group | Endpoints |
|---|---|
| Sign-in (`/v1/auth`) | `POST /code`, `POST /code/verify`, `POST /welcome`, `POST /password`, `POST /sign-out`, `POST /handoff`, `POST /handoff/redeem` |
| Member (`/v1`) | `GET /session`, `PATCH /me` (name and language only) |
| Registry (`/v1/modules`) | `GET ""`, `POST /{key}/enter` |
| Insights | `GET /v1/insights` (open to every signed-in member) |
| Admin and governance (`/v1/admin`) | `GET /me`, `/overview`, `/members`, `/members/{id}`, `/members/{id}/modules`, `/approvals`, `/roles`, `/org`, `/audit`, `/modules`, `/queues`, `/queues/{module}/{view_id}/{item_id}`; `POST /members/{id}/contact`, `/suspend`, `/lift`, `/sign-out`, `/ban`; `POST /approvals/{id}/decide`; `POST /roles`; `POST /roles/{id}/revoke`; `POST /org/chapters`; `POST /org/chapters/{key}/close`; `POST /queues/{module}/{view_id}/{item_id}/actions/{action_id}`; `PATCH /modules/{key}` |
| Internal (`/internal/v1`, hidden from the edge, service key required) | `POST /sessions/resolve`, `POST /members/provision`, `POST /members/{id}/retire-provisioned`, `POST /members/lookup` |
| Development (`/dev/v1`, development only) | `GET /personas`, `POST /sessions` |
| Ops | `GET /health` |

### Database (`forkhatri_identity`, port 5433 in development)

Schemas `identity` (member, password_credential, otp_challenge, session), `platform` (rate_limit_counter), `registry` (module, member_module_entry), `governance` (chapter, role_assignment, suspension, approval_request, audit_event). Migrations: 001 initial, 002 module registry (reference data), 003 member holds basic identity only, 004 dev auth method, 005 governance, 006 Mangalya display name, 007 Marathi and Kannada. The registry key for Mangalya is still `mangaly` (migration 006 changed only the display name).

### Languages

English, Hindi, Telugu since 2026-09-14; Marathi and Kannada added on 2026-10-06 (migration 007; `docs/LANGUAGES-MR-KN-PLAN.md`). Locale parity is checked by `scripts/check_locale_parity.py`.

### How to run, test, migrate

- Start everything: `npm run dev` (see `docs/RUNBOOK.md`); subsets `npm run dev:platform`, `dev:mangalya`, `dev:milavn`, `dev:vyapar`, `dev:counsel`; status `npm run dev:status`; public tunnels `npm run dev:tunnel` or `scripts/start-tunnels.ps1`.
- Identity tests: `platform/identity-service/.venv/Scripts/python -m pytest platform/identity-service/tests` (unit: `test_delivery`, `test_dev_tools`, `test_identifiers`, `test_origin_guard`, `test_secrets`; integration `test_contract_live` needs the service on 8100, `test_governance_db` needs the database).
- Shared library tests: `shared/forkhatri-integrations/tests`.
- Migrations in production: `deploy/migrate/migrate.py` (idempotent, SHA-256 ledger). In development: each service's own `db/migrations` and each module's `07a-db-implementation/init.sh`.
- Development sign-in for tests: `platform/identity-service/scripts/dev_session.py <persona> --storage-state <file>` or `--cookie-header`.

### Conventions

Environment values are never hardcoded (names in `.env.example`, values in git-ignored `.env`; owner rule 2026-09-27). Python APIs run without `--reload` and are restarted after a change. One ForKhatri sign-in; no module builds its own login. Every user-visible string lives in locale files for en, hi, te, mr, kn; one canonical term per concept (`docs/GLOSSARY.md`).

## Change log

Source: `git log --since=2026-09-01 --stat -- platform shared deploy scripts docs/ParentApp .github` plus owner decisions. The history is coarse (14 commits touch these paths and several are large snapshots), so entries are grouped by commit and by what its diff contains.

| Date | Commit | What changed | Why |
|---|---|---|---|
| 2026-09-13 | f67991a | Parent-app pipeline documents 00 to 08 (scope, architecture, BR, FR, UX, UI, tests, impact) | Start of the platform step set |
| 2026-09-16 | 0c09a7f | Consolidation research drafts under `docs/ParentApp/research/` | Research behind the identity and entrance decisions |
| 2026-09-17 | 639a847 | Deployment kit: `deploy/` (compose, Caddyfile, migrate, scripts, README), `.github/workflows/deploy.yml`, Resend delivery, per-app Dockerfiles; 128 files | One Oracle VM behind a Cloudflare Tunnel; nothing deployed |
| 2026-09-25 | 4348ea3 | Splash screen and app icons on the entrance; devotional portrait tweaks; Mangaly dev seed fix | Entrance polish |
| 2026-09-28 | 19955fd | Members dashboard "ForKhatri in numbers" (`app/insights`, `components/insights`, `GET /v1/insights`, `scripts/build_insight_places.py`) | Owner decision 2026-09-27: aggregate dashboard open to all members |
| 2026-09-29 | 98742b8 | Admin and Governance Console: `app/admin/*`, migration 005, `/v1/admin` API | ADR-012: one console for Samaj heads; Samaj runs ForKhatri (owner direction 2026-10-02) |
| 2026-09-29 | 782706b | MOD03 renamed Mangaly to Mangalya in docs, `.env.example`, `scripts/dev.mjs`; `admin-console.md` added | Owner naming decision. Folders and the registry key were NOT renamed (see drift) |
| 2026-09-29 | 268846d | `.gitignore`; build caches and logs untracked | Production-ready repository |
| 2026-09-29 | fc22700 | `scripts/tunnel.mjs`, `npm run dev:tunnel` | Show the app on phones through Cloudflare Quick Tunnels |
| 2026-10-01 | 20ae38b | Entrance phone type pass; `return_to` and `fk_handoff` sign-in handoff; tunnel-aware `next.config.ts` | The cookie does not cross unrelated tunnel hostnames |
| 2026-10-01 | 692b61f | Shared messaging in identity delivery (`SMS_PROVIDER=shared`, `EMAIL_PROVIDER=shared`); persona `mangalya-family`; launcher changes | Owner direction 2026-10-01: one shared integrations utility |
| 2026-10-06 | 0b65862 | `shared/forkhatri-integrations/places` (Nominatim) | Live India place search for modules |
| 2026-10-06 | (migration 007) | Marathi and Kannada | Owner request, `docs/LANGUAGES-MR-KN-PLAN.md` |
| 2026-10-24 | a8f7747 | Entrance and admin CSS pass, layout; 32 files | Visual polish |
| 2026-11-16 | 9e4e363 | `scripts/start-tunnels.ps1` | One command to start tunnels on Windows |

## Known drift found while documenting (2026-11-22)

1. `scripts/dev.mjs` points MOD03 at `modules/MOD03-mangalya/mangalya-service` and `mangalya-web`, but the folders on disk are `mangaly-service` and `mangaly-web` (only `horoscope-service` matches). `npm run dev` therefore reports Mangalya's API and web as missing and skips them; `scripts/tunnel.mjs` uses the real `mangaly-*` names. Verify with `npm run dev:status`.
2. The production kit (`deploy/docker-compose.yml`, `deploy/scripts/deploy.sh`, `deploy/migrate/migrate.py`, `deploy/migrate/Dockerfile`, `.github/workflows/deploy.yml`) refers to `modules/MOD03-mangaly/...`, a folder that does not exist (the module folder is `MOD03-mangalya`). A deploy as written would fail for Mangalya, and the push-trigger path never matches.
3. The production stack contains only identity, Mangalya, Milavn and three web zones. Vyapar (MOD01) and Counsel (MOD04) have no containers, no `Caddyfile` routes, no databases in `migrate.py` and no service keys in compose, although the registry lists Counsel as `available` and development settings carry keys for both.
4. Identity `services_receiving_identifiers` defaults to `["mangaly"]` only, so provisioning and retiring members is Mangalya-only.
5. Handoff codes live in identity process memory (60 seconds, single use); with more than one identity process a code would be unknown to the other.

## What is NOT built (as of 2026-11-22)

- MOD05 Dashboard (the hub plays part of this role), MOD06 Payment Services and MOD07 Loans and Finance: folders exist but are empty.
- Real vendors: no SMS provider (phone codes return `delivery_unavailable` in production), no WhatsApp, no payment gateway (payments are `none` or a development sandbox). The owner chooses vendors later (`shared/forkhatri-integrations/BACKLOG.md`).
- Password set, reset and change; change of phone or email; second identifier; account deletion and data export; consent records; step-up re-authorisation; device list and new-sign-in alerts; appeal screen for suspensions (`docs/Critique/CRITIQUE-platform.md` C1 to C8).
- Platform notification inbox (the hub bell is an empty state).
- Identity level 2 (ID document) has no code path; level 0 to 1 after a verified code is a reported bug (C4).
- Production has never run: Docker builds, Compose, cloudflared, the VM, and the backup and restore scripts were checked only natively or with `bash -n`.
- GitHub push-to-deploy needs its secrets and one manual first deploy.
- Observability beyond container logs and the 5-minute heartbeat (no metrics, alerting or tracing).

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



## Account deletion (added 2026-11-22)

Change log entry, 2026-11-22: account deletion built across the hub and the four modules, following `ACCOUNT-DELETION.md`. Owner reason: members must be able to erase themselves immediately.

Files changed (platform): `platform/identity-service/db/migrations/008-account-deletion.sql`; the identity account and admin routers, the deletion orchestrator and retry loop in `app/main.py`; `tests/integration/test_account_deletion.py`; `platform/forkhatri-web/components/DeleteAccount.tsx`, `AccountSheet`, the entrance, the admin Modules page (stuck deletions); five locale dictionaries. Module files are listed in each module's `09-implementation.md` and `ACCOUNT-DELETION.md`.

Also on 2026-11-22: `scripts/start-tunnels.ps1` and the tunnel launcher (`scripts/tunnel.mjs`) added; `.gitignore` extended (build caches, test media, pycache, keys, tunnel logs; build info untracked); Mangalya web dev server runs `next dev --webpack` (Turbopack next/font bug caused 500s); the repository was pushed to GitHub on 2026-11-16 (see `DEPLOYMENT.md`).

What is NOT built, deletion-related: grievance officer; consent notice and record; age gate; platform-level data export; sign-up block for banned members; "Deleted member" view of Mangalya one-to-one chats (they are removed for both sides); Counsel payout of unpaid earnings after deletion; any browser check of the deletion screens. The "What is NOT built" list above that names "account deletion" is superseded.
