-- =============================================================================
-- MOD01 Vyapar — database schema (Postgres 18, database "vyapar", schema "vyapar")
--
-- [FR50] Identity is owned by the parent ForKhatri platform. `members` here is a
-- thin identity-bridge mirror keyed by the platform member id — never a login table.
-- Approach: one schema, plain SQL, idempotent reset for development; every table
-- that changes state has created_at/updated_at and every state machine is a CHECK.
-- Traces to: FR01-FR55 (table comments name the FR that owns each table)
-- =============================================================================
DROP SCHEMA IF EXISTS vyapar CASCADE;
CREATE SCHEMA vyapar;
SET search_path TO vyapar, public;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- Identity bridge (FR50) — member id is the ONLY identity key stored.
-- ---------------------------------------------------------------------------
CREATE TABLE members (
  id                TEXT PRIMARY KEY,                 -- platform member id (opaque)
  display_name      TEXT NOT NULL,
  phone             TEXT,
  trust_level       SMALLINT NOT NULL DEFAULT 1,      -- platform Level 1/2 (read-only mirror)
  language          TEXT NOT NULL DEFAULT 'en' CHECK (language IN ('en','hi','te')),
  locality          TEXT,
  lat               DOUBLE PRECISION,
  lng               DOUBLE PRECISION,
  radius_km         SMALLINT NOT NULL DEFAULT 10,
  work_mode         TEXT CHECK (work_mode IN ('on_site','remote','both')),
  help_with         TEXT[] NOT NULL DEFAULT '{}',     -- FR44 "what do you want help with"
  capabilities      TEXT[] NOT NULL DEFAULT '{}',     -- FR44 captured capabilities (member-level)
  is_operator       BOOLEAN NOT NULL DEFAULT FALSE,
  operator_permissions TEXT[] NOT NULL DEFAULT '{}',  -- verification|content|commercial|analytics|moderation
  first_run_done    BOOLEAN NOT NULL DEFAULT FALSE,
  first_run_step    SMALLINT NOT NULL DEFAULT 0,      -- FR44 abandonment point
  avatar_url        TEXT,
  synced_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Taxonomy (FR01, FR04, FR48)
-- ---------------------------------------------------------------------------
CREATE TABLE taxonomy_terms (
  id          SERIAL PRIMARY KEY,
  kind        TEXT NOT NULL CHECK (kind IN ('category','capability')),
  slug        TEXT NOT NULL,
  name_en     TEXT NOT NULL,
  name_hi     TEXT,
  name_te     TEXT,
  icon        TEXT,
  parent_id   INT REFERENCES taxonomy_terms(id),
  aliases     TEXT[] NOT NULL DEFAULT '{}',
  status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','unmapped','merged')),
  merged_into INT REFERENCES taxonomy_terms(id),
  version     INT NOT NULL DEFAULT 1,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kind, slug)
);

-- ---------------------------------------------------------------------------
-- Listings = BusinessProfile | ProfessionalListingProfile (FR01-FR07, FR10)
-- ---------------------------------------------------------------------------
CREATE TABLE listings (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id              TEXT NOT NULL REFERENCES members(id),
  kind                  TEXT NOT NULL CHECK (kind IN ('business','professional')),
  name                  TEXT NOT NULL,
  headline              TEXT,
  description           TEXT,
  categories            TEXT[] NOT NULL DEFAULT '{}',   -- taxonomy slugs
  capabilities          TEXT[] NOT NULL DEFAULT '{}',   -- taxonomy slugs
  unmapped_labels       TEXT[] NOT NULL DEFAULT '{}',   -- FR04 free-text escape hatch
  services              JSONB NOT NULL DEFAULT '[]',    -- [{name, price_hint}]
  locality              TEXT NOT NULL,
  lat                   DOUBLE PRECISION,
  lng                   DOUBLE PRECISION,
  service_radius_km     SMALLINT NOT NULL DEFAULT 10,
  service_mode          TEXT NOT NULL DEFAULT 'both' CHECK (service_mode IN ('on_site','remote','both')),
  enquiry_pref          TEXT NOT NULL DEFAULT 'enabled' CHECK (enquiry_pref IN ('enabled','disabled')),
  enquiry_disabled_reason TEXT,
  opportunity_participation BOOLEAN NOT NULL DEFAULT TRUE,
  discoverable          BOOLEAN NOT NULL DEFAULT TRUE,  -- FR02
  partnership_open      BOOLEAN NOT NULL DEFAULT TRUE,  -- FR25 opt-out
  primary_phone         TEXT,
  contact_verified      BOOLEAN NOT NULL DEFAULT FALSE, -- FR07
  experience_years      SMALLINT,
  languages             TEXT[] NOT NULL DEFAULT '{}',
  availability          TEXT CHECK (availability IN ('now','this_week','later')),
  evidence_links        TEXT[] NOT NULL DEFAULT '{}',
  rates                 TEXT,
  intent_state          TEXT CHECK (intent_state IN ('looking','open','curious','not_interested')), -- FR05
  intent_visible        BOOLEAN NOT NULL DEFAULT FALSE,  -- FR05 private by default
  capability_visible    BOOLEAN NOT NULL DEFAULT TRUE,   -- FR05 independent control
  state                 TEXT NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','submitted','active_unverified','active_verified','suspended','archived')),
  state_reason          TEXT,
  verification_state    TEXT NOT NULL DEFAULT 'not_started' CHECK (verification_state IN ('not_started','pending','verified','expiring','expired','rejected','revoked','disputed')),
  verification_document TEXT,                               -- gst|udyam|pan|shops_est|credential
  verification_claim    TEXT,                               -- e.g. credential name
  verified_at           TIMESTAMPTZ,
  verification_expires_at TIMESTAMPTZ,
  credential_ref        JSONB,                              -- FR06 {id, claim, issuer, verified_at, last_checked}
  image_url             TEXT,
  cover_url             TEXT,
  response_minutes      INT,                                -- FR28 "Responds in ~X"
  last_confirmed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at          TIMESTAMPTZ,
  search_tsv            TSVECTOR,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (owner_id, name, locality)                         -- FR01 duplicate rule
);
CREATE INDEX listings_search_idx ON listings USING GIN (search_tsv);
CREATE INDEX listings_state_idx ON listings (state, discoverable);

CREATE TABLE listing_contacts (                            -- FR02
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id  UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  channel     TEXT NOT NULL CHECK (channel IN ('phone','whatsapp','email','website','address')),
  value       TEXT NOT NULL,
  disclosure  TEXT NOT NULL DEFAULT 'after_accept' CHECK (disclosure IN ('public','after_accept','hidden'))
);

CREATE TABLE otp_challenges (                              -- FR07 (listing contact verification, NOT login)
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id    TEXT NOT NULL REFERENCES members(id),
  listing_id   UUID REFERENCES listings(id) ON DELETE CASCADE,
  phone        TEXT NOT NULL,
  code         TEXT NOT NULL,
  attempts     SMALLINT NOT NULL DEFAULT 0,
  expires_at   TIMESTAMPTZ NOT NULL,
  resend_after TIMESTAMPTZ NOT NULL,
  locked_until TIMESTAMPTZ,
  verified_at  TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE verification_records (                        -- FR08, FR09, FR47
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id         UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  member_id          TEXT NOT NULL REFERENCES members(id),
  kind               TEXT NOT NULL CHECK (kind IN ('business','credential')),
  document_type      TEXT NOT NULL CHECK (document_type IN ('gst','udyam','pan','shops_est','credential')),
  identifier_masked  TEXT,
  identifier_enc     TEXT,                                 -- encrypted at rest (dev: base64 marker)
  image_url          TEXT,
  credential_name    TEXT,
  issuer             TEXT,
  state              TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','verified','rejected','needs_clearer_copy','revoked','expired')),
  reason_code        TEXT,
  verifier_id        TEXT REFERENCES members(id),
  decided_at         TIMESTAMPTZ,
  expires_at         TIMESTAMPTZ,
  image_delete_after TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Opportunities (FR11-FR14, FR55)
-- ---------------------------------------------------------------------------
CREATE TABLE opportunities (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  poster_id             TEXT NOT NULL REFERENCES members(id),
  listing_id            UUID REFERENCES listings(id),
  title                 TEXT NOT NULL,
  type                  TEXT NOT NULL CHECK (type IN ('employment','freelance','local_service','partnership','training','community')),
  description           TEXT,
  requirements          TEXT,
  compensation          TEXT,
  value_amount          NUMERIC,
  location              TEXT,
  lat                   DOUBLE PRECISION,
  lng                   DOUBLE PRECISION,
  work_mode             TEXT CHECK (work_mode IN ('on_site','remote','both')),
  timing                TEXT,
  eligibility           JSONB NOT NULL DEFAULT '{}',        -- {min_experience_years, languages, ...}
  required_capabilities TEXT[] NOT NULL DEFAULT '{}',
  response_method       TEXT CHECK (response_method IN ('in_app','external')),
  deadline              TIMESTAMPTZ,
  source_segment        TEXT NOT NULL CHECK (source_segment IN ('community','public')),
  source_name           TEXT,
  source_url            TEXT,
  source_unreachable    BOOLEAN NOT NULL DEFAULT FALSE,
  entry_mode            TEXT NOT NULL DEFAULT 'create' CHECK (entry_mode IN ('create','share','upload')),
  raw_input             TEXT,
  raw_image_url         TEXT,
  unconfirmed_fields    TEXT[] NOT NULL DEFAULT '{}',        -- FR12
  confirmed_fields      TEXT[] NOT NULL DEFAULT '{}',
  state                 TEXT NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','pending_review','active','paused','stale','expired','closed','removed')),
  state_reason          TEXT,
  distribution_limited  BOOLEAN NOT NULL DEFAULT FALSE,      -- FR40 auto-limit
  image_url             TEXT,
  last_confirmed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  reminder_sent_at      TIMESTAMPTZ,
  published_at          TIMESTAMPTZ,
  search_tsv            TSVECTOR,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX opportunities_search_idx ON opportunities USING GIN (search_tsv);
CREATE INDEX opportunities_state_idx ON opportunities (state, source_segment);

CREATE TABLE member_opportunity (                          -- FR55 Saved / viewed / hidden / shared / completed
  member_id       TEXT NOT NULL REFERENCES members(id),
  opportunity_id  UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  saved_at        TIMESTAMPTZ,
  viewed_at       TIMESTAMPTZ,
  hidden_at       TIMESTAMPTZ,
  hidden_reason   TEXT CHECK (hidden_reason IN ('too_far','wrong_type','not_my_capability','value_too_low','wrong_timing','already_found','not_interested')),
  shared_at       TIMESTAMPTZ,
  external_opened_at TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  PRIMARY KEY (member_id, opportunity_id)
);

CREATE TABLE member_listing (                              -- FR16 Save on listings
  member_id   TEXT NOT NULL REFERENCES members(id),
  listing_id  UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  saved_at    TIMESTAMPTZ,
  viewed_at   TIMESTAMPTZ,
  PRIMARY KEY (member_id, listing_id)
);

-- ---------------------------------------------------------------------------
-- Enquiries and threads (FR22-FR24)
-- ---------------------------------------------------------------------------
CREATE TABLE enquiries (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id          TEXT NOT NULL REFERENCES members(id),
  provider_id        TEXT NOT NULL REFERENCES members(id),
  listing_id         UUID REFERENCES listings(id),
  opportunity_id     UUID REFERENCES opportunities(id),
  action_type        TEXT NOT NULL CHECK (action_type IN ('enquire','apply','propose','contact','register')),
  sub_choice         TEXT,                                  -- ask_question | request_quote
  state              TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','awaiting_response','in_progress','resolved','closed','withdrawn','restricted')),
  delivered          BOOLEAN NOT NULL DEFAULT TRUE,        -- FALSE when silently undelivered (blocked)
  safety_notice_seen BOOLEAN NOT NULL DEFAULT FALSE,
  first_reply_at     TIMESTAMPTZ,
  last_activity_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (listing_id IS NOT NULL OR opportunity_id IS NOT NULL)
);
CREATE INDEX enquiries_sender_idx ON enquiries (sender_id, state);
CREATE INDEX enquiries_provider_idx ON enquiries (provider_id, state);

CREATE TABLE enquiry_messages (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  enquiry_id     UUID NOT NULL REFERENCES enquiries(id) ON DELETE CASCADE,
  sender_id      TEXT NOT NULL REFERENCES members(id),
  body           TEXT NOT NULL CHECK (char_length(body) BETWEEN 1 AND 1000),
  attachment_url TEXT,
  system_note    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE blocks (                                      -- FR24, FR39
  blocker_id  TEXT NOT NULL REFERENCES members(id),
  blocked_id  TEXT NOT NULL REFERENCES members(id),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (blocker_id, blocked_id)
);

-- ---------------------------------------------------------------------------
-- Partnership requests (FR25, FR26)
-- ---------------------------------------------------------------------------
CREATE TABLE partnership_requests (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id            TEXT NOT NULL REFERENCES members(id),
  recipient_id         TEXT NOT NULL REFERENCES members(id),
  sender_listing_id    UUID NOT NULL REFERENCES listings(id),
  recipient_listing_id UUID NOT NULL REFERENCES listings(id),
  need                 TEXT NOT NULL,
  offer                TEXT NOT NULL,
  expectations         TEXT NOT NULL,
  category             TEXT NOT NULL,
  locality             TEXT NOT NULL,
  timing               TEXT NOT NULL,
  next_step            TEXT NOT NULL,
  state                TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('draft','pending','accepted','declined','withdrawn','restricted','closed')),
  decided_at           TIMESTAMPTZ,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Reviews (FR27-FR29)
-- ---------------------------------------------------------------------------
CREATE TABLE review_invites (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  interaction_kind  TEXT NOT NULL CHECK (interaction_kind IN ('enquiry','partnership')),
  interaction_id    UUID NOT NULL,
  member_id         TEXT NOT NULL REFERENCES members(id),
  subject_listing_id UUID REFERENCES listings(id),
  subject_member_id TEXT NOT NULL REFERENCES members(id),
  expires_at        TIMESTAMPTZ NOT NULL,
  used_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (interaction_kind, interaction_id, member_id)
);

CREATE TABLE reviews (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  interaction_kind   TEXT NOT NULL CHECK (interaction_kind IN ('enquiry','partnership')),
  interaction_id     UUID NOT NULL,
  author_id          TEXT NOT NULL REFERENCES members(id),
  subject_listing_id UUID REFERENCES listings(id),
  subject_member_id  TEXT NOT NULL REFERENCES members(id),
  recommend          BOOLEAN NOT NULL,
  tags               TEXT[] NOT NULL DEFAULT '{}' CHECK (cardinality(tags) <= 3),
  comment            TEXT CHECK (comment IS NULL OR char_length(comment) BETWEEN 20 AND 500),
  state              TEXT NOT NULL DEFAULT 'published' CHECK (state IN ('published','disputed','hidden','removed')),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (interaction_kind, interaction_id, author_id)
);

CREATE TABLE review_disputes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  review_id   UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  disputer_id TEXT NOT NULL REFERENCES members(id),
  reason      TEXT NOT NULL CHECK (reason IN ('retaliation','manipulation','not_the_interaction','abusive')),
  outcome     TEXT CHECK (outcome IN ('published','hidden','removed')),
  case_id     UUID,
  decided_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (review_id)
);

-- ---------------------------------------------------------------------------
-- Commercial (FR30-FR35, FR49, FR51, FR54)
-- ---------------------------------------------------------------------------
CREATE TABLE products (
  id             TEXT NOT NULL,
  version        INT NOT NULL DEFAULT 1,
  kind           TEXT NOT NULL CHECK (kind IN ('boost','workspace','campaign')),
  name           TEXT NOT NULL,
  description    TEXT,
  duration_days  INT,
  billing        TEXT NOT NULL CHECK (billing IN ('one_time','monthly','annual')),
  price_paise    BIGINT NOT NULL,
  tax_rate_bp    INT NOT NULL DEFAULT 1800,      -- basis points: 18% GST
  capabilities   TEXT[] NOT NULL DEFAULT '{}',
  active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (id, version)
);

CREATE TABLE payment_orders (                              -- FR51
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind                TEXT NOT NULL CHECK (kind IN ('promotion','entitlement','campaign')),
  ref_id              UUID NOT NULL,
  member_id           TEXT NOT NULL REFERENCES members(id),
  amount_paise        BIGINT NOT NULL,
  tax_paise           BIGINT NOT NULL,
  currency            TEXT NOT NULL DEFAULT 'INR',
  gateway             TEXT NOT NULL,
  gateway_order_ref   TEXT,
  gateway_payment_ref TEXT,
  idempotency_key     TEXT NOT NULL UNIQUE,
  state               TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','succeeded','failed','refunded')),
  refund_paise        BIGINT NOT NULL DEFAULT 0,
  refund_ref          TEXT,
  webhook_events      JSONB NOT NULL DEFAULT '[]',
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE promotions (                                  -- FR30, FR31
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id         TEXT NOT NULL REFERENCES members(id),
  target_kind      TEXT NOT NULL CHECK (target_kind IN ('listing','opportunity')),
  target_id        UUID NOT NULL,
  product_id       TEXT NOT NULL,
  product_version  INT NOT NULL,
  price_paise      BIGINT NOT NULL,
  tax_paise        BIGINT NOT NULL,
  audience         JSONB NOT NULL DEFAULT '{}',            -- {locality, category}
  state            TEXT NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','awaiting_payment','scheduled','active','paused','completed','cancelled','rejected','refunded')),
  starts_at        TIMESTAMPTZ,
  ends_at          TIMESTAMPTZ,
  paused_at        TIMESTAMPTZ,
  credit_paise     BIGINT NOT NULL DEFAULT 0,
  campaign_id      UUID,
  payment_order_id UUID REFERENCES payment_orders(id),
  reject_reason    TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (product_id, product_version) REFERENCES products(id, version)
);

CREATE TABLE promotion_history (
  id           BIGSERIAL PRIMARY KEY,
  promotion_id UUID NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
  from_state   TEXT,
  to_state     TEXT NOT NULL,
  reason       TEXT,
  at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE entitlements (                                -- FR33
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id           UUID NOT NULL REFERENCES listings(id),
  owner_id             TEXT NOT NULL REFERENCES members(id),
  product_id           TEXT NOT NULL,
  product_version      INT NOT NULL,
  price_paise          BIGINT NOT NULL,
  tax_paise            BIGINT NOT NULL,
  state                TEXT NOT NULL DEFAULT 'awaiting_payment' CHECK (state IN ('awaiting_payment','active','paused','cancelled','completed','refunded')),
  starts_at            TIMESTAMPTZ,
  renews_at            TIMESTAMPTZ,
  grace_until          TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  renewal_reminder_at  TIMESTAMPTZ,
  payment_order_id     UUID REFERENCES payment_orders(id),
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (product_id, product_version) REFERENCES products(id, version)
);

CREATE TABLE workspace_members (                           -- FR34
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id  UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  member_id   TEXT REFERENCES members(id),
  phone       TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('admin','operator')),
  state       TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','active','revoked','expired')),
  invited_by  TEXT NOT NULL REFERENCES members(id),
  invited_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  accepted_at TIMESTAMPTZ,
  revoked_at  TIMESTAMPTZ,
  expires_at  TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '30 days'
);

CREATE TABLE campaigns (                                   -- FR35
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id       UUID NOT NULL REFERENCES listings(id),
  owner_id         TEXT NOT NULL REFERENCES members(id),
  name             TEXT NOT NULL,
  product_id       TEXT NOT NULL,
  product_version  INT NOT NULL,
  budget_paise     BIGINT NOT NULL,
  tax_paise        BIGINT NOT NULL,
  starts_at        TIMESTAMPTZ NOT NULL,
  ends_at          TIMESTAMPTZ NOT NULL,
  audience         JSONB NOT NULL DEFAULT '{}',
  item_refs        JSONB NOT NULL DEFAULT '[]',            -- [{kind,id}] up to 10
  state            TEXT NOT NULL DEFAULT 'awaiting_payment' CHECK (state IN ('draft','awaiting_payment','active','completed','cancelled','refunded')),
  payment_order_id UUID REFERENCES payment_orders(id),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (product_id, product_version) REFERENCES products(id, version)
);

CREATE TABLE impressions (                                 -- FR32 counts (kept separate from analytics)
  id          BIGSERIAL PRIMARY KEY,
  target_kind TEXT NOT NULL,
  target_id   UUID NOT NULL,
  member_id   TEXT,
  surface     TEXT NOT NULL,
  sponsored   BOOLEAN NOT NULL DEFAULT FALSE,
  kind        TEXT NOT NULL CHECK (kind IN ('impression','view','save','enquiry','outcome')),
  at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX impressions_target_idx ON impressions (target_kind, target_id, at);

-- ---------------------------------------------------------------------------
-- Privacy, consent, data rights (FR36-FR38, FR53)
-- ---------------------------------------------------------------------------
CREATE TABLE privacy_settings (
  member_id             TEXT PRIMARY KEY REFERENCES members(id),
  capability_visible    BOOLEAN NOT NULL DEFAULT TRUE,
  seeking_visible       BOOLEAN NOT NULL DEFAULT FALSE,
  contact_disclosure    TEXT NOT NULL DEFAULT 'after_accept' CHECK (contact_disclosure IN ('public','after_accept','hidden')),
  discoverable          BOOLEAN NOT NULL DEFAULT TRUE,
  notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  commercial_comms      BOOLEAN NOT NULL DEFAULT FALSE,
  behavioral_analytics  BOOLEAN NOT NULL DEFAULT TRUE,
  digest_enabled        BOOLEAN NOT NULL DEFAULT TRUE,
  digest_hour           SMALLINT NOT NULL DEFAULT 19,
  muted_types           TEXT[] NOT NULL DEFAULT '{}',
  prompted              TEXT[] NOT NULL DEFAULT '{}',      -- which contextual prompts were shown
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE legal_documents (                             -- FR53
  id           SERIAL PRIMARY KEY,
  kind         TEXT NOT NULL CHECK (kind IN ('privacy','terms')),
  version      INT NOT NULL,
  language     TEXT NOT NULL CHECK (language IN ('en','hi','te')),
  title        TEXT NOT NULL,
  body         TEXT NOT NULL,
  published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kind, version, language)
);

CREATE TABLE acceptances (
  member_id   TEXT NOT NULL REFERENCES members(id),
  kind        TEXT NOT NULL,
  version     INT NOT NULL,
  accepted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, kind, version)
);

CREATE TABLE data_requests (                               -- FR37
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id           TEXT NOT NULL REFERENCES members(id),
  kind                TEXT NOT NULL CHECK (kind IN ('export','delete','withdraw','correct')),
  state               TEXT NOT NULL DEFAULT 'received' CHECK (state IN ('received','in_progress','ready','completed','failed','blocked')),
  detail              TEXT,
  file_url            TEXT,
  retained_categories TEXT[] NOT NULL DEFAULT '{}',
  due_at              TIMESTAMPTZ,
  completed_at        TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE derived_preferences (                         -- FR38
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id   TEXT NOT NULL REFERENCES members(id),
  key         TEXT NOT NULL,                               -- e.g. max_distance_km, exclude_type
  value       JSONB NOT NULL,
  evidence    TEXT NOT NULL,
  source      TEXT NOT NULL,
  state       TEXT NOT NULL DEFAULT 'proposed' CHECK (state IN ('proposed','active','declined','removed')),
  proposed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at  TIMESTAMPTZ
);

-- ---------------------------------------------------------------------------
-- Trust & safety (FR39-FR41, FR40 queue)
-- ---------------------------------------------------------------------------
CREATE TABLE moderation_cases (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  object_kind          TEXT NOT NULL CHECK (object_kind IN ('listing','opportunity','enquiry','partnership','review')),
  object_id            UUID NOT NULL,
  subject_member_id    TEXT REFERENCES members(id),
  source               TEXT NOT NULL CHECK (source IN ('report','auto_flag','review_dispute')),
  severity             TEXT NOT NULL DEFAULT 'medium' CHECK (severity IN ('low','medium','high','critical')),
  state                TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','in_review','actioned','dismissed','escalated')),
  reporter_count       INT NOT NULL DEFAULT 0,
  primary_reason       TEXT,
  distribution_limited BOOLEAN NOT NULL DEFAULT FALSE,
  target_due_at        TIMESTAMPTZ NOT NULL,
  action               TEXT CHECK (action IN ('limit','remove','restore','request_verification','suspend','dismiss')),
  action_duration_days INT,
  reason_code          TEXT,
  operator_id          TEXT REFERENCES members(id),
  decided_at           TIMESTAMPTZ,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX moderation_cases_open_idx ON moderation_cases (state, severity, target_due_at);

CREATE TABLE reports (                                     -- FR39
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_id   TEXT NOT NULL REFERENCES members(id),
  case_id       UUID NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,
  object_kind   TEXT NOT NULL,
  object_id     UUID NOT NULL,
  reason        TEXT NOT NULL CHECK (reason IN ('scam','fake','impersonation','harassment','discrimination','spam','stale','privacy','other')),
  evidence_text TEXT CHECK (evidence_text IS NULL OR char_length(evidence_text) <= 1000),
  evidence_urls TEXT[] NOT NULL DEFAULT '{}' CHECK (cardinality(evidence_urls) <= 3),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE appeals (                                     -- FR41
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id      UUID NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,
  member_id    TEXT NOT NULL REFERENCES members(id),
  text         TEXT NOT NULL CHECK (char_length(text) <= 1000),
  evidence_urls TEXT[] NOT NULL DEFAULT '{}',
  state        TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','upheld','overturned','delayed')),
  reviewer_id  TEXT REFERENCES members(id),
  reason_code  TEXT,
  due_at       TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '7 days',
  decided_at   TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (case_id, member_id)
);

-- ---------------------------------------------------------------------------
-- Notifications (FR21, FR52b), analytics (FR45), audit (FR52c), config, dead letters
-- ---------------------------------------------------------------------------
CREATE TABLE notifications (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id      TEXT NOT NULL REFERENCES members(id),
  kind           TEXT NOT NULL,                            -- opportunity_match | enquiry | review_invite | moderation | digest | verification | promotion | system
  template_id    TEXT NOT NULL,
  title          TEXT NOT NULL,
  body           TEXT,
  link           TEXT,
  params         JSONB NOT NULL DEFAULT '{}',
  idempotency_key TEXT UNIQUE,
  read_at        TIMESTAMPTZ,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX notifications_member_idx ON notifications (member_id, created_at DESC);

CREATE TABLE analytics_events (
  id            BIGSERIAL PRIMARY KEY,
  member_pseudo TEXT,
  object_id     TEXT,
  surface       TEXT,
  event         TEXT NOT NULL,
  level         TEXT NOT NULL CHECK (level IN ('impression','view','action','attributed_outcome','confirmed_outcome','operational')),
  props         JSONB NOT NULL DEFAULT '{}',
  at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id          BIGSERIAL PRIMARY KEY,
  actor_id    TEXT,
  object_kind TEXT NOT NULL,
  object_id   TEXT NOT NULL,
  action      TEXT NOT NULL,
  reason_code TEXT,
  outcome     TEXT NOT NULL DEFAULT 'ok',
  details     JSONB NOT NULL DEFAULT '{}',
  at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX audit_events_idx ON audit_events (object_kind, object_id, at DESC);

CREATE TABLE config (
  key        TEXT PRIMARY KEY,
  value      JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dead_letters (
  id         BIGSERIAL PRIMARY KEY,
  target     TEXT NOT NULL,
  payload    JSONB NOT NULL,
  error      TEXT,
  attempts   INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE counsel_referrals (                           -- FR52(f)
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id       TEXT NOT NULL REFERENCES members(id),
  enquiry_id      UUID REFERENCES enquiries(id),
  problem_summary TEXT NOT NULL,
  consent         BOOLEAN NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Search vectors (FR15, FR52a) — maintained by trigger
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION listings_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.search_tsv :=
    setweight(to_tsvector('simple', coalesce(NEW.name,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(NEW.headline,'')), 'B') ||
    setweight(to_tsvector('simple', array_to_string(NEW.categories || NEW.capabilities || NEW.unmapped_labels, ' ')), 'B') ||
    setweight(to_tsvector('simple', coalesce(NEW.description,'')), 'C') ||
    setweight(to_tsvector('simple', coalesce(NEW.locality,'')), 'C');
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER listings_tsv BEFORE INSERT OR UPDATE ON listings FOR EACH ROW EXECUTE FUNCTION listings_tsv_update();

CREATE OR REPLACE FUNCTION opportunities_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.search_tsv :=
    setweight(to_tsvector('simple', coalesce(NEW.title,'')), 'A') ||
    setweight(to_tsvector('simple', array_to_string(NEW.required_capabilities, ' ')), 'B') ||
    setweight(to_tsvector('simple', coalesce(NEW.description,'') || ' ' || coalesce(NEW.requirements,'')), 'C') ||
    setweight(to_tsvector('simple', coalesce(NEW.location,'')), 'C');
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER opportunities_tsv BEFORE INSERT OR UPDATE ON opportunities FOR EACH ROW EXECUTE FUNCTION opportunities_tsv_update();

-- Haversine distance in km (FR15 radius filter, FR19 location fit)
CREATE OR REPLACE FUNCTION distance_km(lat1 DOUBLE PRECISION, lng1 DOUBLE PRECISION, lat2 DOUBLE PRECISION, lng2 DOUBLE PRECISION)
RETURNS DOUBLE PRECISION AS $$
  SELECT CASE WHEN lat1 IS NULL OR lng1 IS NULL OR lat2 IS NULL OR lng2 IS NULL THEN NULL ELSE
    2 * 6371 * asin(sqrt(
      power(sin(radians(lat2 - lat1) / 2), 2) +
      cos(radians(lat1)) * cos(radians(lat2)) * power(sin(radians(lng2 - lng1) / 2), 2)))
  END
$$ LANGUAGE sql IMMUTABLE;
