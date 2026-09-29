-- [IMP-B — Pre-accept calling, critique L1, owner-approved 2026-09-28]
-- "Let people call me before I accept": a per-post switch so a job seeker
-- can tap Call / WhatsApp on the opportunity itself (Apna's "Call HR",
-- WorkIndia's "Click to call HR"), with the poster's call hours, days, daily
-- cap and matching_only rule from migration 019 applying to every caller.
-- Additive only.
--
-- 1. opportunities.allow_precall — off by default; only meaningful for
--    employment and local_service (a CHECK, so no code path can store it on
--    another type).
-- 2. contact_attempts gains opportunity_id; enquiry_id becomes nullable so a
--    tap is recorded even when no application could be created (a caller
--    without a profile still counts toward the poster's cap). One of the two
--    must be set.
-- 3. enquiries.applied_via gains 'call' (values only appended): the
--    lightweight application auto-created on a caller's first tap.
-- 4. notify_precall(attempt_id, texts): the caller's session cannot insert
--    the poster's notification or read their language; this narrow SECURITY
--    DEFINER function does exactly that for an attempt the CALLER recorded on
--    a post that allows pre-accept calls, and stays silent when the poster
--    has blocked the caller.
-- Traces to: FR02, FR22, FR24, TR002, TR024, critique L1

-- 1 -------------------------------------------------------------------------
ALTER TABLE vyapar_opportunities.opportunities
  ADD COLUMN IF NOT EXISTS allow_precall boolean NOT NULL DEFAULT false;
ALTER TABLE vyapar_opportunities.opportunities DROP CONSTRAINT IF EXISTS opportunities_allow_precall_type_check;
ALTER TABLE vyapar_opportunities.opportunities ADD CONSTRAINT opportunities_allow_precall_type_check
  CHECK (NOT allow_precall OR type IN ('employment','local_service'));
COMMENT ON COLUMN vyapar_opportunities.opportunities.allow_precall IS
  '[IMP-B/L1] Poster lets people call or WhatsApp before accepting an application. Employment and local_service only.';

-- 2 -------------------------------------------------------------------------
ALTER TABLE vyapar_enquiries.contact_attempts ADD COLUMN IF NOT EXISTS opportunity_id uuid;  -- no cross-schema FK
ALTER TABLE vyapar_enquiries.contact_attempts ALTER COLUMN enquiry_id DROP NOT NULL;
ALTER TABLE vyapar_enquiries.contact_attempts DROP CONSTRAINT IF EXISTS contact_attempts_target_check;
ALTER TABLE vyapar_enquiries.contact_attempts ADD CONSTRAINT contact_attempts_target_check
  CHECK (enquiry_id IS NOT NULL OR opportunity_id IS NOT NULL);
CREATE INDEX IF NOT EXISTS contact_attempts_opportunity_idx
  ON vyapar_enquiries.contact_attempts (opportunity_id, caller_id, at DESC) WHERE opportunity_id IS NOT NULL;

-- 3 -------------------------------------------------------------------------
ALTER TABLE vyapar_enquiries.enquiries DROP CONSTRAINT IF EXISTS enquiries_applied_via_check;
ALTER TABLE vyapar_enquiries.enquiries ADD CONSTRAINT enquiries_applied_via_check
  CHECK (applied_via IN ('form','one_tap','voice','agent','call'));

-- 4 -------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_integration.notify_precall(p_attempt_id uuid, p_texts jsonb)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_integration, pg_temp AS $$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  a vyapar_enquiries.contact_attempts%ROWTYPE;
  v_ok boolean;
  v_lang text;
  v_id uuid;
BEGIN
  SELECT * INTO a FROM vyapar_enquiries.contact_attempts WHERE id = p_attempt_id;
  IF NOT FOUND OR a.caller_id IS DISTINCT FROM v_caller OR a.opportunity_id IS NULL THEN
    RAISE EXCEPTION 'not_your_attempt';
  END IF;
  SELECT true INTO v_ok FROM vyapar_opportunities.opportunities o
   WHERE o.id = a.opportunity_id AND o.poster_id = a.callee_id AND o.allow_precall;
  IF NOT coalesce(v_ok, false) THEN RAISE EXCEPTION 'precall_off'; END IF;
  IF vyapar_enquiries.is_blocked(a.callee_id, v_caller) THEN RETURN false; END IF;

  SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = a.callee_id;
  v_lang := coalesce(v_lang, 'en');
  INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
  VALUES (a.callee_id, 'precallContact', 'precallContact',
          coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
          coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
          '/opportunities/' || a.opportunity_id::text,
          jsonb_build_object('opportunity_id', a.opportunity_id, 'attempt_id', a.id, 'channel', a.channel,
                             'enquiry_id', a.enquiry_id),
          'precall:' || a.id::text)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$$;
REVOKE ALL ON FUNCTION vyapar_integration.notify_precall(uuid, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_integration.notify_precall(uuid, jsonb) TO vyapar_app;
