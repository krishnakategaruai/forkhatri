-- =============================================================================
-- Milavn (MOD02) — migration 005: another member's location precision.
-- Run as milavn_owner.
--
-- FR041/FR042: when a person is suggested (People Discovery), their locality
-- must be shown at no more precision than THEY chose. Their setting row is
-- self-only under RLS, so the viewer's transaction cannot read it directly;
-- this definer function returns only the precision level (an enum), never
-- anything else about the other member.
-- =============================================================================

CREATE OR REPLACE FUNCTION milavn_locationprivacy.precision_of(p_member_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_locationprivacy, pg_catalog AS $$
  SELECT coalesce((SELECT precision_level::text FROM milavn_locationprivacy.location_precision_setting WHERE member_id = p_member_id), 'locality');
$$;

GRANT EXECUTE ON FUNCTION milavn_locationprivacy.precision_of(uuid) TO milavn_app;
