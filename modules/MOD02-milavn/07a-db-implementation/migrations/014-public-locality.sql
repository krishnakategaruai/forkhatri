-- 014 — Another member's approximate place. `member_public_profile` is a plain
-- view, so the base table's self-only RLS still applies to it and People /
-- person pages saw NULL for everyone else. The definer helper returns the raw
-- city/zone/locality; the service then clamps it to the person's own
-- precision setting (FR041) before anything leaves the API.

CREATE OR REPLACE FUNCTION milavn_profile.public_locality(p_member_id uuid)
RETURNS TABLE (locality_city text, locality_zone text, locality_locality text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_profile, pg_catalog AS $$
  SELECT p.locality_city, p.locality_zone, p.locality_locality
  FROM milavn_profile.member_profile p WHERE p.member_id = p_member_id;
$$;
GRANT EXECUTE ON FUNCTION milavn_profile.public_locality(uuid) TO milavn_app;
