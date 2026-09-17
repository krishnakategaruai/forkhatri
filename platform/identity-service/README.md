# ForKhatri Identity & Trust Service

The one place a ForKhatri member signs in. Owns the canonical member, passwords,
one-time codes, sessions and the module registry. Modules resolve the browser's
session through the internal API and never store credentials.

- Contract: `docs/ParentApp/07-tech-reqs.md`
- Decisions and research: `docs/ParentApp/00c-identity-and-entrance-decisions.md`
- Architecture: `ARCHITECTURE.md` ADR-004

## Run locally (Windows, Postgres 18 on localhost:5433)

```powershell
# 1. Database (once)
psql -h localhost -p 5433 -U postgres -f db/000-bootstrap.sql
psql -h localhost -p 5433 -U identity_owner -d forkhatri_identity -f db/migrations/001-initial.sql -f db/migrations/002-module-registry.sql

# 2. Python environment (once)
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"

# 3. Existing identities and development members
$env:MANGALY_SOURCE_DSN = "postgresql://<reader>:<password>@localhost:5433/mangaly"
.venv\Scripts\python scripts\import_module_identities.py
.venv\Scripts\python scripts\seed_dev_members.py

# 4. Serve on :8100 (no --reload on Windows; restart after code changes)
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

Development sign-in after seeding: `+919999900001` or `+919800000001`, password
`ForKhatri-dev-2026`. The code sign-in path returns `dev_code` in development.

## Layout

| Path | Purpose |
|---|---|
| `app/components/identity/` | Members, one-time codes, passwords, sessions |
| `app/components/registry/` | Module registry and member entry index |
| `app/rate_limiting/` | Shared database-backed rate limiter |
| `app/api/routes/` | `auth`, `members`, `modules` (public), `internal` (module services) |
| `db/` | Bootstrap and migrations |
| `scripts/` | Identity import and development seed |

## Tests

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check app scripts tests
```
