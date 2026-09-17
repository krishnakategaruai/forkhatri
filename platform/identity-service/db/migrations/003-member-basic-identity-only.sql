-- =============================================================================
-- 003 — The platform member holds basic identity only (product-owner rule, 2026-09-14)
--
-- "Profile will be present in each module as per their needs; ForKhatri only has
-- basic user info." The platform member keeps: id, display name, verified phone
-- and/or email, preferred language, platform verification level, status.
-- Location, photos, bio and every other profile detail belong to the module that
-- needs them, under that module's own privacy rules (Milavn location precision,
-- Mangaly selective sharing). `home_locality` duplicated module-owned location
-- data, so it is removed. Only development test values existed in it.
--
-- Run as identity_owner after deploying code that no longer reads the column.
-- Idempotent.
-- =============================================================================

ALTER TABLE identity.member DROP COLUMN IF EXISTS home_locality;

COMMENT ON TABLE identity.member IS
  '[TR10] Canonical ForKhatri member: basic identity only. Profile data lives in module member-link tables. PII: phone_e164, email.';
