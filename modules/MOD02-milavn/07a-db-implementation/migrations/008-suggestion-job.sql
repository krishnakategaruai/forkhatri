-- =============================================================================
-- Milavn (MOD02) — migration 008: circle-formation suggestion job writes.
-- Run as milavn_owner. Fix-forward.
--
-- `circle_formation_suggestion_member`'s RLS is member-self (correct: a
-- member may only respond to their own suggestion row). The nightly
-- co-participation job (TR17/FR022) writes rows for OTHER members, and a
-- recipient needs to see who else is in the suggestion — both go through
-- definer-owned functions that return only ids/names of the suggestion itself.
-- =============================================================================
CREATE OR REPLACE FUNCTION milavn_circle.create_formation_suggestion(p_name text, p_member_ids uuid[])
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE sid uuid := gen_random_uuid(); m uuid;
BEGIN
  INSERT INTO milavn_circle.circle_formation_suggestion (id, suggested_circle_name) VALUES (sid, p_name);
  FOREACH m IN ARRAY p_member_ids LOOP
    INSERT INTO milavn_circle.circle_formation_suggestion_member (suggestion_id, member_id) VALUES (sid, m) ON CONFLICT DO NOTHING;
  END LOOP;
  RETURN sid;
END;
$$;

CREATE OR REPLACE FUNCTION milavn_circle.suggestion_member_ids(p_suggestion_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(array_agg(member_id), ARRAY[]::uuid[]) FROM milavn_circle.circle_formation_suggestion_member WHERE suggestion_id = p_suggestion_id;
$$;

-- Does a pending/accepted suggestion already pair these two members?
CREATE OR REPLACE FUNCTION milavn_circle.suggestion_exists_for_pair(p_a uuid, p_b uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (
    SELECT 1 FROM milavn_circle.circle_formation_suggestion_member x
    JOIN milavn_circle.circle_formation_suggestion_member y ON x.suggestion_id = y.suggestion_id
    WHERE x.member_id = p_a AND y.member_id = p_b
  );
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.create_formation_suggestion(text, uuid[]) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.suggestion_member_ids(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.suggestion_exists_for_pair(uuid, uuid) TO milavn_app;
