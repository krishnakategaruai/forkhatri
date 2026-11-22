# MOD04 Counsel — Runbook

**Document status:** 2026-11-22, development environment on Windows (Git Bash). No production deployment exists for Counsel.

## Contents
1 Start and stop · 2 Health checks · 3 Database · 4 Backups and restore · 5 Common failures · 6 Safe operations

## 1. Start and stop
All modules: from repo root `npm run dev` (runs `scripts/dev.mjs`: platform identity :8100, hub :3100, modules). Counsel alone: ensure Postgres on 5433 and identity on 8100 are up, then `cd modules/MOD04-counsel/counsel-service && .venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8014` and `cd modules/MOD04-counsel/counsel-web && npm run dev`. Stop by ending those processes (find with `netstat -ano | grep :8014`). Only stop processes you started. Env files: copy `.env.example` to `.env` (service) and `.env.local` (web).

## 2. Health checks
- API: `curl localhost:8014/` returns `{"service":"counsel","ok":true}`; `curl localhost:8014/openapi.json` lists 106 operations; `curl localhost:8014/expertise` returns 26 areas (needs DB).
- Web: `http://localhost:3014/` loads Home.
- Identity: signed-in calls (`/me`) return 401 without a cookie and 503 if identity is down.
- Jobs: API log lines `expired N abandoned checkouts`, `deliveries: ...`; warnings `housekeeping: <error>` mean the loop hit an error (it continues).

## 3. Database
Initialise or upgrade: `bash counsel-service/db/init.sh` (idempotent, reads `.env`; set `SEED_DB=true` for sample data; ends by printing the table count, expected 40). Read-only checks: `psql -h localhost -p 5433 -U counsel_app -d counsel` then `\dt counsel.*`. Do not run seeds on a shared database.

## 4. Backups and restore
No backup job exists. Back up two things together: the `counsel` database (`pg_dump -h localhost -p 5433 -U counsel_owner counsel`) and the `STORAGE_ROOT` directory (default `counsel-service/.local-files`), plus keep `FILE_ENCRYPTION_KEY` and `PAYOUT_ENCRYPTION_KEY` safe: without them encrypted files and payout details cannot be read. Restore: recreate DB and roles via `init.sh`, `psql` the dump, restore the directory. Unverified: restore has never been rehearsed.

## 5. Common failures
| Symptom | Likely cause | Fix |
|---|---|---|
| Web shows "Can't reach ForKhatri sign-in" | identity :8100 down | start platform; Retry |
| Sign-in card on every page | no `fk_session` for localhost | sign in at hub 3100 (dev: Act as) |
| API refuses to start: "mock only allowed for loopback" | `API_HOST` not 127.0.0.1 with `PAYMENT_PROVIDER=mock` | bind loopback or choose a real provider |
| API refuses: key must be set | CHANGE_ME in payout/file key off loopback | generate keys |
| 503 scan_unavailable on uploads | `MALWARE_SCANNER=clamav` but clamd down | start ClamAV or set `none` |
| Calls do not connect | no TURN; strict network | set `ICE_SERVERS` with a TURN entry |
| Booking stays pending then expires | payment never confirmed | pending expires after 15 min by design |
| Reminders/auto-complete stopped | housekeeping task died | check log, restart API |
| Notifications queued but not sent | no contact lookup; rows marked skipped | expected until B2 |
| `slot_taken` on valid slot | overlap with buffer or another pending hold | wait for expiry |
| Web 404 for photos | API `/media/photos` not reachable via `NEXT_PUBLIC_API_BASE` | fix env |
| CORS error | origin not in `CORS_ALLOWED_ORIGINS` | add origin |

## 6. Safe operations
Settings (fee, policy, hold, retention) change in Admin -> Settings and are audited; they never change existing bookings. To suspend a consultant use Admin -> Provider -> Suspend (pauses services). To erase a member use the member's own You page or the platform's internal erase route. Never edit ledger or booking money columns by hand.

## 7. Account deletion (added 2026-11-22)
Verify: with the API and database up, run `counsel-service/scripts/check_account_deletion.py` with the service's Python (throwaway member #34 and QA members #1, #2; it cleans up); expect 16 passes. Real call: `POST /internal/v1/members/{id}/erase` with the service key and `X-ForKhatri-Service: identity`; expect `done`, then `nothing_to_delete` on repeat.
Resume stuck deletions: in the hub, admin, Modules page, "stuck deletions", Retry (`POST /v1/admin/deletions/{job_id}/retry`). Counsel is safe to call again.
On failure: read the API log. Erase is one transaction, so a failure leaves the data untouched; fix the cause and retry. If files remain after a crash (`STORAGE_ROOT` `private/evidence/<member>/`, `public/photos/<member>/`) and the member is in `erased_member`, the folder can be removed by hand. Open owner question: unpaid earnings (01 section 13).
