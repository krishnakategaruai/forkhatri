-- 025 — What the notification dispatcher may read about a circle (FR115).
--
-- The dispatcher runs after the request's transaction commits and has no acting member, so it
-- cannot see circle rows through RLS. Migration 004 established this pattern for activities; these
-- two readers are the same idea for circles: the smallest projection each notification needs.

CREATE OR REPLACE FUNCTION milavn_circle.circle_name(p_circle_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT c.name FROM milavn_circle.circle c WHERE c.id = p_circle_id;
$$;

-- The people who can act on a join request: the creator, plus anyone holding the organizer role.
CREATE OR REPLACE FUNCTION milavn_circle.circle_organizer_ids(p_circle_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(array_agg(DISTINCT id), ARRAY[]::uuid[]) FROM (
    SELECT c.created_by_member_id AS id FROM milavn_circle.circle c WHERE c.id = p_circle_id
    UNION
    SELECT m.member_id FROM milavn_circle.circle_membership m
    WHERE m.circle_id = p_circle_id AND m.left_at IS NULL AND m.member_role = 'organizer'
  ) people;
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.circle_name(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.circle_organizer_ids(uuid) TO milavn_app;
