-- Owner request (2026-09-30): consultants choose how they can be booked.
--  * Fixed slots: exact start times ("Tue 7:00 pm, Thu 8:30 pm") instead of, or
--    alongside, open windows that are cut into 15-minute starts.
--  * Custom times: per service, a seeker may propose a time outside the listed
--    slots; the consultant accepts (the seeker then pays) or declines.
SET search_path TO counsel, public;

ALTER TABLE availability_rule ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'window';
DO $$ BEGIN
  ALTER TABLE availability_rule ADD CONSTRAINT availability_rule_kind_chk CHECK (kind IN ('window','slot'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

ALTER TABLE service ADD COLUMN IF NOT EXISTS allow_custom_time boolean NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS time_request (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  service_id   uuid NOT NULL REFERENCES service(id) ON DELETE CASCADE,
  provider_id  uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  seeker_id    uuid NOT NULL,
  starts_at    timestamptz NOT NULL,
  seeker_timezone text NOT NULL DEFAULT 'Asia/Kolkata',
  brief        text NOT NULL DEFAULT '',
  note         text,                              -- seeker's reason for the time
  status       text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','declined','withdrawn','expired')),
  reply        text,                              -- consultant's note on decline
  booking_id   uuid REFERENCES booking(id) ON DELETE SET NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  decided_at   timestamptz
);
CREATE INDEX IF NOT EXISTS time_request_provider_idx ON time_request(provider_id, status);
CREATE INDEX IF NOT EXISTS time_request_seeker_idx ON time_request(seeker_id, created_at DESC);

-- Accepted requests hold the time as a pending_payment booking for longer than
-- an abandoned checkout (the seeker may not be online when it is accepted).
ALTER TABLE booking ADD COLUMN IF NOT EXISTS pay_by timestamptz;

GRANT SELECT, INSERT, UPDATE, DELETE ON time_request TO counsel_app;

-- Two seeded consultants enable custom times; one publishes fixed slots.
UPDATE service SET allow_custom_time = true WHERE id IN ('50000000-0000-4000-8000-000000000001','50000000-0000-4000-8000-000000000041','50000000-0000-4000-8000-000000000051');
