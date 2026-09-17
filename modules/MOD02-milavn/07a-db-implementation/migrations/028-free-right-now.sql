-- 028 — "I'm free right now" (FR119).
--
-- WHY (2026-09-17, owner's pick 8): Couchsurfing's Hangouts exist because most meeting up is not
-- planned a week ahead — someone is free this evening and would rather not spend it alone. Milavn
-- could only answer "what is planned?", never "who is around now?". This is the smallest honest
-- version of that: a member says they are free for the next couple of hours, from which locality,
-- and what they fancy; it is visible only to people who share a circle with them, and it expires by
-- itself. Nothing is stored about where anyone actually is — the member types a locality, exactly
-- like everywhere else in Milavn (FR038/FR041).
--
--   free_now                one row per member, replaced each time, gone when it expires
--   free_now_nearby(viewer) who the viewer can see: shared-circle members only, never blocked pairs

CREATE TABLE IF NOT EXISTS milavn_connect.free_now (
  member_id  uuid PRIMARY KEY,
  until      timestamptz NOT NULL,
  locality   text,
  note       text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT free_now_note_short CHECK (note IS NULL OR length(note) <= 80),
  CONSTRAINT free_now_window_sane CHECK (until > created_at AND until < created_at + interval '12 hours')
);
ALTER TABLE milavn_connect.free_now ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS free_now_self ON milavn_connect.free_now;
CREATE POLICY free_now_self ON milavn_connect.free_now
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, UPDATE, DELETE ON milavn_connect.free_now TO milavn_app;

-- Shared-circle only: the same trust boundary messaging uses, minus the "we were at one activity
-- together" arm — being at one activity with someone is not a reason to know their evenings are free.
CREATE OR REPLACE FUNCTION milavn_connect.free_now_nearby(p_viewer uuid)
RETURNS TABLE (member_id uuid, until timestamptz, locality text, note text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, milavn_circle, milavn_safety, pg_catalog AS $$
  SELECT f.member_id, f.until, f.locality, f.note
  FROM milavn_connect.free_now f
  WHERE f.until > now()
    AND f.member_id <> p_viewer
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND NOT milavn_safety.is_blocked_either_way(p_viewer, f.member_id)
    AND EXISTS (
      SELECT 1 FROM milavn_circle.circle_membership a
      JOIN milavn_circle.circle_membership b ON b.circle_id = a.circle_id AND b.left_at IS NULL
      WHERE a.member_id = p_viewer AND a.left_at IS NULL AND b.member_id = f.member_id
    )
  ORDER BY f.until DESC;
$$;

GRANT EXECUTE ON FUNCTION milavn_connect.free_now_nearby(uuid) TO milavn_app;
