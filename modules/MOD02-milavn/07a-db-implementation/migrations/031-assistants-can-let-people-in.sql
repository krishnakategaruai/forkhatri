-- 031 — An assistant can do the day-to-day work (FR121, completing migration 030).
--
-- Letting someone in and reading the answers is exactly the work an organizer wants to share, so
-- both join-request definers now ask `can_moderate_circle` (organizer OR assistant) instead of
-- `is_circle_organizer`. Who holds a role is still the organizer's decision alone (migration 030).

CREATE OR REPLACE FUNCTION milavn_circle.pending_join_requests(p_circle_id uuid, p_viewer uuid)
RETURNS TABLE (request_id uuid, member_id uuid, answers text[], created_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT r.id, r.member_id, r.answers, r.created_at
  FROM milavn_circle.join_request r
  WHERE r.circle_id = p_circle_id AND r.status = 'pending'
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND milavn_circle.can_moderate_circle(p_circle_id, p_viewer)
  ORDER BY r.created_at;
$$;

CREATE OR REPLACE FUNCTION milavn_circle.decide_join_request(p_request_id uuid, p_actor uuid, p_approve boolean)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE r record;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN NULL; END IF;
  SELECT jr.id, jr.circle_id, jr.member_id INTO r
  FROM milavn_circle.join_request jr WHERE jr.id = p_request_id AND jr.status = 'pending';
  IF NOT FOUND OR NOT milavn_circle.can_moderate_circle(r.circle_id, p_actor) THEN RETURN NULL; END IF;
  UPDATE milavn_circle.join_request
     SET status = CASE WHEN p_approve THEN 'approved' ELSE 'declined' END,
         decided_at = now(), decided_by_member_id = p_actor
   WHERE id = r.id;
  IF p_approve THEN
    INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
    VALUES (r.circle_id, r.member_id, 'member') ON CONFLICT DO NOTHING;
  END IF;
  RETURN r.member_id;
END;
$$;

-- Assistants are told about a new request too — they are the people who will act on it.
CREATE OR REPLACE FUNCTION milavn_circle.circle_organizer_ids(p_circle_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(array_agg(DISTINCT id), ARRAY[]::uuid[]) FROM (
    SELECT c.created_by_member_id AS id FROM milavn_circle.circle c WHERE c.id = p_circle_id
    UNION
    SELECT m.member_id FROM milavn_circle.circle_membership m
    WHERE m.circle_id = p_circle_id AND m.left_at IS NULL AND m.member_role IN ('organizer', 'assistant')
  ) people;
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.pending_join_requests(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.decide_join_request(uuid, uuid, boolean) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.circle_organizer_ids(uuid) TO milavn_app;
