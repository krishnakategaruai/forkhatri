# MOD03 Mangalya - Runbook (as built 2026-11-22)

**Document status:** 2026-11-22, as-built scope. Facts come from code, scripts and config. Items marked *unverified* were not executed.

## 1. Components and ports
| Component | Folder | Port | Stack |
|---|---|---|---|
| mangaly-web | `mangaly-web/` | 3000 | Next.js (app router), React, react-i18next, face-api in the browser |
| mangaly-service | `mangaly-service/` | 8000 | FastAPI, SQLAlchemy async, PostgreSQL with RLS, Python 3.13 |
| horoscope-service | `horoscope-service/` | 8013 | Node (TypeScript run natively), `@prisri/jyotish` |
| Database | `07a-db-implementation/` | PostgreSQL | migrations 001-067 |
| Identity (platform) | `platform/identity-service` | 8100 | sign-in; hub on 3100 |

## 2. Start / stop
- Everything: from the repo root `npm run dev` (`scripts/dev.mjs`). **Drift found 2026-11-22:** `dev.mjs` points at `modules/MOD03-mangalya/mangalya-service` and `mangalya-web`, but the real inner folders are still `mangaly-service` and `mangaly-web` (only the module folder was renamed). Fix `dev.mjs` or rename the inner folders; until then start Mangalya by hand. Likewise `deploy/docker-compose.yml` and `deploy/Caddyfile` still say `MOD03-mangaly` (also in MASTER-CRITIQUE item 12).
- By hand: uvicorn `app.main:app` on port 8000 inside `mangaly-service` (virtualenv path unverified); `npm run dev` in `mangaly-web`; `npm start` in `horoscope-service` (needs `HOROSCOPE_SERVICE_TOKEN`, at least 24 characters, or it refuses to start).
- Stop: end only the processes you started.
- Tunnels: `scripts/start-tunnels.ps1`. The web `proxy.ts` redeems `fk_handoff` codes when `FORKHATRI_IDENTITY_INTERNAL_URL` is set.

## 3. Health checks
- `GET http://localhost:8000/health` and `GET http://localhost:8013/health` (both open; other horoscope routes need the service token).
- Web: sign in at `http://localhost:3100`, then open `http://localhost:3000`. The web shows an outage screen (`OutageGate`) when the API is unreachable.

## 4. Database
- Apply migrations in order from `07a-db-implementation/migrations/` (see `07a-db-implementation/README.md`, `init.sh`). Migrations are additive and authoritative; `schema.sql` lags.
- Backup / restore: standard `pg_dump` / `pg_restore` of the `mangaly_*` schemas. No automated backup job exists in the repo (unverified); production policy is not decided (owner / operations).
- Dev seeds: `mangaly-service/scripts/seed_dev_*.py` (accounts, families, circles, horoscope, RM, operator, verification, Vikram family, more matches). Maintenance: `reindex_discovery.py`, `compute_daily_picks.py`, `recalculate_horoscope_charts.py`, `retire_unused_made_for_profiles.py`, `import_osm_places.py`, `fetch_wedding_photos.py`, `build_guides_migration.py`, `check_*.py` (live checks).
- Sessions for tests: `platform/identity-service/scripts/dev_session.py <persona>`; never the OTP screens; never "Sign out on all devices".

## 5. Environment settings (names only)
mangaly-service reads `07a-db-implementation/.env` then `mangaly-service/.env`; names are case-insensitive with no prefix.

Secrets (never commit values): DB_APP_PASSWORD, OBJECT_STORAGE_ACCESS_KEY, OBJECT_STORAGE_SECRET_KEY, HOROSCOPE_SERVICE_TOKEN, ANTHROPIC_API_KEY, PAGERDUTY_ROUTING_KEY, CSAM_REPORT_API_KEY, TWILIO_AUTH_TOKEN, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET, PAYMENTS_WEBHOOK_SECRET, PAYMENT_SERVICES_KEY, PLATFORM_SERVICE_KEY.

All settings (80): DB_HOST, DB_PORT, DB_NAME, DB_APP_USER, DB_APP_PASSWORD, DB_POOL_MODE, DB_POOL_MAX_CONNECTIONS, IDEMPOTENCY_KEY_TTL_DAYS, RATE_LIMIT_DEFAULT_WINDOW_SECONDS, RATE_LIMIT_LOGIN_FAILURE_MAX, RATE_LIMIT_LOGIN_FAILURE_WINDOW_SECONDS, RATE_LIMIT_OTP_RESEND_MAX_PER_HOUR, RATE_LIMIT_OTP_RESEND_MIN_INTERVAL_SECONDS, RATE_LIMIT_HOME_CIRCLE_INVITE_MAX, RATE_LIMIT_CONNECTION_REQUEST_MAX_PER_DAY, REQUEST_COOLDOWN_AFTER_DECLINE_DAYS, REQUEST_COOLDOWN_AFTER_WITHDRAW_DAYS, RATE_LIMIT_MESSAGE_SEND_MAX_PER_HOUR, RATE_LIMIT_REPORT_MAX_PER_DAY, RATE_LIMIT_BLOCK_MAX_PER_DAY, MESSAGE_RETENTION_DAYS, CREDENTIAL_HASH_ALGORITHM, CREDENTIAL_HASH_TIME_COST, CREDENTIAL_HASH_MEMORY_COST_KB, CREDENTIAL_HASH_PARALLELISM, OBJECT_STORAGE_ENDPOINT, OBJECT_STORAGE_BUCKET, OBJECT_STORAGE_ACCESS_KEY, OBJECT_STORAGE_SECRET_KEY, OBJECT_STORAGE_SIGNED_URL_TTL_SECONDS, HOROSCOPE_SERVICE_URL, HOROSCOPE_SERVICE_TOKEN, ANTHROPIC_API_KEY, MATCHMAKER_MODEL, RATE_LIMIT_MATCHMAKER_MAX_PER_DAY, PAGING_VENDOR, PAGERDUTY_EVENTS_API_URL, PAGERDUTY_ROUTING_KEY, PAGERDUTY_ESCALATION_POLICY_ID, CSAM_REPORT_ENDPOINT, CSAM_REPORT_API_KEY, CSAM_REPORT_FALLBACK_MODE, RETENTION_POST_DELETION_GRACE_DAYS, RETENTION_POST_DELETION_ERASURE_DAYS, RETENTION_PRE_ERASURE_NOTICE_HOURS, RETENTION_INACTIVE_ACCOUNT_CEILING_DAYS, RETENTION_AUDIT_LOG_MIN_DAYS, RETENTION_SAFETY_EVIDENCE_POST_CASE_CLOSURE_DAYS, SMS_PROVIDER, SMS_DLT_TEMPLATE_ID_OTP, OTP_FALLBACK_CHANNEL, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_DEV_ALLOWED_NUMBERS, SESSION_TTL_DAYS, OTP_TTL_SECONDS, OTP_MAX_ATTEMPTS, OTP_CODE_DIGITS, PASSWORD_RESET_TTL_SECONDS, MIN_CREDENTIAL_LENGTH, SESSION_COOKIE_SECURE, CORS_ALLOWED_ORIGINS, CORS_ALLOWED_ORIGIN_REGEX, PLATFORM_IDENTITY_URL, PLATFORM_SERVICE_NAME, PLATFORM_SERVICE_KEY, PLATFORM_SESSION_COOKIE_NAME, PLATFORM_IDENTITY_TIMEOUT_SECONDS, FORKHATRI_ENTRANCE_URL, INTERIM_IDENTITY_ENABLED, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET, PAYMENT_GATEWAY, PAYMENTS_WEBHOOK_SECRET, PAYMENT_SERVICES_URL, PAYMENT_SERVICES_KEY, PAYMENTS_ALLOW_SANDBOX, API_DEBUG.

Web: NEXT_PUBLIC_API_BASE, NEXT_PUBLIC_BASE_PATH, NEXT_PUBLIC_IDENTITY_API, NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL, FORKHATRI_IDENTITY_INTERNAL_URL, NEXT_DIST_DIR, NEXT_OUTPUT_STANDALONE, TUNNEL_DEV_ORIGIN.
Horoscope: HOROSCOPE_SERVICE_TOKEN, HOROSCOPE_PORT (default 8013).

## 6. Common failures and fixes
| Symptom | Cause | Fix |
|---|---|---|
| Matchmaker reads words simply; biodata reader fills little | `ANTHROPIC_API_KEY` is a placeholder; built-in keyword reader used; family can attach and type | set a real key |
| Horoscope panel empty / 403 | horoscope-service down or token mismatch | start it; same `HOROSCOPE_SERVICE_TOKEN` in both services |
| Checkout says sandbox | no payment vendor; `PAYMENTS_ALLOW_SANDBOX` on (`/billing/dev/pay`) | expected until a vendor exists |
| Face check cannot start | camera blocked or unavailable | screen says so; draft kept; "Try again later" (optional step) |
| Creating a child's profile still asks the child's phone and a face check | pending server change (see 09-implementation.md section 6) | apply the documented `POST /profile/managed` change |
| 403 `verification_required` | maker gate still in `profile.py` and `agents.py` | same |
| Discover shows skeletons for seconds | dev build | known (critique M6) |
| Port 3000 or 8000 busy | another process | find and stop your own only |

## 7. Account deletion (2026-11-22)
- **Run it:** member path, `/me` then "Delete my data in Mangalya", type DELETE. Platform path: the hub calls `POST /internal/v1/members/{id}/erase` with the service key. Use a throwaway member, never a shared persona.
- **Verify:** the response shows `status` (`done` or `nothing_to_delete`) and counts; check no rows remain for the account id and that `.local-media/<id>/` is gone; `mangaly_platform.deletion_receipt` has one row.
- **Stuck or failed:** the call is one transaction, so a failure leaves the data untouched; call again (idempotent). For kind A, the hub retries automatically and lists stuck jobs on the admin Modules page with a Retry button. 409 `role_must_be_removed_first`: remove the operator role first.
- **Dev web server:** now `next dev --webpack` (a Turbopack next/font bug gave 500s). Photos were once deleted from disk by a git clean-up and restored; do not run `git clean` over `mangaly-service/.local-media`.
