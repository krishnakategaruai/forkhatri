-- =============================================================================
-- 001 — Identity & Trust Service initial schema (database forkhatri_identity)
--
-- Run as identity_owner:
--   psql -h localhost -p 5433 -U identity_owner -d forkhatri_identity -f db/migrations/001-initial.sql
--
-- Contract: docs/ParentApp/07-tech-reqs.md TR10-TR20.
--
-- Why no row-level security here, unlike the module schemas: this service's
-- core operations are lookups by identifier or by session-token digest that
-- necessarily run before any member context exists (sign-in, code
-- verification, internal session resolution). Every such query would need a
-- SECURITY DEFINER bypass, which is the same privilege RLS is meant to remove.
-- Protection instead comes from isolation (own database, only this service
-- connects), a non-owning runtime role with the minimum grants below (no
-- DELETE on members, no DDL), and digests-not-secrets storage.
-- Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS registry;
CREATE SCHEMA IF NOT EXISTS platform;

DO $$ BEGIN
  CREATE TYPE identity.member_status AS ENUM ('active', 'suspended', 'deleted');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE identity.otp_channel AS ENUM ('sms', 'email');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE identity.auth_method AS ENUM ('otp', 'password');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- [TR10] The one canonical member. Module person records reference this id.
CREATE TABLE IF NOT EXISTS identity.member (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name        text NOT NULL CHECK (char_length(btrim(display_name)) BETWEEN 1 AND 80),
  phone_e164          text UNIQUE CHECK (phone_e164 ~ '^\+[1-9][0-9]{7,14}$'),
  email               text UNIQUE CHECK (email = lower(email) AND position('@' in email) > 1),
  preferred_language  text NOT NULL DEFAULT 'en' CHECK (preferred_language IN ('en', 'hi', 'te')),
  home_locality       text CHECK (home_locality IS NULL OR char_length(home_locality) <= 120),
  -- Platform Level 1/2 trust (modules.md shared concern). Level 1 = a verified
  -- phone or email. Module Level-3 trust is module data, never stored here.
  identity_level      smallint NOT NULL DEFAULT 1 CHECK (identity_level BETWEEN 0 AND 2),
  status              identity.member_status NOT NULL DEFAULT 'active',
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT member_has_identifier CHECK (phone_e164 IS NOT NULL OR email IS NOT NULL)
);
COMMENT ON TABLE identity.member IS '[TR10] Canonical ForKhatri member. PII: phone_e164, email.';

-- [TR19] Optional secondary credential. Argon2id digests only.
CREATE TABLE IF NOT EXISTS identity.password_credential (
  member_id      uuid PRIMARY KEY REFERENCES identity.member(id) ON DELETE CASCADE,
  password_hash  text NOT NULL CHECK (password_hash LIKE '$argon2id$%'),
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

-- [TR19] One-time code keyed by identifier, not member: sign-in and sign-up are
-- one flow, and the member may not exist yet.
CREATE TABLE IF NOT EXISTS identity.otp_challenge (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  identifier      text NOT NULL,
  channel         identity.otp_channel NOT NULL,
  code_hmac       text NOT NULL,
  attempt_count   integer NOT NULL DEFAULT 0,
  max_attempts    integer NOT NULL DEFAULT 5,
  expires_at      timestamptz NOT NULL,
  verified_at     timestamptz,
  consumed_at     timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_otp_challenge_identifier ON identity.otp_challenge (identifier, created_at DESC);

-- [TR12] Server-side session. Only the SHA-256 digest of the bearer token is stored.
CREATE TABLE IF NOT EXISTS identity.session (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id      uuid NOT NULL REFERENCES identity.member(id) ON DELETE CASCADE,
  token_hash     bytea NOT NULL UNIQUE,
  auth_method    identity.auth_method NOT NULL,
  user_agent     text,
  created_at     timestamptz NOT NULL DEFAULT now(),
  last_seen_at   timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL,
  revoked_at     timestamptz
);
CREATE INDEX IF NOT EXISTS idx_session_member ON identity.session (member_id);

-- [TR20] Shared fixed-window rate limiter (MODULE-ARCHITECTURE-STANDARD §4c).
CREATE TABLE IF NOT EXISTS platform.rate_limit_counter (
  bucket_key    text NOT NULL,
  window_start  timestamptz NOT NULL,
  hit_count     integer NOT NULL DEFAULT 0,
  PRIMARY KEY (bucket_key, window_start)
);

-- [TR18] Module registry. Entry URLs are environment configuration, not rows.
CREATE TABLE IF NOT EXISTS registry.module (
  key           text PRIMARY KEY CHECK (key ~ '^[a-z][a-z0-9_]{1,30}$'),
  name          text NOT NULL,
  tagline_en    text NOT NULL,
  tagline_hi    text NOT NULL,
  tagline_te    text NOT NULL,
  availability  text NOT NULL CHECK (availability IN ('available', 'in_development', 'planned')),
  accent        text NOT NULL CHECK (accent ~ '^#[0-9a-fA-F]{6}$'),
  sort_order    smallint NOT NULL,
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- [TR18] Platform-owned index of which module surfaces a member has entered.
-- Not an access-control list: every member may enter every available module;
-- module tiers and roles live in the modules (TR11).
CREATE TABLE IF NOT EXISTS registry.member_module_entry (
  member_id         uuid NOT NULL REFERENCES identity.member(id) ON DELETE CASCADE,
  module_key        text NOT NULL REFERENCES registry.module(key),
  first_entered_at  timestamptz NOT NULL DEFAULT now(),
  last_entered_at   timestamptz NOT NULL DEFAULT now(),
  entry_count       integer NOT NULL DEFAULT 1,
  PRIMARY KEY (member_id, module_key)
);

-- Least-privilege runtime grants.
GRANT USAGE ON SCHEMA identity, registry, platform TO identity_app;
GRANT SELECT, INSERT, UPDATE ON identity.member TO identity_app;
GRANT SELECT, INSERT, UPDATE ON identity.password_credential TO identity_app;
GRANT SELECT, INSERT, UPDATE ON identity.otp_challenge TO identity_app;
GRANT SELECT, INSERT, UPDATE ON identity.session TO identity_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON platform.rate_limit_counter TO identity_app;
GRANT SELECT ON registry.module TO identity_app;
GRANT SELECT, INSERT, UPDATE ON registry.member_module_entry TO identity_app;
