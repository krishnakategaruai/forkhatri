-- Privacy (export, deletion), retention and payout details. No outside service needed.
SET search_path TO counsel, public;

-- Where a consultant is paid. The account number / UPI id is encrypted by the
-- API (Fernet, PAYOUT_ENCRYPTION_KEY) and only the last 4 characters are kept
-- readable for display.
CREATE TABLE IF NOT EXISTS payout_method (
  provider_id   uuid PRIMARY KEY REFERENCES provider(member_id) ON DELETE CASCADE,
  kind          text NOT NULL CHECK (kind IN ('upi','bank')),
  holder_name   text NOT NULL,
  secret        text NOT NULL,          -- encrypted UPI id or account number
  ifsc          text,                   -- bank only (not secret)
  last4         text NOT NULL,
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- A member who deleted their Counsel data: kept so late events can be ignored.
CREATE TABLE IF NOT EXISTS erased_member (
  member_id  uuid PRIMARY KEY,
  erased_at  timestamptz NOT NULL DEFAULT now(),
  reason     text NOT NULL
);

INSERT INTO platform_setting (key, value) VALUES
  ('retention_recording_days', '90'),
  ('retention_file_days', '365')
ON CONFLICT (key) DO NOTHING;

GRANT SELECT, INSERT, UPDATE, DELETE ON payout_method, erased_member TO counsel_app;
