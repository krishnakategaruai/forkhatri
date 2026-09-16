-- [TR030/TR031/TR032/TR051 gaps, found during Step 9 design of slice 8 by
-- reading the live RLS policies before writing code — fixed forward; 001-005
-- are applied history and are not edited.]
--
-- Gap 1 (FR51): a payment webhook arrives from the gateway with NO member
--   session. payment_orders is owner-or-commercial-operator only, so the
--   webhook could neither find the order nor record its event.
-- Gap 2 (FR30/TR030): "Commercial's own state-transition function (not the
--   webhook handler itself) moves the row to active" — and promotions'
--   WITH CHECK admits only the owner/workspace, so no system path could
--   activate, pause, complete or refund a promotion at all.
-- Gap 3 (FR30/FR54): every viewer must see "Sponsored" on a boosted card, but
--   promotions are owner/operator-only — search/feed/detail could not tell
--   which items are boosted.
-- Gap 4 (FR31): operator Reject (safety) — operators can read promotions but
--   the WITH CHECK clause blocks their write.
--
-- Fix: narrow SECURITY DEFINER functions (the 002-005 pattern). The two
-- system-path functions are additionally gated on the transaction's
-- `vyapar.service_role` (set only by the verified-webhook handler and the
-- scheduled job), as defence in depth behind the webhook signature check.
SET search_path TO pg_temp;

-- Gap 1. Record one gateway event against its order, idempotently.
-- Dedupe key is the gateway's own per-event id (SP051 refinement). Allowed
-- moves: pending->succeeded|failed, failed->succeeded (a retry that paid),
-- succeeded->refunded. Anything else — e.g. a refund event that arrives
-- before its payment event — is stored unapplied and reconciled when the
-- earlier event lands, never applied blindly against a missing state.
CREATE OR REPLACE FUNCTION vyapar_payments.record_gateway_event(
  p_gateway_order_ref text, p_payment_ref text, p_event_id text, p_event_type text, p_outcome text
) RETURNS TABLE(order_id uuid, kind text, ref_id uuid, member_id text, applied boolean, state text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_payments, pg_temp AS $$
#variable_conflict use_column
DECLARE
  o vyapar_payments.payment_orders%ROWTYPE;
  v_applied boolean := false;
  v_new text;
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') NOT IN ('payment_webhook', 'dispatcher') THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;

  IF p_gateway_order_ref IS NOT NULL THEN
    SELECT * INTO o FROM vyapar_payments.payment_orders WHERE gateway_order_ref = p_gateway_order_ref FOR UPDATE;
  END IF;
  IF o.id IS NULL AND p_payment_ref IS NOT NULL THEN
    SELECT * INTO o FROM vyapar_payments.payment_orders WHERE gateway_payment_ref = p_payment_ref ORDER BY created_at DESC LIMIT 1 FOR UPDATE;
  END IF;
  IF o.id IS NULL THEN RETURN; END IF;

  IF o.webhook_events @> jsonb_build_array(jsonb_build_object('id', p_event_id)) THEN
    RETURN QUERY SELECT o.id, o.kind, o.ref_id, o.member_id, false, o.state;
    RETURN;
  END IF;

  v_new := o.state;
  IF p_outcome = 'succeeded' AND o.state IN ('pending', 'failed') THEN
    v_new := 'succeeded'; v_applied := true;
  ELSIF p_outcome = 'failed' AND o.state = 'pending' THEN
    v_new := 'failed'; v_applied := true;
  ELSIF p_outcome = 'refunded' AND o.state = 'succeeded' THEN
    v_new := 'refunded'; v_applied := true;
  END IF;

  UPDATE vyapar_payments.payment_orders
     SET state = v_new,
         gateway_payment_ref = coalesce(gateway_payment_ref, p_payment_ref),
         webhook_events = webhook_events || jsonb_build_array(jsonb_build_object(
           'id', p_event_id, 'type', p_event_type, 'outcome', p_outcome, 'applied', v_applied, 'at', now())),
         updated_at = now()
   WHERE id = o.id;

  -- Out-of-order reconciliation: a refund stored earlier now has its payment.
  IF v_new = 'succeeded' AND o.webhook_events @> '[{"outcome": "refunded", "applied": false}]'::jsonb THEN
    UPDATE vyapar_payments.payment_orders SET state = 'refunded', updated_at = now() WHERE id = o.id;
    v_new := 'refunded';
  END IF;

  RETURN QUERY SELECT o.id, o.kind, o.ref_id, o.member_id, v_applied, v_new;
END;
$$;

-- Gap 2. Commercial's own transition function for a payment result.
CREATE OR REPLACE FUNCTION vyapar_commercial.apply_payment_result(
  p_kind text, p_ref_id uuid, p_payment_order_id uuid, p_outcome text
) RETURNS TABLE(owner_id text, from_state text, to_state text, ends_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
#variable_conflict use_column
DECLARE
  r vyapar_commercial.promotions%ROWTYPE;
  v_days int;
  v_to text;
  v_ends timestamptz;
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') NOT IN ('payment_webhook', 'dispatcher') THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;
  IF p_kind <> 'promotion' THEN RETURN; END IF;  -- entitlements/campaigns arrive with slice 9

  SELECT * INTO r FROM vyapar_commercial.promotions WHERE id = p_ref_id FOR UPDATE;
  IF NOT FOUND THEN RETURN; END IF;
  v_ends := r.ends_at;

  IF p_outcome = 'succeeded' AND r.state = 'awaiting_payment' THEN
    SELECT duration_days INTO v_days FROM vyapar_commercial.products WHERE id = r.product_id AND version = r.product_version;
    v_ends := now() + make_interval(days => coalesce(v_days, 7));
    UPDATE vyapar_commercial.promotions
       SET state = 'active', starts_at = now(), ends_at = v_ends, payment_order_id = p_payment_order_id, updated_at = now()
     WHERE id = r.id;
    v_to := 'active';
  ELSIF p_outcome = 'failed' AND r.state = 'awaiting_payment' THEN
    v_to := 'awaiting_payment';  -- stays open for the FR30 24-hour retry window
  ELSIF p_outcome = 'refunded' AND r.state IN ('rejected', 'cancelled', 'active', 'paused') THEN
    UPDATE vyapar_commercial.promotions SET state = 'refunded', updated_at = now() WHERE id = r.id;
    v_to := 'refunded';
  ELSE
    RETURN;
  END IF;

  INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
  VALUES ('promotion', r.id, r.state, v_to, 'payment_' || p_outcome);
  RETURN QUERY SELECT r.owner_id, r.state, v_to, v_ends;
END;
$$;

-- Gap 3. Which of these targets are boosted right now (ids + audience only —
-- never price, owner or payment data). NULL p_ids = every active boost.
CREATE OR REPLACE FUNCTION vyapar_commercial.active_boosts(p_kind text, p_ids uuid[])
RETURNS TABLE(target_id uuid, promotion_id uuid, audience jsonb, starts_at timestamptz)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
  SELECT p.target_id, p.id, p.audience, p.starts_at
    FROM vyapar_commercial.promotions p
   WHERE p.target_kind = p_kind
     AND (p_ids IS NULL OR p.target_id = ANY (p_ids))
     AND p.state = 'active' AND p.ends_at > now();
$$;

-- Gap 2 (scheduled). FR30 24-hour payment window, completion at end of
-- window, and Paused + pro-rata credit when the boosted item stops being
-- eligible mid-boost (listing no longer Active-Verified / opportunity no
-- longer Active). One documented cross-schema read of target state.
CREATE OR REPLACE FUNCTION vyapar_commercial.run_promotion_lifecycle()
RETURNS TABLE(promotion_id uuid, owner_id text, from_state text, to_state text, credit_paise bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
#variable_conflict use_column
DECLARE
  r record;
  v_credit bigint;
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') <> 'dispatcher' THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;

  FOR r IN SELECT p.* FROM vyapar_commercial.promotions p
            WHERE p.state = 'awaiting_payment' AND p.updated_at < now() - interval '24 hours' FOR UPDATE LOOP
    UPDATE vyapar_commercial.promotions SET state = 'cancelled', updated_at = now() WHERE id = r.id;
    INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
    VALUES ('promotion', r.id, 'awaiting_payment', 'cancelled', 'payment_window_expired');
    promotion_id := r.id; owner_id := r.owner_id; from_state := 'awaiting_payment'; to_state := 'cancelled'; credit_paise := 0;
    RETURN NEXT;
  END LOOP;

  FOR r IN SELECT p.* FROM vyapar_commercial.promotions p
            WHERE p.state = 'active' AND p.ends_at <= now() FOR UPDATE LOOP
    UPDATE vyapar_commercial.promotions SET state = 'completed', updated_at = now() WHERE id = r.id;
    INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
    VALUES ('promotion', r.id, 'active', 'completed', 'duration_ended');
    promotion_id := r.id; owner_id := r.owner_id; from_state := 'active'; to_state := 'completed'; credit_paise := 0;
    RETURN NEXT;
  END LOOP;

  FOR r IN SELECT p.* FROM vyapar_commercial.promotions p
            WHERE p.state = 'active' AND p.ends_at > now()
              AND ((p.target_kind = 'listing' AND NOT EXISTS (
                      SELECT 1 FROM vyapar_listings.listings l WHERE l.id = p.target_id AND l.state = 'active_verified'))
                OR (p.target_kind = 'opportunity' AND NOT EXISTS (
                      SELECT 1 FROM vyapar_opportunities.opportunities o WHERE o.id = p.target_id AND o.state = 'active')))
            FOR UPDATE OF p LOOP
    v_credit := floor((r.price_paise + r.tax_paise)
                * greatest(0, extract(epoch FROM r.ends_at - now()))
                / nullif(extract(epoch FROM r.ends_at - r.starts_at), 0));
    v_credit := coalesce(v_credit, 0);
    UPDATE vyapar_commercial.promotions
       SET state = 'paused', paused_at = now(), credit_paise = credit_paise + v_credit, updated_at = now()
     WHERE id = r.id;
    INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
    VALUES ('promotion', r.id, 'active', 'paused', 'target_inactive_credited');
    promotion_id := r.id; owner_id := r.owner_id; from_state := 'active'; to_state := 'paused'; credit_paise := v_credit;
    RETURN NEXT;
  END LOOP;
END;
$$;

-- Gap 4. Operator Reject (safety) — commercial permission checked inside.
CREATE OR REPLACE FUNCTION vyapar_commercial.reject_promotion(p_id uuid, p_reason text)
RETURNS TABLE(owner_id text, payment_order_id uuid, from_state text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
#variable_conflict use_column
DECLARE r vyapar_commercial.promotions%ROWTYPE;
BEGIN
  IF NOT vyapar_identity.is_operator('commercial') THEN RAISE EXCEPTION 'commercial_permission_required'; END IF;
  SELECT * INTO r FROM vyapar_commercial.promotions WHERE id = p_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'not_found'; END IF;
  IF r.state NOT IN ('awaiting_payment', 'scheduled', 'active', 'paused') THEN RAISE EXCEPTION 'invalid_transition'; END IF;
  UPDATE vyapar_commercial.promotions
     SET state = 'rejected', reject_reason = p_reason,
         ends_at = CASE WHEN r.state = 'active' THEN now() ELSE ends_at END, updated_at = now()
   WHERE id = r.id;
  INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
  VALUES ('promotion', r.id, r.state, 'rejected', 'rejected:' || p_reason);
  RETURN QUERY SELECT r.owner_id, r.payment_order_id, r.state;
END;
$$;

GRANT EXECUTE ON FUNCTION vyapar_payments.record_gateway_event(text, text, text, text, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.apply_payment_result(text, uuid, uuid, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.active_boosts(text, uuid[]) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.run_promotion_lifecycle() TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.reject_promotion(uuid, text) TO vyapar_app;
