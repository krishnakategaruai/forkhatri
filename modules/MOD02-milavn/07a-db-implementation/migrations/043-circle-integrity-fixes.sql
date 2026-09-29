-- 043 — Circle integrity fixes from the functional test pass (2026-09-28).
--
-- Every write below touches rows the acting member's own RLS cannot reach (other people's
-- suggestion answers, other people's memberships, other people's posts), so each is a
-- SECURITY DEFINER function in the house style: the caller must be the member bound to the
-- transaction (`milavn.member_id`), the rule is checked inside, and the answer is a small
-- outcome code the API maps to 403/404/409 — never a 500.
--
--   B1  respond_to_suggestion   the suggested circle is actually created on the 2nd yes
--   B12 suggested_pairs         the nightly job's "already suggested?" check, in one query,
--                               ignoring declined suggestions after a cooldown
--   B3  add_member_by_manager   organizer OR assistant (today's role) brings someone in
--   B8  delete_circle_post      the author, or the circle's organizer/assistant, takes a post down
--   B8  remove_circle_member    organizer removes anyone but an organizer; assistant removes members
--   B9  poll_vote → poll_option composite key: a vote's option must belong to that poll
--       delete_circle           also refuses while an event is still in progress

-- ---------------------------------------------------------------------------------------------
-- B1 — [FR022, corrected 2026-09-28] A circle forms when a SECOND suggested person says yes.
-- The earlier Python path counted the yeses under the member-self RLS policy (`cfsm_self`), so
-- it only ever saw its own row and the count never reached 2: no circle was ever created.
-- Everything happens here, under a row lock on the suggestion so two people answering at the
-- same moment cannot create two circles.
-- Returns the created (or joined) circle id, or NULL (declined / first yes / not a recipient).
CREATE OR REPLACE FUNCTION milavn_circle.respond_to_suggestion(
  p_suggestion_id uuid, p_member_id uuid, p_accept boolean, p_description text DEFAULT NULL)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog
AS $$
DECLARE
  s record;
  new_circle uuid;
  yes_ids uuid[];
  still_possible integer;
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN NULL; END IF;
  SELECT id, suggested_circle_name, status, created_circle_id INTO s
    FROM milavn_circle.circle_formation_suggestion WHERE id = p_suggestion_id FOR UPDATE;
  IF NOT FOUND THEN RETURN NULL; END IF;

  UPDATE milavn_circle.circle_formation_suggestion_member
     SET responded_at = now(), accepted = p_accept
   WHERE suggestion_id = p_suggestion_id AND member_id = p_member_id;
  IF NOT FOUND THEN RETURN NULL; END IF;  -- not one of the suggested people

  IF NOT p_accept THEN
    -- Once fewer than two people could still say yes, nothing can form: close it out.
    IF s.status = 'pending' THEN
      SELECT count(*) INTO still_possible FROM milavn_circle.circle_formation_suggestion_member
       WHERE suggestion_id = p_suggestion_id AND accepted IS DISTINCT FROM false;
      IF still_possible < 2 THEN
        UPDATE milavn_circle.circle_formation_suggestion SET status = 'declined', responded_at = now() WHERE id = p_suggestion_id;
      END IF;
    END IF;
    RETURN NULL;
  END IF;

  -- The community already formed: a later yes joins it (it is an open recurring-activity circle).
  IF s.created_circle_id IS NOT NULL THEN
    INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
    VALUES (s.created_circle_id, p_member_id, 'member') ON CONFLICT DO NOTHING;
    RETURN s.created_circle_id;
  END IF;
  -- Declined, or formed and later deleted by its organizer: nothing to create or join.
  IF s.status <> 'pending' THEN RETURN NULL; END IF;

  SELECT array_agg(member_id ORDER BY responded_at) INTO yes_ids
    FROM milavn_circle.circle_formation_suggestion_member
   WHERE suggestion_id = p_suggestion_id AND accepted IS TRUE;
  IF coalesce(array_length(yes_ids, 1), 0) < 2 THEN RETURN NULL; END IF;  -- first yes: waiting for a second

  new_circle := gen_random_uuid();
  INSERT INTO milavn_circle.circle (id, name, circle_type, description, created_by_member_id)
  VALUES (new_circle, s.suggested_circle_name, 'recurring_activity', NULLIF(p_description, ''), p_member_id);
  -- The person whose yes formed it organizes it; everyone who said yes is in from the start.
  INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
  SELECT new_circle, m, CASE WHEN m = p_member_id THEN 'organizer' ELSE 'member' END::milavn_circle.circle_member_role
    FROM unnest(yes_ids) AS m
  ON CONFLICT DO NOTHING;
  UPDATE milavn_circle.circle_formation_suggestion
     SET status = 'accepted', responded_at = now(), created_circle_id = new_circle
   WHERE id = p_suggestion_id;
  RETURN new_circle;
END;
$$;

REVOKE ALL ON FUNCTION milavn_circle.respond_to_suggestion(uuid, uuid, boolean, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.respond_to_suggestion(uuid, uuid, boolean, text) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- B12 — Every pair of people already inside a live suggestion, fetched once per job run instead
-- of one call per pair. A pending or accepted suggestion blocks the pair; a declined one only
-- for 90 days, so a group that said "not now" can be asked again once it keeps meeting.
CREATE OR REPLACE FUNCTION milavn_circle.suggested_pairs()
RETURNS TABLE (member_a uuid, member_b uuid)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT DISTINCT x.member_id, y.member_id
  FROM milavn_circle.circle_formation_suggestion s
  JOIN milavn_circle.circle_formation_suggestion_member x ON x.suggestion_id = s.id
  JOIN milavn_circle.circle_formation_suggestion_member y ON y.suggestion_id = s.id AND x.member_id < y.member_id
  WHERE s.status IN ('pending', 'accepted')
     OR (s.status = 'declined' AND coalesce(s.responded_at, s.created_at) > now() - interval '90 days');
$$;
REVOKE ALL ON FUNCTION milavn_circle.suggested_pairs() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.suggested_pairs() TO milavn_app;

-- The per-pair check keeps its signature for any caller still using it, with the same rule.
CREATE OR REPLACE FUNCTION milavn_circle.suggestion_exists_for_pair(p_a uuid, p_b uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (
    SELECT 1 FROM milavn_circle.suggested_pairs() p
    WHERE (p.member_a = p_a AND p.member_b = p_b) OR (p.member_a = p_b AND p.member_b = p_a)
  );
$$;
REVOKE ALL ON FUNCTION milavn_circle.suggestion_exists_for_pair(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.suggestion_exists_for_pair(uuid, uuid) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- The circle's managers as of today: organizer or assistant with a live membership. Deliberately
-- NOT `can_moderate_circle` (which also trusts the original creator even after they left or
-- handed the circle over).
CREATE OR REPLACE FUNCTION milavn_circle.current_role_of(p_circle_id uuid, p_member_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT m.member_role::text FROM milavn_circle.circle_membership m
  WHERE m.circle_id = p_circle_id AND m.member_id = p_member_id AND m.left_at IS NULL
  LIMIT 1;
$$;
REVOKE ALL ON FUNCTION milavn_circle.current_role_of(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.current_role_of(uuid, uuid) TO milavn_app;

-- B3/B11 — [FR121] The organizer or an assistant brings someone in directly. RLS
-- (`circle_membership_self_write`) only lets a member insert their own row or the ORIGINAL creator
-- seed rows, so an assistant (or an organizer the circle was handed to) hit a 500. The person
-- added must be a real Milavn member (has a Milavn profile), not an arbitrary id.
-- 'added' | 'already_member' | 'not_found' | 'not_manager' | 'no_such_member'
CREATE OR REPLACE FUNCTION milavn_circle.add_member_by_manager(p_circle_id uuid, p_actor uuid, p_member_id uuid)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog
AS $$
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_manager'; END IF;
  IF NOT EXISTS (SELECT 1 FROM milavn_circle.circle WHERE id = p_circle_id) THEN RETURN 'not_found'; END IF;
  IF coalesce(milavn_circle.current_role_of(p_circle_id, p_actor), '') NOT IN ('organizer', 'assistant') THEN
    RETURN 'not_manager';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM milavn_profile.member_profile p WHERE p.member_id = p_member_id) THEN
    RETURN 'no_such_member';
  END IF;
  IF milavn_circle.is_active_member(p_circle_id, p_member_id) THEN RETURN 'already_member'; END IF;
  INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
  VALUES (p_circle_id, p_member_id, 'member') ON CONFLICT DO NOTHING;
  RETURN 'added';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.add_member_by_manager(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.add_member_by_manager(uuid, uuid, uuid) TO milavn_app;

-- B8(a) — The author takes their own post back; the organizer or an assistant can take down any
-- post in their circle (Facebook group admins / WhatsApp group admins can). Soft delete, as
-- before. Returns the media refs so the API can remove the files from disk (B5).
-- r_outcome: 'deleted' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_circle.delete_circle_post(p_circle_id uuid, p_post_id uuid, p_actor uuid)
RETURNS TABLE (r_outcome text, r_photo_ref text, r_doc_ref text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog
AS $$
DECLARE
  -- Plain variables rather than a record: a record that SELECT INTO never filled cannot be
  -- read, and the "no such post" branch below still reads the author.
  v_author uuid;
  v_photo text;
  v_doc text;
  actor_role text;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN
    RETURN QUERY SELECT 'not_allowed'::text, NULL::text, NULL::text; RETURN;
  END IF;
  SELECT cp.member_id, cp.photo_ref, cp.doc_ref INTO v_author, v_photo, v_doc
    FROM milavn_circle.circle_post cp
   WHERE cp.id = p_post_id AND cp.circle_id = p_circle_id AND cp.deleted_at IS NULL;
  actor_role := milavn_circle.current_role_of(p_circle_id, p_actor);
  -- Someone who can see neither the post nor the circle's board learns nothing about it.
  IF v_author IS NULL OR (actor_role IS NULL AND v_author IS DISTINCT FROM p_actor) THEN
    RETURN QUERY SELECT 'not_found'::text, NULL::text, NULL::text; RETURN;
  END IF;
  IF v_author IS DISTINCT FROM p_actor AND actor_role NOT IN ('organizer', 'assistant') THEN
    RETURN QUERY SELECT 'not_allowed'::text, NULL::text, NULL::text; RETURN;
  END IF;
  UPDATE milavn_circle.circle_post SET deleted_at = now() WHERE id = p_post_id;
  RETURN QUERY SELECT 'deleted'::text, v_photo, v_doc;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.delete_circle_post(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.delete_circle_post(uuid, uuid, uuid) TO milavn_app;

-- B8(b) — Removing someone from the circle (FR121: the organizer runs the group; an assistant
-- shares the day-to-day work but, as migration 030 says, cannot remove the organizer). Nobody
-- removes an organizer, and nobody removes themselves this way (that is "leave").
-- 'removed' | 'not_found' | 'not_manager' | 'not_member' | 'is_organizer' | 'is_self'
CREATE OR REPLACE FUNCTION milavn_circle.remove_circle_member(p_circle_id uuid, p_actor uuid, p_member_id uuid)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog
AS $$
DECLARE
  actor_role text;
  target_role text;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_manager'; END IF;
  IF NOT EXISTS (SELECT 1 FROM milavn_circle.circle WHERE id = p_circle_id) THEN RETURN 'not_found'; END IF;
  actor_role := milavn_circle.current_role_of(p_circle_id, p_actor);
  IF actor_role IS NULL THEN RETURN 'not_found'; END IF;  -- outsiders learn nothing about the roster
  IF actor_role NOT IN ('organizer', 'assistant') THEN RETURN 'not_manager'; END IF;
  IF p_member_id = p_actor THEN RETURN 'is_self'; END IF;
  target_role := milavn_circle.current_role_of(p_circle_id, p_member_id);
  IF target_role IS NULL THEN RETURN 'not_member'; END IF;
  IF target_role = 'organizer' THEN RETURN 'is_organizer'; END IF;
  IF actor_role = 'assistant' AND target_role <> 'member' THEN RETURN 'not_manager'; END IF;
  UPDATE milavn_circle.circle_membership SET left_at = now()
   WHERE circle_id = p_circle_id AND member_id = p_member_id AND left_at IS NULL;
  RETURN 'removed';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.remove_circle_member(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.remove_circle_member(uuid, uuid, uuid) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- B9 — A vote carries both option_id and poll_id; nothing tied them together, so a vote could
-- name an option from another poll. The pair now has to exist in poll_option.
DELETE FROM milavn_circle.poll_vote v
 WHERE NOT EXISTS (SELECT 1 FROM milavn_circle.poll_option o WHERE o.id = v.option_id AND o.poll_id = v.poll_id);
-- (The foreign key is dropped first: it depends on the unique key, so a re-run must undo it first.)
ALTER TABLE milavn_circle.poll_vote DROP CONSTRAINT IF EXISTS poll_vote_option_in_poll;
ALTER TABLE milavn_circle.poll_option DROP CONSTRAINT IF EXISTS poll_option_id_poll_unique;
ALTER TABLE milavn_circle.poll_option ADD CONSTRAINT poll_option_id_poll_unique UNIQUE (id, poll_id);
ALTER TABLE milavn_circle.poll_vote ADD CONSTRAINT poll_vote_option_in_poll
  FOREIGN KEY (option_id, poll_id) REFERENCES milavn_circle.poll_option (id, poll_id) ON DELETE CASCADE;

-- ---------------------------------------------------------------------------------------------
-- delete_circle (041) also refuses while an event is still happening (started, not yet ended):
-- deleting the circle mid-event would strand the people who are there right now.
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
    WHERE o.circle_id = p_circle_id AND o.status <> 'cancelled'
      AND (o.time_start > now() OR coalesce(o.time_end, o.time_start) > now())
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
