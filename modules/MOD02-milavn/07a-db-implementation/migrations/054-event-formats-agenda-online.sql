-- 054 — Event formats, agenda and speakers, expo stalls, tournament teams, online join and recording, exact venue pin
-- (Phase 2, Step 5 of PLAN-places-events-groups.md). Owner decision: no in-app video. Online sessions use the
-- organizer's own Google Meet / Zoom / Teams / YouTube link; offline events give the exact venue with a map.
--
-- Adds, without rewriting anything earlier except set_event_venue (it now forgets the map pin when the address changes):
--   * occurrence.event_format     what kind of event it is (workshop, webinar, tournament ...), separate from the category
--   * occurrence.team_size_max    tournaments: most people in one team (captain included); NULL = no team registration
--   * event_speaker               speaker cards: name, short bio, optional link to their Milavn member profile
--   * event_session               the agenda: time, title, details, speakers. Multi-day events are one occurrence
--                                 (time_start .. time_end), so one booking covers every day.
--   * event_stall                 expo stalls / exhibitors: stall number, name, description
--   * event_team, event_team_member  tournament teams. Only people with a confirmed spot (going / checked in / attended)
--                                 can be on a team, so the event's capacity and tickets are respected by construction;
--                                 one team per person per event; the organizer's size limit is checked under a lock.
--   * occurrence_venue.venue_lat/venue_lng   the exact map pin for the venue (same protection as the address)
--   * occurrence_followup         recording / notes links after the event (same protection as the venue)
--   * record_online_join()        tapping Join on an online or hybrid event marks the person checked in
--
-- Reading: agenda, speakers and stalls are as visible as the event itself (RLS defers to the occurrence's own policy).
-- Writing: agenda, speakers and stalls only by the organizer or a co-organizer (RLS). Teams, follow-up and online join
-- go through definer functions that check the acting member themselves.

-- ---------------------------------------------------------------------------------------------------------------------
ALTER TABLE milavn_activity.occurrence
  ADD COLUMN IF NOT EXISTS event_format  text,
  ADD COLUMN IF NOT EXISTS team_size_max smallint;
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_event_format_values CHECK (event_format IS NULL OR event_format IN (
    'workshop', 'webinar', 'talk', 'panel', 'masterclass', 'book_club', 'skill_share', 'office_hours', 'bootcamp', 'conference',
    'expo', 'cultural_night', 'tournament', 'festival', 'satsang', 'darshan_stream', 'town_hall', 'volunteering', 'trip', 'meetup'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_team_size_tournament_only CHECK (
    team_size_max IS NULL OR (event_format = 'tournament' AND team_size_max BETWEEN 2 AND 50));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS occurrence_event_format_idx ON milavn_activity.occurrence (event_format) WHERE event_format IS NOT NULL;

-- The acting member, as every function below reads it.
CREATE OR REPLACE FUNCTION milavn_activity.acting_member()
RETURNS uuid LANGUAGE sql STABLE
SET search_path = pg_catalog AS $$
  SELECT nullif(current_setting('milavn.member_id', true), '')::uuid;
$$;
GRANT EXECUTE ON FUNCTION milavn_activity.acting_member() TO milavn_app;

-- ---------------------------------------------------------------------------------------------------------------------
-- Speakers, agenda, stalls.
CREATE TABLE IF NOT EXISTS milavn_activity.event_speaker (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  name          text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 80),
  bio           text CHECK (bio IS NULL OR length(bio) <= 300),
  member_id     uuid,                                  -- optional: their Milavn member profile
  position      integer NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS event_speaker_occurrence_idx ON milavn_activity.event_speaker (occurrence_id, position);

CREATE TABLE IF NOT EXISTS milavn_activity.event_session (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  starts_at     timestamptz NOT NULL,
  ends_at       timestamptz,
  title         text NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 140),
  details       text CHECK (details IS NULL OR length(details) <= 400),
  speaker_ids   uuid[] NOT NULL DEFAULT '{}',
  created_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT event_session_ends_after_start CHECK (ends_at IS NULL OR ends_at > starts_at),
  CONSTRAINT event_session_speakers_few CHECK (cardinality(speaker_ids) <= 8)
);
CREATE INDEX IF NOT EXISTS event_session_occurrence_idx ON milavn_activity.event_session (occurrence_id, starts_at);

CREATE TABLE IF NOT EXISTS milavn_activity.event_stall (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  stall_number  text CHECK (stall_number IS NULL OR length(btrim(stall_number)) BETWEEN 1 AND 20),
  name          text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 80),
  description   text CHECK (description IS NULL OR length(description) <= 300),
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS event_stall_number_unique ON milavn_activity.event_stall (occurrence_id, lower(btrim(stall_number))) WHERE stall_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS event_stall_occurrence_idx ON milavn_activity.event_stall (occurrence_id, created_at);

-- A session's speakers must be this event's speakers, and the session must fall inside the event (start .. end, or the
-- start day when there is no end). Checked here so no path around the API can break it.
CREATE OR REPLACE FUNCTION milavn_activity.event_session_check()
RETURNS trigger LANGUAGE plpgsql
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE o record; last_end timestamptz;
BEGIN
  SELECT time_start, time_end INTO o FROM milavn_activity.occurrence WHERE id = NEW.occurrence_id;
  last_end := coalesce(o.time_end, o.time_start + interval '1 day');
  IF NEW.starts_at < o.time_start - interval '1 minute' OR NEW.starts_at >= last_end OR (NEW.ends_at IS NOT NULL AND NEW.ends_at > last_end + interval '1 minute') THEN
    RAISE EXCEPTION 'session outside the event' USING ERRCODE = 'check_violation', CONSTRAINT = 'event_session_inside_event';
  END IF;
  IF EXISTS (SELECT 1 FROM unnest(NEW.speaker_ids) s(id)
             WHERE NOT EXISTS (SELECT 1 FROM milavn_activity.event_speaker sp WHERE sp.id = s.id AND sp.occurrence_id = NEW.occurrence_id)) THEN
    RAISE EXCEPTION 'speaker of another event' USING ERRCODE = 'check_violation', CONSTRAINT = 'event_session_own_speakers';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS event_session_check ON milavn_activity.event_session;
CREATE TRIGGER event_session_check BEFORE INSERT OR UPDATE ON milavn_activity.event_session
  FOR EACH ROW EXECUTE FUNCTION milavn_activity.event_session_check();

-- A removed speaker leaves every session they were on.
CREATE OR REPLACE FUNCTION milavn_activity.event_speaker_removed()
RETURNS trigger LANGUAGE plpgsql
SET search_path = milavn_activity, pg_catalog AS $$
BEGIN
  UPDATE milavn_activity.event_session SET speaker_ids = array_remove(speaker_ids, OLD.id)
  WHERE occurrence_id = OLD.occurrence_id AND OLD.id = ANY (speaker_ids);
  RETURN OLD;
END;
$$;
DROP TRIGGER IF EXISTS event_speaker_removed ON milavn_activity.event_speaker;
CREATE TRIGGER event_speaker_removed AFTER DELETE ON milavn_activity.event_speaker
  FOR EACH ROW EXECUTE FUNCTION milavn_activity.event_speaker_removed();

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['event_speaker', 'event_session', 'event_stall'] LOOP
    EXECUTE format('ALTER TABLE milavn_activity.%I ENABLE ROW LEVEL SECURITY', t);
    -- Read: whoever can see the event (the sub-select runs under the occurrence's own visibility policy).
    EXECUTE format('DROP POLICY IF EXISTS %I ON milavn_activity.%I', t || '_read', t);
    EXECUTE format('CREATE POLICY %I ON milavn_activity.%I FOR SELECT USING (EXISTS (SELECT 1 FROM milavn_activity.occurrence o WHERE o.id = occurrence_id))', t || '_read', t);
    -- Write: the organizer and co-organizers only.
    EXECUTE format('DROP POLICY IF EXISTS %I ON milavn_activity.%I', t || '_organizer_insert', t);
    EXECUTE format('CREATE POLICY %I ON milavn_activity.%I FOR INSERT WITH CHECK (milavn_activity.is_event_organizer(occurrence_id, milavn_activity.acting_member()))', t || '_organizer_insert', t);
    EXECUTE format('DROP POLICY IF EXISTS %I ON milavn_activity.%I', t || '_organizer_update', t);
    EXECUTE format('CREATE POLICY %I ON milavn_activity.%I FOR UPDATE USING (milavn_activity.is_event_organizer(occurrence_id, milavn_activity.acting_member())) WITH CHECK (milavn_activity.is_event_organizer(occurrence_id, milavn_activity.acting_member()))', t || '_organizer_update', t);
    EXECUTE format('DROP POLICY IF EXISTS %I ON milavn_activity.%I', t || '_organizer_delete', t);
    EXECUTE format('CREATE POLICY %I ON milavn_activity.%I FOR DELETE USING (milavn_activity.is_event_organizer(occurrence_id, milavn_activity.acting_member()))', t || '_organizer_delete', t);
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON milavn_activity.%I TO milavn_app', t);
  END LOOP;
END $$;

-- The speaker-removed trigger rewrites sessions as the organizer, which the update policy already allows.

-- Whether a member id is a Milavn member (for the speaker's profile link). Says nothing else about them.
CREATE OR REPLACE FUNCTION milavn_activity.is_milavn_member(p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_profile, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_profile.member_profile WHERE member_id = p_member_id);
$$;
REVOKE ALL ON FUNCTION milavn_activity.is_milavn_member(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.is_milavn_member(uuid) TO milavn_app;

-- ---------------------------------------------------------------------------------------------------------------------
-- Tournament teams.
CREATE TABLE IF NOT EXISTS milavn_activity.event_team (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id     uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  name              text NOT NULL CHECK (length(btrim(name)) BETWEEN 2 AND 60),
  captain_member_id uuid NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS event_team_name_unique ON milavn_activity.event_team (occurrence_id, lower(btrim(name)));

CREATE TABLE IF NOT EXISTS milavn_activity.event_team_member (
  team_id       uuid NOT NULL REFERENCES milavn_activity.event_team(id) ON DELETE CASCADE,
  occurrence_id uuid NOT NULL,
  member_id     uuid NOT NULL,
  joined_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (team_id, member_id),
  CONSTRAINT event_team_member_one_team UNIQUE (occurrence_id, member_id)
);
ALTER TABLE milavn_activity.event_team ENABLE ROW LEVEL SECURITY;        -- no policy: definer functions only
ALTER TABLE milavn_activity.event_team_member ENABLE ROW LEVEL SECURITY; -- no policy: definer functions only

CREATE OR REPLACE FUNCTION milavn_activity.has_confirmed_spot(p_occurrence_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_activity.participation p
                 WHERE p.occurrence_id = p_occurrence_id AND p.member_id = p_member_id AND p.status IN ('going', 'checked_in', 'attended'));
$$;

-- Leaving a team (or losing the spot): the member goes; a captain hands over to the longest-standing member,
-- and a team nobody is left in is removed.
CREATE OR REPLACE FUNCTION milavn_activity.team_drop_member(p_team_id uuid, p_member_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE nxt uuid;
BEGIN
  DELETE FROM milavn_activity.event_team_member WHERE team_id = p_team_id AND member_id = p_member_id;
  IF EXISTS (SELECT 1 FROM milavn_activity.event_team WHERE id = p_team_id AND captain_member_id = p_member_id) THEN
    SELECT member_id INTO nxt FROM milavn_activity.event_team_member WHERE team_id = p_team_id ORDER BY joined_at, member_id LIMIT 1;
    IF nxt IS NULL THEN
      DELETE FROM milavn_activity.event_team WHERE id = p_team_id;
    ELSE
      UPDATE milavn_activity.event_team SET captain_member_id = nxt WHERE id = p_team_id;
    END IF;
  ELSIF NOT EXISTS (SELECT 1 FROM milavn_activity.event_team_member WHERE team_id = p_team_id) THEN
    DELETE FROM milavn_activity.event_team WHERE id = p_team_id;
  END IF;
END;
$$;

-- Result: 'ok' | 'not_allowed' | 'not_found' | 'no_teams' | 'not_confirmed' | 'in_a_team' | 'duplicate' | 'invalid' | 'cancelled'
CREATE OR REPLACE FUNCTION milavn_activity.team_register(p_occurrence_id uuid, p_actor uuid, p_name text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE o record; tid uuid;
BEGIN
  IF p_actor IS NULL OR p_actor IS DISTINCT FROM milavn_activity.acting_member() THEN RETURN 'not_allowed'; END IF;
  SELECT status::text AS status, event_format, team_size_max INTO o FROM milavn_activity.occurrence WHERE id = p_occurrence_id;
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  IF o.status = 'cancelled' THEN RETURN 'cancelled'; END IF;
  IF o.event_format IS DISTINCT FROM 'tournament' OR o.team_size_max IS NULL THEN RETURN 'no_teams'; END IF;
  IF NOT milavn_activity.has_confirmed_spot(p_occurrence_id, p_actor) THEN RETURN 'not_confirmed'; END IF;
  PERFORM pg_advisory_xact_lock(hashtext('team:' || p_occurrence_id::text));
  IF EXISTS (SELECT 1 FROM milavn_activity.event_team_member WHERE occurrence_id = p_occurrence_id AND member_id = p_actor) THEN RETURN 'in_a_team'; END IF;
  BEGIN
    INSERT INTO milavn_activity.event_team (occurrence_id, name, captain_member_id) VALUES (p_occurrence_id, btrim(p_name), p_actor) RETURNING id INTO tid;
  EXCEPTION WHEN unique_violation THEN RETURN 'duplicate';
            WHEN check_violation THEN RETURN 'invalid';
  END;
  INSERT INTO milavn_activity.event_team_member (team_id, occurrence_id, member_id) VALUES (tid, p_occurrence_id, p_actor);
  RETURN 'ok';
END;
$$;

-- Result: 'ok' | 'not_allowed' | 'not_found' | 'not_confirmed' | 'in_a_team' | 'team_full' | 'cancelled'
CREATE OR REPLACE FUNCTION milavn_activity.team_join(p_team_id uuid, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE tm record; o record; n integer;
BEGIN
  IF p_actor IS NULL OR p_actor IS DISTINCT FROM milavn_activity.acting_member() THEN RETURN 'not_allowed'; END IF;
  SELECT id, occurrence_id INTO tm FROM milavn_activity.event_team WHERE id = p_team_id;
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  SELECT status::text AS status, team_size_max INTO o FROM milavn_activity.occurrence WHERE id = tm.occurrence_id;
  IF o.status = 'cancelled' THEN RETURN 'cancelled'; END IF;
  IF NOT milavn_activity.has_confirmed_spot(tm.occurrence_id, p_actor) THEN RETURN 'not_confirmed'; END IF;
  PERFORM pg_advisory_xact_lock(hashtext('team:' || tm.occurrence_id::text));
  IF EXISTS (SELECT 1 FROM milavn_activity.event_team_member WHERE occurrence_id = tm.occurrence_id AND member_id = p_actor) THEN RETURN 'in_a_team'; END IF;
  SELECT count(*) INTO n FROM milavn_activity.event_team_member WHERE team_id = p_team_id;
  IF n >= coalesce(o.team_size_max, 0) THEN RETURN 'team_full'; END IF;
  INSERT INTO milavn_activity.event_team_member (team_id, occurrence_id, member_id) VALUES (p_team_id, tm.occurrence_id, p_actor);
  RETURN 'ok';
END;
$$;

-- The member themselves, their captain, or an organizer. Result: 'ok' | 'not_allowed' | 'not_found'
CREATE OR REPLACE FUNCTION milavn_activity.team_remove(p_team_id uuid, p_actor uuid, p_member_id uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE tm record;
BEGIN
  IF p_actor IS NULL OR p_actor IS DISTINCT FROM milavn_activity.acting_member() THEN RETURN 'not_allowed'; END IF;
  SELECT id, occurrence_id, captain_member_id INTO tm FROM milavn_activity.event_team WHERE id = p_team_id;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM milavn_activity.event_team_member WHERE team_id = p_team_id AND member_id = p_member_id) THEN RETURN 'not_found'; END IF;
  IF p_actor <> p_member_id AND p_actor <> tm.captain_member_id AND NOT milavn_activity.is_event_organizer(tm.occurrence_id, p_actor) THEN RETURN 'not_allowed'; END IF;
  PERFORM pg_advisory_xact_lock(hashtext('team:' || tm.occurrence_id::text));
  PERFORM milavn_activity.team_drop_member(p_team_id, p_member_id);
  RETURN 'ok';
END;
$$;

-- What a member sees: every team's name and size; the names of who is in which team only for people with a confirmed
-- spot and the organizers (the same rule as the attendee list being private to everyone else).
CREATE OR REPLACE FUNCTION milavn_activity.teams_for(p_occurrence_id uuid, p_actor uuid)
RETURNS TABLE (team_id uuid, name text, captain_member_id uuid, size integer, member_ids uuid[])
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT t.id, t.name,
         CASE WHEN milavn_activity.can_see_venue(p_occurrence_id, p_actor) THEN t.captain_member_id END,
         (SELECT count(*)::integer FROM milavn_activity.event_team_member m WHERE m.team_id = t.id),
         CASE WHEN milavn_activity.can_see_venue(p_occurrence_id, p_actor)
              THEN (SELECT array_agg(m.member_id ORDER BY m.joined_at, m.member_id) FROM milavn_activity.event_team_member m WHERE m.team_id = t.id) END
  FROM milavn_activity.event_team t
  WHERE t.occurrence_id = p_occurrence_id AND p_actor IS NOT DISTINCT FROM milavn_activity.acting_member()
  ORDER BY t.created_at, t.id;
$$;

CREATE OR REPLACE FUNCTION milavn_activity.my_team(p_occurrence_id uuid, p_actor uuid)
RETURNS uuid LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT team_id FROM milavn_activity.event_team_member
  WHERE occurrence_id = p_occurrence_id AND member_id = p_actor AND p_actor IS NOT DISTINCT FROM milavn_activity.acting_member();
$$;

-- A person who gives up their spot (or is waitlisted, or cancelled) leaves their team at once, so a team never holds
-- someone without a spot. Runs as the owner: it touches team rows the member could not write directly.
CREATE OR REPLACE FUNCTION milavn_activity.participation_leaves_team()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE tid uuid;
BEGIN
  IF NEW.status IN ('going', 'checked_in', 'attended') THEN RETURN NEW; END IF;
  SELECT team_id INTO tid FROM milavn_activity.event_team_member WHERE occurrence_id = NEW.occurrence_id AND member_id = NEW.member_id;
  IF tid IS NOT NULL THEN
    PERFORM milavn_activity.team_drop_member(tid, NEW.member_id);
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS participation_leaves_team ON milavn_activity.participation;
CREATE TRIGGER participation_leaves_team AFTER UPDATE OF status ON milavn_activity.participation
  FOR EACH ROW WHEN (OLD.status IS DISTINCT FROM NEW.status) EXECUTE FUNCTION milavn_activity.participation_leaves_team();

-- The team size can only be lowered to the biggest team there already is.
CREATE OR REPLACE FUNCTION milavn_activity.team_size_not_below_teams()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE biggest integer;
BEGIN
  SELECT coalesce(max(c), 0) INTO biggest FROM (SELECT count(*) AS c FROM milavn_activity.event_team_member WHERE occurrence_id = NEW.id GROUP BY team_id) x;
  IF biggest > 0 AND (NEW.team_size_max IS NULL OR NEW.team_size_max < biggest) THEN
    RAISE EXCEPTION 'team size below an existing team' USING ERRCODE = 'check_violation', CONSTRAINT = 'occurrence_team_size_not_below_teams';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS team_size_not_below_teams ON milavn_activity.occurrence;
CREATE TRIGGER team_size_not_below_teams BEFORE UPDATE OF team_size_max, event_format ON milavn_activity.occurrence
  FOR EACH ROW WHEN (OLD.team_size_max IS DISTINCT FROM NEW.team_size_max OR OLD.event_format IS DISTINCT FROM NEW.event_format)
  EXECUTE FUNCTION milavn_activity.team_size_not_below_teams();

-- ---------------------------------------------------------------------------------------------------------------------
-- Exact venue pin. Same table, so the same row-level rule (organizers and confirmed attendees only) covers it.
ALTER TABLE milavn_activity.occurrence_venue
  ADD COLUMN IF NOT EXISTS venue_lat double precision CHECK (venue_lat IS NULL OR venue_lat BETWEEN 6 AND 38),
  ADD COLUMN IF NOT EXISTS venue_lng double precision CHECK (venue_lng IS NULL OR venue_lng BETWEEN 67 AND 98.5);

-- Unchanged from 051 except that a changed address forgets the old pin (it is looked up again for the new address).
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
    SET venue_address = EXCLUDED.venue_address, venue_notes = EXCLUDED.venue_notes, join_link = EXCLUDED.join_link, updated_at = now(),
        venue_lat = CASE WHEN occurrence_venue.venue_address IS NOT DISTINCT FROM EXCLUDED.venue_address THEN occurrence_venue.venue_lat END,
        venue_lng = CASE WHEN occurrence_venue.venue_address IS NOT DISTINCT FROM EXCLUDED.venue_address THEN occurrence_venue.venue_lng END;
  RETURN 'ok';
END;
$$;

-- Organizer / co-organizer only; the address must still be the one the point was looked up for.
CREATE OR REPLACE FUNCTION milavn_activity.set_venue_point(p_occurrence_id uuid, p_actor uuid, p_address text, p_lat double precision, p_lng double precision)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM milavn_activity.acting_member() OR NOT milavn_activity.is_event_organizer(p_occurrence_id, p_actor) THEN RETURN 'not_allowed'; END IF;
  UPDATE milavn_activity.occurrence_venue SET venue_lat = p_lat, venue_lng = p_lng
  WHERE occurrence_id = p_occurrence_id AND venue_address IS NOT DISTINCT FROM nullif(btrim(p_address), '');
  RETURN CASE WHEN FOUND THEN 'ok' ELSE 'changed' END;
EXCEPTION WHEN check_violation THEN RETURN 'invalid';
END;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
-- Recording / notes after the event: the same people who could see the venue.
CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_followup (
  occurrence_id uuid PRIMARY KEY REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  recording_url text CHECK (recording_url IS NULL OR (length(recording_url) <= 500 AND recording_url ~* '^https://[^\s]+$')),
  notes_url     text CHECK (notes_url IS NULL OR (length(notes_url) <= 500 AND notes_url ~* '^https://[^\s]+$')),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE milavn_activity.occurrence_followup ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_followup_confirmed_only ON milavn_activity.occurrence_followup;
CREATE POLICY occurrence_followup_confirmed_only ON milavn_activity.occurrence_followup
  FOR SELECT USING (milavn_activity.can_see_venue(occurrence_id, milavn_activity.acting_member()));
GRANT SELECT ON milavn_activity.occurrence_followup TO milavn_app;

-- 'ok' | 'not_allowed' | 'not_found' | 'not_yet' (before the start) | 'invalid'
CREATE OR REPLACE FUNCTION milavn_activity.set_event_followup(p_occurrence_id uuid, p_actor uuid, p_recording text, p_notes text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE st timestamptz;
BEGIN
  IF p_actor IS DISTINCT FROM milavn_activity.acting_member() THEN RETURN 'not_allowed'; END IF;
  SELECT time_start INTO st FROM milavn_activity.occurrence WHERE id = p_occurrence_id;
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  IF NOT milavn_activity.is_event_organizer(p_occurrence_id, p_actor) THEN RETURN 'not_allowed'; END IF;
  IF now() < st THEN RETURN 'not_yet'; END IF;
  INSERT INTO milavn_activity.occurrence_followup (occurrence_id, recording_url, notes_url)
  VALUES (p_occurrence_id, nullif(btrim(p_recording), ''), nullif(btrim(p_notes), ''))
  ON CONFLICT (occurrence_id) DO UPDATE SET recording_url = EXCLUDED.recording_url, notes_url = EXCLUDED.notes_url, updated_at = now();
  RETURN 'ok';
EXCEPTION WHEN check_violation THEN RETURN 'invalid';
END;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
-- Tapping Join on an online / hybrid event: a confirmed attendee is marked checked in, from p_open_minutes before the
-- start until the end (or three hours after the start when no end was given). The window length is configuration,
-- passed in by the service. Result: 'checked_in' | 'already' | 'not_confirmed' | 'not_open' | 'ended' | 'not_online' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_activity.record_online_join(p_occurrence_id uuid, p_actor uuid, p_open_minutes integer)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE o record; p record;
BEGIN
  IF p_actor IS NULL OR p_actor IS DISTINCT FROM milavn_activity.acting_member() THEN RETURN 'not_allowed'; END IF;
  SELECT time_start, time_end, status::text AS status, attendance_mode INTO o FROM milavn_activity.occurrence WHERE id = p_occurrence_id;
  IF NOT FOUND OR o.status = 'cancelled' THEN RETURN 'not_found'; END IF;
  IF o.attendance_mode NOT IN ('online', 'hybrid') THEN RETURN 'not_online'; END IF;
  IF now() < o.time_start - make_interval(mins => greatest(p_open_minutes, 0)) THEN RETURN 'not_open'; END IF;
  IF now() > coalesce(o.time_end, o.time_start + interval '3 hours') THEN RETURN 'ended'; END IF;
  SELECT id, status::text AS status INTO p FROM milavn_activity.participation WHERE occurrence_id = p_occurrence_id AND member_id = p_actor FOR UPDATE;
  IF NOT FOUND OR p.status NOT IN ('going', 'checked_in', 'attended') THEN RETURN 'not_confirmed'; END IF;
  IF p.status <> 'going' THEN RETURN 'already'; END IF;
  UPDATE milavn_activity.participation SET status = 'checked_in', checked_in_at = coalesce(checked_in_at, now()), updated_at = now() WHERE id = p.id;
  INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
  VALUES (p.id, 'going', 'checked_in', p_actor);
  RETURN 'checked_in';
END;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
REVOKE ALL ON FUNCTION milavn_activity.has_confirmed_spot(uuid, uuid), milavn_activity.team_drop_member(uuid, uuid),
  milavn_activity.team_register(uuid, uuid, text), milavn_activity.team_join(uuid, uuid), milavn_activity.team_remove(uuid, uuid, uuid),
  milavn_activity.teams_for(uuid, uuid), milavn_activity.my_team(uuid, uuid), milavn_activity.participation_leaves_team(),
  milavn_activity.team_size_not_below_teams(), milavn_activity.set_venue_point(uuid, uuid, text, double precision, double precision),
  milavn_activity.set_event_followup(uuid, uuid, text, text), milavn_activity.record_online_join(uuid, uuid, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.team_register(uuid, uuid, text), milavn_activity.team_join(uuid, uuid),
  milavn_activity.team_remove(uuid, uuid, uuid), milavn_activity.teams_for(uuid, uuid), milavn_activity.my_team(uuid, uuid),
  milavn_activity.set_venue_point(uuid, uuid, text, double precision, double precision), milavn_activity.set_event_followup(uuid, uuid, text, text),
  milavn_activity.record_online_join(uuid, uuid, integer), milavn_activity.has_confirmed_spot(uuid, uuid) TO milavn_app;
-- set_event_venue keeps the grants it got in 051 (CREATE OR REPLACE preserves them).
