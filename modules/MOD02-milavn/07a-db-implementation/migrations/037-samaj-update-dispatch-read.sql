-- 037 — What the notification dispatcher may read about an umbrella (FR126).
--
-- The dispatcher runs after the request's transaction commits, with no acting member, so it cannot
-- read `circle_group` through its own RLS (`current_setting('milavn.member_id', true) <> ''` is
-- false with nobody bound). Same pattern as migration 025's `circle_name()` for circles.

CREATE OR REPLACE FUNCTION milavn_circle.group_name(p_group_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT g.name FROM milavn_circle.circle_group g WHERE g.id = p_group_id;
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.group_name(uuid) TO milavn_app;
