-- =============================================================================
-- 037 — A circle member acts for their candidate on acceptance; late-joining
--       members are synced into family conversations (DEC-V1-022/024).
--
-- WHY (2026-09-17): the contract makes every context-scoped action generic
-- ("everything else works identically in every context"), so a parent may
-- accept a request FOR their candidate (`?for_candidate=`), which opens the
-- candidate conversation for the two candidates. `open_conversation()` (026,
-- 035) insisted the caller be the candidate themselves; it now also admits a
-- caller holding `family_info` on that candidate. The roster it writes is
-- still the two candidates — the member gains no seat in the private thread.
--
-- `sync_family_participants_for(candidate)` adds members who joined a circle
-- after a family conversation was opened. They cannot see the conversation
-- row until they are on the roster, so the sync must run with definer rights
-- before listing; the caller must be the candidate or hold `family_info`.
-- Idempotent: safe to re-run.
-- =============================================================================

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
    IF NOT (mangaly_authz.is_self(p_account_id) IS TRUE
            OR mangaly_authz.has_scope(p_account_id, 'family_info') IS TRUE) THEN
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

CREATE OR REPLACE FUNCTION mangaly_communication.sync_family_participants_for(p_candidate_account_id uuid)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_authz, pg_temp
AS $$
DECLARE
    v_conversation uuid;
    v_added integer := 0;
BEGIN
    IF NOT (mangaly_authz.is_self(p_candidate_account_id) IS TRUE
            OR mangaly_authz.has_scope(p_candidate_account_id, 'family_info') IS TRUE) THEN
        RETURN 0;
    END IF;
    FOR v_conversation IN
        SELECT cv.id
          FROM mangaly_communication.conversation cv
          JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
         WHERE cv.kind = 'family'
           AND cr.status = 'accepted'
           AND (cr.subject_account_id = p_candidate_account_id
                OR cr.target_profile_id = p_candidate_account_id)
    LOOP
        v_added := v_added + mangaly_communication.ensure_participants(v_conversation);
    END LOOP;
    RETURN v_added;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.sync_family_participants_for(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.sync_family_participants_for(uuid) TO mangaly_app;
