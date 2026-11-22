# RUNBOOK - MOD02 Milavn (development environment, 2026-11-22)

Written from code and README; commands not re-run in this pass (unverified where marked).

## Start
1. PostgreSQL on localhost:5433, database `forkhatridb`, roles `milavn_owner` (migrations) and `milavn_app` (runtime).
2. Platform: identity service :8100 and entrance :3100 (from repo root; one command to start everything: see memory "dev-command-start-all", unverified here).
3. API: `cd modules/MOD02-milavn/milavn-service` then `.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001` (do **not** use `--reload` on Windows).
4. Web: `cd modules/MOD02-milavn/milavn-web` then `npm run dev` (port 3001).
5. Open http://localhost:3100, sign in, tap Milavn.

## Stop
Stop the two processes you started (by port). Never kill Chrome processes you did not start. If port 8001 answers with stale code, look for orphaned `python` processes whose command line contains `spawn_main` and whose parent is gone, and stop those.

## Health checks
- `GET http://localhost:8001/health` returns `{"status":"ok","module":"MOD02-milavn"}` (verified 200 on 2026-11-22).
- `GET http://localhost:8001/openapi.json` lists 205 operations.
- Web `http://localhost:3001/` returns 200 (verified).
- DB: `psql -h localhost -p 5433 -U milavn_app -d forkhatridb -c "select count(*) from milavn_profile.member_profile"`.
- Identity down: API answers 503 on authenticated calls (fails closed).

## Database
Migrate: as `milavn_owner`, `psql -f 07a-db-implementation/migrations/NNN-name.sql` in file order; migrations are safe to run twice. From scratch: `07a-db-implementation/init.sh` then migrations and `seeds-dev.sql`. Pending owner action (2026-11-22): run `GRANT DELETE ON milavn_notification.notification_inbox_entry TO milavn_app;` (in migration 055) or dismissing a notification fails with 500.
Backup (shared database, unverified procedure): `pg_dump -h localhost -p 5433 -U <owner> -n 'milavn_*' forkhatridb > milavn.sql`. Restore: recreate roles, `psql -f milavn.sql`. Media files are in `milavn-service/.local-media/` and must be backed up with the dump or photos vanish.

## QA data
Seed 20 QA members: `platform/identity-service/.venv/Scripts/python modules/MOD02-milavn/scripts/seed_qa_members.py` (needs ports 8100 and 8001); remove with `--remove`. Events cannot be deleted through the product (cancel only); QA rows may need an owner-run cleanup.

## Common failures
| Symptom | Cause | Fix |
|---|---|---|
| API serves old code | orphaned uvicorn reloader child | stop `spawn_main` orphans, restart without `--reload` |
| 503 on every signed-in call | identity service down | start :8100 |
| 403 `origin_not_allowed` on writes | web origin not in `CORS_ALLOWED_ORIGINS` | add the origin |
| Place search empty | `PLACES_PROVIDER=none`, no network, or OSM rate limit | check settings and network; self-host later |
| Notification "x" fails 500 | GRANT DELETE not applied | see Database |
| Event page blank signed out | server cannot fetch a relative API base | set `API_SERVER_BASE` / `MILAVN_API_INTERNAL_URL` absolute (EVENT-PAGE-LEARNING) |
| Waitlist never gets an offer on a paid event | old function before 055 | apply 055 function change (applied in dev) |
| Professional events show broken cover | `public/assets/covers/professional.jpg` missing | restore file |
| Join link missing on next weekly date | fixed 2026-10-06 | restart API |
| "Next dev badge", build fails on missing locale | another session editing `locales` | wait and retry |
| Jobs run twice | two API instances | run one instance |
