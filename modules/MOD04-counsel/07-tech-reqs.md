# MOD04 Counsel — 07 Technical requirements

**Document status:** 2026-11-22, "as built". Architecture and diagrams: `architecture.md`. Full endpoint table (110 endpoints): `API-REFERENCE.md`. Data model: `07a-er-model.md`.

## Contents
1 Stack · 2 Endpoint summary · 3 Configuration reference · 4 Error model · 5 Jobs, caching, realtime · 6 i18n · 7 Run and deploy · 8 Observability · 9 Versioning · 10 Performance budgets · 11 Technical requirements TR-01..

## 1. Stack
Backend `requirements.txt`: fastapi 0.141.1, uvicorn[standard] 0.52.4, pydantic 2.13.5, pydantic-settings 2.15.0, asyncpg 0.31.0, python-dotenv 1.2.1, python-multipart 0.0.32, httpx 0.28.1, tzdata 2025.2, websockets 15.0.1, cryptography 46.0.1, forkhatri-integrations (editable). Frontend `package.json`: next 16.3.5, react/react-dom 19.2.8, i18next ^26.4.2, react-i18next ^17.0.13, lucide-react ^0.544.0, typescript ^5, eslint ^9. Fonts: Fraunces (display) and Anek Latin/Devanagari/Telugu/Kannada (body). Note: `counsel-web/AGENTS.md` warns this Next.js has breaking changes; read `node_modules/next/dist/docs/` before changing framework-level code.

## 2. Endpoint summary
106 OpenAPI operations + 3 internal + 1 WebSocket = 110, grouped: me/privacy 11, discovery 8, provide 27, bookings and room 28, time requests 4, offers 11, payments 1, admin 20, media/root 2, internal 3, WS 1 (counts approximate by tag; the authoritative list is API-REFERENCE.md API-001..API-110).

## 3. Configuration reference (names only; secrets marked S)
Service (`counsel-service/.env`, loaded by `app/settings.py`):
| Name | Purpose | Default |
|---|---|---|
| API_HOST, API_PORT | bind address/port | 127.0.0.1, 8014 |
| WEB_ORIGIN | web origin for calendar links | http://localhost:3014 |
| CORS_ALLOWED_ORIGINS | CORS list | localhost 3014 |
| DB_HOST, DB_PORT, DB_NAME | database | localhost, 5433, counsel |
| DB_APP_USER, DB_APP_PASSWORD (S), DB_POOL_MAX | runtime role | counsel_app, CHANGE_ME, 20 |
| DB_ADMIN_USER, DB_ADMIN_PASSWORD (S), DB_OWNER_USER, DB_OWNER_PASSWORD (S) | used by `db/init.sh` only | - |
| SEED_DB | load `seeds.sql` in init.sh | false |
| PLATFORM_IDENTITY_URL | identity service | http://localhost:8100 |
| PLATFORM_SERVICE_NAME, PLATFORM_SERVICE_KEY (S) | service credentials | counsel, CHANGE_ME |
| PLATFORM_SESSION_COOKIE | cookie name | fk_session |
| FORKHATRI_ENTRANCE_URL | hub URL | http://localhost:3100 |
| ADMIN_MEMBER_IDS | dev admins (comma ids) | empty |
| PAYMENT_PROVIDER | mock / sandbox / payment_services / vendor | mock |
| PAYMENTS_WEBHOOK_SECRET (S) | verifies `/payments/events` | CHANGE_ME |
| PAYMENT_SERVICES_URL, PAYMENT_SERVICES_KEY (S) | MOD06 client | http://localhost:8016 |
| NOTIFICATION_CHANNELS | inapp, log, email, sms, whatsapp, push | inapp,log |
| SMS_PROVIDER, WHATSAPP_PROVIDER, EMAIL_PROVIDER, PUSH_PROVIDER | senders | console |
| ICE_SERVERS | JSON RTCIceServer list | Google STUN |
| STORAGE_ROOT, MAX_UPLOAD_MB | file store, upload cap | .local-files, 25 |
| PAYOUT_ENCRYPTION_KEY (S) | Fernet key for payout details | CHANGE_ME (dev fallback derived from service key) |
| FILE_ENCRYPTION_KEY (S) | AES-256-GCM key (32 bytes urlsafe base64) | CHANGE_ME (dev fallback) |
| MALWARE_SCANNER, CLAMD_HOST, CLAMD_PORT | scanner | none, 127.0.0.1, 3310 |
| AI_PROVIDER, ANTHROPIC_API_KEY (S), COUNSEL_AI_MODEL | AI | rules, CHANGE_ME, claude-sonnet-5 |
Web (`counsel-web/.env.local`): NEXT_PUBLIC_API_BASE (http://localhost:8014), NEXT_PUBLIC_WS_BASE (ws://localhost:8014), NEXT_PUBLIC_IDENTITY_API (http://localhost:8100), NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL (http://localhost:3100); tunnel only: FORKHATRI_IDENTITY_INTERNAL_URL, COUNSEL_API_INTERNAL_URL, TUNNEL_DEV_ORIGIN. Browser storage keys: `counsel.theme`, saved city, language (i18n provider).

## 4. Error model
All handlers raise `DomainError(code, message, status)` -> `{"detail":{"code","message",...extras}}`; unhandled -> 500 `internal`. The web client translates `errors.<code>` and falls back to the English message. Codes in use: already_reviewed, bad_event, closed, confirm_required, consent_required, custom_time_off, deletion_blocked(blockers), dispute_open, file_infected, file_too_large, file_type, file_unreadable, follow_up_needs_first, forbidden, hold_expired, identity_unavailable(503), incomplete, internal, invalid_account, invalid_ifsc, invalid_slug, invalid_upi, invalid_window, not_a_provider, not_applicable, not_approved, not_cancellable, not_completable, not_completed, not_disputable, not_found, not_open, not_pending, nothing_to_pay, outside_window, own_service, package_inactive, package_not_cheaper, package_used_up, payment_failed(402), payout_method_required, questions_off, recording_not_allowed, scan_unavailable(503), service_unauthorized(401), sessions_booked, slot_taken(409), slot_unavailable(409), slot_taken (time request), timezone_required, too_early, too_many_requests(429), unauthenticated(401), unknown_setting, verification_required(missing[]), wrong_service. Validation errors from pydantic return FastAPI's default 422 shape.

## 5. Jobs, caching, realtime
See architecture.md section 4-5. Caches: session (30 s/5 s, 5000 entries then cleared), name lookup 300 s, in-memory room hub and tickets. No Redis.

## 6. i18n
Client namespaces (top-level keys of `locales/<lang>/common.json`, 40 each, 1029 leaf keys per language, parity verified by count): nav, common, auth, lang, day, country, a11y, home, card, why, verify, format, discover, provider, rep, review, evidence, links, service, book, policy, disclaimer, status, bookings, booking, dispute, system, room, provide, profile, services, avail, earn, payout, saved, notif, report, me, admin, errors. Server sends codes and keys (notification kinds, `system` message bodies, `disclaimer_key`), never prose. Repo script `scripts/check_locale_parity.py` checks parity (unverified whether it covers counsel).

## 7. Run and deploy
Local: from repo root `npm run dev` (starts platform and modules; `scripts/dev.mjs`); Counsel alone: DB `bash counsel-service/db/init.sh` (needs `.env`), API `uvicorn app.main:app --port 8014` from `counsel-service` using its `.venv`, web `npm run dev` in `counsel-web`. Tunnels: `scripts/tunnel.mjs` (Cloudflare quick tunnels) rewrites env for web/API. No production deploy kit covers Counsel (master critique 12). See RUNBOOK.md.

## 8. Observability
Python logging to stdout (`counsel`, `counsel.notify`, `counsel.payments`, `counsel.storage`, `counsel.outbound`); `api.log`/`web.log` files in the module are local run logs. Audit log table is the business trace. No metrics, tracing or alerting. Health: `GET /` returns `{service:"counsel",ok:true}` (no `/health`).

## 9. Versioning
FastAPI app version "1.0"; no API versioning prefix except `/internal/v1`; migrations are numbered files.

## 10. Performance budgets
None defined in code. Known costs: `search` loads all approved providers then builds each card (several queries per card, N+1) and `/provide/dashboard` calls search with limit 500 for rank; fine for tens of consultants, not for thousands. Housekeeping loop runs `badges.refresh_all` every 10 minutes over all approved providers.

## 11. Technical requirements
| ID | Requirement | Status |
|---|---|---|
| TR-01 | Never double book: DB exclusion constraint on live bookings | built |
| TR-02 | Authorise in the handler for every booking resource | built |
| TR-03 | Snapshot price, fee and policy on booking | built |
| TR-04 | Encrypt private files and payout details at rest | built (dev key fallback) |
| TR-05 | Refuse mock payments off-loopback | built |
| TR-06 | Idempotent gateway calls with stable keys | NOT built (G-04) |
| TR-07 | Outbox after commit for gateway calls | NOT built |
| TR-08 | Horizontal scale of hub/jobs | NOT built |
| TR-09 | RLS defence in depth | NOT built |
| TR-10 | Automated tests | NOT built |
| TR-11 | TURN relay configured through ICE_SERVERS | config supported, no server |

## 12. Notification kinds (exact)
booking.new, booking.confirmed, booking.cancelled, booking.no_show, booking.recap, booking.reminder_day, booking.reminder_now, review.available, review.received, payout.eligible, message.new, time_request.new, time_request.accepted, time_request.declined, package.bought, package.refunded, question.new, question.answered, question.refunded, dispute.decided, badge.earned, provider.approved, provider.changes_requested, provider.suspended, expertise.approved, expertise.rejected. Each needs a `notif.<kind>` string in all five locales.

## 13. Service components (`app/components/`)
ai, `audit` (append-only `audit.record`), availability, badges, bookings, insights, money, notifications, outbound, places, privacy, providers, purchases, storage, workspace.

## 14. Account deletion technical requirements (added 2026-11-22)
| ID | Requirement | Status |
|---|---|---|
| TR-12 | `privacy.erase_member(member_id, reason)` erases member data across the 40 tables in one transaction as `counsel_app` (no migration, no RLS change, no privilege added) | built |
| TR-13 | `POST /internal/v1/members/{id}/erase` authenticated by service key and `X-ForKhatri-Service: identity` | built |
| TR-14 | Idempotent: receipt in `erased_member`; second call `nothing_to_delete` | built |
| TR-15 | One-way stand-in id `sha256("counsel-erased:" + member_id + service key)` via `privacy.tombstone()` | built |
| TR-16 | Files removed after commit; caches dropped (`identity.forget()`) | built |
| TR-17 | `POST /me/delete-account-data`, typed DELETE, 3 per hour per member | built |
| TR-18 | Retry on failure is the hub's job (backoff, 7 days, admin stuck list) | built (hub) |
| TR-19 | Erase must not return 500 for a never-seen member | NOT verified for Counsel (Vyapar did once) |
Config names: `STORAGE_ROOT` and the existing service-key settings; no new names. Notification kinds used: `booking.cancelled_deleted` (new in `bookings.py`) and `purchase.closed_deleted` (`privacy.py`).
