-- [IMP-B — owner, 2026-09-30: notifications "are rendered in English for
-- everyone"] Notifications written by the SQL functions below received the
-- title/body already rendered in en/hi/te (`p_texts`) but kept only the one
-- language chosen at write time. They now also keep the full `p_texts` under
-- params._texts (and, when the caller sends one, the `_i18n` template spec
-- inside it), so the read path renders each notification in the reader's
-- language at read time (app/services/notifications.py, render_notification).
-- Each function below is its current definition with ONLY the params value
-- changed to `<same object> || jsonb_build_object('_texts', p_texts)`.
-- Existing rows are backfilled by scripts/backfill_notification_i18n.py.
-- Traces to: FR21, product-owner i18n rule

-- notify_interaction_party
CREATE OR REPLACE FUNCTION vyapar_integration.notify_interaction_party(p_interaction_kind text, p_interaction_id uuid, p_recipient text, p_template text, p_texts jsonb, p_link text, p_idem text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_integration', 'pg_temp'
AS $function$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  v_ok boolean := false;
  v_lang text;
  v_id uuid;
BEGIN
  IF p_interaction_kind = 'enquiry' THEN
    SELECT true INTO v_ok FROM vyapar_enquiries.enquiries e
     WHERE e.id = p_interaction_id AND v_caller IN (e.sender_id, e.provider_id) AND p_recipient IN (e.sender_id, e.provider_id);
  ELSIF p_interaction_kind = 'partnership' THEN
    SELECT true INTO v_ok FROM vyapar_enquiries.partnership_requests p
     WHERE p.id = p_interaction_id AND v_caller IN (p.sender_id, p.recipient_id) AND p_recipient IN (p.sender_id, p.recipient_id);
  END IF;
  IF NOT coalesce(v_ok, false) THEN RAISE EXCEPTION 'not_a_party'; END IF;
  IF p_recipient <> v_caller AND vyapar_enquiries.is_blocked(p_recipient, v_caller) THEN RETURN false; END IF;

  SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = p_recipient;
  v_lang := coalesce(v_lang, 'en');
  INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
  VALUES (p_recipient, p_template, p_template,
          coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
          coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
          p_link, (jsonb_build_object('interaction_kind', p_interaction_kind, 'interaction_id', p_interaction_id) || jsonb_build_object('_texts', p_texts)), p_idem)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$function$;

-- notify_workspace_member
CREATE OR REPLACE FUNCTION vyapar_commercial.notify_workspace_member(p_listing_id uuid, p_recipient text, p_template text, p_texts jsonb, p_link text, p_idem text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_commercial', 'pg_temp'
AS $function$
DECLARE
  v_role text;
  v_lang text;
  v_id uuid;
BEGIN
  SELECT w.role INTO v_role FROM vyapar_commercial.workspace_context(p_listing_id) w;
  IF coalesce(v_role, 'none') NOT IN ('owner', 'admin') THEN RAISE EXCEPTION 'role_not_allowed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM vyapar_commercial.workspace_members wm
                  WHERE wm.listing_id = p_listing_id::text AND wm.member_id = p_recipient) THEN
    RAISE EXCEPTION 'not_a_workspace_member';
  END IF;
  SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = p_recipient;
  v_lang := coalesce(v_lang, 'en');
  INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
  VALUES (p_recipient, p_template, p_template,
          coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
          coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
          p_link, (jsonb_build_object('listing_id', p_listing_id) || jsonb_build_object('_texts', p_texts)), p_idem)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$function$;

-- apply_seeker_charge_reports
CREATE OR REPLACE FUNCTION vyapar_trust_safety.apply_seeker_charge_reports(p_opportunity_id uuid, p_threshold integer, p_texts jsonb)
 RETURNS TABLE(reporters integer, paused boolean, case_id uuid)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_trust_safety', 'pg_temp'
AS $function$
DECLARE
  v_case uuid;
  v_poster text;
  v_state text;
  v_title text;
  v_n int := 0;
  v_paused boolean := false;
  v_lang text;
BEGIN
  SELECT c.id INTO v_case FROM vyapar_trust_safety.moderation_cases c
   WHERE c.object_kind = 'opportunity' AND c.object_id = p_opportunity_id AND c.state IN ('open','in_review','escalated')
   ORDER BY c.created_at LIMIT 1;
  IF v_case IS NULL THEN RETURN QUERY SELECT 0, false, NULL::uuid; RETURN; END IF;

  SELECT count(DISTINCT r.reporter_id)::int INTO v_n FROM vyapar_trust_safety.reports r
   WHERE r.case_id = v_case AND r.reason = 'asked_for_money';

  IF v_n >= p_threshold THEN
    SELECT o.poster_id, o.state, o.title INTO v_poster, v_state, v_title
      FROM vyapar_opportunities.opportunities o WHERE o.id = p_opportunity_id FOR UPDATE;
    IF v_state IN ('active','stale') THEN
      UPDATE vyapar_opportunities.opportunities
         SET state = 'paused', state_reason = 'seeker_charge_reports', distribution_limited = true, updated_at = now()
       WHERE id = p_opportunity_id;
      v_paused := true;
      SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = v_poster;
      v_lang := coalesce(v_lang, 'en');
      INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
      VALUES (v_poster, 'opportunityPausedSeekerCharge', 'opportunityPausedSeekerCharge',
              coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
              coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
              '/opportunities/' || p_opportunity_id::text,
              (jsonb_build_object('opportunity_id', p_opportunity_id, 'case_id', v_case) || jsonb_build_object('_texts', p_texts)),
              'seeker_charge_paused:' || p_opportunity_id::text)
      ON CONFLICT (idempotency_key) DO NOTHING;
    END IF;
    UPDATE vyapar_trust_safety.moderation_cases c
       SET severity = CASE WHEN c.severity = 'critical' THEN c.severity ELSE 'high' END,
           distribution_limited = true,
           primary_reason = 'asked_for_money',
           target_due_at = LEAST(c.target_due_at, now() + vyapar_trust_safety.target_interval('high')),
           updated_at = now()
     WHERE c.id = v_case;
  END IF;
  RETURN QUERY SELECT v_n, v_paused, v_case;
END;
$function$;

-- notify_party
CREATE OR REPLACE FUNCTION vyapar_contracts.notify_party(p_contract_id uuid, p_recipient text, p_template text, p_texts jsonb, p_link text, p_idem text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_contracts', 'pg_temp'
AS $function$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  c vyapar_contracts.contracts%ROWTYPE;
  v_lang text;
  v_id uuid;
BEGIN
  SELECT * INTO c FROM vyapar_contracts.contracts WHERE id = p_contract_id;
  IF c.id IS NULL OR p_recipient NOT IN (c.client_member_id, c.provider_member_id) THEN RAISE EXCEPTION 'not_a_party'; END IF;
  IF v_caller NOT IN (c.client_member_id, c.provider_member_id) AND NOT vyapar_identity.is_operator('moderation') THEN
    RAISE EXCEPTION 'not_a_party';
  END IF;
  IF p_recipient <> v_caller AND vyapar_enquiries.is_blocked(p_recipient, v_caller) THEN RETURN false; END IF;

  SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = p_recipient;
  v_lang := coalesce(v_lang, 'en');
  INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
  VALUES (p_recipient, p_template, p_template,
          coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
          coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
          p_link, (jsonb_build_object('contract_id', p_contract_id) || jsonb_build_object('_texts', p_texts)), p_idem)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$function$;

-- notify_precall
CREATE OR REPLACE FUNCTION vyapar_integration.notify_precall(p_attempt_id uuid, p_texts jsonb)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_integration', 'pg_temp'
AS $function$
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
          (jsonb_build_object('opportunity_id', a.opportunity_id, 'attempt_id', a.id, 'channel', a.channel,
                             'enquiry_id', a.enquiry_id) || jsonb_build_object('_texts', p_texts)),
          'precall:' || a.id::text)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$function$;
