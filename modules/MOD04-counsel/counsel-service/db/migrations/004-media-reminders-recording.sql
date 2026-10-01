-- Profile photos and evidence documents are uploaded, not linked; reminders are
-- sent once per booking; recordings are stored as consultation files.
SET search_path TO counsel, public;

ALTER TABLE provider_evidence ADD COLUMN IF NOT EXISTS document_name text;
ALTER TABLE provider_evidence ADD COLUMN IF NOT EXISTS document_mime text;

ALTER TABLE booking ADD COLUMN IF NOT EXISTS reminded_24h_at timestamptz;
ALTER TABLE booking ADD COLUMN IF NOT EXISTS reminded_15m_at timestamptz;

ALTER TABLE file ADD COLUMN IF NOT EXISTS is_recording boolean NOT NULL DEFAULT false;
