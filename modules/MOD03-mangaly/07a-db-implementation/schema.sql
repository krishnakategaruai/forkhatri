-- =============================================================================
-- Mangaly (MOD03) — Postgres schema DDL
-- Snapshot of the current schema, equivalent to applying every file in
-- migrations/ in order. Keep this file and migrations/ in sync — this file
-- exists for fast local/dev setup (init.sh runs it directly); migrations/ is
-- the authoritative, ordered history. See 07a-db-implementation/README.md.
--
-- Traces to: modules/MOD03-mangaly/07a-er-model.md (full traceability table),
-- 07-tech-reqs.md (TR001-TR102), architecture.md (14-component, 12-schema
-- decomposition), /MODULE-ARCHITECTURE-STANDARD.md §4/§4b/§4c/§5/§6.
--
-- Design conventions applied uniformly (see 07a-er-model.md "Assumptions"
-- for the full reasoning on each):
--   1. One Postgres schema per schema-owning component (architecture.md §3),
--      plus two infrastructure schemas this file's own Assumptions justify:
--      mangaly_identity (interim Identity Bridge credential store — technical
--      debt per v1-decisions.md, TR092) and mangaly_platform (shared
--      idempotency + rate-limiting utilities per MODULE-ARCHITECTURE-STANDARD
--      §4b/§4c — cross-cutting infrastructure, not a business-logic
--      component, so it does not violate architecture.md's fixed 12-schema
--      business-component list).
--   2. Every table has id (uuid pk), created_at, updated_at (except pure
--      append-only event/log tables, which have created_at/occurred_at only
--      — an update would violate their append-only intent).
--   3. Cross-schema references are stored as plain, indexed UUID columns with
--      NO database-level FOREIGN KEY constraint — a real FK would require
--      granting cross-schema SELECT and would let one component's schema
--      silently depend on another's internal row lifecycle, which is exactly
--      what "no cross-schema join written by any component other than the
--      schema's own owner" (MODULE-ARCHITECTURE-STANDARD §4) forbids.
--      Referential integrity across schemas is enforced by the owning
--      component's own interface.py at the application layer, not the DB.
--      Within one schema (same owning component), real FK constraints with
--      an explicit cascade rule are used.
--   4. RLS: every table whose rows are visible to more than one actor gets
--      RLS enabled at creation time (never bolted on later) per
--      MODULE-ARCHITECTURE-STANDARD §4 / TR017. The runtime role
--      (mangaly_app) is a NON-OWNING role — mangaly_owner (migration role)
--      owns every object. RLS keys off two SET LOCAL session variables the
--      Authorization Engine / Identity Bridge set per-transaction, never
--      plain SET (TR017's canonical pooling-safety statement):
--        mangaly.account_id      — the authenticated actor's own account id,
--                                   set by Identity Bridge once a session is
--                                   validated (available before the fuller
--                                   authz chain resolves).
--        mangaly.authz_context   — the resolved acting-subject id the
--                                   Authorization Engine's resolve() call
--                                   produces (may equal account_id, or a
--                                   family member acting on-behalf-of).
--      A shared helper, mangaly_authz.has_scope(), centralizes the actual
--      grant lookup so no table re-derives the predicate independently.
--   5. Outbox pattern (MODULE-ARCHITECTURE-STANDARD §6): every one of the 11
--      schema-owning BUSINESS-LOGIC components (all except Notification
--      Bridge, which is the consumer, and Audit Bridge, which is genuinely
--      schema-less) gets its own <schema>.outbox_event table so the event
--      insert commits in the exact same transaction as the state change it
--      describes — a shared cross-schema outbox table would work in one
--      physical Postgres instance, but would violate "no cross-schema write
--      by any component other than the schema's own owner" the same way a
--      cross-schema FK would.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Extensions. Roles are NOT created here.
-- -----------------------------------------------------------------------------
-- Postgres roles are cluster-wide (shared across every database on the
-- server), not database-local objects, and creating one requires the
-- CREATEROLE attribute (or superuser) — a migration running as the
-- non-superuser mangaly_owner role cannot create roles, by design (verified
-- live: "permission denied to create role... Only roles with the CREATEROLE
-- attribute may create roles" when this was first tried as part of this
-- migration). Role provisioning is therefore an infrastructure/ops step
-- init.sh performs BEFORE running this file, as an actual superuser/admin
-- connection — see init.sh Step 2. This migration only assumes
-- mangaly_owner and mangaly_app already exist and grants privileges to them;
-- it never attempts CREATE ROLE.
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- Discovery's Postgres FTS (TR025/ADR-007/ADR-018)

-- =============================================================================
-- 1. mangaly_identity — Identity Bridge (interim credential/session store)
-- [TR092-TR095, TR101] Genuinely thin per architecture.md for authorization
-- purposes, but per v1-decisions.md's "Known technical debt" (IA092) and
-- TR092's own Sealed text, Mangaly must build its own minimal
-- credential/session store because no Common Platform Identity & Trust
-- Service exists yet at Mangaly's build-order position (ADR-016/017). This
-- schema is explicitly named as a planned future migration target, not a
-- permanent architecture decision — see 07a-er-model.md Assumptions.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_identity AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_identity.account_status AS ENUM ('pending_verification','active','locked','deleted');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_identity.otp_purpose AS ENUM ('signup','login','password_reset','identifier_change');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_identity.otp_channel AS ENUM ('sms','email');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR092] Interim account/credential record. At least one identifier
-- required (FR092). credential_hash never stores plaintext.
CREATE TABLE IF NOT EXISTS mangaly_identity.account (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_identifier    text UNIQUE,
  email_identifier    text UNIQUE,
  credential_hash     text NOT NULL,
  status              mangaly_identity.account_status NOT NULL DEFAULT 'pending_verification',
  identifier_verified_at timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT account_has_identifier CHECK (phone_identifier IS NOT NULL OR email_identifier IS NOT NULL)
);
COMMENT ON TABLE mangaly_identity.account IS
  '[TR092/FR092] Interim, Mangaly-owned credential store — technical debt per v1-decisions.md, to be migrated into a future Common Platform Identity & Trust Service. PII/credential-sensitive.';

-- [TR095/FR095] OTP challenge — bounded validity, single-use, attempt-capped.
CREATE TABLE IF NOT EXISTS mangaly_identity.otp_challenge (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id     uuid NOT NULL REFERENCES mangaly_identity.account(id) ON DELETE CASCADE,
  channel        mangaly_identity.otp_channel NOT NULL,
  purpose        mangaly_identity.otp_purpose NOT NULL,
  code_hash      text NOT NULL,
  attempt_count  integer NOT NULL DEFAULT 0,
  expires_at     timestamptz NOT NULL,
  used_at        timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_otp_challenge_account ON mangaly_identity.otp_challenge(account_id);
COMMENT ON TABLE mangaly_identity.otp_challenge IS '[TR095] Single-use, time-bound OTP; resend is rate-limited via mangaly_platform.rate_limit_counter (TR037 canonical utility).';

-- [TR094/FR094] Password reset — single-use, expiring token.
CREATE TABLE IF NOT EXISTS mangaly_identity.password_reset_token (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id  uuid NOT NULL REFERENCES mangaly_identity.account(id) ON DELETE CASCADE,
  token_hash  text NOT NULL,
  expires_at  timestamptz NOT NULL,
  used_at     timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reset_token_account ON mangaly_identity.password_reset_token(account_id);
COMMENT ON TABLE mangaly_identity.password_reset_token IS '[TR094] Single-use, short-TTL reset token; anti-enumeration enforced at the application layer (generic_auth_error()), not by this table.';

-- [TR101] Session — logout is unconditional/immediate (revoked_at set).
CREATE TABLE IF NOT EXISTS mangaly_identity.session (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id     uuid NOT NULL REFERENCES mangaly_identity.account(id) ON DELETE CASCADE,
  issued_at      timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL,
  revoked_at     timestamptz,
  last_seen_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_session_account ON mangaly_identity.session(account_id);
COMMENT ON TABLE mangaly_identity.session IS '[TR101/TR090] Session store backing splash/launch bootstrap and immediate logout revocation.';

-- RLS: a person may only ever see their own identity rows. This is the
-- pre-authorization trust root, so RLS here keys on mangaly.account_id
-- directly (set by Identity Bridge on token validation), not on the fuller
-- mangaly.authz_context the Authorization Engine resolves downstream of it.
-- Login/signup/OTP/reset themselves necessarily need an identifier-lookup
-- path that runs BEFORE any session variable exists; that path is served by
-- the SECURITY DEFINER function mangaly_identity.lookup_by_identifier()
-- below, which is the sole, narrowly-scoped, exact-identifier-only exception
-- to this schema's RLS — flagged explicitly to Step 8 for STRIDE review.
ALTER TABLE mangaly_identity.account ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS account_self_only ON mangaly_identity.account;
CREATE POLICY account_self_only ON mangaly_identity.account
  USING (id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
ALTER TABLE mangaly_identity.otp_challenge ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS otp_challenge_self_only ON mangaly_identity.otp_challenge;
CREATE POLICY otp_challenge_self_only ON mangaly_identity.otp_challenge
  USING (account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
ALTER TABLE mangaly_identity.password_reset_token ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reset_token_self_only ON mangaly_identity.password_reset_token;
CREATE POLICY reset_token_self_only ON mangaly_identity.password_reset_token
  USING (account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
ALTER TABLE mangaly_identity.session ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS session_self_only ON mangaly_identity.session;
CREATE POLICY session_self_only ON mangaly_identity.session
  USING (account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);

-- [TR092/TR093/TR094] Narrow, audited exception: exact-identifier lookup only
-- (never a scan), used solely by the login/signup/OTP/reset endpoints before
-- a session exists. SECURITY DEFINER with a pinned search_path to avoid
-- search-path injection; returns only the columns those flows need.
CREATE OR REPLACE FUNCTION mangaly_identity.lookup_by_identifier(p_identifier text)
RETURNS TABLE(id uuid, credential_hash text, status mangaly_identity.account_status)
LANGUAGE sql SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
  SELECT a.id, a.credential_hash, a.status
  FROM mangaly_identity.account a
  WHERE a.phone_identifier = p_identifier OR a.email_identifier = p_identifier;
$$;
GRANT EXECUTE ON FUNCTION mangaly_identity.lookup_by_identifier(text) TO mangaly_app;

-- [Found via live testing: mangaly_app had no USAGE on this schema at all,
-- so even the RLS-scoped self-only reads above failed with "permission
-- denied for schema" rather than an empty result set — a schema-level grant
-- gap distinct from (and checked before) any RLS predicate.]
GRANT USAGE ON SCHEMA mangaly_identity TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_identity TO mangaly_app;

-- =============================================================================
-- 2. mangaly_platform — shared cross-cutting infrastructure
-- [MODULE-ARCHITECTURE-STANDARD §4b/§4c, TR102, TR037] Idempotency-key store
-- and rate-limit counter. Not a business-logic component's schema (does not
-- extend architecture.md's 12-schema business list) — this is the same class
-- of infrastructure as the in-process event bus, given its own schema only
-- because it is genuinely persistent, shared state, unlike the bus itself.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_platform AUTHORIZATION mangaly_owner;

-- [TR102] One shared idempotency-key store for every client-queueable
-- mutation named in TR102 (TR002, TR042, TR043, TR046, TR047, TR049, TR057,
-- TR058). request_hash lets a repeated key with a DIFFERENT payload be
-- rejected as a client bug rather than silently returning a stale result.
CREATE TABLE IF NOT EXISTS mangaly_platform.idempotency_key (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  idempotency_key    text NOT NULL,
  endpoint           text NOT NULL,
  account_id         uuid NOT NULL,
  request_hash       text NOT NULL,
  status_code        integer,
  response_snapshot  jsonb,
  created_at         timestamptz NOT NULL DEFAULT now(),
  expires_at         timestamptz NOT NULL DEFAULT (now() + interval '7 days'),
  -- [SP102] Account-scoped, NOT global: the idempotency key is client-generated
  -- (TR102), so a global (key, endpoint) namespace would let one account's
  -- colliding or replayed key return another account's cached response_snapshot,
  -- and would let any account block another's writes by burning keys.
  CONSTRAINT idempotency_key_account_scope UNIQUE (account_id, idempotency_key, endpoint)
);
CREATE INDEX IF NOT EXISTS idx_idempotency_expiry ON mangaly_platform.idempotency_key(expires_at);
CREATE INDEX IF NOT EXISTS idx_idempotency_account ON mangaly_platform.idempotency_key(account_id);
-- [SP102] Defense in depth beneath the middleware's own server-side account
-- scoping — a middleware bug that omitted account_id from its WHERE clause
-- still cannot cross accounts. mangaly_app is non-owning (TR017), so it applies.
ALTER TABLE mangaly_platform.idempotency_key ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS idempotency_key_self ON mangaly_platform.idempotency_key;
CREATE POLICY idempotency_key_self ON mangaly_platform.idempotency_key
  USING (account_id::text = current_setting('mangaly.account_id', true))
  WITH CHECK (account_id::text = current_setting('mangaly.account_id', true));
COMMENT ON TABLE mangaly_platform.idempotency_key IS
  '[TR102/MODULE-ARCHITECTURE-STANDARD §4b] One shared implementation every client-queueable mutation endpoint honors — never re-derived per component. Rows are account-scoped (SP102) by both the UNIQUE constraint and an RLS policy, because the client-generated key is not trustworthy as a global identifier.';

-- [TR037 canonical / §4c] One shared, DB-backed rate-limit counter — used by
-- TR037 (verifier invites), TR093 (login failures), TR095 (OTP resend).
CREATE TABLE IF NOT EXISTS mangaly_platform.rate_limit_counter (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rate_limit_key  text NOT NULL,       -- e.g. 'verifier_invite:{account_id}', 'login_failure:{identifier}', 'otp_resend:{identifier}'
  window_start    timestamptz NOT NULL,
  window_seconds  integer NOT NULL,
  hit_count       integer NOT NULL DEFAULT 1,
  limit_max       integer NOT NULL,
  UNIQUE (rate_limit_key, window_start)
);
CREATE INDEX IF NOT EXISTS idx_rate_limit_key ON mangaly_platform.rate_limit_counter(rate_limit_key);
COMMENT ON TABLE mangaly_platform.rate_limit_counter IS
  '[TR037 canonical/§4c] One shared (key, window, limit) DB-backed counter — TR037, TR093, TR095 all call this same table via one implementation, never a per-component copy.';

GRANT USAGE ON SCHEMA mangaly_platform TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_platform TO mangaly_app;
-- RLS on mangaly_platform is table-by-table, not blanket-off:
--   * idempotency_key DOES carry a per-account row concept (it stores a
--     response_snapshot belonging to one account), so it has both an
--     account-scoped UNIQUE constraint and an RLS policy — see SP102. An
--     earlier revision of this file asserted the opposite; that was wrong.
--   * rate_limit_counter genuinely has no per-account row concept: its rows
--     are opaque (key, window) tuples the shared utility composes and scopes
--     server-side, and several of its keys are deliberately NOT account-keyed
--     at all (login_failure/otp_resend key on a pre-authentication identifier,
--     where no mangaly.account_id exists yet to enforce a policy against).
--     RLS is therefore genuinely inapplicable there, not merely skipped.

-- =============================================================================
-- 3. mangaly_authz — Authorization Engine (BR04, BR05) — the chokepoint
-- [TR017-TR024] Canonical grant model every other schema's RLS keys off.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_authz AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_authz.grant_scope AS ENUM ('candidate_info','family_info');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_authz.grant_type AS ENUM
    ('home_circle_membership','connection_accepted','safety_override','admin_case','pause_exception');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_authz.grant_status AS ENUM ('active','withheld','revoked');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR018] Candidate-info vs. family-info modeled as two independently-typed
-- grant rows — never a single combined boolean. [TR010/TR011] withheld
-- status for disputed/removed relationships, never a hard delete.
CREATE TABLE IF NOT EXISTS mangaly_authz.grant (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id           uuid NOT NULL,          -- the acting party (account or on-behalf-of profile)
  target_profile_id    uuid NOT NULL,          -- whose data this grant concerns
  scope                mangaly_authz.grant_scope NOT NULL,
  grant_type           mangaly_authz.grant_type NOT NULL,
  status               mangaly_authz.grant_status NOT NULL DEFAULT 'active',
  source_component     text NOT NULL,          -- e.g. 'home_circle', 'connection', 'safety', 'operations'
  source_reference_id  uuid,                   -- unconstrained pointer into the source component's own schema
  granted_at           timestamptz NOT NULL DEFAULT now(),
  revoked_at           timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_grant_subject ON mangaly_authz.grant(subject_id);
CREATE INDEX IF NOT EXISTS idx_grant_target ON mangaly_authz.grant(target_profile_id, scope, status);
COMMENT ON TABLE mangaly_authz.grant IS
  '[TR017/TR018] The single canonical authorization data model. Written only through the Authorization Engine''s own interface.py, sourced from Home Circle, Connection, Safety, and Operations events — never directly by those components.';

-- [TR024] Safety-exception override — its own named, individually-audited
-- grant type, distinct from every other grant path.
CREATE TABLE IF NOT EXISTS mangaly_authz.safety_override_grant (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  grant_id              uuid NOT NULL REFERENCES mangaly_authz.grant(id) ON DELETE CASCADE,
  safety_case_reference uuid NOT NULL,          -- unconstrained pointer to mangaly_operations.case
  ops_reviewed          boolean NOT NULL DEFAULT false,
  ops_reviewer_account_id uuid,
  created_at            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_authz.safety_override_grant IS '[TR024] Requires a Safety-Intelligence-issued trigger reference and Operations review for any exception broader than the narrowest named case.';

CREATE TABLE IF NOT EXISTS mangaly_authz.outbox_event (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_id  uuid NOT NULL,
  event_type    text NOT NULL,
  payload       jsonb NOT NULL,
  occurred_at   timestamptz NOT NULL DEFAULT now(),
  published_at  timestamptz
);
CREATE INDEX IF NOT EXISTS idx_authz_outbox_unpublished ON mangaly_authz.outbox_event(published_at) WHERE published_at IS NULL;
COMMENT ON TABLE mangaly_authz.outbox_event IS '[TR017/MODULE-ARCHITECTURE-STANDARD §6] Every grant/deny decision, in the same transaction as the grant write.';

-- Shared helper every other schema's RLS policies call. SECURITY DEFINER
-- with a pinned search_path; EXECUTE granted broadly to mangaly_app.
CREATE OR REPLACE FUNCTION mangaly_authz.has_scope(
  p_target_profile_id uuid,
  p_scope text
) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = mangaly_authz, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM mangaly_authz.grant g
    WHERE g.target_profile_id = p_target_profile_id
      AND g.scope::text = p_scope
      AND g.status = 'active'
      AND g.subject_id = NULLIF(current_setting('mangaly.authz_context', true), '')::uuid
  );
$$;
GRANT EXECUTE ON FUNCTION mangaly_authz.has_scope(uuid, text) TO mangaly_app;

-- Self-access helper: the acting subject accessing their own data.
CREATE OR REPLACE FUNCTION mangaly_authz.is_self(p_profile_or_account_id uuid)
RETURNS boolean
LANGUAGE sql STABLE
AS $$
  SELECT p_profile_or_account_id = NULLIF(current_setting('mangaly.authz_context', true), '')::uuid
      OR p_profile_or_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
$$;
GRANT EXECUTE ON FUNCTION mangaly_authz.is_self(uuid) TO mangaly_app;

ALTER TABLE mangaly_authz.grant ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS grant_visible_to_subject_or_target ON mangaly_authz.grant;
CREATE POLICY grant_visible_to_subject_or_target ON mangaly_authz.grant
  USING (mangaly_authz.is_self(subject_id) OR mangaly_authz.is_self(target_profile_id));
ALTER TABLE mangaly_authz.safety_override_grant ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS safety_override_admin_only ON mangaly_authz.safety_override_grant;
CREATE POLICY safety_override_admin_only ON mangaly_authz.safety_override_grant
  USING (current_setting('mangaly.operator_role', true) = 'operations');

GRANT USAGE ON SCHEMA mangaly_authz TO mangaly_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mangaly_authz TO mangaly_app;

-- =============================================================================
-- 4. mangaly_profile — Profile & Completeness (BR01, BR18-adjacent)
-- [TR001-TR006, TR089]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_profile AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_profile.profile_status AS ENUM ('active','paused');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_profile.field_state AS ENUM ('unset','declined','value');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_profile.media_type AS ENUM ('photo','video');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_profile.media_upload_status AS ENUM ('pending','failed','complete');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR001/DEC-V1-001] Existence-tier fields as first-class, indexed columns
-- (name, DOB, gender, city/locality, status). [TR024] status=paused, no
-- broadcast. [TR089] language_preference is person-level profile data.
CREATE TABLE IF NOT EXISTS mangaly_profile.profile (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id           uuid NOT NULL UNIQUE,   -- cross-schema ref to mangaly_identity.account, no FK (see file header)
  name                 text NOT NULL,
  date_of_birth        date NOT NULL,
  gender               text NOT NULL,
  city_locality        text NOT NULL,
  language_preference  text NOT NULL DEFAULT 'en',
  status               mangaly_profile.profile_status NOT NULL DEFAULT 'active',
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_profile_account ON mangaly_profile.profile(account_id);
COMMENT ON TABLE mangaly_profile.profile IS '[TR001] Existence-tier minimum viable profile. PII.';

-- [TR002] Media (photos/video intro) with retry-preserving-partial-save
-- semantics — a failed upload never blocks other categories.
CREATE TABLE IF NOT EXISTS mangaly_profile.profile_media (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL REFERENCES mangaly_profile.profile(id) ON DELETE CASCADE,
  media_type     mangaly_profile.media_type NOT NULL,
  storage_ref    text,                          -- Object Storage key; null while upload pending
  is_primary     boolean NOT NULL DEFAULT false,
  upload_status  mangaly_profile.media_upload_status NOT NULL DEFAULT 'pending',
  uploaded_at    timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_profile_media_profile ON mangaly_profile.profile_media(profile_id);
COMMENT ON TABLE mangaly_profile.profile_media IS '[TR001/TR002/TR006] No raw bytes — storage_ref only; TR006''s signed URLs are issued at read time, never stored.';

-- [TR002] Tri-state (unset/declined/value) per-category fields — covers
-- discoverability-tier (education, profession, marital history, relocation
-- willingness, partner-preference age/locality per DEC-V1-001) and
-- enhanced-matching-tier fields alike. Tier membership is an application
-- config mapping (DEC-V1-001), not a DB column — avoids a second,
-- potentially-drifting source of truth for tier membership (same principle
-- TR003/TR005 already apply to the discoverability gate itself).
CREATE TABLE IF NOT EXISTS mangaly_profile.profile_attribute (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id    uuid NOT NULL REFERENCES mangaly_profile.profile(id) ON DELETE CASCADE,
  category      text NOT NULL,     -- e.g. 'education','profession','lifestyle','partner_preference'
  attribute_key text NOT NULL,     -- e.g. 'education_level','relocation_willingness'
  state         mangaly_profile.field_state NOT NULL DEFAULT 'unset',
  value         jsonb,
  updated_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (profile_id, category, attribute_key)
);
CREATE INDEX IF NOT EXISTS idx_profile_attribute_profile ON mangaly_profile.profile_attribute(profile_id, category);
COMMENT ON TABLE mangaly_profile.profile_attribute IS '[TR002] declined is a distinct, first-class state — never collapsed to NULL.';

CREATE TABLE IF NOT EXISTS mangaly_profile.outbox_event (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_id  uuid NOT NULL,
  event_type    text NOT NULL,
  payload       jsonb NOT NULL,
  occurred_at   timestamptz NOT NULL DEFAULT now(),
  published_at  timestamptz
);
CREATE INDEX IF NOT EXISTS idx_profile_outbox_unpublished ON mangaly_profile.outbox_event(published_at) WHERE published_at IS NULL;
COMMENT ON TABLE mangaly_profile.outbox_event IS '[TR001/TR069] ProfileCreated and other consequential Profile events, same transaction as the state change.';

ALTER TABLE mangaly_profile.profile ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS profile_owner_or_granted ON mangaly_profile.profile;
CREATE POLICY profile_owner_or_granted ON mangaly_profile.profile
  USING (mangaly_authz.is_self(account_id) OR mangaly_authz.has_scope(id, 'candidate_info'));
ALTER TABLE mangaly_profile.profile_media ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS profile_media_owner_or_granted ON mangaly_profile.profile_media;
CREATE POLICY profile_media_owner_or_granted ON mangaly_profile.profile_media
  USING (EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.id = profile_media.profile_id
                 AND (mangaly_authz.is_self(p.account_id) OR mangaly_authz.has_scope(p.id, 'candidate_info'))));
ALTER TABLE mangaly_profile.profile_attribute ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS profile_attribute_owner_or_granted ON mangaly_profile.profile_attribute;
CREATE POLICY profile_attribute_owner_or_granted ON mangaly_profile.profile_attribute
  USING (EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.id = profile_attribute.profile_id
                 AND (mangaly_authz.is_self(p.account_id) OR mangaly_authz.has_scope(p.id, 'candidate_info'))));

GRANT USAGE ON SCHEMA mangaly_profile TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_profile TO mangaly_app;

-- =============================================================================
-- 5. mangaly_home_circle — Home Circle (BR02, BR03, BR13) [TR007-TR016, TR029, TR060-TR062]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_home_circle AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_home_circle.invitation_status AS ENUM ('pending','accepted','declined','expired');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_home_circle.membership_status AS ENUM ('active','removed','left');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR007] Invite-by-lookup or invite-by-identifier fallback (IA007).
CREATE TABLE IF NOT EXISTS mangaly_home_circle.invitation (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_profile_id uuid NOT NULL,   -- cross-schema ref to mangaly_profile.profile
  inviter_account_id  uuid NOT NULL,
  invitee_identifier  text,             -- phone/email fallback per IA007, nullable once resolved
  invitee_account_id  uuid,
  status              mangaly_home_circle.invitation_status NOT NULL DEFAULT 'pending',
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  expires_at          timestamptz
);
CREATE INDEX IF NOT EXISTS idx_hc_invitation_candidate ON mangaly_home_circle.invitation(candidate_profile_id);
COMMENT ON TABLE mangaly_home_circle.invitation IS '[TR007/TR009] decline is a distinct write, not absence or timeout-only.';

-- [TR008/TR010] Membership — historical rows preserved (status, not delete).
CREATE TABLE IF NOT EXISTS mangaly_home_circle.membership (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_profile_id uuid NOT NULL,
  member_account_id    uuid NOT NULL,
  invitation_id        uuid REFERENCES mangaly_home_circle.invitation(id) ON DELETE SET NULL,
  status               mangaly_home_circle.membership_status NOT NULL DEFAULT 'active',
  joined_at            timestamptz NOT NULL DEFAULT now(),
  removed_at           timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_hc_membership_candidate ON mangaly_home_circle.membership(candidate_profile_id, status);
CREATE INDEX IF NOT EXISTS idx_hc_membership_member ON mangaly_home_circle.membership(member_account_id);
COMMENT ON TABLE mangaly_home_circle.membership IS '[TR010] Removal/leave writes status + removed_at; never a hard delete (Audit Bridge append-only guarantee).';

-- [TR016] Private family notes, forwarded only on explicit candidate approval.
CREATE TABLE IF NOT EXISTS mangaly_home_circle.home_circle_note (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_profile_id  uuid NOT NULL,
  author_membership_id  uuid NOT NULL REFERENCES mangaly_home_circle.membership(id) ON DELETE CASCADE,
  content               text NOT NULL,
  forwarded_at          timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_hc_note_candidate ON mangaly_home_circle.home_circle_note(candidate_profile_id);
COMMENT ON TABLE mangaly_home_circle.home_circle_note IS '[TR016] Family-only by default; forwarded_at set only via explicit candidate-approved forward action.';

-- [TR014] Suggestion — structurally separate from a connection request;
-- no code path converts this row into mangaly_connection.connection_request.
CREATE TABLE IF NOT EXISTS mangaly_home_circle.suggestion (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_profile_id    uuid NOT NULL,
  suggested_by_membership_id uuid NOT NULL REFERENCES mangaly_home_circle.membership(id) ON DELETE CASCADE,
  suggested_profile_id    uuid NOT NULL,
  note                    text,
  created_at              timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_hc_suggestion_candidate ON mangaly_home_circle.suggestion(candidate_profile_id);

-- [TR029/DEC-V1-003] Deliberately, structurally, has NO name/photo/contact
-- column — the field doesn't exist to leak, not merely hidden in the UI.
CREATE TABLE IF NOT EXISTS mangaly_home_circle.discovery_hint (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_profile_id    uuid NOT NULL,
  submitted_by_membership_id uuid NOT NULL REFERENCES mangaly_home_circle.membership(id) ON DELETE CASCADE,
  community_locality_text text NOT NULL,
  context_note            text NOT NULL,
  created_at              timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_hc_hint_candidate ON mangaly_home_circle.discovery_hint(candidate_profile_id);
COMMENT ON TABLE mangaly_home_circle.discovery_hint IS
  '[TR029/DEC-V1-003] Schema-introspection check (Step 8/9) must confirm no name/photo/contact column exists on this table.';

-- [TR011] False/inappropriate relationship claim — withholds access pending review.
CREATE TABLE IF NOT EXISTS mangaly_home_circle.report (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_account_id uuid NOT NULL,
  membership_id   uuid NOT NULL REFERENCES mangaly_home_circle.membership(id) ON DELETE CASCADE,
  reason          text NOT NULL,
  case_reference  uuid,       -- unconstrained pointer to mangaly_operations.case
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- [TR060/TR061] Candidate-initiated, sole trigger for per-connection scoping.
CREATE TABLE IF NOT EXISTS mangaly_home_circle.connection_home_circle_scope (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id  uuid NOT NULL,     -- cross-schema ref to mangaly_connection.connection_request
  scoped_at      timestamptz NOT NULL DEFAULT now(),
  scoped_by_account_id uuid NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_hc_connection_scope ON mangaly_home_circle.connection_home_circle_scope(connection_id);

-- [TR062] Family-to-family introduction — two independently-resolved exposures.
CREATE TABLE IF NOT EXISTS mangaly_home_circle.family_introduction (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id             uuid NOT NULL,
  side_a_candidate_profile_id uuid NOT NULL,
  side_b_candidate_profile_id uuid NOT NULL,
  side_a_exposed_at         timestamptz,
  side_b_exposed_at         timestamptz,
  created_at                timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_hc_family_introduction ON mangaly_home_circle.family_introduction(connection_id);
COMMENT ON TABLE mangaly_home_circle.family_introduction IS '[TR062] side_a/side_b exposure timestamps set by two independent authz.resolve() calls — never one combined event granting both.';

CREATE TABLE IF NOT EXISTS mangaly_home_circle.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_hc_outbox_unpublished ON mangaly_home_circle.outbox_event(published_at) WHERE published_at IS NULL;

ALTER TABLE mangaly_home_circle.invitation ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_invitation_participants ON mangaly_home_circle.invitation;
CREATE POLICY hc_invitation_participants ON mangaly_home_circle.invitation
  USING (mangaly_authz.is_self(inviter_account_id) OR mangaly_authz.is_self(invitee_account_id) OR mangaly_authz.is_self(candidate_profile_id));
ALTER TABLE mangaly_home_circle.membership ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_membership_participants ON mangaly_home_circle.membership;
CREATE POLICY hc_membership_participants ON mangaly_home_circle.membership
  USING (mangaly_authz.is_self(candidate_profile_id) OR mangaly_authz.is_self(member_account_id) OR mangaly_authz.has_scope(candidate_profile_id, 'family_info'));
ALTER TABLE mangaly_home_circle.home_circle_note ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_note_family_or_forwarded ON mangaly_home_circle.home_circle_note;
CREATE POLICY hc_note_family_or_forwarded ON mangaly_home_circle.home_circle_note
  USING (mangaly_authz.has_scope(candidate_profile_id, 'family_info') OR (forwarded_at IS NOT NULL AND mangaly_authz.is_self(candidate_profile_id)));
ALTER TABLE mangaly_home_circle.suggestion ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_suggestion_family ON mangaly_home_circle.suggestion;
CREATE POLICY hc_suggestion_family ON mangaly_home_circle.suggestion
  USING (mangaly_authz.has_scope(candidate_profile_id, 'family_info'));
ALTER TABLE mangaly_home_circle.discovery_hint ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_hint_readable_by_viewers ON mangaly_home_circle.discovery_hint;
CREATE POLICY hc_hint_readable_by_viewers ON mangaly_home_circle.discovery_hint
  USING (true); -- [TR029] deliberately broad read (it is designed to be shown to any Discovery viewer); write path is restricted at the application layer to a Home Circle member only.
ALTER TABLE mangaly_home_circle.report ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_report_reporter_or_ops ON mangaly_home_circle.report;
CREATE POLICY hc_report_reporter_or_ops ON mangaly_home_circle.report
  USING (mangaly_authz.is_self(reporter_account_id) OR current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_home_circle.connection_home_circle_scope ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_conn_scope_participants ON mangaly_home_circle.connection_home_circle_scope;
CREATE POLICY hc_conn_scope_participants ON mangaly_home_circle.connection_home_circle_scope USING (true);
ALTER TABLE mangaly_home_circle.family_introduction ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hc_family_intro_participants ON mangaly_home_circle.family_introduction;
CREATE POLICY hc_family_intro_participants ON mangaly_home_circle.family_introduction
  USING (mangaly_authz.has_scope(side_a_candidate_profile_id, 'family_info') OR mangaly_authz.has_scope(side_b_candidate_profile_id, 'family_info'));

GRANT USAGE ON SCHEMA mangaly_home_circle TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_home_circle TO mangaly_app;

-- =============================================================================
-- 6. mangaly_discovery — Discovery & Ranking (BR06) [TR025-TR029, TR003/TR027 gate]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_discovery AUTHORIZATION mangaly_owner;

-- [TR025/ADR-007/ADR-018] Own Postgres-FTS-backed read model, kept in sync
-- via Profile's domain events (subscriber), never a live cross-schema query
-- into mangaly_profile — preserves schema-per-component isolation while
-- giving Discovery its own queryable index, per the event-bus pattern (§6).
-- [TR021] searchable is independent of any specific viewer's authorization.
-- [TR022] Deliberately has NO view_count/rejection_count/demand-signal column.
CREATE TABLE IF NOT EXISTS mangaly_discovery.discovery_profile_index (
  profile_id              uuid PRIMARY KEY,     -- cross-schema ref to mangaly_profile.profile, no FK
  searchable              boolean NOT NULL DEFAULT false,
  locality                text,
  relocation_willingness  text,
  education_level         text,
  profession              text,
  search_vector           tsvector,
  ranking_input_snapshot  jsonb,
  updated_at              timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_discovery_search_vector ON mangaly_discovery.discovery_profile_index USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_discovery_searchable ON mangaly_discovery.discovery_profile_index(searchable);
COMMENT ON TABLE mangaly_discovery.discovery_profile_index IS
  '[TR021] searchable and per-viewer visibility are deliberately separate code paths — this column never gates on who is asking.';

CREATE TABLE IF NOT EXISTS mangaly_discovery.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_discovery_outbox_unpublished ON mangaly_discovery.outbox_event(published_at) WHERE published_at IS NULL;

ALTER TABLE mangaly_discovery.discovery_profile_index ENABLE ROW LEVEL SECURITY;
-- [TR013/TR015/TR020/TR023] Any authenticated searcher may query the
-- searchable index (Discovery itself does not gate per-viewer content —
-- the Authorization Engine gates the full profile read afterward, TR020);
-- a non-searchable row is only visible to its own owner.
DROP POLICY IF EXISTS discovery_index_searchable_or_owner ON mangaly_discovery.discovery_profile_index;
CREATE POLICY discovery_index_searchable_or_owner ON mangaly_discovery.discovery_profile_index
  USING (searchable = true OR mangaly_authz.is_self(profile_id));

GRANT USAGE ON SCHEMA mangaly_discovery TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_discovery TO mangaly_app;

-- =============================================================================
-- 7. mangaly_compatibility — Compatibility Engine (BR07) [TR030-TR034]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_compatibility AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_compatibility.assessment_status AS ENUM ('not_started','in_progress','completed','skipped');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR033] Instrument-agnostic; instrument_key stays NULL until Product
-- selects one (v1-decisions.md "What stays open") — never hardcode a
-- specific instrument's question set/scoring logic.
CREATE TABLE IF NOT EXISTS mangaly_compatibility.assessment_response (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id      uuid NOT NULL UNIQUE,
  instrument_key  text,
  response_data   jsonb,
  status          mangaly_compatibility.assessment_status NOT NULL DEFAULT 'not_started',
  skipped_at      timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_compatibility.assessment_response IS '[TR033] Never gates Discovery or the core Compatibility path (TR032).';

-- [TR034] Separately-toggled table — no code path reads this unless
-- opted_in = true (enforced as a query-time filter, not convention).
CREATE TABLE IF NOT EXISTS mangaly_compatibility.horoscope (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL UNIQUE,
  opted_in       boolean NOT NULL DEFAULT false,
  birth_details  jsonb,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_compatibility.horoscope IS '[TR034] A non-opted-in candidate''s Compatibility computation has no code path capable of reading this table.';

CREATE TABLE IF NOT EXISTS mangaly_compatibility.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_compat_outbox_unpublished ON mangaly_compatibility.outbox_event(published_at) WHERE published_at IS NULL;

ALTER TABLE mangaly_compatibility.assessment_response ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS assessment_owner_or_granted ON mangaly_compatibility.assessment_response;
CREATE POLICY assessment_owner_or_granted ON mangaly_compatibility.assessment_response
  USING (mangaly_authz.is_self(profile_id) OR mangaly_authz.has_scope(profile_id, 'candidate_info'));
ALTER TABLE mangaly_compatibility.horoscope ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS horoscope_owner_or_granted ON mangaly_compatibility.horoscope;
CREATE POLICY horoscope_owner_or_granted ON mangaly_compatibility.horoscope
  USING (opted_in = true AND (mangaly_authz.is_self(profile_id) OR mangaly_authz.has_scope(profile_id, 'candidate_info')));

GRANT USAGE ON SCHEMA mangaly_compatibility TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_compatibility TO mangaly_app;

-- =============================================================================
-- 8. mangaly_trust — Trust & Verification (BR08) [TR035-TR041]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_trust AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_trust.layer_type AS ENUM
    ('account_authenticity','identity_age','profile_facts','home_circle_relationship','community_verification','operational_verification');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_trust.layer_status AS ENUM ('unavailable','pending','self_reported','verified','disputed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_trust.verifier_invite_status AS ENUM ('invited','confirmed','declined','expired','invalidated');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR035/TR036] Six independent layers — never collapsed into one score.
CREATE TABLE IF NOT EXISTS mangaly_trust.verification_layer_status (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL,
  layer          mangaly_trust.layer_type NOT NULL,
  status         mangaly_trust.layer_status NOT NULL DEFAULT 'unavailable',
  provenance     text,
  source_category text,
  verified_at    timestamptz,
  freshness_expires_at timestamptz,
  updated_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (profile_id, layer)
);
CREATE INDEX IF NOT EXISTS idx_trust_layer_profile ON mangaly_trust.verification_layer_status(profile_id);
COMMENT ON TABLE mangaly_trust.verification_layer_status IS '[TR035/TR039] No aggregate score column exists anywhere on this table or any view over it.';

-- [TR037/DEC-V1-004] Idempotent per candidate-fact pair (unique constraint).
CREATE TABLE IF NOT EXISTS mangaly_trust.verification_circle_invite (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id         uuid NOT NULL,
  verifier_account_id uuid NOT NULL,
  fact_reference     text NOT NULL,
  status             mangaly_trust.verifier_invite_status NOT NULL DEFAULT 'invited',
  invited_at         timestamptz NOT NULL DEFAULT now(),
  responded_at       timestamptz,
  invalidated_at     timestamptz,
  invalidation_reason text,
  UNIQUE (profile_id, verifier_account_id, fact_reference)
);
CREATE INDEX IF NOT EXISTS idx_verifier_invite_profile ON mangaly_trust.verification_circle_invite(profile_id);
COMMENT ON TABLE mangaly_trust.verification_circle_invite IS '[TR037] invalidated, never deleted, on fraud finding; rate-limited via mangaly_platform.rate_limit_counter.';

-- [TR038] Admin/Mangaly-operated verification fallback, unconditional.
CREATE TABLE IF NOT EXISTS mangaly_trust.admin_verification_request (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL,
  requested_at   timestamptz NOT NULL DEFAULT now(),
  sla_target_at  timestamptz NOT NULL DEFAULT (now() + interval '1 hour'),
  case_reference uuid   -- unconstrained pointer to mangaly_operations.case
);

-- [TR040] Raw verification documents. NEVER exposed via the Evidence-panel
-- response model — only Operations' role-gated Admin Case detail endpoint
-- (a structurally separate response model, TR040) may read this table.
CREATE TABLE IF NOT EXISTS mangaly_trust.evidence_document_ref (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id                  uuid NOT NULL,
  verification_circle_invite_id uuid REFERENCES mangaly_trust.verification_circle_invite(id) ON DELETE SET NULL,
  admin_verification_request_id uuid REFERENCES mangaly_trust.admin_verification_request(id) ON DELETE SET NULL,
  storage_ref                 text NOT NULL,
  document_type               text NOT NULL,
  uploaded_at                 timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_evidence_doc_profile ON mangaly_trust.evidence_document_ref(profile_id);
COMMENT ON TABLE mangaly_trust.evidence_document_ref IS '[TR040] Highest-sensitivity table in this schema — raw verification documents. Read path restricted to the Operations Admin Case detail endpoint only.';

CREATE TABLE IF NOT EXISTS mangaly_trust.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_trust_outbox_unpublished ON mangaly_trust.outbox_event(published_at) WHERE published_at IS NULL;

ALTER TABLE mangaly_trust.verification_layer_status ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS trust_layer_owner_or_granted ON mangaly_trust.verification_layer_status;
CREATE POLICY trust_layer_owner_or_granted ON mangaly_trust.verification_layer_status
  USING (mangaly_authz.is_self(profile_id) OR mangaly_authz.has_scope(profile_id, 'candidate_info'));
ALTER TABLE mangaly_trust.verification_circle_invite ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS verifier_invite_participants ON mangaly_trust.verification_circle_invite;
CREATE POLICY verifier_invite_participants ON mangaly_trust.verification_circle_invite
  USING (mangaly_authz.is_self(profile_id) OR mangaly_authz.is_self(verifier_account_id));
ALTER TABLE mangaly_trust.admin_verification_request ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS admin_verif_request_owner_or_ops ON mangaly_trust.admin_verification_request;
CREATE POLICY admin_verif_request_owner_or_ops ON mangaly_trust.admin_verification_request
  USING (mangaly_authz.is_self(profile_id) OR current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_trust.evidence_document_ref ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS evidence_doc_ops_only ON mangaly_trust.evidence_document_ref;
CREATE POLICY evidence_doc_ops_only ON mangaly_trust.evidence_document_ref
  USING (current_setting('mangaly.operator_role', true) = 'operations');

GRANT USAGE ON SCHEMA mangaly_trust TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_trust TO mangaly_app;

-- =============================================================================
-- 9. mangaly_connection — Connection & Sharing (BR09, BR10) [TR042-TR048]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_connection AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_connection.connection_status AS ENUM ('pending','accepted','declined');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR042/TR043/TR044/TR045] No single-active-connection constraint — many
-- concurrent accepted connections fully supported.
CREATE TABLE IF NOT EXISTS mangaly_connection.connection_request (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  acting_account_id      uuid NOT NULL,     -- candidate, or family member acting on-behalf-of
  on_behalf_of_profile_id uuid,
  target_profile_id      uuid NOT NULL,
  status                 mangaly_connection.connection_status NOT NULL DEFAULT 'pending',
  requested_at           timestamptz NOT NULL DEFAULT now(),
  decided_at             timestamptz,
  decided_by_account_id  uuid,
  created_at             timestamptz NOT NULL DEFAULT now(),
  updated_at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_connection_target ON mangaly_connection.connection_request(target_profile_id, status);
CREATE INDEX IF NOT EXISTS idx_connection_acting ON mangaly_connection.connection_request(acting_account_id);
COMMENT ON TABLE mangaly_connection.connection_request IS '[TR043] No default/auto-expiry transition — no scheduled job targets this table''s status column.';

-- [TR046] Per-category, own row, own independent grant timestamp.
CREATE TABLE IF NOT EXISTS mangaly_connection.sharing_grant (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id    uuid NOT NULL REFERENCES mangaly_connection.connection_request(id) ON DELETE CASCADE,
  category         text NOT NULL,
  granted_by_account_id uuid NOT NULL,
  granted_at       timestamptz NOT NULL DEFAULT now(),
  revoked_at       timestamptz,
  UNIQUE (connection_id, category)
);
COMMENT ON TABLE mangaly_connection.sharing_grant IS '[TR046] Never a combined bitmask/flag field — one row per category.';

-- [TR048] Requires two independently-resolved AuthzContexts.
CREATE TABLE IF NOT EXISTS mangaly_connection.family_contact_share (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id             uuid NOT NULL REFERENCES mangaly_connection.connection_request(id) ON DELETE CASCADE,
  candidate_account_id      uuid NOT NULL,
  family_member_account_id  uuid NOT NULL,
  candidate_authz_resolved_at timestamptz,
  family_authz_resolved_at  timestamptz,
  granted_at                timestamptz,
  created_at                timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_connection.family_contact_share IS '[TR048] granted_at set only once BOTH candidate_authz_resolved_at and family_authz_resolved_at are non-null.';

CREATE TABLE IF NOT EXISTS mangaly_connection.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_conn_outbox_unpublished ON mangaly_connection.outbox_event(published_at) WHERE published_at IS NULL;

ALTER TABLE mangaly_connection.connection_request ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS connection_participants ON mangaly_connection.connection_request;
CREATE POLICY connection_participants ON mangaly_connection.connection_request
  USING (mangaly_authz.is_self(acting_account_id) OR mangaly_authz.is_self(target_profile_id)
         OR mangaly_authz.has_scope(on_behalf_of_profile_id, 'candidate_info'));
ALTER TABLE mangaly_connection.sharing_grant ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS sharing_grant_participants ON mangaly_connection.sharing_grant;
CREATE POLICY sharing_grant_participants ON mangaly_connection.sharing_grant
  USING (EXISTS (SELECT 1 FROM mangaly_connection.connection_request c WHERE c.id = sharing_grant.connection_id
                 AND (mangaly_authz.is_self(c.acting_account_id) OR mangaly_authz.is_self(c.target_profile_id))));
ALTER TABLE mangaly_connection.family_contact_share ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS family_contact_share_participants ON mangaly_connection.family_contact_share;
CREATE POLICY family_contact_share_participants ON mangaly_connection.family_contact_share
  USING (mangaly_authz.is_self(candidate_account_id) OR mangaly_authz.is_self(family_member_account_id));

GRANT USAGE ON SCHEMA mangaly_connection TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_connection TO mangaly_app;

-- =============================================================================
-- 10. mangaly_communication — Communication (BR11, BR12) [TR049-TR059]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_communication AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_communication.exchange_status AS ENUM ('pending','accepted','declined');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_communication.job_run_status AS ENUM ('success','failure','partial');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR049/TR055] One conversation per accepted connection; no
-- seriousness-score/exclusivity column anywhere.
CREATE TABLE IF NOT EXISTS mangaly_communication.conversation (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id  uuid NOT NULL UNIQUE,   -- cross-schema ref to mangaly_connection.connection_request
  created_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_communication.conversation IS '[TR055] No seriousness-score/exclusivity column; multiple concurrent conversations per candidate fully supported.';

CREATE TABLE IF NOT EXISTS mangaly_communication.message (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES mangaly_communication.conversation(id) ON DELETE CASCADE,
  sender_account_id uuid NOT NULL,
  content         text NOT NULL,
  sent_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_message_conversation ON mangaly_communication.message(conversation_id, sent_at);
COMMENT ON TABLE mangaly_communication.message IS
  '[TR051] Exactly one application-level read path beyond the sender/recipient: the case-scoped Safety Intelligence pathway (TR064). Highest-sensitivity table in the module.';

-- [TR053] Individually-logged, scope-limited retention exception.
CREATE TABLE IF NOT EXISTS mangaly_communication.retention_policy_exception (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id       uuid NOT NULL REFERENCES mangaly_communication.conversation(id) ON DELETE CASCADE,
  triggered_by_safety_case_reference uuid NOT NULL,
  ops_case_reference    uuid NOT NULL,
  created_at            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_communication.retention_policy_exception IS '[TR053] Scope: this conversation only, never cross-conversation. Duration ceiling is a config read (DPDP-gated), not hardcoded.';

-- [TR054] Legal-hold suspension of deletion.
CREATE TABLE IF NOT EXISTS mangaly_communication.legal_hold (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES mangaly_communication.conversation(id) ON DELETE CASCADE,
  active         boolean NOT NULL DEFAULT true,
  reason         text NOT NULL,
  placed_at      timestamptz NOT NULL DEFAULT now(),
  released_at    timestamptz
);
CREATE INDEX IF NOT EXISTS idx_legal_hold_active ON mangaly_communication.legal_hold(conversation_id) WHERE active = true;

-- [TR054] Retention/lifecycle job failure-alerting — built now, independent
-- of the still-open legal-hold scope question.
CREATE TABLE IF NOT EXISTS mangaly_communication.retention_job_run (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_at       timestamptz NOT NULL DEFAULT now(),
  status       mangaly_communication.job_run_status NOT NULL,
  error_detail text,
  alerted_at   timestamptz
);

-- [TR057/TR058/TR059] Each contact channel independently gated; recipient-
-- only decision authority even within one Home Circle.
CREATE TABLE IF NOT EXISTS mangaly_communication.contact_exchange_request (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id         uuid NOT NULL,
  requester_account_id  uuid NOT NULL,
  status                mangaly_communication.exchange_status NOT NULL DEFAULT 'pending',
  phone_disclosed_at    timestamptz,
  email_disclosed_at    timestamptz,
  requested_at          timestamptz NOT NULL DEFAULT now(),
  decided_at            timestamptz,
  decided_by_account_id uuid
);
COMMENT ON TABLE mangaly_communication.contact_exchange_request IS
  '[TR059] phone_disclosed_at/email_disclosed_at are independently nullable — disclosing one never implies the other. [TR058] decided_by_account_id must differ from requester_account_id even within one Home Circle, enforced at the application layer.';

CREATE TABLE IF NOT EXISTS mangaly_communication.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_comm_outbox_unpublished ON mangaly_communication.outbox_event(published_at) WHERE published_at IS NULL;

ALTER TABLE mangaly_communication.conversation ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS conversation_participants ON mangaly_communication.conversation;
CREATE POLICY conversation_participants ON mangaly_communication.conversation
  USING (EXISTS (SELECT 1 FROM mangaly_connection.connection_request c WHERE c.id = conversation.connection_id
                 AND (mangaly_authz.is_self(c.acting_account_id) OR mangaly_authz.is_self(c.target_profile_id))));
ALTER TABLE mangaly_communication.message ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS message_sender_or_safety_case ON mangaly_communication.message;
CREATE POLICY message_sender_or_safety_case ON mangaly_communication.message
  USING (mangaly_authz.is_self(sender_account_id)
         OR EXISTS (SELECT 1 FROM mangaly_communication.conversation cv WHERE cv.id = message.conversation_id)
            AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation');
ALTER TABLE mangaly_communication.retention_policy_exception ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS retention_exception_ops_only ON mangaly_communication.retention_policy_exception;
CREATE POLICY retention_exception_ops_only ON mangaly_communication.retention_policy_exception
  USING (current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_communication.legal_hold ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS legal_hold_ops_only ON mangaly_communication.legal_hold;
CREATE POLICY legal_hold_ops_only ON mangaly_communication.legal_hold
  USING (current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_communication.contact_exchange_request ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contact_exchange_participants ON mangaly_communication.contact_exchange_request;
CREATE POLICY contact_exchange_participants ON mangaly_communication.contact_exchange_request
  USING (mangaly_authz.is_self(requester_account_id) OR mangaly_authz.is_self(decided_by_account_id));

GRANT USAGE ON SCHEMA mangaly_communication TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_communication TO mangaly_app;
-- retention_job_run is written only by the background lifecycle job's own
-- service-role context, not by request-scoped app traffic; no per-row RLS
-- needed (it carries no per-user data), but table-level grants stay scoped
-- to mangaly_app since there is no separate job-runner role in V1.

-- =============================================================================
-- 11. mangaly_safety — Safety Intelligence (BR14, BR20-reporting) [TR063-TR068]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_safety AUTHORIZATION mangaly_owner;

-- [TR063/TR087] Universal, non-downgradable reporting entry point — shared
-- by the in-app report flow and the post-meeting report flow (identical pipeline).
CREATE TABLE IF NOT EXISTS mangaly_safety.report (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_account_id      uuid NOT NULL,
  reported_profile_id      uuid,
  reported_message_id      uuid,      -- cross-schema ref to mangaly_communication.message, no FK
  meeting_context_reference uuid,     -- cross-schema ref to mangaly_lifecycle.meeting_note, no FK
  category                 text NOT NULL,  -- validated at the application layer against DEC-V1-006's named taxonomy, not a hardcoded DB enum (taxonomy is a versioned config object per TR068)
  description              text,
  source                   text NOT NULL DEFAULT 'user_reported',
  created_at                timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_safety_report_reporter ON mangaly_safety.report(reporter_account_id);
COMMENT ON TABLE mangaly_safety.report IS '[TR063] Triage never uses "no automated-detection signal fired" as a dismissal criterion — structural rule in the triage query, not enforced by this table alone.';

-- [TR064] Automated detection — message metadata/text only, never photo/video,
-- never Home Circle or Trust data (repository-layer absence, not modeled here
-- because it is an absence: no FK/column referencing those schemas exists).
CREATE TABLE IF NOT EXISTS mangaly_safety.detection_signal (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid,               -- cross-schema ref to mangaly_communication.conversation, no FK
  signal_type     text NOT NULL,
  inference       boolean NOT NULL DEFAULT false,  -- [TR064/TR028] mandatory AI-signal label
  metadata        jsonb,
  detected_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_safety.detection_signal IS '[TR064] No column anywhere in this schema references mangaly_home_circle or mangaly_trust — a structural absence, not an unused capability.';

-- [TR065/TR068/DEC-V1-006] Severity classification drives the graduated
-- response pipeline's SLA clock; tier definitions read from config.
CREATE TABLE IF NOT EXISTS mangaly_safety.severity_classification (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id           uuid REFERENCES mangaly_safety.report(id) ON DELETE CASCADE,
  detection_signal_id uuid REFERENCES mangaly_safety.detection_signal(id) ON DELETE CASCADE,
  tier                smallint NOT NULL CHECK (tier BETWEEN 1 AND 4),
  classified_at       timestamptz NOT NULL DEFAULT now(),
  sla_clock_started_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT one_source CHECK (num_nonnulls(report_id, detection_signal_id) = 1)
);
CREATE INDEX IF NOT EXISTS idx_severity_tier ON mangaly_safety.severity_classification(tier);
COMMENT ON TABLE mangaly_safety.severity_classification IS '[TR065] Tier 3/4 rows are the ones that must auto-fire mangaly_operations.paging_event / csam_report_packet — see that schema.';

CREATE TABLE IF NOT EXISTS mangaly_safety.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_safety_outbox_unpublished ON mangaly_safety.outbox_event(published_at) WHERE published_at IS NULL;

ALTER TABLE mangaly_safety.report ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS safety_report_reporter_or_ops ON mangaly_safety.report;
CREATE POLICY safety_report_reporter_or_ops ON mangaly_safety.report
  USING (mangaly_authz.is_self(reporter_account_id) OR current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_safety.detection_signal ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS detection_signal_ops_only ON mangaly_safety.detection_signal;
CREATE POLICY detection_signal_ops_only ON mangaly_safety.detection_signal
  USING (current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_safety.severity_classification ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS severity_classification_ops_only ON mangaly_safety.severity_classification;
CREATE POLICY severity_classification_ops_only ON mangaly_safety.severity_classification
  USING (current_setting('mangaly.operator_role', true) = 'operations');

GRANT USAGE ON SCHEMA mangaly_safety TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_safety TO mangaly_app;

-- =============================================================================
-- 12. mangaly_lifecycle — Lifecycle & Outcomes (BR18, BR19, BR20-guidance) [TR079-TR088]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_lifecycle AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_lifecycle.lifecycle_status AS ENUM ('active','concluded');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_lifecycle.consent_status AS ENUM ('pending','granted','revoked');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR079/TR080/TR081] Sole path to concluded; excluded from Discovery/
-- Compatibility without any historical data loss elsewhere.
CREATE TABLE IF NOT EXISTS mangaly_lifecycle.profile_lifecycle_status (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL UNIQUE,
  status         mangaly_lifecycle.lifecycle_status NOT NULL DEFAULT 'active',
  concluded_at   timestamptz,
  reactivated_at timestamptz,
  updated_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_lifecycle.profile_lifecycle_status IS '[TR079] No inactivity-duration job or other inferred-from-behavior mechanism may write this table — sole write path is PATCH /profile/lifecycle/conclude|reactivate.';

-- [TR086] Manual-only "meeting occurred" note.
CREATE TABLE IF NOT EXISTS mangaly_lifecycle.meeting_note (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id uuid NOT NULL,
  noted_by_account_id uuid NOT NULL,
  occurred_at   timestamptz,
  note_text     text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- [TR082/TR083] Each party's own explicit, independent, revocable consent.
CREATE TABLE IF NOT EXISTS mangaly_lifecycle.success_story_invite (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id  uuid NOT NULL,
  invited_by_account_id uuid NOT NULL,
  party_a_consent_status mangaly_lifecycle.consent_status NOT NULL DEFAULT 'pending',
  party_b_consent_status mangaly_lifecycle.consent_status NOT NULL DEFAULT 'pending',
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_lifecycle.success_story_invite IS '[TR083] Declining writes no field anywhere any other component''s logic reads (negative-dependency contract, same pattern as TR012).';

-- [TR084] Allow-listed payload only — excludes Home Circle, private
-- Communication content, and Trust contact details beyond explicit approval.
CREATE TABLE IF NOT EXISTS mangaly_lifecycle.success_story (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  success_story_invite_id   uuid NOT NULL REFERENCES mangaly_lifecycle.success_story_invite(id) ON DELETE CASCADE,
  allow_listed_payload      jsonb NOT NULL,
  automated_scan_passed     boolean NOT NULL DEFAULT false,
  reviewed_by_account_id    uuid,
  reviewed_at               timestamptz,
  published_at              timestamptz,
  takedown_at               timestamptz
);
COMMENT ON TABLE mangaly_lifecycle.success_story IS '[TR084] automated_scan_passed must be true, in addition to manual review, before published_at may be set — enforced at the application layer.';

CREATE TABLE IF NOT EXISTS mangaly_lifecycle.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_lifecycle_outbox_unpublished ON mangaly_lifecycle.outbox_event(published_at) WHERE published_at IS NULL;
COMMENT ON TABLE mangaly_lifecycle.outbox_event IS '[TR081] Also the sole publisher of the mangaly.activity_summary event consumed by Dashboard (MOD05) over the platform Message Broker — privacy-filtered, never raw match/profile data.';

ALTER TABLE mangaly_lifecycle.profile_lifecycle_status ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lifecycle_owner_or_granted ON mangaly_lifecycle.profile_lifecycle_status;
CREATE POLICY lifecycle_owner_or_granted ON mangaly_lifecycle.profile_lifecycle_status
  USING (mangaly_authz.is_self(profile_id) OR mangaly_authz.has_scope(profile_id, 'candidate_info'));
ALTER TABLE mangaly_lifecycle.meeting_note ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS meeting_note_noter_only ON mangaly_lifecycle.meeting_note;
CREATE POLICY meeting_note_noter_only ON mangaly_lifecycle.meeting_note
  USING (mangaly_authz.is_self(noted_by_account_id));
ALTER TABLE mangaly_lifecycle.success_story_invite ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS success_invite_participants ON mangaly_lifecycle.success_story_invite;
CREATE POLICY success_invite_participants ON mangaly_lifecycle.success_story_invite USING (true);
ALTER TABLE mangaly_lifecycle.success_story ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS success_story_published_or_ops ON mangaly_lifecycle.success_story;
CREATE POLICY success_story_published_or_ops ON mangaly_lifecycle.success_story
  USING (published_at IS NOT NULL OR current_setting('mangaly.operator_role', true) = 'operations');

GRANT USAGE ON SCHEMA mangaly_lifecycle TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_lifecycle TO mangaly_app;

-- =============================================================================
-- 13. mangaly_operations — Operations (BR16) [TR038, TR065, TR072-TR076, TR100]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_operations AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_operations.case_type AS ENUM
    ('verification','false_relationship_dispute','safety_abuse','support_ticket_escalated');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_operations.case_status AS ENUM
    ('intake','triage','assigned','investigation','decided','escalated','resolved','appealed','appeal_resolved');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_operations.decision_type AS ENUM ('approve','deny','request_more_evidence','escalate');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR072/DEC-V1-007] intake -> triage -> assignment -> investigation ->
-- decision -> resolution -> appeal, as an explicit state machine.
CREATE TABLE IF NOT EXISTS mangaly_operations.case (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_type             mangaly_operations.case_type NOT NULL,
  source_schema         text NOT NULL,     -- e.g. 'mangaly_trust', 'mangaly_home_circle', 'mangaly_safety'
  source_reference_id   uuid NOT NULL,     -- unconstrained pointer into that schema's own record
  status                mangaly_operations.case_status NOT NULL DEFAULT 'intake',
  priority_tier         smallint CHECK (priority_tier IS NULL OR priority_tier BETWEEN 1 AND 4),
  assigned_operator_id  uuid,
  sla_target_at         timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_case_status_priority ON mangaly_operations.case(status, priority_tier);
CREATE INDEX IF NOT EXISTS idx_case_source ON mangaly_operations.case(source_schema, source_reference_id);
COMMENT ON TABLE mangaly_operations.case IS '[TR072/TR073/TR074] One state machine for verification, false-relationship-dispute, and safety/fraud cases alike — not three independently-built variants.';

CREATE TABLE IF NOT EXISTS mangaly_operations.case_decision (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id         uuid NOT NULL REFERENCES mangaly_operations.case(id) ON DELETE CASCADE,
  decision_type   mangaly_operations.decision_type NOT NULL,
  decided_by_operator_id uuid NOT NULL,
  rationale_text  text,
  decided_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_case_decision_case ON mangaly_operations.case_decision(case_id);

-- [TR075] Reviewer-independence is a soft preference (DEC-V1-007's "where
-- staffing allows"), not a hard constraint — no CHECK forcing a different
-- reviewer, since a small on-call team genuinely cannot always guarantee it.
CREATE TABLE IF NOT EXISTS mangaly_operations.case_appeal (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id               uuid NOT NULL REFERENCES mangaly_operations.case(id) ON DELETE CASCADE,
  appealed_by_account_id uuid NOT NULL,
  reviewer_operator_id  uuid,
  decision              mangaly_operations.decision_type,
  appealed_at           timestamptz NOT NULL DEFAULT now(),
  decided_at            timestamptz
);

-- [TR076] No role may reference "all cases" — structurally, not by policy:
-- case_type_scope is a required, single, named enum value; there is no
-- '*'/all member of mangaly_operations.case_type to grant.
CREATE TABLE IF NOT EXISTS mangaly_operations.operator_role_scope (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_account_id uuid NOT NULL,
  case_type_scope    mangaly_operations.case_type NOT NULL,
  granted_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (operator_account_id, case_type_scope)
);
COMMENT ON TABLE mangaly_operations.operator_role_scope IS '[TR076] case_type_scope''s type is the case_type enum itself — a wildcard/all value is not a valid enum member, so it cannot be granted even by mistake.';

-- [DEC-V1-009/TR065] Tier 3/4 on-call paging — auto-fired, never manual.
CREATE TABLE IF NOT EXISTS mangaly_operations.paging_event (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id           uuid NOT NULL REFERENCES mangaly_operations.case(id) ON DELETE CASCADE,
  tier              smallint NOT NULL CHECK (tier IN (3,4)),
  paging_vendor_ref text,
  paged_at          timestamptz NOT NULL DEFAULT now(),
  acknowledged_at   timestamptz
);
COMMENT ON TABLE mangaly_operations.paging_event IS '[DEC-V1-009] Vendor is a Step 7 procurement choice; the auto-fire-on-Tier-3/4-classification trigger contract is fixed here.';

-- [DEC-V1-009/POCSO Rule 11(2)] Structured hand-off packet, fired in
-- parallel with the internal block, never sequenced after investigation.
CREATE TABLE IF NOT EXISTS mangaly_operations.csam_report_packet (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id                     uuid NOT NULL REFERENCES mangaly_operations.case(id) ON DELETE CASCADE,
  packet_payload_ref          text NOT NULL,   -- Object Storage ref: content + provenance + reporting-account identifiers
  submitted_to                text NOT NULL,   -- 'cybercrime_portal' | 'sjpu' | 'local_police'
  submitted_at                timestamptz NOT NULL DEFAULT now(),
  source_material_handover_at timestamptz
);
COMMENT ON TABLE mangaly_operations.csam_report_packet IS '[DEC-V1-009 Rule 11(2)] source_material_handover_at records the mandatory handover of the material and its source, not merely a notification.';

-- [TR100] Thin support ticket; safety-classified tickets route into the
-- Safety pipeline (routed_case_id), same SLA-critical treatment as Tier 3/4.
CREATE TABLE IF NOT EXISTS mangaly_operations.support_ticket (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  submitted_by_account_id uuid NOT NULL,
  description         text NOT NULL,
  classified_as_safety boolean NOT NULL DEFAULT false,
  routed_case_id      uuid REFERENCES mangaly_operations.case(id) ON DELETE SET NULL,
  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mangaly_operations.outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_id uuid NOT NULL, event_type text NOT NULL,
  payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_ops_outbox_unpublished ON mangaly_operations.outbox_event(published_at) WHERE published_at IS NULL;
COMMENT ON TABLE mangaly_operations.outbox_event IS '[TR076] 100% admin-action audit coverage — every mutation on this schema publishes a corresponding event, lint-enforced at the application layer.';

ALTER TABLE mangaly_operations.case ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS case_ops_scoped ON mangaly_operations.case;
CREATE POLICY case_ops_scoped ON mangaly_operations.case
  USING (current_setting('mangaly.operator_role', true) = 'operations'
         AND EXISTS (SELECT 1 FROM mangaly_operations.operator_role_scope s
                     WHERE s.operator_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
                       AND s.case_type_scope = "case".case_type));
ALTER TABLE mangaly_operations.case_decision ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS case_decision_ops_only ON mangaly_operations.case_decision;
CREATE POLICY case_decision_ops_only ON mangaly_operations.case_decision
  USING (current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_operations.case_appeal ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS case_appeal_participant_or_ops ON mangaly_operations.case_appeal;
CREATE POLICY case_appeal_participant_or_ops ON mangaly_operations.case_appeal
  USING (mangaly_authz.is_self(appealed_by_account_id) OR current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_operations.operator_role_scope ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS operator_scope_ops_only ON mangaly_operations.operator_role_scope;
CREATE POLICY operator_scope_ops_only ON mangaly_operations.operator_role_scope
  USING (current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_operations.paging_event ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS paging_event_ops_only ON mangaly_operations.paging_event;
CREATE POLICY paging_event_ops_only ON mangaly_operations.paging_event
  USING (current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_operations.csam_report_packet ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS csam_packet_ops_only ON mangaly_operations.csam_report_packet;
CREATE POLICY csam_packet_ops_only ON mangaly_operations.csam_report_packet
  USING (current_setting('mangaly.operator_role', true) = 'operations');
ALTER TABLE mangaly_operations.support_ticket ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS support_ticket_submitter_or_ops ON mangaly_operations.support_ticket;
CREATE POLICY support_ticket_submitter_or_ops ON mangaly_operations.support_ticket
  USING (mangaly_authz.is_self(submitted_by_account_id) OR current_setting('mangaly.operator_role', true) = 'operations');

GRANT USAGE ON SCHEMA mangaly_operations TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_operations TO mangaly_app;

-- =============================================================================
-- 14. mangaly_notification — Notification Bridge (in-app inbox only) [TR098]
-- Delivery itself stays a thin Common Platform pass-through (architecture.md
-- §2.1) — this schema exists solely for the persistent inbox record.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS mangaly_notification AUTHORIZATION mangaly_owner;

DO $$ BEGIN
  CREATE TYPE mangaly_notification.push_delivery_status AS ENUM ('not_attempted','sent','failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS mangaly_notification.inbox_entry (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  recipient_account_id  uuid NOT NULL,
  source_component      text NOT NULL,
  event_type            text NOT NULL,
  payload               jsonb NOT NULL,
  push_delivery_status  mangaly_notification.push_delivery_status NOT NULL DEFAULT 'not_attempted',
  read_at               timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_inbox_recipient ON mangaly_notification.inbox_entry(recipient_account_id, read_at);
COMMENT ON TABLE mangaly_notification.inbox_entry IS
  '[TR098] Independent of whether the underlying push delivery succeeded. Every notification-worthy event from Profile/Home Circle/Connection/Communication/Safety/Operations produces exactly one row here — lint-enforced completeness at the application layer.';

ALTER TABLE mangaly_notification.inbox_entry ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inbox_recipient_only ON mangaly_notification.inbox_entry;
CREATE POLICY inbox_recipient_only ON mangaly_notification.inbox_entry
  USING (mangaly_authz.is_self(recipient_account_id));

GRANT USAGE ON SCHEMA mangaly_notification TO mangaly_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mangaly_notification TO mangaly_app;

-- =============================================================================
-- 15. RLS on outbox_event (+ retention_job_run) tables
-- [MODULE-ARCHITECTURE-STANDARD §6/TR069] Added after LIVE testing against a
-- real Postgres instance surfaced that these 11 internal event-bus tables
-- had been reasoned about as "dispatcher-only" but that predicate had never
-- actually been implemented as RLS — every other table got a real policy,
-- these were silently left at the Postgres default (RLS disabled). Fixed
-- here rather than left as a documentation-only intent: reads are
-- restricted to the internal event-dispatcher's own service-role context
-- (a payload can legitimately contain another actor's data — e.g. a
-- ConnectionRequested event's payload references both parties — so an
-- unrestricted read here would be a real cross-actor leak path). Inserts
-- stay open to any authenticated transaction, since publishing an event is
-- a normal, expected part of every business mutation, not a privileged
-- action gated by who is asking.
-- =============================================================================
DO $$
DECLARE
  s text;
BEGIN
  FOREACH s IN ARRAY ARRAY[
    'mangaly_profile','mangaly_home_circle','mangaly_authz','mangaly_discovery',
    'mangaly_compatibility','mangaly_trust','mangaly_connection','mangaly_communication',
    'mangaly_safety','mangaly_lifecycle','mangaly_operations'
  ]
  LOOP
    EXECUTE format('ALTER TABLE %I.outbox_event ENABLE ROW LEVEL SECURITY', s);
    EXECUTE format('DROP POLICY IF EXISTS outbox_insert_any_authenticated ON %I.outbox_event', s);
    EXECUTE format('CREATE POLICY outbox_insert_any_authenticated ON %I.outbox_event FOR INSERT WITH CHECK (true)', s);
    EXECUTE format('DROP POLICY IF EXISTS outbox_select_dispatcher_only ON %I.outbox_event', s);
    EXECUTE format(
      'CREATE POLICY outbox_select_dispatcher_only ON %I.outbox_event FOR SELECT USING (current_setting(''mangaly.service_role'', true) = ''dispatcher'')',
      s
    );
  END LOOP;
END $$;

ALTER TABLE mangaly_communication.retention_job_run ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS retention_job_run_insert_any ON mangaly_communication.retention_job_run;
CREATE POLICY retention_job_run_insert_any ON mangaly_communication.retention_job_run FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS retention_job_run_select_ops_or_dispatcher ON mangaly_communication.retention_job_run;
CREATE POLICY retention_job_run_select_ops_or_dispatcher ON mangaly_communication.retention_job_run FOR SELECT
  USING (current_setting('mangaly.operator_role', true) = 'operations' OR current_setting('mangaly.service_role', true) = 'dispatcher');

-- =============================================================================
-- End of schema.sql
-- =============================================================================
