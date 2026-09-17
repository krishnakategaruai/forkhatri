-- =============================================================================
-- 028 — Either participant can clear their own conversation (FR050, DEC-V1-021).
--
-- WHY (2026-09-17, found live):
--   `message_delete_sender_or_safety_case` let a member delete only the rows
--   they had sent themselves. Two consequences, both silent:
--     * DEC-V1-021's session rule did not hold. When one person ended the
--       session, their own messages went and the other person's stayed, so the
--       thread was not cleared for both — the check caught exactly this.
--     * DEC-V1-014's retention promise was never kept either. The lazy purge in
--       `list_messages()` runs as whoever opened the thread, so it only ever
--       deleted that reader's own aged-out rows; the other party's messages
--       stayed past the window. "Deleted from storage" was not true.
--   A conversation belongs to its two people jointly, so either of them may
--   clear it — the same pair the SELECT policy already treats as participants.
--   The safety-case clause is carried over unchanged.
-- Idempotent: safe to re-run.
-- =============================================================================

DROP POLICY IF EXISTS message_delete_sender_or_safety_case ON mangaly_communication.message;
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
    OR (
      EXISTS (
        SELECT 1 FROM mangaly_communication.conversation cv
         WHERE cv.id = message.conversation_id
      )
      AND current_setting('mangaly.operator_role', true) = 'safety_case_investigation'
    )
  );
