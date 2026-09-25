-- [Critique agent finding, fixed here] FR41 explicitly names optional
-- evidence as part of an appeal. The `appeals` table already carries an
-- `evidence_urls text[]` column (migration 001) but `file_appeal()` never
-- accepted or stored anything into it — the column existed, unused, since
-- the very first migration. Fix-forward only (001/004 stay as applied);
-- CREATE OR REPLACE on the same function signature-compatible... actually
-- the signature changes (new optional param), so this replaces it with a
-- default so every existing caller (none yet, this was never wired to any
-- UI) keeps working unchanged.
-- Traces to: FR41, TR041

-- PostgreSQL resolves overloads by parameter TYPES, not by name — adding a
-- third parameter creates a second, separate function rather than
-- replacing the old one. Drop the old 2-arg signature explicitly so
-- exactly one `file_appeal` exists going forward (the router's own call
-- site is updated in the same change to always pass three arguments).
DROP FUNCTION IF EXISTS vyapar_trust_safety.file_appeal(uuid, text);

CREATE OR REPLACE FUNCTION vyapar_trust_safety.file_appeal(p_case_id uuid, p_text text, p_evidence_urls text[] DEFAULT '{}')
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

  INSERT INTO vyapar_trust_safety.appeals (case_id, member_id, text, evidence_urls, reviewer_id)
  VALUES (p_case_id, v_member, p_text, COALESCE(p_evidence_urls, '{}'), v_reviewer) RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

GRANT EXECUTE ON FUNCTION vyapar_trust_safety.file_appeal(uuid, text, text[]) TO vyapar_app;
