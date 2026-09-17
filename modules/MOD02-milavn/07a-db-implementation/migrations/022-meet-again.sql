-- 022 — Would meet again (FR106).
--
-- Research (RESEARCH-BEHAVIOUR-2026.md §1.1): people underestimate how much others liked them after a first
-- conversation (Boothby et al. 2018, "the liking gap"), so they rarely follow up; Meetup's Connections turns a mutual
-- choice after an event into a friendship signal. Milavn keeps it private and mutual only: a pick is never shown to
-- the person picked, there are no counts anywhere, and nothing about it is public (no Match/Like model, FR044).
--
--   milavn_connect.meet_again        a private pick of someone who was at the same activity (visible to the chooser only)
--   milavn_connect.meet_again_told   pairs already told they would both meet again (so toggling never re-notifies)
--   meet_again_candidates(occ, me)   people who were there — shown only to someone who was there, after it started
--   pick_meet_again(occ, me, other)  'picked' | 'mutual' | 'new_mutual' | NULL (not allowed)
--   my_connections(me)               mutual pairs only, newest first, never across a block

CREATE TABLE IF NOT EXISTS milavn_connect.meet_again (
  chooser_member_id uuid NOT NULL,
  chosen_member_id  uuid NOT NULL,
  occurrence_id     uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  created_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chooser_member_id, chosen_member_id),
  CONSTRAINT meet_again_not_self CHECK (chooser_member_id <> chosen_member_id)
);
ALTER TABLE milavn_connect.meet_again ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS meet_again_chooser_read ON milavn_connect.meet_again;
CREATE POLICY meet_again_chooser_read ON milavn_connect.meet_again
  FOR SELECT USING (chooser_member_id = current_setting('milavn.member_id', true)::uuid);
DROP POLICY IF EXISTS meet_again_chooser_delete ON milavn_connect.meet_again;
CREATE POLICY meet_again_chooser_delete ON milavn_connect.meet_again
  FOR DELETE USING (chooser_member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, DELETE ON milavn_connect.meet_again TO milavn_app;

CREATE TABLE IF NOT EXISTS milavn_connect.meet_again_told (
  low_member_id  uuid NOT NULL,
  high_member_id uuid NOT NULL,
  told_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (low_member_id, high_member_id)
);
ALTER TABLE milavn_connect.meet_again_told ENABLE ROW LEVEL SECURITY; -- definer access only

CREATE OR REPLACE FUNCTION milavn_connect.meet_again_candidates(p_occurrence_id uuid, p_viewer uuid)
RETURNS TABLE (member_id uuid, picked boolean)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, milavn_activity, milavn_safety, pg_catalog AS $$
  WITH people AS (
    SELECT o.creator_member_id AS m FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id
    UNION
    SELECT c.member_id FROM milavn_activity.occurrence_co_organizer c WHERE c.occurrence_id = p_occurrence_id AND c.revoked_at IS NULL
    UNION
    SELECT p.member_id FROM milavn_activity.participation p WHERE p.occurrence_id = p_occurrence_id AND p.status IN ('checked_in', 'attended')
  )
  SELECT pe.m,
         EXISTS (SELECT 1 FROM milavn_connect.meet_again x WHERE x.chooser_member_id = p_viewer AND x.chosen_member_id = pe.m)
  FROM people pe
  WHERE p_viewer = current_setting('milavn.member_id', true)::uuid
    AND EXISTS (SELECT 1 FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id AND o.time_start <= now())
    AND milavn_activity.was_there(p_occurrence_id, p_viewer)
    AND pe.m <> p_viewer
    AND NOT milavn_safety.is_blocked_either_way(p_viewer, pe.m);
$$;

CREATE OR REPLACE FUNCTION milavn_connect.pick_meet_again(p_occurrence_id uuid, p_chooser uuid, p_chosen uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_connect, pg_catalog AS $$
DECLARE n integer;
BEGIN
  IF p_chooser IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN NULL; END IF;
  IF NOT EXISTS (SELECT 1 FROM milavn_connect.meet_again_candidates(p_occurrence_id, p_chooser) c WHERE c.member_id = p_chosen) THEN
    RETURN NULL;
  END IF;
  INSERT INTO milavn_connect.meet_again (chooser_member_id, chosen_member_id, occurrence_id)
  VALUES (p_chooser, p_chosen, p_occurrence_id)
  ON CONFLICT (chooser_member_id, chosen_member_id) DO UPDATE SET occurrence_id = EXCLUDED.occurrence_id, created_at = now();
  IF NOT EXISTS (SELECT 1 FROM milavn_connect.meet_again WHERE chooser_member_id = p_chosen AND chosen_member_id = p_chooser) THEN
    RETURN 'picked';
  END IF;
  INSERT INTO milavn_connect.meet_again_told (low_member_id, high_member_id)
  VALUES (LEAST(p_chooser, p_chosen), GREATEST(p_chooser, p_chosen))
  ON CONFLICT DO NOTHING;
  GET DIAGNOSTICS n = ROW_COUNT;
  RETURN CASE WHEN n = 1 THEN 'new_mutual' ELSE 'mutual' END;
END;
$$;

CREATE OR REPLACE FUNCTION milavn_connect.my_connections(p_viewer uuid)
RETURNS TABLE (member_id uuid, occurrence_title text, formed_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, milavn_activity, milavn_safety, pg_catalog AS $$
  SELECT a.chosen_member_id, o.title, GREATEST(a.created_at, b.created_at)
  FROM milavn_connect.meet_again a
  JOIN milavn_connect.meet_again b ON b.chooser_member_id = a.chosen_member_id AND b.chosen_member_id = a.chooser_member_id
  JOIN milavn_activity.occurrence o ON o.id = CASE WHEN a.created_at >= b.created_at THEN a.occurrence_id ELSE b.occurrence_id END
  WHERE a.chooser_member_id = p_viewer
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND NOT milavn_safety.is_blocked_either_way(a.chooser_member_id, a.chosen_member_id)
  ORDER BY 3 DESC;
$$;

GRANT EXECUTE ON FUNCTION milavn_connect.meet_again_candidates(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.pick_meet_again(uuid, uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.my_connections(uuid) TO milavn_app;
