-- =============================================================================
-- Counsel (MOD04) — schema. Run as counsel_owner against the `counsel` database.
-- Idempotent: safe to re-run.
--
-- Principles from the product definition:
--   * Providers are generic; professions/expertise are DATA (expertise_area).
--   * Expertise, experience, qualification, certification and registration are
--     separate kinds of evidence; verification is granular per dimension.
--   * Money is a ledger, not a payment status (booking -> payment -> ledger).
--   * The booking state machine is explicit; double booking is impossible by
--     constraint, not by discipline (EXCLUDE on the provider's time range).
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE SCHEMA IF NOT EXISTS counsel;
SET search_path TO counsel, public;

-- Members known to Counsel (a cache of platform identity; identity is platform-owned).
CREATE TABLE IF NOT EXISTS member (
  member_id    uuid PRIMARY KEY,
  display_name text NOT NULL,
  language     text NOT NULL DEFAULT 'en',
  timezone     text NOT NULL DEFAULT 'Asia/Kolkata',
  first_seen   timestamptz NOT NULL DEFAULT now(),
  last_seen    timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Expertise taxonomy (extensible; consultants may propose new areas)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expertise_area (
  id          text PRIMARY KEY,                 -- slug
  parent_id   text REFERENCES expertise_area(id) ON DELETE SET NULL,
  name_en     text NOT NULL,
  name_hi     text NOT NULL,
  name_te     text NOT NULL,
  status      text NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled')),
  regulated   boolean NOT NULL DEFAULT false,
  sort_order  int NOT NULL DEFAULT 100,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS expertise_request (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposed_by  uuid NOT NULL,
  name         text NOT NULL,
  parent_id    text REFERENCES expertise_area(id),
  note         text,
  status       text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  decided_by   uuid,
  decided_at   timestamptz,
  created_area text REFERENCES expertise_area(id),
  created_at   timestamptz NOT NULL DEFAULT now()
);

-- Per-area, per-jurisdiction compliance: which verification dimensions a
-- provider must clear before a service in that area may be published.
CREATE TABLE IF NOT EXISTS compliance_rule (
  area_id             text NOT NULL REFERENCES expertise_area(id) ON DELETE CASCADE,
  jurisdiction        text NOT NULL DEFAULT '*',
  required_dimensions text[] NOT NULL DEFAULT '{}',
  disclaimer_key      text,
  recording_allowed   boolean NOT NULL DEFAULT true,
  PRIMARY KEY (area_id, jurisdiction)
);

-- ---------------------------------------------------------------------------
-- Provider
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider (
  member_id     uuid PRIMARY KEY,
  headline      text NOT NULL DEFAULT '',
  intro         text NOT NULL DEFAULT '',
  photo_url     text,
  city          text,
  country       text NOT NULL DEFAULT 'IN',
  timezone      text NOT NULL DEFAULT 'Asia/Kolkata',
  languages     text[] NOT NULL DEFAULT '{en}',
  links         jsonb NOT NULL DEFAULT '{}'::jsonb,   -- {linkedin, website, youtube, instagram, portfolio}
  currency      text NOT NULL DEFAULT 'INR',
  status        text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','pending_review','approved','changes_requested','suspended')),
  review_note   text,
  submitted_at  timestamptz,
  reviewed_at   timestamptz,
  reviewed_by   uuid,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS provider_expertise (
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  area_id     text NOT NULL REFERENCES expertise_area(id),
  years       int NOT NULL DEFAULT 0 CHECK (years >= 0),
  is_primary  boolean NOT NULL DEFAULT false,
  PRIMARY KEY (provider_id, area_id)
);

-- Experience / qualification / certification / registration / business / portfolio
CREATE TABLE IF NOT EXISTS provider_evidence (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id   uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  kind          text NOT NULL CHECK (kind IN ('experience','qualification','certification','registration','business','portfolio')),
  title         text NOT NULL,
  issuer        text,                           -- organisation / institution / authority / employer
  year_from     int,
  year_to       int,
  reference_no  text,                           -- registration / certificate number (sensitive)
  document_url  text,                           -- private upload
  status        text NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted','verified','rejected')),
  review_note   text,
  reviewed_by   uuid,
  reviewed_at   timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS provider_evidence_provider_idx ON provider_evidence(provider_id);

-- Granular verification: never one universal "Verified" badge.
CREATE TABLE IF NOT EXISTS verification (
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  dimension   text NOT NULL CHECK (dimension IN ('identity','contact','experience','qualification','certification','registration','business','portfolio')),
  verified_at timestamptz NOT NULL DEFAULT now(),
  verified_by uuid,
  note        text,
  PRIMARY KEY (provider_id, dimension)
);

-- ---------------------------------------------------------------------------
-- Services and availability
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS service (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id        uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  area_id            text NOT NULL REFERENCES expertise_area(id),
  title              text NOT NULL,
  description        text NOT NULL DEFAULT '',
  outcomes           text[] NOT NULL DEFAULT '{}',   -- "what you leave with"
  duration_min       int NOT NULL CHECK (duration_min BETWEEN 15 AND 240),
  price_minor        bigint NOT NULL CHECK (price_minor > 0),
  currency           text NOT NULL DEFAULT 'INR',
  formats            text[] NOT NULL DEFAULT '{video}',  -- video | audio | screen | files
  min_notice_hours   int NOT NULL DEFAULT 12,
  max_advance_days   int NOT NULL DEFAULT 30,
  buffer_min         int NOT NULL DEFAULT 10,
  recording_allowed  boolean NOT NULL DEFAULT false,
  status             text NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused','archived')),
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS service_provider_idx ON service(provider_id);

CREATE TABLE IF NOT EXISTS availability_rule (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  weekday     int NOT NULL CHECK (weekday BETWEEN 0 AND 6),  -- 0 = Monday
  start_time  time NOT NULL,
  end_time    time NOT NULL,
  CHECK (end_time > start_time)
);
CREATE INDEX IF NOT EXISTS availability_rule_provider_idx ON availability_rule(provider_id);

CREATE TABLE IF NOT EXISTS availability_exception (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  on_date     date NOT NULL,
  start_time  time,            -- NULL + available=false => whole day off
  end_time    time,
  available   boolean NOT NULL DEFAULT false,
  note        text
);
CREATE INDEX IF NOT EXISTS availability_exception_provider_idx ON availability_exception(provider_id, on_date);

-- ---------------------------------------------------------------------------
-- Booking (the commercial unit) — explicit state machine
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS booking (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  service_id            uuid NOT NULL REFERENCES service(id),
  provider_id           uuid NOT NULL REFERENCES provider(member_id),
  seeker_id             uuid NOT NULL,
  starts_at             timestamptz NOT NULL,
  ends_at               timestamptz NOT NULL,
  seeker_timezone       text NOT NULL DEFAULT 'Asia/Kolkata',
  status                text NOT NULL DEFAULT 'pending_payment' CHECK (status IN (
                          'pending_payment','confirmed','in_progress','completed',
                          'cancelled_by_seeker','cancelled_by_provider','no_show_seeker','no_show_provider','expired')),
  brief                 text NOT NULL DEFAULT '',   -- what the seeker needs help with
  -- price snapshot (never recomputed from the live service)
  service_title         text NOT NULL,
  duration_min          int NOT NULL,
  currency              text NOT NULL,
  gross_minor           bigint NOT NULL,
  platform_fee_minor    bigint NOT NULL,
  processing_fee_minor  bigint NOT NULL DEFAULT 0,
  tax_minor             bigint NOT NULL DEFAULT 0,
  provider_payable_minor bigint NOT NULL,
  refund_minor          bigint NOT NULL DEFAULT 0,
  cancellation_policy   jsonb NOT NULL,           -- snapshot shown before payment
  recording_allowed     boolean NOT NULL DEFAULT false,
  formats               text[] NOT NULL DEFAULT '{video}',
  cancel_reason         text,
  cancelled_by          uuid,
  cancelled_at          timestamptz,
  completed_at          timestamptz,
  payout_status         text NOT NULL DEFAULT 'none' CHECK (payout_status IN ('none','eligible','paid')),
  payout_id             uuid,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CHECK (ends_at > starts_at),
  -- A provider can hold only one live booking per time range.
  EXCLUDE USING gist (provider_id WITH =, tstzrange(starts_at, ends_at) WITH &&)
    WHERE (status IN ('pending_payment','confirmed','in_progress'))
);
CREATE INDEX IF NOT EXISTS booking_seeker_idx ON booking(seeker_id, starts_at DESC);
CREATE INDEX IF NOT EXISTS booking_provider_idx ON booking(provider_id, starts_at DESC);

-- ---------------------------------------------------------------------------
-- Money: payment attempts, ledger, payouts (provider-agnostic)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id    uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  provider_name text NOT NULL,                   -- 'mock' | 'razorpay' | ...
  external_ref  text,
  amount_minor  bigint NOT NULL,
  currency      text NOT NULL,
  status        text NOT NULL DEFAULT 'created' CHECK (status IN ('created','succeeded','failed','refunded','partially_refunded')),
  refunded_minor bigint NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS payment_booking_idx ON payment(booking_id);

CREATE TABLE IF NOT EXISTS ledger_entry (
  id           bigserial PRIMARY KEY,
  booking_id   uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  kind         text NOT NULL CHECK (kind IN ('gross','platform_fee','processing_fee','tax','refund','provider_payable','payout','adjustment')),
  amount_minor bigint NOT NULL,
  currency     text NOT NULL,
  note         text,
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ledger_booking_idx ON ledger_entry(booking_id);

CREATE TABLE IF NOT EXISTS payout (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id  uuid NOT NULL REFERENCES provider(member_id),
  amount_minor bigint NOT NULL,
  currency     text NOT NULL,
  status       text NOT NULL DEFAULT 'requested' CHECK (status IN ('requested','paid','failed')),
  external_ref text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  paid_at      timestamptz
);

-- ---------------------------------------------------------------------------
-- Consultation workspace
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS message (
  id         bigserial PRIMARY KEY,
  booking_id uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  sender_id  uuid,                                -- NULL = system
  kind       text NOT NULL DEFAULT 'chat' CHECK (kind IN ('chat','system','file')),
  body       text NOT NULL,
  file_id    uuid,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS message_booking_idx ON message(booking_id, id);

-- owner_id NULL = the shared note; otherwise that member's private note.
CREATE TABLE IF NOT EXISTS note (
  booking_id uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  owner_id   uuid,
  body       text NOT NULL DEFAULT '',
  updated_by uuid,
  updated_at timestamptz NOT NULL DEFAULT now(),
  version    int NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS note_shared_uidx ON note(booking_id) WHERE owner_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS note_private_uidx ON note(booking_id, owner_id) WHERE owner_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS action_item (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  text       text NOT NULL,
  owner_id   uuid,                                -- who will do it (optional)
  done       boolean NOT NULL DEFAULT false,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  owner_id   uuid NOT NULL,
  name       text NOT NULL,
  mime       text NOT NULL,
  size_bytes bigint NOT NULL,
  storage_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

CREATE TABLE IF NOT EXISTS recording_consent (
  booking_id   uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  member_id    uuid NOT NULL,
  consented_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (booking_id, member_id)
);

CREATE TABLE IF NOT EXISTS session_event (
  id         bigserial PRIMARY KEY,
  booking_id uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  member_id  uuid,
  kind       text NOT NULL,   -- joined | left | recording_started | recording_stopped | screen_share_started | screen_share_stopped
  at         timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Reviews, reputation, saved
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id      uuid NOT NULL UNIQUE REFERENCES booking(id) ON DELETE CASCADE,
  provider_id     uuid NOT NULL REFERENCES provider(member_id),
  reviewer_id     uuid NOT NULL,
  overall         int NOT NULL CHECK (overall BETWEEN 1 AND 5),
  expertise       int NOT NULL CHECK (expertise BETWEEN 1 AND 5),
  communication   int NOT NULL CHECK (communication BETWEEN 1 AND 5),
  professionalism int NOT NULL CHECK (professionalism BETWEEN 1 AND 5),
  punctuality     int NOT NULL CHECK (punctuality BETWEEN 1 AND 5),
  body            text NOT NULL DEFAULT '',
  hidden          boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS review_provider_idx ON review(provider_id, created_at DESC);

CREATE TABLE IF NOT EXISTS saved_provider (
  member_id   uuid NOT NULL,
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, provider_id)
);

-- ---------------------------------------------------------------------------
-- Notifications, safety, audit, settings
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notification (
  id         bigserial PRIMARY KEY,
  member_id  uuid NOT NULL,
  kind       text NOT NULL,
  params     jsonb NOT NULL DEFAULT '{}'::jsonb,
  booking_id uuid,
  read_at    timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS notification_member_idx ON notification(member_id, id DESC);

-- Outbound deliveries through channel adapters (email / sms / whatsapp / push).
CREATE TABLE IF NOT EXISTS delivery (
  id          bigserial PRIMARY KEY,
  member_id   uuid NOT NULL,
  channel     text NOT NULL,
  kind        text NOT NULL,
  payload     jsonb NOT NULL,
  status      text NOT NULL DEFAULT 'queued',
  attempts    int NOT NULL DEFAULT 0,
  last_error  text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  sent_at     timestamptz
);

CREATE TABLE IF NOT EXISTS report (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_id uuid NOT NULL,
  target_kind text NOT NULL CHECK (target_kind IN ('provider','service','booking','message','member')),
  target_id   text NOT NULL,
  reason      text NOT NULL,
  detail      text,
  status      text NOT NULL DEFAULT 'open' CHECK (status IN ('open','actioned','dismissed')),
  decided_by  uuid,
  decided_at  timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dispute (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id  uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  opened_by   uuid NOT NULL,
  reason      text NOT NULL,
  status      text NOT NULL DEFAULT 'open' CHECK (status IN ('open','refunded','partially_refunded','closed')),
  resolution  text,
  refund_minor bigint NOT NULL DEFAULT 0,
  decided_by  uuid,
  decided_at  timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS block (
  member_id  uuid NOT NULL,
  blocked_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, blocked_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id          bigserial PRIMARY KEY,
  actor_id    uuid,
  action      text NOT NULL,
  target_kind text NOT NULL,
  target_id   text NOT NULL,
  detail      jsonb NOT NULL DEFAULT '{}'::jsonb,
  at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS platform_setting (
  key   text PRIMARY KEY,
  value jsonb NOT NULL
);

-- Defaults. Commercial figures live here as data, never in code.
INSERT INTO platform_setting (key, value) VALUES
  ('platform_fee_percent', '2'),
  ('cancellation_policy', '{"seeker":[{"min_hours_before":24,"refund_percent":100},{"min_hours_before":6,"refund_percent":50},{"min_hours_before":0,"refund_percent":0}],"provider_cancel_refund_percent":100,"seeker_no_show_refund_percent":0,"provider_no_show_refund_percent":100}'),
  ('payout_hold_hours', '24'),
  ('review_window_days', '14')
ON CONFLICT (key) DO NOTHING;

-- Grants for the non-owning runtime role.
GRANT USAGE ON SCHEMA counsel TO counsel_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA counsel TO counsel_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA counsel TO counsel_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA counsel GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO counsel_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA counsel GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO counsel_app;
