-- 051 — Exact venue per event, shown only after a confirmed spot (Step 2 of PLAN-places-events-groups.md).
--
-- Before: an event had only an approximate place, so "Going" revealed nothing about where to turn up.
-- Now an event can carry, in a separate table the public screens never read:
--   venue_address  the full address people turn up at
--   venue_notes    arrival notes (gate, floor, who to ask for)
--   join_link      the link for online and hybrid events
-- plus occurrence.attendance_mode ('in_person' | 'online' | 'hybrid'), which is not secret.
--
-- Who may read the private part, decided in the database (RLS), not only in the screens:
--   the organizer, a co-organizer, and a person whose spot is confirmed
--   (going, checked in, attended; a paid ticket makes the spot 'going').
-- Interested, waitlisted, cancelled and no-show people, and everyone else, get no row at all.
-- Writing goes through set_event_venue(), which only the organizer or a co-organizer may use.

ALTER TABLE milavn_activity.occurrence
  ADD COLUMN IF NOT EXISTS attendance_mode text NOT NULL DEFAULT 'in_person';
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_attendance_mode_values CHECK (attendance_mode IN ('in_person', 'online', 'hybrid'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_venue (
  occurrence_id uuid PRIMARY KEY REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  venue_address text CHECK (venue_address IS NULL OR length(venue_address) <= 400),
  venue_notes   text CHECK (venue_notes IS NULL OR length(venue_notes) <= 400),
  join_link     text CHECK (join_link IS NULL OR (length(join_link) <= 500 AND join_link ~* '^https://')),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_activity.occurrence_venue IS
  'Exact address, arrival notes and online join link. Readable only by organizers and confirmed attendees (RLS below); never part of any public or discovery read.';

CREATE OR REPLACE FUNCTION milavn_activity.is_event_organizer(p_occurrence_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id AND o.creator_member_id = p_member_id)
      OR EXISTS (SELECT 1 FROM milavn_activity.occurrence_co_organizer c
                 WHERE c.occurrence_id = p_occurrence_id AND c.member_id = p_member_id AND c.revoked_at IS NULL);
$$;

CREATE OR REPLACE FUNCTION milavn_activity.can_see_venue(p_occurrence_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT p_member_id IS NOT NULL AND (
    milavn_activity.is_event_organizer(p_occurrence_id, p_member_id)
    OR EXISTS (SELECT 1 FROM milavn_activity.participation p
               WHERE p.occurrence_id = p_occurrence_id AND p.member_id = p_member_id AND p.status IN ('going', 'checked_in', 'attended'))
  );
$$;

ALTER TABLE milavn_activity.occurrence_venue ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_venue_confirmed_only ON milavn_activity.occurrence_venue;
CREATE POLICY occurrence_venue_confirmed_only ON milavn_activity.occurrence_venue
  FOR SELECT USING (milavn_activity.can_see_venue(occurrence_id, nullif(current_setting('milavn.member_id', true), '')::uuid));
GRANT SELECT ON milavn_activity.occurrence_venue TO milavn_app;

-- Organizer / co-organizer only. Empty text clears a field. 'ok' | 'not_allowed' | 'not_found'
CREATE OR REPLACE FUNCTION milavn_activity.set_event_venue(p_occurrence_id uuid, p_actor uuid, p_address text, p_notes text, p_link text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM nullif(current_setting('milavn.member_id', true), '')::uuid THEN RETURN 'not_allowed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM milavn_activity.occurrence WHERE id = p_occurrence_id) THEN RETURN 'not_found'; END IF;
  IF NOT milavn_activity.is_event_organizer(p_occurrence_id, p_actor) THEN RETURN 'not_allowed'; END IF;
  INSERT INTO milavn_activity.occurrence_venue (occurrence_id, venue_address, venue_notes, join_link)
  VALUES (p_occurrence_id, nullif(btrim(p_address), ''), nullif(btrim(p_notes), ''), nullif(btrim(p_link), ''))
  ON CONFLICT (occurrence_id) DO UPDATE
    SET venue_address = EXCLUDED.venue_address, venue_notes = EXCLUDED.venue_notes, join_link = EXCLUDED.join_link, updated_at = now();
  RETURN 'ok';
END;
$$;
REVOKE ALL ON FUNCTION milavn_activity.set_event_venue(uuid, uuid, text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.set_event_venue(uuid, uuid, text, text, text) TO milavn_app;
REVOKE ALL ON FUNCTION milavn_activity.can_see_venue(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.can_see_venue(uuid, uuid) TO milavn_app;
REVOKE ALL ON FUNCTION milavn_activity.is_event_organizer(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.is_event_organizer(uuid, uuid) TO milavn_app;
