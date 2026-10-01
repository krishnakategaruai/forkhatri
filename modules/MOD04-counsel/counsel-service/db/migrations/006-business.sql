-- Business opportunities from the competitor review (2026-09-30):
--   packages (MentorCruise/Topmate bundles), paid questions (Topmate Priority DM /
--   JustAnswer), instant consults (Practo / Astrotalk), post-call recap (GrowthMentor).
-- Money for a package or a question is a "purchase"; the ledger can now point at
-- either a booking or a purchase.
SET search_path TO counsel, public;

-- Packages: N sessions of one service for one price, used within a validity window.
CREATE TABLE IF NOT EXISTS package (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  service_id  uuid NOT NULL REFERENCES service(id) ON DELETE CASCADE,
  sessions    int NOT NULL CHECK (sessions BETWEEN 2 AND 24),
  price_minor bigint NOT NULL CHECK (price_minor > 0),
  valid_days  int NOT NULL DEFAULT 90 CHECK (valid_days BETWEEN 14 AND 365),
  active      boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS package_service_idx ON package(service_id);

-- One purchase row per package bought or question asked.
CREATE TABLE IF NOT EXISTS purchase (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind                  text NOT NULL CHECK (kind IN ('package','question')),
  buyer_id              uuid NOT NULL,
  provider_id           uuid NOT NULL REFERENCES provider(member_id),
  package_id            uuid REFERENCES package(id),
  service_id            uuid REFERENCES service(id),
  sessions_total        int,
  sessions_used         int NOT NULL DEFAULT 0,
  expires_at            timestamptz,
  currency              text NOT NULL,
  gross_minor           bigint NOT NULL,
  platform_fee_minor    bigint NOT NULL,
  provider_payable_minor bigint NOT NULL,
  refund_minor          bigint NOT NULL DEFAULT 0,
  status                text NOT NULL DEFAULT 'pending_payment' CHECK (status IN ('pending_payment','active','used_up','expired','refunded','answered','cancelled')),
  payout_status         text NOT NULL DEFAULT 'none' CHECK (payout_status IN ('none','eligible','paid')),
  external_ref          text,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS purchase_buyer_idx ON purchase(buyer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS purchase_provider_idx ON purchase(provider_id, created_at DESC);

-- A booking made with a package session carries the purchase; its price is the
-- per-session share and it is confirmed without a separate payment.
ALTER TABLE booking ADD COLUMN IF NOT EXISTS purchase_id uuid REFERENCES purchase(id);

-- Ledger rows may belong to a purchase instead of a booking.
ALTER TABLE ledger_entry ALTER COLUMN booking_id DROP NOT NULL;
ALTER TABLE ledger_entry ADD COLUMN IF NOT EXISTS purchase_id uuid REFERENCES purchase(id) ON DELETE CASCADE;

-- Paid questions: asked in writing, answered in writing within `answer_days`,
-- otherwise refunded automatically.
ALTER TABLE service ADD COLUMN IF NOT EXISTS question_price_minor bigint;         -- NULL = questions off
ALTER TABLE service ADD COLUMN IF NOT EXISTS question_answer_days int NOT NULL DEFAULT 3;
ALTER TABLE service ADD COLUMN IF NOT EXISTS instant_allowed boolean NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS question (
  purchase_id uuid PRIMARY KEY REFERENCES purchase(id) ON DELETE CASCADE,
  service_id  uuid NOT NULL REFERENCES service(id),
  body        text NOT NULL,
  answer      text,
  answered_at timestamptz,
  due_at      timestamptz NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- Instant consults: the consultant is "available now" until this time.
ALTER TABLE provider ADD COLUMN IF NOT EXISTS available_until timestamptz;

-- Post-call recap stored with the booking.
ALTER TABLE booking ADD COLUMN IF NOT EXISTS recap text;
ALTER TABLE booking ADD COLUMN IF NOT EXISTS recap_at timestamptz;

GRANT SELECT, INSERT, UPDATE, DELETE ON package, purchase, question TO counsel_app;

-- Sample offers on two seeded services, so the flows can be seen.
INSERT INTO package (id, service_id, sessions, price_minor, valid_days) VALUES
  ('5a000000-0000-4000-8000-000000000001','50000000-0000-4000-8000-000000000041',3,450000,90),
  ('5a000000-0000-4000-8000-000000000002','50000000-0000-4000-8000-000000000011',4,400000,120)
ON CONFLICT (id) DO NOTHING;
UPDATE service SET question_price_minor = 50000, question_answer_days = 2 WHERE id IN ('50000000-0000-4000-8000-000000000011','50000000-0000-4000-8000-000000000031') AND question_price_minor IS NULL;
UPDATE service SET instant_allowed = true WHERE id IN ('50000000-0000-4000-8000-000000000011','50000000-0000-4000-8000-000000000051');
