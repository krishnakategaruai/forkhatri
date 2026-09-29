-- 044 — Adding people to a circle (invitations, share links) and circle recommendations
-- from the people you know. Owner, 2026-09-29: "a big missing piece is adding people into our
-- circle" and "getting recommendations of circles people are following".
--
-- Modelled on Facebook group invites / WhatsApp group invite links: adding someone is an
-- INVITATION they accept, never a silent add. Being invited IS the approval, so accepting
-- skips the circle's join questions. Every write touches rows the actor's own RLS cannot reach
-- (another person's invite, another person's membership), so each is a SECURITY DEFINER
-- function in the house style: the caller must be the member bound to the transaction
-- (`milavn.member_id`), the rule is checked inside, and a small outcome code comes back for the
-- API to map to 403/404/409. Safe to run twice.

-- The types anyone can find and join (mirrors OPEN_TYPES in app/components/circle/interface.py).
CREATE OR REPLACE FUNCTION milavn_circle.is_joinable_type(p_type milavn_circle.circle_type)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT p_type::text IN ('public','community','interest','local','recurring_activity','temple','travel');
$$;

-- ---------------------------------------------------------------------------------------------
-- Invitations
CREATE TABLE IF NOT EXISTS milavn_circle.circle_invite (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id            uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  invited_member_id    uuid NOT NULL,
  invited_by_member_id uuid NOT NULL,
  status               text NOT NULL DEFAULT 'pending'
                       CONSTRAINT circle_invite_status_known CHECK (status IN ('pending','accepted','declined','cancelled')),
  created_at           timestamptz NOT NULL DEFAULT now(),
  responded_at         timestamptz,
  CONSTRAINT circle_invite_not_self CHECK (invited_member_id <> invited_by_member_id)
);
-- One live invitation per person per circle; re-inviting is a no-op, not a second notification.
CREATE UNIQUE INDEX IF NOT EXISTS circle_invite_one_pending ON milavn_circle.circle_invite (circle_id, invited_member_id) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS circle_invite_invitee ON milavn_circle.circle_invite (invited_member_id) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS circle_invite_circle ON milavn_circle.circle_invite (circle_id, status);

ALTER TABLE milavn_circle.circle_invite ENABLE ROW LEVEL SECURITY;
-- The invitee and the inviter see their own rows; the circle's managers see the circle's invites.
DROP POLICY IF EXISTS circle_invite_visible ON milavn_circle.circle_invite;
CREATE POLICY circle_invite_visible ON milavn_circle.circle_invite FOR SELECT USING (
  invited_member_id = current_setting('milavn.member_id', true)::uuid
  OR invited_by_member_id = current_setting('milavn.member_id', true)::uuid
  OR coalesce(milavn_circle.current_role_of(circle_id, current_setting('milavn.member_id', true)::uuid), '') IN ('organizer','assistant')
);
GRANT SELECT ON milavn_circle.circle_invite TO milavn_app;  -- writes only through the functions below

-- Share links: only a hash of the token is ever stored, so a database read cannot mint a link.
CREATE TABLE IF NOT EXISTS milavn_circle.circle_invite_link (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id            uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  token_hash           text NOT NULL UNIQUE,
  created_by_member_id uuid NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  expires_at           timestamptz NOT NULL DEFAULT now() + interval '14 days',
  revoked_at           timestamptz
);
CREATE INDEX IF NOT EXISTS circle_invite_link_circle ON milavn_circle.circle_invite_link (circle_id);
ALTER TABLE milavn_circle.circle_invite_link ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_invite_link_visible ON milavn_circle.circle_invite_link;
CREATE POLICY circle_invite_link_visible ON milavn_circle.circle_invite_link FOR SELECT USING (
  created_by_member_id = current_setting('milavn.member_id', true)::uuid
  OR coalesce(milavn_circle.current_role_of(circle_id, current_setting('milavn.member_id', true)::uuid), '') IN ('organizer','assistant')
);
GRANT SELECT ON milavn_circle.circle_invite_link TO milavn_app;

-- Who may bring people in: any member of an open circle (like a public Facebook group); only the
-- organizer or an assistant of an invite-only ('private', 'organization') circle.
-- 'ok' | 'not_found' (cannot see the circle) | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_circle.invite_permission(p_circle_id uuid, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  ctype milavn_circle.circle_type;
  role text;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  SELECT circle_type INTO ctype FROM milavn_circle.circle WHERE id = p_circle_id;
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  role := milavn_circle.current_role_of(p_circle_id, p_actor);
  IF role IS NULL THEN
    -- An invite-only circle does not exist for an outsider; an open one exists but they are not in it.
    RETURN CASE WHEN milavn_circle.is_joinable_type(ctype) THEN 'not_allowed' ELSE 'not_found' END;
  END IF;
  IF milavn_circle.is_joinable_type(ctype) OR role IN ('organizer','assistant') THEN RETURN 'ok'; END IF;
  RETURN 'not_allowed';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.invite_permission(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.invite_permission(uuid, uuid) TO milavn_app;

-- Invite several people at once. Per person:
-- 'invited' | 'already_invited' | 'already_member' | 'blocked' | 'no_such_member' | 'self'
-- A person who declined this circle in the last 30 days reads 'already_invited': they are not
-- pestered again, and the inviter is not told that they said no.
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

-- For the "add people" picker: of these people, who is already in, and who already has an invite.
-- Answers only to someone who is inside the circle, so it reveals nothing to outsiders.
CREATE OR REPLACE FUNCTION milavn_circle.invite_state(p_circle_id uuid, p_viewer uuid, p_member_ids uuid[])
RETURNS TABLE (member_id uuid, already_member boolean, invited boolean)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT x, milavn_circle.is_active_member(p_circle_id, x),
         EXISTS (SELECT 1 FROM milavn_circle.circle_invite i WHERE i.circle_id = p_circle_id AND i.invited_member_id = x AND i.status = 'pending')
  FROM unnest(p_member_ids) x
  WHERE p_viewer = current_setting('milavn.member_id', true)::uuid
    AND milavn_circle.is_active_member(p_circle_id, p_viewer);
$$;
REVOKE ALL ON FUNCTION milavn_circle.invite_state(uuid, uuid, uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.invite_state(uuid, uuid, uuid[]) TO milavn_app;

-- My pending invitations, with enough of the circle to show a card — the invitee cannot read an
-- invite-only circle through RLS until they are in it, and must still see what they are invited to.
CREATE OR REPLACE FUNCTION milavn_circle.my_circle_invites(p_viewer uuid)
RETURNS TABLE (
  invite_id uuid, invited_by_member_id uuid, invited_at timestamptz,
  id uuid, name text, circle_type text, description text, created_by_member_id uuid, created_at timestamptz,
  locality_city text, locality_locality text, join_policy text, join_questions text[], starts_on date, ends_on date,
  group_id uuid, posting_policy text, cover_ref text, member_count integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT i.id, i.invited_by_member_id, i.created_at,
         c.id, c.name, c.circle_type::text, c.description, c.created_by_member_id, c.created_at,
         c.locality_city, c.locality_locality, c.join_policy, c.join_questions, c.starts_on, c.ends_on,
         c.group_id, c.posting_policy, c.cover_ref,
         (SELECT count(*)::integer FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.left_at IS NULL)
  FROM milavn_circle.circle_invite i
  JOIN milavn_circle.circle c ON c.id = i.circle_id
  WHERE i.invited_member_id = p_viewer AND i.status = 'pending'
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND NOT milavn_safety.is_blocked_either_way(p_viewer, i.invited_by_member_id)
  ORDER BY i.created_at DESC;
$$;
REVOKE ALL ON FUNCTION milavn_circle.my_circle_invites(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.my_circle_invites(uuid) TO milavn_app;

-- Accept (join, bypassing the circle's join questions — the invitation was the approval) or
-- decline. Only the invitee, only while pending. A join request they had waiting is settled too.
-- r_outcome: 'joined' | 'declined' | 'not_found'
CREATE OR REPLACE FUNCTION milavn_circle.respond_to_invite(p_invite_id uuid, p_actor uuid, p_accept boolean)
RETURNS TABLE (r_outcome text, r_circle_id uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  inv record;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN
    RETURN QUERY SELECT 'not_found'::text, NULL::uuid; RETURN;
  END IF;
  SELECT i.id, i.circle_id, i.status INTO inv FROM milavn_circle.circle_invite i
   WHERE i.id = p_invite_id AND i.invited_member_id = p_actor FOR UPDATE;
  IF NOT FOUND OR inv.status <> 'pending' THEN
    RETURN QUERY SELECT 'not_found'::text, NULL::uuid; RETURN;
  END IF;
  UPDATE milavn_circle.circle_invite SET status = CASE WHEN p_accept THEN 'accepted' ELSE 'declined' END, responded_at = now()
   WHERE id = p_invite_id;
  IF NOT p_accept THEN
    RETURN QUERY SELECT 'declined'::text, inv.circle_id; RETURN;
  END IF;
  INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
  VALUES (inv.circle_id, p_actor, 'member') ON CONFLICT DO NOTHING;
  UPDATE milavn_circle.join_request SET status = 'approved'
   WHERE circle_id = inv.circle_id AND member_id = p_actor AND status = 'pending';
  RETURN QUERY SELECT 'joined'::text, inv.circle_id;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.respond_to_invite(uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.respond_to_invite(uuid, uuid, boolean) TO milavn_app;

-- The person who sent it, or the circle's organizer/assistant, withdraws a pending invitation.
-- 'cancelled' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_circle.cancel_invite(p_circle_id uuid, p_invite_id uuid, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  inv record;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  SELECT i.invited_by_member_id, i.status INTO inv FROM milavn_circle.circle_invite i
   WHERE i.id = p_invite_id AND i.circle_id = p_circle_id FOR UPDATE;
  IF NOT FOUND OR inv.status <> 'pending' THEN RETURN 'not_found'; END IF;
  IF inv.invited_by_member_id IS DISTINCT FROM p_actor
     AND coalesce(milavn_circle.current_role_of(p_circle_id, p_actor), '') NOT IN ('organizer','assistant') THEN
    RETURN 'not_allowed';
  END IF;
  UPDATE milavn_circle.circle_invite SET status = 'cancelled', responded_at = now() WHERE id = p_invite_id;
  RETURN 'cancelled';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.cancel_invite(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.cancel_invite(uuid, uuid, uuid) TO milavn_app;

-- Share link. Whoever may invite (invite_permission) may make one; the API generates the token and
-- hands only its SHA-256 here. 'created' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_circle.create_invite_link(p_circle_id uuid, p_actor uuid, p_token_hash text)
RETURNS TABLE (r_outcome text, r_expires_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  perm text := milavn_circle.invite_permission(p_circle_id, p_actor);
  exp timestamptz;
BEGIN
  IF perm <> 'ok' THEN RETURN QUERY SELECT perm, NULL::timestamptz; RETURN; END IF;
  INSERT INTO milavn_circle.circle_invite_link (circle_id, token_hash, created_by_member_id)
  VALUES (p_circle_id, p_token_hash, p_actor) RETURNING expires_at INTO exp;
  RETURN QUERY SELECT 'created'::text, exp;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.create_invite_link(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.create_invite_link(uuid, uuid, text) TO milavn_app;

-- invite_permission without the caller check, for judging a link's maker (internal only).
CREATE OR REPLACE FUNCTION milavn_circle.invite_permission_of(p_circle_id uuid, p_member uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(
    (SELECT milavn_circle.is_joinable_type(c.circle_type)
            OR milavn_circle.current_role_of(c.id, p_member) IN ('organizer','assistant')
     FROM milavn_circle.circle c WHERE c.id = p_circle_id)
    AND milavn_circle.current_role_of(p_circle_id, p_member) IS NOT NULL, false);
$$;
REVOKE ALL ON FUNCTION milavn_circle.invite_permission_of(uuid, uuid) FROM PUBLIC;
-- What someone holding a link sees before joining: the circle's public face only (never its
-- members or board). A link that is expired, revoked, or made by someone who has since left the
-- circle is no longer valid.
CREATE OR REPLACE FUNCTION milavn_circle.invite_link_preview(p_token_hash text)
RETURNS TABLE (circle_id uuid, name text, circle_type text, description text, cover_ref text, member_count integer, valid boolean)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT c.id, c.name, c.circle_type::text, c.description, c.cover_ref,
         (SELECT count(*)::integer FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.left_at IS NULL),
         (l.revoked_at IS NULL AND l.expires_at > now()
          AND milavn_circle.invite_permission_of(l.circle_id, l.created_by_member_id))
  FROM milavn_circle.circle_invite_link l
  JOIN milavn_circle.circle c ON c.id = l.circle_id
  WHERE l.token_hash = p_token_hash AND current_setting('milavn.member_id', true) IS NOT NULL;
$$;
REVOKE ALL ON FUNCTION milavn_circle.invite_link_preview(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.invite_link_preview(text) TO milavn_app;

-- Join through a link (the link is the approval). Someone blocked with the link's maker cannot use it.
-- r_outcome: 'joined' | 'already_member' | 'invalid'
CREATE OR REPLACE FUNCTION milavn_circle.join_by_invite_link(p_token_hash text, p_actor uuid)
RETURNS TABLE (r_outcome text, r_circle_id uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  l record;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN
    RETURN QUERY SELECT 'invalid'::text, NULL::uuid; RETURN;
  END IF;
  SELECT k.circle_id, k.created_by_member_id INTO l FROM milavn_circle.circle_invite_link k
   WHERE k.token_hash = p_token_hash AND k.revoked_at IS NULL AND k.expires_at > now();
  IF NOT FOUND OR NOT milavn_circle.invite_permission_of(l.circle_id, l.created_by_member_id)
     OR milavn_safety.is_blocked_either_way(p_actor, l.created_by_member_id) THEN
    RETURN QUERY SELECT 'invalid'::text, NULL::uuid; RETURN;
  END IF;
  IF milavn_circle.is_active_member(l.circle_id, p_actor) THEN
    RETURN QUERY SELECT 'already_member'::text, l.circle_id; RETURN;
  END IF;
  INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
  VALUES (l.circle_id, p_actor, 'member') ON CONFLICT DO NOTHING;
  -- Anything else they were waiting on for this circle is now settled.
  UPDATE milavn_circle.circle_invite SET status = 'accepted', responded_at = now()
   WHERE circle_id = l.circle_id AND invited_member_id = p_actor AND status = 'pending';
  UPDATE milavn_circle.join_request SET status = 'approved'
   WHERE circle_id = l.circle_id AND member_id = p_actor AND status = 'pending';
  RETURN QUERY SELECT 'joined'::text, l.circle_id;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.join_by_invite_link(text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.join_by_invite_link(text, uuid) TO milavn_app;

-- Joining any other way (open join, approved request, suggestion) closes a pending invitation to
-- that circle, so it does not linger as a prompt for a circle the person is already in.
CREATE OR REPLACE FUNCTION milavn_circle.settle_invites_on_join() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = milavn_circle, pg_catalog AS $$
BEGIN
  IF NEW.left_at IS NULL THEN
    UPDATE milavn_circle.circle_invite SET status = 'accepted', responded_at = now()
     WHERE circle_id = NEW.circle_id AND invited_member_id = NEW.member_id AND status = 'pending';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS circle_membership_settles_invites ON milavn_circle.circle_membership;
CREATE TRIGGER circle_membership_settles_invites AFTER INSERT ON milavn_circle.circle_membership
  FOR EACH ROW EXECUTE FUNCTION milavn_circle.settle_invites_on_join();

-- ---------------------------------------------------------------------------------------------
-- People I know — the people an "add people" picker offers first, and whose circles we recommend.
-- Four ways to know someone in Milavn, each with a weight; `known_via` names the strongest one:
--   connection  both said "meet again" (milavn_connect.meet_again, mutual)          40
--   chat        share a live direct or group conversation                            30
--   circle      share an active circle (10 per circle, up to 30)                      ≤30
--   activity    were both actually at the same past activity (8 each, up to 24)      ≤24
-- Attendance counts only once it happened and only when checked in / attended — the same rule as
-- familiar_count (027), so a future RSVP is never revealed (FR040). Blocked pairs never appear.
CREATE OR REPLACE FUNCTION milavn_circle.people_i_know(p_viewer uuid)
RETURNS TABLE (member_id uuid, known_via text, strength integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  WITH me AS (
    SELECT p_viewer AS v WHERE p_viewer = current_setting('milavn.member_id', true)::uuid
  ), src AS (
    SELECT a.chosen_member_id AS m, 'connection'::text AS via, 40 AS w
      FROM milavn_connect.meet_again a
      JOIN milavn_connect.meet_again b ON b.chooser_member_id = a.chosen_member_id AND b.chosen_member_id = a.chooser_member_id
      JOIN me ON a.chooser_member_id = me.v
    UNION ALL
    SELECT DISTINCT o.member_id, 'chat', 30
      FROM milavn_connect.conversation_member mine
      JOIN me ON mine.member_id = me.v
      JOIN milavn_connect.conversation_member o ON o.conversation_id = mine.conversation_id AND o.member_id <> me.v AND o.left_at IS NULL
     WHERE mine.left_at IS NULL
    UNION ALL
    SELECT o.member_id, 'circle', least(10 * count(*), 30)::integer
      FROM milavn_circle.circle_membership mine
      JOIN me ON mine.member_id = me.v
      JOIN milavn_circle.circle_membership o ON o.circle_id = mine.circle_id AND o.member_id <> me.v AND o.left_at IS NULL
     WHERE mine.left_at IS NULL
     GROUP BY o.member_id
    UNION ALL
    SELECT b.member_id, 'activity', least(8 * count(DISTINCT a.occurrence_id), 24)::integer
      FROM milavn_activity.participation a
      JOIN me ON a.member_id = me.v
      JOIN milavn_activity.participation b ON b.occurrence_id = a.occurrence_id AND b.member_id <> me.v
      JOIN milavn_activity.occurrence oc ON oc.id = a.occurrence_id
     WHERE a.status IN ('checked_in','attended') AND b.status IN ('checked_in','attended')
       AND oc.status = 'active' AND oc.time_start < now()
     GROUP BY b.member_id
  ), ranked AS (
    SELECT s.m, s.via, s.w, sum(s.w) OVER (PARTITION BY s.m) AS total,
           row_number() OVER (PARTITION BY s.m ORDER BY s.w DESC,
             array_position(ARRAY['connection','chat','circle','activity'], s.via)) AS rn
      FROM src s
  )
  SELECT r.m, r.via, r.total::integer FROM ranked r
   WHERE r.rn = 1 AND NOT milavn_safety.is_blocked_either_way(p_viewer, r.m)
   ORDER BY r.total DESC;
$$;
REVOKE ALL ON FUNCTION milavn_circle.people_i_know(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.people_i_know(uuid) TO milavn_app;

-- The pool a name search runs over: every Milavn member except the viewer and anyone blocked
-- either way. Ids only — names live on the platform and are matched in the API.
CREATE OR REPLACE FUNCTION milavn_circle.searchable_member_ids(p_viewer uuid)
RETURNS SETOF uuid LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT p.member_id FROM milavn_profile.member_profile p
   WHERE p_viewer = current_setting('milavn.member_id', true)::uuid
     AND p.member_id <> p_viewer
     AND NOT milavn_safety.is_blocked_either_way(p_viewer, p.member_id);
$$;
REVOKE ALL ON FUNCTION milavn_circle.searchable_member_ids(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.searchable_member_ids(uuid) TO milavn_app;

-- A member's chosen language, so a notification written for them is in their language.
CREATE OR REPLACE FUNCTION milavn_profile.language_of(p_member_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_profile, pg_catalog AS $$
  SELECT language_preference FROM milavn_profile.member_profile WHERE member_id = p_member_id;
$$;
REVOKE ALL ON FUNCTION milavn_profile.language_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_profile.language_of(uuid) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- Circle recommendations. Open circles only (never 'private' / 'organization'), that the viewer is
-- not in, not a past temple visit or trip. Ranked by how many people the viewer knows are in it,
-- then whether it is near them, then size. When fewer than 4 circles have someone the viewer knows,
-- the list is topped up to 8 with circles near them and then the most popular, so a new member
-- never sees an empty section. One statement; nothing about invite-only circles is ever read.
-- reason: 'known_members' | 'near_you' | 'popular'
CREATE OR REPLACE FUNCTION milavn_circle.recommended_circles(p_viewer uuid, p_limit integer DEFAULT 12)
RETURNS TABLE (circle_id uuid, known_count integer, known_ids uuid[], member_count integer, near_you boolean, reason text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  WITH me AS (
    SELECT p.member_id AS v, p.locality_city AS city, p.locality_locality AS loc
      FROM milavn_profile.member_profile p
     WHERE p.member_id = p_viewer AND p_viewer = current_setting('milavn.member_id', true)::uuid
    UNION ALL
    -- a member without a Milavn profile yet still gets popular circles
    SELECT p_viewer, NULL, NULL
     WHERE p_viewer = current_setting('milavn.member_id', true)::uuid
       AND NOT EXISTS (SELECT 1 FROM milavn_profile.member_profile p WHERE p.member_id = p_viewer)
  ), known AS (
    SELECT k.member_id, k.strength FROM milavn_circle.people_i_know(p_viewer) k
  ), candidates AS (
    SELECT c.id, c.locality_city, c.locality_locality, c.created_at,
           (SELECT count(*)::integer FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.left_at IS NULL) AS members,
           coalesce((SELECT array_agg(m.member_id ORDER BY k.strength DESC)
                       FROM milavn_circle.circle_membership m JOIN known k ON k.member_id = m.member_id
                      WHERE m.circle_id = c.id AND m.left_at IS NULL), '{}') AS knowns,
           (me.city IS NOT NULL AND c.locality_city = me.city
              AND (c.locality_locality IS NULL OR c.locality_locality = me.loc)) AS near
      FROM milavn_circle.circle c CROSS JOIN me
     WHERE milavn_circle.is_joinable_type(c.circle_type)
       AND NOT (c.circle_type::text IN ('temple','travel') AND coalesce(c.ends_on, c.starts_on) < CURRENT_DATE)
       AND NOT EXISTS (SELECT 1 FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.member_id = me.v AND m.left_at IS NULL)
  ), with_known AS (
    SELECT count(*) AS n FROM candidates WHERE cardinality(knowns) > 0
  ), ranked AS (
    SELECT cand.*, CASE WHEN cardinality(knowns) > 0 THEN 'known_members' WHEN near THEN 'near_you' ELSE 'popular' END AS why,
           row_number() OVER (ORDER BY cardinality(knowns) DESC, near DESC, members DESC, created_at DESC) AS pos
      FROM candidates cand
  )
  SELECT r.id, cardinality(r.knowns), r.knowns[1:3], r.members, r.near, r.why
    FROM ranked r, with_known w
   WHERE (r.why = 'known_members' AND r.pos <= p_limit)
      OR (w.n < 4 AND r.why <> 'known_members' AND r.pos <= 8)
   ORDER BY r.pos;
$$;
REVOKE ALL ON FUNCTION milavn_circle.recommended_circles(uuid, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.recommended_circles(uuid, integer) TO milavn_app;
