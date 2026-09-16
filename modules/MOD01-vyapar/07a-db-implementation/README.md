# Vyapar (MOD01) — Database Implementation

This is Vyapar's own slice of the Core Platform Postgres instance — one
Postgres database (`vyapar`, per `/ARCHITECTURE.md` ADR-001/ADR-002's
modular-monolith placement), twelve schemas, one schema-owning component per
schema, per `/MODULE-ARCHITECTURE-STANDARD.md` §4 and
`modules/MOD01-vyapar/07-tech-reqs.md`'s "Component decomposition (Vyapar)"
table. It stores every piece of Vyapar-owned data: the member-link identity
mirror, listings and verification evidence, opportunities, enquiries and
partnership requests, reviews, commercial (boosts/workspaces/campaigns),
payment orders, privacy/consent records, trust & safety cases, analytics
events, and the integration-bridge tables (notifications inbox, audit log,
dead letters, config, counsel referrals). No other module/container ever
queries this database directly.

Full traceability from every table/column back to its FR/TR is in
`../07a-er-model.md`. Read that file first if you need to know *why* a table
or constraint exists — this README only covers *how to run it*.

## Getting started

```bash
cd modules/MOD01-vyapar/07a-db-implementation
cp .env.example .env   # edit DB_* if your local Postgres differs
./init.sh
```

This creates the `vyapar` database (if missing), provisions `vyapar_owner`
(migration/DDL role) and `vyapar_app` (non-owning runtime role) as an admin
connection, runs every file in `migrations/` in order as `vyapar_owner`,
loads `seeds.sql` if `SEED_DB=true`, then prints a verification report
(schema/table counts, RLS-enabled check, non-owning-role check, seed row
counts).

**Rollback / start over:**
```bash
PGPASSWORD=$DB_ADMIN_PASSWORD psql -h localhost -p 5433 -U postgres -c "DROP DATABASE vyapar;"
./init.sh
```

## Schema overview

| Schema | Owning component | RLS? | Primary tables |
|---|---|---|---|
| `vyapar_identity` | Identity Bridge | Yes | members |
| `vyapar_listings` | Listings & Verification | Yes | listings, listing_contacts, otp_challenges, verification_records, taxonomy_terms, member_listing, outbox_event |
| `vyapar_opportunities` | Opportunities | Yes | opportunities, member_opportunity, outbox_event |
| `vyapar_enquiries` | Enquiries & Partnerships | Yes | enquiries, enquiry_messages, blocks, partnership_requests |
| `vyapar_reviews` | Reviews & Reputation | Yes | review_invites, reviews, review_disputes |
| `vyapar_commercial` | Commercial | Yes (products/no) | products, campaigns, promotions, commercial_order_history, entitlements, workspace_members, impressions, outbox_event |
| `vyapar_payments` | Payment Bridge | Yes | payment_orders |
| `vyapar_privacy` | Privacy & Consent | Yes (legal_documents/no) | privacy_settings, legal_documents, acceptances, data_requests, derived_preferences |
| `vyapar_trust_safety` | Trust & Safety | Yes | moderation_cases, reports, appeals |
| `vyapar_analytics` | Analytics | Yes | analytics_events |
| `vyapar_integration` | Integration Bridges | Yes (config/no) | dead_letters, config, counsel_referrals, notifications, audit_events |
| `vyapar_platform` | (shared infra, not a business component) | Yes (idempotency_key only) | idempotency_key, rate_limit_counter |

**Discovery & Ranking** and the **Authorization Engine** (components #4 and
#13 in `07-tech-reqs.md`) own no tables and have no schema — both are
logic-only, reading through the other components' own public interfaces
(Discovery) or taking an already-resolved context as a parameter (Authorization).

### RLS: what it enforces

Every table gets RLS enabled at creation time, never bolted on later. The
runtime role `vyapar_app` is **non-owning** — `vyapar_owner` (the
migration/DDL role) owns every object, so RLS actually applies (Postgres
silently skips RLS for a table's owner by default — the exact failure mode
`/MODULE-ARCHITECTURE-STANDARD.md` §4 names). One session variable,
`vyapar.authz_context`, holds the platform-resolved member id and is set via
`SET LOCAL` (never plain `SET`, which can leak across pooled connections in
transaction-mode pooling) by the Identity Bridge once per request, per
TR050. A shared helper, `vyapar_identity.is_operator(permission)`, centralizes
the operator-bypass predicate every schema's policies call, reading the same
`operator_permissions` array (`verification|content|commercial|analytics|moderation`)
TR047-TR049 already gate specific admin routes on — so DB-layer and
route-layer authorization cannot silently diverge. A second variable,
`vyapar.service_role`, gates the background outbox dispatcher's read of the
three `outbox_event` tables.

Three **pre-authorization SECURITY DEFINER functions** exist because they
must run before `vyapar.authz_context` is meaningful, or because they need a
narrow, audited exception to a table's own RLS:
- `vyapar_identity.ensure_member(...)` — the just-in-time upsert that
  creates the very member row `vyapar.authz_context` will reference (TR050).
- `vyapar_identity.lookup_member_by_phone(...)` — narrow phone→id resolution
  for Business Workspace invites (TR034), returning only `id, display_name`.
- `vyapar_listings.contacts_for_viewer(...)` — the single call site for
  after-accept contact disclosure (TR002/TR024), taking the caller's
  already-resolved "has an accepted enquiry" boolean as a parameter rather
  than querying `vyapar_enquiries` itself (a same-function cross-schema join
  would violate §4's "no cross-schema join by any component other than the
  schema's own owner").
- `vyapar_commercial.impressions_report(...)` and
  `vyapar_commercial.is_workspace_collaborator(...)` are the same pattern
  applied within Commercial's own schema (TR032, TR034).

### Idempotency and rate-limiting (`vyapar_platform`)

`vyapar_platform.idempotency_key` is the one shared store every
client-queueable mutation (`POST /v1/enquiries`, `/partnership-requests`,
`/reviews`, `/promotions|entitlements|campaigns`, `/reports`) honors via its
`Idempotency-Key` header — member-scoped by both a `UNIQUE(member_id,
idempotency_key, endpoint)` constraint and an RLS policy, since the key is
client-generated and therefore not trustworthy as a global identifier.
`payment_orders.idempotency_key` and `notifications.idempotency_key` stay as
their own existing one-off columns (Payment Bridge's and the Notification
Bridge's own dedicated dedup concerns) — 07-tech-reqs.md's own closing note
says these are fine to keep as-is.

`vyapar_platform.rate_limit_counter` plus
`vyapar_platform.check_and_increment(key, window_seconds, limit)` (the exact
function name 07-tech-reqs.md's Cross-cutting §2 specifies) back the three
rolling-window caps: TR021 (proactive-notification fatigue, 3/day),
TR022 (enquiries, 20/day), TR039 (reports, 10/day). TR025's 10-pending-
partnership-request cap is correctly a plain `COUNT(*) WHERE state='pending'`
query against `vyapar_enquiries.partnership_requests` — no counter table.

## Development and testing

- Seed data (`seeds.sql`) migrates every row from the pre-Step-7a draft
  (`modules/MOD01-vyapar/db/seeds.sql`, left in place for history) into this
  schema-per-component structure. The only structural seed change is
  `promotion_history` → `commercial_order_history` (TR031 gap fix).
- To reset: drop and recreate the database (see Rollback above), then
  `./init.sh` again.
- `migrations/001-initial.sql` is idempotent (`IF NOT EXISTS` throughout,
  `DROP POLICY IF EXISTS` before every `CREATE POLICY`) — safe to re-run
  against an already-migrated database.

## Links

- `/ARCHITECTURE.md` — system-wide data ownership and Vyapar's container placement.
- `/MODULE-ARCHITECTURE-STANDARD.md` — why schema-per-component, RLS, `SET LOCAL`, and the shared idempotency/rate-limit utilities are structured this way.
- `../07-tech-reqs.md` — TR001-TR055 and the "Closing note for Step 7a" that named every gap this implementation resolves.
- `../07a-er-model.md` — full entity/attribute traceability, RLS policy table, and the three-pass cross-validation record.
