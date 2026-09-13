# Milavn (MOD02) — Database Implementation

One-line summary: this is the Postgres schema backing Milavn's discovery,
activity/occurrence, circle, trust/reputation, location/privacy, people
discovery, public page, notification, and safety/moderation capabilities —
ten business-component schemas plus one shared cross-cutting schema, living
inside the Core Platform monolith's **shared** database (not an isolated
one). Owned entirely by this module; no other module's code may query these
schemas directly.

See `/ARCHITECTURE.md` (system-wide data-ownership story), `/MODULE-
ARCHITECTURE-STANDARD.md` (why schema-per-component + RLS + idempotency are
structured the way they are), `modules/MOD02-milavn/07-tech-reqs.md` (the
technical requirements this schema implements), and `modules/MOD02-milavn/
07a-er-model.md` (the full reasoning behind every entity/relationship here).

## Getting started

```bash
cp .env.example .env   # fill in real local values — CHANGE_ME placeholders are not usable as-is
./init.sh
```

`init.sh` is idempotent — safe to re-run. It: (1) ensures the shared Core
Platform database exists (default `forkhatridb`, matching this project's
already-running local dev Postgres per the repo root `.mcp.json`), (2)
provisions the `milavn_owner` (migration) and `milavn_app` (runtime) roles
as an admin connection, (3) runs every file in `migrations/` in order, (4)
optionally loads `seeds.sql` if `SEED_DB=true`, (5) prints a verification
summary (schema/table counts, RLS status per table, table-ownership check,
cross-cutting infra table presence).

**Rollback / start over** (drops only Milavn's own schemas, never the
shared database): see the command `init.sh` prints at the end of a run.

## Schema overview

| Schema | Owning component | RLS? | Primary tables |
|---|---|---|---|
| `milavn_profile` | Member Profile | Yes | `member_profile`, `member_interest`, `member_profile_media` |
| `milavn_discovery` | Discovery & Ranking | No (non-sensitive config) | `ranking_weight_config` |
| `milavn_activity` | Activity & Occurrence | Yes | `activity`, `occurrence`, `participation`, `occurrence_co_organizer`, `occurrence_update`, `qr_checkin_token` |
| `milavn_circle` | Circle (incl. OrganizationScope) | Yes | `circle`, `circle_membership`, `circle_formation_suggestion(_member)`, `organization_scope` |
| `milavn_trust` | Trust & Reputation (incl. Feedback) | Partial (reputation_signal/feedback yes; trust_status no) | `trust_status`, `reputation_signal`, `feedback` |
| `milavn_locationprivacy` | Location & Privacy | Yes | `location_precision_setting`, `consent_grant` |
| `milavn_connect` | Connect (People Discovery) | N/A | none — stateless read-model (see `07a-er-model.md` Assumptions) |
| `milavn_publicpage` | Public Page | N/A | none — stateless read-model over Activity/Trust (see Assumptions) |
| `milavn_notification` | Notification Dispatch (incl. inbox) | Yes | `notification_inbox_entry`, `notification_preference`, `notification_outbox` |
| `milavn_safety` | Safety & Moderation | Yes | `report`, `block`, `moderation_action` |
| `milavn_platform` | Cross-cutting infra (not a business component) | No | `idempotency_key`, `rate_limit_counter` |

Identity Bridge and Audit Bridge (architecture.md's two thin bridges) own no
schema, per that file's own design.

### RLS session variables

Every request the Authorization Engine resolves must, inside that request's
own transaction, run (never plain `SET`, per `MODULE-ARCHITECTURE-STANDARD`
§4's second named failure mode):

```sql
SET LOCAL milavn.member_id = '<uuid>';           -- always
SET LOCAL milavn.permission_scope = 'milavn.moderate';  -- only for TR-PLAT-01 console-authenticated moderator actions
SET LOCAL milavn.internal_service = 'true';      -- only the platform reputation-scoring engine (ADR-005), never an ordinary request
```

The application connects as `milavn_app`, a **non-owning** role — `milavn_owner`
(the migration role) owns every table, so RLS is never silently bypassed by
table ownership (§4's first named failure mode).

### RLS-recursion note (found and fixed during live verification)

`circle`'s own RLS policy needs to check `circle_membership`, and
`circle_membership`'s own RLS policy needs to check both itself (does this
member already have an active row in this circle) and `circle` (is this
circle Public/Community). Writing that as direct cross-table `EXISTS`
subqueries produces `ERROR: infinite recursion detected in policy for
relation "circle_membership"` — confirmed live, not a theoretical concern.
Fixed with three `SECURITY DEFINER` helper functions
(`milavn_circle.is_active_member`, `is_open_circle`, `is_circle_creator`),
owned by `milavn_owner`: Postgres exempts a table's *owner* from RLS
regardless of which role calls a `SECURITY DEFINER` function that owner
defined, so these functions resolve membership/type/creator facts without
re-triggering RLS on the table they query, breaking the cycle. `occurrence`'s
own circle-scope visibility check reuses the same `is_active_member`
function rather than a fourth independently-written cross-schema subquery.

## Idempotency mechanism

Per `TR-CROSSCUT-01` / `MODULE-ARCHITECTURE-STANDARD` §4b: one shared table,
`milavn_platform.idempotency_key`, keyed by `(endpoint, actor_member_id,
idempotency_key)`. The API layer (not each business-logic component) looks
this up before executing any of the four named client-retryable mutations —
activity/occurrence creation, participation toggle, report submission,
feedback submission — and returns the stored `response_snapshot` verbatim on
a repeat instead of re-executing. This is deliberately **not** a column on
each business table (that would be "reimplemented per business-logic
component," the exact anti-pattern `TR-CROSSCUT-01` names).

## Rate limiting

Per `TR-CROSSCUT-02` / `MODULE-ARCHITECTURE-STANDARD` §4c: one shared table,
`milavn_platform.rate_limit_counter`, a fixed-window counter keyed by
`(rate_key, window_start)`, called by report submission, activity creation,
and participation toggling — never a per-endpoint counter.

## Waitlist concurrency (TR39)

Promotion on a withdrawal takes a row lock on the freed occurrence
(`SELECT id FROM milavn_activity.occurrence WHERE id = $1 FOR UPDATE`)
inside the same transaction as the withdrawal write, then promotes the
lowest `waitlist_position` row for that occurrence. The partial unique index
`idx_participation_waitlist_position_unique` (`occurrence_id,
waitlist_position` where `status = 'waitlisted'`) prevents two concurrent
promotions from assigning the same position. Live-verified: a promotion
transitions `waitlisted` → `going` correctly under this pattern (see
`07a-er-model.md`'s live-verification log for the exact commands run).

## Development and testing

- `SEED_DB=true ./init.sh` loads `seeds.sql` — three members, one recurring
  Activity with one Occurrence plus one standalone Occurrence with no
  Activity wrapper (demonstrating TR08's non-forced-wrapper rule), a
  capacity-2 occurrence with one Going and one Waitlisted participant, one
  public Circle, one report.
- To reset: run the `DROP SCHEMA ... CASCADE` command `init.sh` prints, then
  re-run `./init.sh`.
- Never run `SEED_DB=true` against a shared staging/production database —
  seed data is development/test only.

## Live-verified, not just reviewed on paper

Before this file was marked Ready for Review, `init.sh` and
`migrations/001-initial.sql` were applied against a real running Postgres
instance (this project's local dev server, `localhost:5433`, the same
shared `forkhatridb` database named in the repo root `.mcp.json`) — not only
reviewed statically. This found and fixed two real defects the static
design missed:

1. **Schema creation order** — `milavn_activity`'s `occurrence_visibility`
   RLS policy referenced `milavn_circle.circle_membership`, but
   `milavn_circle` was declared as the schema created *after*
   `milavn_activity`. Fixed by reordering so Circle is created before
   Activity & Occurrence (component numbering in `schema.sql`'s section
   headers updated to match).
2. **RLS self-reference recursion** — see "RLS-recursion note" above.

Functional RLS behavior (not just "RLS is enabled") was then exercised as
the actual non-owning `milavn_app` role: zero-row results with no session
context on `participation`; correct single-row/full-roster results scoped
to `SET LOCAL milavn.member_id`; correct organizer-sees-all vs.
participant-sees-own-row-only behavior; confirmed `SET LOCAL` does not leak
a member id across transactions on the same connection (the following
transaction's query errors on an empty context rather than silently reusing
the prior member's id — fail-loud, not fail-open); correct private-circle
visibility (non-member sees zero rows, member/creator sees the full
roster); correct circle-scoped occurrence visibility (non-member of the
referenced circle sees zero rows); correct moderator-only report visibility
via `milavn.permission_scope`; correct `reputation_signal` internal-only
isolation (zero rows for an ordinary request, even for one's own signals,
without `milavn.internal_service = 'true'`); and the `FOR UPDATE`
waitlist-promotion lock pattern was run end-to-end, correctly transitioning
a `waitlisted` row to `going`. A second, clean re-run of the full migration
produced zero errors, confirming idempotency.

Not exercised in this pass (left for Step 8/Step 9/Step 10, consistent with
this agent's own scope — it designs and stands up the schema, it does not
replace Security & Performance's or Implementation's own testing): load/
performance behavior under concurrency at scale, the actual FastAPI
application code calling this schema, and the Object Storage/MapTiler/
OpenCage external integrations named in TR01/TR03/TR29 (those are
config-placeholder external services, not database objects).
