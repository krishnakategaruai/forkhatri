-- 046 — One-to-one chat between people (DEC-V1-026)
--
-- Owner, 2026-09-22: "we only offer incognito mode chat to candidate, and
-- general chat for individual account like how chat present in Instagram /
-- FB; now that we have option of family chat keep that as additional."
--
-- So Mangaly has three kinds of conversation:
--   candidate  the two connected candidates' incognito session (unchanged);
--   direct     NEW: an ordinary, kept, one-to-one chat between two people,
--              like Instagram or Facebook messages;
--   family     the optional group of both candidates and both Home Circles.
--
-- Who may message whom directly. Mangaly is not an open network, so a direct
-- chat needs a real link between the two people:
--   * the same family: a candidate and the members of their Home Circle, or
--     two members of the same circle (a mother and a brother);
--   * the two families of an accepted connection: anyone on one side with
--     anyone on the other (Divya's father with Varun's mother).
-- Never: the two connected candidates themselves (theirs is the incognito
-- session), yourself, or anyone blocked either way.
--
-- A direct conversation has no connection: `connection_id` becomes nullable,
-- and `direct_key` (the two account ids in order) keeps one thread per pair.

ALTER TABLE mangaly_communication.conversation ALTER COLUMN connection_id DROP NOT NULL;
ALTER TABLE mangaly_communication.conversation ADD COLUMN IF NOT EXISTS direct_key text;
DO $$ BEGIN
  ALTER TABLE mangaly_communication.conversation
    ADD CONSTRAINT conversation_direct_key_key UNIQUE (direct_key);
EXCEPTION WHEN duplicate_object OR duplicate_table THEN NULL;
END $$;
ALTER TABLE mangaly_communication.conversation DROP CONSTRAINT IF EXISTS conversation_kind_check;
ALTER TABLE mangaly_communication.conversation
  ADD CONSTRAINT conversation_kind_check CHECK (kind IN ('candidate', 'family', 'direct'));
ALTER TABLE mangaly_communication.conversation DROP CONSTRAINT IF EXISTS conversation_direct_shape;
ALTER TABLE mangaly_communication.conversation
  ADD CONSTRAINT conversation_direct_shape CHECK (
    (kind = 'direct' AND connection_id IS NULL AND direct_key IS NOT NULL)
    OR (kind <> 'direct' AND connection_id IS NOT NULL AND direct_key IS NULL));

-- The candidates whose "side" an account is on: themself, and every candidate
-- whose Home Circle they are an active member of.
CREATE OR REPLACE FUNCTION mangaly_communication.sides_of(p_account uuid)
RETURNS TABLE (candidate_account_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, pg_temp
AS $$
    SELECT p_account
    UNION
    SELECT m.candidate_profile_id FROM mangaly_home_circle.membership m
     WHERE m.member_account_id = p_account AND m.status = 'active';
$$;
REVOKE ALL ON FUNCTION mangaly_communication.sides_of(uuid) FROM PUBLIC;

-- May the signed-in account message p_other directly?
CREATE OR REPLACE FUNCTION mangaly_communication.can_direct(p_other uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_safety, pg_temp
AS $$
    WITH me AS (SELECT NULLIF(current_setting('mangaly.account_id', true), '')::uuid AS id)
    SELECT COALESCE((
      SELECT me.id IS NOT NULL
         AND p_other IS NOT NULL
         AND p_other <> me.id
         AND NOT mangaly_safety.is_blocked_between(me.id, p_other)
         -- the two connected candidates talk only in their incognito session
         AND NOT EXISTS (
               SELECT 1 FROM mangaly_connection.connection_request cr
                WHERE cr.status = 'accepted'
                  AND ((cr.subject_account_id = me.id AND cr.target_profile_id = p_other)
                    OR (cr.subject_account_id = p_other AND cr.target_profile_id = me.id)))
         AND (
               -- the same family
               EXISTS (SELECT 1 FROM mangaly_communication.sides_of(me.id) a
                         JOIN mangaly_communication.sides_of(p_other) b
                           ON a.candidate_account_id = b.candidate_account_id)
               -- the two families of an accepted connection
            OR EXISTS (
               SELECT 1 FROM mangaly_connection.connection_request cr
                WHERE cr.status = 'accepted'
                  AND ((cr.subject_account_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(me.id))
                        AND cr.target_profile_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(p_other)))
                    OR (cr.target_profile_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(me.id))
                        AND cr.subject_account_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(p_other)))))
         )
      FROM me), false);
$$;
REVOKE ALL ON FUNCTION mangaly_communication.can_direct(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.can_direct(uuid) TO mangaly_app;

-- Everyone the signed-in account may message directly, with how they are
-- linked, for the "New message" list: `side_account_id` is the candidate whose
-- family they belong to, and `mine` says whether that is the reader's own
-- family or the other family of a connection.
CREATE OR REPLACE FUNCTION mangaly_communication.direct_contacts()
RETURNS TABLE (
    account_id uuid,
    display_name text,
    photo_ref text,
    role text,
    relation text,
    side_account_id uuid,
    side_name text,
    mine boolean
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_home_circle, mangaly_profile, mangaly_identity, pg_temp
AS $$
    WITH me AS (SELECT NULLIF(current_setting('mangaly.account_id', true), '')::uuid AS id),
    my_sides AS (SELECT s.candidate_account_id FROM me, mangaly_communication.sides_of(me.id) s),
    their_sides AS (
        SELECT CASE WHEN cr.subject_account_id IN (SELECT candidate_account_id FROM my_sides)
                    THEN cr.target_profile_id ELSE cr.subject_account_id END AS candidate_account_id
          FROM mangaly_connection.connection_request cr
         WHERE cr.status = 'accepted'
           AND (cr.subject_account_id IN (SELECT candidate_account_id FROM my_sides)
             OR cr.target_profile_id IN (SELECT candidate_account_id FROM my_sides))),
    sides AS (
        SELECT candidate_account_id, true AS mine FROM my_sides
        UNION
        SELECT candidate_account_id, false FROM their_sides
         WHERE candidate_account_id NOT IN (SELECT candidate_account_id FROM my_sides)),
    people AS (
        -- the candidate of each side (only if they have a profile: a parent
        -- with no profile is not "a side" of their own)
        SELECT s.candidate_account_id AS account_id, 'candidate'::text AS role, NULL::text AS relation,
               s.candidate_account_id AS side_account_id, s.mine
          FROM sides s
         WHERE EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.account_id = s.candidate_account_id)
        UNION ALL
        SELECT m.member_account_id, m.relationship_type::text, m.relation, m.candidate_profile_id, s.mine
          FROM sides s
          JOIN mangaly_home_circle.membership m
            ON m.candidate_profile_id = s.candidate_account_id AND m.status = 'active')
    SELECT DISTINCT ON (pp.account_id)
           pp.account_id,
           COALESCE(pr.name, a.display_name),
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = pr.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1),
           pp.role, pp.relation, pp.side_account_id,
           COALESCE(sp.name, sa.display_name),
           pp.mine
      FROM people pp CROSS JOIN me
      LEFT JOIN mangaly_profile.profile pr ON pr.account_id = pp.account_id
      LEFT JOIN mangaly_identity.account a ON a.id = pp.account_id
      LEFT JOIN mangaly_profile.profile sp ON sp.account_id = pp.side_account_id
      LEFT JOIN mangaly_identity.account sa ON sa.id = pp.side_account_id
     WHERE pp.account_id <> me.id
       AND mangaly_communication.can_direct(pp.account_id)
     ORDER BY pp.account_id, pp.mine DESC;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.direct_contacts() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.direct_contacts() TO mangaly_app;

-- Open (or find) the one direct thread between the signed-in account and p_other.
CREATE OR REPLACE FUNCTION mangaly_communication.open_direct(p_other uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_communication, pg_temp
AS $$
DECLARE
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_key text;
    v_id uuid;
BEGIN
    IF NOT mangaly_communication.can_direct(p_other) THEN
        RETURN NULL;
    END IF;
    v_key := least(v_me::text, p_other::text) || ':' || greatest(v_me::text, p_other::text);
    INSERT INTO mangaly_communication.conversation (id, connection_id, kind, direct_key)
    VALUES (gen_random_uuid(), NULL, 'direct', v_key)
    ON CONFLICT (direct_key) DO NOTHING;
    SELECT id INTO v_id FROM mangaly_communication.conversation WHERE direct_key = v_key;
    INSERT INTO mangaly_communication.conversation_participant (conversation_id, account_id)
    VALUES (v_id, v_me), (v_id, p_other)
    ON CONFLICT (conversation_id, account_id) DO NOTHING;
    RETURN v_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.open_direct(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.open_direct(uuid) TO mangaly_app;

-- A participant check that also covers a direct thread, which has no
-- connection. Connection threads still require the connection to be accepted.
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
          LEFT JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
         WHERE cp.conversation_id = p_conversation_id
           AND (cv.kind = 'direct' OR cr.status = 'accepted')
           AND mangaly_authz.is_self(cp.account_id)
    );
$$;
REVOKE ALL ON FUNCTION mangaly_communication.is_participant(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.is_participant(uuid) TO mangaly_app;

-- Row visibility for direct threads and their messages: participants only.
DROP POLICY IF EXISTS conversation_participants ON mangaly_communication.conversation;
CREATE POLICY conversation_participants ON mangaly_communication.conversation
  USING (
    EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
             WHERE c.id = conversation.connection_id
               AND (mangaly_authz.is_self(c.subject_account_id)
                    OR mangaly_authz.is_self(c.target_profile_id)))
    OR (conversation.kind IN ('family', 'direct') AND mangaly_communication.is_participant(conversation.id))
  );

DROP POLICY IF EXISTS message_select_direct_participant ON mangaly_communication.message;
CREATE POLICY message_select_direct_participant ON mangaly_communication.message
  FOR SELECT
  USING (EXISTS (SELECT 1 FROM mangaly_communication.conversation cv
                  WHERE cv.id = message.conversation_id
                    AND cv.kind = 'direct'
                    AND mangaly_communication.is_participant(cv.id)));

-- Names for the people in any thread, now including direct threads (no
-- connection): their exact relation and whose family they are in, with that
-- candidate's name, so the header can read "Harish · father of Divya".
DROP FUNCTION IF EXISTS mangaly_communication.conversation_people(uuid);
CREATE FUNCTION mangaly_communication.conversation_people(p_conversation_id uuid)
RETURNS TABLE (
    account_id uuid,
    display_name text,
    role text,
    photo_ref text,
    last_read_at timestamptz,
    relation text,
    side_account_id uuid,
    side_name text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
    SELECT cp.account_id,
           COALESCE(p.name, a.display_name),
           CASE WHEN cr.id IS NOT NULL AND cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN 'candidate'
                WHEN mm.relationship_type IS NOT NULL THEN mm.relationship_type::text
                WHEN p.id IS NOT NULL THEN 'candidate'
                ELSE 'relative' END,
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1),
           cp.last_read_at,
           CASE WHEN cr.id IS NOT NULL AND cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN NULL
                ELSE mm.relation END,
           CASE WHEN cr.id IS NOT NULL AND cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN cp.account_id
                WHEN mm.candidate_profile_id IS NOT NULL THEN mm.candidate_profile_id
                ELSE cp.account_id END,
           COALESCE(sp.name, sa.display_name)
      FROM mangaly_communication.conversation_participant cp
      JOIN mangaly_communication.conversation cv ON cv.id = cp.conversation_id
      LEFT JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
      LEFT JOIN mangaly_profile.profile p ON p.account_id = cp.account_id
      LEFT JOIN mangaly_identity.account a ON a.id = cp.account_id
      LEFT JOIN LATERAL (
            SELECT m.relationship_type, m.relation, m.candidate_profile_id
              FROM mangaly_home_circle.membership m
             WHERE m.member_account_id = cp.account_id
               AND m.status = 'active'
               AND (cr.id IS NULL OR m.candidate_profile_id IN (cr.subject_account_id, cr.target_profile_id))
             ORDER BY m.joined_at LIMIT 1) mm ON true
      LEFT JOIN mangaly_profile.profile sp
        ON sp.account_id = COALESCE(mm.candidate_profile_id, cp.account_id)
      LEFT JOIN mangaly_identity.account sa
        ON sa.id = COALESCE(mm.candidate_profile_id, cp.account_id)
     WHERE cp.conversation_id = p_conversation_id
       AND mangaly_communication.is_participant(p_conversation_id)
     ORDER BY cp.joined_at;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.conversation_people(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.conversation_people(uuid) TO mangaly_app;

-- The conversation list reads connections through a narrow definer read, so a
-- parent on a families' conversation sees it listed (RLS keeps connection rows
-- from them).
CREATE OR REPLACE FUNCTION mangaly_communication.thread_connections()
RETURNS TABLE (id uuid, subject_account_id uuid, target_profile_id uuid, status text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_authz, pg_temp
AS $$
    SELECT cr.id, cr.subject_account_id, cr.target_profile_id, cr.status::text
      FROM mangaly_connection.connection_request cr
     WHERE cr.status = 'accepted'
       AND (mangaly_authz.is_self(cr.subject_account_id)
            OR mangaly_authz.is_self(cr.target_profile_id)
            OR EXISTS (SELECT 1 FROM mangaly_communication.conversation cv
                         JOIN mangaly_communication.conversation_participant cp ON cp.conversation_id = cv.id
                        WHERE cv.connection_id = cr.id AND cv.kind = 'family'
                          AND mangaly_authz.is_self(cp.account_id)));
$$;
REVOKE ALL ON FUNCTION mangaly_communication.thread_connections() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.thread_connections() TO mangaly_app;

-- A report from a direct thread keeps its evidence the same way (migration
-- 044's report_conversation already checks the reporter is on the roster).
