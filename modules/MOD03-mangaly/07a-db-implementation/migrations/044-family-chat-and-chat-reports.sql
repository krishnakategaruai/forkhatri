-- 044 — Family chat opened by parents, named people in it, and chat reports
-- that keep their evidence (DEC-V1-024, owner scenario DEC-V1-018).
--
-- 1. A parent or guardian may open the family conversation for a connection
--    of the candidate they help. Owner: "if parents want to chat there will
--    always be a chat way". Siblings and relatives take part once it is open
--    but do not start it: the same people who may answer a request
--    (DEC-V1-020) may open the families' conversation.
-- 2. conversation_people also says each person's exact relation and whose
--    side they are on, so a message reads "Rekha, Varun's mother".
-- 3. A report made from inside a conversation stores the conversation as it
--    stood at that moment. The candidates' chat is a session that is deleted
--    when it ends, so evidence has to be taken at report time or never.

-- 1 ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_communication.open_family_conversation(
    p_connection_id uuid,
    p_account_id uuid,
    p_system_key text
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
DECLARE
    v_conversation_id uuid;
    v_subject uuid;
    v_target uuid;
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
BEGIN
    IF v_me IS NULL OR p_account_id <> v_me THEN
        RETURN NULL;
    END IF;

    SELECT c.subject_account_id, c.target_profile_id INTO v_subject, v_target
      FROM mangaly_connection.connection_request c
     WHERE c.id = p_connection_id AND c.status = 'accepted';
    IF v_subject IS NULL THEN
        RETURN NULL;
    END IF;

    IF NOT (v_me IN (v_subject, v_target) OR EXISTS (
        SELECT 1 FROM mangaly_home_circle.membership m
         WHERE m.member_account_id = v_me
           AND m.candidate_profile_id IN (v_subject, v_target)
           AND m.status = 'active'
           AND m.relationship_type::text IN ('parent', 'guardian'))) THEN
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
           AND m.kind = 'system' AND m.content = p_system_key
    ) THEN
        INSERT INTO mangaly_communication.message
            (id, conversation_id, sender_account_id, content, kind)
        VALUES (gen_random_uuid(), v_conversation_id, NULL, p_system_key, 'system');
    END IF;

    -- Both candidates and everyone active in both circles are on the roster.
    INSERT INTO mangaly_communication.conversation_participant (conversation_id, account_id)
    SELECT v_conversation_id, w.account_id
      FROM (SELECT v_subject AS account_id UNION SELECT v_target
            UNION SELECT m.member_account_id FROM mangaly_home_circle.membership m
                   WHERE m.candidate_profile_id IN (v_subject, v_target) AND m.status = 'active') w
    ON CONFLICT (conversation_id, account_id) DO NOTHING;
    RETURN v_conversation_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.open_family_conversation(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.open_family_conversation(uuid, uuid, text) TO mangaly_app;

-- 2 ---------------------------------------------------------------------
DROP FUNCTION IF EXISTS mangaly_communication.conversation_people(uuid);
CREATE FUNCTION mangaly_communication.conversation_people(p_conversation_id uuid)
RETURNS TABLE (
    account_id uuid,
    display_name text,
    role text,
    photo_ref text,
    last_read_at timestamptz,
    relation text,
    side_account_id uuid
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
    SELECT cp.account_id,
           COALESCE(p.name, a.display_name),
           CASE WHEN cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN 'candidate'
                ELSE COALESCE(mm.relationship_type::text, 'relative') END,
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1),
           cp.last_read_at,
           CASE WHEN cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN NULL
                ELSE mm.relation END,
           CASE WHEN cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN cp.account_id
                ELSE mm.candidate_profile_id END
      FROM mangaly_communication.conversation_participant cp
      JOIN mangaly_communication.conversation cv ON cv.id = cp.conversation_id
      JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
      LEFT JOIN mangaly_profile.profile p ON p.account_id = cp.account_id
      LEFT JOIN mangaly_identity.account a ON a.id = cp.account_id
      LEFT JOIN LATERAL (
            SELECT m.relationship_type, m.relation, m.candidate_profile_id
              FROM mangaly_home_circle.membership m
             WHERE m.member_account_id = cp.account_id
               AND m.candidate_profile_id IN (cr.subject_account_id, cr.target_profile_id)
               AND m.status = 'active'
             ORDER BY m.joined_at LIMIT 1) mm ON true
     WHERE cp.conversation_id = p_conversation_id
       AND mangaly_communication.is_participant(p_conversation_id)
     ORDER BY cp.joined_at;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.conversation_people(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.conversation_people(uuid) TO mangaly_app;

-- 3 ---------------------------------------------------------------------
ALTER TABLE mangaly_safety.report ADD COLUMN IF NOT EXISTS reported_conversation_id uuid;
ALTER TABLE mangaly_safety.report ADD COLUMN IF NOT EXISTS evidence jsonb;
COMMENT ON COLUMN mangaly_safety.report.evidence IS
  '[DEC-V1-024] The conversation as it stood when reported: sender, text, time. Taken at report time because the candidates'' chat is deleted when its session ends. Read only by moderation.';

CREATE OR REPLACE FUNCTION mangaly_safety.report_conversation(
    p_conversation_id uuid,
    p_reported_account_id uuid,
    p_category text,
    p_description text
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_safety, mangaly_communication, mangaly_authz, pg_temp
AS $$
DECLARE
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_id uuid := gen_random_uuid();
BEGIN
    IF v_me IS NULL OR NOT EXISTS (
        SELECT 1 FROM mangaly_communication.conversation_participant cp
         WHERE cp.conversation_id = p_conversation_id AND cp.account_id = v_me) THEN
        RETURN NULL;
    END IF;
    INSERT INTO mangaly_safety.report
        (id, reporter_account_id, reported_profile_id, reported_conversation_id,
         category, description, source, evidence)
    VALUES (v_id, v_me, p_reported_account_id, p_conversation_id, p_category,
            NULLIF(left(btrim(COALESCE(p_description, '')), 2000), ''), 'user_reported',
            (SELECT COALESCE(jsonb_agg(jsonb_build_object(
                        'sender_account_id', m.sender_account_id,
                        'kind', m.kind,
                        'content', m.content,
                        'sent_at', m.sent_at) ORDER BY m.sent_at), '[]'::jsonb)
               FROM (SELECT * FROM mangaly_communication.message
                      WHERE conversation_id = p_conversation_id
                      ORDER BY sent_at DESC LIMIT 200) m));
    RETURN v_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_safety.report_conversation(uuid, uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_safety.report_conversation(uuid, uuid, text, text) TO mangaly_app;

-- 4 ---------------------------------------------------------------------
-- A family member reaches the families' conversation through the roster, not
-- through the connection row (which RLS keeps from them). So the roster check
-- itself requires the connection to still be accepted: when a connection ends,
-- everyone loses the thread at once.
CREATE OR REPLACE FUNCTION mangaly_communication.is_participant(p_conversation_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_communication.conversation_participant cp
          JOIN mangaly_communication.conversation cv ON cv.id = cp.conversation_id
          JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
         WHERE cp.conversation_id = p_conversation_id
           AND cr.status = 'accepted'
           AND mangaly_authz.is_self(cp.account_id)
    );
$$;
REVOKE ALL ON FUNCTION mangaly_communication.is_participant(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.is_participant(uuid) TO mangaly_app;
