-- =============================================================================
-- Migration 001 — initial schema. No dependency (first migration for MOD02).
-- Idempotent: every CREATE SCHEMA/TABLE/INDEX uses IF NOT EXISTS, every
-- CREATE TYPE is wrapped in a duplicate_object-tolerant DO block, and every
-- CREATE POLICY is preceded by a matching DROP POLICY IF EXISTS — safe to
-- re-run against a database that already has it applied.
-- =============================================================================
-- =============================================================================
-- Milavn (MOD02) — Postgres schema DDL
-- Snapshot of the current schema, equivalent to applying every file in
-- migrations/ in order. Keep this file and migrations/ in sync — this file
-- exists for fast local/dev setup (init.sh runs it directly); migrations/ is
-- the authoritative, ordered history. See 07a-db-implementation/README.md.
--
-- Traces to: modules/MOD02-milavn/07a-er-model.md (full traceability table),
-- 07-tech-reqs.md (TR01-TR47, TR-PLAT-01, TR-CROSSCUT-01..04), architecture.md
-- (12-component, 10-schema decomposition), /MODULE-ARCHITECTURE-STANDARD.md
-- §4/§4b/§4c/§5/§6.
--
-- Milavn lives in the Core Platform monolith's SHARED database (not an
-- isolated one — unlike Mangaly), per /ARCHITECTURE.md ADR-001/ADR-002. This
-- file only creates/owns the milavn_* schemas; it never touches any other
-- module's schema in the same database.
--
-- Design conventions applied uniformly (see 07a-er-model.md "Assumptions"
-- for the full reasoning on each):
--   1. One Postgres schema per schema-owning component (architecture.md §3):
--      milavn_profile, milavn_discovery, milavn_activity, milavn_circle,
--      milavn_trust, milavn_locationprivacy, milavn_connect, milavn_publicpage,
--      milavn_notification, milavn_safety — ten schemas, exactly as
--      architecture.md fixes. Identity Bridge and Audit Bridge are genuinely
--      schema-less thin bridges (no tables). PLUS one infrastructure schema,
--      milavn_platform, for the shared idempotency/rate-limit utilities
--      (MODULE-ARCHITECTURE-STANDARD §4b/§4c) — cross-cutting, not a
--      business-logic component, so it does not add to or compete with
--      architecture.md's fixed ten-schema business list (same reasoning
--      Mangaly's own 07a-er-model.md already used for mangaly_platform).
--   2. Every table has id (uuid pk), created_at, updated_at (except
--      append-only event/log/history tables, which have created_at/
--      occurred_at only — an update would violate their append-only intent).
--   3. Cross-schema references (e.g. an Occurrence's circle_id pointing into
--      milavn_circle, or any member_id pointing at the platform Identity &
--      Trust Service's own Member table) are stored as plain, indexed UUID
--      columns with NO database-level FOREIGN KEY constraint — a real FK
--      would require granting cross-schema SELECT and would let one
--      component's schema silently depend on another's internal row
--      lifecycle, exactly what "no cross-schema join written by any
--      component other than the schema's own owner" (MODULE-ARCHITECTURE-
--      STANDARD §4) forbids. Referential integrity across schemas/services is
--      enforced by the owning component's own public interface at the
--      application layer, not the DB. Within one schema (same owning
--      component), real FK constraints with an explicit cascade rule are
--      used.
--   4. RLS: every table whose rows carry meaningful privacy sensitivity gets
--      RLS enabled at creation time (never bolted on later) per
--      MODULE-ARCHITECTURE-STANDARD §4. The runtime role (milavn_app) is a
--      NON-OWNING role — milavn_owner (migration role) owns every object, so
--      RLS is never silently bypassed by table ownership (§4's first named
--      failure mode). RLS policies key off session variables the
--      Authorization Engine sets with SET LOCAL (never plain SET, §4's
--      second named failure mode — this platform runs behind PgBouncer-class
--      pooling at scale, per TR16):
--        milavn.member_id         — the authenticated actor's own member id
--                                    (opaque reference into Identity & Trust
--                                    Service; resolved once per request).
--        milavn.permission_scope  — comma-separated resolved permission
--                                    scopes for this request (e.g.
--                                    'milavn.moderate' for a moderator acting
--                                    through TR-PLAT-01's console).
--        milavn.internal_service  — 'true' only when the calling code path is
--                                    the platform's own internal reputation-
--                                    scoring engine (ADR-005) reading
--                                    Milavn's write-only-by-Milavn reputation
--                                    signal log — never set for an ordinary
--                                    API request.
--   5. Outbox pattern (MODULE-ARCHITECTURE-STANDARD §6 / TR-CROSSCUT-04):
--      the four components that publish to the in-process event bus per
--      architecture.md §3 (Activity & Occurrence, Circle, Trust & Reputation,
--      Safety & Moderation) each get their own <schema>.outbox_event table so
--      the event insert commits in the exact same transaction as the state
--      change it describes. Notification Dispatch owns a second, distinct
--      outbox (milavn_notification.notification_outbox) for its own OUTBOUND
--      publish to the platform Message Broker / Notification & Communication
--      Service (TR13/TR37, ADR-006) — a different edge (module → external
--      service) from the in-process bus.
--   6. Idempotency (TR-CROSSCUT-01, MODULE-ARCHITECTURE-STANDARD §4b) is
--      implemented ONCE, at the API layer, via milavn_platform.idempotency_key
--      — not as a column re-implemented on every mutable table — exactly the
--      "owned by the API-layer component, not reimplemented per business-
--      logic component" instruction TR-CROSSCUT-01 states. It covers the
--      four endpoints named there: activity/occurrence creation (TR07),
--      participation toggle (TR12), report submission (TR41), feedback
--      submission (TR44).
--   7. Rate-limiting (TR-CROSSCUT-02, MODULE-ARCHITECTURE-STANDARD §4c) is
--      implemented ONCE via milavn_platform.rate_limit_counter, called by
--      every abuse-prone endpoint (report submission, activity creation,
--      participation toggling) — never a per-endpoint counter.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Extensions. Roles are NOT created here.
-- -----------------------------------------------------------------------------
-- Postgres roles are cluster-wide (shared across every database on the
-- server, and in this project's case shared across every module living in
-- the Core Platform monolith's one database), not database-local objects,
-- and creating one requires the CREATEROLE attribute (or superuser). A
-- migration running as the non-superuser milavn_owner role cannot create
-- roles, by design (confirmed by the identical, already-live-verified
-- finding in Mangaly's own migration, see modules/MOD03-mangaly/
-- 07a-er-model.md revision log). Role provisioning is therefore an
-- infrastructure/ops step init.sh performs BEFORE running this file, as an
-- actual superuser/admin connection — see init.sh Step 2. This migration
-- only assumes milavn_owner and milavn_app already exist and grants
-- privileges to them; it never attempts CREATE ROLE.
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- Discovery's embedded Postgres full-text/filter search (TR03/TR06, ADR-007/ADR-018)

-- =============================================================================
-- 1. milavn_platform — shared cross-cutting utilities
-- [TR-CROSSCUT-01, TR-CROSSCUT-02, MODULE-ARCHITECTURE-STANDARD §4b/§4c]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_platform AUTHORIZATION milavn_owner;

-- [TR-CROSSCUT-01] One shared idempotency mechanism for every client-
-- queueable mutation endpoint this module names: activity/occurrence
-- creation (TR07), participation toggle (TR12), report submission (TR41),
-- feedback submission (TR44). The API layer looks up (endpoint, actor,
-- idempotency_key) before executing a mutation; on a repeat, it returns
-- response_snapshot verbatim instead of re-executing.
CREATE TABLE IF NOT EXISTS milavn_platform.idempotency_key (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint          text NOT NULL,
  actor_member_id   uuid NOT NULL,
  idempotency_key   text NOT NULL,
  request_hash      text NOT NULL,
  response_status   integer NOT NULL,
  response_snapshot jsonb NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT idempotency_key_unique UNIQUE (endpoint, actor_member_id, idempotency_key)
);
COMMENT ON TABLE milavn_platform.idempotency_key IS
  '[TR-CROSSCUT-01/TR07/TR12/TR41/TR44] Single shared idempotency store for every client-retryable mutation in this module. Not per-endpoint.';
CREATE INDEX IF NOT EXISTS idx_idempotency_key_created_at ON milavn_platform.idempotency_key (created_at);

-- [TR-CROSSCUT-02] One shared, DB-backed, parameterized rate-limiting
-- utility for every abuse-prone endpoint (report submission, activity
-- creation, participation toggling). Fixed-window counter; key encodes
-- endpoint+actor+window boundary.
CREATE TABLE IF NOT EXISTS milavn_platform.rate_limit_counter (
  rate_key      text NOT NULL,
  window_start  timestamptz NOT NULL,
  attempt_count integer NOT NULL DEFAULT 1,
  limit_max     integer NOT NULL,
  updated_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (rate_key, window_start)
);
COMMENT ON TABLE milavn_platform.rate_limit_counter IS
  '[TR-CROSSCUT-02] Single shared rate-limiting utility for every abuse-prone Milavn endpoint. Not per-endpoint.';

GRANT USAGE ON SCHEMA milavn_platform TO milavn_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA milavn_platform TO milavn_app;

-- =============================================================================
-- 2. milavn_profile — Member Profile
-- [TR01, FR001-FR003, FR085]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_profile AUTHORIZATION milavn_owner;

-- [TR01/FR001] member_id is a foreign-key REFERENCE ONLY into Identity &
-- Trust Service's own Member record (ADR-004) — Milavn never forks its own
-- login/identity table, so there is no local FK, just a stored id.
CREATE TABLE IF NOT EXISTS milavn_profile.member_profile (
  member_id           uuid PRIMARY KEY,
  locality_city        text NOT NULL,
  locality_zone        text,
  locality_locality     text,
  language_preference  text NOT NULL DEFAULT 'en',  -- ADR-010 day-one set: en/hi/te; per-person override of the shared i18n default
  photo_media_id       uuid,   -- nullable FK -> member_profile_media.id; enrichment, never gates any read/write path (TR01)
  bio                  text,   -- nullable enrichment
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_profile.member_profile IS
  '[TR01/FR001-FR003] Minimal required profile (locality + language) plus optional enrichment (photo/bio). PII-sensitive (locality is approximate, never exact address, per BR09/TR29). Required fields never include photo/bio (TR01 two-transaction save).';
COMMENT ON COLUMN milavn_profile.member_profile.locality_city IS 'Required at signup (FR001). Approximate hierarchy top level (BR09/TR29).';

-- [TR01/FR001] Interest tags — many-to-many, at least one required for a
-- Discovery-eligible profile (enforced at the application layer per BR01's
-- "must not require more than locality + interests").
CREATE TABLE IF NOT EXISTS milavn_profile.member_interest (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id    uuid NOT NULL REFERENCES milavn_profile.member_profile (member_id) ON DELETE CASCADE,
  interest_tag text NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT member_interest_unique UNIQUE (member_id, interest_tag)
);
COMMENT ON TABLE milavn_profile.member_interest IS '[TR01/FR001] Interest tags feeding Discovery ranking (TR05).';
CREATE INDEX IF NOT EXISTS idx_member_interest_member_id ON milavn_profile.member_interest (member_id);
CREATE INDEX IF NOT EXISTS idx_member_interest_tag ON milavn_profile.member_interest (interest_tag);

-- [TR01/FR003] Photo/cover-image uploads go through Object Storage/CDN via a
-- pre-signed URL; this row exists independently of member_profile's own
-- save (two-transaction pattern) so a failed/slow upload never blocks
-- profile save. upload_status lets the client poll without blocking.
DO $$ BEGIN
  CREATE TYPE milavn_profile.media_upload_status AS ENUM ('pending','completed','failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS milavn_profile.member_profile_media (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id       uuid NOT NULL REFERENCES milavn_profile.member_profile (member_id) ON DELETE CASCADE,
  storage_ref     text,   -- nullable until upload completes
  upload_status   milavn_profile.media_upload_status NOT NULL DEFAULT 'pending',
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_profile.member_profile_media IS
  '[TR01/FR003] Profile photo reference. Object Storage outage cannot block profile save — write is a separate transaction from member_profile itself.';
CREATE INDEX IF NOT EXISTS idx_member_profile_media_member_id ON milavn_profile.member_profile_media (member_id);

ALTER TABLE milavn_profile.member_profile ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_profile_self_or_public_cols ON milavn_profile.member_profile;
-- [TR01, MODULE-ARCHITECTURE-STANDARD §4] Full-row access restricted to the
-- profile's own owner. Other components needing a NON-sensitive subset
-- (locality/interests for ranking, language for rendering) read through
-- milavn_profile.member_public_profile (a view, defined below), which is
-- what Discovery/Circle/Notification etc. are expected to query per §4's
-- "goes through that component's own public interface" rule — RLS on the
-- base table is the second, database-enforced layer behind that discipline.
CREATE POLICY member_profile_self_or_public_cols ON milavn_profile.member_profile
  FOR ALL
  USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

CREATE OR REPLACE VIEW milavn_profile.member_public_profile
  WITH (security_invoker = true) AS
  SELECT member_id, locality_city, locality_zone, locality_locality, language_preference
  FROM milavn_profile.member_profile;
COMMENT ON VIEW milavn_profile.member_public_profile IS
  '[TR01] Non-sensitive projection (no photo/bio) other components read cross-schema instead of the RLS-restricted base table.';

ALTER TABLE milavn_profile.member_interest ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_interest_self ON milavn_profile.member_interest;
CREATE POLICY member_interest_self ON milavn_profile.member_interest
  FOR ALL
  USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_profile.member_profile_media ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_profile_media_self ON milavn_profile.member_profile_media;
CREATE POLICY member_profile_media_self ON milavn_profile.member_profile_media
  FOR ALL
  USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

GRANT USAGE ON SCHEMA milavn_profile TO milavn_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA milavn_profile TO milavn_app;
GRANT SELECT ON milavn_profile.member_public_profile TO milavn_app;

-- =============================================================================
-- 3. milavn_discovery — Discovery & Ranking
-- [TR03, TR05, TR06, FR004-FR009, FR033]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_discovery AUTHORIZATION milavn_owner;

-- [TR05] Ranking weights live in a versioned config row, never hardcoded per
-- call site, so tuning is a config change (auditable via this table's own
-- history) rather than a silent code edit. Exactly one row has
-- effective_to IS NULL (the currently-active version) at any time.
CREATE TABLE IF NOT EXISTS milavn_discovery.ranking_weight_config (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version           integer NOT NULL,
  locality_weight   numeric(5,4) NOT NULL,
  interest_weight   numeric(5,4) NOT NULL,
  trust_weight      numeric(5,4) NOT NULL,
  freshness_weight  numeric(5,4) NOT NULL,
  effective_from    timestamptz NOT NULL DEFAULT now(),
  effective_to      timestamptz,
  created_by_member_id uuid,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ranking_weight_config_version_unique UNIQUE (version)
);
COMMENT ON TABLE milavn_discovery.ranking_weight_config IS
  '[TR05] Versioned ranking-formula weights (locality/interest/trust/freshness). Popularity/engagement counters are deliberately never a column here (PRODUCT-GUARDRAILS.md ranking philosophy).';
CREATE INDEX IF NOT EXISTS idx_ranking_weight_config_active ON milavn_discovery.ranking_weight_config (effective_to) WHERE effective_to IS NULL;

GRANT USAGE ON SCHEMA milavn_discovery TO milavn_app;
GRANT SELECT ON ALL TABLES IN SCHEMA milavn_discovery TO milavn_app;

-- =============================================================================
-- 4. milavn_circle — Circle (including the minimal OrganizationScope, TR23)
-- [TR16-TR24, FR020-FR029]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_circle AUTHORIZATION milavn_owner;

DO $$ BEGIN
  CREATE TYPE milavn_circle.circle_type AS ENUM ('public','community','private','organization','interest','local','recurring_activity');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_circle.circle_member_role AS ENUM ('member','organizer');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_circle.suggestion_status AS ENUM ('pending','accepted','declined');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR16/TR21/FR020-FR021] Circle type is an enum, enforced at write time,
-- never a free-text field (TR16).
CREATE TABLE IF NOT EXISTS milavn_circle.circle (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                text NOT NULL,
  circle_type         milavn_circle.circle_type NOT NULL,
  description         text,
  created_by_member_id uuid NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_circle.circle IS '[TR16/FR020-FR021] Persistent community group; type drives every visibility rule downstream (TR20/TR24/TR30).';
CREATE INDEX IF NOT EXISTS idx_circle_type ON milavn_circle.circle (circle_type);

CREATE INDEX IF NOT EXISTS idx_circle_created_by ON milavn_circle.circle (created_by_member_id);

-- [TR16/FR020/FR023] Join/leave is immediate for the acting member;
-- left_at IS NULL marks current membership. No approval gate for a
-- voluntary leave (FR020) or for any other capability outside Circle
-- itself (FR023/TR18).
CREATE TABLE IF NOT EXISTS milavn_circle.circle_membership (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id    uuid NOT NULL REFERENCES milavn_circle.circle (id) ON DELETE CASCADE,
  member_id    uuid NOT NULL,
  member_role  milavn_circle.circle_member_role NOT NULL DEFAULT 'member',
  joined_at    timestamptz NOT NULL DEFAULT now(),
  left_at      timestamptz
);
COMMENT ON TABLE milavn_circle.circle_membership IS '[TR16/FR020/FR023/TR18] Circle membership. TR18: never referenced by any authorization check outside this component''s own interface.';
CREATE INDEX IF NOT EXISTS idx_circle_membership_circle ON milavn_circle.circle_membership (circle_id);
CREATE INDEX IF NOT EXISTS idx_circle_membership_member ON milavn_circle.circle_membership (member_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_circle_membership_active_unique
  ON milavn_circle.circle_membership (circle_id, member_id) WHERE left_at IS NULL;

-- [TR17/FR022] Suggestion-only output of the nightly co-participation batch
-- job — never auto-creates a circle (PRODUCT-GUARDRAILS.md).
-- [MODULE-ARCHITECTURE-STANDARD §4 RLS] SECURITY DEFINER helper functions,
-- owned by milavn_owner (the table owner). Postgres exempts a table's OWNER
-- from RLS regardless of who calls a SECURITY DEFINER function it owns —
-- these functions exist specifically so `circle`'s own RLS policy can check
-- `circle_membership`, and `circle_membership`'s own RLS policy can check
-- itself/`circle`, WITHOUT each policy's subquery re-triggering the other
-- table's RLS and recursing (found live: "infinite recursion detected in
-- policy for relation circle_membership" when this was first written as a
-- direct cross-table EXISTS subquery — fixed here, not worked around).
CREATE OR REPLACE FUNCTION milavn_circle.is_active_member(p_circle_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (
    SELECT 1 FROM milavn_circle.circle_membership
    WHERE circle_id = p_circle_id AND member_id = p_member_id AND left_at IS NULL
  );
$$;
COMMENT ON FUNCTION milavn_circle.is_active_member IS 'RLS-recursion-safe membership check (SECURITY DEFINER, bypasses RLS as the owning role). Used by circle/circle_membership/occurrence policies.';

CREATE OR REPLACE FUNCTION milavn_circle.is_open_circle(p_circle_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT circle_type IN ('public','community') FROM milavn_circle.circle WHERE id = p_circle_id;
$$;
COMMENT ON FUNCTION milavn_circle.is_open_circle IS 'RLS-recursion-safe circle-type check (SECURITY DEFINER).';

CREATE OR REPLACE FUNCTION milavn_circle.is_circle_creator(p_circle_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_circle.circle WHERE id = p_circle_id AND created_by_member_id = p_member_id);
$$;
COMMENT ON FUNCTION milavn_circle.is_circle_creator IS 'RLS-recursion-safe circle-creator check (SECURITY DEFINER).';
CREATE TABLE IF NOT EXISTS milavn_circle.circle_formation_suggestion (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_activity_id    uuid,   -- cross-schema ref -> milavn_activity.activity(id) or occurrence(id), no FK
  suggested_circle_name text NOT NULL,
  status                milavn_circle.suggestion_status NOT NULL DEFAULT 'pending',
  created_at            timestamptz NOT NULL DEFAULT now(),
  responded_at          timestamptz
);
COMMENT ON TABLE milavn_circle.circle_formation_suggestion IS '[TR17/FR022] Scheduled-batch-job output; requires explicit member acceptance before any circle is created.';

CREATE TABLE IF NOT EXISTS milavn_circle.circle_formation_suggestion_member (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  suggestion_id  uuid NOT NULL REFERENCES milavn_circle.circle_formation_suggestion (id) ON DELETE CASCADE,
  member_id      uuid NOT NULL,
  responded_at   timestamptz,
  CONSTRAINT circle_formation_suggestion_member_unique UNIQUE (suggestion_id, member_id)
);
COMMENT ON TABLE milavn_circle.circle_formation_suggestion_member IS '[TR17/FR022] Recipients of one circle-formation suggestion.';
CREATE INDEX IF NOT EXISTS idx_cfsm_member ON milavn_circle.circle_formation_suggestion_member (member_id);

-- [TR23, DEC-001 — deliberately minimal, no roster/roles/verification/
-- billing] Sole writer is created_by_member_id (TR23: "whoever created the
-- OrganizationScope record is its only writer for V1; there is no
-- invite/join flow for it").
CREATE TABLE IF NOT EXISTS milavn_circle.organization_scope (
  organization_scope_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name          text NOT NULL,
  created_by_member_id  uuid NOT NULL,
  created_at            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_circle.organization_scope IS
  '[TR23/FR028] Deliberately minimal Calendar-scope tag. NO roster, roles, verification, or billing — expanding this table''s shape without a new BR/FR pass is explicitly out of bounds per TR23 DEC-001.';

CREATE TABLE IF NOT EXISTS milavn_circle.outbox_event (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    text NOT NULL,
  aggregate_id  uuid NOT NULL,
  payload       jsonb NOT NULL,
  occurred_at   timestamptz NOT NULL DEFAULT now(),
  dispatched_at timestamptz
);
COMMENT ON TABLE milavn_circle.outbox_event IS '[TR-CROSSCUT-04] In-process domain event outbox for Circle.';
CREATE INDEX IF NOT EXISTS idx_circle_outbox_event_undispatched ON milavn_circle.outbox_event (occurred_at) WHERE dispatched_at IS NULL;

ALTER TABLE milavn_circle.circle ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_visibility ON milavn_circle.circle;
-- [TR16/TR20/FR025] Public/Community circles are broadly visible;
-- Private/Organization/Interest/Local/Recurring-Activity circles are
-- visible only to their own members (or the creator before any membership
-- row exists).
CREATE POLICY circle_visibility ON milavn_circle.circle
  FOR SELECT
  USING (
    circle_type IN ('public','community')
    OR created_by_member_id = current_setting('milavn.member_id', true)::uuid
    OR milavn_circle.is_active_member(circle.id, current_setting('milavn.member_id', true)::uuid)
  );
DROP POLICY IF EXISTS circle_write ON milavn_circle.circle;
CREATE POLICY circle_write ON milavn_circle.circle
  FOR INSERT WITH CHECK (created_by_member_id = current_setting('milavn.member_id', true)::uuid);
DROP POLICY IF EXISTS circle_modify ON milavn_circle.circle;
CREATE POLICY circle_modify ON milavn_circle.circle
  FOR UPDATE USING (created_by_member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_circle.circle_membership ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_membership_visibility ON milavn_circle.circle_membership;
-- [FR024 — Community Memory visible at minimum to circle's own members;
-- non-Public circles do not expose stats/roster beyond members]
CREATE POLICY circle_membership_visibility ON milavn_circle.circle_membership
  FOR SELECT
  USING (
    milavn_circle.is_open_circle(circle_membership.circle_id)
    OR member_id = current_setting('milavn.member_id', true)::uuid
    OR milavn_circle.is_active_member(circle_membership.circle_id, current_setting('milavn.member_id', true)::uuid)
  );
DROP POLICY IF EXISTS circle_membership_self_write ON milavn_circle.circle_membership;
-- [FR020] A member's own join/leave never requires another member's
-- approval — this policy restricts WRITE to the acting member's own row
-- (or the circle creator seeding initial membership at creation time).
CREATE POLICY circle_membership_self_write ON milavn_circle.circle_membership
  FOR INSERT WITH CHECK (
    member_id = current_setting('milavn.member_id', true)::uuid
    OR milavn_circle.is_circle_creator(circle_membership.circle_id, current_setting('milavn.member_id', true)::uuid)
  );
DROP POLICY IF EXISTS circle_membership_self_leave ON milavn_circle.circle_membership;
CREATE POLICY circle_membership_self_leave ON milavn_circle.circle_membership
  FOR UPDATE USING (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_circle.circle_formation_suggestion_member ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cfsm_self ON milavn_circle.circle_formation_suggestion_member;
CREATE POLICY cfsm_self ON milavn_circle.circle_formation_suggestion_member
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid);

GRANT USAGE ON SCHEMA milavn_circle TO milavn_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA milavn_circle TO milavn_app;

-- =============================================================================
-- 5. milavn_activity — Activity & Occurrence (highest-scrutiny schema, TR08)
-- [TR07-TR15, TR38-TR40, TR44 (feedback trigger only), FR010-FR019,
--  FR058-FR060]
--
-- TR08's behavioral contract, implemented here exactly as follows:
--   - `occurrence` carries every field a single concrete instance actually
--     needs to exist and be participated in on its own — title, intent
--     category, time, place, capacity, visibility scope, high-risk flag,
--     etc. It NEVER requires a parent `activity` row (activity_id is
--     nullable) — this is what satisfies BR03's "non-forced-wrapper" rule
--     for a one-off event (TS021/TS022).
--   - `activity` is a genuinely optional, lightweight RECURRING-SERIES
--     wrapper: it exists only when a creator explicitly marks something as
--     recurring, and it owns only the umbrella-level fields (title/intent
--     category as the series' own canonical values, the recurrence rule).
--     It is never required to create, participate in, or view a single
--     occurrence.
--   - Every FR that reads "activity data" elsewhere (participation,
--     calendar, organizer tools, public page) is written against
--     `occurrence`, never against `activity` directly — resolving TR08's
--     "must resolve to a specific Occurrence, never an ambiguous
--     Activity-level record" requirement structurally: there is no
--     Activity-level participation, calendar entry, or public page table at
--     all, only Occurrence-level ones. History/attendance aggregation "at
--     the Activity level" (FR011, BR03) is achieved by joining Occurrence
--     rows through their shared, optional activity_id — a read-time
--     aggregation, not a duplicated write.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_activity AUTHORIZATION milavn_owner;

DO $$ BEGIN
  CREATE TYPE milavn_activity.intent_category AS ENUM ('play','meet','eat','learn','work','explore','celebrate','help');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_activity.visibility_scope AS ENUM ('personal','circle','organization','community','public');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_activity.occurrence_status AS ENUM ('active','cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_activity.participation_status AS ENUM ('interested','going','waitlisted','cancelled','checked_in','attended','no_show');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR08/FR011] The optional recurring-series umbrella. Only ever created
-- when a creator marks something recurring (FR010/FR013) — never a forced
-- wrapper for a standalone Occurrence.
CREATE TABLE IF NOT EXISTS milavn_activity.activity (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  creator_member_id   uuid NOT NULL,
  title               text NOT NULL,
  intent_category     milavn_activity.intent_category NOT NULL,
  recurrence_rule     jsonb NOT NULL,   -- e.g. {"freq":"weekly","by_day":"SUN"} — implementation-stage shape, TR10
  cancelled_at        timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_activity.activity IS
  '[TR08/TR10/FR011] Optional recurring-series umbrella. Exists only for recurring activities (BR03 DEC-001) — never required for a standalone Occurrence (TS021/TS022 non-forced-wrapper rule).';
CREATE INDEX IF NOT EXISTS idx_activity_creator ON milavn_activity.activity (creator_member_id);

-- [TR07/TR08/TR09/TR10/FR010-FR014] The concrete, participable unit. Every
-- other FR in this module that touches "activity data" resolves here.
CREATE TABLE IF NOT EXISTS milavn_activity.occurrence (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  activity_id           uuid REFERENCES milavn_activity.activity (id) ON DELETE RESTRICT,  -- nullable: TR08 non-forced-wrapper
  creator_member_id     uuid NOT NULL,
  title                 text NOT NULL,
  description           text,
  intent_category       milavn_activity.intent_category NOT NULL,
  time_start            timestamptz NOT NULL,
  time_end              timestamptz,
  locality_city         text NOT NULL,
  locality_zone         text,
  locality_locality      text,
  capacity              integer,        -- nullable: no cap set (TR10 progressive disclosure)
  cover_image_media_id  uuid,           -- nullable enrichment (TR10), never blocks save
  high_risk             boolean NOT NULL DEFAULT false,   -- [TR42/FR064]
  visibility_scope      milavn_activity.visibility_scope NOT NULL DEFAULT 'public',
  circle_id             uuid,             -- cross-schema ref -> milavn_circle.circle(id), no FK (§4). Set when visibility_scope='circle'.
  organization_scope_id uuid,             -- cross-schema ref -> milavn_circle.organization_scope(organization_scope_id), no FK. Set when visibility_scope='organization'. [TR23]
  canonical_url_slug    text NOT NULL,    -- [TR11] deterministic from id, generated at creation
  status                milavn_activity.occurrence_status NOT NULL DEFAULT 'active',
  cancelled_at          timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT occurrence_canonical_url_slug_unique UNIQUE (canonical_url_slug),
  CONSTRAINT occurrence_circle_scope_requires_circle CHECK (visibility_scope <> 'circle' OR circle_id IS NOT NULL),
  CONSTRAINT occurrence_org_scope_requires_org CHECK (visibility_scope <> 'organization' OR organization_scope_id IS NOT NULL),
  CONSTRAINT occurrence_scope_tags_mutually_exclusive CHECK (NOT (circle_id IS NOT NULL AND organization_scope_id IS NOT NULL))
);
COMMENT ON TABLE milavn_activity.occurrence IS
  '[TR07-TR14/TR23/TR36/TR42/FR010-FR014/FR028-FR029/FR038/FR050/FR064] The concrete, dated, participable instance — one row per real-world session, whether or not it belongs to a recurring Activity. visibility_scope drives Calendar (TR21/TR22/TR23/TR24) and Public Page (TR33/TR36) queries identically for Circle/Organization scopes (TR23''s own stated design).';
COMMENT ON COLUMN milavn_activity.occurrence.circle_id IS 'Cross-schema reference into milavn_circle.circle — no DB FK per MODULE-ARCHITECTURE-STANDARD §4.';
COMMENT ON COLUMN milavn_activity.occurrence.organization_scope_id IS 'Cross-schema reference into milavn_circle.organization_scope — no DB FK. TR23: minimal scope tag only, no roster/roles.';
CREATE INDEX IF NOT EXISTS idx_occurrence_activity_id ON milavn_activity.occurrence (activity_id);
CREATE INDEX IF NOT EXISTS idx_occurrence_creator ON milavn_activity.occurrence (creator_member_id);
CREATE INDEX IF NOT EXISTS idx_occurrence_time_start ON milavn_activity.occurrence (time_start);
CREATE INDEX IF NOT EXISTS idx_occurrence_locality ON milavn_activity.occurrence (locality_city, locality_zone, locality_locality);
CREATE INDEX IF NOT EXISTS idx_occurrence_visibility_scope ON milavn_activity.occurrence (visibility_scope);
CREATE INDEX IF NOT EXISTS idx_occurrence_circle_id ON milavn_activity.occurrence (circle_id) WHERE circle_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_occurrence_organization_scope_id ON milavn_activity.occurrence (organization_scope_id) WHERE organization_scope_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_occurrence_status ON milavn_activity.occurrence (status);
CREATE INDEX IF NOT EXISTS idx_occurrence_intent_category ON milavn_activity.occurrence (intent_category);

-- [TR38/FR059] Delegable, revocable co-organizer grant — same authorization
-- chokepoint as the primary organizer (TR-CROSSCUT-03).
CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_co_organizer (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id         uuid NOT NULL REFERENCES milavn_activity.occurrence (id) ON DELETE CASCADE,
  member_id             uuid NOT NULL,
  granted_by_member_id  uuid NOT NULL,
  granted_at            timestamptz NOT NULL DEFAULT now(),
  revoked_at            timestamptz,
  CONSTRAINT occurrence_co_organizer_unique UNIQUE (occurrence_id, member_id)
);
COMMENT ON TABLE milavn_activity.occurrence_co_organizer IS '[TR38/FR059] Co-organizer delegation, revocable, per occurrence.';
CREATE INDEX IF NOT EXISTS idx_occurrence_co_organizer_occurrence ON milavn_activity.occurrence_co_organizer (occurrence_id);
CREATE INDEX IF NOT EXISTS idx_occurrence_co_organizer_member ON milavn_activity.occurrence_co_organizer (member_id);

-- [TR13/TR38/FR057] Organizer-authored update/announcement, dispatched to
-- every current participant via Notification Dispatch.
CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_update (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id       uuid NOT NULL REFERENCES milavn_activity.occurrence (id) ON DELETE CASCADE,
  organizer_member_id uuid NOT NULL,
  message             text NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_activity.occurrence_update IS '[TR13/TR38/FR057] Organizer broadcast update/announcement.';
CREATE INDEX IF NOT EXISTS idx_occurrence_update_occurrence ON milavn_activity.occurrence_update (occurrence_id);

-- [TR12/TR39/FR015-FR016/FR058] The single most-repeated write in the
-- module (IA015). waitlist_position supports TR39's concurrency-safe FIFO
-- promotion; NULL unless status='waitlisted'.
CREATE TABLE IF NOT EXISTS milavn_activity.participation (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id      uuid NOT NULL REFERENCES milavn_activity.occurrence (id) ON DELETE CASCADE,
  member_id          uuid NOT NULL,
  status             milavn_activity.participation_status NOT NULL DEFAULT 'interested',
  waitlist_position  integer,
  checked_in_at      timestamptz,
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT participation_unique UNIQUE (occurrence_id, member_id),
  CONSTRAINT participation_waitlist_position_requires_status CHECK (waitlist_position IS NULL OR status = 'waitlisted')
);
COMMENT ON TABLE milavn_activity.participation IS
  '[TR12/TR39/FR015-FR016/FR040/FR058] Attendance-intent/lifecycle record. Private by default (FR040) — visible only to the participant and the occurrence''s organizer/co-organizers, enforced by RLS below.';
CREATE INDEX IF NOT EXISTS idx_participation_occurrence ON milavn_activity.participation (occurrence_id);
CREATE INDEX IF NOT EXISTS idx_participation_member ON milavn_activity.participation (member_id);
CREATE INDEX IF NOT EXISTS idx_participation_status ON milavn_activity.participation (status);
-- [TR39] Ensures waitlist FIFO ordering is unambiguous per occurrence — the
-- row lock taken during promotion (`SELECT ... FROM occurrence ... FOR
-- UPDATE`) combined with this uniqueness prevents two concurrent
-- withdrawals from double-promoting or skipping the same slot.
CREATE UNIQUE INDEX IF NOT EXISTS idx_participation_waitlist_position_unique
  ON milavn_activity.participation (occurrence_id, waitlist_position)
  WHERE status = 'waitlisted';

-- [TR12/FR016] Full status-transition history, queryable by participant and
-- organizer — a status change with no history row is a defect per FR016.
CREATE TABLE IF NOT EXISTS milavn_activity.participation_status_history (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  participation_id    uuid NOT NULL REFERENCES milavn_activity.participation (id) ON DELETE CASCADE,
  old_status          milavn_activity.participation_status,
  new_status          milavn_activity.participation_status NOT NULL,
  changed_by_member_id uuid NOT NULL,
  changed_at          timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_activity.participation_status_history IS '[TR12/FR016] Append-only attendance-status audit trail.';
CREATE INDEX IF NOT EXISTS idx_participation_status_history_participation ON milavn_activity.participation_status_history (participation_id);

-- [TR14/FR018] QR check-in token, short-lived, single-use. Manual-entry
-- fallback (organizer taps a name) uses the same endpoint/table with
-- participation_id set directly and no token — TR14 names this fallback as
-- the primary reliability mechanism, not optional polish.
CREATE TABLE IF NOT EXISTS milavn_activity.qr_checkin_token (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id    uuid NOT NULL REFERENCES milavn_activity.occurrence (id) ON DELETE CASCADE,
  token            text NOT NULL,
  expires_at       timestamptz NOT NULL,
  used_at          timestamptz,
  used_by_participation_id uuid REFERENCES milavn_activity.participation (id),
  created_at       timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT qr_checkin_token_unique UNIQUE (token)
);
COMMENT ON TABLE milavn_activity.qr_checkin_token IS '[TR14/FR018] Scale-gated optional QR check-in token; never required for small sessions.';
CREATE INDEX IF NOT EXISTS idx_qr_checkin_token_occurrence ON milavn_activity.qr_checkin_token (occurrence_id);

-- [TR09/TR13/TR-CROSSCUT-04] Transactional outbox — cancellation/update
-- events published in the same transaction as the state change (IA017).
CREATE TABLE IF NOT EXISTS milavn_activity.outbox_event (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    text NOT NULL,         -- e.g. 'occurrence.cancelled', 'occurrence.updated'
  aggregate_id  uuid NOT NULL,         -- occurrence.id
  payload       jsonb NOT NULL,
  occurred_at   timestamptz NOT NULL DEFAULT now(),
  dispatched_at timestamptz
);
COMMENT ON TABLE milavn_activity.outbox_event IS '[TR09/TR13/TR-CROSSCUT-04] In-process domain event outbox for Activity & Occurrence — never bypassed by a direct cross-component call.';
CREATE INDEX IF NOT EXISTS idx_activity_outbox_event_undispatched ON milavn_activity.outbox_event (occurred_at) WHERE dispatched_at IS NULL;

ALTER TABLE milavn_activity.occurrence ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_visibility ON milavn_activity.occurrence;
-- [TR16/TR20/TR24/TR30/TR36 — IA050's highest-severity check] An occurrence
-- is readable if: it is Public or Community-scoped (broad platform
-- visibility by definition, FR028-FR029); OR the acting member created it
-- or is a co-organizer; OR it is Circle-scoped and the acting member is a
-- member of that circle (checked via milavn_circle.is_active_member(), the
-- same RLS-recursion-safe SECURITY DEFINER helper `circle`/
-- `circle_membership`'s own policies use — a raw cross-schema EXISTS here
-- was tried first and found, live, to be one hop of the same recursive-RLS
-- class of defect this project's helper functions exist to prevent).
-- Organization-scoped occurrences are treated like Community for READ
-- visibility (TR23: the minimal OrganizationScope entity has no roster/
-- membership concept at all, so there is no narrower group to restrict
-- reads to — restriction happens on WRITE, not read, per TR23's "sole
-- writer for V1" rule, enforced by occurrence_write below). A non-public,
-- non-matching occurrence is invisible — including to a direct-id lookup —
-- which is exactly TR36's "404, never 403" requirement at the RLS layer
-- underneath the API's own 404 response.
CREATE POLICY occurrence_visibility ON milavn_activity.occurrence
  FOR SELECT
  USING (
    visibility_scope IN ('public','community','organization')
    OR creator_member_id = current_setting('milavn.member_id', true)::uuid
    OR EXISTS (
      SELECT 1 FROM milavn_activity.occurrence_co_organizer oco
      WHERE oco.occurrence_id = occurrence.id
        AND oco.member_id = current_setting('milavn.member_id', true)::uuid
        AND oco.revoked_at IS NULL
    )
    OR (
      visibility_scope = 'circle' AND circle_id IS NOT NULL
      AND milavn_circle.is_active_member(occurrence.circle_id, current_setting('milavn.member_id', true)::uuid)
    )
  );
DROP POLICY IF EXISTS occurrence_write ON milavn_activity.occurrence;
CREATE POLICY occurrence_write ON milavn_activity.occurrence
  FOR INSERT WITH CHECK (creator_member_id = current_setting('milavn.member_id', true)::uuid);
DROP POLICY IF EXISTS occurrence_update ON milavn_activity.occurrence;
CREATE POLICY occurrence_update ON milavn_activity.occurrence
  FOR UPDATE
  USING (
    creator_member_id = current_setting('milavn.member_id', true)::uuid
    OR EXISTS (
      SELECT 1 FROM milavn_activity.occurrence_co_organizer oco
      WHERE oco.occurrence_id = occurrence.id
        AND oco.member_id = current_setting('milavn.member_id', true)::uuid
        AND oco.revoked_at IS NULL
    )
  );
DROP POLICY IF EXISTS occurrence_delete ON milavn_activity.occurrence;
CREATE POLICY occurrence_delete ON milavn_activity.occurrence
  FOR DELETE USING (creator_member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_activity.participation ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS participation_self_or_organizer ON milavn_activity.participation;
-- [FR040/FR056/TR38] Private attendance by default: visible only to the
-- participant themselves or the occurrence's organizer/co-organizer
-- (attendee-list visibility, FR056) — never to an ordinary participant
-- viewing another participant's row.
CREATE POLICY participation_self_or_organizer ON milavn_activity.participation
  FOR ALL
  USING (
    member_id = current_setting('milavn.member_id', true)::uuid
    OR EXISTS (
      SELECT 1 FROM milavn_activity.occurrence o
      WHERE o.id = participation.occurrence_id
        AND (
          o.creator_member_id = current_setting('milavn.member_id', true)::uuid
          OR EXISTS (
            SELECT 1 FROM milavn_activity.occurrence_co_organizer oco
            WHERE oco.occurrence_id = o.id
              AND oco.member_id = current_setting('milavn.member_id', true)::uuid
              AND oco.revoked_at IS NULL
          )
        )
    )
  )
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_activity.occurrence_update ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_update_participants_and_organizer ON milavn_activity.occurrence_update;
CREATE POLICY occurrence_update_participants_and_organizer ON milavn_activity.occurrence_update
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM milavn_activity.participation p
      WHERE p.occurrence_id = occurrence_update.occurrence_id
        AND p.member_id = current_setting('milavn.member_id', true)::uuid
    )
    OR organizer_member_id = current_setting('milavn.member_id', true)::uuid
  );
DROP POLICY IF EXISTS occurrence_update_organizer_write ON milavn_activity.occurrence_update;
CREATE POLICY occurrence_update_organizer_write ON milavn_activity.occurrence_update
  FOR INSERT WITH CHECK (organizer_member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_activity.occurrence_co_organizer ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_co_organizer_visibility ON milavn_activity.occurrence_co_organizer;
CREATE POLICY occurrence_co_organizer_visibility ON milavn_activity.occurrence_co_organizer
  FOR ALL
  USING (
    member_id = current_setting('milavn.member_id', true)::uuid
    OR granted_by_member_id = current_setting('milavn.member_id', true)::uuid
  );

ALTER TABLE milavn_activity.qr_checkin_token ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS qr_checkin_token_organizer_only ON milavn_activity.qr_checkin_token;
CREATE POLICY qr_checkin_token_organizer_only ON milavn_activity.qr_checkin_token
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM milavn_activity.occurrence o
      WHERE o.id = qr_checkin_token.occurrence_id
        AND (
          o.creator_member_id = current_setting('milavn.member_id', true)::uuid
          OR EXISTS (
            SELECT 1 FROM milavn_activity.occurrence_co_organizer oco
            WHERE oco.occurrence_id = o.id AND oco.member_id = current_setting('milavn.member_id', true)::uuid AND oco.revoked_at IS NULL
          )
        )
    )
    OR current_setting('milavn.internal_service', true) = 'true'  -- scan validation path
  );

GRANT USAGE ON SCHEMA milavn_activity TO milavn_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA milavn_activity TO milavn_app;

-- =============================================================================
-- 6. milavn_trust — Trust & Reputation (including Feedback)
-- [TR25-TR28, TR44, FR030-FR037, FR066-FR069]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_trust AUTHORIZATION milavn_owner;

DO $$ BEGIN
  CREATE TYPE milavn_trust.trust_subject_type AS ENUM ('occurrence','activity','organizer','venue','organization');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_trust.trust_level AS ENUM ('forkhatri_verified','community_verified','partner_verified','external_trusted_source','community_submitted');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_trust.reputation_signal_type AS ENUM ('identity_verified','event_completed','cancellation','attendance_reliable','no_show','report_received','community_contribution','organizer_consistency');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR25/TR30/FR030] Always resolves to exactly one value per subject —
-- enforced by the unique constraint below, never null/ambiguous.
CREATE TABLE IF NOT EXISTS milavn_trust.trust_status (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_type  milavn_trust.trust_subject_type NOT NULL,
  subject_id    uuid NOT NULL,   -- cross-schema/cross-service ref depending on subject_type; no FK (§4)
  trust_level   milavn_trust.trust_level NOT NULL,
  resolved_at   timestamptz NOT NULL DEFAULT now(),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT trust_status_subject_unique UNIQUE (subject_type, subject_id)
);
COMMENT ON TABLE milavn_trust.trust_status IS
  '[TR25/TR26/TR30/FR030-FR032] Visible-label trust taxonomy, never a purchasable/opaque score. Venues/Organizations share the Partner Verified path (TR26/FR032) — no separate venue-specific row shape.';
CREATE INDEX IF NOT EXISTS idx_trust_status_subject ON milavn_trust.trust_status (subject_type, subject_id);

-- [TR27/FR034 — internal-only, never exposed raw] Append-only log of named
-- behaviours; the qualitative-only API contract (TR28) is a VIEW-layer/
-- application concern over this table, never a raw pass-through.
CREATE TABLE IF NOT EXISTS milavn_trust.reputation_signal (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id             uuid NOT NULL,
  signal_type           milavn_trust.reputation_signal_type NOT NULL,
  source_occurrence_id  uuid,   -- cross-schema ref -> milavn_activity.occurrence(id), no FK; nullable (some signals aren't occurrence-specific, e.g. identity_verified)
  weight                numeric(6,3) NOT NULL,
  recorded_at           timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_trust.reputation_signal IS
  '[TR27/TR28/FR034-FR037/TR15/TR69 — internal-only] Never surfaced as a raw number to any client (FR035/FR037); no payment event may ever write here (FR036 standing structural gate). A single No-Show never triggers an automated consequential action by itself (TR15/FR019/FR069) — this table is read-only input to reputation display, never a trigger for moderation action.';
CREATE INDEX IF NOT EXISTS idx_reputation_signal_member ON milavn_trust.reputation_signal (member_id);
CREATE INDEX IF NOT EXISTS idx_reputation_signal_type ON milavn_trust.reputation_signal (signal_type);

-- [TR44/FR066-FR069 — optional, internal-only, never a precondition]
CREATE TABLE IF NOT EXISTS milavn_trust.feedback (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id          uuid NOT NULL,   -- cross-schema ref -> milavn_activity.occurrence(id), no FK
  participant_member_id  uuid NOT NULL,
  rating_internal        smallint,
  comments_internal      text,
  submitted_at           timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT feedback_unique UNIQUE (occurrence_id, participant_member_id),
  CONSTRAINT feedback_rating_range CHECK (rating_internal IS NULL OR (rating_internal BETWEEN 1 AND 5))
);
COMMENT ON TABLE milavn_trust.feedback IS
  '[TR44/FR066-FR069 — internal-only] Optional post-event feedback. Feeds reputation_signal as a read-only input; never surfaced publicly beyond TR28''s qualitative contract; never a precondition anywhere else (CI-scan-enforced per TR44).';
CREATE INDEX IF NOT EXISTS idx_feedback_occurrence ON milavn_trust.feedback (occurrence_id);

CREATE TABLE IF NOT EXISTS milavn_trust.outbox_event (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    text NOT NULL,
  aggregate_id  uuid NOT NULL,
  payload       jsonb NOT NULL,
  occurred_at   timestamptz NOT NULL DEFAULT now(),
  dispatched_at timestamptz
);
COMMENT ON TABLE milavn_trust.outbox_event IS '[TR-CROSSCUT-04] In-process domain event outbox for Trust & Reputation.';
CREATE INDEX IF NOT EXISTS idx_trust_outbox_event_undispatched ON milavn_trust.outbox_event (occurred_at) WHERE dispatched_at IS NULL;

-- trust_status carries no personal sensitivity beyond what's already
-- publicly displayed on cards/pages by design (FR031) — no RLS required.
GRANT USAGE ON SCHEMA milavn_trust TO milavn_app;
GRANT SELECT, INSERT, UPDATE ON milavn_trust.trust_status TO milavn_app;
GRANT SELECT ON milavn_trust.outbox_event TO milavn_app;
GRANT INSERT ON milavn_trust.outbox_event TO milavn_app;

ALTER TABLE milavn_trust.reputation_signal ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reputation_signal_internal_only ON milavn_trust.reputation_signal;
-- [FR035/FR037 — never a raw score reachable by a client] Ordinary
-- application requests get ZERO rows; only the internal reputation-scoring
-- engine (milavn.internal_service = 'true', ADR-005) and the writing
-- component itself may read/write this table directly.
CREATE POLICY reputation_signal_internal_only ON milavn_trust.reputation_signal
  FOR ALL
  USING (current_setting('milavn.internal_service', true) = 'true')
  WITH CHECK (current_setting('milavn.internal_service', true) = 'true');
GRANT SELECT, INSERT ON milavn_trust.reputation_signal TO milavn_app;

ALTER TABLE milavn_trust.feedback ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS feedback_self_or_internal ON milavn_trust.feedback;
CREATE POLICY feedback_self_or_internal ON milavn_trust.feedback
  FOR ALL
  USING (
    participant_member_id = current_setting('milavn.member_id', true)::uuid
    OR current_setting('milavn.internal_service', true) = 'true'
  )
  WITH CHECK (participant_member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT ON milavn_trust.feedback TO milavn_app;

-- =============================================================================
-- 7. milavn_locationprivacy — Location & Privacy
-- [TR30, FR038-FR041]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_locationprivacy AUTHORIZATION milavn_owner;

DO $$ BEGIN
  CREATE TYPE milavn_locationprivacy.precision_level AS ENUM ('city','zone','locality','precise');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_locationprivacy.consent_type AS ENUM ('precise_location');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR30/FR041] Single, centrally-enforced source every location-consuming
-- feature must query through a shared helper — never independently
-- re-checked per consumer (IA041).
CREATE TABLE IF NOT EXISTS milavn_locationprivacy.location_precision_setting (
  member_id       uuid PRIMARY KEY,
  precision_level milavn_locationprivacy.precision_level NOT NULL DEFAULT 'locality',
  updated_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_locationprivacy.location_precision_setting IS
  '[TR30/FR038/FR041] Default never exceeds locality-level (approximate hierarchy, BR09) unless the member explicitly raises it, and a feature may never use a more precise level than this setting (FR041).';

-- [TR30/FR039] Precise location requires an explicit, specific consent
-- record before any feature may request it — no current caller (standing
-- guardrail, verified structurally).
CREATE TABLE IF NOT EXISTS milavn_locationprivacy.consent_grant (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id          uuid NOT NULL,
  consent_type       milavn_locationprivacy.consent_type NOT NULL,
  granted_to_context text NOT NULL,   -- e.g. the specific feature/purpose the consent covers
  granted_at         timestamptz NOT NULL DEFAULT now(),
  revoked_at         timestamptz
);
COMMENT ON TABLE milavn_locationprivacy.consent_grant IS '[TR30/FR039] Explicit, purpose-specific consent required before any precise-location disclosure.';
CREATE INDEX IF NOT EXISTS idx_consent_grant_member ON milavn_locationprivacy.consent_grant (member_id);

ALTER TABLE milavn_locationprivacy.location_precision_setting ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS location_precision_setting_self ON milavn_locationprivacy.location_precision_setting;
CREATE POLICY location_precision_setting_self ON milavn_locationprivacy.location_precision_setting
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_locationprivacy.consent_grant ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS consent_grant_self ON milavn_locationprivacy.consent_grant;
CREATE POLICY consent_grant_self ON milavn_locationprivacy.consent_grant
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid);

GRANT USAGE ON SCHEMA milavn_locationprivacy TO milavn_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA milavn_locationprivacy TO milavn_app;

-- =============================================================================
-- 8. milavn_connect — Connect (People Discovery)
-- [TR31-TR32, FR042-FR045]
-- No persistent tables at V1: every FR here (reason-based suggestion,
-- structural prohibition on a reason-less list or a swipe/match mechanic)
-- is satisfied by a stateless read-model computed over milavn_circle
-- (membership) and milavn_activity (participation history) through those
-- components' own public interfaces — there is no Milavn-specific state
-- this component itself needs to own or persist. The schema is created for
-- namespace/ownership completeness (architecture.md's fixed ten-schema
-- list) but intentionally has zero tables — see 07a-er-model.md
-- Assumptions for why this is a documented decision, not an omission.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_connect AUTHORIZATION milavn_owner;

-- =============================================================================
-- 9. milavn_publicpage — Public Page
-- [TR33-TR36, FR046-FR050]
-- No persistent tables at V1: the public page is a read-only rendering of
-- milavn_activity.occurrence + milavn_trust.trust_status data (TR34's fixed
-- Pydantic content contract), served through a dedicated SSR route (TR33).
-- It owns no state of its own to persist. Schema created for namespace/
-- ownership completeness; zero tables — documented decision, not an
-- omission (07a-er-model.md Assumptions).
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_publicpage AUTHORIZATION milavn_owner;

-- =============================================================================
-- 10. milavn_notification — Notification Dispatch (including inbox)
-- [TR13, TR37, FR051-FR057, FR086]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_notification AUTHORIZATION milavn_owner;

DO $$ BEGIN
  CREATE TYPE milavn_notification.notification_class AS ENUM ('important','useful','social','opportunity');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_notification.outbox_status AS ENUM ('pending','dispatched','failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR37/FR086] Persistent in-app inbox record — the one schema-owning
-- responsibility this otherwise-thin bridge component has (architecture.md
-- §2.1).
CREATE TABLE IF NOT EXISTS milavn_notification.notification_inbox_entry (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id             uuid NOT NULL,
  notification_class    milavn_notification.notification_class NOT NULL,
  title                 text NOT NULL,
  body                  text NOT NULL,
  deep_link             text,
  source_occurrence_id  uuid,   -- cross-schema ref -> milavn_activity.occurrence(id), no FK; nullable
  read_at               timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_notification.notification_inbox_entry IS '[TR37/FR051-FR055/FR086] Persistent in-app inbox record for all four notification classes.';
CREATE INDEX IF NOT EXISTS idx_notification_inbox_entry_member ON milavn_notification.notification_inbox_entry (member_id, created_at DESC);

-- [TR37/FR054] Opportunity-class frequency is user-controlled; Important is
-- never user-mutable (enforced at the application layer — this table never
-- has an 'important' row, by construction).
CREATE TABLE IF NOT EXISTS milavn_notification.notification_preference (
  member_id           uuid NOT NULL,
  notification_class  milavn_notification.notification_class NOT NULL,
  muted               boolean NOT NULL DEFAULT false,
  frequency_setting   text,   -- e.g. 'daily_digest' | 'immediate' | 'weekly' — Opportunity/Useful only
  updated_at          timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, notification_class),
  CONSTRAINT notification_preference_important_not_mutable CHECK (notification_class <> 'important' OR muted = false)
);
COMMENT ON TABLE milavn_notification.notification_preference IS '[TR37/FR051/FR054] Important class is never suppressible — enforced by the CHECK constraint above.';

-- [TR13/TR37 — transactional outbox to the platform Notification &
-- Communication Service, ADR-006] A dropped Important-class dispatch (e.g.
-- a cancellation) is a safety-relevant gap, not best-effort (IA017).
CREATE TABLE IF NOT EXISTS milavn_notification.notification_outbox (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id           uuid NOT NULL,
  notification_class  milavn_notification.notification_class NOT NULL,
  payload             jsonb NOT NULL,
  status              milavn_notification.outbox_status NOT NULL DEFAULT 'pending',
  created_at          timestamptz NOT NULL DEFAULT now(),
  dispatched_at       timestamptz
);
COMMENT ON TABLE milavn_notification.notification_outbox IS
  '[TR13/TR37 — ADR-006] Transactional outbox to the platform Notification & Communication Service. Milavn governs what/when; delivery infra is Common Platform (TR55).';
CREATE INDEX IF NOT EXISTS idx_notification_outbox_undispatched ON milavn_notification.notification_outbox (created_at) WHERE status = 'pending';

ALTER TABLE milavn_notification.notification_inbox_entry ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS notification_inbox_entry_self ON milavn_notification.notification_inbox_entry;
CREATE POLICY notification_inbox_entry_self ON milavn_notification.notification_inbox_entry
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_notification.notification_preference ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS notification_preference_self ON milavn_notification.notification_preference;
CREATE POLICY notification_preference_self ON milavn_notification.notification_preference
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid);

GRANT USAGE ON SCHEMA milavn_notification TO milavn_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA milavn_notification TO milavn_app;

-- =============================================================================
-- 11. milavn_safety — Safety & Moderation
-- [TR41-TR43, TR-PLAT-01 (module-side only), FR061-FR065, FR087]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS milavn_safety AUTHORIZATION milavn_owner;

DO $$ BEGIN
  CREATE TYPE milavn_safety.report_subject_type AS ENUM ('activity','occurrence','user','organization','content');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_safety.report_status AS ENUM ('open','in_review','dismissed','actioned');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE milavn_safety.moderation_action_type AS ENUM ('dismiss','warn','escalate','restrict');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR41/FR061 — also backs FR087's Help/Support "Contact support" reuse]
CREATE TABLE IF NOT EXISTS milavn_safety.report (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_member_id uuid NOT NULL,
  subject_type       milavn_safety.report_subject_type NOT NULL,
  subject_id         uuid NOT NULL,   -- cross-schema/cross-service ref depending on subject_type; no FK (§4)
  reason_category    text NOT NULL,
  description        text,
  status             milavn_safety.report_status NOT NULL DEFAULT 'open',
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_safety.report IS '[TR41/TR43/FR061/FR065/FR087] Feeds the TR-PLAT-01 moderation queue (via list_endpoint/detail_endpoint). Sensitive — visible to reporter and moderators only.';
CREATE INDEX IF NOT EXISTS idx_report_status ON milavn_safety.report (status);
CREATE INDEX IF NOT EXISTS idx_report_subject ON milavn_safety.report (subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_report_reporter ON milavn_safety.report (reporter_member_id);

-- [TR41/FR062]
CREATE TABLE IF NOT EXISTS milavn_safety.block (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  blocking_member_id  uuid NOT NULL,
  blocked_member_id   uuid NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT block_unique UNIQUE (blocking_member_id, blocked_member_id),
  CONSTRAINT block_not_self CHECK (blocking_member_id <> blocked_member_id)
);
COMMENT ON TABLE milavn_safety.block IS '[TR41/FR062] Enforced at every contact/appearance touchpoint via the shared is_blocked(actor, target) helper (TR41), not re-checked per surface.';
CREATE INDEX IF NOT EXISTS idx_block_blocking_member ON milavn_safety.block (blocking_member_id);
CREATE INDEX IF NOT EXISTS idx_block_blocked_member ON milavn_safety.block (blocked_member_id);

-- [TR43 — TR-PLAT-01's action-dispatch contract, module side]
CREATE TABLE IF NOT EXISTS milavn_safety.moderation_action (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id             uuid NOT NULL REFERENCES milavn_safety.report (id) ON DELETE CASCADE,
  moderator_member_id   uuid NOT NULL,
  action_type           milavn_safety.moderation_action_type NOT NULL,
  notes                 text,
  created_at            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_safety.moderation_action IS '[TR43/TR15 — every action here is a human decision by construction] Never a single-signal automated penalty.';
CREATE INDEX IF NOT EXISTS idx_moderation_action_report ON milavn_safety.moderation_action (report_id);

-- [TR41/TR-CROSSCUT-04 — a dropped audit event for a safety report is a
-- compliance gap, not best-effort (IA061)]
CREATE TABLE IF NOT EXISTS milavn_safety.outbox_event (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    text NOT NULL,
  aggregate_id  uuid NOT NULL,
  payload       jsonb NOT NULL,
  occurred_at   timestamptz NOT NULL DEFAULT now(),
  dispatched_at timestamptz
);
COMMENT ON TABLE milavn_safety.outbox_event IS '[TR41/TR-CROSSCUT-04] In-process domain event outbox for Safety & Moderation — report submission and every TR-PLAT-01 moderation action publish here, in the same transaction as the write.';
CREATE INDEX IF NOT EXISTS idx_safety_outbox_event_undispatched ON milavn_safety.outbox_event (occurred_at) WHERE dispatched_at IS NULL;

ALTER TABLE milavn_safety.report ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS report_reporter_or_moderator ON milavn_safety.report;
-- [TR-PLAT-01 required_permission_scope: "milavn.moderate"]
CREATE POLICY report_reporter_or_moderator ON milavn_safety.report
  FOR SELECT
  USING (
    reporter_member_id = current_setting('milavn.member_id', true)::uuid
    OR current_setting('milavn.permission_scope', true) LIKE '%milavn.moderate%'
  );
DROP POLICY IF EXISTS report_self_write ON milavn_safety.report;
CREATE POLICY report_self_write ON milavn_safety.report
  FOR INSERT WITH CHECK (reporter_member_id = current_setting('milavn.member_id', true)::uuid);
DROP POLICY IF EXISTS report_moderator_update ON milavn_safety.report;
CREATE POLICY report_moderator_update ON milavn_safety.report
  FOR UPDATE USING (current_setting('milavn.permission_scope', true) LIKE '%milavn.moderate%');

ALTER TABLE milavn_safety.block ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS block_self ON milavn_safety.block;
CREATE POLICY block_self ON milavn_safety.block
  FOR ALL USING (blocking_member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_safety.moderation_action ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS moderation_action_moderator_only ON milavn_safety.moderation_action;
CREATE POLICY moderation_action_moderator_only ON milavn_safety.moderation_action
  FOR ALL USING (current_setting('milavn.permission_scope', true) LIKE '%milavn.moderate%');

GRANT USAGE ON SCHEMA milavn_safety TO milavn_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA milavn_safety TO milavn_app;

-- =============================================================================
-- Done. Verification query used by init.sh:
--   SELECT schemaname, count(*) FROM pg_tables WHERE schemaname LIKE 'milavn_%' GROUP BY schemaname;
-- =============================================================================
