-- 053 — Circle social (Phase 2, Step 6; owner approved 2026-10-05).
--
--   1. A circle post carries several photos and files (circle_post_media). Older posts keep their
--      single photo_ref / doc_ref; new posts put every attachment here. Private like every other
--      circle file: served only through circle_media_access (045).
--   2. Circle photo albums: members add photos to named albums; the uploader, an organizer or an
--      assistant removes a photo; an organizer or assistant removes an album.
--   3. Notifications for circle activity, with a per-circle setting per member:
--        all         every new post, plus the highlights
--        highlights  announcements, new events and questions (polls) only
--        off         nothing from this circle
--      New posts are grouped: while "N new posts in <circle>" is unread it is updated in place, and
--      a push goes out at most once an hour per circle per person. The author is never told.
--   4. Circles co-hosting an event: the event's host invites another circle; that circle's
--      organizer accepts. The event then shows in both circles and both circles' members can see it.
--
-- Safe to run twice.

-- ---------------------------------------------------------------------------------------------
-- 1. Several attachments per post
-- ---------------------------------------------------------------------------------------------

ALTER TABLE milavn_circle.circle_post ADD COLUMN IF NOT EXISTS attachment_count smallint NOT NULL DEFAULT 0;
ALTER TABLE milavn_circle.circle_post DROP CONSTRAINT IF EXISTS circle_post_body_check;
ALTER TABLE milavn_circle.circle_post ADD CONSTRAINT circle_post_body_check
  CHECK (length(body) <= 1000 AND (length(body) >= 1 OR photo_ref IS NOT NULL OR doc_ref IS NOT NULL OR attachment_count > 0));

CREATE TABLE IF NOT EXISTS milavn_circle.circle_post_media (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id     uuid NOT NULL REFERENCES milavn_circle.circle_post(id) ON DELETE CASCADE,
  circle_id   uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  kind        text NOT NULL CHECK (kind IN ('photo', 'doc')),
  storage_ref text NOT NULL UNIQUE,
  file_name   text CHECK (file_name IS NULL OR length(file_name) <= 120),
  byte_size   bigint,
  position    smallint NOT NULL DEFAULT 0,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS circle_post_media_post_idx ON milavn_circle.circle_post_media (post_id, position);

ALTER TABLE milavn_circle.circle_post_media ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_post_media_members ON milavn_circle.circle_post_media;
CREATE POLICY circle_post_media_members ON milavn_circle.circle_post_media
  FOR SELECT USING (
    milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
    OR milavn_circle.is_circle_creator(circle_id, current_setting('milavn.member_id', true)::uuid));
-- Only onto your own live post, in the post's own circle.
DROP POLICY IF EXISTS circle_post_media_author_adds ON milavn_circle.circle_post_media;
CREATE POLICY circle_post_media_author_adds ON milavn_circle.circle_post_media
  FOR INSERT WITH CHECK (EXISTS (
    SELECT 1 FROM milavn_circle.circle_post p
     WHERE p.id = circle_post_media.post_id AND p.circle_id = circle_post_media.circle_id
       AND p.member_id = current_setting('milavn.member_id', true)::uuid AND p.deleted_at IS NULL));
GRANT SELECT, INSERT ON milavn_circle.circle_post_media TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- 2. Albums
-- ---------------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS milavn_circle.circle_album (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id            uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  name                 text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 60),
  created_by_member_id uuid NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS circle_album_name_uidx ON milavn_circle.circle_album (circle_id, lower(btrim(name)));

CREATE TABLE IF NOT EXISTS milavn_circle.circle_album_photo (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  album_id    uuid NOT NULL REFERENCES milavn_circle.circle_album(id) ON DELETE CASCADE,
  circle_id   uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  member_id   uuid NOT NULL,
  storage_ref text NOT NULL UNIQUE,
  caption     text CHECK (caption IS NULL OR length(caption) <= 200),
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS circle_album_photo_album_idx ON milavn_circle.circle_album_photo (album_id, created_at DESC);

ALTER TABLE milavn_circle.circle_album ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_album_members ON milavn_circle.circle_album;
CREATE POLICY circle_album_members ON milavn_circle.circle_album
  FOR SELECT USING (
    milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
    OR milavn_circle.is_circle_creator(circle_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS circle_album_member_creates ON milavn_circle.circle_album;
CREATE POLICY circle_album_member_creates ON milavn_circle.circle_album
  FOR INSERT WITH CHECK (
    created_by_member_id = current_setting('milavn.member_id', true)::uuid
    AND milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid));

ALTER TABLE milavn_circle.circle_album_photo ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_album_photo_members ON milavn_circle.circle_album_photo;
CREATE POLICY circle_album_photo_members ON milavn_circle.circle_album_photo
  FOR SELECT USING (
    milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
    OR milavn_circle.is_circle_creator(circle_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS circle_album_photo_member_adds ON milavn_circle.circle_album_photo;
CREATE POLICY circle_album_photo_member_adds ON milavn_circle.circle_album_photo
  FOR INSERT WITH CHECK (
    member_id = current_setting('milavn.member_id', true)::uuid
    AND milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
    AND EXISTS (SELECT 1 FROM milavn_circle.circle_album a WHERE a.id = circle_album_photo.album_id AND a.circle_id = circle_album_photo.circle_id));
GRANT SELECT, INSERT ON milavn_circle.circle_album TO milavn_app;
GRANT SELECT, INSERT ON milavn_circle.circle_album_photo TO milavn_app;

-- The uploader, or the circle's organizer / assistant, removes one photo. Returns the file's ref
-- so the API can delete it from disk; r_outcome 'removed' | 'not_found' | 'not_allowed'.
CREATE OR REPLACE FUNCTION milavn_circle.remove_album_photo(p_circle_id uuid, p_photo_id uuid, p_actor uuid)
RETURNS TABLE (r_outcome text, r_ref text) LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  v_author uuid;
  v_ref text;
  actor_role text;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN
    RETURN QUERY SELECT 'not_allowed'::text, NULL::text; RETURN;
  END IF;
  SELECT member_id, storage_ref INTO v_author, v_ref FROM milavn_circle.circle_album_photo
   WHERE id = p_photo_id AND circle_id = p_circle_id;
  actor_role := milavn_circle.current_role_of(p_circle_id, p_actor);
  IF v_author IS NULL OR (actor_role IS NULL AND v_author IS DISTINCT FROM p_actor) THEN
    RETURN QUERY SELECT 'not_found'::text, NULL::text; RETURN;
  END IF;
  IF v_author IS DISTINCT FROM p_actor AND actor_role NOT IN ('organizer', 'assistant') THEN
    RETURN QUERY SELECT 'not_allowed'::text, NULL::text; RETURN;
  END IF;
  DELETE FROM milavn_circle.circle_album_photo WHERE id = p_photo_id;
  RETURN QUERY SELECT 'removed'::text, v_ref;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.remove_album_photo(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.remove_album_photo(uuid, uuid, uuid) TO milavn_app;

-- An organizer or assistant removes a whole album (its photos go with it). Returns every file ref.
-- r_outcome 'removed' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_circle.remove_circle_album(p_circle_id uuid, p_album_id uuid, p_actor uuid)
RETURNS TABLE (r_outcome text, r_refs text[]) LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  actor_role text;
  refs text[];
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN
    RETURN QUERY SELECT 'not_allowed'::text, NULL::text[]; RETURN;
  END IF;
  actor_role := milavn_circle.current_role_of(p_circle_id, p_actor);
  IF actor_role IS NULL OR NOT EXISTS (SELECT 1 FROM milavn_circle.circle_album WHERE id = p_album_id AND circle_id = p_circle_id) THEN
    RETURN QUERY SELECT 'not_found'::text, NULL::text[]; RETURN;
  END IF;
  IF actor_role NOT IN ('organizer', 'assistant') THEN
    RETURN QUERY SELECT 'not_allowed'::text, NULL::text[]; RETURN;
  END IF;
  SELECT coalesce(array_agg(storage_ref), ARRAY[]::text[]) INTO refs FROM milavn_circle.circle_album_photo WHERE album_id = p_album_id;
  DELETE FROM milavn_circle.circle_album WHERE id = p_album_id;
  RETURN QUERY SELECT 'removed'::text, refs;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.remove_circle_album(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.remove_circle_album(uuid, uuid, uuid) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- 1+2. Who may open a circle file: now also a post's extra attachments and album photos.
-- kind: 'cover' | 'photo' | 'doc' | 'album'. Same rules as 045 for everything but covers:
-- an active member, the circle's creator, or a moderator; a taken-down post's files are gone.
-- ---------------------------------------------------------------------------------------------
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
    IF NOT FOUND THEN
      SELECT m.circle_id, m.kind, m.file_name INTO c_id, k, dn
        FROM milavn_circle.circle_post_media m JOIN milavn_circle.circle_post p ON p.id = m.post_id
       WHERE m.storage_ref = p_ref AND p.deleted_at IS NULL
       LIMIT 1;
      IF NOT FOUND THEN
        SELECT ap.circle_id, 'album', NULL INTO c_id, k, dn
          FROM milavn_circle.circle_album_photo ap WHERE ap.storage_ref = p_ref LIMIT 1;
        IF NOT FOUND THEN RETURN; END IF;
      END IF;
    END IF;
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
-- 3. Per-circle notification setting, recipients, grouped delivery
-- ---------------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS milavn_circle.circle_notify_setting (
  circle_id  uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  member_id  uuid NOT NULL,
  level      text NOT NULL CHECK (level IN ('all', 'highlights', 'off')),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (circle_id, member_id)
);
ALTER TABLE milavn_circle.circle_notify_setting ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_notify_setting_self ON milavn_circle.circle_notify_setting;
CREATE POLICY circle_notify_setting_self ON milavn_circle.circle_notify_setting
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid
              AND milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid));
GRANT SELECT, INSERT, UPDATE, DELETE ON milavn_circle.circle_notify_setting TO milavn_app;

-- Who hears about something in a circle (the dispatcher has no member context, hence definer):
-- active members, never the person who caused it, never someone who blocked them (or was blocked),
-- and only as far as each member's own setting allows. p_highlight: announcements, events, polls.
CREATE OR REPLACE FUNCTION milavn_circle.circle_notify_recipients(p_circle_id uuid, p_actor uuid, p_highlight boolean)
RETURNS TABLE (member_id uuid, lang text) LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT m.member_id, coalesce(milavn_profile.language_of(m.member_id), 'en')
    FROM milavn_circle.circle_membership m
    LEFT JOIN milavn_circle.circle_notify_setting s ON s.circle_id = m.circle_id AND s.member_id = m.member_id
   WHERE m.circle_id = p_circle_id AND m.left_at IS NULL
     AND m.member_id IS DISTINCT FROM p_actor
     AND coalesce(s.level, 'all') <> 'off'
     AND (p_highlight OR coalesce(s.level, 'all') = 'all')
     AND (p_actor IS NULL OR NOT milavn_safety.is_blocked_either_way(m.member_id, p_actor));
$$;
REVOKE ALL ON FUNCTION milavn_circle.circle_notify_recipients(uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.circle_notify_recipients(uuid, uuid, boolean) TO milavn_app;

-- What a new-post notification says, read by the dispatcher (no member context).
CREATE OR REPLACE FUNCTION milavn_circle.post_brief(p_post_id uuid)
RETURNS TABLE (circle_id uuid, member_id uuid, body text, photos integer, docs integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT p.circle_id, p.member_id, p.body,
         (CASE WHEN p.photo_ref IS NOT NULL THEN 1 ELSE 0 END
          + (SELECT count(*) FROM milavn_circle.circle_post_media m WHERE m.post_id = p.id AND m.kind = 'photo'))::integer,
         (CASE WHEN p.doc_ref IS NOT NULL THEN 1 ELSE 0 END
          + (SELECT count(*) FROM milavn_circle.circle_post_media m WHERE m.post_id = p.id AND m.kind = 'doc'))::integer
    FROM milavn_circle.circle_post p WHERE p.id = p_post_id AND p.deleted_at IS NULL;
$$;
REVOKE ALL ON FUNCTION milavn_circle.post_brief(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.post_brief(uuid) TO milavn_app;

-- A poll's question and its most-picked answer, for the dispatcher.
CREATE OR REPLACE FUNCTION milavn_circle.poll_brief(p_poll_id uuid)
RETURNS TABLE (circle_id uuid, created_by uuid, question text, top_label text, top_time timestamptz, top_votes integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT p.circle_id, p.created_by_member_id, p.question, t.label, t.option_time, coalesce(t.n, 0)::integer
    FROM milavn_circle.poll p
    LEFT JOIN LATERAL (
      SELECT o.label, o.option_time, count(v.member_id) AS n
        FROM milavn_circle.poll_option o LEFT JOIN milavn_circle.poll_vote v ON v.option_id = o.id
       WHERE o.poll_id = p.id
       GROUP BY o.id, o.label, o.option_time, o.position
       ORDER BY count(v.member_id) DESC, o.position ASC
       LIMIT 1) t ON true
   WHERE p.id = p_poll_id;
$$;
REVOKE ALL ON FUNCTION milavn_circle.poll_brief(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.poll_brief(uuid) TO milavn_app;

-- Grouped inbox entries: "3 new posts in <circle>" instead of three entries.
ALTER TABLE milavn_notification.notification_inbox_entry ADD COLUMN IF NOT EXISTS group_key text;
ALTER TABLE milavn_notification.notification_inbox_entry ADD COLUMN IF NOT EXISTS group_count integer NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS notification_inbox_group_idx
  ON milavn_notification.notification_inbox_entry (member_id, group_key) WHERE group_key IS NOT NULL AND read_at IS NULL;

-- Like deliver(), for a burst-prone kind. While an unread entry with the same key exists (24h), it
-- is updated in place (count + 1, newest text, moved to the top) instead of adding another. A push
-- (outbox row) goes out at most once per hour per key. p_title_many carries '{n}' for the count.
CREATE OR REPLACE FUNCTION milavn_notification.deliver_grouped(
  p_member_id uuid, p_class text, p_title_one text, p_title_many text, p_body text, p_deep_link text, p_group_key text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_notification, pg_catalog AS $$
DECLARE
  muted_pref boolean;
  e_id uuid;
  e_count integer;
  t text := p_title_one;
BEGIN
  SELECT muted INTO muted_pref FROM milavn_notification.notification_preference
   WHERE member_id = p_member_id AND notification_class = p_class::milavn_notification.notification_class;
  IF p_class <> 'important' AND coalesce(muted_pref, false) THEN RETURN; END IF;
  SELECT id, group_count INTO e_id, e_count FROM milavn_notification.notification_inbox_entry
   WHERE member_id = p_member_id AND group_key = p_group_key AND read_at IS NULL
     AND created_at > now() - interval '24 hours'
   ORDER BY created_at DESC LIMIT 1 FOR UPDATE;
  IF e_id IS NOT NULL THEN
    t := replace(p_title_many, '{n}', (e_count + 1)::text);
    UPDATE milavn_notification.notification_inbox_entry
       SET group_count = e_count + 1, title = t, body = p_body, deep_link = p_deep_link, created_at = now()
     WHERE id = e_id;
  ELSE
    INSERT INTO milavn_notification.notification_inbox_entry
      (member_id, notification_class, title, body, deep_link, source_occurrence_id, group_key, group_count)
    VALUES (p_member_id, p_class::milavn_notification.notification_class, t, p_body, p_deep_link, NULL, p_group_key, 1);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM milavn_notification.notification_outbox
     WHERE member_id = p_member_id AND payload->>'group_key' = p_group_key AND created_at > now() - interval '1 hour'
  ) THEN
    INSERT INTO milavn_notification.notification_outbox (member_id, notification_class, payload)
    VALUES (p_member_id, p_class::milavn_notification.notification_class,
            jsonb_build_object('title', t, 'body', p_body, 'deep_link', p_deep_link, 'occurrence_id', NULL, 'group_key', p_group_key));
  END IF;
END;
$$;
REVOKE ALL ON FUNCTION milavn_notification.deliver_grouped(uuid, text, text, text, text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_notification.deliver_grouped(uuid, text, text, text, text, text, text) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- 4. Circles co-hosting an event
-- ---------------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_cohost (
  occurrence_id        uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  circle_id            uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  status               text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined')),
  invited_by_member_id uuid NOT NULL,
  decided_by_member_id uuid,
  created_at           timestamptz NOT NULL DEFAULT now(),
  decided_at           timestamptz,
  PRIMARY KEY (occurrence_id, circle_id)
);
CREATE INDEX IF NOT EXISTS occurrence_cohost_circle_idx ON milavn_activity.occurrence_cohost (circle_id, status);
-- Every read and write goes through the definer functions below; the table itself is closed.
ALTER TABLE milavn_activity.occurrence_cohost ENABLE ROW LEVEL SECURITY;

-- The event's managers today: its creator or an active co-organizer.
CREATE OR REPLACE FUNCTION milavn_activity.is_event_manager(p_occurrence_id uuid, p_member uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id AND o.creator_member_id = p_member)
      OR EXISTS (SELECT 1 FROM milavn_activity.occurrence_co_organizer c
                  WHERE c.occurrence_id = p_occurrence_id AND c.member_id = p_member AND c.revoked_at IS NULL);
$$;
REVOKE ALL ON FUNCTION milavn_activity.is_event_manager(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.is_event_manager(uuid, uuid) TO milavn_app;

-- A co-hosting circle's members see the event (accepted); the invited circle's organizer sees it
-- while deciding (pending). Definer, so the occurrence policy below does not recurse.
CREATE OR REPLACE FUNCTION milavn_activity.cohost_can_see(p_occurrence_id uuid, p_member uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT p_member IS NOT NULL AND EXISTS (
    SELECT 1 FROM milavn_activity.occurrence_cohost h
     WHERE h.occurrence_id = p_occurrence_id
       AND ((h.status = 'accepted' AND milavn_circle.is_active_member(h.circle_id, p_member))
         OR (h.status = 'pending' AND milavn_circle.current_role_of(h.circle_id, p_member) = 'organizer')));
$$;
REVOKE ALL ON FUNCTION milavn_activity.cohost_can_see(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.cohost_can_see(uuid, uuid) TO milavn_app;

-- 001's occurrence visibility, plus the co-hosting circles.
DROP POLICY IF EXISTS occurrence_visibility ON milavn_activity.occurrence;
CREATE POLICY occurrence_visibility ON milavn_activity.occurrence
  FOR SELECT
  USING (
    visibility_scope IN ('public','community','organization')
    OR creator_member_id = current_setting('milavn.member_id', true)::uuid
    OR EXISTS (
      SELECT 1 FROM milavn_activity.occurrence_co_organizer oco
      WHERE oco.occurrence_id = occurrence.id
        AND oco.member_id = current_setting('milavn.member_id', true)::uuid
        AND oco.revoked_at IS NULL
    )
    OR (
      visibility_scope = 'circle' AND circle_id IS NOT NULL
      AND milavn_circle.is_active_member(occurrence.circle_id, current_setting('milavn.member_id', true)::uuid)
    )
    OR milavn_activity.cohost_can_see(occurrence.id, current_setting('milavn.member_id', true)::uuid)
  );

-- The event's host (creator / co-organizer) invites a circle. The circle must be one the host can
-- see (open, or one they belong to), not the event's own circle, at most 3 per event. An organizer
-- inviting their own circle needs no second step: it is accepted at once.
-- 'invited' | 'accepted' | 'already' | 'declined_before' | 'limit' | 'own_circle' | 'ended' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_activity.invite_cohost_circle(p_occurrence_id uuid, p_circle_id uuid, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE
  o record;
  c_type text;
  existing text;
  n integer;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  SELECT id, circle_id, status::text AS status, coalesce(time_end, time_start + interval '3 hours') AS ends INTO o
    FROM milavn_activity.occurrence WHERE id = p_occurrence_id FOR UPDATE;
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  IF NOT milavn_activity.is_event_manager(p_occurrence_id, p_actor) THEN RETURN 'not_allowed'; END IF;
  IF o.status <> 'active' OR o.ends < now() THEN RETURN 'ended'; END IF;
  SELECT circle_type::text INTO c_type FROM milavn_circle.circle WHERE id = p_circle_id;
  IF c_type IS NULL OR NOT (milavn_circle.is_joinable_type(c_type::milavn_circle.circle_type)
                            OR milavn_circle.is_active_member(p_circle_id, p_actor)) THEN
    RETURN 'not_found';
  END IF;
  IF o.circle_id = p_circle_id THEN RETURN 'own_circle'; END IF;
  SELECT status INTO existing FROM milavn_activity.occurrence_cohost WHERE occurrence_id = p_occurrence_id AND circle_id = p_circle_id;
  IF existing IN ('pending', 'accepted') THEN RETURN 'already'; END IF;
  IF existing = 'declined' THEN RETURN 'declined_before'; END IF;
  SELECT count(*) INTO n FROM milavn_activity.occurrence_cohost WHERE occurrence_id = p_occurrence_id AND status IN ('pending', 'accepted');
  IF n >= 3 THEN RETURN 'limit'; END IF;
  IF milavn_circle.current_role_of(p_circle_id, p_actor) = 'organizer' THEN
    INSERT INTO milavn_activity.occurrence_cohost (occurrence_id, circle_id, status, invited_by_member_id, decided_by_member_id, decided_at)
    VALUES (p_occurrence_id, p_circle_id, 'accepted', p_actor, p_actor, now());
    RETURN 'accepted';
  END IF;
  INSERT INTO milavn_activity.occurrence_cohost (occurrence_id, circle_id, invited_by_member_id)
  VALUES (p_occurrence_id, p_circle_id, p_actor);
  RETURN 'invited';
END;
$$;
REVOKE ALL ON FUNCTION milavn_activity.invite_cohost_circle(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.invite_cohost_circle(uuid, uuid, uuid) TO milavn_app;

-- The invited circle's organizer answers. 'accepted' | 'declined' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_activity.respond_cohost_invite(p_occurrence_id uuid, p_circle_id uuid, p_actor uuid, p_accept boolean)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  IF milavn_circle.current_role_of(p_circle_id, p_actor) IS DISTINCT FROM 'organizer' THEN RETURN 'not_found'; END IF;
  UPDATE milavn_activity.occurrence_cohost
     SET status = CASE WHEN p_accept THEN 'accepted' ELSE 'declined' END,
         decided_by_member_id = p_actor, decided_at = now()
   WHERE occurrence_id = p_occurrence_id AND circle_id = p_circle_id AND status = 'pending';
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  RETURN CASE WHEN p_accept THEN 'accepted' ELSE 'declined' END;
END;
$$;
REVOKE ALL ON FUNCTION milavn_activity.respond_cohost_invite(uuid, uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.respond_cohost_invite(uuid, uuid, uuid, boolean) TO milavn_app;

-- The event's host withdraws an invitation (or ends a co-hosting); the co-hosting circle's
-- organizer steps their circle out. 'removed' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_activity.remove_cohost(p_occurrence_id uuid, p_circle_id uuid, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  IF NOT (milavn_activity.is_event_manager(p_occurrence_id, p_actor)
          OR milavn_circle.current_role_of(p_circle_id, p_actor) = 'organizer') THEN
    RETURN 'not_allowed';
  END IF;
  DELETE FROM milavn_activity.occurrence_cohost
   WHERE occurrence_id = p_occurrence_id AND circle_id = p_circle_id AND status IN ('pending', 'accepted');
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  RETURN 'removed';
END;
$$;
REVOKE ALL ON FUNCTION milavn_activity.remove_cohost(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.remove_cohost(uuid, uuid, uuid) TO milavn_app;

-- The co-hosting circles of one event. The API calls this only after the viewer has read the
-- occurrence through its RLS (so it is visible to them); pending / declined rows only for the
-- event's managers.
CREATE OR REPLACE FUNCTION milavn_activity.occurrence_cohosts(p_occurrence_id uuid, p_viewer uuid)
RETURNS TABLE (circle_id uuid, name text, status text, cover_ref text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT h.circle_id, c.name, h.status, c.cover_ref
    FROM milavn_activity.occurrence_cohost h JOIN milavn_circle.circle c ON c.id = h.circle_id
   WHERE h.occurrence_id = p_occurrence_id
     AND p_viewer = current_setting('milavn.member_id', true)::uuid
     AND (h.status = 'accepted' OR milavn_activity.is_event_manager(p_occurrence_id, p_viewer))
   ORDER BY h.created_at;
$$;
REVOKE ALL ON FUNCTION milavn_activity.occurrence_cohosts(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.occurrence_cohosts(uuid, uuid) TO milavn_app;

-- Pending co-host invitations to one circle, for its organizer only (they may not see the event's
-- own circle, so this is definer).
CREATE OR REPLACE FUNCTION milavn_activity.cohost_invites_for_circle(p_circle_id uuid, p_viewer uuid)
RETURNS TABLE (occurrence_id uuid, title text, slug text, time_start timestamptz, invited_by uuid, host_circle_name text, created_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT o.id, o.title, o.canonical_url_slug, o.time_start, h.invited_by_member_id, hc.name, h.created_at
    FROM milavn_activity.occurrence_cohost h
    JOIN milavn_activity.occurrence o ON o.id = h.occurrence_id
    LEFT JOIN milavn_circle.circle hc ON hc.id = o.circle_id
   WHERE h.circle_id = p_circle_id AND h.status = 'pending' AND o.status = 'active'
     AND p_viewer = current_setting('milavn.member_id', true)::uuid
     AND milavn_circle.current_role_of(p_circle_id, p_viewer) = 'organizer'
   ORDER BY o.time_start;
$$;
REVOKE ALL ON FUNCTION milavn_activity.cohost_invites_for_circle(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.cohost_invites_for_circle(uuid, uuid) TO milavn_app;

-- The events a circle co-hosts (accepted). The API then reads each through occurrence RLS.
CREATE OR REPLACE FUNCTION milavn_activity.cohosted_occurrence_ids(p_circle_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT coalesce(array_agg(occurrence_id), ARRAY[]::uuid[])
    FROM milavn_activity.occurrence_cohost WHERE circle_id = p_circle_id AND status = 'accepted';
$$;
REVOKE ALL ON FUNCTION milavn_activity.cohosted_occurrence_ids(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.cohosted_occurrence_ids(uuid) TO milavn_app;

-- For the dispatcher: the event's own circle and its creator.
CREATE OR REPLACE FUNCTION milavn_activity.cohost_event_brief(p_occurrence_id uuid)
RETURNS TABLE (title text, slug text, host_circle_id uuid, creator uuid)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT o.title, o.canonical_url_slug, o.circle_id, o.creator_member_id FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
$$;
REVOKE ALL ON FUNCTION milavn_activity.cohost_event_brief(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.cohost_event_brief(uuid) TO milavn_app;
