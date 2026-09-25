-- =============================================================================
-- 031 — Discovery index carries the biodata facts the rework filters on.
--
-- WHY (2026-09-17, rework contract §3): Discover gains height, gotra,
-- sub-community, profession, income band, mother tongue and manglik filters,
-- free-text `q` and three sort orders, plus a `total`. Filtering moves into
-- SQL, so the facts it filters on become real columns on the read model
-- (`refresh_index()` writes them from `profile_attribute`), instead of being
-- dug out of the JSON snapshot in Python for every row.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_discovery.discovery_profile_index
  ADD COLUMN IF NOT EXISTS gender text,
  ADD COLUMN IF NOT EXISTS looking_for text,
  ADD COLUMN IF NOT EXISTS date_of_birth date,
  ADD COLUMN IF NOT EXISTS marital_status text,
  ADD COLUMN IF NOT EXISTS diet text,
  ADD COLUMN IF NOT EXISTS height_cm integer,
  ADD COLUMN IF NOT EXISTS gotra text,
  ADD COLUMN IF NOT EXISTS sub_community text,
  ADD COLUMN IF NOT EXISTS mother_tongue text,
  ADD COLUMN IF NOT EXISTS income_band text,
  ADD COLUMN IF NOT EXISTS manglik text,
  ADD COLUMN IF NOT EXISTS profile_created_at timestamptz,
  ADD COLUMN IF NOT EXISTS last_active_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_discovery_gender_looking
  ON mangaly_discovery.discovery_profile_index (searchable, gender, looking_for);
CREATE INDEX IF NOT EXISTS idx_discovery_created
  ON mangaly_discovery.discovery_profile_index (profile_created_at DESC);
CREATE INDEX IF NOT EXISTS idx_discovery_active
  ON mangaly_discovery.discovery_profile_index (last_active_at DESC);
