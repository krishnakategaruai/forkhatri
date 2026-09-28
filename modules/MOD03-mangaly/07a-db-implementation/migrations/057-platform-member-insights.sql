-- =============================================================================
-- 057 — Facts for the ForKhatri owner's Members dashboard (platform console,
--       ARCHITECTURE.md ADR-012)
--
-- WHY (owner, 2026-09-27): "I want to see total users, and locations hotspot
-- ... counts (m, f, age, etc.)". Gender and date of birth exist only in
-- Mangaly, and city lives in each module's own profile, so the platform's
-- dashboard asks Mangaly for them over the internal, service-key-protected
-- endpoint `GET /internal/v1/insights/members`. The platform turns them into
-- totals; nothing is stored outside Mangaly and the browser only ever sees
-- counts.
--
-- One row per Mangaly account that has a profile of either kind:
--   * 'candidate' — a matrimonial profile (gender, date of birth, city,
--     looking for, marital status, mother tongue);
--   * 'member'    — a parent/sibling/relative's own "My profile" (city only).
-- No names, photos, phone numbers or free text leave this function.
--
-- SECURITY DEFINER because the reader is the platform, not a signed-in
-- member: under RLS a member may only read their own profile row.
-- Idempotent.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_operations.platform_member_facts()
RETURNS TABLE (
  account_id      uuid,
  kind            text,
  gender          text,
  date_of_birth   date,
  city            text,
  profile_status  text,
  looking_for     text,
  marital_status  text,
  mother_tongue   text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_discovery, pg_temp
AS $$
  SELECT p.account_id, 'candidate', p.gender, p.date_of_birth, p.city_locality,
         p.status::text, d.looking_for, d.marital_status, d.mother_tongue
    FROM mangaly_profile.profile p
    -- The discovery index keys on the account id (its `profile_id` is the account).
    LEFT JOIN mangaly_discovery.discovery_profile_index d ON d.profile_id = p.account_id
  UNION ALL
  SELECT m.account_id, 'member', NULL, NULL, m.city, NULL, NULL, NULL, NULL
    FROM mangaly_profile.member_profile m
   WHERE NOT EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.account_id = m.account_id);
$$;

REVOKE ALL ON FUNCTION mangaly_operations.platform_member_facts() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.platform_member_facts() TO mangaly_app;
