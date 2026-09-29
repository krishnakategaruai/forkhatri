-- 049 — Activity chat in Messages, and the social layer of circle posts (owner, 2026-09-29).
--
-- A circle is a community page, never a chat; chats live in Messages. So:
--
--   1. Activity chat. Each occurrence gets one group conversation (kind 'activity') holding the
--      host plus everyone whose RSVP is "going" (or checked in / attended). A trigger on
--      participation keeps it in step: going → added, cancel / leave → removed. About 24 hours
--      after the activity ends the chat closes: read-only, and hidden from the chat list.
--   2. Circle posts gain: announcements (organizer / assistant only, members react but do not
--      reply), pins (organizers, at most 3 per circle), comments (one level under the post; the
--      author or an organizer / assistant deletes) and reactions from a small fixed set
--      ("reactions, not likes" — milavn-social-decisions).
--
-- Safe to run twice.

-- ---------------------------------------------------------------------------------------------
-- 1. Activity chat
-- ---------------------------------------------------------------------------------------------

ALTER TABLE milavn_connect.conversation ADD COLUMN IF NOT EXISTS occurrence_id uuid;
ALTER TABLE milavn_connect.conversation DROP CONSTRAINT IF EXISTS conversation_kind_check;
ALTER TABLE milavn_connect.conversation ADD CONSTRAINT conversation_kind_check CHECK (kind IN ('direct','group','activity'));
CREATE UNIQUE INDEX IF NOT EXISTS conversation_occurrence_uidx ON milavn_connect.conversation (occurrence_id) WHERE occurrence_id IS NOT NULL;

-- When an activity's chat closes: ~24h after it ends (no end time → 3 hours after the start).
CREATE OR REPLACE FUNCTION milavn_connect.activity_chat_closes_at(p_conversation_id uuid)
RETURNS timestamptz LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, milavn_activity, pg_catalog AS $$
  SELECT coalesce(o.time_end, o.time_start + interval '3 hours') + interval '24 hours'
    FROM milavn_connect.conversation c JOIN milavn_activity.occurrence o ON o.id = c.occurrence_id
   WHERE c.id = p_conversation_id;
$$;

CREATE OR REPLACE FUNCTION milavn_connect.is_conversation_closed(p_conversation_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, pg_catalog AS $$
  SELECT coalesce(milavn_connect.activity_chat_closes_at(p_conversation_id) < now(), false);
$$;

-- Brings one occurrence's chat in line with who is going. Creates the chat the first time anyone
-- other than the host is going; never deletes it (history stays for the members who were in it).
CREATE OR REPLACE FUNCTION milavn_connect.sync_activity_chat(p_occurrence_id uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_connect, milavn_activity, pg_catalog AS $$
DECLARE
  cid uuid;
  host uuid;
  ttl text;
  going uuid[];
BEGIN
  SELECT o.creator_member_id, o.title INTO host, ttl FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
  IF host IS NULL THEN RETURN NULL; END IF;
  SELECT coalesce(array_agg(p.member_id), ARRAY[]::uuid[]) INTO going
    FROM milavn_activity.participation p
   WHERE p.occurrence_id = p_occurrence_id AND p.status IN ('going','checked_in','attended') AND p.member_id <> host;
  SELECT id INTO cid FROM milavn_connect.conversation WHERE occurrence_id = p_occurrence_id;
  IF cid IS NULL THEN
    IF cardinality(going) = 0 THEN RETURN NULL; END IF;
    INSERT INTO milavn_connect.conversation (kind, title, created_by, occurrence_id, last_message_at)
    VALUES ('activity', left(ttl, 80), host, p_occurrence_id, now())
    ON CONFLICT (occurrence_id) WHERE occurrence_id IS NOT NULL DO NOTHING
    RETURNING id INTO cid;
    IF cid IS NULL THEN SELECT id INTO cid FROM milavn_connect.conversation WHERE occurrence_id = p_occurrence_id; END IF;
  END IF;
  -- Host + going are in (re-joining clears left_at); everyone else is out.
  INSERT INTO milavn_connect.conversation_member (conversation_id, member_id)
  SELECT cid, m FROM unnest(array_append(going, host)) AS m
  ON CONFLICT (conversation_id, member_id) DO UPDATE SET left_at = NULL
    WHERE milavn_connect.conversation_member.left_at IS NOT NULL;
  UPDATE milavn_connect.conversation_member SET left_at = now()
   WHERE conversation_id = cid AND left_at IS NULL AND member_id <> host AND NOT (member_id = ANY(going));
  RETURN cid;
END;
$$;
REVOKE ALL ON FUNCTION milavn_connect.sync_activity_chat(uuid) FROM PUBLIC;

CREATE OR REPLACE FUNCTION milavn_connect.participation_syncs_activity_chat()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_connect, pg_catalog AS $$
BEGIN
  PERFORM milavn_connect.sync_activity_chat(CASE WHEN TG_OP = 'DELETE' THEN OLD.occurrence_id ELSE NEW.occurrence_id END);
  RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION milavn_connect.participation_syncs_activity_chat() FROM PUBLIC;

DROP TRIGGER IF EXISTS participation_syncs_activity_chat ON milavn_activity.participation;
CREATE TRIGGER participation_syncs_activity_chat
  AFTER INSERT OR DELETE OR UPDATE OF status ON milavn_activity.participation
  FOR EACH ROW EXECUTE FUNCTION milavn_connect.participation_syncs_activity_chat();

-- The activity page's "Chat with people going": the chat id, only for someone in it.
CREATE OR REPLACE FUNCTION milavn_connect.activity_chat_for(p_occurrence_id uuid, p_member uuid)
RETURNS uuid LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, pg_catalog AS $$
  SELECT c.id FROM milavn_connect.conversation c
   WHERE c.occurrence_id = p_occurrence_id
     AND p_member = current_setting('milavn.member_id', true)::uuid
     AND milavn_connect.is_conversation_member(c.id, p_member);
$$;
REVOKE ALL ON FUNCTION milavn_connect.activity_chat_for(uuid, uuid) FROM PUBLIC;

-- A closed chat takes no new messages (reading stays allowed for its members).
DROP POLICY IF EXISTS chat_message_write ON milavn_connect.chat_message;
CREATE POLICY chat_message_write ON milavn_connect.chat_message
  FOR INSERT WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid
                         AND milavn_connect.is_conversation_member(conversation_id, current_setting('milavn.member_id', true)::uuid)
                         AND NOT milavn_connect.is_conversation_closed(conversation_id));

-- Backfill: every activity that has not closed yet gets its chat now.
DO $$
DECLARE o record;
BEGIN
  FOR o IN SELECT id FROM milavn_activity.occurrence
            WHERE coalesce(time_end, time_start + interval '3 hours') + interval '24 hours' > now() LOOP
    PERFORM milavn_connect.sync_activity_chat(o.id);
  END LOOP;
END $$;

GRANT EXECUTE ON FUNCTION milavn_connect.activity_chat_closes_at(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.is_conversation_closed(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.activity_chat_for(uuid, uuid) TO milavn_app;

-- ---------------------------------------------------------------------------------------------
-- 2. Circle posts: announcements, pins, comments, reactions
-- ---------------------------------------------------------------------------------------------

ALTER TABLE milavn_circle.circle_post ADD COLUMN IF NOT EXISTS is_announcement boolean NOT NULL DEFAULT false;
ALTER TABLE milavn_circle.circle_post ADD COLUMN IF NOT EXISTS pinned_at timestamptz;
CREATE INDEX IF NOT EXISTS circle_post_pinned_idx ON milavn_circle.circle_post (circle_id) WHERE pinned_at IS NOT NULL AND deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS milavn_circle.circle_post_comment (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id    uuid NOT NULL REFERENCES milavn_circle.circle_post(id) ON DELETE CASCADE,
  circle_id  uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  member_id  uuid NOT NULL,
  body       text NOT NULL CHECK (length(body) BETWEEN 1 AND 500),
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);
CREATE INDEX IF NOT EXISTS circle_post_comment_post_idx ON milavn_circle.circle_post_comment (post_id, created_at);

CREATE TABLE IF NOT EXISTS milavn_circle.circle_post_reaction (
  post_id    uuid NOT NULL REFERENCES milavn_circle.circle_post(id) ON DELETE CASCADE,
  circle_id  uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  member_id  uuid NOT NULL,
  emoji      text NOT NULL CHECK (emoji IN ('❤️','👏','😂','🙏','🎉')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (post_id, member_id, emoji)
);

-- Members (and the creator) read; every write goes through the definer functions below.
ALTER TABLE milavn_circle.circle_post_comment ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_post_comment_members ON milavn_circle.circle_post_comment;
CREATE POLICY circle_post_comment_members ON milavn_circle.circle_post_comment
  FOR SELECT USING (
    milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
    OR milavn_circle.is_circle_creator(circle_id, current_setting('milavn.member_id', true)::uuid));
ALTER TABLE milavn_circle.circle_post_reaction ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_post_reaction_members ON milavn_circle.circle_post_reaction;
CREATE POLICY circle_post_reaction_members ON milavn_circle.circle_post_reaction
  FOR SELECT USING (
    milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
    OR milavn_circle.is_circle_creator(circle_id, current_setting('milavn.member_id', true)::uuid));
GRANT SELECT ON milavn_circle.circle_post_comment TO milavn_app;
GRANT SELECT ON milavn_circle.circle_post_reaction TO milavn_app;

-- Organizer / assistant pins or unpins. 'pinned' | 'unpinned' | 'limit' | 'not_allowed' | 'not_found'
CREATE OR REPLACE FUNCTION milavn_circle.pin_circle_post(p_circle_id uuid, p_post_id uuid, p_actor uuid, p_pin boolean)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  actor_role text;
  n integer;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  actor_role := milavn_circle.current_role_of(p_circle_id, p_actor);
  IF actor_role IS NULL THEN RETURN 'not_found'; END IF;
  IF actor_role NOT IN ('organizer','assistant') THEN RETURN 'not_allowed'; END IF;
  PERFORM 1 FROM milavn_circle.circle WHERE id = p_circle_id FOR UPDATE;  -- serialise the 3-pin count
  IF NOT EXISTS (SELECT 1 FROM milavn_circle.circle_post WHERE id = p_post_id AND circle_id = p_circle_id AND deleted_at IS NULL) THEN
    RETURN 'not_found';
  END IF;
  IF NOT p_pin THEN
    UPDATE milavn_circle.circle_post SET pinned_at = NULL WHERE id = p_post_id;
    RETURN 'unpinned';
  END IF;
  SELECT count(*) INTO n FROM milavn_circle.circle_post
   WHERE circle_id = p_circle_id AND pinned_at IS NOT NULL AND deleted_at IS NULL AND id <> p_post_id;
  IF n >= 3 THEN RETURN 'limit'; END IF;
  UPDATE milavn_circle.circle_post SET pinned_at = coalesce(pinned_at, now()) WHERE id = p_post_id;
  RETURN 'pinned';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.pin_circle_post(uuid, uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.pin_circle_post(uuid, uuid, uuid, boolean) TO milavn_app;

-- Any member comments, except under an announcement. Returns the comment id, or NULL with
-- r_outcome 'not_found' | 'announcement' | 'not_allowed'.
CREATE OR REPLACE FUNCTION milavn_circle.add_post_comment(p_circle_id uuid, p_post_id uuid, p_actor uuid, p_body text)
RETURNS TABLE (r_outcome text, r_comment_id uuid) LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  v_ann boolean;
  cid uuid;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN
    RETURN QUERY SELECT 'not_allowed'::text, NULL::uuid; RETURN;
  END IF;
  IF milavn_circle.current_role_of(p_circle_id, p_actor) IS NULL THEN
    RETURN QUERY SELECT 'not_found'::text, NULL::uuid; RETURN;
  END IF;
  SELECT is_announcement INTO v_ann FROM milavn_circle.circle_post WHERE id = p_post_id AND circle_id = p_circle_id AND deleted_at IS NULL;
  IF v_ann IS NULL THEN RETURN QUERY SELECT 'not_found'::text, NULL::uuid; RETURN; END IF;
  IF v_ann THEN RETURN QUERY SELECT 'announcement'::text, NULL::uuid; RETURN; END IF;
  INSERT INTO milavn_circle.circle_post_comment (post_id, circle_id, member_id, body)
  VALUES (p_post_id, p_circle_id, p_actor, p_body) RETURNING id INTO cid;
  RETURN QUERY SELECT 'added'::text, cid;
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.add_post_comment(uuid, uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.add_post_comment(uuid, uuid, uuid, text) TO milavn_app;

-- The comment's author, or the circle's organizer / assistant. 'deleted' | 'not_found' | 'not_allowed'
CREATE OR REPLACE FUNCTION milavn_circle.delete_post_comment(p_circle_id uuid, p_comment_id uuid, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE
  v_author uuid;
  actor_role text;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  SELECT member_id INTO v_author FROM milavn_circle.circle_post_comment
   WHERE id = p_comment_id AND circle_id = p_circle_id AND deleted_at IS NULL;
  actor_role := milavn_circle.current_role_of(p_circle_id, p_actor);
  IF v_author IS NULL OR (actor_role IS NULL AND v_author IS DISTINCT FROM p_actor) THEN RETURN 'not_found'; END IF;
  IF v_author IS DISTINCT FROM p_actor AND actor_role NOT IN ('organizer','assistant') THEN RETURN 'not_allowed'; END IF;
  UPDATE milavn_circle.circle_post_comment SET deleted_at = now() WHERE id = p_comment_id;
  RETURN 'deleted';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.delete_post_comment(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.delete_post_comment(uuid, uuid, uuid) TO milavn_app;

-- Toggle one reaction. 'added' | 'removed' | 'not_found' | 'not_allowed' | 'bad_emoji'
CREATE OR REPLACE FUNCTION milavn_circle.toggle_post_reaction(p_circle_id uuid, p_post_id uuid, p_actor uuid, p_emoji text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN 'not_allowed'; END IF;
  IF p_emoji NOT IN ('❤️','👏','😂','🙏','🎉') THEN RETURN 'bad_emoji'; END IF;
  IF milavn_circle.current_role_of(p_circle_id, p_actor) IS NULL
     OR NOT EXISTS (SELECT 1 FROM milavn_circle.circle_post WHERE id = p_post_id AND circle_id = p_circle_id AND deleted_at IS NULL) THEN
    RETURN 'not_found';
  END IF;
  DELETE FROM milavn_circle.circle_post_reaction WHERE post_id = p_post_id AND member_id = p_actor AND emoji = p_emoji;
  IF FOUND THEN RETURN 'removed'; END IF;
  INSERT INTO milavn_circle.circle_post_reaction (post_id, circle_id, member_id, emoji) VALUES (p_post_id, p_circle_id, p_actor, p_emoji);
  RETURN 'added';
END;
$$;
REVOKE ALL ON FUNCTION milavn_circle.toggle_post_reaction(uuid, uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.toggle_post_reaction(uuid, uuid, uuid, text) TO milavn_app;

-- The notification fan-out (a process session with no member context) reads an announcement's text.
CREATE OR REPLACE FUNCTION milavn_circle.announcement_text(p_post_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT body FROM milavn_circle.circle_post WHERE id = p_post_id AND is_announcement AND deleted_at IS NULL;
$$;
REVOKE ALL ON FUNCTION milavn_circle.announcement_text(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_circle.announcement_text(uuid) TO milavn_app;
