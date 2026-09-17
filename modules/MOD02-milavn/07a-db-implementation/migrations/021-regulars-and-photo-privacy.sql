-- 021 — Regulars (FR112) and photo privacy (FR113).
--
-- Research (RESEARCH-BEHAVIOUR-2026.md §1.1, §1.5, §1.9): friendships come from repeated time together
-- (Hall 2019); habits form in a stable context (Wood & Neal 2007); a warm "welcome back" after a miss was the best
-- of 54 gym interventions while broken streaks hurt (Milkman et al. 2021; Silverman & Barasch 2023). Identifiable
-- photos are personal data and consent to take a photo is not consent to publish it (DPDP Rules 2025); online photo
-- abuse is a real harm for women in South Asia (Sambasivan et al. 2018/2019).
--
--   activity.series_regular        a member keeps a spot in every new date of a free series (opt-in, opt-out any time)
--   keep_regular_spots(occurrence) gives regulars their spot (or a waitlist place) when a date is added
--   series_recent_attendance       "you've been to X of the last Y" — for the member themselves only, never a streak
--   claim_reminders                + missed_last: the three-day reminder welcomes someone back after a missed date
--   activity.photo_preference      "please don't include me in photos"
--   photo_opt_outs(occurrence)     who asked not to be pictured, shown only to people who were there
--   request_photo_removal(photo)   anyone who can see a photo can take it down at once; the uploader is told

-- ---- regulars --------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS milavn_activity.series_regular (
  member_id   uuid NOT NULL,
  activity_id uuid NOT NULL REFERENCES milavn_activity.activity(id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, activity_id)
);
ALTER TABLE milavn_activity.series_regular ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS series_regular_self ON milavn_activity.series_regular;
CREATE POLICY series_regular_self ON milavn_activity.series_regular
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, DELETE ON milavn_activity.series_regular TO milavn_app;

CREATE OR REPLACE FUNCTION milavn_activity.keep_regular_spots(p_occurrence_id uuid)
RETURNS TABLE (kept_member_id uuid, kept_status text)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
#variable_conflict use_column
DECLARE occ record; r record; pos integer; pid uuid;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext(p_occurrence_id::text));
  SELECT o.id, o.activity_id, o.capacity, o.price_paise, o.status::text AS st, o.time_start, o.creator_member_id
    INTO occ FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
  -- Free, active, future dates of a series only: a paid spot is never taken on someone's behalf.
  IF NOT FOUND OR occ.activity_id IS NULL OR occ.st <> 'active' OR occ.price_paise IS NOT NULL OR occ.time_start <= now() THEN
    RETURN;
  END IF;
  FOR r IN
    SELECT sr.member_id AS m FROM milavn_activity.series_regular sr
    WHERE sr.activity_id = occ.activity_id AND sr.member_id <> occ.creator_member_id
      AND NOT EXISTS (SELECT 1 FROM milavn_activity.participation p WHERE p.occurrence_id = occ.id AND p.member_id = sr.member_id)
      AND NOT milavn_safety.is_blocked_either_way(sr.member_id, occ.creator_member_id)
    ORDER BY sr.created_at
  LOOP
    pid := gen_random_uuid();
    IF occ.capacity IS NOT NULL AND milavn_activity.going_count(occ.id) >= occ.capacity THEN
      SELECT coalesce(max(p.waitlist_position), 0) + 1 INTO pos FROM milavn_activity.participation p WHERE p.occurrence_id = occ.id AND p.status = 'waitlisted';
      INSERT INTO milavn_activity.participation (id, occurrence_id, member_id, status, waitlist_position) VALUES (pid, occ.id, r.m, 'waitlisted', pos);
      INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id) VALUES (pid, NULL, 'waitlisted', r.m);
      kept_member_id := r.m; kept_status := 'waitlisted';
    ELSE
      INSERT INTO milavn_activity.participation (id, occurrence_id, member_id, status) VALUES (pid, occ.id, r.m, 'going');
      INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id) VALUES (pid, NULL, 'going', r.m);
      kept_member_id := r.m; kept_status := 'going';
    END IF;
    RETURN NEXT;
  END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION milavn_activity.series_recent_attendance(p_member_id uuid, p_activity_id uuid)
RETURNS TABLE (attended integer, total integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  WITH recent AS (
    SELECT o.id FROM milavn_activity.occurrence o
    WHERE o.activity_id = p_activity_id AND o.status = 'active' AND o.time_start < now()
    ORDER BY o.time_start DESC LIMIT 4
  )
  SELECT
    (SELECT count(*)::integer FROM milavn_activity.participation p
      WHERE p.member_id = p_member_id AND p.occurrence_id IN (SELECT id FROM recent) AND p.status IN ('checked_in', 'attended')),
    (SELECT count(*)::integer FROM recent)
  WHERE p_member_id = current_setting('milavn.member_id', true)::uuid;
$$;

DROP FUNCTION IF EXISTS milavn_notification.claim_reminders(text);
CREATE FUNCTION milavn_notification.claim_reminders(p_kind text)
RETURNS TABLE (member_id uuid, occurrence_id uuid, title text, slug text, time_start timestamptz, locality text,
               plan_travel text, plan_with text, waitlisted integer, paid boolean, missed_last boolean)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, milavn_notification, pg_catalog AS $$
#variable_conflict use_column
DECLARE lo interval; hi interval;
BEGIN
  IF p_kind = 'three_days' THEN lo := interval '66 hours'; hi := interval '78 hours';
  ELSIF p_kind = 'still_coming' THEN lo := interval '20 hours'; hi := interval '28 hours';
  ELSIF p_kind = 'two_hours' THEN lo := interval '90 minutes'; hi := interval '150 minutes';
  ELSE RAISE EXCEPTION 'unknown reminder kind %', p_kind;
  END IF;
  RETURN QUERY
  WITH due AS (
    SELECT p.member_id AS m, o.id AS o_id, o.title AS t, o.canonical_url_slug AS s, o.time_start AS ts,
           COALESCE(o.locality_locality, o.locality_city) AS loc, p.plan_travel AS pt, p.plan_with AS pw,
           (SELECT count(*)::integer FROM milavn_activity.participation w WHERE w.occurrence_id = o.id AND w.status = 'waitlisted') AS wl,
           (o.price_paise IS NOT NULL) AS pd,
           COALESCE((
             SELECT p2.status::text IN ('no_show', 'cancelled')
             FROM milavn_activity.occurrence o2
             JOIN milavn_activity.participation p2 ON p2.occurrence_id = o2.id AND p2.member_id = p.member_id
             WHERE o.activity_id IS NOT NULL AND o2.activity_id = o.activity_id AND o2.time_start < o.time_start AND o2.status = 'active'
             ORDER BY o2.time_start DESC LIMIT 1
           ), false) AS ml
    FROM milavn_activity.participation p
    JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id
    WHERE p.status = 'going' AND o.status = 'active' AND o.creator_member_id <> p.member_id
      AND o.time_start > now() + lo AND o.time_start <= now() + hi
      AND (p_kind <> 'still_coming' OR (p.confirmed_at IS NULL AND p.updated_at < now() - interval '3 hours'))
      AND NOT EXISTS (SELECT 1 FROM milavn_notification.reminder_sent r WHERE r.member_id = p.member_id AND r.occurrence_id = o.id AND r.kind = p_kind)
  ),
  claimed AS (
    INSERT INTO milavn_notification.reminder_sent (member_id, occurrence_id, kind)
    SELECT d.m, d.o_id, p_kind FROM due d
    ON CONFLICT DO NOTHING
    RETURNING reminder_sent.member_id AS cm, reminder_sent.occurrence_id AS co
  )
  SELECT d.m, d.o_id, d.t, d.s, d.ts, d.loc, d.pt, d.pw, d.wl, d.pd, d.ml
  FROM due d JOIN claimed c ON c.cm = d.m AND c.co = d.o_id;
END;
$$;

-- ---- photo privacy ---------------------------------------------------------------

ALTER TABLE milavn_activity.occurrence_photo
  ADD COLUMN IF NOT EXISTS removed_at timestamptz,
  ADD COLUMN IF NOT EXISTS removal_requested_by uuid;

CREATE TABLE IF NOT EXISTS milavn_activity.photo_preference (
  member_id           uuid PRIMARY KEY,
  prefer_not_pictured boolean NOT NULL DEFAULT false,
  updated_at          timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE milavn_activity.photo_preference ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS photo_preference_self ON milavn_activity.photo_preference;
CREATE POLICY photo_preference_self ON milavn_activity.photo_preference
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, UPDATE ON milavn_activity.photo_preference TO milavn_app;

-- Who asked not to be pictured, among the people who were there — shown only to someone who was there too.
CREATE OR REPLACE FUNCTION milavn_activity.photo_opt_outs(p_occurrence_id uuid, p_viewer uuid)
RETURNS TABLE (member_id uuid)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT pp.member_id FROM milavn_activity.photo_preference pp
  WHERE pp.prefer_not_pictured AND pp.member_id <> p_viewer
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND milavn_activity.was_there(p_occurrence_id, p_viewer)
    AND milavn_activity.was_there(p_occurrence_id, pp.member_id);
$$;

-- Anyone who can see a photo can take it down at once. Returns the uploader (to be told), or NULL.
CREATE OR REPLACE FUNCTION milavn_activity.request_photo_removal(p_photo_id uuid, p_member_id uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE ph record;
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN NULL; END IF;
  SELECT id, occurrence_id, member_id INTO ph FROM milavn_activity.occurrence_photo WHERE id = p_photo_id AND removed_at IS NULL;
  IF NOT FOUND OR NOT milavn_activity.can_view_thread(ph.occurrence_id, p_member_id) THEN RETURN NULL; END IF;
  UPDATE milavn_activity.occurrence_photo SET removed_at = now(), removal_requested_by = p_member_id WHERE id = p_photo_id;
  RETURN ph.member_id;
END;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.keep_regular_spots(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.series_recent_attendance(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_notification.claim_reminders(text) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.photo_opt_outs(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.request_photo_removal(uuid, uuid) TO milavn_app;
