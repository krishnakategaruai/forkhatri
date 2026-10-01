-- Owner decision (2026-09-30): Counsel is one-to-one advice, not tuition. Packages
-- become "follow-ups": 1–3 check-ins with the same consultant on the same problem,
-- offered after a completed consultation, used within 30–90 days.
SET search_path TO counsel, public;

ALTER TABLE package DROP CONSTRAINT IF EXISTS package_sessions_check;
ALTER TABLE package DROP CONSTRAINT IF EXISTS package_valid_days_check;
UPDATE package SET sessions = LEAST(sessions, 3), valid_days = LEAST(GREATEST(valid_days, 30), 90);
ALTER TABLE package ADD CONSTRAINT package_sessions_check CHECK (sessions BETWEEN 1 AND 3);
ALTER TABLE package ADD CONSTRAINT package_valid_days_check CHECK (valid_days BETWEEN 30 AND 90);
ALTER TABLE package ALTER COLUMN valid_days SET DEFAULT 60;

-- Seed samples re-priced as follow-ups (less than the same number of full sessions).
UPDATE package SET sessions = 2, price_minor = 280000, valid_days = 60 WHERE id = '5a000000-0000-4000-8000-000000000001';  -- Neha: 2 × ₹1,800 → ₹2,800
UPDATE package SET sessions = 2, price_minor = 200000, valid_days = 90 WHERE id = '5a000000-0000-4000-8000-000000000002';  -- Ravi: 2 × ₹1,200 → ₹2,000

-- Call quality feedback after a call (Teams-style thumbs + issues), for improving the room.
CREATE TABLE IF NOT EXISTS call_feedback (
  booking_id uuid NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
  member_id  uuid NOT NULL,
  good       boolean NOT NULL,
  issues     text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (booking_id, member_id)
);
GRANT SELECT, INSERT, UPDATE, DELETE ON call_feedback TO counsel_app;

-- Stored files: encrypted at rest (flag per file for files saved before this change) and scan result.
ALTER TABLE file ADD COLUMN IF NOT EXISTS encrypted boolean NOT NULL DEFAULT false;
ALTER TABLE file ADD COLUMN IF NOT EXISTS scan_status text NOT NULL DEFAULT 'not_scanned';
ALTER TABLE provider_evidence ADD COLUMN IF NOT EXISTS document_encrypted boolean NOT NULL DEFAULT false;
