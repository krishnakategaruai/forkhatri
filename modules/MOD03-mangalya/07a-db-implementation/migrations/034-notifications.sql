-- =============================================================================
-- 034 — In-app notifications, one row per reader, scoped to a context.
--
-- WHY (2026-09-17, rework contract §3): `GET /notifications?for_candidate=`
-- lists what happened in a context; `POST /notifications/read` marks rows
-- read. `mangaly_notification.inbox_entry` (migration 001, TR098) is the
-- inbox record and is reused:
--   * `subject_account_id` — the context the entry belongs to (the candidate
--     whose matter it is). A personal entry (an invitation to the reader) has
--     subject = recipient.
--   * `kind` — the contract's vocabulary; `link` — where the row leads.
--   * One row PER READER: when a request arrives for Ananya, Ananya and every
--     active member of her circle each get their own row, so read state is
--     per person and the existing `inbox_recipient_only` policy is enough.
-- Writing a row for someone else is not allowed by that policy, so the two
-- writers below are SECURITY DEFINER, held to migration 010's rules: a
-- signed-in caller, recipients derived from rows (`notify_circle`), and a
-- payload that carries ids and non-identifying params only (SP098).
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_notification.inbox_entry
  ADD COLUMN IF NOT EXISTS subject_account_id uuid,
  ADD COLUMN IF NOT EXISTS kind text,
  ADD COLUMN IF NOT EXISTS link text;

UPDATE mangaly_notification.inbox_entry
   SET kind = event_type WHERE kind IS NULL;
UPDATE mangaly_notification.inbox_entry
   SET subject_account_id = recipient_account_id WHERE subject_account_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_inbox_recipient_subject
  ON mangaly_notification.inbox_entry (recipient_account_id, subject_account_id, created_at DESC);

CREATE OR REPLACE FUNCTION mangaly_notification.notify(
    p_recipients uuid[],
    p_subject_account_id uuid,
    p_kind text,
    p_payload jsonb,
    p_link text
) RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_notification, pg_temp
AS $$
DECLARE
    v_count integer := 0;
    v_recipient uuid;
BEGIN
    IF NULLIF(current_setting('mangaly.account_id', true), '') IS NULL THEN
        RETURN 0;
    END IF;
    FOR v_recipient IN SELECT DISTINCT r FROM unnest(p_recipients) AS r WHERE r IS NOT NULL LOOP
        INSERT INTO mangaly_notification.inbox_entry
            (recipient_account_id, source_component, event_type, payload, subject_account_id, kind, link)
        VALUES
            (v_recipient, 'notifications', p_kind, COALESCE(p_payload, '{}'::jsonb),
             COALESCE(p_subject_account_id, v_recipient), p_kind, p_link);
        v_count := v_count + 1;
    END LOOP;
    RETURN v_count;
END;
$$;

-- The candidate plus every active member of their circle, each their own row.
CREATE OR REPLACE FUNCTION mangaly_notification.notify_circle(
    p_candidate_account_id uuid,
    p_kind text,
    p_payload jsonb,
    p_link text,
    p_exclude uuid DEFAULT NULL
) RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_notification, mangaly_home_circle, pg_temp
AS $$
DECLARE
    v_recipients uuid[];
BEGIN
    SELECT array_agg(x) INTO v_recipients
      FROM (
        SELECT p_candidate_account_id AS x
        UNION
        SELECT m.member_account_id FROM mangaly_home_circle.membership m
         WHERE m.candidate_profile_id = p_candidate_account_id AND m.status = 'active'
      ) s
     WHERE x IS DISTINCT FROM p_exclude;
    RETURN mangaly_notification.notify(v_recipients, p_candidate_account_id, p_kind, p_payload, p_link);
END;
$$;

REVOKE ALL ON FUNCTION mangaly_notification.notify(uuid[], uuid, text, jsonb, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_notification.notify(uuid[], uuid, text, jsonb, text) TO mangaly_app;
REVOKE ALL ON FUNCTION mangaly_notification.notify_circle(uuid, text, jsonb, text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_notification.notify_circle(uuid, text, jsonb, text, uuid) TO mangaly_app;

GRANT USAGE ON SCHEMA mangaly_notification TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON mangaly_notification.inbox_entry TO mangaly_app;
