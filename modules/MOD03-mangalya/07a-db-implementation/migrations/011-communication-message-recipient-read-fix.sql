-- 011 — A message's recipient could never read it (real RLS defect, not a
-- pre-authorization chicken-and-egg like the others in this file)
--
-- [Found live, 2026-09-14] `message_sender_or_safety_case` was a single
-- `FOR ALL` policy: `is_self(sender_account_id) OR (safety-case
-- investigation)`, with NO clause for "the other participant in this
-- message's conversation." FR049 requires two-way private messaging
-- between the two connected parties; as written, a recipient's own session
-- could never read a message the other party sent — confirmed live via a
-- real cross-account read that returned zero rows despite the message
-- existing. Raised against Step 7a for ratification.
--
-- Fixed by splitting the single `FOR ALL` policy into three, rather than
-- widening the one policy's USING clause: a `FOR ALL` policy's `WITH CHECK`
-- defaults to its own `USING` when none is given, so simply OR-ing in "any
-- participant" to the existing policy would have also let a RECIPIENT
-- **insert** a row claiming to be the sender (`sender_account_id` set to
-- the other party) — a real spoofing hole, not merely a missed read case.
-- Splitting by command keeps INSERT exactly as strict as before
-- (sender-only, matching every message write in this codebase, which
-- always sets `sender_account_id` to the caller's own account id) while
-- only SELECT gains the missing participant clause. This does not weaken
-- SP051's own finding — that finding is about there being no THIRD,
-- unaccountable read path into message content, and this migration adds
-- none; it only restores the two legitimate parties' mutual visibility,
-- which is the entire point of a two-way conversation.

DROP POLICY message_sender_or_safety_case ON mangaly_communication.message;

CREATE POLICY message_insert_sender_only ON mangaly_communication.message
    FOR INSERT
    WITH CHECK (mangaly_authz.is_self(sender_account_id));

CREATE POLICY message_select_participant_or_safety_case ON mangaly_communication.message
    FOR SELECT
    USING (
        mangaly_authz.is_self(sender_account_id)
        OR EXISTS (
            SELECT 1
            FROM mangaly_communication.conversation cv
            JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
            WHERE cv.id = message.conversation_id
              AND (mangaly_authz.is_self(cr.acting_account_id) OR mangaly_authz.is_self(cr.target_profile_id))
        )
        OR (
            EXISTS (SELECT 1 FROM mangaly_communication.conversation cv WHERE cv.id = message.conversation_id)
            AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation'
        )
    );

-- Messages are immutable once sent (no edit/delete feature anywhere in this
-- codebase) — kept exactly as restrictive as the original policy was for
-- these two commands, matching prior behaviour precisely rather than
-- widening anything beyond the one gap actually found.
CREATE POLICY message_update_sender_or_safety_case ON mangaly_communication.message
    FOR UPDATE
    USING (
        mangaly_authz.is_self(sender_account_id)
        OR (
            EXISTS (SELECT 1 FROM mangaly_communication.conversation cv WHERE cv.id = message.conversation_id)
            AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation'
        )
    );

CREATE POLICY message_delete_sender_or_safety_case ON mangaly_communication.message
    FOR DELETE
    USING (
        mangaly_authz.is_self(sender_account_id)
        OR (
            EXISTS (SELECT 1 FROM mangaly_communication.conversation cv WHERE cv.id = message.conversation_id)
            AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation'
        )
    );
