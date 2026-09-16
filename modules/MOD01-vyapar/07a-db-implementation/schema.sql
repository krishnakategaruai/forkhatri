-- =============================================================================
-- Vyapar (MOD01) — Postgres schema DDL
-- Snapshot of the current schema, equivalent to applying migrations/001-initial.sql.
-- Keep this file and migrations/ in sync — this file exists for fast local/dev
-- setup (init.sh runs it directly); migrations/ is the authoritative, ordered
-- history. See 07a-db-implementation/README.md.
--
-- Traces to: modules/MOD01-vyapar/07a-er-model.md (full traceability table),
-- 07-tech-reqs.md (TR001-TR055 + "Closing note for Step 7a"),
-- /MODULE-ARCHITECTURE-STANDARD.md §4/§4b/§4c/§5/§5b/§6.
--
-- Design conventions applied uniformly (see 07a-er-model.md "Assumptions" for
-- the full reasoning on each):
--   1. One Postgres schema per schema-owning component (07-tech-reqs.md
--      "Component decomposition (Vyapar)" table), plus one infrastructure
--      schema (vyapar_platform: idempotency + rate-limiting, per
--      MODULE-ARCHITECTURE-STANDARD §4b/§4c) that is not a business-logic
--      component and does not extend the 13-component list. Discovery &
--      Ranking and the Authorization Engine own no tables (logic-only,
--      per 07-tech-reqs.md's own component table) and therefore have no
--      schema of their own — this is a stated decision, not an omission.
--   2. Every table has id (uuid or platform-opaque text pk per 07a-er-model.md),
--      created_at, updated_at (except pure append-only event/log tables, which
--      have created_at/occurred_at only — an update would violate their
--      append-only intent).
--   3. Cross-schema references are stored as plain, indexed columns with NO
--      database-level FOREIGN KEY constraint — a real FK would require
--      granting cross-schema SELECT and would let one component's schema
--      silently depend on another's internal row lifecycle, which is exactly
--      what "no cross-schema join written by any component other than the
--      schema's own owner" (MODULE-ARCHITECTURE-STANDARD §4) forbids.
--      Referential integrity across schemas is enforced by the owning
--      component's own interface at the application layer, not the DB.
--      Within one schema (same owning component), real FK constraints with
--      an explicit cascade rule are used.
--   4. RLS: every table whose rows are visible to more than one actor, or
--      whose sensitivity warrants it, gets RLS enabled at creation time
--      (never bolted on later) per MODULE-ARCHITECTURE-STANDARD §4. The
--      runtime role (vyapar_app) is a NON-OWNING role — vyapar_owner (the
--      migration role) owns every object. RLS keys off ONE SET LOCAL session
--      variable the Identity Bridge sets per-transaction (TR050's own exact
--      wording), never plain SET (the pooling-safety failure mode):
--        vyapar.authz_context  — the platform member id TR050's resolve()
--                                 call produces, bound once per request.
--      A shared helper, vyapar_identity.is_operator(permission), centralizes
--      the operator-bypass predicate so no table re-derives it independently
--      — it reads the SAME operator_permissions array TR047/TR048/TR049
--      already gate specific admin routes on, so DB-layer and route-layer
--      authorization cannot silently diverge.
--      A second variable, vyapar.service_role, gates the background
--      dispatcher's read of outbox_event tables (never set by request-time
--      code).
--   5. Outbox pattern (MODULE-ARCHITECTURE-STANDARD §6): the three schemas
--      07-tech-reqs.md names as actually publishing domain events
--      (vyapar_listings — TR002/TR003/TR048; vyapar_opportunities — TR013;
--      vyapar_commercial — TR030) each get their own outbox_event table so
--      the event insert commits in the exact same transaction as the state
--      change it describes. No other schema is given one — inventing an
--      outbox table for a component with no cited domain-event requirement
--      would be an orphan ER element (Pass 2).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Extensions. Roles are NOT created here.
-- -----------------------------------------------------------------------------
-- Postgres roles are cluster-wide, not database-local, and creating one
-- requires CREATEROLE/superuser — a migration running as the non-superuser
-- vyapar_owner role cannot create roles, by design (same finding Mangaly's
-- 07a pass made live). Role provisioning is therefore an infrastructure/ops
-- step init.sh performs BEFORE running this file, as an actual admin
-- connection — see init.sh Step 2. This file only assumes vyapar_owner and
-- vyapar_app already exist and grants privileges to them; it never attempts
-- CREATE ROLE.
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

-- =============================================================================
-- 1. vyapar_identity — Identity Bridge [TR050, FR44, FR50]
-- Thin per architecture (no credentials, no sessions — those are the
-- platform's own, per MODULE-ARCHITECTURE-STANDARD §5b) but genuinely owns
-- one table: the member-link row every other schema references by plain id.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_identity AUTHORIZATION vyapar_owner;

-- [TR050/FR50] member.id is the platform's own opaque member id (never a
-- Vyapar-generated identity) — created just-in-time on first entry via
-- ensure_member() below, never via a signup form. [TR044/FR44] first_run_*
-- track the five-screen progressive first-run (no auth screen in this flow —
-- a structural absence, see TR044). [TR037] deleted_at/anonymized implement
-- the anonymize-in-place deletion contract: on account deletion, this row is
-- scrubbed and anonymized=true is set, but the row (and its id) is NEVER
-- removed, so every other schema's plain member_id/owner_id/sender_id columns
-- continue to resolve — a counterpart's enquiry thread or review is never
-- corrupted by cascade delete (TR037's own explicit rule; IA037).
CREATE TABLE IF NOT EXISTS vyapar_identity.members (
  id                    text PRIMARY KEY,
  display_name          text NOT NULL,
  phone                 text,
  trust_level           smallint NOT NULL DEFAULT 1,
  language              text NOT NULL DEFAULT 'en' CHECK (language IN ('en','hi','te')),
  locality              text,
  lat                   double precision,
  lng                   double precision,
  radius_km             smallint NOT NULL DEFAULT 10,
  work_mode             text CHECK (work_mode IN ('on_site','remote','both')),
  help_with             text[] NOT NULL DEFAULT '{}',
  capabilities          text[] NOT NULL DEFAULT '{}',
  is_operator           boolean NOT NULL DEFAULT false,
  operator_permissions  text[] NOT NULL DEFAULT '{}' CHECK (operator_permissions <@ ARRAY['verification','content','commercial','analytics','moderation']),
  first_run_done        boolean NOT NULL DEFAULT false,
  first_run_step        smallint NOT NULL DEFAULT 0,
  avatar_url            text,
  anonymized            boolean NOT NULL DEFAULT false,
  deleted_at            timestamptz,
  synced_at             timestamptz NOT NULL DEFAULT now(),
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE vyapar_identity.members IS
  '[TR050] Thin Identity Bridge member-link row, keyed by the platform member id. PII (phone, locality, lat/lng). Never a login/credential table.';

-- [Cross-cutting §3 / MODULE-ARCHITECTURE-STANDARD §4] shared operator-bypass
-- predicate — every other schema's RLS policies call this instead of
-- re-deriving "is this actor staff with permission X" independently. Reads
-- the SAME operator_permissions array TR047/048/049 already gate admin
-- routes on. SECURITY DEFINER + pinned search_path (search-path injection
-- defense), STABLE (safe to call once per row-check).
CREATE OR REPLACE FUNCTION vyapar_identity.is_operator(p_permission text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_identity, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM vyapar_identity.members m
    WHERE m.id = current_setting('vyapar.authz_context', true)
      AND m.is_operator
      AND (p_permission IS NULL OR p_permission = ANY (m.operator_permissions))
  );
$$;
COMMENT ON FUNCTION vyapar_identity.is_operator(text) IS
  '[MODULE-ARCHITECTURE-STANDARD §4/§5] Shared RLS operator-bypass helper. p_permission NULL means "any operator flag", matching the broad admin-visibility surfaces (e.g. members lookups); a specific permission string (verification|content|commercial|analytics|moderation) matches TR047-TR049''s own route-level gate exactly, so DB and route enforcement cannot silently diverge.';

-- [TR050] Pre-authorization escape hatch, same pattern as Mangaly's
-- lookup_by_identifier(): the row this statement creates/updates is the
-- very row vyapar.authz_context will reference, so it must run BEFORE that
-- session variable is meaningful for THIS member. Called once per request
-- by the Identity Bridge immediately after it has already independently
-- validated the platform session (TR050) — p_member_id is therefore
-- trusted input from that resolve() call, never raw end-user input.
CREATE OR REPLACE FUNCTION vyapar_identity.ensure_member(
  p_member_id text, p_display_name text, p_phone text, p_language text
) RETURNS void
LANGUAGE sql SECURITY DEFINER
SET search_path = vyapar_identity, pg_temp
AS $$
  INSERT INTO vyapar_identity.members (id, display_name, phone, language)
  VALUES (p_member_id, p_display_name, p_phone, coalesce(p_language, 'en'))
  ON CONFLICT (id) DO UPDATE SET synced_at = now(), updated_at = now();
$$;
COMMENT ON FUNCTION vyapar_identity.ensure_member(text, text, text, text) IS
  '[TR050/IA050] Idempotent just-in-time upsert, closing the duplicate-row risk. The ONLY write path to this table that runs before vyapar.authz_context exists for a new member.';

-- [TR034] Narrow, exact-match phone lookup for Business Workspace invites —
-- returns only what the invite flow needs (id, display_name), never a full
-- profile scan, and is the sole path that reads another member's row by a
-- value other than their own id.
CREATE OR REPLACE FUNCTION vyapar_identity.lookup_member_by_phone(p_phone text)
RETURNS TABLE(id text, display_name text)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_identity, pg_temp
AS $$
  SELECT m.id, m.display_name FROM vyapar_identity.members m WHERE m.phone = p_phone;
$$;
COMMENT ON FUNCTION vyapar_identity.lookup_member_by_phone(text) IS '[TR034] Workspace invite-by-phone resolution — narrow response shape by design.';

ALTER TABLE vyapar_identity.members ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS members_self_or_operator ON vyapar_identity.members;
CREATE POLICY members_self_or_operator ON vyapar_identity.members
  USING (id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL))
  WITH CHECK (id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL));

GRANT USAGE ON SCHEMA vyapar_identity TO vyapar_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA vyapar_identity TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_identity.is_operator(text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_identity.ensure_member(text, text, text, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_identity.lookup_member_by_phone(text) TO vyapar_app;

-- =============================================================================
-- 2. vyapar_listings — Listings & Verification [FR01-FR10, FR47]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_listings AUTHORIZATION vyapar_owner;

-- [FR01, FR04, FR48] shared reference list; free-text fallback via
-- unmapped_labels[]/aliases[] (CCR10) so nothing is ever blocked pending
-- taxonomy review.
CREATE TABLE IF NOT EXISTS vyapar_listings.taxonomy_terms (
  id          serial PRIMARY KEY,
  kind        text NOT NULL CHECK (kind IN ('category','capability')),
  slug        text NOT NULL,
  name_en     text NOT NULL,
  name_hi     text,
  name_te     text,
  icon        text,
  parent_id   int REFERENCES vyapar_listings.taxonomy_terms(id),
  aliases     text[] NOT NULL DEFAULT '{}',
  status      text NOT NULL DEFAULT 'active' CHECK (status IN ('active','unmapped','merged')),
  merged_into int REFERENCES vyapar_listings.taxonomy_terms(id),
  version     int NOT NULL DEFAULT 1,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kind, slug)
);

-- [FR01-FR07, FR10, FR16, FR30, FR42] BusinessProfile | ProfessionalListingProfile.
-- setup_step [TR004 gap] makes "reached Discover before optional fields" a
-- server-verifiable state. intent_visible defaults false [FR05 — private by
-- default]; capability_visible is an INDEPENDENT boolean — the two must
-- never be conflated (TR005's own highest-severity-risk fix: Listings'
-- own public-read function is the sole place that decides whether to
-- include intent_state, never a raw column read from any other component).
CREATE TABLE IF NOT EXISTS vyapar_listings.listings (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id                text NOT NULL,                 -- vyapar_identity.members(id), no cross-schema FK (§4)
  kind                    text NOT NULL CHECK (kind IN ('business','professional')),
  name                    text NOT NULL,
  headline                text,
  description             text,
  content_language        text CHECK (content_language IN ('en','hi','te')),  -- [TR042 gap]
  categories              text[] NOT NULL DEFAULT '{}',
  capabilities            text[] NOT NULL DEFAULT '{}',
  unmapped_labels         text[] NOT NULL DEFAULT '{}',
  services                jsonb NOT NULL DEFAULT '[]',
  locality                text NOT NULL,
  lat                     double precision,
  lng                     double precision,
  service_radius_km       smallint NOT NULL DEFAULT 10,
  service_mode            text NOT NULL DEFAULT 'both' CHECK (service_mode IN ('on_site','remote','both')),
  enquiry_pref            text NOT NULL DEFAULT 'enabled' CHECK (enquiry_pref IN ('enabled','disabled')),
  enquiry_disabled_reason text,
  opportunity_participation boolean NOT NULL DEFAULT true,
  discoverable            boolean NOT NULL DEFAULT true,   -- [FR02]
  partnership_open        boolean NOT NULL DEFAULT true,   -- [FR25]
  primary_phone           text,
  contact_verified        boolean NOT NULL DEFAULT false,  -- [FR07]
  setup_step              smallint NOT NULL DEFAULT 0,     -- [TR004 gap]
  experience_years        smallint,
  languages               text[] NOT NULL DEFAULT '{}',
  availability            text CHECK (availability IN ('now','this_week','later')),
  evidence_links          text[] NOT NULL DEFAULT '{}',
  rates                   text,
  intent_state            text CHECK (intent_state IN ('looking','open','curious','not_interested')), -- [FR05]
  intent_visible          boolean NOT NULL DEFAULT false,   -- [FR05] private by default
  capability_visible      boolean NOT NULL DEFAULT true,    -- [FR05] independent control
  state                   text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','submitted','active_unverified','active_verified','suspended','archived')),
  state_reason            text,
  verification_state      text NOT NULL DEFAULT 'not_started' CHECK (verification_state IN ('not_started','pending','verified','expiring','expired','rejected','revoked','disputed')),
  verification_document   text,
  verification_claim      text,
  verified_at             timestamptz,
  verification_expires_at timestamptz,
  credential_ref          jsonb,                           -- [FR06] {id,claim,issuer,verified_at,last_checked}
  image_url               text,
  cover_url               text,
  response_minutes        int,                              -- [FR28]
  distribution_limited    boolean NOT NULL DEFAULT false,   -- [TR040] auto-limit at report-merge time
  last_confirmed_at       timestamptz NOT NULL DEFAULT now(),
  published_at            timestamptz,
  search_tsv              tsvector,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now(),
  UNIQUE (owner_id, name, locality)                         -- [FR01] duplicate rule
);
CREATE INDEX IF NOT EXISTS listings_search_idx ON vyapar_listings.listings USING GIN (search_tsv);
CREATE INDEX IF NOT EXISTS listings_state_idx ON vyapar_listings.listings (state, discoverable);
CREATE INDEX IF NOT EXISTS listings_owner_idx ON vyapar_listings.listings (owner_id);
COMMENT ON TABLE vyapar_listings.listings IS '[FR01-FR10] BusinessProfile/ProfessionalListingProfile. intent_state is private-sensitive (FR05) — never read outside this schema''s own public-read function.';

-- [FR02] disclosure is per-channel and independent of the listing's own
-- discoverability toggle.
CREATE TABLE IF NOT EXISTS vyapar_listings.listing_contacts (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id  uuid NOT NULL REFERENCES vyapar_listings.listings(id) ON DELETE CASCADE,
  channel     text NOT NULL CHECK (channel IN ('phone','whatsapp','email','website','address')),
  value       text NOT NULL,
  disclosure  text NOT NULL DEFAULT 'after_accept' CHECK (disclosure IN ('public','after_accept','hidden'))
);
CREATE INDEX IF NOT EXISTS listing_contacts_listing_idx ON vyapar_listings.listing_contacts (listing_id);

-- [FR24/TR002/TR024] narrow, same-schema function: exposes an after_accept
-- contact ONLY when the caller (Enquiries & Partnerships' own composed read,
-- per TR024) has already independently confirmed acceptance in ITS OWN
-- schema and passes that fact in — this function never queries
-- vyapar_enquiries itself (that would be the exact cross-schema join §4
-- forbids). p_disclose_after_accept is the caller's own, already-resolved
-- boolean, not derived here.
CREATE OR REPLACE FUNCTION vyapar_listings.contacts_for_viewer(
  p_listing_id uuid, p_disclose_after_accept boolean
) RETURNS SETOF vyapar_listings.listing_contacts
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_listings, pg_temp
AS $$
  SELECT * FROM vyapar_listings.listing_contacts
  WHERE listing_id = p_listing_id
    AND (disclosure = 'public' OR (disclosure = 'after_accept' AND p_disclose_after_accept));
$$;
COMMENT ON FUNCTION vyapar_listings.contacts_for_viewer(uuid, boolean) IS '[TR002/TR024] The single call site every enquiry/detail read uses for contact-channel visibility — never a second, independently-coded check.';

-- [FR07] listing-contact OTP — NOT authentication (Cross-cutting/TR007).
CREATE TABLE IF NOT EXISTS vyapar_listings.otp_challenges (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id    text NOT NULL,
  listing_id   uuid REFERENCES vyapar_listings.listings(id) ON DELETE CASCADE,
  phone        text NOT NULL,
  code         text NOT NULL,
  attempts     smallint NOT NULL DEFAULT 0,
  expires_at   timestamptz NOT NULL,
  resend_after timestamptz NOT NULL,
  locked_until timestamptz,
  verified_at  timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS otp_challenges_listing_idx ON vyapar_listings.otp_challenges (listing_id);
COMMENT ON TABLE vyapar_listings.otp_challenges IS '[TR007] Ephemeral verification code state. Sensitive: private to the requesting member only, no operator visibility.';

-- [TR007 gap] a change to primary_phone must reset contact_verified.
CREATE OR REPLACE FUNCTION vyapar_listings.reset_contact_verified() RETURNS trigger AS $$
BEGIN
  IF NEW.primary_phone IS DISTINCT FROM OLD.primary_phone THEN
    NEW.contact_verified := false;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS listings_phone_change_resets_verified ON vyapar_listings.listings;
CREATE TRIGGER listings_phone_change_resets_verified BEFORE UPDATE ON vyapar_listings.listings
  FOR EACH ROW EXECUTE FUNCTION vyapar_listings.reset_contact_verified();

-- [FR08, FR09, FR47] business-existence / professional-credential documents.
-- identifier_enc/image_url are the module's most identity-sensitive columns
-- (CCR07) — masked display + 30-day image_delete_after (TR008).
CREATE TABLE IF NOT EXISTS vyapar_listings.verification_records (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id         uuid NOT NULL REFERENCES vyapar_listings.listings(id) ON DELETE CASCADE,
  member_id          text NOT NULL,
  kind               text NOT NULL CHECK (kind IN ('business','credential')),
  document_type      text NOT NULL CHECK (document_type IN ('gst','udyam','pan','shops_est','credential')),
  identifier_masked  text,
  identifier_enc     text,
  image_url          text,
  credential_name    text,
  issuer             text,
  state              text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','verified','rejected','needs_clearer_copy','revoked','expired')),
  reason_code        text,
  verifier_id        text,
  decided_at         timestamptz,
  expires_at         timestamptz,
  image_delete_after timestamptz,
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS verification_records_listing_idx ON vyapar_listings.verification_records (listing_id);
COMMENT ON TABLE vyapar_listings.verification_records IS '[TR008/TR009] Identity/credential-sensitive. Owner-only + verification-permission operator visibility.';

-- [FR16] Save/view on listings — natural extension of Listings & Verification
-- (same schema as listings, same owner, real FK).
CREATE TABLE IF NOT EXISTS vyapar_listings.member_listing (
  member_id   text NOT NULL,
  listing_id  uuid NOT NULL REFERENCES vyapar_listings.listings(id) ON DELETE CASCADE,
  saved_at    timestamptz,
  viewed_at   timestamptz,
  PRIMARY KEY (member_id, listing_id)
);

-- [MODULE-ARCHITECTURE-STANDARD §6, TR002/TR003/TR048] transactional outbox.
CREATE TABLE IF NOT EXISTS vyapar_listings.outbox_event (
  id           bigserial PRIMARY KEY,
  event_type   text NOT NULL,
  payload      jsonb NOT NULL,
  published_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

-- search + distance triggers/functions
CREATE OR REPLACE FUNCTION vyapar_listings.listings_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.search_tsv :=
    setweight(to_tsvector('simple', coalesce(NEW.name,'')), 'A') ||
    setweight(to_tsvector('simple', array_to_string(NEW.categories || NEW.capabilities || NEW.unmapped_labels, ' ')), 'B') ||
    setweight(to_tsvector('simple', coalesce(NEW.description,'')), 'C') ||
    setweight(to_tsvector('simple', coalesce(NEW.locality,'')), 'C');
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS listings_tsv ON vyapar_listings.listings;
CREATE TRIGGER listings_tsv BEFORE INSERT OR UPDATE ON vyapar_listings.listings
  FOR EACH ROW EXECUTE FUNCTION vyapar_listings.listings_tsv_update();

-- RLS
ALTER TABLE vyapar_listings.listings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS listings_visibility ON vyapar_listings.listings;
CREATE POLICY listings_visibility ON vyapar_listings.listings
  USING (state IN ('active_unverified','active_verified') OR owner_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('content'))
  WITH CHECK (owner_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('content'));

ALTER TABLE vyapar_listings.listing_contacts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS listing_contacts_owner_or_public ON vyapar_listings.listing_contacts;
CREATE POLICY listing_contacts_owner_or_public ON vyapar_listings.listing_contacts
  USING (disclosure = 'public'
    OR EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.id = listing_contacts.listing_id AND l.owner_id = current_setting('vyapar.authz_context', true))
    OR vyapar_identity.is_operator('content'));

ALTER TABLE vyapar_listings.otp_challenges ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS otp_self_only ON vyapar_listings.otp_challenges;
CREATE POLICY otp_self_only ON vyapar_listings.otp_challenges
  USING (member_id = current_setting('vyapar.authz_context', true));

ALTER TABLE vyapar_listings.verification_records ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS verification_owner_or_verifier ON vyapar_listings.verification_records;
CREATE POLICY verification_owner_or_verifier ON vyapar_listings.verification_records
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('verification'));

ALTER TABLE vyapar_listings.member_listing ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_listing_self ON vyapar_listings.member_listing;
CREATE POLICY member_listing_self ON vyapar_listings.member_listing
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL));

ALTER TABLE vyapar_listings.outbox_event ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outbox_insert_any ON vyapar_listings.outbox_event;
CREATE POLICY outbox_insert_any ON vyapar_listings.outbox_event FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS outbox_select_dispatcher ON vyapar_listings.outbox_event;
CREATE POLICY outbox_select_dispatcher ON vyapar_listings.outbox_event FOR SELECT
  USING (current_setting('vyapar.service_role', true) = 'dispatcher');

GRANT USAGE ON SCHEMA vyapar_listings TO vyapar_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapar_listings TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_listings.contacts_for_viewer(uuid, boolean) TO vyapar_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vyapar_listings TO vyapar_app;

-- =============================================================================
-- 3. vyapar_opportunities — Opportunities [FR11-FR14, FR55]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_opportunities AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_opportunities.opportunities (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  poster_id             text NOT NULL,
  listing_id            uuid,                              -- vyapar_listings.listings(id), no cross-schema FK
  title                 text NOT NULL,
  type                  text NOT NULL CHECK (type IN ('employment','freelance','local_service','partnership','training','community')),
  description           text,
  content_language      text CHECK (content_language IN ('en','hi','te')),  -- [TR042 gap]
  requirements          text,
  compensation          text,
  value_amount          numeric,
  location              text,
  lat                   double precision,
  lng                   double precision,
  work_mode             text CHECK (work_mode IN ('on_site','remote','both')),
  timing                text,
  eligibility           jsonb NOT NULL DEFAULT '{}',
  required_capabilities text[] NOT NULL DEFAULT '{}',
  response_method       text CHECK (response_method IN ('in_app','external')),
  deadline              timestamptz,
  source_segment        text NOT NULL CHECK (source_segment IN ('community','public')),
  source_name           text,
  source_url            text,
  source_unreachable    boolean NOT NULL DEFAULT false,
  entry_mode            text NOT NULL DEFAULT 'create' CHECK (entry_mode IN ('create','share','upload')),
  raw_input             text,
  raw_image_url         text,
  unconfirmed_fields    text[] NOT NULL DEFAULT '{}',        -- [FR12]
  confirmed_fields      text[] NOT NULL DEFAULT '{}',
  state                 text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','pending_review','active','paused','stale','expired','closed','removed')),
  state_reason          text,
  distribution_limited  boolean NOT NULL DEFAULT false,      -- [TR040] auto-limit
  image_url             text,
  last_confirmed_at     timestamptz NOT NULL DEFAULT now(),
  reminder_sent_at      timestamptz,
  published_at          timestamptz,
  search_tsv            tsvector,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS opportunities_search_idx ON vyapar_opportunities.opportunities USING GIN (search_tsv);
CREATE INDEX IF NOT EXISTS opportunities_state_idx ON vyapar_opportunities.opportunities (state, source_segment);
CREATE INDEX IF NOT EXISTS opportunities_poster_idx ON vyapar_opportunities.opportunities (poster_id);

CREATE TABLE IF NOT EXISTS vyapar_opportunities.member_opportunity (  -- [FR55]
  member_id       text NOT NULL,
  opportunity_id  uuid NOT NULL REFERENCES vyapar_opportunities.opportunities(id) ON DELETE CASCADE,
  saved_at        timestamptz,
  viewed_at       timestamptz,
  hidden_at       timestamptz,
  hidden_reason   text CHECK (hidden_reason IN ('too_far','wrong_type','not_my_capability','value_too_low','wrong_timing','already_found','not_interested')),
  shared_at       timestamptz,
  external_opened_at timestamptz,
  completed_at    timestamptz,
  PRIMARY KEY (member_id, opportunity_id)
);

CREATE TABLE IF NOT EXISTS vyapar_opportunities.outbox_event (  -- [TR013]
  id           bigserial PRIMARY KEY,
  event_type   text NOT NULL,
  payload      jsonb NOT NULL,
  published_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION vyapar_opportunities.opportunities_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.search_tsv :=
    setweight(to_tsvector('simple', coalesce(NEW.title,'')), 'A') ||
    setweight(to_tsvector('simple', array_to_string(NEW.required_capabilities, ' ')), 'B') ||
    setweight(to_tsvector('simple', coalesce(NEW.description,'') || ' ' || coalesce(NEW.requirements,'')), 'C') ||
    setweight(to_tsvector('simple', coalesce(NEW.location,'')), 'C');
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS opportunities_tsv ON vyapar_opportunities.opportunities;
CREATE TRIGGER opportunities_tsv BEFORE INSERT OR UPDATE ON vyapar_opportunities.opportunities
  FOR EACH ROW EXECUTE FUNCTION vyapar_opportunities.opportunities_tsv_update();

ALTER TABLE vyapar_opportunities.opportunities ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS opportunities_visibility ON vyapar_opportunities.opportunities;
CREATE POLICY opportunities_visibility ON vyapar_opportunities.opportunities
  USING (state IN ('active','paused','stale') OR poster_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('content'))
  WITH CHECK (poster_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('content'));

ALTER TABLE vyapar_opportunities.member_opportunity ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_opportunity_self ON vyapar_opportunities.member_opportunity;
CREATE POLICY member_opportunity_self ON vyapar_opportunities.member_opportunity
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL));

ALTER TABLE vyapar_opportunities.outbox_event ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outbox_insert_any ON vyapar_opportunities.outbox_event;
CREATE POLICY outbox_insert_any ON vyapar_opportunities.outbox_event FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS outbox_select_dispatcher ON vyapar_opportunities.outbox_event;
CREATE POLICY outbox_select_dispatcher ON vyapar_opportunities.outbox_event FOR SELECT
  USING (current_setting('vyapar.service_role', true) = 'dispatcher');

GRANT USAGE ON SCHEMA vyapar_opportunities TO vyapar_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapar_opportunities TO vyapar_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vyapar_opportunities TO vyapar_app;

-- =============================================================================
-- 4. vyapar_enquiries — Enquiries & Partnerships [FR22-FR26]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_enquiries AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_enquiries.enquiries (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id          text NOT NULL,
  provider_id        text NOT NULL,
  listing_id         uuid,                                  -- no cross-schema FK
  opportunity_id     uuid,                                  -- no cross-schema FK
  action_type        text NOT NULL CHECK (action_type IN ('enquire','apply','propose','contact','register')),
  sub_choice         text,
  state              text NOT NULL DEFAULT 'open' CHECK (state IN ('open','awaiting_response','in_progress','resolved','closed','withdrawn','restricted')),
  delivered          boolean NOT NULL DEFAULT true,
  safety_notice_seen boolean NOT NULL DEFAULT false,
  first_reply_at     timestamptz,
  state_reason       text,                                   -- [TR023] e.g. 'no_response_yet', never overwrites state itself
  last_activity_at   timestamptz NOT NULL DEFAULT now(),
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  CHECK (listing_id IS NOT NULL OR opportunity_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS enquiries_sender_idx ON vyapar_enquiries.enquiries (sender_id, state);
CREATE INDEX IF NOT EXISTS enquiries_provider_idx ON vyapar_enquiries.enquiries (provider_id, state);
-- [TR022 gap] one open enquiry per (sender, target) — database-enforced, not
-- only an application check a race condition could bypass.
CREATE UNIQUE INDEX IF NOT EXISTS enquiries_one_open_per_target
  ON vyapar_enquiries.enquiries (sender_id, COALESCE(listing_id::text, opportunity_id::text))
  WHERE state NOT IN ('resolved','closed','withdrawn');

CREATE TABLE IF NOT EXISTS vyapar_enquiries.enquiry_messages (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  enquiry_id     uuid NOT NULL REFERENCES vyapar_enquiries.enquiries(id) ON DELETE CASCADE,
  sender_id      text NOT NULL,
  body           text NOT NULL CHECK (char_length(body) BETWEEN 1 AND 1000),
  content_language text CHECK (content_language IN ('en','hi','te')),  -- [TR042 gap]
  attachment_url text,
  system_note    boolean NOT NULL DEFAULT false,
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS enquiry_messages_enquiry_idx ON vyapar_enquiries.enquiry_messages (enquiry_id);

CREATE TABLE IF NOT EXISTS vyapar_enquiries.blocks (  -- [FR24, FR39]
  blocker_id  text NOT NULL,
  blocked_id  text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (blocker_id, blocked_id)
);

CREATE TABLE IF NOT EXISTS vyapar_enquiries.partnership_requests (  -- [FR25, FR26]
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id            text NOT NULL,
  recipient_id         text NOT NULL,
  sender_listing_id    uuid NOT NULL,                        -- no cross-schema FK
  recipient_listing_id uuid NOT NULL,                        -- no cross-schema FK
  need                 text NOT NULL,
  offer                text NOT NULL,
  expectations         text NOT NULL,
  content_language     text CHECK (content_language IN ('en','hi','te')),  -- [TR042 gap]
  category             text NOT NULL,
  locality             text NOT NULL,
  timing               text NOT NULL,
  next_step            text NOT NULL,
  state                text NOT NULL DEFAULT 'pending' CHECK (state IN ('draft','pending','accepted','declined','withdrawn','restricted','closed')),
  decided_at           timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS partnership_requests_sender_idx ON vyapar_enquiries.partnership_requests (sender_id, state);

ALTER TABLE vyapar_enquiries.enquiries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS enquiries_participants ON vyapar_enquiries.enquiries;
CREATE POLICY enquiries_participants ON vyapar_enquiries.enquiries
  USING (sender_id = current_setting('vyapar.authz_context', true) OR provider_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('moderation'))
  WITH CHECK (sender_id = current_setting('vyapar.authz_context', true) OR provider_id = current_setting('vyapar.authz_context', true));

ALTER TABLE vyapar_enquiries.enquiry_messages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS enquiry_messages_participants ON vyapar_enquiries.enquiry_messages;
CREATE POLICY enquiry_messages_participants ON vyapar_enquiries.enquiry_messages
  USING (EXISTS (SELECT 1 FROM vyapar_enquiries.enquiries e WHERE e.id = enquiry_messages.enquiry_id
                 AND (e.sender_id = current_setting('vyapar.authz_context', true) OR e.provider_id = current_setting('vyapar.authz_context', true)))
         OR vyapar_identity.is_operator('moderation'));

ALTER TABLE vyapar_enquiries.blocks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS blocks_blocker_only ON vyapar_enquiries.blocks;
CREATE POLICY blocks_blocker_only ON vyapar_enquiries.blocks
  USING (blocker_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('moderation'));

ALTER TABLE vyapar_enquiries.partnership_requests ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS partnership_participants ON vyapar_enquiries.partnership_requests;
CREATE POLICY partnership_participants ON vyapar_enquiries.partnership_requests
  USING (sender_id = current_setting('vyapar.authz_context', true) OR recipient_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL))
  WITH CHECK (sender_id = current_setting('vyapar.authz_context', true));

GRANT USAGE ON SCHEMA vyapar_enquiries TO vyapar_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapar_enquiries TO vyapar_app;

-- =============================================================================
-- 5. vyapar_reviews — Reviews & Reputation [FR27-FR29]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_reviews AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_reviews.review_invites (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  interaction_kind  text NOT NULL CHECK (interaction_kind IN ('enquiry','partnership')),
  interaction_id    uuid NOT NULL,                            -- no cross-schema FK (polymorphic + cross-schema)
  member_id         text NOT NULL,
  subject_listing_id uuid,                                    -- no cross-schema FK
  subject_member_id text NOT NULL,
  expires_at        timestamptz NOT NULL,
  used_at           timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (interaction_kind, interaction_id, member_id)
);

CREATE TABLE IF NOT EXISTS vyapar_reviews.reviews (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  interaction_kind   text NOT NULL CHECK (interaction_kind IN ('enquiry','partnership')),
  interaction_id     uuid NOT NULL,
  author_id          text NOT NULL,
  subject_listing_id uuid,
  subject_member_id  text NOT NULL,
  recommend          boolean NOT NULL,
  tags               text[] NOT NULL DEFAULT '{}' CHECK (cardinality(tags) <= 3),
  comment            text CHECK (comment IS NULL OR char_length(comment) BETWEEN 20 AND 500),
  content_language   text CHECK (content_language IN ('en','hi','te')),  -- [TR042 gap]
  state              text NOT NULL DEFAULT 'published' CHECK (state IN ('published','disputed','hidden','removed')),
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (interaction_kind, interaction_id, author_id)
);
CREATE INDEX IF NOT EXISTS reviews_subject_idx ON vyapar_reviews.reviews (subject_member_id, state);

CREATE TABLE IF NOT EXISTS vyapar_reviews.review_disputes (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  review_id   uuid NOT NULL REFERENCES vyapar_reviews.reviews(id) ON DELETE CASCADE,
  disputer_id text NOT NULL,
  reason      text NOT NULL CHECK (reason IN ('retaliation','manipulation','not_the_interaction','abusive')),
  outcome     text CHECK (outcome IN ('published','hidden','removed')),
  case_id     uuid,                                            -- no cross-schema FK (vyapar_trust_safety)
  decided_at  timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (review_id)
);

ALTER TABLE vyapar_reviews.review_invites ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS review_invites_self ON vyapar_reviews.review_invites;
CREATE POLICY review_invites_self ON vyapar_reviews.review_invites
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL));

ALTER TABLE vyapar_reviews.reviews ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reviews_published_or_party ON vyapar_reviews.reviews;
CREATE POLICY reviews_published_or_party ON vyapar_reviews.reviews
  USING (state = 'published' OR author_id = current_setting('vyapar.authz_context', true) OR subject_member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('moderation'))
  WITH CHECK (author_id = current_setting('vyapar.authz_context', true));
-- [TR029] Reviews & Reputation exposes NO write path for the review's own
-- subject at all — enforced structurally: WITH CHECK only ever admits
-- author_id = self, never subject_member_id = self, so a bug cannot grant a
-- provider self-hide/self-edit capability even at the RLS layer.

ALTER TABLE vyapar_reviews.review_disputes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS review_disputes_party ON vyapar_reviews.review_disputes;
CREATE POLICY review_disputes_party ON vyapar_reviews.review_disputes
  USING (disputer_id = current_setting('vyapar.authz_context', true)
    OR EXISTS (SELECT 1 FROM vyapar_reviews.reviews r WHERE r.id = review_disputes.review_id AND r.subject_member_id = current_setting('vyapar.authz_context', true))
    OR vyapar_identity.is_operator('moderation'));

GRANT USAGE ON SCHEMA vyapar_reviews TO vyapar_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapar_reviews TO vyapar_app;

-- =============================================================================
-- 6. vyapar_commercial — Commercial [FR30-FR35, FR49, FR54]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_commercial AUTHORIZATION vyapar_owner;

-- [TR049] insert-only: never UPDATE an existing (id,version) row with orders
-- against it — enforced by having no route capable of it (app layer); the
-- versioned composite PK below is the DB-level half of that guarantee.
CREATE TABLE IF NOT EXISTS vyapar_commercial.products (
  id             text NOT NULL,
  version        int NOT NULL DEFAULT 1,
  kind           text NOT NULL CHECK (kind IN ('boost','workspace','campaign')),
  name           text NOT NULL,
  description    text,
  duration_days  int,
  billing        text NOT NULL CHECK (billing IN ('one_time','monthly','annual')),
  price_paise    bigint NOT NULL,
  tax_rate_bp    int NOT NULL DEFAULT 1800,
  capabilities   text[] NOT NULL DEFAULT '{}',
  active         boolean NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, version)
);

CREATE TABLE IF NOT EXISTS vyapar_commercial.campaigns (  -- [FR35]
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id       text NOT NULL,                          -- uuid stored as text; no cross-schema FK
  owner_id         text NOT NULL,
  name             text NOT NULL,
  product_id       text NOT NULL,
  product_version  int NOT NULL,
  budget_paise     bigint NOT NULL,
  tax_paise        bigint NOT NULL,
  starts_at        timestamptz NOT NULL,
  ends_at          timestamptz NOT NULL,
  audience         jsonb NOT NULL DEFAULT '{}',
  item_refs        jsonb NOT NULL DEFAULT '[]',             -- [{kind,id}] up to 10, app-validated
  state            text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','awaiting_payment','active','completed','cancelled','refunded')),
  payment_order_id uuid,                                    -- no cross-schema FK (vyapar_payments)
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (product_id, product_version) REFERENCES vyapar_commercial.products(id, version)
);

CREATE TABLE IF NOT EXISTS vyapar_commercial.promotions (  -- [FR30, FR31]
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id         text NOT NULL,
  target_kind      text NOT NULL CHECK (target_kind IN ('listing','opportunity')),
  target_id        uuid NOT NULL,                           -- no cross-schema FK
  product_id       text NOT NULL,
  product_version  int NOT NULL,
  price_paise      bigint NOT NULL,
  tax_paise        bigint NOT NULL,
  audience         jsonb NOT NULL DEFAULT '{}',
  state            text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','awaiting_payment','scheduled','active','paused','completed','cancelled','rejected','refunded')),
  starts_at        timestamptz,
  ends_at          timestamptz,
  paused_at        timestamptz,
  credit_paise     bigint NOT NULL DEFAULT 0,
  campaign_id      uuid REFERENCES vyapar_commercial.campaigns(id),  -- [TR035 gap] now a real, same-schema FK
  payment_order_id uuid,                                     -- no cross-schema FK (vyapar_payments — CCR13 swap seam)
  reject_reason    text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (product_id, product_version) REFERENCES vyapar_commercial.products(id, version)
);
CREATE INDEX IF NOT EXISTS promotions_target_idx ON vyapar_commercial.promotions (target_kind, target_id);
CREATE INDEX IF NOT EXISTS promotions_owner_idx ON vyapar_commercial.promotions (owner_id);

-- [TR031 gap] generalized, kind-agnostic history — replaces the draft's
-- promotion-only history table so an Entitlement's state changes are also
-- owner-visible, per FR31's own text covering "a Promotion or Entitlement."
CREATE TABLE IF NOT EXISTS vyapar_commercial.commercial_order_history (
  id          bigserial PRIMARY KEY,
  order_kind  text NOT NULL CHECK (order_kind IN ('promotion','entitlement')),
  order_id    uuid NOT NULL,
  from_state  text,
  to_state    text NOT NULL,
  reason      text,
  at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS commercial_order_history_order_idx ON vyapar_commercial.commercial_order_history (order_kind, order_id);

CREATE TABLE IF NOT EXISTS vyapar_commercial.entitlements (  -- [FR33]
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id           text NOT NULL,                        -- no cross-schema FK
  owner_id             text NOT NULL,
  product_id           text NOT NULL,
  product_version      int NOT NULL,
  price_paise          bigint NOT NULL,
  tax_paise            bigint NOT NULL,
  state                text NOT NULL DEFAULT 'awaiting_payment' CHECK (state IN ('awaiting_payment','active','paused','cancelled','completed','refunded')),
  starts_at            timestamptz,
  renews_at            timestamptz,
  grace_until          timestamptz,
  cancel_at_period_end boolean NOT NULL DEFAULT false,
  renewal_reminder_at  timestamptz,
  renewal_reminder_acked_at timestamptz,     -- [TR054] renewal job's own guard — never fires charge without this
  payment_order_id     uuid,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (product_id, product_version) REFERENCES vyapar_commercial.products(id, version)
);
CREATE INDEX IF NOT EXISTS entitlements_owner_idx ON vyapar_commercial.entitlements (owner_id);

CREATE TABLE IF NOT EXISTS vyapar_commercial.workspace_members (  -- [FR34]
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id  text NOT NULL,                                 -- no cross-schema FK
  member_id   text,
  phone       text NOT NULL,
  role        text NOT NULL CHECK (role IN ('admin','operator')),
  state       text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','active','revoked','expired')),
  invited_by  text NOT NULL,
  invited_at  timestamptz NOT NULL DEFAULT now(),
  accepted_at timestamptz,
  revoked_at  timestamptz,
  expires_at  timestamptz NOT NULL DEFAULT now() + INTERVAL '30 days'
);
CREATE INDEX IF NOT EXISTS workspace_members_listing_idx ON vyapar_commercial.workspace_members (listing_id, state);

-- [MODULE-ARCHITECTURE-STANDARD §4] same-schema helper — reads ONLY
-- workspace_members (which Commercial owns), never listings' own ownership
-- column, so it is not a cross-schema join.
CREATE OR REPLACE FUNCTION vyapar_commercial.is_workspace_collaborator(p_listing_id text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_commercial, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM vyapar_commercial.workspace_members wm
    WHERE wm.listing_id = p_listing_id
      AND wm.member_id = current_setting('vyapar.authz_context', true)
      AND wm.state = 'active'
  );
$$;

CREATE TABLE IF NOT EXISTS vyapar_commercial.impressions (  -- [FR32]
  id          bigserial PRIMARY KEY,
  target_kind text NOT NULL,
  target_id   uuid NOT NULL,
  member_id   text,
  surface     text NOT NULL,
  sponsored   boolean NOT NULL DEFAULT false,
  kind        text NOT NULL CHECK (kind IN ('impression','view','save','enquiry','outcome')),
  at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS impressions_target_idx ON vyapar_commercial.impressions (target_kind, target_id, at);

-- [TR032] the app has already verified target ownership via Listings/
-- Opportunities' own interface BEFORE calling this — this function itself
-- performs no cross-schema ownership check (that would violate §4); it only
-- returns the aggregate the already-authorized caller asked for.
CREATE OR REPLACE FUNCTION vyapar_commercial.impressions_report(p_target_kind text, p_target_id uuid)
RETURNS TABLE(day date, sponsored boolean, kind text, n bigint)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_commercial, pg_temp
AS $$
  SELECT date_trunc('day', at)::date, sponsored, kind, count(*)
  FROM vyapar_commercial.impressions
  WHERE target_kind = p_target_kind AND target_id = p_target_id
  GROUP BY 1,2,3;
$$;

CREATE TABLE IF NOT EXISTS vyapar_commercial.outbox_event (  -- [TR030]
  id           bigserial PRIMARY KEY,
  event_type   text NOT NULL,
  payload      jsonb NOT NULL,
  published_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE vyapar_commercial.campaigns ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS campaigns_owner_or_workspace ON vyapar_commercial.campaigns;
CREATE POLICY campaigns_owner_or_workspace ON vyapar_commercial.campaigns
  USING (owner_id = current_setting('vyapar.authz_context', true) OR vyapar_commercial.is_workspace_collaborator(listing_id) OR vyapar_identity.is_operator('commercial'))
  WITH CHECK (owner_id = current_setting('vyapar.authz_context', true) OR vyapar_commercial.is_workspace_collaborator(listing_id));

ALTER TABLE vyapar_commercial.promotions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS promotions_owner_or_workspace ON vyapar_commercial.promotions;
CREATE POLICY promotions_owner_or_workspace ON vyapar_commercial.promotions
  USING (owner_id = current_setting('vyapar.authz_context', true)
    OR (target_kind = 'listing' AND vyapar_commercial.is_workspace_collaborator(target_id::text))
    OR vyapar_identity.is_operator('commercial'))
  WITH CHECK (owner_id = current_setting('vyapar.authz_context', true) OR (target_kind = 'listing' AND vyapar_commercial.is_workspace_collaborator(target_id::text)));

ALTER TABLE vyapar_commercial.commercial_order_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS order_history_visible_to_owner ON vyapar_commercial.commercial_order_history;
CREATE POLICY order_history_visible_to_owner ON vyapar_commercial.commercial_order_history
  USING (vyapar_identity.is_operator('commercial')
    OR (order_kind = 'promotion' AND EXISTS (SELECT 1 FROM vyapar_commercial.promotions p WHERE p.id = commercial_order_history.order_id AND p.owner_id = current_setting('vyapar.authz_context', true)))
    OR (order_kind = 'entitlement' AND EXISTS (SELECT 1 FROM vyapar_commercial.entitlements e WHERE e.id = commercial_order_history.order_id AND e.owner_id = current_setting('vyapar.authz_context', true))));

ALTER TABLE vyapar_commercial.entitlements ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS entitlements_owner_or_workspace ON vyapar_commercial.entitlements;
CREATE POLICY entitlements_owner_or_workspace ON vyapar_commercial.entitlements
  USING (owner_id = current_setting('vyapar.authz_context', true) OR vyapar_commercial.is_workspace_collaborator(listing_id) OR vyapar_identity.is_operator('commercial'))
  WITH CHECK (owner_id = current_setting('vyapar.authz_context', true));

ALTER TABLE vyapar_commercial.workspace_members ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS workspace_members_visible ON vyapar_commercial.workspace_members;
CREATE POLICY workspace_members_visible ON vyapar_commercial.workspace_members
  USING (invited_by = current_setting('vyapar.authz_context', true) OR member_id = current_setting('vyapar.authz_context', true)
    OR vyapar_commercial.is_workspace_collaborator(listing_id) OR vyapar_identity.is_operator('commercial'));

ALTER TABLE vyapar_commercial.impressions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS impressions_insert_any ON vyapar_commercial.impressions;
CREATE POLICY impressions_insert_any ON vyapar_commercial.impressions FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS impressions_select_operator_only ON vyapar_commercial.impressions;
CREATE POLICY impressions_select_operator_only ON vyapar_commercial.impressions FOR SELECT
  USING (vyapar_identity.is_operator('commercial') OR vyapar_identity.is_operator('analytics'));
-- Owner-facing reporting reads via impressions_report() (SECURITY DEFINER)
-- after the app has verified target ownership through Listings/Opportunities'
-- own interface — never a direct table SELECT from a non-operator caller.

ALTER TABLE vyapar_commercial.outbox_event ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outbox_insert_any ON vyapar_commercial.outbox_event;
CREATE POLICY outbox_insert_any ON vyapar_commercial.outbox_event FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS outbox_select_dispatcher ON vyapar_commercial.outbox_event;
CREATE POLICY outbox_select_dispatcher ON vyapar_commercial.outbox_event FOR SELECT
  USING (current_setting('vyapar.service_role', true) = 'dispatcher');

GRANT USAGE ON SCHEMA vyapar_commercial TO vyapar_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapar_commercial TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.is_workspace_collaborator(text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.impressions_report(text, uuid) TO vyapar_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vyapar_commercial TO vyapar_app;

-- =============================================================================
-- 7. vyapar_payments — Payment Bridge [FR51] — the CCR13 swap seam, isolated
-- on purpose from Commercial's own business rules.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_payments AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_payments.payment_orders (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind                text NOT NULL CHECK (kind IN ('promotion','entitlement','campaign')),
  ref_id              uuid NOT NULL,                          -- no cross-schema FK
  member_id           text NOT NULL,
  amount_paise        bigint NOT NULL,
  tax_paise           bigint NOT NULL,
  currency            text NOT NULL DEFAULT 'INR',
  gateway             text NOT NULL,
  gateway_order_ref   text,
  gateway_payment_ref text,
  idempotency_key     text NOT NULL UNIQUE,                   -- [TR051] DB-enforced, not app-logic-only
  state               text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','succeeded','failed','refunded')),
  refund_paise        bigint NOT NULL DEFAULT 0,
  refund_ref          text,
  webhook_events      jsonb NOT NULL DEFAULT '[]',             -- [TR051] dedup by event id, reconciles out-of-order events
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS payment_orders_member_idx ON vyapar_payments.payment_orders (member_id);
COMMENT ON TABLE vyapar_payments.payment_orders IS '[TR051] No field on this table is capable of holding raw card/bank credentials by construction — hosted/tokenized checkout only.';

ALTER TABLE vyapar_payments.payment_orders ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS payment_orders_owner_or_operator ON vyapar_payments.payment_orders;
CREATE POLICY payment_orders_owner_or_operator ON vyapar_payments.payment_orders
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('commercial'));

GRANT USAGE ON SCHEMA vyapar_payments TO vyapar_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA vyapar_payments TO vyapar_app;

-- =============================================================================
-- 8. vyapar_privacy — Privacy & Consent [FR36-FR38, FR53]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_privacy AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_privacy.privacy_settings (
  member_id             text PRIMARY KEY,
  capability_visible    boolean NOT NULL DEFAULT true,
  seeking_visible       boolean NOT NULL DEFAULT false,
  contact_disclosure    text NOT NULL DEFAULT 'after_accept' CHECK (contact_disclosure IN ('public','after_accept','hidden')),
  discoverable          boolean NOT NULL DEFAULT true,
  notifications_enabled boolean NOT NULL DEFAULT true,
  commercial_comms      boolean NOT NULL DEFAULT false,
  behavioral_analytics  boolean NOT NULL DEFAULT true,
  digest_enabled        boolean NOT NULL DEFAULT true,
  digest_hour           smallint NOT NULL DEFAULT 19,
  muted_types           text[] NOT NULL DEFAULT '{}',
  prompted              text[] NOT NULL DEFAULT '{}',
  updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vyapar_privacy.legal_documents (  -- [FR53]
  id           serial PRIMARY KEY,
  kind         text NOT NULL CHECK (kind IN ('privacy','terms')),
  version      int NOT NULL,
  language     text NOT NULL CHECK (language IN ('en','hi','te')),
  title        text NOT NULL,
  body         text NOT NULL,
  published_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kind, version, language)
);

CREATE TABLE IF NOT EXISTS vyapar_privacy.acceptances (
  member_id   text NOT NULL,
  kind        text NOT NULL,
  version     int NOT NULL,
  accepted_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, kind, version)
);

-- [TR053] The gate every gated action (TR003 listing submit, TR022 enquiry
-- submit) calls BEFORE proceeding — enforced at the call site, never only a
-- client-side redirect.
CREATE OR REPLACE FUNCTION vyapar_privacy.has_accepted(p_member_id text, p_kind text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_privacy, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM vyapar_privacy.acceptances a
    JOIN vyapar_privacy.legal_documents d ON d.kind = a.kind AND d.version = a.version
    WHERE a.member_id = p_member_id AND a.kind = p_kind
      AND d.version = (SELECT max(version) FROM vyapar_privacy.legal_documents WHERE kind = p_kind)
  );
$$;

CREATE TABLE IF NOT EXISTS vyapar_privacy.data_requests (  -- [FR37]
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id           text NOT NULL,
  kind                text NOT NULL CHECK (kind IN ('export','delete','withdraw','correct')),
  state               text NOT NULL DEFAULT 'received' CHECK (state IN ('received','in_progress','ready','completed','failed','blocked')),
  detail              text,
  file_url            text,
  retained_categories text[] NOT NULL DEFAULT '{}',
  due_at              timestamptz,
  completed_at        timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE vyapar_privacy.data_requests IS '[TR037] kind=delete anonymizes vyapar_identity.members in place (see that table''s comment) — never a cascading hard delete. Deferred while a paid promotions/entitlements row is active (TR031).';

CREATE TABLE IF NOT EXISTS vyapar_privacy.derived_preferences (  -- [FR38]
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id   text NOT NULL,
  key         text NOT NULL,
  value       jsonb NOT NULL,
  evidence    text NOT NULL,
  source      text NOT NULL,
  state       text NOT NULL DEFAULT 'proposed' CHECK (state IN ('proposed','active','declined','removed')),
  proposed_at timestamptz NOT NULL DEFAULT now(),
  decided_at  timestamptz
);

ALTER TABLE vyapar_privacy.privacy_settings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS privacy_settings_self_only ON vyapar_privacy.privacy_settings;
CREATE POLICY privacy_settings_self_only ON vyapar_privacy.privacy_settings
  USING (member_id = current_setting('vyapar.authz_context', true));

ALTER TABLE vyapar_privacy.acceptances ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS acceptances_self_or_operator ON vyapar_privacy.acceptances;
CREATE POLICY acceptances_self_or_operator ON vyapar_privacy.acceptances
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL));

ALTER TABLE vyapar_privacy.data_requests ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS data_requests_self_or_operator ON vyapar_privacy.data_requests;
CREATE POLICY data_requests_self_or_operator ON vyapar_privacy.data_requests
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL));

ALTER TABLE vyapar_privacy.derived_preferences ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS derived_preferences_self_only ON vyapar_privacy.derived_preferences;
CREATE POLICY derived_preferences_self_only ON vyapar_privacy.derived_preferences
  USING (member_id = current_setting('vyapar.authz_context', true));

GRANT USAGE ON SCHEMA vyapar_privacy TO vyapar_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA vyapar_privacy TO vyapar_app;
GRANT SELECT ON vyapar_privacy.legal_documents TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_privacy.has_accepted(text, text) TO vyapar_app;

-- =============================================================================
-- 9. vyapar_trust_safety — Trust & Safety [FR39-FR41]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_trust_safety AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_trust_safety.moderation_cases (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  object_kind          text NOT NULL CHECK (object_kind IN ('listing','opportunity','enquiry','partnership','review')),
  object_id            uuid NOT NULL,                          -- no cross-schema FK (polymorphic)
  subject_member_id    text,
  source               text NOT NULL CHECK (source IN ('report','auto_flag','review_dispute')),
  severity             text NOT NULL DEFAULT 'medium' CHECK (severity IN ('low','medium','high','critical')),
  state                text NOT NULL DEFAULT 'open' CHECK (state IN ('open','in_review','actioned','dismissed','escalated')),
  reporter_count       int NOT NULL DEFAULT 0,
  primary_reason       text,
  distribution_limited boolean NOT NULL DEFAULT false,
  target_due_at        timestamptz NOT NULL,
  action               text CHECK (action IN ('limit','remove','restore','request_verification','suspend','dismiss')),
  action_duration_days int,
  reason_code          text,
  operator_id          text,
  decided_at           timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS moderation_cases_open_idx ON vyapar_trust_safety.moderation_cases (state, severity, target_due_at);
COMMENT ON TABLE vyapar_trust_safety.moderation_cases IS '[TR039/TR040] Operator-only visibility — neither the reporter nor the reported party (subject_member_id) sees this table directly, only their own vyapar_trust_safety.reports/appeals row.';

CREATE TABLE IF NOT EXISTS vyapar_trust_safety.reports (  -- [FR39]
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_id   text NOT NULL,
  case_id       uuid NOT NULL REFERENCES vyapar_trust_safety.moderation_cases(id) ON DELETE CASCADE,
  object_kind   text NOT NULL,
  object_id     uuid NOT NULL,
  reason        text NOT NULL CHECK (reason IN ('scam','fake','impersonation','harassment','discrimination','spam','stale','privacy','other')),
  evidence_text text CHECK (evidence_text IS NULL OR char_length(evidence_text) <= 1000),
  content_language text CHECK (content_language IN ('en','hi','te')),  -- [TR042 gap]
  evidence_urls text[] NOT NULL DEFAULT '{}' CHECK (cardinality(evidence_urls) <= 3),
  created_at    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE vyapar_trust_safety.reports IS '[TR039] reporter_id is never selected by any query surface exposed to the reported party — this table''s RLS admits only the reporter themselves or an operator, structurally.';

CREATE TABLE IF NOT EXISTS vyapar_trust_safety.appeals (  -- [FR41]
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id       uuid NOT NULL REFERENCES vyapar_trust_safety.moderation_cases(id) ON DELETE CASCADE,
  member_id     text NOT NULL,
  text          text NOT NULL CHECK (char_length(text) <= 1000),
  content_language text CHECK (content_language IN ('en','hi','te')),  -- [TR042 gap]
  evidence_urls text[] NOT NULL DEFAULT '{}',
  state         text NOT NULL DEFAULT 'open' CHECK (state IN ('open','upheld','overturned','delayed')),
  reviewer_id   text,
  reason_code   text,
  due_at        timestamptz NOT NULL DEFAULT now() + INTERVAL '7 days',
  decided_at    timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (case_id, member_id)
);

ALTER TABLE vyapar_trust_safety.moderation_cases ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS moderation_cases_operator_only ON vyapar_trust_safety.moderation_cases;
CREATE POLICY moderation_cases_operator_only ON vyapar_trust_safety.moderation_cases
  USING (vyapar_identity.is_operator('moderation'));

ALTER TABLE vyapar_trust_safety.reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reports_reporter_or_operator ON vyapar_trust_safety.reports;
CREATE POLICY reports_reporter_or_operator ON vyapar_trust_safety.reports
  USING (reporter_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('moderation'))
  WITH CHECK (reporter_id = current_setting('vyapar.authz_context', true));

ALTER TABLE vyapar_trust_safety.appeals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS appeals_self_or_operator ON vyapar_trust_safety.appeals;
CREATE POLICY appeals_self_or_operator ON vyapar_trust_safety.appeals
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('moderation'));

GRANT USAGE ON SCHEMA vyapar_trust_safety TO vyapar_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA vyapar_trust_safety TO vyapar_app;

-- =============================================================================
-- 10. vyapar_analytics — Analytics [FR45-FR46]
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_analytics AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_analytics.analytics_events (
  id            bigserial PRIMARY KEY,
  member_pseudo text,
  object_id     text,
  surface       text,
  event         text NOT NULL,
  level         text NOT NULL CHECK (level IN ('impression','view','action','attributed_outcome','confirmed_outcome','operational')),
  props         jsonb NOT NULL DEFAULT '{}',
  at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS analytics_events_at_idx ON vyapar_analytics.analytics_events (at);
COMMENT ON TABLE vyapar_analytics.analytics_events IS '[TR045] member_pseudo, never a raw member id. [TR046] every admin GROUP BY over this table suppresses groups < 10 at the query layer.';

ALTER TABLE vyapar_analytics.analytics_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS analytics_insert_any ON vyapar_analytics.analytics_events;
CREATE POLICY analytics_insert_any ON vyapar_analytics.analytics_events FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS analytics_select_operator_only ON vyapar_analytics.analytics_events;
CREATE POLICY analytics_select_operator_only ON vyapar_analytics.analytics_events FOR SELECT
  USING (vyapar_identity.is_operator('analytics'));

GRANT USAGE ON SCHEMA vyapar_analytics TO vyapar_app;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA vyapar_analytics TO vyapar_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vyapar_analytics TO vyapar_app;

-- =============================================================================
-- 11. vyapar_integration — Integration Bridges [FR52 + async side of many FRs]
-- Six thin sub-bridges (Search/Notification/Audit/Object Storage/Dashboard-
-- Read/Counsel-Referral), grouped per 07-tech-reqs.md because none owns
-- member-facing business logic. dead_letters/config/counsel_referrals are
-- the component's own named tables; notifications and audit_events are
-- explicit fold-ins (documented in 07a-er-model.md Assumptions, same style
-- as Mangaly's own Notification Bridge correction) because the Notification
-- and Audit sub-bridges each need a durable, pre-forward record.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_integration AUTHORIZATION vyapar_owner;

CREATE TABLE IF NOT EXISTS vyapar_integration.dead_letters (
  id         bigserial PRIMARY KEY,
  target     text NOT NULL,
  payload    jsonb NOT NULL,
  error      text,
  attempts   int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- [TR049] vyapar_app deliberately has NO write grant on this table at all —
-- reinforces, at the DB layer, TR049's "no route writes ranking config
-- weights" separation-of-powers rule; config changes are an owner/admin-
-- tooling operation, never a runtime app write.
CREATE TABLE IF NOT EXISTS vyapar_integration.config (
  key        text PRIMARY KEY,
  value      jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vyapar_integration.counsel_referrals (  -- [FR52(f)]
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id       text NOT NULL,
  enquiry_id      uuid,                                        -- no cross-schema FK
  problem_summary text NOT NULL,
  consent         boolean NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE vyapar_integration.counsel_referrals IS '[FR52(f)] Minimal-payload boundary (member_id, problem_summary, consent only). Self-only visibility — not even operators, per the minimal-payload intent.';

CREATE TABLE IF NOT EXISTS vyapar_integration.notifications (  -- [FR21, FR52(b)]
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id       text NOT NULL,
  kind            text NOT NULL,
  template_id     text NOT NULL,
  title           text NOT NULL,
  body            text,
  link            text,
  params          jsonb NOT NULL DEFAULT '{}',
  idempotency_key text UNIQUE,
  read_at         timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS notifications_member_idx ON vyapar_integration.notifications (member_id, created_at DESC);

CREATE TABLE IF NOT EXISTS vyapar_integration.audit_events (  -- [FR52(c)]
  id          bigserial PRIMARY KEY,
  actor_id    text,
  object_kind text NOT NULL,
  object_id   text NOT NULL,
  action      text NOT NULL,
  reason_code text,
  outcome     text NOT NULL DEFAULT 'ok',
  details     jsonb NOT NULL DEFAULT '{}',
  at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_events_idx ON vyapar_integration.audit_events (object_kind, object_id, at DESC);

ALTER TABLE vyapar_integration.dead_letters ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS dead_letters_operator_only ON vyapar_integration.dead_letters;
CREATE POLICY dead_letters_operator_only ON vyapar_integration.dead_letters
  USING (vyapar_identity.is_operator(NULL));

ALTER TABLE vyapar_integration.counsel_referrals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS counsel_referrals_self_only ON vyapar_integration.counsel_referrals;
CREATE POLICY counsel_referrals_self_only ON vyapar_integration.counsel_referrals
  USING (member_id = current_setting('vyapar.authz_context', true));

ALTER TABLE vyapar_integration.notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS notifications_self_or_operator ON vyapar_integration.notifications;
CREATE POLICY notifications_self_or_operator ON vyapar_integration.notifications
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL));

ALTER TABLE vyapar_integration.audit_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS audit_insert_any ON vyapar_integration.audit_events;
CREATE POLICY audit_insert_any ON vyapar_integration.audit_events FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS audit_select_operator_only ON vyapar_integration.audit_events;
CREATE POLICY audit_select_operator_only ON vyapar_integration.audit_events FOR SELECT
  USING (vyapar_identity.is_operator(NULL));

GRANT USAGE ON SCHEMA vyapar_integration TO vyapar_app;
GRANT SELECT, INSERT, UPDATE ON vyapar_integration.dead_letters, vyapar_integration.counsel_referrals, vyapar_integration.notifications, vyapar_integration.audit_events TO vyapar_app;
GRANT SELECT ON vyapar_integration.config TO vyapar_app;  -- no INSERT/UPDATE/DELETE — see table comment above
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vyapar_integration TO vyapar_app;

-- =============================================================================
-- 12. vyapar_platform — shared cross-cutting infrastructure
-- [MODULE-ARCHITECTURE-STANDARD §4b/§4c, Cross-cutting §1/§2 of 07-tech-reqs.md]
-- Not a business-logic component's schema — same infrastructure class as the
-- in-process event bus, given its own schema only because this state must
-- persist across restarts/instances.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS vyapar_platform AUTHORIZATION vyapar_owner;

-- [Cross-cutting §1 gap] shared idempotency-key store for TR022, TR025,
-- TR027, TR030/033/035, TR039 — rather than a one-off column per table (the
-- pattern payment_orders/notifications already use ad hoc, which is fine to
-- keep as-is for those two per 07-tech-reqs.md's own note).
CREATE TABLE IF NOT EXISTS vyapar_platform.idempotency_key (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  idempotency_key   text NOT NULL,
  endpoint          text NOT NULL,
  member_id         text NOT NULL,
  request_hash      text NOT NULL,
  status_code       int,
  response_snapshot jsonb,
  created_at        timestamptz NOT NULL DEFAULT now(),
  expires_at        timestamptz NOT NULL DEFAULT (now() + interval '7 days'),
  -- Account-scoped, NOT global: the key is client-generated, so a global
  -- (key, endpoint) namespace would let one member's colliding/replayed key
  -- return another member's cached response_snapshot (same reasoning as
  -- Mangaly's SP102).
  CONSTRAINT idempotency_key_member_scope UNIQUE (member_id, idempotency_key, endpoint)
);
CREATE INDEX IF NOT EXISTS idx_idempotency_expiry ON vyapar_platform.idempotency_key (expires_at);

ALTER TABLE vyapar_platform.idempotency_key ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS idempotency_key_self ON vyapar_platform.idempotency_key;
CREATE POLICY idempotency_key_self ON vyapar_platform.idempotency_key
  USING (member_id = current_setting('vyapar.authz_context', true))
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true));

-- [Cross-cutting §2 gap] one shared, DB-backed rolling-window counter — used
-- by TR021 (notification fatigue cap), TR022 (enquiries/day), TR039 (reports/day).
-- The 10-pending-partnership-request cap (TR025) correctly stays a plain
-- COUNT(*) query against vyapar_enquiries.partnership_requests — a cap on
-- concurrently-open records is the wrong shape for a rolling window.
CREATE TABLE IF NOT EXISTS vyapar_platform.rate_limit_counter (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rate_limit_key  text NOT NULL,        -- e.g. 'enquiry:{sender_id}:day', 'report:{reporter_id}:day', 'notify:{member_id}:day'
  window_start    timestamptz NOT NULL,
  window_seconds  int NOT NULL,
  hit_count       int NOT NULL DEFAULT 1,
  limit_max       int NOT NULL,
  UNIQUE (rate_limit_key, window_start)
);
CREATE INDEX IF NOT EXISTS idx_rate_limit_key ON vyapar_platform.rate_limit_counter (rate_limit_key);

-- [Cross-cutting §2(a)] "one check_and_increment(key, window_seconds, limit)
-- function every rate-limited endpoint calls" — named literally in
-- 07-tech-reqs.md; this is that function. Returns true if the call is
-- allowed (and increments), false if the limit is already reached.
CREATE OR REPLACE FUNCTION vyapar_platform.check_and_increment(p_key text, p_window_seconds int, p_limit int)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
  v_window_start timestamptz := to_timestamp(floor(extract(epoch FROM now()) / p_window_seconds) * p_window_seconds);
  v_count int;
BEGIN
  INSERT INTO vyapar_platform.rate_limit_counter (rate_limit_key, window_start, window_seconds, hit_count, limit_max)
  VALUES (p_key, v_window_start, p_window_seconds, 1, p_limit)
  ON CONFLICT (rate_limit_key, window_start) DO UPDATE SET hit_count = vyapar_platform.rate_limit_counter.hit_count + 1
  RETURNING hit_count INTO v_count;
  RETURN v_count <= p_limit;
END;
$$;

-- [Cross-cutting] shared Haversine distance helper (FR15 radius filter, FR19
-- location fit) — pure infrastructure, not owned by one business component.
CREATE OR REPLACE FUNCTION vyapar_platform.distance_km(lat1 double precision, lng1 double precision, lat2 double precision, lng2 double precision)
RETURNS double precision AS $$
  SELECT CASE WHEN lat1 IS NULL OR lng1 IS NULL OR lat2 IS NULL OR lng2 IS NULL THEN NULL ELSE
    2 * 6371 * asin(sqrt(
      power(sin(radians(lat2 - lat1) / 2), 2) +
      cos(radians(lat1)) * cos(radians(lat2)) * power(sin(radians(lng2 - lng1) / 2), 2)))
  END
$$ LANGUAGE sql IMMUTABLE;

GRANT USAGE ON SCHEMA vyapar_platform TO vyapar_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapar_platform TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_platform.check_and_increment(text, int, int) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_platform.distance_km(double precision, double precision, double precision, double precision) TO vyapar_app;
