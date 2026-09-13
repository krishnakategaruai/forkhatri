---
title: SDLC Pipeline Step 7 Refactor — ER Model Becomes Step 7a
status: Active
updated: 2026-09-12
approver: Chief Architect
---

# Overview

The original Step 7 combined two distinct responsibilities: translating Functional Requirements into Technical Requirements (a requirements-translation task) and designing the complete database ER model + implementation (a detailed architectural/implementation task). These are now split:

- **Step 7: Technical Requirements** — Translate each FR into a technical requirement, one at a time
- **Step 7a: ER Model Design & Database Implementation** (NEW) — Design the complete ER model through a mandatory three-pass internal process and implement the actual database schema, migrations, and initialization

## Why this split matters

### Before (combined Step 7):
- One agent responsible for both strategic (ER model) and implementation (database DDL) tasks
- Risk: ER model design gets rushed after completing tech reqs, or vice versa
- Risk: Database implementation treated as an afterthought rather than a first-class design artifact
- Risk: Three-pass internal process for ER model gets compressed or skipped under time pressure
- ER model and database implementation live in the same step, making it unclear which is "done"

### After (split into Step 7 + Step 7a):
- **Step 7** focuses purely on translating FRs into technical requirements — what changes, at what layer, against what system
- **Step 7a** has one job only: comprehensive ER model design + implementation — no other responsibilities competing for focus
- Three-pass internal process is explicit and mandatory (draft → cross-validate → sign-off)
- Database implementation is first-class: schema, migrations, configuration, setup scripts, documentation all produced together
- Step 8 (Security & Performance) reviews a complete, frozen ER model and implementation plan, not a partial or uncertain one
- Implementation (Step 9) implements against a database already designed and whose structure is guaranteed not to change during implementation

## How it changes the pipeline flow

```
Step 6: Impact Analysis
    ↓ (Sealed)
Step 7: Technical Requirements (unchanged: translates FRs to TRs)
    ↓ (Sealed)
Step 7a: ER Model Design & DB Implementation (NEW)
    ↓ (Sealed)
Step 7b: Component Diagram (existing, already split from Step 7)
    ↓ (Sealed)
Step 8: Security & Performance Analysis
    ↓ (Sealed)
Step 9: Implementation
    [uses Step 7a's database schema + migrations directly]
```

## What Step 7a produces

### Artifact: `07a-er-model.md`

A living document (updated in place via revision log, never a new versioned file) containing:

- **Mermaid ER diagram** — the complete data model
- **Entity/attribute → source requirement traceability table** — every row cites the FR/UX/UI/TR/test scenario that justifies it
- **Data ownership map** — which component owns which schema, following MODULE-ARCHITECTURE-STANDARD §4 (schema-per-component)
- **Cross-validation results** — explicit Pass/Fail on orphan detection in both directions
- **RLS policies** — identified for every sensitive data entity (per MODULE-ARCHITECTURE-STANDARD §4)
- **Idempotency mechanism** — designed for every mutable endpoint if the module supports offline/retryable operations (per §4b)
- **Assumptions** — every inferred relationship or temporal aspect not explicitly stated in a requirement
- **Revision log** — every correction after sign-off becomes a new dated entry, never an overwrite

The file is never single-pass. It goes through:
1. **Draft pass** — comprehensive design, grounded in research of comparable products
2. **Cross-validation pass** — adversarial orphan detection in both directions
3. **Sign-off pass** — final check before human review, confirming all gates Pass

### Implementation: `07a-db-implementation/` directory

- **`schema.sql`** — Postgres schema DDL with all CREATE TABLE, constraints, indexes, RLS policies
- **`migrations/`** — versioned migration files (001-initial.sql, 002-*.sql, etc.), idempotent and executable in order
- **`seeds.sql`** (if needed) — sample/development test data
- **`init.sh`** or **`docker-compose.local.yml`** — one-command database initialization for developers
- **`.env.example`** — sample configuration with placeholder values (user fills in real values later)
- **`README.md`** — schema overview, getting-started instructions, RLS/idempotency explanations, links to parent documents

## Key design principles baked into Step 7a

### Three-pass internal process is mandatory, not optional

After Pass 1 (draft complete), the agent updates 07a-er-model.md status to "Cross-validated".
After Pass 2 (full cross-validation, no orphans), the agent completes Pass 3 (sign-off readiness check).
Only after Pass 3 all checks Pass, the agent sets status to "Ready for Review".
Only after human approval, the agent sets status to "Sealed".

This makes it impossible for an incomplete or uncertain model to slip through to downstream steps.

### Every entity/attribute/relationship must trace to a source

No entity floats free of a requirement. No requirement lacks a corresponding ER element.
Pass 2 catches both directions (orphan requirements, orphan ER elements) before human review.

This ensures traceability — you can walk backward from any database table to the FR that demanded it exist.

### Schema-per-component data ownership

Per MODULE-ARCHITECTURE-STANDARD §4, the ER model identifies which component owns which schema.
Each component is the sole writer to its schema; cross-component data access goes through component interfaces, not direct queries.

This prevents architectural coupling and silent authorization bugs.

### RLS and idempotency are first-class design elements, not afterthoughts

Row-Level Security (§4) and idempotency keys (§4b) are designed into the schema now, not added later when Implementation finds they're needed.
They show up as explicit columns, policies, and assumptions in the ER model.

This follows MODULE-ARCHITECTURE-STANDARD's own principle: security and offline-capability are structural requirements, enforced at the database layer, not conventions a developer might skip.

### Database implementation is immediate, not deferred

The agent produces not just a diagram, but a complete, executable database schema and migration setup.
Implementation (Step 9) inherits a database that is ready to use, not a list of tables that someone else has to turn into working DDL.

This reduces risk and ensures Implementation is never blocked by database schema uncertainty.

## What changes for Implementation (Step 9)

When Step 9 (Implementation) receives the code changes to build against:

- The ER model is complete and Sealed — no changes to the database structure during implementation
- Migration files already exist and are ordered — Implementation does not create migrations; it may add new ones if the tech req unfolds to need new tables, but existing ones are frozen
- `.env.example` is available — Implementation uses it as a template, filling in real values in their own development setup
- `init.sh` is executable — developers can run it once to have a working database without manual SQL

If Implementation discovers the ER model is incomplete or wrong:
- Implementation raises a blocker against Step 7a (does not edit the ER model itself)
- Step 7a adds a new dated revision log entry describing what was missing and why
- New migrations are generated if the schema needs to change
- Implementation continues once the blocker is cleared

## Timeline impact

Originally: Step 7 was split across ER model design + tech reqs writing, both competing for one agent's focus. This often resulted in:
- ER model being designed quickly and partially, or
- Tech reqs being written faster than the ER model could be properly thought through

Now: Step 7a has one job only — design the ER model and implement the database. This is a separate, focused step that can take the time needed for three full passes of validation. The pipeline doesn't move forward until the ER model is Sealed, which is correct: everything downstream depends on a correct, complete data model.

The trade-off is explicit: you invest more upfront in ER model design (three passes, research, comprehensive traceability), so Implementation, Security, Test, and all downstream steps never waste effort working against an uncertain data model.

## Approval

Chief Architect — [x] Approved — krishna kategaru, 2026-09-12
