-- 045 — Private circle media, invite notifications that go away, and admin console extras.
--
-- 1. Circle media is private (2026-09-29). `/media` used to be an open static folder, so anyone
--    holding a URL could fetch an invite-only circle's photos and documents. The API now serves
--    circle photos, documents and covers through `circle_media_access`, which answers only when
--    the member bound to the transaction may see the file. Everything is decided here, in one
--    place, because the rules reach rows the caller's own RLS cannot (a pending invitation, an
--    invite link, a moderator looking at a reported post).
-- 2. An invitation that stops being pending (withdrawn, declined, accepted, joined another way,
--    circle deleted) takes its "X invited you to <circle>" notification with it.
-- 3. Admin console (TR-PLAT-01): a moderation action may carry a `reason_code`; the queue can
--    name any reported thing (`moderation_subject_title`); and a per-member summary
--    (`member_admin_summary`) for the shared ForKhatri console. Both read functions answer only
--    for a moderator.
-- Safe to run twice.

-- ---------------------------------------------------------------------------------------------
-- 1. Circle media
CREATE INDEX IF NOT EXISTS circle_cover_ref_idx ON milavn_circle.circle (cover_ref) WHERE cover_ref IS NOT NULL;
CREATE INDEX IF NOT EXISTS circle_post_photo_ref_idx ON milavn_circle.circle_post (photo_ref) WHERE photo_ref IS NOT NULL;
CREATE INDEX IF NOT EXISTS circle_post_doc_ref_idx ON milavn_circle.circle_post (doc_ref) WHERE doc_ref IS NOT NULL;
CREATE INDEX IF NOT EXISTS chat_message_media_ref_idx ON milavn_connect.chat_message (media_ref) WHERE media_ref IS NOT NULL;
CREATE INDEX IF NOT EXISTS occurrence_photo_storage_ref_idx ON milavn_activity.occurrence_photo (storage_ref);

-- One row when the bound member may see the file `p_ref` (e.g. 'circle-posts/<circle>-<hex>.jpg'),
-- no row otherwise (the API answers 404 either way, so existence is not leaked).
--   post photo / document: an active member, the circle's creator (the same rule as the board's
--                          RLS), or a moderator. A taken-down post's files are gone for everyone.
--   cover:                 anyone for an open circle (discover cards); for an invite-only circle
--                          the members, the creator, a moderator, someone with a pending
--                          invitation, or someone holding a working invite link to it.
-- kind: 'cover' | 'photo' | 'doc'. doc_name is the uploader's file name, for Content-Disposition.
CREATE OR REPLACE FUNCTION milavn_circle.circle_media_access(p_ref text, p_invite_token_hash text DEFAULT NULL)
RETURNS TABLE (circle_id uuid, kind text, doc_name text, is_open boolean)
LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  me uuid := nullif(current_setting('milavn.member_id', true), '')::uuid;
  moderator boolean := coalesce(current_setting('milavn.permission_scope', true), '') LIKE '%milavn.moderate%';
  c_id uuid;
  c_open boolean;
  k text;
  dn text;
  insider boolean;
BEGIN
  IF p_ref IS NULL OR p_ref = '' THEN RETURN; END IF;
  SELECT c.id, milavn_circle.is_joinable_type(c.circle_type) INTO c_id, c_open
    FROM milavn_circle.circle c WHERE c.cover_ref = p_ref LIMIT 1;
  IF FOUND THEN
    k := 'cover';
  ELSE
    SELECT p.circle_id, CASE WHEN p.photo_ref = p_ref THEN 'photo' ELSE 'doc' END, p.doc_name
      INTO c_id, k, dn
      FROM milavn_circle.circle_post p
     WHERE (p.photo_ref = p_ref OR p.doc_ref = p_ref) AND p.deleted_at IS NULL
     LIMIT 1;
    IF NOT FOUND THEN RETURN; END IF;
    SELECT milavn_circle.is_joinable_type(c.circle_type) INTO c_open FROM milavn_circle.circle c WHERE c.id = c_id;
  END IF;

  insider := moderator OR (me IS NOT NULL AND (
    milavn_circle.is_active_member(c_id, me) OR milavn_circle.is_circle_creator(c_id, me)));

  IF k = 'cover' AND NOT insider THEN
    insider := coalesce(c_open, false)
      OR (me IS NOT NULL AND EXISTS (
            SELECT 1 FROM milavn_circle.circle_invite i
             WHERE i.circle_id = c_id AND i.invited_member_id = me AND i.status = 'pending'))
      OR (p_invite_token_hash IS NOT NULL AND EXISTS (
            SELECT 1 FROM milavn_circle.circle_invite_link l
             WHERE l.token_hash = p_invite_token_hash AND l.circle_id = c_id
               AND l.revoked_at IS NULL AND l.expires_at > now()
               AND milavn_circle.invite_permission_of(l.circle_id, l.created_by_member_id)));
  END IF;

  IF insider THEN
    RETURN QUERY SELECT c_id, k, dn, coalesce(c_open, false);
  END IF;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.circle_media_access(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.circle_media_access(text, text) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- 2. An invitation's notification leaves with the invitation.
-- The invite notification's deep link names the circle ('/circles?invites=1&circle=<id>'), so the
-- one for this circle can be found. Rows written before this migration carry the bare
-- '/circles?invites=1'; those go once the person has no pending invitation left at all.
CREATE OR REPLACE FUNCTION milavn_circle.clear_settled_invite_notification() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  inv record;
  link text;
BEGIN
  IF TG_OP = 'DELETE' THEN inv := OLD; ELSE inv := NEW; END IF;
  IF TG_OP = 'UPDATE' AND NOT (OLD.status = 'pending' AND NEW.status <> 'pending') THEN
    RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' AND OLD.status <> 'pending' THEN
    RETURN OLD;
  END IF;
  link := '/circles?invites=1&circle=' || inv.circle_id::text;
  DELETE FROM milavn_notification.notification_inbox_entry
   WHERE member_id = inv.invited_member_id AND deep_link = link;
  DELETE FROM milavn_notification.notification_outbox
   WHERE member_id = inv.invited_member_id AND payload->>'deep_link' = link;
  IF NOT EXISTS (
    SELECT 1 FROM milavn_circle.circle_invite i
     WHERE i.invited_member_id = inv.invited_member_id AND i.status = 'pending' AND i.id <> inv.id
  ) THEN
    DELETE FROM milavn_notification.notification_inbox_entry
     WHERE member_id = inv.invited_member_id AND deep_link = '/circles?invites=1';
    DELETE FROM milavn_notification.notification_outbox
     WHERE member_id = inv.invited_member_id AND payload->>'deep_link' = '/circles?invites=1';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS circle_invite_clears_notification ON milavn_circle.circle_invite;
CREATE TRIGGER circle_invite_clears_notification
  AFTER UPDATE OF status OR DELETE ON milavn_circle.circle_invite
  FOR EACH ROW EXECUTE FUNCTION milavn_circle.clear_settled_invite_notification();

-- Invitations settled before this trigger existed left their notification behind (e.g. Asha's
-- withdrawn invitation of Meera to Jubilee Hills Badminton Circle). Clear any invite notification
-- whose invitation is no longer pending. Safe to run again: it only removes stale rows.
DELETE FROM milavn_notification.notification_inbox_entry e
 WHERE e.deep_link LIKE '/circles?invites=1%'
   AND NOT EXISTS (
     SELECT 1 FROM milavn_circle.circle_invite i
      WHERE i.invited_member_id = e.member_id AND i.status = 'pending'
        AND (e.deep_link = '/circles?invites=1' OR e.deep_link = '/circles?invites=1&circle=' || i.circle_id::text));
DELETE FROM milavn_notification.notification_outbox o
 WHERE o.payload->>'deep_link' LIKE '/circles?invites=1%'
   AND NOT EXISTS (
     SELECT 1 FROM milavn_circle.circle_invite i
      WHERE i.invited_member_id = o.member_id AND i.status = 'pending'
        AND (o.payload->>'deep_link' = '/circles?invites=1' OR o.payload->>'deep_link' = '/circles?invites=1&circle=' || i.circle_id::text));

-- The notification is written after the inviting transaction commits; if the invitation was
-- already withdrawn by then, it must not be written at all.
CREATE OR REPLACE FUNCTION milavn_circle.invite_is_pending(p_circle_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_circle.circle_invite
                  WHERE circle_id = p_circle_id AND invited_member_id = p_member_id AND status = 'pending');
$$;
REVOKE ALL ON FUNCTION milavn_circle.invite_is_pending(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.invite_is_pending(uuid, uuid) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- 3. Admin console extras
ALTER TABLE milavn_safety.moderation_action ADD COLUMN IF NOT EXISTS reason_code text;
DO $$ BEGIN
  ALTER TABLE milavn_safety.moderation_action
    ADD CONSTRAINT moderation_action_reason_code_shape CHECK (reason_code IS NULL OR reason_code ~ '^[a-z0-9_.-]{1,64}$');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- A human name for a reported thing, for a moderator only (NULL for anyone else, or when the
-- thing is gone). 'content' may be a circle, a circle post or an activity; 'organization' an
-- organization scope; 'occurrence'/'activity' the activity title; 'user' is named by the API.
CREATE OR REPLACE FUNCTION milavn_safety.moderation_subject_title(p_subject_type text, p_subject_id uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_safety, pg_catalog AS $$
DECLARE t text;
BEGIN
  IF coalesce(current_setting('milavn.permission_scope', true), '') NOT LIKE '%milavn.moderate%' THEN RETURN NULL; END IF;
  IF p_subject_type IN ('occurrence', 'activity', 'content') THEN
    SELECT o.title INTO t FROM milavn_activity.occurrence o WHERE o.id = p_subject_id;
    IF t IS NOT NULL THEN RETURN t; END IF;
    SELECT a.title INTO t FROM milavn_activity.activity a WHERE a.id = p_subject_id;
    IF t IS NOT NULL THEN RETURN t; END IF;
  END IF;
  IF p_subject_type = 'content' THEN
    SELECT c.name INTO t FROM milavn_circle.circle c WHERE c.id = p_subject_id;
    IF t IS NOT NULL THEN RETURN t; END IF;
    SELECT CASE WHEN length(p.body) > 80 THEN left(p.body, 79) || '…' ELSE p.body END || ' — ' || c.name
      INTO t FROM milavn_circle.circle_post p JOIN milavn_circle.circle c ON c.id = p.circle_id WHERE p.id = p_subject_id;
    IF t IS NOT NULL THEN RETURN t; END IF;
  END IF;
  IF p_subject_type = 'organization' THEN
    SELECT s.display_name INTO t FROM milavn_circle.organization_scope s WHERE s.organization_scope_id = p_subject_id;
  END IF;
  RETURN t;
END;
$$;
REVOKE ALL ON FUNCTION milavn_safety.moderation_subject_title(text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_safety.moderation_subject_title(text, uuid) TO milavn_app;

-- Everything the console's member page needs about one person in Milavn, for a moderator only.
-- NULL when the caller is not a moderator or the person has never opened Milavn (no profile).
CREATE OR REPLACE FUNCTION milavn_safety.member_admin_summary(p_member_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_safety, pg_catalog AS $$
DECLARE since timestamptz;
BEGIN
  IF coalesce(current_setting('milavn.permission_scope', true), '') NOT LIKE '%milavn.moderate%' THEN RETURN NULL; END IF;
  SELECT created_at INTO since FROM milavn_profile.member_profile WHERE member_id = p_member_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  RETURN jsonb_build_object(
    'member_since', since,
    'reports_total', (SELECT count(*) FROM milavn_safety.report r WHERE r.subject_type = 'user' AND r.subject_id = p_member_id),
    'reports_open', (SELECT count(*) FROM milavn_safety.report r WHERE r.subject_type = 'user' AND r.subject_id = p_member_id AND r.status IN ('open', 'in_review')),
    'restricted', EXISTS (
       SELECT 1 FROM milavn_safety.moderation_action a JOIN milavn_safety.report r ON r.id = a.report_id
        WHERE r.subject_type = 'user' AND r.subject_id = p_member_id AND a.action_type = 'restrict'),
    'blocks_against', (SELECT count(*) FROM milavn_safety.block b WHERE b.blocked_member_id = p_member_id),
    'organizes_count', (SELECT count(*) FROM milavn_circle.circle_membership m
                         WHERE m.member_id = p_member_id AND m.left_at IS NULL AND m.member_role = 'organizer'),
    'organizes_names', coalesce((
       SELECT jsonb_agg(x.name) FROM (
         SELECT c.name FROM milavn_circle.circle_membership m JOIN milavn_circle.circle c ON c.id = m.circle_id
          WHERE m.member_id = p_member_id AND m.left_at IS NULL AND m.member_role = 'organizer'
          ORDER BY c.created_at DESC LIMIT 3) x), '[]'::jsonb),
    'member_of_count', (SELECT count(*) FROM milavn_circle.circle_membership m WHERE m.member_id = p_member_id AND m.left_at IS NULL)
  );
END;
$$;
REVOKE ALL ON FUNCTION milavn_safety.member_admin_summary(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_safety.member_admin_summary(uuid) TO milavn_app;
