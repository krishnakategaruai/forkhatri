-- =============================================================================
-- 023 — A request a family member sends belongs to the candidate, not to them.
--
-- WHY (2026-09-17, product owner, acting as a parent): "parents can send a
-- request direct to a profile — understand how shaadi.com works: even if the
-- account is controlled by parents, they can send it. Here we don't." On
-- Shaadi.com a parent commonly creates and runs the profile and sends interest
-- for their son or daughter (the site asks only that the profile says so). This
-- overrides DEC-V1-019, which refused every on-behalf-of request and left a
-- family member only "Suggest to the candidate" — and it restores FR042's own
-- sealed wording: "a candidate OR AUTHORIZED FAMILY PARTICIPANT ... may send a
-- connection request, recording the requester's identity and capacity (self or
-- on-behalf-of)".
--
-- DEC-V1-019 was made for a real reason, which this migration fixes properly
-- instead of banning the action: acceptance granted profile visibility between
-- the SENDING ACCOUNT and the recipient, so a parent's request connected the
-- PARENT to the recipient (or nobody at all, a parent having no profile) rather
-- than the candidate it was sent for.
--
-- The fix is to say plainly, in one column, whose request it is:
--   * `subject_account_id` — the candidate the request is about. Their own
--     account when they send it themselves; the candidate's account when a
--     Home Circle member sends it for them. `acting_account_id` still records
--     WHO pressed send (BR15 accountability) and never changes meaning.
--   * every downstream rule then keys on the subject: who may see the request,
--     who the conversation is between, and who gets profile visibility on
--     acceptance. A family member sending a request never gains visibility of
--     the recipient, and never joins the candidate's private conversation.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_connection.connection_request
  ADD COLUMN IF NOT EXISTS subject_account_id uuid;

-- Existing rows: the sender was always the subject (on-behalf was refused).
UPDATE mangaly_connection.connection_request
   SET subject_account_id = COALESCE(
         (SELECT p.account_id FROM mangaly_profile.profile p WHERE p.id = on_behalf_of_profile_id),
         acting_account_id)
 WHERE subject_account_id IS NULL;

ALTER TABLE mangaly_connection.connection_request
  ALTER COLUMN subject_account_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_connection_request_subject
  ON mangaly_connection.connection_request (subject_account_id, status);

-- The candidate sees a request sent in their name; so does the family member
-- who sent it (they are `acting`), which is what lets them see their own work.
DROP POLICY IF EXISTS connection_participants ON mangaly_connection.connection_request;
CREATE POLICY connection_participants ON mangaly_connection.connection_request
  USING (mangaly_authz.is_self(acting_account_id)
         OR mangaly_authz.is_self(target_profile_id)
         OR mangaly_authz.is_self(subject_account_id)
         OR mangaly_authz.has_scope(on_behalf_of_profile_id, 'candidate_info'));

-- Sharing (FR046-FR048) is the candidate's own contact information, so it is
-- between the subject and the recipient — never the family member who sent it.
DROP POLICY IF EXISTS sharing_grant_participants ON mangaly_connection.sharing_grant;
CREATE POLICY sharing_grant_participants ON mangaly_connection.sharing_grant
  USING (EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                 WHERE c.id = sharing_grant.connection_id
                   AND (mangaly_authz.is_self(c.subject_account_id)
                        OR mangaly_authz.is_self(c.target_profile_id))));

-- Acceptance grants visibility between the CANDIDATE and the recipient.
-- Re-derived from the row (never caller-supplied), as in migration 010.
CREATE OR REPLACE FUNCTION mangaly_authz.grant_connection_candidate_info(
    p_connection_id uuid,
    p_caller_account_id uuid
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_authz, mangaly_connection, mangaly_profile, pg_temp
AS $$
DECLARE
    v_subject_account_id uuid;
    v_target_account_id uuid;
    v_subject_profile_id uuid;
    v_target_profile_id uuid;
BEGIN
    SELECT subject_account_id, target_profile_id
    INTO v_subject_account_id, v_target_account_id
    FROM mangaly_connection.connection_request
    WHERE id = p_connection_id
      AND status = 'accepted'
      AND (subject_account_id = p_caller_account_id OR target_profile_id = p_caller_account_id);

    IF v_subject_account_id IS NULL THEN
        RETURN; -- not an accepted connection the caller is actually part of
    END IF;

    SELECT id INTO v_subject_profile_id FROM mangaly_profile.profile WHERE account_id = v_subject_account_id;
    SELECT id INTO v_target_profile_id FROM mangaly_profile.profile WHERE account_id = v_target_account_id;

    IF v_subject_profile_id IS NULL OR v_target_profile_id IS NULL THEN
        RETURN;
    END IF;

    INSERT INTO mangaly_authz.grant
        (id, subject_id, target_profile_id, scope, grant_type, status, source_component, source_reference_id)
    VALUES
        (gen_random_uuid(), v_target_account_id, v_subject_profile_id, 'candidate_info',
         'connection_accepted', 'active', 'connection', p_connection_id);

    INSERT INTO mangaly_authz.grant
        (id, subject_id, target_profile_id, scope, grant_type, status, source_component, source_reference_id)
    VALUES
        (gen_random_uuid(), v_subject_account_id, v_target_profile_id, 'candidate_info',
         'connection_accepted', 'active', 'connection', p_connection_id);
END;
$$;

REVOKE ALL ON FUNCTION mangaly_authz.grant_connection_candidate_info(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_authz.grant_connection_candidate_info(uuid, uuid) TO mangaly_app;
