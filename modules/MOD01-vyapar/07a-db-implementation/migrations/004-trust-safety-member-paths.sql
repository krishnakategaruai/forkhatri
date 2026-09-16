-- [TR039/TR040/TR041 gaps, found during Step 9 design of slice 6 by reading
-- the live RLS policies before writing code — fixed forward with a new
-- migration; 001-initial.sql is applied history and is not edited.]
--
-- Gap 1 (FR39): vyapar_trust_safety.moderation_cases is operator-only
-- (moderation_cases_operator_only), and reports.case_id is NOT NULL. A
-- member's session therefore cannot create or merge the case its own report
-- must reference — so no member could ever file a report.
-- Gap 2 (FR41): the same operator-only policy means the reported party
-- cannot read the decided case they are entitled to appeal.
-- Gap 3 (FR40): enquiries/partnership_requests/reviews WITH CHECK clauses
-- admit only the parties themselves, so an operator's Remove/Restore on
-- those object kinds is rejected by RLS.
-- Gap 4 (FR03/FR40): automated safety flags are raised during the AUTHOR's
-- own submit/publish request, which also cannot insert a moderation case.
--
-- Fix: narrow SECURITY DEFINER functions, the same pattern as
-- ensure_member()/contacts_for_viewer()/notification_targets()/is_blocked().
-- Each takes the caller identity from vyapar.authz_context (never a
-- parameter), guards itself, and exposes only what its one job needs. The
-- reported party never receives reporter identity from any of them.
SET search_path TO vyapar_trust_safety, pg_temp;

-- FR40 severity target response times — one definition, reused below.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.target_interval(p_severity text)
RETURNS interval LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE p_severity WHEN 'critical' THEN interval '4 hours' WHEN 'high' THEN interval '24 hours'
                         WHEN 'medium' THEN interval '72 hours' ELSE interval '7 days' END;
$$;

-- FR39 "severity auto-suggested from reason".
CREATE OR REPLACE FUNCTION vyapar_trust_safety.severity_for_reason(p_reason text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE WHEN p_reason IN ('scam','impersonation','harassment','discrimination') THEN 'high'
              WHEN p_reason IN ('fake','privacy') THEN 'medium' ELSE 'low' END;
$$;

-- Gap 1. Create or merge (dedup by object within an open case, incrementing
-- reporter_count — TR039). High/Critical auto-limits the case AND the object
-- at report-merge time (TR040's own text names this exact coupling; this is
-- the one documented cross-schema write for it).
CREATE OR REPLACE FUNCTION vyapar_trust_safety.file_report(
  p_object_kind text, p_object_id uuid, p_subject_member_id text, p_reason text, p_evidence_text text
) RETURNS TABLE(report_id uuid, case_id uuid, severity text, merged boolean)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_trust_safety, pg_temp AS $$
DECLARE
  v_reporter text := current_setting('vyapar.authz_context', true);
  v_case uuid;
  v_sev text := vyapar_trust_safety.severity_for_reason(p_reason);
  v_merged boolean := false;
  v_report uuid;
BEGIN
  IF v_reporter IS NULL OR v_reporter = '' THEN RAISE EXCEPTION 'no_caller_context'; END IF;
  IF p_subject_member_id = v_reporter THEN RAISE EXCEPTION 'cannot_report_own'; END IF;

  SELECT c.id INTO v_case FROM vyapar_trust_safety.moderation_cases c
   WHERE c.object_kind = p_object_kind AND c.object_id = p_object_id AND c.state IN ('open','in_review','escalated')
   ORDER BY c.created_at LIMIT 1 FOR UPDATE;

  IF v_case IS NULL THEN
    INSERT INTO vyapar_trust_safety.moderation_cases
      (object_kind, object_id, subject_member_id, source, severity, reporter_count, primary_reason, distribution_limited, target_due_at)
    VALUES (p_object_kind, p_object_id, p_subject_member_id, 'report', v_sev, 1, p_reason, v_sev IN ('high','critical'),
            now() + vyapar_trust_safety.target_interval(v_sev))
    RETURNING id INTO v_case;
  ELSE
    v_merged := true;
    UPDATE vyapar_trust_safety.moderation_cases c SET
      reporter_count = c.reporter_count + 1,
      severity = CASE WHEN array_position(ARRAY['low','medium','high','critical'], v_sev)
                         > array_position(ARRAY['low','medium','high','critical'], c.severity) THEN v_sev ELSE c.severity END,
      distribution_limited = c.distribution_limited OR v_sev IN ('high','critical'),
      updated_at = now()
    WHERE c.id = v_case
    RETURNING c.severity INTO v_sev;
  END IF;

  INSERT INTO vyapar_trust_safety.reports (reporter_id, case_id, object_kind, object_id, reason, evidence_text)
  VALUES (v_reporter, v_case, p_object_kind, p_object_id, p_reason, p_evidence_text)
  RETURNING id INTO v_report;

  IF v_sev IN ('high','critical') THEN
    IF p_object_kind = 'listing' THEN
      UPDATE vyapar_listings.listings SET distribution_limited = true, updated_at = now() WHERE id = p_object_id;
    ELSIF p_object_kind = 'opportunity' THEN
      UPDATE vyapar_opportunities.opportunities SET distribution_limited = true, updated_at = now() WHERE id = p_object_id;
    END IF;
  END IF;

  RETURN QUERY SELECT v_report, v_case, v_sev, v_merged;
END;
$$;

-- Gap 2. The caller's own decided outcomes — never reporter identity.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.my_outcomes()
RETURNS TABLE(case_id uuid, object_kind text, object_id uuid, action text, reason_code text,
              action_duration_days int, decided_at timestamptz, appeal_deadline timestamptz, appeal_state text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_trust_safety, pg_temp AS $$
  SELECT c.id, c.object_kind, c.object_id, c.action, c.reason_code, c.action_duration_days, c.decided_at,
         c.decided_at + interval '15 days', a.state
    FROM vyapar_trust_safety.moderation_cases c
    LEFT JOIN vyapar_trust_safety.appeals a ON a.case_id = c.id AND a.member_id = c.subject_member_id
   WHERE c.subject_member_id = current_setting('vyapar.authz_context', true)
     AND c.decided_at IS NOT NULL AND c.action IS NOT NULL AND c.action <> 'dismiss'
   ORDER BY c.decided_at DESC;
$$;

-- Gap 2. One appeal per decision within 15 days (UNIQUE(case_id, member_id)
-- already enforces "one"); a different moderation operator where staffing
-- allows, degrading to the original decider at solo scale (TR041).
CREATE OR REPLACE FUNCTION vyapar_trust_safety.file_appeal(p_case_id uuid, p_text text)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_trust_safety, pg_temp AS $$
DECLARE
  v_member text := current_setting('vyapar.authz_context', true);
  v_case vyapar_trust_safety.moderation_cases%ROWTYPE;
  v_reviewer text;
  v_id uuid;
BEGIN
  SELECT * INTO v_case FROM vyapar_trust_safety.moderation_cases WHERE id = p_case_id;
  IF NOT FOUND OR v_case.subject_member_id IS DISTINCT FROM v_member THEN RAISE EXCEPTION 'case_not_found'; END IF;
  IF v_case.decided_at IS NULL OR v_case.action IS NULL OR v_case.action IN ('dismiss','restore') THEN RAISE EXCEPTION 'not_appealable'; END IF;
  IF now() > v_case.decided_at + interval '15 days' THEN RAISE EXCEPTION 'window_closed'; END IF;

  SELECT m.id INTO v_reviewer FROM vyapar_identity.members m
   WHERE m.is_operator AND 'moderation' = ANY (m.operator_permissions) AND m.id IS DISTINCT FROM v_case.operator_id
   ORDER BY m.id LIMIT 1;
  IF v_reviewer IS NULL THEN v_reviewer := v_case.operator_id; END IF;

  INSERT INTO vyapar_trust_safety.appeals (case_id, member_id, text, reviewer_id)
  VALUES (p_case_id, v_member, p_text, v_reviewer) RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

-- Gap 3. Operator Remove/Restore on the object kinds whose own WITH CHECK
-- admits only the parties. Guarded by the moderation permission inside.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.set_object_state(p_kind text, p_object_id uuid, p_op text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_trust_safety, pg_temp AS $$
BEGIN
  IF NOT vyapar_identity.is_operator('moderation') THEN RAISE EXCEPTION 'moderation_permission_required'; END IF;
  IF p_op NOT IN ('hide','restore') THEN RAISE EXCEPTION 'invalid_op'; END IF;
  IF p_kind = 'enquiry' THEN
    UPDATE vyapar_enquiries.enquiries SET state = CASE p_op WHEN 'hide' THEN 'restricted' ELSE 'open' END, updated_at = now()
     WHERE id = p_object_id AND (p_op = 'hide' OR state = 'restricted');
  ELSIF p_kind = 'partnership' THEN
    UPDATE vyapar_enquiries.partnership_requests SET state = CASE p_op WHEN 'hide' THEN 'restricted' ELSE 'pending' END, updated_at = now()
     WHERE id = p_object_id AND (p_op = 'hide' OR state = 'restricted');
  ELSIF p_kind = 'review' THEN
    UPDATE vyapar_reviews.reviews SET state = CASE p_op WHEN 'hide' THEN 'removed' ELSE 'published' END
     WHERE id = p_object_id AND (p_op = 'hide' OR state IN ('removed','hidden','disputed'));
  END IF;
END;
$$;

-- Gap 4. An automated flag on the caller's OWN content (subject must equal
-- the caller, so this can never be used to flag someone else).
CREATE OR REPLACE FUNCTION vyapar_trust_safety.raise_auto_flag(
  p_kind text, p_object_id uuid, p_subject text, p_reason text, p_severity text
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_trust_safety, pg_temp AS $$
DECLARE v_case uuid;
BEGIN
  IF p_subject IS DISTINCT FROM current_setting('vyapar.authz_context', true) THEN RAISE EXCEPTION 'auto_flag_subject_mismatch'; END IF;
  SELECT id INTO v_case FROM vyapar_trust_safety.moderation_cases
   WHERE object_kind = p_kind AND object_id = p_object_id AND source = 'auto_flag' AND state IN ('open','in_review','escalated');
  IF v_case IS NULL THEN
    INSERT INTO vyapar_trust_safety.moderation_cases
      (object_kind, object_id, subject_member_id, source, severity, primary_reason, distribution_limited, target_due_at)
    VALUES (p_kind, p_object_id, p_subject, 'auto_flag', p_severity, p_reason, p_severity IN ('high','critical'),
            now() + vyapar_trust_safety.target_interval(p_severity))
    RETURNING id INTO v_case;
  END IF;
  RETURN v_case;
END;
$$;

GRANT EXECUTE ON FUNCTION vyapar_trust_safety.target_interval(text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.severity_for_reason(text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.file_report(text, uuid, text, text, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.my_outcomes() TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.file_appeal(uuid, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.set_object_state(text, uuid, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.raise_auto_flag(text, uuid, text, text, text) TO vyapar_app;
