-- ===========================================================================
-- 033 - Account deletion: vyapar_identity.erase_member(member, analytics pseudonym)
-- (docs/ParentApp/ACCOUNT-DELETION.md; modules/MOD01-vyapar/ACCOUNT-DELETION.md)
-- Additive and idempotent. One transactional, re-runnable routine that removes
-- everything Vyapar holds about one member (all 63 tables inspected). Owned by
-- vyapar_owner (bypasses RLS; no FORCE RLS anywhere), SECURITY DEFINER, and
-- guarded: it only runs for the member's own request context or the
-- dispatcher/service context the internal endpoint sets.
-- Other people's records that point at the member are re-pointed to a one-way
-- tombstone member ('del_<hash>', display name 'Deleted member', no contact).
-- Returns jsonb: {status, deleted{kind:n}, retained[], file_urls[], tombstone}.
-- ===========================================================================
CREATE OR REPLACE FUNCTION vyapar_identity.erase_member(p_member_id text, p_pseudo text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'vyapar_identity', 'pg_temp'
AS $fn$
DECLARE
  v_tomb text := 'del_' || left(encode(sha256(convert_to(p_member_id, 'utf8')), 'hex'), 16);
  v_del jsonb := '{}'::jsonb;
  v_ret jsonb := '[]'::jsonb;
  v_files text[] := '{}';
  v_n bigint;
  v_total bigint := 0;
  v_has_member boolean;
  v_listings uuid[];
  v_opps uuid[];
BEGIN
  IF p_member_id IS NULL OR p_member_id = '' OR p_member_id LIKE 'del\_%' THEN
    RAISE EXCEPTION 'invalid_member' USING ERRCODE = '22023';
  END IF;
  IF coalesce(current_setting('vyapar.authz_context', true), '') <> p_member_id
     AND coalesce(current_setting('vyapar.service_role', true), '') <> 'dispatcher' THEN
    RAISE EXCEPTION 'not_authorised' USING ERRCODE = '42501';
  END IF;
  IF EXISTS (SELECT 1 FROM vyapar_identity.members WHERE id = p_member_id AND is_operator) THEN
    RAISE EXCEPTION 'operator_role_must_be_removed' USING ERRCODE = '55000';
  END IF;
  SELECT EXISTS (SELECT 1 FROM vyapar_identity.members WHERE id = p_member_id) INTO v_has_member;

  SELECT coalesce(array_agg(id), '{}') INTO v_listings FROM vyapar_listings.listings WHERE owner_id = p_member_id;
  SELECT coalesce(array_agg(id), '{}') INTO v_opps FROM vyapar_opportunities.opportunities WHERE poster_id = p_member_id;

  -- ---- uploaded files referenced by rows about to go -----------------------
  SELECT coalesce(array_agg(DISTINCT x.m[1]), '{}') INTO v_files FROM (
    SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') AS m FROM vyapar_identity.members t WHERE id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_listings.listings t WHERE owner_id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_listings.verification_records t WHERE member_id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_listings.council_credentials t WHERE member_id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_opportunities.opportunities t WHERE poster_id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_enquiries.enquiry_messages t WHERE sender_id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_enquiries.enquiries t WHERE sender_id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_trust_safety.reports t WHERE reporter_id = p_member_id
    UNION ALL SELECT regexp_matches(row_to_json(t)::text, '(/uploads/[A-Za-z0-9_.-]+)', 'g') FROM vyapar_trust_safety.appeals t WHERE member_id = p_member_id
  ) x;

  -- ---- tombstone member (so other people's records keep resolving) ---------
  INSERT INTO vyapar_identity.members (id, display_name, anonymized, deleted_at)
  VALUES (v_tomb, 'Deleted member', true, now()) ON CONFLICT (id) DO NOTHING;

  -- ---- Learned taste, privacy, consent, preferences ------------------------
  DELETE FROM vyapar_privacy.member_taste WHERE member_id = p_member_id;               GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('taste_profile', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_privacy.derived_preferences WHERE member_id = p_member_id;        GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('derived_preferences', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_privacy.privacy_settings WHERE member_id = p_member_id;           GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('privacy_settings', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_privacy.acceptances WHERE member_id = p_member_id;                GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('consent_records', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_privacy.data_requests WHERE member_id = p_member_id;              GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('privacy_requests', v_n); v_total := v_total + v_n;

  -- ---- Analytics, impressions, platform bookkeeping ------------------------
  IF p_pseudo IS NOT NULL THEN
    DELETE FROM vyapar_analytics.analytics_events WHERE member_pseudo = p_pseudo;      GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('analytics_events', v_n); v_total := v_total + v_n;
  END IF;
  DELETE FROM vyapar_commercial.impressions WHERE member_id = p_member_id OR target_id = ANY (v_listings) OR target_id = ANY (v_opps); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('impressions', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_platform.idempotency_key WHERE member_id = p_member_id;           GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('idempotency_keys', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key LIKE '%' || p_member_id || '%'; GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('rate_limit_counters', v_n); v_total := v_total + v_n;

  -- ---- Integrations: tokens, webhooks, notifications, AI log, referrals ----
  DELETE FROM vyapar_integration.access_tokens WHERE member_id = p_member_id;          GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('access_tokens', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_integration.webhook_subscriptions WHERE member_id = p_member_id;  GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('webhook_subscriptions', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_integration.webhook_deliveries WHERE member_id = p_member_id;     GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('webhook_deliveries', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_integration.notifications WHERE member_id = p_member_id;          GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('notifications', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_integration.ai_events WHERE member_id = p_member_id;              GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('ai_events', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_integration.counsel_referrals WHERE member_id = p_member_id;      GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('counsel_referrals', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_integration.dead_letters WHERE payload::text LIKE '%' || p_member_id || '%'; GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('dead_letters', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_listings.outbox_event WHERE payload::text LIKE '%' || p_member_id || '%';       GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;
  DELETE FROM vyapar_opportunities.outbox_event WHERE payload::text LIKE '%' || p_member_id || '%';  GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;
  DELETE FROM vyapar_enquiries.outbox_event WHERE payload::text LIKE '%' || p_member_id || '%';      GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;
  DELETE FROM vyapar_reviews.outbox_event WHERE payload::text LIKE '%' || p_member_id || '%';        GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;
  DELETE FROM vyapar_commercial.outbox_event WHERE payload::text LIKE '%' || p_member_id || '%';     GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;

  -- ---- Reviews (written by, about, or for the member's listings) -----------
  DELETE FROM vyapar_reviews.reviews WHERE author_id = p_member_id OR subject_member_id = p_member_id OR subject_listing_id = ANY (v_listings); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('reviews', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_reviews.review_disputes WHERE disputer_id = p_member_id;          GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('review_disputes', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_reviews.review_invites WHERE member_id = p_member_id OR subject_member_id = p_member_id OR subject_listing_id = ANY (v_listings); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('review_invites', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_reviews.paid_on_time_asks WHERE payer_id = p_member_id OR payee_id = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('paid_on_time_asks', v_n); v_total := v_total + v_n;

  -- ---- Enquiries, quotes/proposals, messages, partnerships, calls ----------
  DELETE FROM vyapar_enquiries.enquiry_messages WHERE sender_id = p_member_id;         GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('messages', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_enquiries.enquiries WHERE provider_id = p_member_id OR listing_id = ANY (v_listings) OR opportunity_id = ANY (v_opps);
  GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('enquiries_received', v_n); v_total := v_total + v_n;
  -- enquiries/proposals the member sent to other people: the other party keeps the thread, shown as Deleted member, content removed
  UPDATE vyapar_enquiries.enquiries SET sender_id = v_tomb, profile_snapshot = NULL, screening_answers = '{}'::jsonb, milestones = '[]'::jsonb, state_reason = NULL
   WHERE sender_id = p_member_id;                                                      GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('enquiries_sent_detached', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_enquiries.partnership_requests WHERE sender_id = p_member_id OR recipient_id = p_member_id OR sender_listing_id = ANY (v_listings) OR recipient_listing_id = ANY (v_listings);
  GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('partnership_requests', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_enquiries.blocks WHERE blocker_id = p_member_id OR blocked_id = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('blocks', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_enquiries.contact_attempts WHERE caller_id = p_member_id OR callee_id = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('contact_attempts', v_n); v_total := v_total + v_n;

  -- ---- Contracts: the other party keeps theirs, shown as Deleted member ----
  UPDATE vyapar_contracts.contracts SET
      client_member_id = CASE WHEN client_member_id = p_member_id THEN v_tomb ELSE client_member_id END,
      provider_member_id = CASE WHEN provider_member_id = p_member_id THEN v_tomb ELSE provider_member_id END,
      cancelled_by = CASE WHEN cancelled_by = p_member_id THEN v_tomb ELSE cancelled_by END,
      provider_listing_id = CASE WHEN provider_listing_id = ANY (v_listings) THEN NULL ELSE provider_listing_id END,
      cancelled_at = CASE WHEN state IN ('completed','cancelled') THEN cancelled_at ELSE now() END,
      cancel_reason = CASE WHEN state IN ('completed','cancelled') THEN cancel_reason ELSE 'member_deleted' END,
      state = CASE WHEN state IN ('completed','cancelled') THEN state ELSE 'cancelled' END,
      updated_at = now()
   WHERE client_member_id = p_member_id OR provider_member_id = p_member_id;           GET DIAGNOSTICS v_n = ROW_COUNT;
  v_del := v_del || jsonb_build_object('contracts_detached', v_n); v_total := v_total + v_n;
  UPDATE vyapar_contracts.contract_events SET actor_member_id = v_tomb, data = '{}'::jsonb WHERE actor_member_id = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;
  UPDATE vyapar_contracts.contract_disputes SET opened_by = v_tomb, notes = NULL WHERE opened_by = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;
  UPDATE vyapar_contracts.contract_disputes SET resolved_by = v_tomb WHERE resolved_by = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;

  -- ---- Commercial: campaigns, boosts, entitlements, workspace --------------
  DELETE FROM vyapar_commercial.commercial_order_history WHERE order_id IN (
      SELECT id FROM vyapar_commercial.campaigns WHERE owner_id = p_member_id
      UNION SELECT id FROM vyapar_commercial.promotions WHERE owner_id = p_member_id
      UNION SELECT id FROM vyapar_commercial.entitlements WHERE owner_id = p_member_id);
  DELETE FROM vyapar_commercial.promotions WHERE owner_id = p_member_id OR campaign_id IN (SELECT id FROM vyapar_commercial.campaigns WHERE owner_id = p_member_id);
  GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('boosts', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_commercial.campaigns WHERE owner_id = p_member_id OR listing_id = ANY (v_listings::text[]); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('campaigns', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_commercial.entitlements WHERE owner_id = p_member_id OR listing_id = ANY (v_listings::text[]); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('entitlements', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_commercial.workspace_members WHERE member_id = p_member_id OR listing_id = ANY (v_listings::text[]); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('workspace_members', v_n); v_total := v_total + v_n;
  UPDATE vyapar_commercial.workspace_members SET invited_by = v_tomb WHERE invited_by = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;

  -- ---- Payment orders: RETAINED with tombstone (legal retention) -----------
  UPDATE vyapar_payments.payment_orders SET member_id = v_tomb, webhook_events = '[]'::jsonb, updated_at = now() WHERE member_id = p_member_id;
  GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n > 0 THEN v_ret := v_ret || jsonb_build_array(jsonb_build_object('kind', 'payment_orders', 'count', v_n, 'reason', 'Payment and tax records are kept for the legal retention period; only a one-way id, amount and date remain.')); END IF;

  -- ---- Trust & safety: RETAINED minimal, pseudonymised ---------------------
  UPDATE vyapar_trust_safety.reports SET reporter_id = v_tomb, evidence_text = NULL, evidence_urls = '{}' WHERE reporter_id = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n > 0 THEN v_ret := v_ret || jsonb_build_array(jsonb_build_object('kind', 'reports_filed', 'count', v_n, 'reason', 'Kept without your name or text so reported people stay protected.')); END IF;
  UPDATE vyapar_trust_safety.appeals SET member_id = v_tomb, text = '', evidence_urls = '{}' WHERE member_id = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT;
  UPDATE vyapar_trust_safety.moderation_cases SET subject_member_id = v_tomb WHERE subject_member_id = p_member_id; GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n > 0 THEN v_ret := v_ret || jsonb_build_array(jsonb_build_object('kind', 'safety_cases', 'count', v_n, 'reason', 'A record that a report or ban happened is kept (one-way id only) so a removed member cannot simply return and harm others.')); END IF;
  UPDATE vyapar_trust_safety.moderation_cases SET operator_id = v_tomb WHERE operator_id = p_member_id;
  UPDATE vyapar_trust_safety.appeals SET reviewer_id = v_tomb WHERE reviewer_id = p_member_id;

  -- ---- Audit log: RETAINED, id replaced, free text removed -----------------
  UPDATE vyapar_integration.audit_events SET
         details = '{}'::jsonb,
         actor_id = CASE WHEN actor_id = p_member_id THEN v_tomb ELSE actor_id END,
         object_id = CASE WHEN object_id = p_member_id THEN v_tomb ELSE object_id END
   WHERE actor_id = p_member_id OR object_id = p_member_id;                            GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n > 0 THEN v_ret := v_ret || jsonb_build_array(jsonb_build_object('kind', 'audit_log', 'count', v_n, 'reason', 'Security logs are kept for the minimum legal period with your id replaced by a one-way id.')); END IF;

  -- ---- Verification, credentials, listings (cascade children) --------------
  DELETE FROM vyapar_listings.otp_challenges WHERE member_id = p_member_id OR listing_id = ANY (v_listings); GET DIAGNOSTICS v_n = ROW_COUNT; v_total := v_total + v_n;
  DELETE FROM vyapar_listings.council_credentials WHERE member_id = p_member_id OR listing_id = ANY (v_listings); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('credentials', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_listings.verification_records WHERE member_id = p_member_id OR listing_id = ANY (v_listings); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('verification_records', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_listings.member_listing WHERE member_id = p_member_id OR listing_id = ANY (v_listings); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('saved_viewed_listings', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_listings.listing_contacts WHERE listing_id = ANY (v_listings);   GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('listing_contacts', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_listings.listing_packages WHERE listing_id = ANY (v_listings);   GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('listing_packages', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_listings.listings WHERE owner_id = p_member_id;                  GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('profiles_and_listings', v_n); v_total := v_total + v_n;

  -- ---- Opportunities ------------------------------------------------------
  DELETE FROM vyapar_opportunities.member_opportunity WHERE member_id = p_member_id OR opportunity_id = ANY (v_opps); GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('saved_hidden_opportunities', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_opportunities.saved_searches WHERE member_id = p_member_id;      GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('saved_searches', v_n); v_total := v_total + v_n;
  DELETE FROM vyapar_opportunities.opportunities WHERE poster_id = p_member_id;       GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('opportunities', v_n); v_total := v_total + v_n;

  -- ---- The Vyapar member mirror itself --------------------------------------
  DELETE FROM vyapar_identity.members WHERE id = p_member_id;                         GET DIAGNOSTICS v_n = ROW_COUNT; v_del := v_del || jsonb_build_object('member_record', v_n); v_total := v_total + v_n;

  -- drop zero counts so the answer lists only what existed
  SELECT coalesce(jsonb_object_agg(e.k, e.v), '{}'::jsonb) INTO v_del FROM jsonb_each(v_del) AS e(k, v) WHERE e.v::text <> '0';

  IF v_total = 0 AND NOT v_has_member THEN
    RETURN jsonb_build_object('status', 'nothing_to_delete', 'deleted', '{}'::jsonb, 'retained', '[]'::jsonb, 'file_urls', '[]'::jsonb, 'tombstone', v_tomb);
  END IF;

  -- one-line deletion receipt (tombstone id, date, counts) - no personal data
  INSERT INTO vyapar_privacy.data_requests (member_id, kind, state, detail, retained_categories, completed_at)
  VALUES (v_tomb, 'delete', 'completed', v_del::text, ARRAY(SELECT x->>'kind' FROM jsonb_array_elements(v_ret) x), now());
  RETURN jsonb_build_object('status', 'done', 'deleted', v_del, 'retained', v_ret, 'file_urls', to_jsonb(v_files), 'tombstone', v_tomb);
END
$fn$;

REVOKE ALL ON FUNCTION vyapar_identity.erase_member(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_identity.erase_member(text, text) TO vyapar_app;
