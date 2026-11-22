# MOD01 Vyapar — runbook (as built, 2026-11-22)

**Document status:** as built, 2026-11-22; from package.json, scripts, config and 07a-db-implementation/init.sh. Commands not run during this documentation pass are marked unverified.

## Start and stop
- All services: `npm run dev` at the repo root (scripts/dev.mjs). Platform plus Vyapar only: `npm run dev:vyapar`. Status: `npm run dev:status`. Public tunnels: `npm run dev:tunnel` (Ctrl+C reverts the .env blocks).
- Manually: API `cd vyapar-service && .venv/Scripts/python -m uvicorn app.main:app --port 8011`; web `cd vyapar-web && npm run dev` (port 3011).
- Owner rule: restart dev services yourself when your change needs it.

## Health checks
- API alive: `GET http://localhost:8011/openapi.json` returns 200 (observed 2026-11-22). Web: http://localhost:3011 loads Vyapar. Database: `psql -h localhost -p 5433 -U vyapar_app -d vyapar -c "select 1"`.
- Identity: open http://localhost:3100.

## Database
- Fresh build: `07a-db-implementation/init.sh` (roles via admin, schema, migrations 001 to 032 as vyapar_owner, seeds). Single migration: `psql -v ON_ERROR_STOP=1 -U vyapar_owner -d vyapar -f 07a-db-implementation/migrations/032-start-flow.sql`. Migrations are additive and idempotent.
- Marketplace demo data: `vyapar-service/scripts/seed_marketplace.py`.
- Backup/restore: no scheduled backup exists (gap). Manual: `pg_dump -h localhost -p 5433 -U vyapar_owner -Fc vyapar > vyapar.dump`; restore with `pg_restore -c -d vyapar vyapar.dump` (unverified).

## Checks and tests
`vyapar-service/scripts/check_*.py` (admin_console, ai, backend_b, contracts, profile, structured_hiring, taste, trust_pack, voice_interview) run against a live API; `eval_recommendations.py`; web `scripts/check-contrast.mjs`, `scripts/check-i18n-keys.py`; repo `scripts/check_locale_parity.py`. Test sign-in: `platform/identity-service/.venv/Scripts/python platform/identity-service/scripts/dev_session.py <persona> --storage-state <file>`.

## Common failures
| Symptom | Cause | Fix |
|---|---|---|
| Discover shows "could not load posts" | API down, or feed error for a member (seen 2026-11-22 for QA member #28 on a Hindi session; cause not investigated, unverified) | check API log `vyapar-service/api-err.log`, reload, check member data |
| 503 on every call | identity service unreachable (adapter fails closed) | start platform identity service; check IDENTITY_SERVICE_INTERNAL_URL |
| 401 behind a tunnel | cookie not on Vyapar host | use `npm run dev:tunnel`; hub sends fk_handoff; check FORKHATRI_IDENTITY_INTERNAL_URL |
| Payment says "payment service unavailable" | PAYMENT_GATEWAY=razorpay with placeholder keys | use dev_sandbox |
| AI drafts are keyword based | ANTHROPIC_API_KEY placeholder | set key and AI_PROVIDER=anthropic |
| Second `next dev` refuses to start | build lock | set VYAPAR_WEB_DIST_DIR |
| Webhook to localhost rejected | WEBHOOK_ALLOW_PRIVATE_TARGETS false | dev only: set true |
