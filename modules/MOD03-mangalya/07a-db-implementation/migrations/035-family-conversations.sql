-- =============================================================================
-- 035 — Two conversation kinds on a connection: candidate and family
--       (DEC-V1-024, rework contract §2).
--
-- WHY (2026-09-17): "Messaging is one of only two things that vary by role."
--   * `candidate` — the two candidates only, opened on acceptance (unchanged).
--   * `family`    — both candidates plus every active member of both circles,
--                   opened when EITHER candidate taps "Involve my family" on an
--                   accepted connection. Family members are only ever in family
--                   conversations.
-- `conversation.kind` distinguishes them (one of each per connection), and
-- `conversation_participant` is the roster with per-person `last_read_at`,
-- from which the unread count is computed. Participant rows exist for both
-- kinds so unread works uniformly.
-- Every roster write is a SECURITY DEFINER function held to migration 010's
-- rules: the caller must be a party, everything is re-derived from rows, and
-- re-running adds nothing. RLS on messages/conversations is widened by exactly
-- one clause: a family conversation's participant.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_communication.conversation
  ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'candidate';

DO $$ BEGIN
  ALTER TABLE mangaly_communication.conversation
    ADD CONSTRAINT conversation_kind_check CHECK (kind IN ('candidate', 'family'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE mangaly_communication.conversation
  DROP CONSTRAINT IF EXISTS conversation_connection_id_key;
DO $$ BEGIN
  ALTER TABLE mangaly_communication.conversation
    ADD CONSTRAINT conversation_connection_kind_key UNIQUE (connection_id, kind);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS mangaly_communication.conversation_participant (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES mangaly_communication.conversation(id) ON DELETE CASCADE,
  account_id      uuid NOT NULL,
  joined_at       timestamptz NOT NULL DEFAULT now(),
  last_read_at    timestamptz,
  UNIQUE (conversation_id, account_id)
);
CREATE INDEX IF NOT EXISTS idx_conversation_participant_account
  ON mangaly_communication.conversation_participant (account_id);

-- Is the current session a participant of this conversation? Definer rights,
-- so the policy on the participant table can use it without recursing.
CREATE OR REPLACE FUNCTION mangaly_communication.is_participant(p_conversation_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_communication.conversation_participant cp
         WHERE cp.conversation_id = p_conversation_id
           AND mangaly_authz.is_self(cp.account_id)
    );
$$;
REVOKE ALL ON FUNCTION mangaly_communication.is_participant(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.is_participant(uuid) TO mangaly_app;

ALTER TABLE mangaly_communication.conversation_participant ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS participant_roster_visible_to_participants ON mangaly_communication.conversation_participant;
CREATE POLICY participant_roster_visible_to_participants ON mangaly_communication.conversation_participant
  FOR SELECT USING (mangaly_communication.is_participant(conversation_id));
DROP POLICY IF EXISTS participant_updates_own_row ON mangaly_communication.conversation_participant;
CREATE POLICY participant_updates_own_row ON mangaly_communication.conversation_participant
  FOR UPDATE USING (mangaly_authz.is_self(account_id)) WITH CHECK (mangaly_authz.is_self(account_id));
GRANT SELECT, UPDATE ON mangaly_communication.conversation_participant TO mangaly_app;

-- Conversation visibility: the two candidates (any kind), or a participant of
-- a family conversation.
DROP POLICY IF EXISTS conversation_participants ON mangaly_communication.conversation;
CREATE POLICY conversation_participants ON mangaly_communication.conversation
  USING (
    EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
             WHERE c.id = conversation.connection_id
               AND (mangaly_authz.is_self(c.subject_account_id)
                    OR mangaly_authz.is_self(c.target_profile_id)))
    OR (conversation.kind = 'family' AND mangaly_communication.is_participant(conversation.id))
  );

DROP POLICY IF EXISTS message_select_participant_or_safety_case ON mangaly_communication.message;
CREATE POLICY message_select_participant_or_safety_case ON mangaly_communication.message
    FOR SELECT
    USING (
        mangaly_authz.is_self(sender_account_id)
        OR EXISTS (
            SELECT 1
            FROM mangaly_communication.conversation cv
            JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
            WHERE cv.id = message.conversation_id
              AND (mangaly_authz.is_self(cr.subject_account_id)
                   OR mangaly_authz.is_self(cr.target_profile_id))
        )
        OR EXISTS (
            SELECT 1 FROM mangaly_communication.conversation cv
             WHERE cv.id = message.conversation_id
               AND cv.kind = 'family'
               AND mangaly_communication.is_participant(cv.id)
        )
        OR (
            EXISTS (SELECT 1 FROM mangaly_communication.conversation cv WHERE cv.id = message.conversation_id)
            AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation'
        )
    );

DROP POLICY IF EXISTS message_delete_participant_or_safety_case ON mangaly_communication.message;
CREATE POLICY message_delete_participant_or_safety_case ON mangaly_communication.message
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1
        FROM mangaly_communication.conversation cv
        JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
       WHERE cv.id = message.conversation_id
         AND (mangaly_authz.is_self(cr.subject_account_id)
              OR mangaly_authz.is_self(cr.target_profile_id))
    )
    OR EXISTS (
      SELECT 1 FROM mangaly_communication.conversation cv
       WHERE cv.id = message.conversation_id
         AND cv.kind = 'family'
         AND mangaly_communication.is_participant(cv.id)
    )
    OR (
      EXISTS (SELECT 1 FROM mangaly_communication.conversation cv WHERE cv.id = message.conversation_id)
      AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation'
    )
  );

-- Roster maintenance. For a candidate conversation: the two candidates. For a
-- family conversation: both candidates plus every ACTIVE member of both
-- circles at call time (members who join a circle later are added the next
-- time anyone lists). Never removes anyone: a member who leaves a circle keeps
-- the messages they were party to, as in any group chat.
CREATE OR REPLACE FUNCTION mangaly_communication.ensure_participants(p_conversation_id uuid)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
DECLARE
    v_kind text;
    v_subject uuid;
    v_target uuid;
    v_added integer := 0;
BEGIN
    SELECT cv.kind, cr.subject_account_id, cr.target_profile_id
      INTO v_kind, v_subject, v_target
      FROM mangaly_communication.conversation cv
      JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
     WHERE cv.id = p_conversation_id
       AND cr.status = 'accepted';
    IF v_kind IS NULL THEN
        RETURN 0;
    END IF;

    -- The caller must already be a party: a candidate, or (family) a circle member.
    IF NOT (mangaly_authz.is_self(v_subject) OR mangaly_authz.is_self(v_target)
            OR (v_kind = 'family' AND (mangaly_authz.has_scope(v_subject, 'family_info')
                                       OR mangaly_authz.has_scope(v_target, 'family_info')))
            OR mangaly_communication.is_participant(p_conversation_id)) THEN
        RETURN 0;
    END IF;

    WITH wanted AS (
        SELECT v_subject AS account_id
        UNION SELECT v_target
        UNION
        SELECT m.member_account_id FROM mangaly_home_circle.membership m
         WHERE v_kind = 'family'
           AND m.candidate_profile_id IN (v_subject, v_target)
           AND m.status = 'active'
    ),
    ins AS (
        INSERT INTO mangaly_communication.conversation_participant (conversation_id, account_id)
        SELECT p_conversation_id, w.account_id FROM wanted w
        ON CONFLICT (conversation_id, account_id) DO NOTHING
        RETURNING 1
    )
    SELECT count(*) INTO v_added FROM ins;
    RETURN v_added;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.ensure_participants(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.ensure_participants(uuid) TO mangaly_app;

-- Acceptance opens the candidate conversation (migration 026), now keyed by kind.
CREATE OR REPLACE FUNCTION mangaly_communication.open_conversation(
    p_connection_id uuid,
    p_account_id uuid,
    p_system_key text
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_authz, pg_temp
AS $$
DECLARE
    v_conversation_id uuid;
BEGIN
    IF mangaly_authz.is_self(p_account_id) IS NOT TRUE THEN
        RETURN NULL;
    END IF;

    PERFORM 1
       FROM mangaly_connection.connection_request c
      WHERE c.id = p_connection_id
        AND c.status = 'accepted'
        AND (c.subject_account_id = p_account_id OR c.target_profile_id = p_account_id);
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    INSERT INTO mangaly_communication.conversation (id, connection_id, kind)
    VALUES (gen_random_uuid(), p_connection_id, 'candidate')
    ON CONFLICT (connection_id, kind) DO NOTHING;

    SELECT id INTO v_conversation_id
      FROM mangaly_communication.conversation
     WHERE connection_id = p_connection_id AND kind = 'candidate';

    IF p_system_key IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM mangaly_communication.message m
         WHERE m.conversation_id = v_conversation_id
           AND m.kind = 'system'
           AND m.content = p_system_key
    ) THEN
        INSERT INTO mangaly_communication.message
            (id, conversation_id, sender_account_id, content, kind)
        VALUES (gen_random_uuid(), v_conversation_id, NULL, p_system_key, 'system');
    END IF;

    PERFORM mangaly_communication.ensure_participants(v_conversation_id);
    RETURN v_conversation_id;
END;
$$;

-- Either candidate opens the family conversation ("Involve my family").
CREATE OR REPLACE FUNCTION mangaly_communication.open_family_conversation(
    p_connection_id uuid,
    p_account_id uuid,
    p_system_key text
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_authz, pg_temp
AS $$
DECLARE
    v_conversation_id uuid;
BEGIN
    IF mangaly_authz.is_self(p_account_id) IS NOT TRUE THEN
        RETURN NULL;
    END IF;

    PERFORM 1
       FROM mangaly_connection.connection_request c
      WHERE c.id = p_connection_id
        AND c.status = 'accepted'
        AND (c.subject_account_id = p_account_id OR c.target_profile_id = p_account_id);
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    INSERT INTO mangaly_communication.conversation (id, connection_id, kind)
    VALUES (gen_random_uuid(), p_connection_id, 'family')
    ON CONFLICT (connection_id, kind) DO NOTHING;

    SELECT id INTO v_conversation_id
      FROM mangaly_communication.conversation
     WHERE connection_id = p_connection_id AND kind = 'family';

    IF p_system_key IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM mangaly_communication.message m
         WHERE m.conversation_id = v_conversation_id
           AND m.kind = 'system'
           AND m.content = p_system_key
    ) THEN
        INSERT INTO mangaly_communication.message
            (id, conversation_id, sender_account_id, content, kind)
        VALUES (gen_random_uuid(), v_conversation_id, NULL, p_system_key, 'system');
    END IF;

    PERFORM mangaly_communication.ensure_participants(v_conversation_id);
    RETURN v_conversation_id;
END;
$$;

REVOKE ALL ON FUNCTION mangaly_communication.open_family_conversation(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.open_family_conversation(uuid, uuid, text) TO mangaly_app;

-- The other side of a conversation, by name, for the list: a family member
-- has no `candidate_info` on the other candidate, so the name of the person
-- their candidate is connected to is read here, narrowly, only for a
-- conversation the caller is a participant of.
CREATE OR REPLACE FUNCTION mangaly_communication.conversation_people(p_conversation_id uuid)
RETURNS TABLE (
    account_id uuid,
    display_name text,
    role text,
    photo_ref text,
    last_read_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
    SELECT cp.account_id,
           COALESCE(p.name, a.display_name),
           CASE WHEN cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN 'candidate'
                ELSE COALESCE((SELECT m.relationship_type::text FROM mangaly_home_circle.membership m
                                WHERE m.member_account_id = cp.account_id
                                  AND m.candidate_profile_id IN (cr.subject_account_id, cr.target_profile_id)
                                  AND m.status = 'active'
                                ORDER BY m.joined_at LIMIT 1), 'relative') END,
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1),
           cp.last_read_at
      FROM mangaly_communication.conversation_participant cp
      JOIN mangaly_communication.conversation cv ON cv.id = cp.conversation_id
      JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
      LEFT JOIN mangaly_profile.profile p ON p.account_id = cp.account_id
      LEFT JOIN mangaly_identity.account a ON a.id = cp.account_id
     WHERE cp.conversation_id = p_conversation_id
       AND mangaly_communication.is_participant(p_conversation_id)
     ORDER BY cp.joined_at;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.conversation_people(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.conversation_people(uuid) TO mangaly_app;

-- A family member serving a conversation counterpart's main photo: allowed for
-- the main photo of either candidate of a conversation the caller is in.
CREATE OR REPLACE FUNCTION mangaly_communication.is_conversation_photo(p_storage_ref text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM mangaly_profile.profile_media pm
          JOIN mangaly_profile.profile p ON p.id = pm.profile_id
          JOIN mangaly_connection.connection_request cr
            ON p.account_id IN (cr.subject_account_id, cr.target_profile_id)
          JOIN mangaly_communication.conversation cv ON cv.connection_id = cr.id
          JOIN mangaly_communication.conversation_participant cp ON cp.conversation_id = cv.id
         WHERE pm.storage_ref = p_storage_ref
           AND pm.is_primary
           AND pm.media_type::text = 'photo'
           AND mangaly_authz.is_self(cp.account_id)
    );
$$;
REVOKE ALL ON FUNCTION mangaly_communication.is_conversation_photo(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.is_conversation_photo(text) TO mangaly_app;

-- Roster rows for conversations opened before this migration.
INSERT INTO mangaly_communication.conversation_participant (conversation_id, account_id)
SELECT cv.id, x.account_id
  FROM mangaly_communication.conversation cv
  JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
  CROSS JOIN LATERAL (VALUES (cr.subject_account_id), (cr.target_profile_id)) AS x(account_id)
ON CONFLICT (conversation_id, account_id) DO NOTHING;
