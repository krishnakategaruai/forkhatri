-- =============================================================================
-- 036 — A circle sees its candidate's requests; a request can be withdrawn;
--       the recipient learns who pressed send (DEC-V1-022, contract §2).
--
-- WHY (2026-09-17):
--   * "Family members MAY send a connection request on behalf of their
--     candidate ... the recipient sees 'Sent by Ananya's mother'." Migration
--     023 already records `acting_account_id` and `subject_account_id`. Two
--     things were missing: every member of the candidate's circle must SEE
--     the candidate's requests (incoming and sent, `?for_candidate=`), and
--     the recipient must learn the sender's relation to the candidate, which
--     lives in a membership row the recipient cannot read.
--   * `withdrawn` joins the status vocabulary: a pending request can be taken
--     back by the candidate or by any active member of their circle.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TYPE mangaly_connection.connection_status ADD VALUE IF NOT EXISTS 'withdrawn';

DROP POLICY IF EXISTS connection_participants ON mangaly_connection.connection_request;
CREATE POLICY connection_participants ON mangaly_connection.connection_request
  USING (mangaly_authz.is_self(acting_account_id)
         OR mangaly_authz.is_self(target_profile_id)
         OR mangaly_authz.is_self(subject_account_id)
         OR mangaly_authz.has_scope(subject_account_id, 'family_info')
         OR mangaly_authz.has_scope(target_profile_id, 'family_info')
         OR mangaly_authz.has_scope(on_behalf_of_profile_id, 'candidate_info'));

-- Who sent this request, in relation to the candidate it is for. Readable by
-- any party to the request (subject, target, acting member) and by a circle
-- of either side. The candidate's NAME is returned only to the sending side
-- or once the connection is accepted — identity still moves on acceptance.
CREATE OR REPLACE FUNCTION mangaly_connection.request_sender_info(p_connection_id uuid)
RETURNS TABLE (
    acting_account_id uuid,
    subject_account_id uuid,
    relationship_type text,
    acting_name text,
    subject_name text,
    subject_profile_id uuid,
    target_name text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_connection, mangaly_home_circle, mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
    SELECT cr.acting_account_id,
           cr.subject_account_id,
           CASE WHEN cr.acting_account_id = cr.subject_account_id THEN 'self'
                ELSE COALESCE((SELECT m.relationship_type::text FROM mangaly_home_circle.membership m
                                WHERE m.candidate_profile_id = cr.subject_account_id
                                  AND m.member_account_id = cr.acting_account_id
                                ORDER BY (m.status = 'active') DESC, m.joined_at DESC LIMIT 1), 'relative') END,
           CASE WHEN cr.acting_account_id = cr.subject_account_id THEN NULL
                ELSE COALESCE(aa.display_name,
                              (SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = cr.acting_account_id)) END,
           CASE WHEN cr.status = 'accepted'
                  OR mangaly_authz.is_self(cr.subject_account_id)
                  OR mangaly_authz.is_self(cr.acting_account_id)
                  OR mangaly_authz.has_scope(cr.subject_account_id, 'family_info')
                THEN sp.name ELSE NULL END,
           sp.id,
           CASE WHEN cr.status = 'accepted'
                  OR mangaly_authz.is_self(cr.target_profile_id)
                  OR mangaly_authz.has_scope(cr.target_profile_id, 'family_info')
                THEN tp.name ELSE NULL END
      FROM mangaly_connection.connection_request cr
      LEFT JOIN mangaly_identity.account aa ON aa.id = cr.acting_account_id
      LEFT JOIN mangaly_profile.profile sp ON sp.account_id = cr.subject_account_id
      LEFT JOIN mangaly_profile.profile tp ON tp.account_id = cr.target_profile_id
     WHERE cr.id = p_connection_id
       AND (mangaly_authz.is_self(cr.acting_account_id)
            OR mangaly_authz.is_self(cr.subject_account_id)
            OR mangaly_authz.is_self(cr.target_profile_id)
            OR mangaly_authz.has_scope(cr.subject_account_id, 'family_info')
            OR mangaly_authz.has_scope(cr.target_profile_id, 'family_info'));
$$;

REVOKE ALL ON FUNCTION mangaly_connection.request_sender_info(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_connection.request_sender_info(uuid) TO mangaly_app;
