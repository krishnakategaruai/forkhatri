-- =============================================================================
-- 039 — Facts for the ForKhatri owner's Members dashboard (platform console,
--       ARCHITECTURE.md ADR-012)
--
-- WHY (owner, 2026-09-27): "I want to see total users, and locations hotspot".
-- A member's city lives in Milavn's own profile, so the platform asks Milavn
-- over the internal, service-key-protected endpoint
-- `GET /internal/v1/insights/members` and turns the answer into totals.
-- Only the member id and the city (the coarsest level of Milavn's location
-- hierarchy, never zone, locality or a precise place) leave this function.
--
-- SECURITY DEFINER because the reader is the platform, not a signed-in member:
-- RLS lets a member read only their own profile row. Idempotent.
-- =============================================================================

CREATE OR REPLACE FUNCTION milavn_profile.platform_member_facts()
RETURNS TABLE (member_id uuid, city text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = milavn_profile, pg_temp
AS $$
  SELECT p.member_id, p.locality_city FROM milavn_profile.member_profile p;
$$;

REVOKE ALL ON FUNCTION milavn_profile.platform_member_facts() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_profile.platform_member_facts() TO milavn_app;
