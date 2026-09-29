-- 041 — The organizer can delete their circle (owner review, 2026-09-28: "the admin gets every
-- option of the circle"). Also how the pair-born "Asha & Arjun's circle" gets removed.
--
-- The delete is a SECURITY DEFINER function rather than an RLS DELETE policy because it must
-- (a) read milavn_activity.occurrence across the component boundary and (b) detach the
-- formation suggestion that created the circle (its FK is NO ACTION). Rules:
--   * only today's organizer may delete;
--   * a circle with upcoming, uncancelled events cannot be deleted — cancel them first, so
--     no attendee is left holding an event whose circle vanished (Meetup's rule too);
--   * everything inside the circle (memberships, posts, polls, requests, drives) goes with it
--     via the existing ON DELETE CASCADE keys.

CREATE OR REPLACE FUNCTION milavn_circle.delete_circle(p_circle_id uuid, p_member_id uuid)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog
AS $$
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_organizer'; END IF;
  IF NOT EXISTS (SELECT 1 FROM milavn_circle.circle WHERE id = p_circle_id) THEN RETURN 'not_found'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM milavn_circle.circle_membership m
    WHERE m.circle_id = p_circle_id AND m.member_id = p_member_id AND m.member_role = 'organizer' AND m.left_at IS NULL
  ) THEN
    RETURN 'not_organizer';
  END IF;
  IF EXISTS (
    SELECT 1 FROM milavn_activity.occurrence o
    WHERE o.circle_id = p_circle_id AND o.status <> 'cancelled' AND o.time_start > now()
  ) THEN
    RETURN 'has_upcoming';
  END IF;
  UPDATE milavn_circle.circle_formation_suggestion SET created_circle_id = NULL WHERE created_circle_id = p_circle_id;
  UPDATE milavn_activity.occurrence SET circle_id = NULL WHERE circle_id = p_circle_id;
  DELETE FROM milavn_circle.circle WHERE id = p_circle_id;
  RETURN 'deleted';
END;
$$;

REVOKE ALL ON FUNCTION milavn_circle.delete_circle(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.delete_circle(uuid, uuid) TO milavn_app;

-- Posts can carry a document (a trek checklist PDF, a samaj meeting agenda, a match schedule)
-- beside or instead of a photo. The original file name is kept for display.
ALTER TABLE milavn_circle.circle_post ADD COLUMN IF NOT EXISTS doc_ref text;
ALTER TABLE milavn_circle.circle_post ADD COLUMN IF NOT EXISTS doc_name text;
ALTER TABLE milavn_circle.circle_post DROP CONSTRAINT IF EXISTS circle_post_body_check;
ALTER TABLE milavn_circle.circle_post ADD CONSTRAINT circle_post_body_check
  CHECK (length(body) <= 1000 AND (length(body) >= 1 OR photo_ref IS NOT NULL OR doc_ref IS NOT NULL));
