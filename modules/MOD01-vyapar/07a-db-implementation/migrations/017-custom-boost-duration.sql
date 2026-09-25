-- [Custom boost duration — product owner, 2026-09-21, looking at the boost
-- screen: "no custom duration?"] Boosts were sold only as 3, 7 or 14-day
-- packs. A member can now pick any length from 1 to 30 days.
--
-- Pricing stays anchored to the pack catalogue (no second price list to keep
-- in sync): a custom length is billed at the per-day rate of the longest pack
-- that fits inside it (the shortest pack's rate below 3 days), so 7 custom
-- days cost exactly the 7-day pack and a longer boost is never dearer per day.
-- The promotion row still references that pack (product_id/version, so the
-- FK and every historical report keep working) and records its own day count
-- here. NULL means "use the product's duration", so existing rows are
-- unchanged.
-- Traces to: FR30, FR31, TR030, TR031

ALTER TABLE vyapar_commercial.promotions
  ADD COLUMN IF NOT EXISTS duration_days int CHECK (duration_days BETWEEN 1 AND 30);

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
    -- A custom-length boost carries its own day count; a pack uses the product's.
    v_ends := now() + make_interval(days => coalesce(r.duration_days, v_days, 7));
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
