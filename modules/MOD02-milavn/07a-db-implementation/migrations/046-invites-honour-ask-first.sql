-- 046 — Invitations and share links honour the organizer's "Ask first" setting (critique, 2026-09-29).
--
-- 044 let any member of an open circle invite people and make share links, and accepting either
-- one inserted a membership directly, so a plain member could walk anyone past a circle whose
-- organizer screens new people (join_policy = 'approval'). Modelled on WhatsApp's "approve new
-- members" and Facebook's "member invites need admin approval":
--   * being invited, or given a link, by an organizer or assistant IS the approval: one tap in;
--   * in an 'approval' circle, a plain member may still invite, but accepting their invitation (or
--     using a link they made before this change, or made while they were a manager and have since
--     been demoted) files a pending join request (no answers) for the organizers to decide;
--   * in an 'approval' circle, only organizers and assistants may make a new share link.
-- Outcomes: respond_to_invite 'joined' | 'pending' | 'already_pending' | 'declined' | 'not_found';
--           join_by_invite_link 'joined' | 'already_member' | 'pending' | 'already_pending' | 'invalid';
--           create_invite_link adds 'managers_only'.
-- Safe to run twice.

CREATE OR REPLACE FUNCTION milavn_circle.is_manager_of(p_circle_id uuid, p_member uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(milavn_circle.current_role_of(p_circle_id, p_member), '') IN ('organizer', 'assistant');
$$;
REVOKE ALL ON FUNCTION milavn_circle.is_manager_of(uuid, uuid) FROM PUBLIC;

-- Does someone brought in by `p_via` still have to be approved? True when the circle asks first and
-- the person who invited them (or made the link) is not an organizer or assistant today.
CREATE OR REPLACE FUNCTION milavn_circle.entry_needs_approval(p_circle_id uuid, p_via uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce((SELECT c.join_policy = 'approval' FROM milavn_circle.circle c WHERE c.id = p_circle_id), false)
         AND NOT milavn_circle.is_manager_of(p_circle_id, p_via);
$$;
REVOKE ALL ON FUNCTION milavn_circle.entry_needs_approval(uuid, uuid) FROM PUBLIC;

-- File a pending join request (no answers) unless one is already waiting.
-- 'pending' (new) | 'already_pending'
CREATE OR REPLACE FUNCTION milavn_circle.file_join_request(p_circle_id uuid, p_member uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
BEGIN
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
  SELECT i.id, i.circle_id, i.status, i.invited_by_member_id INTO inv FROM milavn_circle.circle_invite i
   WHERE i.id = p_invite_id AND i.invited_member_id = p_actor FOR UPDATE;
  IF NOT FOUND OR inv.status <> 'pending' THEN
    RETURN QUERY SELECT 'not_found'::text, NULL::uuid; RETURN;
  END IF;
  UPDATE milavn_circle.circle_invite SET status = CASE WHEN p_accept THEN 'accepted' ELSE 'declined' END, responded_at = now()
   WHERE id = p_invite_id;
  IF NOT p_accept THEN
    RETURN QUERY SELECT 'declined'::text, inv.circle_id; RETURN;
  END IF;
  IF NOT milavn_circle.is_active_member(inv.circle_id, p_actor)
     AND milavn_circle.entry_needs_approval(inv.circle_id, inv.invited_by_member_id) THEN
    RETURN QUERY SELECT milavn_circle.file_join_request(inv.circle_id, p_actor), inv.circle_id; RETURN;
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

CREATE OR REPLACE FUNCTION milavn_circle.create_invite_link(p_circle_id uuid, p_actor uuid, p_token_hash text)
RETURNS TABLE (r_outcome text, r_expires_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  perm text := milavn_circle.invite_permission(p_circle_id, p_actor);
  exp timestamptz;
BEGIN
  IF perm <> 'ok' THEN RETURN QUERY SELECT perm, NULL::timestamptz; RETURN; END IF;
  IF milavn_circle.entry_needs_approval(p_circle_id, p_actor) THEN
    RETURN QUERY SELECT 'managers_only'::text, NULL::timestamptz; RETURN;
  END IF;
  INSERT INTO milavn_circle.circle_invite_link (circle_id, token_hash, created_by_member_id)
  VALUES (p_circle_id, p_token_hash, p_actor) RETURNING expires_at INTO exp;
  RETURN QUERY SELECT 'created'::text, exp;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.create_invite_link(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.create_invite_link(uuid, uuid, text) TO milavn_app;

-- The preview also says whether using the link joins straight away or asks the organizers.
DROP FUNCTION IF EXISTS milavn_circle.invite_link_preview(text);
CREATE FUNCTION milavn_circle.invite_link_preview(p_token_hash text)
RETURNS TABLE (circle_id uuid, name text, circle_type text, description text, cover_ref text, member_count integer,
               valid boolean, needs_approval boolean)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT c.id, c.name, c.circle_type::text, c.description, c.cover_ref,
         (SELECT count(*)::integer FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.left_at IS NULL),
         (l.revoked_at IS NULL AND l.expires_at > now()
          AND milavn_circle.invite_permission_of(l.circle_id, l.created_by_member_id)),
         milavn_circle.entry_needs_approval(l.circle_id, l.created_by_member_id)
  FROM milavn_circle.circle_invite_link l
  JOIN milavn_circle.circle c ON c.id = l.circle_id
  WHERE l.token_hash = p_token_hash AND current_setting('milavn.member_id', true) IS NOT NULL;
$$;
REVOKE ALL ON FUNCTION milavn_circle.invite_link_preview(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.invite_link_preview(text) TO milavn_app;

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
  IF milavn_circle.entry_needs_approval(l.circle_id, l.created_by_member_id) THEN
    RETURN QUERY SELECT milavn_circle.file_join_request(l.circle_id, p_actor), l.circle_id; RETURN;
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
