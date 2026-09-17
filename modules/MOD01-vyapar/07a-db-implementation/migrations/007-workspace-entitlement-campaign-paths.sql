-- [TR033/TR034/TR035/TR049 gaps, found during Step 9 design of slice 9 by
-- reading the live RLS policies before writing code — fixed forward; 001-006
-- are applied history and are not edited.]
--
-- Gap 1 (FR33/TR033 "single chokepoint"): `is_workspace_collaborator()` (001)
--   checks only `workspace_members.state='active'`. Nothing tied collaborator
--   authority to the entitlement being active, so a Paused plan (renewal
--   failure) would have kept granting workspace capabilities. Fix: the helper
--   now also requires an active entitlement for that listing — because RLS
--   policies already call this one helper, the chokepoint is enforced in the
--   database for every surface at once, exactly as SP033 demands, with no
--   per-feature check able to drift.
-- Gap 2 (FR34): a workspace role grants nothing today. `listings`,
--   `opportunities`, `enquiries` and `enquiry_messages` policies admit only
--   the owner / the parties, so an Admin or Operator could not act for the
--   business at all. Fix: those four policies now also admit an active
--   collaborator of the listing (via the Gap-1 helper, so entitlement state
--   gates it too). The Admin-vs-Operator split (no billing, no team
--   management for Operators) is a route-layer rule in `app/authz.py` — RLS
--   cannot express it, and FR34 defines it in terms of actions, not rows.
-- Gap 3 (FR34): invite-by-phone. `workspace_members` is self/inviter-visible,
--   so an invitee whose row has no `member_id` yet (not a member when
--   invited) can never see or accept it; and resolving a phone to a member id
--   is the Identity Bridge's job, not a cross-schema query.
-- Gap 4 (FR33/FR35/FR54): entitlement renewal, the 7-day grace, the 3-day
--   reminder that GATES a renewal charge, and campaign activation all run
--   without a member session and are blocked by the same WITH CHECK clauses.
SET search_path TO pg_temp;

-- Gap 1 — the one capability chokepoint.
CREATE OR REPLACE FUNCTION vyapar_commercial.is_workspace_collaborator(p_listing_id text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_commercial, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM vyapar_commercial.workspace_members wm
     WHERE wm.listing_id = p_listing_id
       AND wm.member_id = current_setting('vyapar.authz_context', true)
       AND wm.state = 'active'
       AND EXISTS (SELECT 1 FROM vyapar_commercial.entitlements e
                    WHERE e.listing_id = p_listing_id AND e.state = 'active')
  );
$$;
COMMENT ON FUNCTION vyapar_commercial.is_workspace_collaborator(text) IS
  '[TR033/SP033] The single capability chokepoint: active workspace role AND active entitlement. Every RLS policy that admits a collaborator calls this one function, so a Paused plan locks capabilities everywhere at once.';

-- Gap 2 — let an active collaborator act for the business.
DROP POLICY IF EXISTS listings_visibility ON vyapar_listings.listings;
CREATE POLICY listings_visibility ON vyapar_listings.listings
  USING (state IN ('active_unverified','active_verified')
    OR owner_id = current_setting('vyapar.authz_context', true)
    OR vyapar_commercial.is_workspace_collaborator(id::text)
    OR vyapar_identity.is_operator('content'))
  WITH CHECK (owner_id = current_setting('vyapar.authz_context', true)
    OR vyapar_commercial.is_workspace_collaborator(id::text)
    OR vyapar_identity.is_operator('content'));

DROP POLICY IF EXISTS opportunities_visibility ON vyapar_opportunities.opportunities;
CREATE POLICY opportunities_visibility ON vyapar_opportunities.opportunities
  USING (state IN ('active','paused','stale')
    OR poster_id = current_setting('vyapar.authz_context', true)
    OR (listing_id IS NOT NULL AND vyapar_commercial.is_workspace_collaborator(listing_id::text))
    OR vyapar_identity.is_operator('content'))
  WITH CHECK (poster_id = current_setting('vyapar.authz_context', true)
    OR (listing_id IS NOT NULL AND vyapar_commercial.is_workspace_collaborator(listing_id::text))
    OR vyapar_identity.is_operator('content'));

DROP POLICY IF EXISTS enquiries_participants ON vyapar_enquiries.enquiries;
CREATE POLICY enquiries_participants ON vyapar_enquiries.enquiries
  USING (sender_id = current_setting('vyapar.authz_context', true)
    OR provider_id = current_setting('vyapar.authz_context', true)
    OR (listing_id IS NOT NULL AND vyapar_commercial.is_workspace_collaborator(listing_id::text))
    OR vyapar_identity.is_operator('moderation'))
  WITH CHECK (sender_id = current_setting('vyapar.authz_context', true)
    OR provider_id = current_setting('vyapar.authz_context', true)
    OR (listing_id IS NOT NULL AND vyapar_commercial.is_workspace_collaborator(listing_id::text)));

DROP POLICY IF EXISTS enquiry_messages_participants ON vyapar_enquiries.enquiry_messages;
CREATE POLICY enquiry_messages_participants ON vyapar_enquiries.enquiry_messages
  USING (EXISTS (SELECT 1 FROM vyapar_enquiries.enquiries e WHERE e.id = enquiry_messages.enquiry_id
                 AND (e.sender_id = current_setting('vyapar.authz_context', true)
                   OR e.provider_id = current_setting('vyapar.authz_context', true)
                   OR (e.listing_id IS NOT NULL AND vyapar_commercial.is_workspace_collaborator(e.listing_id::text))))
         OR vyapar_identity.is_operator('moderation'));

-- The Authorization Engine's own read: role + entitlement state in one call.
CREATE OR REPLACE FUNCTION vyapar_commercial.workspace_context(p_listing_id uuid)
RETURNS TABLE(role text, entitlement_state text, entitlement_active boolean, owner_id text, entitlement_id uuid,
              renews_at timestamptz, grace_until timestamptz, cancel_at_period_end boolean,
              product_id text, product_version int, listing_name text)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  v_owner text;
  v_name text;
  v_role text;
  e vyapar_commercial.entitlements%ROWTYPE;
BEGIN
  SELECT l.owner_id, l.name INTO v_owner, v_name FROM vyapar_listings.listings l WHERE l.id = p_listing_id;
  IF v_owner IS NULL THEN RETURN; END IF;
  IF v_owner = v_caller THEN
    v_role := 'owner';
  ELSE
    SELECT wm.role INTO v_role FROM vyapar_commercial.workspace_members wm
     WHERE wm.listing_id = p_listing_id::text AND wm.member_id = v_caller AND wm.state = 'active' LIMIT 1;
    v_role := coalesce(v_role, 'none');
  END IF;
  SELECT * INTO e FROM vyapar_commercial.entitlements en
   WHERE en.listing_id = p_listing_id::text AND en.state IN ('active','paused','awaiting_payment')
   ORDER BY (en.state = 'active') DESC, en.created_at DESC LIMIT 1;
  RETURN QUERY SELECT v_role, e.state, coalesce(e.state = 'active', false), v_owner, e.id,
                      e.renews_at, e.grace_until, coalesce(e.cancel_at_period_end, false),
                      e.product_id, e.product_version, v_name;
END;
$$;

-- Gap 3 — Identity Bridge phone lookup (dev stand-in over the member link
-- table; the real deployment calls the Identity & Trust service, TR034/SP034).
-- Returns an id or nothing — never a name, phone or any other field.
CREATE OR REPLACE FUNCTION vyapar_identity.member_id_for_phone(p_phone text)
RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_identity, pg_temp AS $$
  SELECT m.id FROM vyapar_identity.members m
   WHERE m.phone = p_phone AND m.deleted_at IS NULL AND NOT m.anonymized LIMIT 1;
$$;

-- Gap 3 — an invitee can see and answer their own invite even when the row
-- was created by phone before they joined.
CREATE OR REPLACE FUNCTION vyapar_commercial.pending_invites_for_me()
RETURNS TABLE(id uuid, listing_id text, listing_name text, role text, invited_by text, invited_at timestamptz, expires_at timestamptz)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
  SELECT wm.id, wm.listing_id, l.name, wm.role, wm.invited_by, wm.invited_at, wm.expires_at
    FROM vyapar_commercial.workspace_members wm
    LEFT JOIN vyapar_listings.listings l ON l.id = wm.listing_id::uuid
   WHERE wm.state = 'pending' AND wm.expires_at > now()
     AND (wm.member_id = current_setting('vyapar.authz_context', true)
       OR wm.phone = (SELECT m.phone FROM vyapar_identity.members m WHERE m.id = current_setting('vyapar.authz_context', true)));
$$;

CREATE OR REPLACE FUNCTION vyapar_commercial.answer_invite(p_invite_id uuid, p_accept boolean)
RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  v_phone text;
  wm vyapar_commercial.workspace_members%ROWTYPE;
BEGIN
  SELECT m.phone INTO v_phone FROM vyapar_identity.members m WHERE m.id = v_caller;
  SELECT * INTO wm FROM vyapar_commercial.workspace_members WHERE id = p_invite_id FOR UPDATE;
  IF NOT FOUND OR wm.state <> 'pending' THEN RAISE EXCEPTION 'invite_not_found'; END IF;
  IF wm.member_id IS DISTINCT FROM v_caller AND wm.phone IS DISTINCT FROM v_phone THEN RAISE EXCEPTION 'invite_not_found'; END IF;
  IF wm.expires_at <= now() THEN
    UPDATE vyapar_commercial.workspace_members SET state = 'expired' WHERE id = wm.id;
    RAISE EXCEPTION 'invite_expired';
  END IF;
  IF p_accept THEN
    UPDATE vyapar_commercial.workspace_members SET state = 'active', member_id = v_caller, accepted_at = now() WHERE id = wm.id;
    RETURN 'active';
  END IF;
  UPDATE vyapar_commercial.workspace_members SET state = 'revoked', member_id = coalesce(member_id, v_caller), revoked_at = now() WHERE id = wm.id;
  RETURN 'revoked';
END;
$$;

-- Gap 4 — payment results for entitlements and campaigns (replaces 006's
-- promotion-only version; promotion behaviour is unchanged).
CREATE OR REPLACE FUNCTION vyapar_commercial.apply_payment_result(
  p_kind text, p_ref_id uuid, p_payment_order_id uuid, p_outcome text
) RETURNS TABLE(owner_id text, from_state text, to_state text, ends_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
#variable_conflict use_column
DECLARE
  r vyapar_commercial.promotions%ROWTYPE;
  en vyapar_commercial.entitlements%ROWTYPE;
  c vyapar_commercial.campaigns%ROWTYPE;
  v_days int;
  v_to text;
  v_ends timestamptz;
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') NOT IN ('payment_webhook', 'dispatcher') THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;

  IF p_kind = 'promotion' THEN
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
      v_to := 'awaiting_payment';
    ELSIF p_outcome = 'refunded' AND r.state IN ('rejected','cancelled','active','paused') THEN
      UPDATE vyapar_commercial.promotions SET state = 'refunded', updated_at = now() WHERE id = r.id;
      v_to := 'refunded';
    ELSE
      RETURN;
    END IF;
    INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
    VALUES ('promotion', r.id, r.state, v_to, 'payment_' || p_outcome);
    RETURN QUERY SELECT r.owner_id, r.state, v_to, v_ends;

  ELSIF p_kind = 'entitlement' THEN
    SELECT * INTO en FROM vyapar_commercial.entitlements WHERE id = p_ref_id FOR UPDATE;
    IF NOT FOUND THEN RETURN; END IF;
    IF p_outcome = 'succeeded' AND en.state IN ('awaiting_payment','active','paused') THEN
      SELECT duration_days INTO v_days FROM vyapar_commercial.products WHERE id = en.product_id AND version = en.product_version;
      -- a first payment starts the period now; a renewal extends from the later of (renews_at, now)
      v_ends := greatest(coalesce(en.renews_at, now()), now()) + make_interval(days => coalesce(v_days, 30));
      UPDATE vyapar_commercial.entitlements
         SET state = 'active', starts_at = coalesce(starts_at, now()), renews_at = v_ends,
             grace_until = NULL, renewal_reminder_at = NULL, renewal_reminder_acked_at = NULL,
             payment_order_id = p_payment_order_id, updated_at = now()
       WHERE id = en.id;
      v_to := 'active';
    ELSIF p_outcome = 'failed' AND en.state = 'awaiting_payment' THEN
      v_to := 'awaiting_payment';
      v_ends := en.renews_at;
    ELSIF p_outcome = 'refunded' AND en.state IN ('active','paused','cancelled','completed') THEN
      UPDATE vyapar_commercial.entitlements SET state = 'refunded', updated_at = now() WHERE id = en.id;
      v_to := 'refunded';
      v_ends := en.renews_at;
    ELSE
      RETURN;
    END IF;
    INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
    VALUES ('entitlement', en.id, en.state, v_to, 'payment_' || p_outcome);
    RETURN QUERY SELECT en.owner_id, en.state, v_to, v_ends;

  ELSIF p_kind = 'campaign' THEN
    SELECT * INTO c FROM vyapar_commercial.campaigns WHERE id = p_ref_id FOR UPDATE;
    IF NOT FOUND THEN RETURN; END IF;
    IF p_outcome = 'succeeded' AND c.state = 'awaiting_payment' THEN
      UPDATE vyapar_commercial.campaigns SET state = 'active', payment_order_id = p_payment_order_id, updated_at = now() WHERE id = c.id;
      -- [TR035] each item runs as a real boost with the campaign's own window
      UPDATE vyapar_commercial.promotions
         SET state = 'active', starts_at = greatest(c.starts_at, now()), ends_at = c.ends_at, updated_at = now()
       WHERE campaign_id = c.id AND state = 'awaiting_payment';
      INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
      SELECT 'promotion', p.id, 'awaiting_payment', 'active', 'campaign_payment_succeeded'
        FROM vyapar_commercial.promotions p WHERE p.campaign_id = c.id AND p.state = 'active';
      v_to := 'active';
      v_ends := c.ends_at;
    ELSIF p_outcome = 'failed' AND c.state = 'awaiting_payment' THEN
      v_to := 'awaiting_payment';
      v_ends := c.ends_at;
    ELSIF p_outcome = 'refunded' AND c.state IN ('active','awaiting_payment','cancelled') THEN
      UPDATE vyapar_commercial.campaigns SET state = 'refunded', updated_at = now() WHERE id = c.id;
      UPDATE vyapar_commercial.promotions SET state = 'cancelled', updated_at = now() WHERE campaign_id = c.id AND state IN ('awaiting_payment','active');
      v_to := 'refunded';
      v_ends := c.ends_at;
    ELSE
      RETURN;
    END IF;
    RETURN QUERY SELECT c.owner_id, c.state, v_to, v_ends;
  END IF;
END;
$$;

-- Gap 4 — FR33 renewal/grace and FR54's reminder gate. Returns the actions
-- the dispatcher must follow up on; it never charges anything itself.
CREATE OR REPLACE FUNCTION vyapar_commercial.run_entitlement_lifecycle()
RETURNS TABLE(entitlement_id uuid, owner_id text, listing_id text, action text,
              renews_at timestamptz, grace_until timestamptz, product_id text, product_version int)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
#variable_conflict use_column
DECLARE r record;
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') <> 'dispatcher' THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;

  -- 3 days before renewal: record the attempt and hand the send to the caller
  FOR r IN SELECT e.* FROM vyapar_commercial.entitlements e
            WHERE e.state = 'active' AND NOT e.cancel_at_period_end
              AND e.renews_at IS NOT NULL AND e.renews_at > now()
              AND e.renews_at - interval '3 days' <= now() AND e.renewal_reminder_at IS NULL
            FOR UPDATE LOOP
    UPDATE vyapar_commercial.entitlements SET renewal_reminder_at = now(), updated_at = now() WHERE id = r.id;
    entitlement_id := r.id; owner_id := r.owner_id; listing_id := r.listing_id; action := 'reminder_due';
    renews_at := r.renews_at; grace_until := r.grace_until; product_id := r.product_id; product_version := r.product_version;
    RETURN NEXT;
  END LOOP;

  -- renewal date reached
  FOR r IN SELECT e.* FROM vyapar_commercial.entitlements e
            WHERE e.state = 'active' AND e.renews_at IS NOT NULL AND e.renews_at <= now() AND e.grace_until IS NULL
            FOR UPDATE LOOP
    IF r.cancel_at_period_end THEN
      UPDATE vyapar_commercial.entitlements SET state = 'completed', updated_at = now() WHERE id = r.id;
      INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
      VALUES ('entitlement', r.id, 'active', 'completed', 'cancelled_at_period_end');
      action := 'completed_cancelled';
    ELSIF r.renewal_reminder_acked_at IS NULL THEN
      -- [TR054] never charge a renewal whose reminder was not delivered
      UPDATE vyapar_commercial.entitlements SET state = 'paused', updated_at = now() WHERE id = r.id;
      INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
      VALUES ('entitlement', r.id, 'active', 'paused', 'renewal_reminder_undelivered');
      action := 'paused_no_reminder';
    ELSE
      UPDATE vyapar_commercial.entitlements SET grace_until = now() + interval '7 days', updated_at = now() WHERE id = r.id;
      action := 'charge_due';
    END IF;
    entitlement_id := r.id; owner_id := r.owner_id; listing_id := r.listing_id;
    renews_at := r.renews_at; grace_until := r.grace_until; product_id := r.product_id; product_version := r.product_version;
    RETURN NEXT;
  END LOOP;

  -- [FR33] 7-day grace expired with no successful renewal payment
  FOR r IN SELECT e.* FROM vyapar_commercial.entitlements e
            WHERE e.state = 'active' AND e.grace_until IS NOT NULL AND e.grace_until < now()
            FOR UPDATE LOOP
    UPDATE vyapar_commercial.entitlements SET state = 'paused', updated_at = now() WHERE id = r.id;
    INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
    VALUES ('entitlement', r.id, 'active', 'paused', 'grace_expired');
    entitlement_id := r.id; owner_id := r.owner_id; listing_id := r.listing_id; action := 'paused_grace_expired';
    renews_at := r.renews_at; grace_until := r.grace_until; product_id := r.product_id; product_version := r.product_version;
    RETURN NEXT;
  END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION vyapar_commercial.mark_reminder_acked(p_entitlement_id uuid)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') <> 'dispatcher' THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;
  UPDATE vyapar_commercial.entitlements SET renewal_reminder_acked_at = now(), updated_at = now() WHERE id = p_entitlement_id;
END;
$$;

-- Gap 4 — a campaign ends when its window closes or every item has stopped.
CREATE OR REPLACE FUNCTION vyapar_commercial.run_campaign_lifecycle()
RETURNS TABLE(campaign_id uuid, owner_id text, to_state text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
#variable_conflict use_column
DECLARE r record;
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') <> 'dispatcher' THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;
  FOR r IN SELECT c.* FROM vyapar_commercial.campaigns c
            WHERE c.state = 'active'
              AND (c.ends_at <= now()
                OR NOT EXISTS (SELECT 1 FROM vyapar_commercial.promotions p WHERE p.campaign_id = c.id AND p.state = 'active'))
            FOR UPDATE LOOP
    UPDATE vyapar_commercial.campaigns SET state = 'completed', updated_at = now() WHERE id = r.id;
    UPDATE vyapar_commercial.promotions SET state = 'completed', updated_at = now() WHERE campaign_id = r.id AND state = 'active';
    campaign_id := r.id; owner_id := r.owner_id; to_state := 'completed';
    RETURN NEXT;
  END LOOP;
END;
$$;

-- [TR035] campaign-scope reporting reuses TR032's aggregate, grouped over the
-- campaign's own items — never a second reporting implementation.
CREATE OR REPLACE FUNCTION vyapar_commercial.campaign_impressions_report(p_campaign_id uuid)
RETURNS TABLE(day date, sponsored boolean, kind text, n bigint)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
  SELECT i.day, i.sponsored, i.kind, sum(i.n)
    FROM vyapar_commercial.promotions p
    CROSS JOIN LATERAL vyapar_commercial.impressions_report(p.target_kind, p.target_id) i
   WHERE p.campaign_id = p_campaign_id
   GROUP BY i.day, i.sponsored, i.kind;
$$;

GRANT EXECUTE ON FUNCTION vyapar_commercial.workspace_context(uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_identity.member_id_for_phone(text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.pending_invites_for_me() TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.answer_invite(uuid, boolean) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.run_entitlement_lifecycle() TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.mark_reminder_acked(uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.run_campaign_lifecycle() TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.campaign_impressions_report(uuid) TO vyapar_app;
