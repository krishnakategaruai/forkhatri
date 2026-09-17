-- =============================================================================
-- 026 — An accepted connection opens the private conversation itself, with a
--       system line both people can see (FR043/FR044/FR049).
--
-- WHY (2026-09-17):
--   * Product owner: "candidate should get private message once any request is
--     successful". Until now nothing at all reached either party on
--     acceptance: the conversation row was created lazily on the first send,
--     so the Messages tab stayed empty and the only way to learn a request had
--     been accepted was to re-read a status string on another screen.
--   * The conversation is now opened at acceptance and carries one system
--     line. A system line has no sender (`sender_account_id` is NULL, `kind`
--     is 'system'), because it is the platform speaking, not either person —
--     rendering it as if one of them typed it would be a lie about who said
--     what. `content` holds a stable key, not prose, so the line is shown in
--     the reader's own language (en/hi/te) rather than frozen in whichever
--     language the accepting person happened to be using.
--   * Opening the conversation must work from the accepting party's own
--     session, which cannot insert a NULL-sender row under
--     `message`'s sender-only INSERT policy (migration 011). Hence one
--     SECURITY DEFINER function held to migration 010's rules: the caller must
--     be a party to the connection, the connection must already be accepted,
--     every value is re-derived from rows, and re-running it adds nothing.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_communication.message
  ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'member';

DO $$ BEGIN
  ALTER TABLE mangaly_communication.message
    ADD CONSTRAINT message_kind_check CHECK (kind IN ('member', 'system'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- A system line has no sender; a member message still must have one.
ALTER TABLE mangaly_communication.message ALTER COLUMN sender_account_id DROP NOT NULL;

DO $$ BEGIN
  ALTER TABLE mangaly_communication.message
    ADD CONSTRAINT message_sender_matches_kind
    CHECK ((kind = 'system' AND sender_account_id IS NULL)
           OR (kind = 'member' AND sender_account_id IS NOT NULL));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

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

    INSERT INTO mangaly_communication.conversation (id, connection_id)
    VALUES (gen_random_uuid(), p_connection_id)
    ON CONFLICT (connection_id) DO NOTHING;

    SELECT id INTO v_conversation_id
      FROM mangaly_communication.conversation
     WHERE connection_id = p_connection_id;

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

    RETURN v_conversation_id;
END;
$$;

REVOKE ALL ON FUNCTION mangaly_communication.open_conversation(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.open_conversation(uuid, uuid, text) TO mangaly_app;
