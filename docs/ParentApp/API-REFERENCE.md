# ForKhatri Identity & Trust Service: API reference

**Document status 2026-11-22, as built.** Source of truth: the running service (`GET http://localhost:8100/openapi.json`, 39 public operations) plus `platform/identity-service/app/api/routes/*.py`, `app/api/deps.py`, `app/main.py`, `app/errors.py`. The four internal routes are hidden from OpenAPI (`include_in_schema=False`) and were read from `routes/internal.py`. Contract narrative: [07-tech-reqs.md](07-tech-reqs.md). Data: [07a-er-model.md](07a-er-model.md). Security: [08-security-performance.md](08-security-performance.md).

Inventory: 39 public + 4 internal = 43 endpoints (of which 2 are development-only), grouped below.

| Group | Count |
|---|---|
| Ops (`/health`) | 1 |
| Auth (`/v1/auth/*`) | 7 |
| Member (`/v1/session`, `/v1/me`) | 2 |
| Modules (`/v1/modules*`) | 2 |
| Insights (`/v1/insights`) | 1 |
| Admin (`/v1/admin/*`) | 24 |
| Development (`/dev/v1/*`, dev only) | 2 |
| Internal (`/internal/v1/*`, service to service) | 4 |

## Contents
1. Conventions (base URLs, cookie, error model, rate limits, headers)
2. Ops and auth
3. Member, modules, insights
4. Admin and governance
5. Internal (module services)
6. Development tools
7. Error code catalogue
8. Rate-limit bucket catalogue

## 1. Conventions

- **Base URL.** Development `http://localhost:8100`. Deployed: one origin, service reached at `/api/identity/*` (edge strips the prefix; service runs with `--root-path /api/identity`). The deployed edge answers 404 for `/api/identity/internal*`.
- **Format.** JSON in and out. Browser calls use `credentials: "include"`.
- **Authentication.** Browser endpoints: one opaque session token in the cookie named by `SESSION_COOKIE_NAME` (`fk_session` in development, `__Host-fk_session` in production), resolved by `deps.get_current_session` (digest lookup in `identity.session`, requires `revoked_at IS NULL`, `expires_at > now()`, member `status = 'active'`). "Cookie" below means that. "Optional cookie" means anonymous callers are accepted. Internal endpoints: headers `X-ForKhatri-Service` and `X-ForKhatri-Service-Key` (constant-time compare against `SERVICE_KEYS`). Admin endpoints additionally need an administrative role (`admin_forbidden` 403 otherwise).
- **Error model.** Every failure is `{"detail": {"code": "<stable_code>", "message": "<English fallback>", ...extras}}`; clients localise by `code`. Three producers: `DomainError(code, message, status)` (`app/errors.py`); `RateLimitExceeded` (429, `code=rate_limited`, extra `retry_after` seconds, header `Retry-After`); `RequestValidationError` (422, `code=validation_failed`, extra `fields` = list of dotted field names). The Origin guard returns 403 `origin_not_allowed`. Unknown internal path through a proxy returns a bare FastAPI 404 (`{"detail":"Not Found"}`), the one error not in the model.
- **Origin guard** (middleware, TR20): any `POST/PUT/PATCH/DELETE` to `/v1/*` or `/dev/v1/*` carrying an `Origin` header not in `CORS_ALLOWED_ORIGINS` returns 403 `origin_not_allowed` (requests with no Origin, such as server-to-server, pass). Applies to every write endpoint below; not repeated per row.
- **Caching.** `Cache-Control: no-store` on every `/v1/*`, `/internal/*`, `/dev/*` response. `/health` is not marked.
- **CORS.** Origins from `CORS_ALLOWED_ORIGINS`, credentials allowed, methods `GET, POST, PATCH, OPTIONS`, headers `Content-Type, Accept-Language`; `Retry-After` exposed. Note: `X-ForKhatri-Dev-Token` is not in `allow_headers`, so the test-mode token header is for non-browser callers only.
- **Transactions.** Each request has one DB session (`get_db`), committed on success, rolled back on exception. Auth write paths commit before the cookie is set. Rate-limit hits commit in their own short transaction so failed attempts still count.
- **Language.** Public `GET /v1/modules` uses member language, else `Accept-Language` (first two letters), else `en`. Admin endpoints use `Accept-Language` if supported, else the member's language. Supported: `en hi te mr kn`.
- **Versioning.** URL prefix `/v1`; service version string `0.1.0`. No deprecation policy is written (gap).
- **Member object** (`Member.public()`): `member_id, display_name, preferred_language, identity_level, phone_hint, email_hint` (masked, e.g. `+91•••••43210`).

## 2. Ops and auth

### API-GET-health
`GET /health`. Auth none. Response `200 {"status":"ok","service":"identity"}`. Runs `SELECT 1` (a DB outage gives 500). Tables: none. Used by `RUNBOOK`/deploy health checks.

### API-POST-v1-auth-code
`POST /v1/auth/code`. Auth none. Request `{identifier: string 3-254}` (10-digit Indian mobile, `+`E.164, or email). Response `202 {challenge_id, channel: "sms"|"email", destination_hint, expires_in, resend_in, dev_code?}` (`dev_code` only when `DEV_EXPOSE_OTP=true`).
- Errors: `invalid_identifier` 422; `delivery_unavailable` 503 (channel off or provider failed; decided by channel only, never by member existence; the challenge is rolled back); `rate_limited` 429 (code per IP, code per identifier, or resend interval `OTP_RESEND_SECONDS`); `validation_failed` 422.
- Rate limits: buckets `code:ip:<ip>` (30 per 900 s), `code:id:<identifier>` (5 per 900 s), plus resend interval 30 s measured from the latest challenge for that identifier.
- Side effects: inserts one `identity.otp_challenge` (HMAC of code, never the code); sends the code via the channel provider (console log, Resend HTTP, or shared messaging adapter) before commit.
- Tables: `identity.otp_challenge` (R/W), `platform.rate_limit_counter` (W). Anti-enumeration: same 202 whether or not a member exists.

### API-POST-v1-auth-code-verify
`POST /v1/auth/code/verify`. Auth none. Request `{challenge_id: uuid, code: 6 digits}`. Response `200 {"outcome":"signed_in","member"}` plus `Set-Cookie`, or `200 {"outcome":"name_required"}` when the identifier belongs to no member (challenge marked `verified_at`, expiry extended by `OTP_VERIFIED_GRACE_SECONDS`).
- Errors: `code_invalid` 400; `code_expired` 400; `code_attempts_exhausted` 400; `account_unavailable` 403 (suspended/deleted member); `rate_limited` 429; `validation_failed` 422.
- Rate limit: `verify:<challenge_id>` 10 per 900 s; each wrong code also increments `attempt_count` against `max_attempts` (5).
- Side effects: marks challenge verified/consumed; creates `identity.session` (`auth_method='otp'`, user-agent truncated to 300 chars); cookie `HttpOnly`, `SameSite` per `SESSION_COOKIE_SAMESITE`, `Secure` per `SESSION_COOKIE_SECURE`, `Path=/`, `Max-Age = SESSION_TTL_DAYS*86400`, `Domain` only if `SESSION_COOKIE_DOMAIN` set.
- Tables: `otp_challenge` (R/W), `member` (R), `session` (W), `rate_limit_counter` (W).

### API-POST-v1-auth-welcome
`POST /v1/auth/welcome`. Auth none. Request `{challenge_id, code, display_name: 1-80 trimmed, preferred_language: en|hi|te|mr|kn = en}`. Response `201 {"outcome":"signed_in","member"}` plus cookie. Creates the member for a new identifier.
- Errors: `code_invalid` (including "Verify the code before continuing" when the challenge was never verified), `code_expired`, `code_attempts_exhausted`, `account_unavailable` 403, `rate_limited`, `validation_failed`.
- Side effects: INSERT `identity.member` (phone or email, `identity_level` default 1), challenge consumed, session opened (`otp`).
- Tables: `member` (W), `otp_challenge` (W), `session` (W), `rate_limit_counter` (W). Same `verify:` bucket as verify.

### API-POST-v1-auth-password
`POST /v1/auth/password`. Auth none. Request `{identifier 3-254, password 1-256}`. Response `200 {"outcome":"signed_in","member"}` plus cookie.
- Errors: `invalid_credentials` 401 (identical for unknown identifier, wrong password, bad format, inactive member; unknown identifiers still run one dummy Argon2id verify); `rate_limited` 429; `validation_failed` 422.
- Rate limits: `password:ip:<ip>` 30, `password:id:<identifier>` 10, per 900 s.
- Side effects: opens session (`auth_method='password'`); silently rehashes if Argon2 parameters changed.
- Tables: `member` (R), `password_credential` (R, W on rehash), `session` (W), `rate_limit_counter` (W). Note: no endpoint creates or changes a password (known gap; passwords exist only from imports and seeds).

### API-POST-v1-auth-sign-out
`POST /v1/auth/sign-out`. Auth optional cookie. Request optional `{everywhere: bool=false}`. Response `204`, cookie cleared. Always 204 even when signed out.
- Side effects: `everywhere=false` revokes the presented session; `true` revokes every unrevoked session of that member. Modules notice within their resolve cache (up to 30 s).
- Tables: `identity.session` (W).

### API-POST-v1-auth-handoff
`POST /v1/auth/handoff`. Auth cookie. No body. Response `200 {code, expires_in: 60}`. For hub-to-module sign-in across unrelated hosts (tunnels). Code is 32 random bytes URL-safe.
- Errors: `not_signed_in` 401.
- Side effects: stores `code -> session token` in process memory for 60 s (monotonic clock). Tables: none. Limitation: in-memory, so it works only with one service process and is lost on restart; no rate limit.

### API-POST-v1-auth-handoff-redeem
`POST /v1/auth/handoff/redeem`. Auth none (the code is the credential). Request `{code: 16-128 chars}`. Response `200 {"outcome":"signed_in","member"}` plus a session cookie with the same token and the remaining lifetime.
- Errors: `handoff_invalid` 401 (unknown, used, expired, or underlying session gone); `validation_failed` 422.
- Side effects: single use (popped on first try). Tables: `session`, `member` (R via resolve). No rate limit on guesses (32-byte code makes guessing infeasible; flagged in 08).

## 3. Member, modules, insights

### API-GET-v1-session
`GET /v1/session`. Cookie. Response `200 {member, expires_at (ISO)}`. Errors: `not_signed_in` 401. Side effect: `last_seen_at` refreshed if older than 5 minutes. Tables: `session` (R/W), `member` (R).

### API-PATCH-v1-me
`PATCH /v1/me`. Cookie. Request any of `{display_name: <=80, preferred_language: en|hi|te|mr|kn}`; extra fields rejected. Response `200 Member`.
- Errors: `validation_failed` 422 (empty value, unknown field, bad language), `not_signed_in` 401. Side effects: UPDATE `identity.member` and `updated_at`. Tables: `member` (W). Phone and email cannot be changed (known gap).

### API-GET-v1-modules
`GET /v1/modules`. Optional cookie. Response `200 [{key, name, tagline, availability, entry_url|null, accent, last_entered_at|null}]` ordered by `sort_order`. `tagline` is `COALESCE(tagline_<lang>, tagline_en)`; `entry_url` only when `available`, from `MODULE_ENTRY_URLS`. Tables: `registry.module` (R), `registry.member_module_entry` (R). Current rows: 6.

### API-POST-v1-modules-key-enter
`POST /v1/modules/{key}/enter`. Cookie. `key` pattern `^[a-z][a-z0-9_]{1,30}$` (else 422). Response `200 {entry_url}`.
- Errors: `module_unknown` 404; `module_unavailable` 409 (not `available` or no entry URL configured); `not_signed_in` 401.
- Side effects: upsert `registry.member_module_entry` (`last_entered_at`, `entry_count + 1`). Tables: `module` (R), `member_module_entry` (W).

### API-GET-v1-insights
`GET /v1/insights`. Cookie (any signed-in member; owner decision 2026-09-27). Response: aggregate dashboard (member totals, joined/not yet joined, suspended, language, city/state/country, gender and age bands via module facts). Never a person. Calls each module in `MODULE_API_URLS` server to server with its service key (timeout `INSIGHTS_TIMEOUT_SECONDS`); a module not configured or unreachable is reported as `ok:false` with an error, and the page shows missing numbers. Tables: `member` (R), `session` (R, max `last_seen_at`), `member_module_entry` (R). Open critique: small cells identify people (CRITIQUE-platform C9).

## 4. Admin and governance (24 endpoints)

Common: Cookie required. Every endpoint except `GET /v1/admin/me` also needs an administrative role, else `admin_forbidden` 403 ("The admin console is for people the samaj has appointed."). Roles and permissions: see the matrix in [08-security-performance.md](08-security-performance.md) and `app/components/governance/roles.py`. Every mutation writes `governance.audit_event` (append-only; action in brackets). Body models forbid unknown fields (`validation_failed` 422). No rate limits are applied on admin endpoints (gap). Common errors from the governance layer: `note_required` 422 (note under a few characters), `reason_unknown` 422, `member_unknown` 404, `admin_self_action` 403, `admin_target_owner` 403, `admin_target_staff` 403.

| ID | Method path | Permission | Request | Response | Side effects, tables | Specific errors |
|---|---|---|---|---|---|---|
| API-GET-v1-admin-me | `GET /v1/admin/me` | any signed-in member | none | `{is_admin, member, roles, permissions, module_scopes, managed_chapters, catalogue|null}` (catalogue: roles, reason codes, suspension days, only for admins) | R `role_assignment`, `chapter` | |
| API-GET-v1-admin-overview | `GET /v1/admin/overview` | any admin | none | "Today" counts: what needs attention | R member, suspension, approval_request | |
| API-GET-v1-admin-members | `GET /v1/admin/members?q&status&limit=30&offset=0` | `members.view` or a chapter head | `q` <=80, `status` <=20 | `{members[], total...}` contact masked | R member | `admin_forbidden` |
| API-GET-v1-admin-members-member_id | `GET /v1/admin/members/{member_id}` | `members.view` | uuid | one person across the platform | R member, session, entries, suspension, roles | `member_unknown` |
| API-GET-v1-admin-members-member_id-modules | `GET /v1/admin/members/{member_id}/modules` | `members.view` | uuid | each module's own view (tier, flags) via federation gateway; forwards the admin's session token | HTTP to module `admin` APIs (`ADMIN_MODULE_API_URLS`, timeout `ADMIN_GATEWAY_TIMEOUT_SECONDS`) | `module_unreachable` 502, `module_refused` |
| API-POST-v1-admin-members-member_id-contact | `POST /v1/admin/members/{member_id}/contact` | `members.contact` | `{note}` (reason required) | full phone and email | audit `[member.contact_viewed]` incl. IP | `note_required` |
| API-POST-v1-admin-members-member_id-suspend | `POST .../suspend` | `members.suspend` | `{reason_code<=40, days: 1|3|7|30|null(open), note}` | updated member status | INSERT `suspension` (lifts any open one first); `member.status='suspended'`; revokes all sessions; audit `[member.suspended]` | `validation_failed` (length), `member_banned` 409, `member_deleted` 409 |
| API-POST-v1-admin-members-member_id-lift | `POST .../lift` | `members.suspend` (a ban also needs `approvals.decide`) | `{note}` | member | closes suspension; status back to `active`; audit `[member.suspension_lifted]` or `[member.ban_lifted]` | `not_suspended` 409 |
| API-POST-v1-admin-members-member_id-sign-out | `POST .../sign-out` | `members.suspend` | `{note}` | result | revokes every session; audit `[member.signed_out]` | |
| API-POST-v1-admin-members-member_id-ban | `POST .../ban` | `members.ban` | `{reason_code, note}` | pending approval | INSERT `approval_request(kind=ban)`; audit; a second person must decide | `approval_exists` 409, `member_banned` 409, `admin_target_owner` |
| API-GET-v1-admin-approvals | `GET /v1/admin/approvals?status=pending` | `approvals.decide` or `members.ban` or `roles.manage` | status in pending/approved/declined/withdrawn | list with `can_decide` flag (not requester, not target) | R approval_request | `admin_forbidden` |
| API-POST-v1-admin-approvals-approval_id-decide | `POST /v1/admin/approvals/{approval_id}/decide` | `approvals.decide` (withdraw: requester only) | `{decision: approved|declined|withdrawn, note}` | approval | approved ban: INSERT `suspension(kind=ban)`, status suspended, sessions revoked; approved grant: creates `role_assignment`; audit | `approval_unknown` 404, `approval_closed` 409, `approval_four_eyes` 403, `admin_self_action` |
| API-GET-v1-admin-roles | `GET /v1/admin/roles?include_ended=false` | `roles.view` or chapter head | | assignments | R role_assignment | `admin_forbidden` |
| API-POST-v1-admin-roles | `POST /v1/admin/roles` | `roles.manage` or `chapter.manage` (own chapter) | `{member_id, role<=40, scope_key?, title?<=60, ends_at?, note}` | assignment, or a pending approval for sensitive roles | INSERT `role_assignment` or `approval_request(kind=grant_role)`; audit `[role.granted]` | `role_unknown`, `scope_unknown`, `role_exists` 409, `member_inactive` 409, `admin_self_action`, `admin_forbidden` (owner appoints owner) |
| API-POST-v1-admin-roles-assignment_id-revoke | `POST /v1/admin/roles/{assignment_id}/revoke` | `roles.manage` or `chapter.manage` | `{note}` | assignment | sets `revoked_at/by/note`; audit `[role.revoked]` | `role_unknown` 404, `last_owner` 409, `admin_forbidden` |
| API-GET-v1-admin-org | `GET /v1/admin/org` | `org.view` | | office bearers, chapters | R chapter, role_assignment | |
| API-POST-v1-admin-org-chapters | `POST /v1/admin/org/chapters` | `org.manage` or `chapter.manage` | `{name<=80, kind: state|city, parent_key?}` | chapter | INSERT `chapter` (key slug of name); audit `[org.chapter_created]` | `chapter_exists` 409, `scope_unknown`, `validation_failed` |
| API-POST-v1-admin-org-chapters-key-close | `POST /v1/admin/org/chapters/{key}/close` | `org.manage` | `{note}` | chapter | sets `archived_at`; audit `[org.chapter_closed]` | `chapter_has_children` 409, `chapter_has_bearers` 409, `scope_unknown` 404 |
| API-GET-v1-admin-audit | `GET /v1/admin/audit?actor&target&action&module&before&limit=50` | `audit.view` | filters | audit rows, newest first, `before` = id cursor | R audit_event | |
| API-GET-v1-admin-modules | `GET /v1/admin/modules` | any admin | | module registry | R registry.module | |
| API-PATCH-v1-admin-modules-key | `PATCH /v1/admin/modules/{key}` | `modules.manage` | `{availability: available|in_development|planned, note}` | registry | UPDATE `registry.module.availability`; audit `[module.availability_changed]` | `scope_unknown` 404, `validation_failed` |
| API-GET-v1-admin-queues | `GET /v1/admin/queues` | any admin | | every module queue the admin is appointed to (federated manifests, cached `_MANIFEST_TTL_SECONDS`) | HTTP to modules | `module_unreachable` 502 |
| API-GET-v1-admin-queues-module-view_id-item_id | `GET /v1/admin/queues/{module}/{view_id}/{item_id}` | module scope | | one item | HTTP to module | `module_unknown` 404, `view_unknown` 404, `admin_forbidden`, `module_refused` |
| API-POST-v1-admin-queues-module-view_id-item_id-actions-action_id | `POST .../actions/{action_id}` | module scope | `{notes<=1000, reason_code<=40}` | module's answer | HTTP POST to module; audit `[queue.action]` with module, view/item | `view_read_only` 409, `module_refused`, `module_unreachable` |

Notes. The `contact` reveal is the only way full identifiers leave the service to a browser. Suspension and ban both set `member.status='suspended'`, which makes `resolve_session` fail everywhere at once (every module closes). A background task ends dated suspensions every 60 seconds (`expire_due_suspensions`, audit `[member.suspension_ended]`). Audit action names also include `member.suspension_lifted`, `member.ban_lifted` (above).

## 5. Internal endpoints (module services only)

Prefix `/internal/v1`, tag `internal`, hidden from OpenAPI. Two guards: (1) `not_through_the_edge`: a request carrying `X-Forwarded-For` gets a bare 404; (2) `authenticated_service`: headers `X-ForKhatri-Service` and `X-ForKhatri-Service-Key` compared in constant time against `SERVICE_KEYS`, else `service_unauthorized` 401. Identifier-bearing calls need the service to be in `SERVICES_RECEIVING_IDENTIFIERS` (default `mangaly`), else `service_forbidden` 403. No rate limits.

| ID | Method path | Request | Response | Errors | Side effects, tables |
|---|---|---|---|---|---|
| API-POST-internal-v1-sessions-resolve | `POST /internal/v1/sessions/resolve` | `{session_token 1-128}` | `200 SessionClaims`: `member_id, display_name, preferred_language, identity_level, status, session_expires_at`, plus `phone_e164`/`email` only for identifier-trusted services, plus `admin_scopes` (module permissions appointed in the console, e.g. `milavn.moderate`) | `session_invalid` 401, `service_unauthorized` 401 | `last_seen_at` refresh; R session, member, role_assignment |
| API-POST-internal-v1-members-provision | `POST /internal/v1/members/provision` | `{phone 6-32, display_name 1-80, preferred_language en|hi|te|mr|kn}` | `201 {member_id, phone_e164}` | `service_forbidden` 403, `member_exists` 409, `identifier_invalid` 422 | INSERT `member` at `identity_level=0`, no credential, no session; an untouched earlier provisioned member is handed back |
| API-POST-internal-v1-members-member_id-retire-provisioned | `POST /internal/v1/members/{member_id}/retire-provisioned` | uuid | `{removed: bool}` | `service_forbidden` 403 | DELETE `member` only if level 0, no password, no session (six-month rule, owner 2026-09-21). **Finding:** the live `identity_app` role holds no DELETE privilege on `identity.member`, so this statement is expected to fail with a permission error. Unverified by calling it; verify with a throwaway provisioned member in a test database. |
| API-POST-internal-v1-members-lookup | `POST /internal/v1/members/lookup` | `{member_ids: uuid[] max 200}` | `[{member_id, display_name, identity_level}]` active members only, unknown ids omitted | | R member |

## 6. Development tools (mounted only when `ENVIRONMENT=development`, `DEV_TOOLS_ENABLED=true`, `LOCAL_HTTP_TEST` off; production refuses to start with the flag on)

### API-GET-dev-v1-personas
`GET /dev/v1/personas`. Auth none. Response `[{key, member_id, display_name, description, for_automated_tests}]` for personas whose member exists. Personas (code `app/dev_tools/personas.py`): `krishna`, `asha`, `new-member`, `mangaly-family`, `mangaly-parent`, `milavn-moderator` (see CLAUDE.md). Tables: `member` (R).

### API-POST-dev-v1-sessions
`POST /dev/v1/sessions`. Request exactly one of `{persona}` or `{member_id}`. Browser mode (no token header): opens a session (`auth_method='dev'`), revokes the browser's previous session (this device only), sets the cookie, returns `{outcome, member}`. Test mode (header `X-ForKhatri-Dev-Token` equal to `DEV_TOOLS_TOKEN`, at least 32 chars): no cookie, body carries `session_token, cookie_name, expires_at`.
- Errors: `dev_token_invalid` 403; `persona_unknown` 404; `owner_reserved` 403 (test mode never acts as the owner account); `member_unknown` 404; `validation_failed` 422. Origin guard applies. Tables: `session` (W), `member` (R).

## 7. Error code catalogue

Auth and member: `invalid_identifier` 422, `delivery_unavailable` 503, `rate_limited` 429, `code_invalid` 400, `code_expired` 400, `code_attempts_exhausted` 400, `account_unavailable` 403, `invalid_credentials` 401, `not_signed_in` 401, `handoff_invalid` 401, `origin_not_allowed` 403, `validation_failed` 422 (extra `fields`). Modules: `module_unknown` 404, `module_unavailable` 409. Internal: `service_unauthorized` 401, `service_forbidden` 403, `session_invalid` 401, `member_exists` 409, `identifier_invalid` 422. Dev: `dev_token_invalid` 403, `persona_unknown` 404, `owner_reserved` 403, `member_unknown` 404. Admin: `admin_forbidden` 403, `admin_self_action` 403, `admin_target_owner` 403, `admin_target_staff` 403, `note_required` 422, `reason_unknown` 422, `member_unknown` 404, `member_deleted` 409, `member_banned` 409, `not_suspended` 409, `member_inactive` 409, `approval_exists` 409, `approval_unknown` 404, `approval_closed` 409, `approval_four_eyes` 403, `role_unknown` 422/404, `role_exists` 409, `scope_unknown` 422/404, `last_owner` 409, `chapter_exists` 409, `chapter_has_children` 409, `chapter_has_bearers` 409, `view_unknown` 404, `view_read_only` 409, `module_unreachable` 502, `module_refused` (module's status), plus gateway-derived codes. Total: 46 distinct codes.

## 8. Rate-limit bucket catalogue

All fixed window `RATE_LIMIT_WINDOW_SECONDS` (900), stored in `platform.rate_limit_counter` (key, window start). Old rows are purged opportunistically (1 in 200 hits deletes rows older than a day).

| Bucket key | Default limit | Setting |
|---|---|---|
| `code:ip:<ip>` | 30 | `RATE_LIMIT_CODE_PER_IP` |
| `code:id:<normalised identifier>` | 5 | `RATE_LIMIT_CODE_PER_IDENTIFIER` |
| `verify:<challenge_id>` | 10 | `RATE_LIMIT_VERIFY_PER_CHALLENGE` |
| `password:ip:<ip>` | 30 | `RATE_LIMIT_PASSWORD_PER_IP` |
| `password:id:<normalised identifier>` | 10 | `RATE_LIMIT_PASSWORD_PER_IDENTIFIER` |
| resend interval (not a bucket) | 30 s | `OTP_RESEND_SECONDS` |

The client IP is `request.client.host`; in the production image uvicorn runs with `--proxy-headers --forwarded-allow-ips ${FORWARDED_ALLOW_IPS:-127.0.0.1}`, so the real client IP is used only when the proxy address is listed in `FORWARDED_ALLOW_IPS` (verify the value in the deployed compose file; if it is wrong every member shares one IP bucket).
