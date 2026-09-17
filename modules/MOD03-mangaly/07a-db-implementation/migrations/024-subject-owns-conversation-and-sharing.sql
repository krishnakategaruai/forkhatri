-- =============================================================================
-- 024 — The candidate, not whoever pressed send, is the party to the conversation.
--
-- WHY (2026-09-17): migration 023 let an authorized family member send a
-- connection request for a candidate. Three policies still decided "are you a
-- party to this connection?" by looking at `acting_account_id`, which is now the
-- sender rather than the subject. Found by running the live check
-- (`scripts/check_family_sends_request.py`): after the match accepted a request
-- Ananya's mother had sent, ANANYA could not send her first message — the
-- conversation row was refused by its own RLS policy. The same reading applies
-- to message visibility and to per-category sharing.
--
-- This also restores the per-sharer WITH CHECK clause from migration 015 that
-- 023's rewrite of `sharing_grant_participants` dropped: a grant may still only
-- be written by the sharer themselves, on an accepted connection.
-- Idempotent: safe to re-run.
-- =============================================================================

DROP POLICY IF EXISTS conversation_participants ON mangaly_communication.conversation;
CREATE POLICY conversation_participants ON mangaly_communication.conversation
  USING (EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                 WHERE c.id = conversation.connection_id
                   AND (mangaly_authz.is_self(c.subject_account_id)
                        OR mangaly_authz.is_self(c.target_profile_id))));

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
        OR (
            EXISTS (SELECT 1 FROM mangaly_communication.conversation cv WHERE cv.id = message.conversation_id)
            AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation'
        )
    );

DROP POLICY IF EXISTS sharing_grant_participants ON mangaly_connection.sharing_grant;
CREATE POLICY sharing_grant_participants ON mangaly_connection.sharing_grant
  USING (EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                 WHERE c.id = sharing_grant.connection_id
                   AND (mangaly_authz.is_self(c.subject_account_id)
                        OR mangaly_authz.is_self(c.target_profile_id))))
  WITH CHECK (mangaly_authz.is_self(granted_by_account_id)
              AND EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                          WHERE c.id = sharing_grant.connection_id
                            AND c.status = 'accepted'
                            AND (mangaly_authz.is_self(c.subject_account_id)
                                 OR mangaly_authz.is_self(c.target_profile_id))));
