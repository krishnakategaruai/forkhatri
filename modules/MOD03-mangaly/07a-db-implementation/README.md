# Mangaly (MOD03) — Database Implementation

This is MangalyService's own isolated Postgres database ("MangalyDB" in
`/ARCHITECTURE.md`'s Container diagram) — one Postgres instance, fourteen
schemas, one schema-owning component per schema, per
`/MODULE-ARCHITECTURE-STANDARD.md` §4 and `modules/MOD03-mangaly/
architecture.md` §3. It stores every piece of Mangaly-owned data: profiles,
Home Circle relationships, authorization grants, discovery/ranking index,
compatibility inputs, trust/verification evidence, connections, private
messages, safety cases, lifecycle state, admin operations cases, and the
in-app notification inbox. No other module/container ever queries this
database directly — every cross-module edge goes through a REST call or an
async event, never a shared connection (`/ARCHITECTURE.md` ADR-002).

Full traceability from every table/column back to its FR/TR is in
`../07a-er-model.md`. Read that file first if you need to know *why* a table
or constraint exists — this README only covers *how to run it*.

## Live-verified, not just reviewed on paper

This schema has actually been applied to a real running Postgres instance
(the project's already-running local server at `localhost:5433`, per the
project-root `.mcp.json` — a fresh `mangaly` database was created on it, not
the shared `forKhatridb`), not just authored and eyeballed. What was
confirmed live, and the real bugs found and fixed in the process:

- **`./init.sh` runs clean, end to end, from empty.** All 14 schemas and 61
  tables are created in dependency order with zero manual intervention.
- **`./init.sh` is genuinely idempotent** — re-run against an
  already-provisioned database with zero errors. This caught a real bug:
  `CREATE POLICY` has no `IF NOT EXISTS` form in Postgres, so the first
  re-run failed on the very first policy statement. Fixed by preceding
  every `CREATE POLICY` with a matching `DROP POLICY IF EXISTS` — applied
  mechanically across all ~66 policies in both `schema.sql` and
  `migrations/001-initial.sql`, not just the one that happened to fail first.
- **The non-owning-role requirement (TR017) is real, not asserted.**
  `mangaly_app` (the runtime role) owns **zero** of the 61 tables —
  `SELECT tableowner, count(*) ... GROUP BY tableowner` returns exactly one
  row, `mangaly_owner | 61`. Also caught a real bug in the process: role
  creation is cluster-wide and requires `CREATEROLE`/superuser, so the
  original migration's own `CREATE ROLE` (running as `mangaly_owner`)
  failed with "permission denied to create role." Fixed by moving role
  provisioning out of the migration entirely and into `init.sh`'s own
  admin-connection step — migrations only ever `GRANT` to roles that
  already exist, never create them.
- **RLS actually restricts access, tested as `mangaly_app` itself** (not
  `mangaly_owner`, which would silently bypass every policy): with no
  session context set, every business table returns zero rows; setting
  `mangaly.account_id`/`mangaly.authz_context` via `SET LOCAL` to a
  candidate's own id reveals exactly that candidate's own profile and
  nothing else; a different, unrelated id sees zero rows; a Home Circle
  member with an active `family_info` grant sees the membership row an
  unrelated account cannot. `SET LOCAL`'s transaction-only scoping was also
  confirmed directly (a value set in one transaction does not leak into the
  next statement on the same session) — the exact pooling-safety property
  TR017 requires.
- **A real schema-level grant gap was found and fixed**: `mangaly_app` had
  no `USAGE` on the `mangaly_identity` schema at all, so even the
  pre-authentication `lookup_by_identifier()` function failed with
  "permission denied for schema" — a failure mode distinct from (and
  checked before) any RLS predicate. Fixed with an explicit
  `GRANT USAGE ON SCHEMA mangaly_identity` + table grants, then re-verified
  live that the lookup function works and identity RLS still correctly
  restricts `account` to its own row.
- **A real missing-RLS gap was found and fixed**: the 11 `outbox_event`
  tables (plus `retention_job_run`) had been reasoned about as
  "dispatcher-only" in the original design comments, but that predicate had
  never actually been implemented — they had RLS disabled entirely. Fixed
  with a split policy per table (`FOR INSERT WITH CHECK (true)` — publishing
  an event is a normal part of any business mutation — and
  `FOR SELECT USING (current_setting('mangaly.service_role', true) =
  'dispatcher')` — reads are restricted, since a payload can legitimately
  reference another actor's data), confirmed live: an authenticated insert
  succeeds, the row is invisible to a normal request context, and becomes
  visible once `mangaly.service_role = 'dispatcher'` is set.
- **`mangaly_platform.idempotency_key` and `mangaly_platform.rate_limit_counter`**
  confirmed writable/readable by `mangaly_app` with real inserted rows.
- **Seed data loads cleanly** and re-loads cleanly on a second run (every
  seed insert uses `ON CONFLICT ... DO NOTHING` against fixed UUIDs).

What was **not** re-verified live (out of this step's scope, explicitly
handed to Step 8/9 per the ER model's own Assumptions): the *complete* BR04
permission matrix behind every RLS predicate (TR017 itself states this
remains implementation-stage), and the actual behavior under a real
connection pooler in transaction mode (no PgBouncer-equivalent sits in front
of this local Postgres instance — the `SET LOCAL`-only discipline was
verified structurally and via direct transaction-scoping tests, not against
a real pooler, exactly the residual verification TR017 itself names as
release-blocking for whichever pooling mode Step 9 actually deploys).

## ORM / migration-tool conventions for Step 9

Neither `/ARCHITECTURE.md` nor `CODING-GUIDE.md` names a specific ORM or
migration-tool product — both fix the stack at "Python/FastAPI... Postgres"
and leave the data-access library itself unstated. Given that silence,
Step 9 should default to what's already standard for this stack rather than
introducing a new choice at implementation time:

- **SQLAlchemy 2.x (async engine)** as the ORM, since it is the de facto
  standard for FastAPI + Postgres and its `Mapped[...]`/`mapped_column()`
  typed style matches `CODING-GUIDE.md`'s general preference for
  typed, Pydantic-validated code throughout the API layer.
- **One SQLAlchemy model module per component package**
  (`app/components/<name>/models.py`), mirroring `CODING-GUIDE.md` §2's
  "one Python package per component" rule — a component's models live
  inside its own package, imported only by that component's own
  `interface.py` and repository code, never reached into directly by
  another component (the same import-boundary discipline
  `/MODULE-ARCHITECTURE-STANDARD.md` §3 already requires for everything
  else in this module).
- **Do not let SQLAlchemy's own migration-autogeneration (Alembic) invent
  schema changes.** This directory's `migrations/*.sql` are the
  authoritative, hand-written history (per this agent's own remit); if
  Step 9 adopts Alembic for *application-level* convenience, it should be
  configured to generate against the already-applied `migrations/*.sql`
  state (`alembic stamp` after each raw migration lands), not to own schema
  evolution itself — two independently-authoritative migration systems for
  one database is exactly the kind of drift risk this pipeline's own §4c
  precedent (one shared implementation, never two independently-built
  copies "following the same pattern") already warns against.
- **Cross-schema references stay unconstrained UUID columns at the ORM
  layer too** — do not add a SQLAlchemy `ForeignKey()` across schema
  packages; resolve the referenced entity through the owning component's
  own `interface.py` call, matching this file's own "no cross-schema
  database-level FK" convention (see `07a-er-model.md` Assumptions #3).

## Getting started

```bash
cd modules/MOD03-mangaly/07a-db-implementation
cp .env.example .env        # fill in real local values (init.sh does this for you if you skip it)
./init.sh
```

This creates the database, the `mangaly_owner` and `mangaly_app` roles, runs
every migration in `migrations/` in order, optionally loads `seeds.sql`, and
prints a schema/table-count summary to verify success.

**Rollback / start over:**
```bash
psql -h localhost -p 5433 -U postgres -c "DROP DATABASE mangaly;"
./init.sh
```

## Migrations vs. `schema.sql`

- `migrations/001-initial.sql` is the **authoritative** history — every
  future schema change is a new, numbered, idempotent file here
  (`002-*.sql`, `003-*.sql`, ...), each stating what changed and why in its
  own header comment, per this pipeline's own convention for this file.
- `schema.sql` is a **snapshot** of the same DDL, kept identical to "apply
  every migration in order," so a fresh local setup or a quick schema
  lookup doesn't require reading N migration files. `init.sh` runs the
  `migrations/` files, not `schema.sql`, directly — `schema.sql` is a
  reference copy, not a second execution path, so there is exactly one
  source of truth for what actually runs.

## Schema overview (14 schemas, one owning component each)

| Schema | Owning component | RLS | Notes |
|---|---|---|---|
| `mangaly_identity` | Identity Bridge | Self-only (pre-authz) | **Interim, technical debt** — see Assumptions in `../07a-er-model.md` and `v1-decisions.md`'s "Known technical debt." |
| `mangaly_platform` | — (shared cross-cutting infra) | None (opaque keys) | Idempotency-key store (§4b) + rate-limit counter (§4c/TR037 canonical). |
| `mangaly_authz` | Authorization Engine | Yes | The chokepoint (TR017) — every other schema's RLS policy calls `mangaly_authz.has_scope()`. |
| `mangaly_profile` | Profile & Completeness | Yes | Existence/discoverability/enhanced-tier data (DEC-V1-001). |
| `mangaly_home_circle` | Home Circle | Yes | Membership, notes, suggestions, discovery hints (DEC-V1-003 — no name/photo/contact column, by construction). |
| `mangaly_discovery` | Discovery & Ranking | Yes | Own Postgres-FTS read model, synced via domain events, not a live cross-schema query. |
| `mangaly_compatibility` | Compatibility Engine | Yes | Personality-assessment scaffolding (instrument-agnostic) + opt-in-gated horoscope. |
| `mangaly_trust` | Trust & Verification | Yes | Six independent evidence layers; raw documents readable only by Operations. |
| `mangaly_connection` | Connection & Sharing | Yes | Requests, per-category sharing grants, two-context family-contact sharing. |
| `mangaly_communication` | Communication | Yes | Messages (highest-sensitivity table in the module — one read path, TR051), retention/legal-hold. |
| `mangaly_safety` | Safety Intelligence | Yes | Reports/detection signals; structurally cannot query Home Circle or Trust tables. |
| `mangaly_lifecycle` | Lifecycle & Outcomes | Yes | Conclude/reactivate, meeting notes, success stories. |
| `mangaly_operations` | Operations | Yes | Admin case queue/decisions/appeals, on-call paging, CSAM report packets. |
| `mangaly_notification` | Notification Bridge | Yes | In-app inbox only — delivery itself is Common Platform. |

Two components are genuinely schema-less by design and own no tables here:
**Identity Bridge's authorization role** (it only translates to a future
platform Identity & Trust Service — its interim credential store above is a
named exception, not its authorization function) and **Audit Bridge**
(forwards every event to the platform Audit Log Store; keeps no local copy).

## RLS ("Row-Level Security")

Every business schema above has RLS enabled **at table-creation time**
(never bolted on later, per `/MODULE-ARCHITECTURE-STANDARD.md` §4). Two
non-owning-role/pooling failure modes are addressed explicitly, per TR017's
canonical statement:

1. **Non-owning runtime role.** `mangaly_owner` runs migrations and owns
   every object; `mangaly_app` (what `MangalyService` actually connects as)
   is a separate, non-owning role. RLS silently no-ops for a table's owner —
   `init.sh` never lets the app connect as `mangaly_owner`.
2. **`SET LOCAL`, never `SET`.** The app sets `mangaly.account_id` (Identity
   Bridge, on session validation) and `mangaly.authz_context` (Authorization
   Engine, on `resolve()`) via `SET LOCAL` inside the same transaction as
   every query. Under transaction-mode connection pooling (PgBouncer or
   equivalent), a plain `SET` would leak one request's context onto a
   different pooled connection's next transaction — confirm whichever
   pooling mode Step 9 deploys either guarantees session affinity or that
   the app code exclusively uses `SET LOCAL`, verified by an integration
   test against the real pooling configuration, not asserted from code
   review alone (TR017's own release-blocking requirement).

RLS here is deliberately representative/structural, not the complete
authorization model — the shared `mangaly_authz.has_scope()` function and
each table's policy predicate are Step 9's implementation surface;
Step 8 (Security & Performance) re-verifies every policy against the actual
BR04 permission matrix once it is fully specified.

## Idempotency mechanism (`mangaly_platform.idempotency_key`)

Every client-queueable mutation endpoint TR102 names (profile category save,
connection request/accept/decline, per-category share grant/confirmation,
message send, contact-exchange request/decision) accepts a client-generated
idempotency key. The API-layer `idempotency/` middleware (see
`modules/MOD03-mangaly/CODING-GUIDE.md` §2) looks up
`(idempotency_key, endpoint)` in this one shared table before executing the
mutation, and returns the original `response_snapshot` unchanged on a
repeat — this is one implementation every endpoint calls, never a
per-endpoint re-derivation.

## Rate limiting (`mangaly_platform.rate_limit_counter`)

One shared, DB-backed `(key, window, limit)` counter, per
`/MODULE-ARCHITECTURE-STANDARD.md` §4c and TR037's canonical statement.
TR037 (verifier invites), TR093 (login failures), and TR095 (OTP resend)
all call this same table through one implementation — none builds its own
counter "following the same pattern."

## Development and testing

- **Seed data:** `SEED_DB=true` in `.env` (default) loads `seeds.sql` — a
  small, internally-consistent fixture set (one candidate profile, one
  Home Circle member, one authorization grant, one trust layer, one inbox
  entry) with fixed UUIDs so Step 10/11 test fixtures can reference them
  directly rather than querying for "whatever got seeded."
- **Reset:** drop and re-run `./init.sh` (see Rollback above) — every
  migration is idempotent, so re-running against a partially-applied
  database is also safe.
- **Local Postgres:** any Postgres 14+ works; `pgcrypto` (for
  `gen_random_uuid()`) and `pg_trgm` (Discovery's full-text search, per
  ADR-007/ADR-018) are enabled automatically by migration 001.

## Further reading

- `/ARCHITECTURE.md` — system-wide data ownership story, MangalyDB's
  placement, and why it is a fully isolated Postgres instance.
- `/MODULE-ARCHITECTURE-STANDARD.md` — the generic schema-per-component,
  RLS, idempotency (§4b), and rate-limiting (§4c) patterns this file applies.
- `modules/MOD03-mangaly/07-tech-reqs.md` — the 102 Sealed tech reqs every
  table below traces to.
- `modules/MOD03-mangaly/07a-er-model.md` — the full ER model, three-pass
  cross-validation, and every design assumption this implementation makes.
