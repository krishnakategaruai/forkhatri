---
project: ForKhatri
artifact: Parent Application Technical Requirements
step: 7
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Technical Requirements

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
