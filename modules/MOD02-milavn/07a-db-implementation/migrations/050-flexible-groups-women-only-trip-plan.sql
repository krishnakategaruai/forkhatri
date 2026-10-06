-- 050 — Flexible groups, an enforced women-only option, and a simple trip plan
-- (PLAN-places-events-groups.md, Step 4; owner approved 2026-10-05).
--
--   1. kind_label      a member's own label for a circle ("Bhajan evening", "Cycling"), shown instead
--                      of the built-in kind. The built-in enum (temple, travel, local, interest...)
--                      stays as the shortcuts; a custom label rides on top of any of them.
--   2. women_only      the creator ticks "Women only" when making a circle. It is fixed at creation.
--   3. member_gender   the member's OWN answer ("I am a woman" / "I am a man"), asked once, only when
--                      someone tries to enter a women-only circle. Neither Milavn's profile nor the
--                      platform identity holds one, so this is the single place it lives. It is
--                      private: only the member can read their own row; other members, organizers
--                      and the API's public profile never see it.
--   4. enforcement     ONE trigger on circle_membership refuses any membership row for a women-only
--                      circle unless the member answered "woman". Every way in (join, approval by
--                      the organizer, accepting an invite, an invite link, add-member, circle
--                      suggestions) ends in that insert, so none of them can bypass it. Inviting an
--                      ineligible member quietly sends nothing, so an inviter never learns anyone's
--                      answer. Error code WO001 / message 'women_only' is mapped by the API.
--   5. trip_stop       the route of a travel circle: ordered stops, each with an optional day and
--                      note. The trip's own dates already live on the circle (035). No cost split.
--
-- Safe to run twice.

-- 1 + 2 ---------------------------------------------------------------------------------------
ALTER TABLE milavn_circle.circle
  ADD COLUMN IF NOT EXISTS kind_label text,
  ADD COLUMN IF NOT EXISTS women_only boolean NOT NULL DEFAULT false;

DO $$ BEGIN
  ALTER TABLE milavn_circle.circle ADD CONSTRAINT circle_kind_label_sane CHECK (kind_label IS NULL OR length(kind_label) BETWEEN 1 AND 40);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 3 -------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS milavn_profile.member_gender (
  member_id   uuid PRIMARY KEY,
  gender      text NOT NULL CONSTRAINT member_gender_known CHECK (gender IN ('woman', 'man')),
  declared_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_profile.member_gender IS
  '050: the member''s own answer, used only to honour women-only circles. Readable by the member alone; the trigger reads it through a SECURITY DEFINER function.';

ALTER TABLE milavn_profile.member_gender ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_gender_self ON milavn_profile.member_gender;
CREATE POLICY member_gender_self ON milavn_profile.member_gender
  USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, UPDATE ON milavn_profile.member_gender TO milavn_app;

-- The answer for the trigger and the invite check (not exposed to the app).
CREATE OR REPLACE FUNCTION milavn_profile.declared_gender(p_member uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_profile, pg_catalog AS $$
  SELECT gender FROM milavn_profile.member_gender WHERE member_id = p_member;
$$;
REVOKE ALL ON FUNCTION milavn_profile.declared_gender(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_profile.declared_gender(uuid) TO milavn_owner;

-- 4 -------------------------------------------------------------------------------------------
-- May this member be in this circle? True for every circle that is not women-only.
CREATE OR REPLACE FUNCTION milavn_circle.may_enter(p_circle_id uuid, p_member uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT NOT coalesce((SELECT c.women_only FROM milavn_circle.circle c WHERE c.id = p_circle_id), false)
         OR coalesce(milavn_profile.declared_gender(p_member), '') = 'woman';
$$;
REVOKE ALL ON FUNCTION milavn_circle.may_enter(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.may_enter(uuid, uuid) TO milavn_app;

CREATE OR REPLACE FUNCTION milavn_circle.enforce_women_only()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
BEGIN
  IF NEW.left_at IS NULL AND NOT milavn_circle.may_enter(NEW.circle_id, NEW.member_id) THEN
    RAISE EXCEPTION 'women_only' USING ERRCODE = 'WO001';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.enforce_women_only() FROM PUBLIC;

DROP TRIGGER IF EXISTS circle_membership_women_only ON milavn_circle.circle_membership;
CREATE TRIGGER circle_membership_women_only
  BEFORE INSERT ON milavn_circle.circle_membership
  FOR EACH ROW EXECUTE FUNCTION milavn_circle.enforce_women_only();

-- A request to join (from an invite or link in an "ask first" circle) from someone who may not
-- enter is refused up front, not left waiting for an organizer to click into the trigger.
CREATE OR REPLACE FUNCTION milavn_circle.file_join_request(p_circle_id uuid, p_member uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
BEGIN
  IF NOT milavn_circle.may_enter(p_circle_id, p_member) THEN
    RAISE EXCEPTION 'women_only' USING ERRCODE = 'WO001';
  END IF;
  IF EXISTS (SELECT 1 FROM milavn_circle.join_request r
              WHERE r.circle_id = p_circle_id AND r.member_id = p_member AND r.status = 'pending') THEN
    RETURN 'already_pending';
  END IF;
  INSERT INTO milavn_circle.join_request (circle_id, member_id, answers) VALUES (p_circle_id, p_member, '{}')
  ON CONFLICT DO NOTHING;
  RETURN 'pending';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.file_join_request(uuid, uuid) FROM PUBLIC;

-- request_to_join (024): same up-front refusal for the ordinary "Join" / "Ask to join" button.
CREATE OR REPLACE FUNCTION milavn_circle.request_to_join(p_circle_id uuid, p_member_id uuid, p_answers text[])
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE policy text;
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN NULL; END IF;
  SELECT c.join_policy INTO policy FROM milavn_circle.circle c WHERE c.id = p_circle_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  IF EXISTS (SELECT 1 FROM milavn_circle.circle_membership m
             WHERE m.circle_id = p_circle_id AND m.member_id = p_member_id AND m.left_at IS NULL) THEN
    RETURN 'already_member';
  END IF;
  IF NOT milavn_circle.may_enter(p_circle_id, p_member_id) THEN
    RAISE EXCEPTION 'women_only' USING ERRCODE = 'WO001';
  END IF;
  IF policy <> 'approval' THEN
    INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
    VALUES (p_circle_id, p_member_id, 'member') ON CONFLICT DO NOTHING;
    RETURN 'joined';
  END IF;
  IF EXISTS (SELECT 1 FROM milavn_circle.join_request r
             WHERE r.circle_id = p_circle_id AND r.member_id = p_member_id AND r.status = 'pending') THEN
    RETURN 'already_pending';
  END IF;
  INSERT INTO milavn_circle.join_request (circle_id, member_id, answers)
  VALUES (p_circle_id, p_member_id, coalesce(p_answers, '{}'));
  RETURN 'pending';
END;
$$;
GRANT EXECUTE ON FUNCTION milavn_circle.request_to_join(uuid, uuid, text[]) TO milavn_app;

-- Inviting someone who may not enter sends nothing and reads like an invite already outstanding,
-- so the inviter never learns the answer (the same quiet outcome a recent decline already gets).
CREATE OR REPLACE FUNCTION milavn_circle.invite_to_circle(p_circle_id uuid, p_actor uuid, p_member_ids uuid[])
RETURNS TABLE (r_member_id uuid, r_outcome text, r_invite_id uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  m uuid;
  new_id uuid;
BEGIN
  IF milavn_circle.invite_permission(p_circle_id, p_actor) <> 'ok' THEN
    RAISE EXCEPTION 'not allowed to invite into this circle' USING ERRCODE = '42501';
  END IF;
  FOREACH m IN ARRAY (SELECT coalesce(array_agg(DISTINCT x), '{}') FROM unnest(p_member_ids) x) LOOP
    IF m = p_actor THEN
      RETURN QUERY SELECT m, 'self'::text, NULL::uuid;
    ELSIF NOT EXISTS (SELECT 1 FROM milavn_profile.member_profile p WHERE p.member_id = m) THEN
      RETURN QUERY SELECT m, 'no_such_member'::text, NULL::uuid;
    ELSIF milavn_safety.is_blocked_either_way(p_actor, m) THEN
      RETURN QUERY SELECT m, 'blocked'::text, NULL::uuid;
    ELSIF milavn_circle.is_active_member(p_circle_id, m) THEN
      RETURN QUERY SELECT m, 'already_member'::text, NULL::uuid;
    ELSIF NOT milavn_circle.may_enter(p_circle_id, m) THEN
      RETURN QUERY SELECT m, 'already_invited'::text, NULL::uuid;
    ELSIF EXISTS (SELECT 1 FROM milavn_circle.circle_invite i WHERE i.circle_id = p_circle_id AND i.invited_member_id = m
                   AND (i.status = 'pending' OR (i.status = 'declined' AND i.responded_at > now() - interval '30 days'))) THEN
      RETURN QUERY SELECT m, 'already_invited'::text, NULL::uuid;
    ELSE
      INSERT INTO milavn_circle.circle_invite (circle_id, invited_member_id, invited_by_member_id)
      VALUES (p_circle_id, m, p_actor) ON CONFLICT DO NOTHING RETURNING id INTO new_id;
      RETURN QUERY SELECT m, CASE WHEN new_id IS NULL THEN 'already_invited' ELSE 'invited' END::text, new_id;
    END IF;
  END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.invite_to_circle(uuid, uuid, uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.invite_to_circle(uuid, uuid, uuid[]) TO milavn_app;

-- 5 -------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS milavn_circle.trip_stop (
  id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  position  integer NOT NULL,
  place     text NOT NULL CONSTRAINT trip_stop_place_sane CHECK (length(place) BETWEEN 1 AND 80),
  on_day    date,
  note      text CONSTRAINT trip_stop_note_sane CHECK (note IS NULL OR length(note) <= 200)
);
CREATE INDEX IF NOT EXISTS idx_trip_stop_circle ON milavn_circle.trip_stop (circle_id, position);

ALTER TABLE milavn_circle.trip_stop ENABLE ROW LEVEL SECURITY;
-- Anyone who can see the circle can see its route (it is what helps them decide to join).
DROP POLICY IF EXISTS trip_stop_visible ON milavn_circle.trip_stop;
CREATE POLICY trip_stop_visible ON milavn_circle.trip_stop FOR SELECT
  USING (EXISTS (SELECT 1 FROM milavn_circle.circle c WHERE c.id = trip_stop.circle_id));
-- Only the organizer or an assistant plans the route.
DROP POLICY IF EXISTS trip_stop_managers_write ON milavn_circle.trip_stop;
CREATE POLICY trip_stop_managers_write ON milavn_circle.trip_stop FOR ALL
  USING (milavn_circle.is_manager_of(circle_id, current_setting('milavn.member_id', true)::uuid))
  WITH CHECK (milavn_circle.is_manager_of(circle_id, current_setting('milavn.member_id', true)::uuid));
GRANT SELECT, INSERT, UPDATE, DELETE ON milavn_circle.trip_stop TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.is_manager_of(uuid, uuid) TO milavn_app;
