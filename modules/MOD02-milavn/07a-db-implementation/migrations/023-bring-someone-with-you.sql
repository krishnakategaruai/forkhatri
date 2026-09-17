-- 023 — Bringing someone with you (FR114), and a waitlist that keeps a party together.
--
-- WHY (2026-09-17, owner's pick from the competitor research): every comparable product treats
-- "+1" as a first-class part of an RSVP — Meetup counts up to 5 guests per RSVP against the
-- capacity, Partiful makes plus-ones an object of their own (hosts can even require their names),
-- and 222 offers a plus-one specifically so nobody has to walk in alone. In this community an
-- activity is rarely attended alone: a cousin, a spouse, a child comes along. Until now Milavn
-- could only record that intention as a note ("coming with: family") which no capacity maths ever
-- saw, so a host with 12 spots could have 20 people arrive.
--
--   occurrence.max_guests_per_member   how many extra people each person may bring (host's choice, 0 = none)
--   participation.guest_count          how many that member is actually bringing
--   spots_taken(occurrence)            people + their guests — the number capacity is judged against
--   promote_next_waitlisted            promotes the first waitlisted party that FITS the freed room
--
-- The waitlist rule matches Meetup's: a party is skipped (not broken up, and not moved down the
-- queue) until enough spots open for all of them, so nobody is told "you are in but your wife is
-- not". Guests are for free activities only — a paid spot is per person and is bought per person.

ALTER TABLE milavn_activity.occurrence
  ADD COLUMN IF NOT EXISTS max_guests_per_member smallint NOT NULL DEFAULT 0;
ALTER TABLE milavn_activity.participation
  ADD COLUMN IF NOT EXISTS guest_count smallint NOT NULL DEFAULT 0;

DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence
    ADD CONSTRAINT occurrence_max_guests_sane CHECK (max_guests_per_member BETWEEN 0 AND 4);
EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE milavn_activity.participation
    ADD CONSTRAINT participation_guest_count_sane CHECK (guest_count BETWEEN 0 AND 4);
EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
END $$;

-- [FR114] What capacity is actually judged against: the people coming, plus the people they bring.
CREATE OR REPLACE FUNCTION milavn_activity.spots_taken(p_occurrence_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT coalesce(sum(1 + guest_count), 0)::integer FROM milavn_activity.participation
  WHERE occurrence_id = p_occurrence_id AND status IN ('going', 'checked_in', 'attended');
$$;

-- [FR114] How many guests are coming in total — shown next to the going count, never per person.
CREATE OR REPLACE FUNCTION milavn_activity.guest_total(p_occurrence_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT coalesce(sum(guest_count), 0)::integer FROM milavn_activity.participation
  WHERE occurrence_id = p_occurrence_id AND status IN ('going', 'checked_in', 'attended');
$$;

-- [FR114/TR39] Promotion now asks "does this whole party fit?" and moves on to the next person if
-- not — the party keeps its place in the queue rather than being split or pushed to the back.
CREATE OR REPLACE FUNCTION milavn_activity.promote_next_waitlisted(p_occurrence_id uuid, p_actor uuid)
RETURNS TABLE(participation_id uuid, member_id uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE r record; free_spots integer; cap integer;
BEGIN
  SELECT o.capacity INTO cap FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
  IF cap IS NULL THEN
    free_spots := NULL;
  ELSE
    free_spots := cap - milavn_activity.spots_taken(p_occurrence_id) - milavn_activity.held_spot_count(p_occurrence_id);
    IF free_spots <= 0 THEN RETURN; END IF;
  END IF;
  FOR r IN
    SELECT p.id, p.member_id, p.guest_count
    FROM milavn_activity.participation p
    WHERE p.occurrence_id = p_occurrence_id AND p.status = 'waitlisted'
    ORDER BY p.waitlist_position ASC
  LOOP
    IF free_spots IS NULL OR (1 + r.guest_count) <= free_spots THEN
      UPDATE milavn_activity.participation SET status = 'going', waitlist_position = NULL, updated_at = now() WHERE id = r.id;
      INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
      VALUES (r.id, 'waitlisted', 'going', p_actor);
      participation_id := r.id; member_id := r.member_id;
      RETURN NEXT;
      RETURN;
    END IF;
  END LOOP;
END;
$$;

-- [FR112] A regular's kept spot counts the same way (they may bring people too).
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
    IF occ.capacity IS NOT NULL AND milavn_activity.spots_taken(occ.id) >= occ.capacity THEN
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

GRANT EXECUTE ON FUNCTION milavn_activity.spots_taken(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.guest_total(uuid) TO milavn_app;
