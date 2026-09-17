-- 026 — What someone outside a circle may see before asking to join (FR115).
--
-- Found live while testing FR115: a member who is not in a circle gets 404 on its detail page (the
-- circle row is not theirs to read), which is the intended privacy rule — but it also meant the
-- questions the organizer asks were unreadable to the very person who has to answer them. Joining
-- happens from the Circles list, so this returns exactly what that row needs and nothing else:
-- the circle's name, whether it screens, and the questions themselves. No members, no activity, no
-- description — those stay behind membership.

CREATE OR REPLACE FUNCTION milavn_circle.join_prompt(p_circle_id uuid)
RETURNS TABLE (circle_name text, join_policy text, join_questions text[])
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT c.name, c.join_policy, c.join_questions
  FROM milavn_circle.circle c
  WHERE c.id = p_circle_id
    AND current_setting('milavn.member_id', true) <> ''  -- signed-in members only
    AND c.circle_type IN ('public', 'community', 'interest', 'local', 'recurring_activity');  -- OPEN_TYPES
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.join_prompt(uuid) TO milavn_app;
