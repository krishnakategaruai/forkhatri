---
project: ForKhatri
artifact: Parent Application Technical Requirements
step: 7
status: As built (2026-11-22); TR10-TR24 history retained below
updated: 2026-11-22
---

# Parent Application Technical Requirements

> **Document status 2026-11-22, as built.** The TR10-TR24 sections below are the 2026-09-14 contract and remain valid except where the "As-built update" section at the end says otherwise (languages now `en hi te mr kn`; governance, handoff, insights, provisioning endpoints added; `COUNSEL` registered). The complete endpoint list is in [API-REFERENCE.md](API-REFERENCE.md) (43 endpoints); the data model is in [07a-er-model.md](07a-er-model.md); security in [08-security-performance.md](08-security-performance.md).

This file is the single integration contract for the ForKhatri entrance: the
platform Identity & Trust Service, the ForKhatri web entrance, and every module
that accepts the ForKhatri session. Module implementations must not invent a
second shape for anything defined here. Decisions and their research are in
`00c-identity-and-entrance-decisions.md`.

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial static-shell requirements (TR01-TR09). | First reviewable parent slice. |
| 2026-09-14 | Replaced the static demo-session requirements with the real platform identity contract (TR10-TR24). TR01 (dependency-free static shell) is retired: the entrance is now a Next.js app on the same stack as the modules. TR02-TR09 remain and are restated against the real implementation. | Product owner instruction to build one ForKhatri entrance with one identity; `web/parent-app/` is kept as the superseded prototype, not deleted. |
| 2026-09-14 (deployment kit) | Added error code `delivery_unavailable` (`503`, `POST /v1/auth/code`) to TR13; TR19 names the production providers (email via Resend, SMS `disabled` until funded); TR12 notes the `LOCAL_HTTP_TEST` rehearsal-only exception; TR14 adds the edge block and the `X-Forwarded-For` guard on `/internal`; TR22 records the adopted routing (`/api/<service>` prefixes stripped at the edge, env-driven `basePath`). | Production deployment on one Oracle VM behind a Cloudflare Tunnel (`deploy/README.md`). |
| 2026-09-15 | Added "Development tools (development only)": the `/dev/v1` member switcher, named personas, the entrance "Act as" control and the test session helper. | Module teams sign in and out many times while developing, without module-specific logins or typing passwords. |

## Components and development ports

| Component | Path | Dev port | Owns |
|---|---|---|---|
| Identity & Trust Service | `platform/identity-service/` | 8100 | Canonical member, credentials, OTP, sessions, module registry, member→module entry index |
| ForKhatri web entrance | `platform/forkhatri-web/` | 3100 | Sign-in/sign-up, module hub, account sheet, return-to routing |
| Mangaly (existing) | `modules/MOD03-mangaly/` | web 3000, API 8000 | Matrimonial domain; `mangaly_identity.account` becomes Mangaly's member-link table |
| Milavn (existing) | `modules/MOD02-milavn/` | web 3001, API 8001 | Participation domain; `milavn_profile.member_profile` is Milavn's member-link table |
| Vyapar (in development) | `modules/MOD01-vyapar/` | not running | `vyapar.members` is Vyapar's member-link table |

Database: Postgres 18 on `localhost:5433`. The Identity & Trust Service uses
its own database `forkhatri_identity` (ADR-002 isolation), owner role
`identity_owner`, runtime role `identity_app` (non-owning, MODULE-ARCHITECTURE-
STANDARD §4).

## TR10 — One canonical member

`identity.member.id` (uuid) is the only `member_id` on the platform. Every
module stores this value, never its own generated person id.

The platform member holds **basic identity only**: display name, verified phone
and/or email, preferred language, platform verification level and status
(product-owner rule, 2026-09-14). Every profile detail — location, photos, bio,
interests, matrimonial, business or organiser details — lives in the module that
needs it (TR11). The platform does not add profile fields for convenience or to
share them between modules; sharing needs an explicit contract. Existing ids are
preserved on migration: Mangaly `mangaly_identity.account.id` and Milavn dev
member ids become platform member ids unchanged, so no module foreign key is
rewritten.

## TR11 — Module member-link tables stay in modules

A module keeps its own row per member (profile, tier, role, onboarding state)
keyed by `member_id`. The platform never reads or writes module tables. A module
creates its link row lazily the first time a member enters it (just-in-time
provisioning). Module tiers and roles are module data and never appear in the
platform session.

## TR12 — Browser credential: one HttpOnly session cookie

- The browser holds exactly one credential: an opaque session token in the cookie
  named by `SESSION_COOKIE_NAME` (dev `fk_session`; production `__Host-fk_session`).
- Token: 256 bits from a CSPRNG, URL-safe base64. Stored server-side only as its
  SHA-256 digest (`identity.session.token_hash`).
- Attributes: `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` in every deployed
  environment, no `Domain` attribute. Absolute lifetime 30 days.
- No token is ever placed in `localStorage`, `sessionStorage`, a URL, or a
  response body (RFC 10017 / BCP 212).
- `SameSite=Lax` rather than `Strict`: SMS/notification deep links open the app
  through a top-level cross-site navigation, which `Strict` would turn into a
  signed-out view. State-changing requests are additionally protected by TR20.
- Local production rehearsal only: `LOCAL_HTTP_TEST=true` lets a production
  build use `fk_session` without `Secure` over `http://localhost`. It is never
  set on a deployed host, and every other production guard still applies.
- Development note: browsers scope cookies by host, not port, so `localhost:3000`,
  `:3001`, `:3100`, `:8000`, `:8001` and `:8100` all receive `fk_session`. In
  production the zones share one origin (TR22), which gives the same result.

## TR13 — Public identity API (called by the entrance web only)

All bodies are JSON. Errors use `{"detail": {"code": "<stable_code>", "message": "<English fallback>"}}`;
clients localize by `code`. Every call uses `credentials: "include"`.

| Method & path | Auth | Request | Success |
|---|---|---|---|
| `GET /health` | none | — | `{"status":"ok","service":"identity"}` |
| `POST /v1/auth/code` | none | `{"identifier": "9876543210" \| "+919876543210" \| "a@b.in"}` | `202 {"challenge_id","channel":"sms"\|"email","destination_hint","expires_in","resend_in","dev_code"?}` — identical whether or not a member exists; `dev_code` only when `DEV_EXPOSE_OTP=true` |
| `POST /v1/auth/code/verify` | none | `{"challenge_id","code"}` | existing member: `200 {"outcome":"signed_in","member":Member}` + cookie; new identifier: `200 {"outcome":"name_required"}` (challenge marked verified, valid 10 more minutes) |
| `POST /v1/auth/welcome` | none | `{"challenge_id","code","display_name","preferred_language"}` | `201 {"outcome":"signed_in","member":Member}` + cookie; creates the member |
| `POST /v1/auth/password` | none | `{"identifier","password"}` | `200 {"outcome":"signed_in","member":Member}` + cookie. Secondary path for members who set a password and for development testing |
| `POST /v1/auth/sign-out` | cookie | `{"everywhere": false}` | `204`, session(s) revoked, cookie cleared |
| `GET /v1/session` | cookie | — | `200 {"member":Member,"expires_at"}` or `401 not_signed_in` |
| `PATCH /v1/me` | cookie | any of `display_name`, `preferred_language` (other fields → `422 validation_failed`) | `200 Member` |
| `GET /v1/modules` | optional cookie | — | `200 [{"key","name","tagline","availability","entry_url","accent","last_entered_at"}]` (`tagline` in the member's language, else `Accept-Language`, else English) |
| `POST /v1/modules/{key}/enter` | cookie | — | `200 {"entry_url"}`; `409 module_unavailable` unless `availability="available"` |

`Member = {"member_id","display_name","preferred_language","identity_level","phone_hint","email_hint"}`.
Hints are masked (`+91•••••43210`); full identifiers never leave the service on
public endpoints.

Stable error codes: `invalid_identifier`, `rate_limited` (with `Retry-After`),
`code_invalid`, `code_expired`, `code_attempts_exhausted`, `invalid_credentials`,
`not_signed_in`, `module_unavailable`, `module_unknown`, `validation_failed`,
`origin_not_allowed`, `delivery_unavailable` (`503` from `POST /v1/auth/code`
when the identifier's channel cannot deliver a code in this environment, or the
provider failed; decided by channel only, never by whether a member exists; no
challenge is created, so the resend interval is not consumed).

Identifier normalisation: a 10-digit Indian mobile number becomes `+91XXXXXXXXXX`;
any `+`-prefixed number must be E.164; emails are trimmed and lower-cased.

## TR14 — Internal identity API (module services only)

Server-to-server only. In deployment the edge answers `404` for `/internal/*`
and `/api/identity/internal*`, and the service itself answers `404` to any
`/internal` request carrying `X-Forwarded-For` (it came through a proxy).
Authenticated by header `X-ForKhatri-Service: <service_name>`
plus `X-ForKhatri-Service-Key: <secret>`, compared in constant time against
`SERVICE_KEYS`. Never called from a browser; CORS does not apply.

| Method & path | Request | Success |
|---|---|---|
| `POST /internal/v1/sessions/resolve` | `{"session_token"}` | `200 SessionClaims` or `401 session_invalid` |
| `POST /internal/v1/members/lookup` | `{"member_ids": [uuid, …]}` (max 200) | `200 [{"member_id","display_name","identity_level"}]` (unknown ids omitted) |

`SessionClaims = {"member_id","display_name","preferred_language","identity_level","status","session_expires_at","phone_e164"?,"email"?}`.
`phone_e164`/`email` are included only for services listed in
`SERVICES_RECEIVING_IDENTIFIERS` (development: `mangaly`, whose Home Circle
invitations match on identifiers). Data minimisation is the default.

## TR15 — Module session bridge (every module service)

Each module implements resolution inside its own Identity Bridge component and
nowhere else:

1. Read `fk_session` from the request cookie. Absent → anonymous (module decides 401 or public view).
2. Resolve via TR14 with a per-token in-process cache of at most 30 seconds
   (negative results cached 5 seconds). Sign-out therefore reaches every module
   within 30 seconds.
3. Identity service unreachable → fail closed with `503` (never treat as a
   default member).
4. Ensure the module's member-link row exists (TR11), then bind the module's
   own RLS context from `member_id` exactly as today (`SET LOCAL`).
5. A module's legacy development identity path (Milavn `X-Milavn-Member-Id`,
   Mangaly `mangaly_session`) is disabled by default and may only be enabled by
   an explicit development setting for automated tests.

## TR16 — Module web clients

- Send `credentials: "include"` on every API call.
- Signed-out or `401` → full-page navigation to
  `${FORKHATRI_ENTRANCE_URL}/?return_to=${encodeURIComponent(location.href)}`.
- Sign-out → `POST ${IDENTITY_API}/v1/auth/sign-out` then navigate to the entrance.
- Module login, sign-up, OTP and password-reset screens are not rendered; their
  routes redirect to the entrance (files are retained, not deleted).
- Every module surface shows a persistent way back to the ForKhatri hub.

## TR17 — Return-to handling

The entrance follows `return_to` only when its origin equals the entrance origin
or the origin of a registry `entry_url`. Anything else is ignored and the member
lands on the hub (open-redirect prevention).

## TR18 — Module registry

`registry.module` holds `key`, `name`, taglines (`en`/`hi`/`te`), `availability`
(`available` | `in_development` | `planned`), `accent`, `sort_order`. Entry URLs
are environment configuration (`MODULE_ENTRY_URLS`), not database rows.
Initial rows: `mangaly` available, `milavn` available, `vyapar` in development,
`counsel`, `payments`, `finance` planned. Dashboard is the hub itself, not a tile.
`registry.member_module_entry` records first/last entry per member for ordering
and "continue" affordances.

## TR19 — Credentials and one-time codes

- Passwords: Argon2id (`argon2-cffi` defaults). Unknown identifiers run a dummy
  verification so the timing does not reveal account existence.
- OTP: 6 digits, 5-minute expiry, 5 attempts, 30-second resend interval. Stored as
  HMAC-SHA256 keyed by `OTP_PEPPER` over `challenge_id:code`.
- Delivery: development logs the code and may expose `dev_code`. Production:
  `EMAIL_PROVIDER=resend` (Resend HTTP API, challenge id as `Idempotency-Key`)
  and `SMS_PROVIDER=disabled` until an SMS provider is funded, so phone members
  sign in with a password and phone code requests return `delivery_unavailable`.
  The production guard refuses `console` for either channel.

## TR20 — Abuse and request forgery protection

- One shared, database-backed fixed-window rate limiter (MODULE-ARCHITECTURE-
  STANDARD §4c): code requests 5 per identifier / 15 min and 30 per client IP /
  15 min; verification 10 per challenge; password attempts 10 per identifier and
  30 per client IP / 15 min. These are the defaults in every deployed
  environment; a local development `.env` may raise the per-IP and per-member
  values because automated local tests share one IP and two seeded members.
- State-changing requests with an `Origin` header outside `CORS_ALLOWED_ORIGINS`
  are rejected with `403 origin_not_allowed`, in addition to `SameSite=Lax`.
- CORS allows only the entrance and module web origins, with credentials.

## TR21 — ForKhatri web entrance

- Next.js 16.3.5 / React 19.2.8 / TypeScript, same stack as the modules.
- Signed out: identifier → code → (new) name → hub. "Use a password instead"
  secondary path.
- Signed in: module hub rendered from `GET /v1/modules`; entering a module calls
  `POST /v1/modules/{key}/enter` then navigates to `entry_url`.
- Header: notifications bell immediately left of the member avatar; avatar is
  always the right-most item; no tab bar.
- English, Hindi and Telugu interface text (ADR-010).
- Mobile-first, keyboard accessible, `prefers-reduced-motion` honoured.

## TR22 — Production composition: Next.js Multi-Zones

Production serves one origin. The entrance is the default zone (`/`); each
module web app is a zone with its own `basePath` (`/mangaly`, `/milavn`,
`/vyapar`) and `assetPrefix`, routed by the entrance's rewrites or the edge
proxy. Links between zones are plain `<a>` navigations. Development runs the
zones on separate ports with no base path. Adopted in the deployment kit
(2026-09-14): `basePath`/`assetPrefix` come from `NEXT_PUBLIC_BASE_PATH` at build
time (unset in development); the edge (Caddy, `deploy/Caddyfile`) routes `/`,
`/mangaly/*`, `/milavn/*` to the zones and `/api/identity/*`, `/api/mangaly/*`,
`/api/milavn/*` to the services with the prefix stripped (each service runs with
the matching `--root-path`), including the Milavn chat WebSocket and `/media`. Module Federation is not used (the
`@module-federation/nextjs-mf` plugin never supported the App Router and is being
retired).

## TR23 — Migration of existing identities

`platform/identity-service/scripts/import_module_identities.py`:

- Imports every `active` Mangaly account with its id, phone, email and Argon2id
  hash (members keep their password). `pending_verification` accounts are not
  imported: their identifier was never proven.
- Imports Milavn development identities with their ids and names.
- Where both sources hold the same id (development seed data `1111…`, `2222…`),
  the result is one member: identifiers from Mangaly, display name from Milavn.
- Idempotent (`ON CONFLICT DO NOTHING`); prints a reconciliation summary.

## TR24 — Configuration

All secrets and environment-specific values live in `.env` files with
`.env.example` placeholders (`CHANGE_ME`). No module hardcodes the identity URL,
service key, entrance URL or cookie name.

## Development tools (development only)

Never available in production: the identity service mounts the router only when
`ENVIRONMENT=development`, `DEV_TOOLS_ENABLED=true` and `LOCAL_HTTP_TEST` is off, and
its production settings guard refuses to start with `DEV_TOOLS_ENABLED=true`.

| Method & path | Request | Result |
|---|---|---|
| `GET /dev/v1/personas` | — | `[{"key","member_id","display_name","description","for_automated_tests"}]` |
| `POST /dev/v1/sessions` (browser) | `{"persona"}` or `{"member_id"}` | Opens a real session and sets the normal session cookie (TR12); `200 {"outcome":"signed_in","member"}`. The TR20 Origin guard applies. |
| `POST /dev/v1/sessions` (tests) | same, plus header `X-ForKhatri-Dev-Token: <DEV_TOOLS_TOKEN>` (at least 32 characters) | `200` with `session_token`, `cookie_name` and `expires_at` in the body and no cookie. A wrong or short token → `403 dev_token_invalid`; the owner account → `403 owner_reserved`. |

Unknown persona → `404 persona_unknown`.

Personas: `krishna` (product owner's account; people only, never automated tests),
`asha` (data in Mangaly and Milavn), `new-member` (no module data at seed time),
`mangaly-family` (Vikram Rao, Home Circle family member), `mangaly-parent` (Lakshmi
Reddy, Ananya Reddy's mother, not a candidate), `milavn-moderator`.

- Entrance: in a non-production build with `NEXT_PUBLIC_DEV_TOOLS=true`, the account
  sheet shows "Act as (development)", and the sign-in screen shows one small link.
  Production builds compile the component out.
- Tests: `platform/identity-service/scripts/dev_session.py <persona> --storage-state <file>`
  (Playwright) or `--cookie-header` (curl).

## Retained requirements (restated)

- TR02 — the module registry is data-driven (now TR18).
- TR03 — the session adapter is `GET /v1/session` (TR13).
- TR04 — entrance routes: `/` (entry or hub), `/account`; module routes belong to modules.
- TR05 — the hub renders if `/v1/modules` or a module is unavailable (cached registry fallback, clear offline state).
- TR06/TR07 — accessibility and responsive rules (TR21).
- TR08 — no module-specific authentication anywhere (TR15/TR16).
- TR09 — contracts above are the integration boundary.

---

# As-built update (2026-11-22)

Revision row: 2026-11-22, "As-built reference: full endpoint list moved to API-REFERENCE.md; stack, configuration, integrations, caching, rate limiting, i18n, performance budgets recorded from code", reason: owner request that documents match the application as built.

## A1. Endpoints (summary)

Complete reference with request, response, errors, side effects and tables: [API-REFERENCE.md](API-REFERENCE.md). Counts: 39 public (health 1, auth 7, member 2, modules 2, insights 1, admin 24, development 2) plus 4 internal (`sessions/resolve`, `members/provision`, `members/{id}/retire-provisioned`, `members/lookup`). TR13 and TR14 above list only the original subset. Added since: `POST /v1/auth/handoff` and `/handoff/redeem` (cross-host sign-in for tunnels), `GET /v1/insights` (members dashboard, owner decision 2026-09-27), the 24 `/v1/admin/*` governance endpoints (ADR-012), and the internal provisioning and retirement calls (Mangalya parents creating a child's profile, DEC-V1-019; six-month rule 2026-09-21). `admin_scopes` is added to the resolve response.

## A2. Stack and versions

| Part | Version (source) |
|---|---|
| Identity service | Python >=3.12, FastAPI 0.141.1, uvicorn[standard] 0.52.4, Pydantic 2.13.5, pydantic-settings 2.15.0, SQLAlchemy[asyncio] 2.0.52, asyncpg 0.31.0, greenlet 3.5.5, argon2-cffi 25.1.0, httpx 0.28.1, email-validator 2.3.0 (`pyproject.toml`) |
| Identity dev tools | pytest 9.0.1, pytest-asyncio 1.3.0, ruff 0.15.1 (line length 120) |
| Web entrance | Next.js 16.3.5, React and react-dom 19.2.8, TypeScript 5, motion ^13.2.0, d3-geo ^3.1.1, topojson-client ^3.1.0, ESLint 9 (`package.json`); dev port 3100 |
| Database | PostgreSQL 18 (compose image `postgres:18-bookworm`; local psql 18.0), dev port 5433 |
| Edge | Caddy `caddy:2.11-alpine`, `cloudflare/cloudflared:latest` (to be pinned, noted in `.env.production.example`) |
| Hosting | One Oracle Always Free Ampere VM, Docker Compose, Cloudflare Tunnel (`deploy/README.md`) |
| Shared library | `shared/forkhatri-integrations` (standard library only) |

Processes: identity API (uvicorn, default port 8100; production image runs `--proxy-headers --forwarded-allow-ips ${FORWARDED_ALLOW_IPS:-127.0.0.1} --root-path ${ROOT_PATH}`), web entrance (3100), and one background task inside the API process (suspension expiry sweep every 60 s). Run without `--reload` on Windows (an orphaned reloader keeps serving stale code).

## A3. Configuration reference (names only; S marks a secret)

Identity service, `platform/identity-service/app/config/settings.py` (process environment or `.env`; 46 settings fields):

| Name | Default | Purpose |
|---|---|---|
| ENVIRONMENT | development | `development` or `production`; production enables the guard below |
| DB_HOST, DB_PORT, DB_NAME | localhost, 5433, forkhatri_identity | Postgres location |
| DB_APP_USER | identity_app | runtime role |
| DB_APP_PASSWORD (S) | dev placeholder | runtime role password |
| DB_POOL_SIZE | 10 | connection pool |
| API_HOST, API_PORT | 127.0.0.1, 8100 | bind |
| CORS_ALLOWED_ORIGINS | localhost 3100, 3000, 3001, 3011, 3014 | CORS and Origin guard allow-list |
| SESSION_COOKIE_NAME | fk_session | production must start `__Host-` |
| SESSION_COOKIE_SECURE | false | production must be true |
| SESSION_TTL_DAYS | 30 | absolute session lifetime |
| SESSION_COOKIE_DOMAIN | empty | host-only by default; must be unset in production |
| SESSION_COOKIE_SAMESITE | lax | `lax`, `strict`, `none`; `none` refused in production |
| OTP_PEPPER (S) | dev placeholder | HMAC key for codes; at least 32 chars in production |
| OTP_TTL_SECONDS | 300 | code lifetime |
| OTP_MAX_ATTEMPTS | 5 | wrong tries per code |
| OTP_RESEND_SECONDS | 30 | resend interval |
| OTP_VERIFIED_GRACE_SECONDS | 600 | time to finish the name step after verifying a code |
| DEV_EXPOSE_OTP | true | returns `dev_code`; must be false in production |
| SMS_PROVIDER | console | `console`, `disabled`, `shared` |
| EMAIL_PROVIDER | console | `console`, `disabled`, `resend`, `shared` |
| SHARED_SMS_SENDER, SHARED_EMAIL_SENDER | disabled | adapter names in the shared library |
| SMS_DLT_TEMPLATE_ID | empty | India DLT template for the sign-in SMS |
| RESEND_API_KEY (S) | empty | required when EMAIL_PROVIDER=resend |
| RESEND_API_URL | https://api.resend.com/emails | |
| EMAIL_FROM | empty | verified sender, required for resend |
| DELIVERY_TIMEOUT_SECONDS | 10 | provider call timeout |
| LOCAL_HTTP_TEST | false | local production rehearsal only: allows `fk_session` without Secure |
| DEV_TOOLS_ENABLED | false | mounts `/dev/v1` (development only; refused in production) |
| DEV_TOOLS_TOKEN (S) | empty | at least 32 chars; enables test mode |
| RATE_LIMIT_WINDOW_SECONDS | 900 | window |
| RATE_LIMIT_CODE_PER_IDENTIFIER, RATE_LIMIT_CODE_PER_IP | 5, 30 | |
| RATE_LIMIT_VERIFY_PER_CHALLENGE | 10 | |
| RATE_LIMIT_PASSWORD_PER_IDENTIFIER, RATE_LIMIT_PASSWORD_PER_IP | 10, 30 | |
| SERVICE_KEYS (S) | dev placeholders for mangaly, milavn, vyapar, counsel | service name to key; at least 32 chars, no CHANGE_ME in production |
| SERVICES_RECEIVING_IDENTIFIERS | ["mangaly"] | services given phone and email in claims and allowed to provision |
| MODULE_ENTRY_URLS | localhost 3000, 3001, 3011, 3014 | hub entry URLs |
| MODULE_API_URLS | {} (environment only) | modules asked for dashboard facts |
| INSIGHTS_TIMEOUT_SECONDS | 5 | |
| ADMIN_MODULE_API_URLS | {} (environment only) | extra modules federated into the console |
| ADMIN_GATEWAY_TIMEOUT_SECONDS | 8 | |

The table groups some names per row; the full count of distinct settings fields is 46 (`Settings.model_fields`). The Docker image adds `PORT`, `ROOT_PATH`, `FORWARDED_ALLOW_IPS`.

Production guard (`Settings._production_guard`): the service refuses to start when dev tools are on, the cookie is not Secure or lacks the `__Host-` prefix, a cookie domain is set, SameSite is none, `DEV_EXPOSE_OTP` is true, the pepper or any service key is a placeholder or under 32 characters, a provider is `console`, or resend lacks a key or from-address (`LOCAL_HTTP_TEST` relaxes only the cookie rules). It also refuses to start if its database role owns objects.

Deployment, `deploy/.env.production.example` (generated by `deploy/scripts/generate-secrets.sh`): owner inputs DOMAIN, CLOUDFLARE_TUNNEL_TOKEN (S), RESEND_API_KEY (S), EMAIL_FROM, optional R2_ACCOUNT_ID, R2_ACCESS_KEY_ID (S), R2_SECRET_ACCESS_KEY (S), R2_BUCKET; derived PUBLIC_ORIGIN, PUBLIC_SCHEME; SESSION_COOKIE_NAME, SESSION_COOKIE_SECURE, LOCAL_HTTP_TEST; SMS_PROVIDER, EMAIL_PROVIDER; generated secrets POSTGRES_PASSWORD, IDENTITY_OWNER_PASSWORD, IDENTITY_APP_PASSWORD, MANGALY_OWNER_PASSWORD, MANGALY_APP_PASSWORD, MILAVN_OWNER_PASSWORD, MILAVN_APP_PASSWORD, OTP_PEPPER, MANGALY_SERVICE_KEY, MILAVN_SERVICE_KEY (all S); operations COMPOSE_PROJECT_NAME, RELEASE_ID, BACKUP_KEEP_DAYS, POSTGRES_IMAGE, CADDY_IMAGE, CLOUDFLARED_IMAGE. That is 31 names. The production example holds service keys for Mangalya and Milavn only; Vyapar and Counsel are not in the deployed kit (CRITIQUE architecture C2).

Web entrance (`platform/forkhatri-web`): `NEXT_PUBLIC_IDENTITY_API` (identity base URL; rewritten by the tunnel script in development), `NEXT_PUBLIC_DEV_TOOLS` (shows "Act as"; development only), `NEXT_PUBLIC_BASE_PATH` (zone base path, build time; unset in development), `TUNNEL_DEV_ORIGIN` (set by `npm run dev:tunnel`), `NEXT_OUTPUT_STANDALONE`, `NEXT_DIST_DIR`, `PORT`, `PLAYWRIGHT_PATH` (e2e script): 8 names. Defaults of the build-time names are unverified (read from code only).

Total names inventoried: 46 identity + 31 deployment + 8 web = 85.

## A4. Integrations

| Integration | Direction | Notes |
|---|---|---|
| Resend (email codes) | out, HTTPS | `EMAIL_PROVIDER=resend`; challenge id as `Idempotency-Key`; the production email path today |
| Shared messaging (`forkhatri_integrations.messaging`) | out | `SMS_PROVIDER=shared` or `EMAIL_PROVIDER=shared`; adapters `console` (dev only) and `disabled` exist; no SMS vendor connected, owner picks later (owner direction 2026-10-01); see `shared/forkhatri-integrations/BACKLOG.md` |
| Module APIs, dashboard | out, HTTPS | `GET /v1/insights` asks each `MODULE_API_URLS` module for facts with that module's service key |
| Module APIs, admin federation | out, HTTPS | gateway forwards the admin's session token and language to module admin views (queues, member summaries, actions) |
| Module services | in | `/internal/v1/*` with service keys |
| Cloudflare Tunnel and Caddy | edge | strips `/api/identity`, blocks `/internal*` and docs |
| Postgres backups to Cloudflare R2 | out | optional (`R2_*`); nightly dump (`deploy/scripts/backup.sh`) |

Not built: any real SMS or WhatsApp vendor, push, passkeys, DigiLocker. The platform does no payments.

## A5. Caching

Server responses carry `no-store`. In-process caches: governance gateway manifest cache keyed by module and language (TTL constant `_MANIFEST_TTL_SECONDS` in `gateway.py`); `lru_cache` for settings and the insights place tables; handoff codes in memory (60 s). Module services cache session resolution per token for at most 30 s (negative 5 s) (TR15), the accepted sign-out delay. The hub's cached public registry fallback (TR05) is a design statement; verify in web code.

## A6. Rate limiting

See API-REFERENCE section 8: database-backed fixed window, five buckets plus a resend interval. Not limited: handoff, admin, internal, insights, `PATCH /v1/me`, module enter.

## A7. Internationalisation

Languages `en`, `hi`, `te`, `mr`, `kn` (Marathi and Kannada added 2026-10-06, migration 007). The server returns stable error codes with English fallback messages; the web localises by code. Module taglines are stored per language with English fallback. Owner rules: every Telugu and Hindi string accurate and respectful; no hardcoded user-visible strings. Open: human review of Hindi in the admin console (CRITIQUE-platform C13).

## A8. Performance budgets

Recorded targets (08-security-performance.md): availability 99.9% monthly, RPO <= 5 min, RTO <= 1 h (the critique notes the deployed nightly backup does not yet meet this), at most one internal resolve call per module per 30 s per member. No per-endpoint latency budget is written (gap). Suggested working budgets, unverified and for the owner to adopt: public auth endpoints p95 under 300 ms excluding provider delivery; internal session resolve p95 under 50 ms; `GET /v1/insights` under 2 s (module timeouts are 5 s each).

## A9. Observability and errors

Python logging at INFO (`identity`, `identity.delivery`); codes and full destinations are never logged, only masked hints. No metrics, tracing or error tracker (CRITIQUE architecture M2). Health: `GET /health` (checks the DB). Error model: API-REFERENCE section 1.

## A10. Run, test and migrate

Run: `platform/identity-service/.venv/Scripts/python -m uvicorn app.main:app --port 8100` (no `--reload`), or the one start-all command. Migrate: `db/000-bootstrap.sql` as superuser, then `db/migrations/*.sql` in order as `identity_owner`; production uses `deploy/migrate`. Tests in `platform/identity-service/tests`: test_delivery, test_dev_tools, test_identifiers, test_origin_guard, test_secrets (unit); `integration/test_contract_live.py`, `integration/test_governance_db.py`. Scripts in `scripts/`: `dev_session.py`, `seed_dev_members.py`, `seed_dev_governance.py`, `import_module_identities.py`, `build_insight_places.py`.
