-- 048 — Trust & safety operations: operators, severity classification with a
-- real SLA clock, bounded automated detection, the moderator queue, account
-- suspension and the Tier 3/4 exits (DEC-V1-006, DEC-V1-007, DEC-V1-009,
-- DEC-V1-011, SP063, SP064, SP065; recorded as DEC-V1-028).
--
-- Before this migration a report was stored and nothing read it. This adds:
--   1. mangaly_operations.operator — who may open the review queue, with the
--      application-level roles (moderator, safety_investigator, operations).
--      The DB-level `mangaly.operator_role` value the existing RLS policies
--      read ('operations' / 'safety_case_investigation') is set by the API's
--      OperatorAccount dependency after checking this table.
--   2. mangaly_operations.account_suspension — a suspended account is refused
--      at sign-in resolution (api/deps.py) with a translated 403.
--   3. severity_classification gains the SLA deadlines (acknowledge_by /
--      resolve_by), the taxonomy version and the rationale; the clock starts
--      at classification time, never at pickup (SP065 tampering row).
--   4. mangaly_operations.case gains the moderator workflow columns
--      (acknowledged/resolved/outcome/reopen) on the existing state machine.
--   5. paging_event / csam_report_packet gain the columns the escalation code
--      records (vendor, dispatch status, structured packet metadata).
--   6. SECURITY DEFINER functions: classification and case opening run inside
--      a member's own request (a member may not write a classification row
--      under RLS), automated reports are written by the system, and the queue
--      reads reporter/reported summaries across schemas the operator role
--      cannot otherwise see. Every function checks its own precondition.
--
-- [SP063] The queue function below never filters on the absence of a
-- detection signal: a report with no automated signal is exactly as open as
-- one with a signal. [SP064] Nothing here reads mangaly_home_circle or
-- mangaly_trust in the safety path; the CSAM packet's "associated context"
-- (connection id) is assembled by the Operations schema's own function, not
-- by Safety.

-- 1 ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_operations.operator (
  account_id  uuid PRIMARY KEY,
  roles       text[] NOT NULL DEFAULT '{}'::text[],
  granted_at  timestamptz NOT NULL DEFAULT now(),
  granted_by  uuid,
  CONSTRAINT operator_roles_known CHECK (
    roles <@ ARRAY['moderator','safety_investigator','operations']::text[]
  )
);
COMMENT ON TABLE mangaly_operations.operator IS
  '[DEC-V1-028] Application-level operator roles. Never a user type: an operator is an ordinary member who additionally holds these roles.';

ALTER TABLE mangaly_operations.operator ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS operator_self_or_ops ON mangaly_operations.operator;
CREATE POLICY operator_self_or_ops ON mangaly_operations.operator
  USING (account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
         OR current_setting('mangaly.operator_role', true) = 'operations');

-- Cheap, RLS-independent read for the auth dependency and /auth/me.
CREATE OR REPLACE FUNCTION mangaly_operations.operator_roles(p_account_id uuid)
RETURNS text[]
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT COALESCE((SELECT o.roles FROM mangaly_operations.operator o WHERE o.account_id = p_account_id),
                    '{}'::text[]);
$$;
REVOKE ALL ON FUNCTION mangaly_operations.operator_roles(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.operator_roles(uuid) TO mangaly_app;

-- 2 ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_operations.account_suspension (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id         uuid NOT NULL,
  case_id            uuid REFERENCES mangaly_operations.case(id) ON DELETE SET NULL,
  reason             text,
  suspended_by       uuid NOT NULL,
  suspended_at       timestamptz NOT NULL DEFAULT now(),
  lifted_at          timestamptz,
  lifted_by          uuid
);
CREATE INDEX IF NOT EXISTS idx_account_suspension_active
  ON mangaly_operations.account_suspension(account_id) WHERE lifted_at IS NULL;
COMMENT ON TABLE mangaly_operations.account_suspension IS
  '[DEC-V1-028] An active row (lifted_at IS NULL) makes every member request from that account a translated 403 at session resolution.';

ALTER TABLE mangaly_operations.account_suspension ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS account_suspension_ops_only ON mangaly_operations.account_suspension;
CREATE POLICY account_suspension_ops_only ON mangaly_operations.account_suspension
  USING (current_setting('mangaly.operator_role', true) = 'operations');

CREATE OR REPLACE FUNCTION mangaly_operations.is_suspended(p_account_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT EXISTS (SELECT 1 FROM mangaly_operations.account_suspension s
                    WHERE s.account_id = p_account_id AND s.lifted_at IS NULL);
$$;
REVOKE ALL ON FUNCTION mangaly_operations.is_suspended(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.is_suspended(uuid) TO mangaly_app;

-- 3 ---------------------------------------------------------------------
ALTER TABLE mangaly_safety.severity_classification
  ADD COLUMN IF NOT EXISTS acknowledge_by   timestamptz,
  ADD COLUMN IF NOT EXISTS resolve_by       timestamptz,
  ADD COLUMN IF NOT EXISTS taxonomy_version text,
  ADD COLUMN IF NOT EXISTS rationale        text,
  ADD COLUMN IF NOT EXISTS case_id          uuid;
COMMENT ON COLUMN mangaly_safety.severity_classification.acknowledge_by IS
  '[DEC-V1-006/SP065] Deadline computed from sla_clock_started_at at classification time, never at pickup.';

-- 4 ---------------------------------------------------------------------
ALTER TABLE mangaly_operations.case
  ADD COLUMN IF NOT EXISTS acknowledged_at        timestamptz,
  ADD COLUMN IF NOT EXISTS acknowledged_by        uuid,
  ADD COLUMN IF NOT EXISTS resolved_at            timestamptz,
  ADD COLUMN IF NOT EXISTS resolved_by            uuid,
  ADD COLUMN IF NOT EXISTS outcome                text,
  ADD COLUMN IF NOT EXISTS resolution_note        text,
  ADD COLUMN IF NOT EXISTS reopened_count         integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS acknowledge_by         timestamptz;

-- 5 ---------------------------------------------------------------------
ALTER TABLE mangaly_operations.paging_event
  ADD COLUMN IF NOT EXISTS vendor         text,
  ADD COLUMN IF NOT EXISTS dedup_key      text,
  ADD COLUMN IF NOT EXISTS dispatch_status text,     -- 'sent' | 'logged' | 'failed'
  ADD COLUMN IF NOT EXISTS summary        text;      -- event type + reference only, never content
ALTER TABLE mangaly_operations.csam_report_packet
  ADD COLUMN IF NOT EXISTS packet_payload         jsonb,   -- DEC-V1-011 field groups; pointers only, no raw material
  ADD COLUMN IF NOT EXISTS dispatch_mode          text,    -- CSAM_REPORT_FALLBACK_MODE at assembly time
  ADD COLUMN IF NOT EXISTS dispatch_status        text,    -- 'stored_for_manual_portal' | 'submitted' | 'failed'
  ADD COLUMN IF NOT EXISTS human_reviewer_summary text,
  ADD COLUMN IF NOT EXISTS reporting_reference_id text;

-- 6a. Classify a report and open its case. Runs as owner because the caller
--     is the member who filed the report (or the system), and neither may
--     write classification or case rows under RLS. Idempotent per report.
CREATE OR REPLACE FUNCTION mangaly_safety.classify_report(
    p_report_id uuid,
    p_tier smallint,
    p_acknowledge_by timestamptz,
    p_resolve_by timestamptz,
    p_taxonomy_version text,
    p_rationale text
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_safety, mangaly_operations, pg_temp
AS $$
DECLARE
    v_case_id uuid;
    v_now timestamptz := now();
BEGIN
    IF NOT EXISTS (SELECT 1 FROM mangaly_safety.report r WHERE r.id = p_report_id) THEN
        RETURN NULL;
    END IF;
    SELECT sc.case_id INTO v_case_id
      FROM mangaly_safety.severity_classification sc
     WHERE sc.report_id = p_report_id;
    IF v_case_id IS NOT NULL THEN
        RETURN v_case_id;
    END IF;

    v_case_id := gen_random_uuid();
    INSERT INTO mangaly_operations.case
        (id, case_type, source_schema, source_reference_id, status, priority_tier,
         sla_target_at, acknowledge_by, created_at, updated_at)
    VALUES (v_case_id, 'safety_abuse', 'mangaly_safety', p_report_id, 'intake', p_tier,
            p_resolve_by, p_acknowledge_by, v_now, v_now);

    INSERT INTO mangaly_safety.severity_classification
        (id, report_id, tier, classified_at, sla_clock_started_at, acknowledge_by,
         resolve_by, taxonomy_version, rationale, case_id)
    VALUES (gen_random_uuid(), p_report_id, p_tier, v_now, v_now, p_acknowledge_by,
            p_resolve_by, p_taxonomy_version, p_rationale, v_case_id);
    RETURN v_case_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_safety.classify_report(uuid, smallint, timestamptz, timestamptz, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_safety.classify_report(uuid, smallint, timestamptz, timestamptz, text, text) TO mangaly_app;

-- 6b. An automated detection signal plus the report it opens. The signal's
--     metadata carries the signal type and pattern class only (SP064), never
--     the message text; the report's evidence keeps the surrounding thread
--     for the human reviewer, same shape as report_conversation() (044).
--     reporter_account_id is the nil uuid: "the system", not a person.
CREATE OR REPLACE FUNCTION mangaly_safety.open_automated_report(
    p_conversation_id uuid,
    p_message_id uuid,
    p_sender_account_id uuid,
    p_signal_type text,
    p_category text,
    p_metadata jsonb
) RETURNS TABLE (report_id uuid, signal_id uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_safety, mangaly_communication, pg_temp
AS $$
DECLARE
    v_report uuid := gen_random_uuid();
    v_signal uuid := gen_random_uuid();
BEGIN
    INSERT INTO mangaly_safety.detection_signal (id, conversation_id, signal_type, inference, metadata)
    VALUES (v_signal, p_conversation_id, p_signal_type, true,
            COALESCE(p_metadata, '{}'::jsonb) || jsonb_build_object('message_id', p_message_id,
                                                                     'sender_account_id', p_sender_account_id));
    INSERT INTO mangaly_safety.report
        (id, reporter_account_id, reported_profile_id, reported_message_id,
         reported_conversation_id, category, description, source, evidence)
    VALUES (v_report, '00000000-0000-0000-0000-000000000000'::uuid, p_sender_account_id, p_message_id,
            p_conversation_id, p_category, NULL, 'automated',
            (SELECT COALESCE(jsonb_agg(jsonb_build_object(
                        'sender_account_id', m.sender_account_id,
                        'kind', m.kind,
                        'content', m.content,
                        'sent_at', m.sent_at,
                        'flagged', m.id = p_message_id) ORDER BY m.sent_at), '[]'::jsonb)
               FROM (SELECT * FROM mangaly_communication.message
                      WHERE conversation_id = p_conversation_id
                      ORDER BY sent_at DESC LIMIT 40) m));
    RETURN QUERY SELECT v_report, v_signal;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_safety.open_automated_report(uuid, uuid, uuid, text, text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_safety.open_automated_report(uuid, uuid, uuid, text, text, jsonb) TO mangaly_app;

-- 6c. A profile-level signal (no conversation): a date of birth under 18.
CREATE OR REPLACE FUNCTION mangaly_safety.open_profile_signal_report(
    p_account_id uuid,
    p_signal_type text,
    p_category text,
    p_metadata jsonb
) RETURNS TABLE (report_id uuid, signal_id uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_safety, pg_temp
AS $$
DECLARE
    v_report uuid := gen_random_uuid();
    v_signal uuid := gen_random_uuid();
BEGIN
    -- One open automated report per (person, signal type): a sweep that runs
    -- twice must not flood the queue.
    IF EXISTS (SELECT 1 FROM mangaly_safety.report r
                 JOIN mangaly_operations.case c ON c.source_reference_id = r.id
                WHERE r.reported_profile_id = p_account_id AND r.source = 'automated'
                  AND r.category = p_category AND c.status <> 'resolved') THEN
        RETURN;
    END IF;
    INSERT INTO mangaly_safety.detection_signal (id, conversation_id, signal_type, inference, metadata)
    VALUES (v_signal, NULL, p_signal_type, true,
            COALESCE(p_metadata, '{}'::jsonb) || jsonb_build_object('account_id', p_account_id));
    INSERT INTO mangaly_safety.report
        (id, reporter_account_id, reported_profile_id, category, source)
    VALUES (v_report, '00000000-0000-0000-0000-000000000000'::uuid, p_account_id, p_category, 'automated');
    RETURN QUERY SELECT v_report, v_signal;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_safety.open_profile_signal_report(uuid, text, text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_safety.open_profile_signal_report(uuid, text, text, jsonb) TO mangaly_app;

-- 6d. Minor-safety sweep: every profile whose date of birth is under 18 today.
--     The wizard refuses these; this catches anything that got past it.
CREATE OR REPLACE FUNCTION mangaly_safety.underage_profiles()
RETURNS TABLE (account_id uuid, date_of_birth date)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, pg_temp
AS $$
    SELECT p.account_id, p.date_of_birth
      FROM mangaly_profile.profile p
     WHERE p.date_of_birth > (current_date - interval '18 years')::date;
$$;
REVOKE ALL ON FUNCTION mangaly_safety.underage_profiles() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_safety.underage_profiles() TO mangaly_app;

-- 6e. Exits: paging event and CSAM packet rows are written by the request
--     that classified (a member's), so they run as owner too.
CREATE OR REPLACE FUNCTION mangaly_operations.record_paging_event(
    p_case_id uuid, p_tier smallint, p_vendor text, p_vendor_ref text,
    p_dedup_key text, p_dispatch_status text, p_summary text
) RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    INSERT INTO mangaly_operations.paging_event
        (id, case_id, tier, paging_vendor_ref, vendor, dedup_key, dispatch_status, summary)
    VALUES (gen_random_uuid(), p_case_id, p_tier, p_vendor_ref, p_vendor, p_dedup_key, p_dispatch_status, p_summary)
    RETURNING id;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.record_paging_event(uuid, smallint, text, text, text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.record_paging_event(uuid, smallint, text, text, text, text, text) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_operations.store_csam_packet(
    p_case_id uuid, p_payload jsonb, p_submitted_to text, p_dispatch_mode text, p_dispatch_status text
) RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    INSERT INTO mangaly_operations.csam_report_packet
        (id, case_id, packet_payload_ref, submitted_to, packet_payload, dispatch_mode, dispatch_status)
    VALUES (gen_random_uuid(), p_case_id, 'mangaly_operations.csam_report_packet:' || p_case_id::text,
            p_submitted_to, p_payload, p_dispatch_mode, p_dispatch_status)
    RETURNING id;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.store_csam_packet(uuid, jsonb, text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.store_csam_packet(uuid, jsonb, text, text, text) TO mangaly_app;

-- Associated context for the CSAM packet (DEC-V1-011): the connection the
-- flagged conversation belongs to. Read by Operations, never by Safety.
CREATE OR REPLACE FUNCTION mangaly_operations.packet_context(p_account_id uuid, p_conversation_id uuid)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_identity, mangaly_profile, mangaly_communication, pg_temp
AS $$
    SELECT jsonb_build_object(
        'account_id', a.id,
        'profile_id', p.id,
        'phone_identifier', a.phone_identifier,
        'email_identifier', a.email_identifier,
        'account_created_at', a.created_at,
        'identifier_verified_at', a.identifier_verified_at,
        'connection_id', (SELECT cv.connection_id FROM mangaly_communication.conversation cv WHERE cv.id = p_conversation_id))
      FROM mangaly_identity.account a
      LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id
     WHERE a.id = p_account_id;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.packet_context(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.packet_context(uuid, uuid) TO mangaly_app;

-- The detection signal that opened an automated report is linked through the
-- signal's metadata (message_id) rather than the classification row, so the
-- queue's signal column reads it directly. Simpler than the join above:
CREATE OR REPLACE FUNCTION mangaly_operations.case_signal_type(p_report_id uuid)
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_safety, pg_temp
AS $$
    SELECT ds.signal_type
      FROM mangaly_safety.report r
      JOIN mangaly_safety.detection_signal ds
        ON (ds.metadata ->> 'message_id')::uuid = r.reported_message_id
        OR (r.reported_message_id IS NULL AND (ds.metadata ->> 'account_id')::uuid = r.reported_profile_id
            AND ds.conversation_id IS NULL)
     WHERE r.id = p_report_id AND r.source = 'automated'
     ORDER BY ds.detected_at DESC LIMIT 1;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.case_signal_type(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.case_signal_type(uuid) TO mangaly_app;

-- 6f. The review queue. Requires the operations role; joins the report, its
--     classification and the two people's display summaries. [SP063] There is
--     no predicate on detection_signal here — the LEFT JOIN is informational.
CREATE OR REPLACE FUNCTION mangaly_operations.safety_queue(p_state text, p_tier smallint)
RETURNS TABLE (
    case_id uuid, status text, tier smallint, created_at timestamptz,
    acknowledge_by timestamptz, resolve_by timestamptz, acknowledged_at timestamptz,
    resolved_at timestamptz, outcome text, reopened_count integer,
    report_id uuid, category text, source text, description text,
    has_evidence boolean, signal_type text,
    reporter_account_id uuid, reporter_name text,
    reported_account_id uuid, reported_name text, reported_photo_ref text,
    reported_suspended boolean, paged boolean
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_safety, mangaly_identity, mangaly_profile, pg_temp
AS $$
    SELECT c.id, c.status::text, c.priority_tier, c.created_at,
           c.acknowledge_by, c.sla_target_at, c.acknowledged_at, c.resolved_at, c.outcome, c.reopened_count,
           r.id, r.category, r.source, r.description,
           r.evidence IS NOT NULL,
           mangaly_operations.case_signal_type(r.id),   -- informational; never a filter (SP063)
           r.reporter_account_id, COALESCE(rp.name, ra.display_name),
           r.reported_profile_id, COALESCE(tp.name, ta.display_name),
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = tp.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1),
           mangaly_operations.is_suspended(r.reported_profile_id),
           EXISTS (SELECT 1 FROM mangaly_operations.paging_event pe WHERE pe.case_id = c.id)
      FROM mangaly_operations.case c
      JOIN mangaly_safety.report r ON r.id = c.source_reference_id
      LEFT JOIN mangaly_identity.account ra ON ra.id = r.reporter_account_id
      LEFT JOIN mangaly_profile.profile rp ON rp.account_id = r.reporter_account_id
      LEFT JOIN mangaly_identity.account ta ON ta.id = r.reported_profile_id
      LEFT JOIN mangaly_profile.profile tp ON tp.account_id = r.reported_profile_id
     WHERE current_setting('mangaly.operator_role', true) = 'operations'
       AND c.case_type = 'safety_abuse'
       AND (p_state IS NULL
            OR (p_state = 'open' AND c.status IN ('intake','triage'))
            OR (p_state = 'acknowledged' AND c.status IN ('assigned','investigation','decided','escalated'))
            OR (p_state = 'resolved' AND c.status = 'resolved'))
       AND (p_tier IS NULL OR c.priority_tier = p_tier)
     ORDER BY (c.status = 'resolved'), c.priority_tier DESC, COALESCE(c.acknowledge_by, c.sla_target_at, c.created_at) ASC, c.created_at ASC;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.safety_queue(text, smallint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.safety_queue(text, smallint) TO mangaly_app;

-- 6g. Case actions. Each checks the role and returns false when nothing changed.
CREATE OR REPLACE FUNCTION mangaly_operations.acknowledge_case(p_case_id uuid, p_operator uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
DECLARE v_n integer;
BEGIN
    IF current_setting('mangaly.operator_role', true) <> 'operations' THEN RETURN false; END IF;
    UPDATE mangaly_operations.case
       SET status = 'investigation', acknowledged_at = COALESCE(acknowledged_at, now()),
           acknowledged_by = COALESCE(acknowledged_by, p_operator),
           assigned_operator_id = p_operator, updated_at = now()
     WHERE id = p_case_id AND status IN ('intake','triage');
    GET DIAGNOSTICS v_n = ROW_COUNT;
    RETURN v_n > 0;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.acknowledge_case(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.acknowledge_case(uuid, uuid) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_operations.resolve_case(
    p_case_id uuid, p_operator uuid, p_outcome text, p_note text
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
DECLARE v_n integer;
BEGIN
    IF current_setting('mangaly.operator_role', true) <> 'operations' THEN RETURN false; END IF;
    UPDATE mangaly_operations.case
       SET status = CASE WHEN p_outcome = 'escalated_to_investigation' THEN 'escalated' ELSE 'resolved' END,
           acknowledged_at = COALESCE(acknowledged_at, now()),
           acknowledged_by = COALESCE(acknowledged_by, p_operator),
           resolved_at = CASE WHEN p_outcome = 'escalated_to_investigation' THEN NULL ELSE now() END,
           resolved_by = p_operator, outcome = p_outcome,
           resolution_note = NULLIF(left(btrim(COALESCE(p_note, '')), 4000), ''),
           assigned_operator_id = p_operator, updated_at = now()
     WHERE id = p_case_id AND status <> 'resolved';
    GET DIAGNOSTICS v_n = ROW_COUNT;
    IF v_n > 0 THEN
        INSERT INTO mangaly_operations.case_decision (id, case_id, decision_type, decided_by_operator_id, rationale_text)
        VALUES (gen_random_uuid(), p_case_id,
                CASE WHEN p_outcome = 'escalated_to_investigation' THEN 'escalate'
                     WHEN p_outcome = 'no_action' THEN 'deny' ELSE 'approve' END,
                p_operator, p_note);
    END IF;
    RETURN v_n > 0;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.resolve_case(uuid, uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.resolve_case(uuid, uuid, text, text) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_operations.reopen_case(p_case_id uuid, p_operator uuid, p_note text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
DECLARE v_n integer;
BEGIN
    IF current_setting('mangaly.operator_role', true) <> 'operations' THEN RETURN false; END IF;
    UPDATE mangaly_operations.case
       SET status = 'investigation', resolved_at = NULL, resolved_by = NULL, outcome = NULL,
           resolution_note = NULLIF(left(btrim(COALESCE(p_note, '')), 4000), ''),
           reopened_count = reopened_count + 1, assigned_operator_id = p_operator, updated_at = now()
     WHERE id = p_case_id AND status IN ('resolved','escalated');
    GET DIAGNOSTICS v_n = ROW_COUNT;
    RETURN v_n > 0;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.reopen_case(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.reopen_case(uuid, uuid, text) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_operations.suspend_account(
    p_account_id uuid, p_case_id uuid, p_operator uuid, p_reason text
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
DECLARE v_id uuid;
BEGIN
    IF current_setting('mangaly.operator_role', true) <> 'operations' THEN RETURN NULL; END IF;
    IF p_account_id = p_operator THEN RETURN NULL; END IF;
    SELECT id INTO v_id FROM mangaly_operations.account_suspension
     WHERE account_id = p_account_id AND lifted_at IS NULL;
    IF v_id IS NOT NULL THEN RETURN v_id; END IF;
    v_id := gen_random_uuid();
    INSERT INTO mangaly_operations.account_suspension (id, account_id, case_id, reason, suspended_by)
    VALUES (v_id, p_account_id, p_case_id, NULLIF(left(btrim(COALESCE(p_reason, '')), 2000), ''), p_operator);
    RETURN v_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.suspend_account(uuid, uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.suspend_account(uuid, uuid, uuid, text) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_operations.lift_suspension(p_account_id uuid, p_operator uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
DECLARE v_n integer;
BEGIN
    IF current_setting('mangaly.operator_role', true) <> 'operations' THEN RETURN false; END IF;
    UPDATE mangaly_operations.account_suspension
       SET lifted_at = now(), lifted_by = p_operator
     WHERE account_id = p_account_id AND lifted_at IS NULL;
    GET DIAGNOSTICS v_n = ROW_COUNT;
    RETURN v_n > 0;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.lift_suspension(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.lift_suspension(uuid, uuid) TO mangaly_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mangaly_operations TO mangaly_app;
