-- 015 — Messaging (owner decision 2026-09-14, recorded in DESIGN-DIRECTION-2030.md
-- and milavn-social-decisions): 1:1 and group chats, reactions, presence and
-- live expressions — trust-scoped. You can only message people you already
-- share an activity or a circle with (can_message), never strangers.
--
--   conversation / conversation_member / chat_message / message_reaction
--   presence — heartbeat + current expression; read only through presence_of()
--
-- Every visibility rule is a definer helper; RLS delegates to them.

CREATE SCHEMA IF NOT EXISTS milavn_connect;
GRANT USAGE ON SCHEMA milavn_connect TO milavn_app;

CREATE TABLE IF NOT EXISTS milavn_connect.conversation (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind            text NOT NULL CHECK (kind IN ('direct','group')),
  title           text CHECK (title IS NULL OR length(title) <= 80),
  created_by      uuid NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  last_message_at timestamptz
);
CREATE TABLE IF NOT EXISTS milavn_connect.conversation_member (
  conversation_id uuid NOT NULL REFERENCES milavn_connect.conversation(id) ON DELETE CASCADE,
  member_id       uuid NOT NULL,
  joined_at       timestamptz NOT NULL DEFAULT now(),
  left_at         timestamptz,
  last_read_at    timestamptz,
  muted           boolean NOT NULL DEFAULT false,
  PRIMARY KEY (conversation_id, member_id)
);
CREATE INDEX IF NOT EXISTS conversation_member_member_idx ON milavn_connect.conversation_member (member_id) WHERE left_at IS NULL;
CREATE TABLE IF NOT EXISTS milavn_connect.chat_message (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES milavn_connect.conversation(id) ON DELETE CASCADE,
  member_id       uuid NOT NULL,
  kind            text NOT NULL DEFAULT 'text' CHECK (kind IN ('text','photo','expression')),
  body            text CHECK (body IS NULL OR length(body) <= 2000),
  media_ref       text,
  expression      text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  deleted_at      timestamptz
);
CREATE INDEX IF NOT EXISTS chat_message_conv_idx ON milavn_connect.chat_message (conversation_id, created_at);
CREATE TABLE IF NOT EXISTS milavn_connect.message_reaction (
  message_id uuid NOT NULL REFERENCES milavn_connect.chat_message(id) ON DELETE CASCADE,
  member_id  uuid NOT NULL,
  emoji      text NOT NULL CHECK (length(emoji) <= 8),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (message_id, member_id, emoji)
);
CREATE TABLE IF NOT EXISTS milavn_connect.presence (
  member_id        uuid PRIMARY KEY,
  last_seen_at     timestamptz NOT NULL DEFAULT now(),
  expression       text,
  at_occurrence_id uuid
);

-- ---- helpers -----------------------------------------------------------------

CREATE OR REPLACE FUNCTION milavn_connect.is_conversation_member(p_conversation_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_connect.conversation_member m
                 WHERE m.conversation_id = p_conversation_id AND m.member_id = p_member_id AND m.left_at IS NULL);
$$;

-- Trust scope: a shared active circle, or a shared occurrence (either as participants or as organizer + participant).
CREATE OR REPLACE FUNCTION milavn_connect.can_message(p_a uuid, p_b uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, milavn_circle, milavn_activity, milavn_safety, pg_catalog AS $$
  SELECT p_a <> p_b
    AND NOT milavn_safety.is_blocked_either_way(p_a, p_b)
    AND (
      EXISTS (SELECT 1 FROM milavn_circle.circle_membership x JOIN milavn_circle.circle_membership y ON x.circle_id = y.circle_id
              WHERE x.member_id = p_a AND y.member_id = p_b AND x.left_at IS NULL AND y.left_at IS NULL)
      OR EXISTS (SELECT 1 FROM milavn_activity.participation x JOIN milavn_activity.participation y ON x.occurrence_id = y.occurrence_id
                 WHERE x.member_id = p_a AND y.member_id = p_b
                   AND x.status IN ('going','interested','checked_in','attended') AND y.status IN ('going','interested','checked_in','attended'))
      OR EXISTS (SELECT 1 FROM milavn_activity.occurrence o JOIN milavn_activity.participation p ON p.occurrence_id = o.id
                 WHERE ((o.creator_member_id = p_a AND p.member_id = p_b) OR (o.creator_member_id = p_b AND p.member_id = p_a))
                   AND p.status IN ('going','interested','checked_in','attended'))
    );
$$;

CREATE OR REPLACE FUNCTION milavn_connect.direct_conversation_id(p_a uuid, p_b uuid)
RETURNS uuid LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, pg_catalog AS $$
  SELECT c.id FROM milavn_connect.conversation c
  JOIN milavn_connect.conversation_member x ON x.conversation_id = c.id AND x.member_id = p_a AND x.left_at IS NULL
  JOIN milavn_connect.conversation_member y ON y.conversation_id = c.id AND y.member_id = p_b AND y.left_at IS NULL
  WHERE c.kind = 'direct' LIMIT 1;
$$;

-- Creation goes through one definer path so membership rows and trust checks cannot be bypassed.
CREATE OR REPLACE FUNCTION milavn_connect.create_conversation(p_kind text, p_title text, p_creator uuid, p_members uuid[])
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_connect, pg_catalog AS $$
DECLARE cid uuid; m uuid;
BEGIN
  IF p_kind NOT IN ('direct','group') THEN RAISE EXCEPTION 'bad kind'; END IF;
  FOREACH m IN ARRAY p_members LOOP
    IF m <> p_creator AND NOT milavn_connect.can_message(p_creator, m) THEN RAISE EXCEPTION 'not_allowed:%', m; END IF;
  END LOOP;
  IF p_kind = 'direct' THEN
    cid := milavn_connect.direct_conversation_id(p_creator, p_members[1]);
    IF cid IS NOT NULL THEN RETURN cid; END IF;
  END IF;
  INSERT INTO milavn_connect.conversation (kind, title, created_by) VALUES (p_kind, NULLIF(p_title, ''), p_creator) RETURNING id INTO cid;
  INSERT INTO milavn_connect.conversation_member (conversation_id, member_id) VALUES (cid, p_creator) ON CONFLICT DO NOTHING;
  FOREACH m IN ARRAY p_members LOOP
    INSERT INTO milavn_connect.conversation_member (conversation_id, member_id) VALUES (cid, m) ON CONFLICT DO NOTHING;
  END LOOP;
  RETURN cid;
END;
$$;

CREATE OR REPLACE FUNCTION milavn_connect.touch_conversation(p_conversation_id uuid)
RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_connect, pg_catalog AS $$
  UPDATE milavn_connect.conversation SET last_message_at = now() WHERE id = p_conversation_id;
$$;

CREATE OR REPLACE FUNCTION milavn_connect.heartbeat(p_member_id uuid, p_expression text, p_occurrence_id uuid)
RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_connect, pg_catalog AS $$
  INSERT INTO milavn_connect.presence (member_id, last_seen_at, expression, at_occurrence_id)
  VALUES (p_member_id, now(), p_expression, p_occurrence_id)
  ON CONFLICT (member_id) DO UPDATE SET last_seen_at = now(), expression = EXCLUDED.expression, at_occurrence_id = EXCLUDED.at_occurrence_id;
$$;

-- Presence of people you can already see in a conversation (or can message): active = seen in the last 2 minutes.
CREATE OR REPLACE FUNCTION milavn_connect.presence_of(p_member_ids uuid[])
RETURNS TABLE (member_id uuid, active boolean, expression text, at_occurrence_id uuid)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, pg_catalog AS $$
  SELECT p.member_id, p.last_seen_at > now() - interval '2 minutes', p.expression, p.at_occurrence_id
  FROM milavn_connect.presence p WHERE p.member_id = ANY(p_member_ids);
$$;

-- Unread count per conversation for the viewer.
CREATE OR REPLACE FUNCTION milavn_connect.unread_count(p_conversation_id uuid, p_member_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, pg_catalog AS $$
  SELECT count(*)::integer FROM milavn_connect.chat_message m
  JOIN milavn_connect.conversation_member cm ON cm.conversation_id = m.conversation_id AND cm.member_id = p_member_id
  WHERE m.conversation_id = p_conversation_id AND m.member_id <> p_member_id AND m.deleted_at IS NULL
    AND (cm.last_read_at IS NULL OR m.created_at > cm.last_read_at);
$$;

-- ---- RLS -----------------------------------------------------------------------

ALTER TABLE milavn_connect.conversation ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS conversation_members ON milavn_connect.conversation;
CREATE POLICY conversation_members ON milavn_connect.conversation
  FOR SELECT USING (milavn_connect.is_conversation_member(id, current_setting('milavn.member_id', true)::uuid));

ALTER TABLE milavn_connect.conversation_member ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS conversation_member_visible ON milavn_connect.conversation_member;
CREATE POLICY conversation_member_visible ON milavn_connect.conversation_member
  FOR SELECT USING (milavn_connect.is_conversation_member(conversation_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS conversation_member_self_update ON milavn_connect.conversation_member;
CREATE POLICY conversation_member_self_update ON milavn_connect.conversation_member
  FOR UPDATE USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_connect.chat_message ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS chat_message_members ON milavn_connect.chat_message;
CREATE POLICY chat_message_members ON milavn_connect.chat_message
  FOR SELECT USING (milavn_connect.is_conversation_member(conversation_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS chat_message_write ON milavn_connect.chat_message;
CREATE POLICY chat_message_write ON milavn_connect.chat_message
  FOR INSERT WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid
                         AND milavn_connect.is_conversation_member(conversation_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS chat_message_own_delete ON milavn_connect.chat_message;
CREATE POLICY chat_message_own_delete ON milavn_connect.chat_message
  FOR UPDATE USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_connect.message_reaction ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS message_reaction_members ON milavn_connect.message_reaction;
CREATE POLICY message_reaction_members ON milavn_connect.message_reaction
  FOR SELECT USING (EXISTS (SELECT 1 FROM milavn_connect.chat_message m WHERE m.id = message_id
                            AND milavn_connect.is_conversation_member(m.conversation_id, current_setting('milavn.member_id', true)::uuid)));
DROP POLICY IF EXISTS message_reaction_own ON milavn_connect.message_reaction;
CREATE POLICY message_reaction_own ON milavn_connect.message_reaction
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

ALTER TABLE milavn_connect.presence ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS presence_self ON milavn_connect.presence;
CREATE POLICY presence_self ON milavn_connect.presence
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

GRANT SELECT ON milavn_connect.conversation TO milavn_app;
GRANT SELECT, UPDATE ON milavn_connect.conversation_member TO milavn_app;
GRANT SELECT, INSERT, UPDATE ON milavn_connect.chat_message TO milavn_app;
GRANT SELECT, INSERT, DELETE ON milavn_connect.message_reaction TO milavn_app;
GRANT SELECT ON milavn_connect.presence TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.is_conversation_member(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.can_message(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.direct_conversation_id(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.create_conversation(text, text, uuid, uuid[]) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.touch_conversation(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.heartbeat(uuid, text, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.presence_of(uuid[]) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_connect.unread_count(uuid, uuid) TO milavn_app;
