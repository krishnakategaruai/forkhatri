-- =============================================================================
-- 051 — Plans, entitlements and payments (DEC-V1-031).
--
-- WHY (2026-09-22): Mangaly earns its keep the way Shaadi, BharatMatrimony
-- and Jeevansathi do — a free tier that lets anyone browse and send a few
-- requests a day, and paid plans (Gold; Assisted with a relationship manager)
-- that buy CAPABILITY for the member's own search. What a plan never buys is
-- a place in someone else's results: nothing in this schema is read by
-- discovery, "For you" or the photo wall.
--
-- Tables:
--   mangaly_billing.order              one row per checkout attempt
--   mangaly_billing.plan_subscription  what an account holds, from a paid order
--   mangaly_billing.webhook_event      idempotent store of gateway events
--   mangaly_profile.profile_view       who looked at whom (for the VIEWED
--                                      person's benefit only; never ranking)
--
-- RLS: an account reads its own orders and subscriptions and creates its own
-- orders. State changes that a payment gateway drives (marking an order paid,
-- opening the subscription) run through SECURITY DEFINER functions, since a
-- webhook has no signed-in member. Family reads (a parent acting for the
-- candidate uses the candidate's plan) go through `active_subscriptions()`,
-- which checks `family_info` the way every other family read here does.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS mangaly_billing AUTHORIZATION mangaly_owner;
GRANT USAGE ON SCHEMA mangaly_billing TO mangaly_app;

DO $$ BEGIN
  CREATE TYPE mangaly_billing.order_status AS ENUM ('created', 'paid', 'failed', 'refunded');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE mangaly_billing.subscription_status AS ENUM ('active', 'expired', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------------------------------------------------------------------------
-- Orders
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_billing."order" (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id          uuid NOT NULL,
  plan_code           text NOT NULL CHECK (plan_code IN ('GOLD', 'ASSISTED')),
  term_months         int  NOT NULL CHECK (term_months IN (3, 6, 12)),
  amount_paise        bigint NOT NULL CHECK (amount_paise > 0),
  gst_paise           bigint NOT NULL CHECK (gst_paise >= 0),
  currency            text NOT NULL DEFAULT 'INR' CHECK (currency = 'INR'),
  status              mangaly_billing.order_status NOT NULL DEFAULT 'created',
  gateway             text NOT NULL,
  gateway_order_id    text,
  gateway_payment_id  text,
  catalogue_version   text NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  paid_at             timestamptz
);
COMMENT ON TABLE mangaly_billing."order" IS
  '[DEC-V1-031] One checkout attempt. amount_paise is the plan price; gst_paise the 18% GST line, kept apart for invoicing. gateway is razorpay or dev-sandbox.';
CREATE INDEX IF NOT EXISTS idx_billing_order_account
  ON mangaly_billing."order" (account_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_order_gateway_order
  ON mangaly_billing."order" (gateway, gateway_order_id) WHERE gateway_order_id IS NOT NULL;

ALTER TABLE mangaly_billing."order" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS billing_order_owner ON mangaly_billing."order";
CREATE POLICY billing_order_owner ON mangaly_billing."order"
  USING (mangaly_authz.is_self(account_id))
  WITH CHECK (mangaly_authz.is_self(account_id));
-- The application inserts and reads its own orders; every status change is a
-- SECURITY DEFINER function below, so no UPDATE grant.
GRANT SELECT, INSERT ON mangaly_billing."order" TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Subscriptions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_billing.plan_subscription (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id    uuid NOT NULL,
  plan_code     text NOT NULL CHECK (plan_code IN ('GOLD', 'ASSISTED')),
  term_months   int  NOT NULL,
  status        mangaly_billing.subscription_status NOT NULL DEFAULT 'active',
  started_at    timestamptz NOT NULL DEFAULT now(),
  ends_at       timestamptz NOT NULL,
  order_id      uuid NOT NULL REFERENCES mangaly_billing."order"(id),
  auto_renew    boolean NOT NULL DEFAULT false,
  cancelled_at  timestamptz,
  CHECK (ends_at > started_at)
);
COMMENT ON TABLE mangaly_billing.plan_subscription IS
  '[DEC-V1-031] The entitlement belongs to the CANDIDATE account; a parent acting for the candidate uses it. Cancelling turns auto-renew off; the plan runs to ends_at.';
CREATE INDEX IF NOT EXISTS idx_billing_subscription_account
  ON mangaly_billing.plan_subscription (account_id, ends_at DESC);

ALTER TABLE mangaly_billing.plan_subscription ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS billing_subscription_owner ON mangaly_billing.plan_subscription;
CREATE POLICY billing_subscription_owner ON mangaly_billing.plan_subscription
  USING (mangaly_authz.is_self(account_id))
  WITH CHECK (mangaly_authz.is_self(account_id));
GRANT SELECT, UPDATE ON mangaly_billing.plan_subscription TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Webhook events — an infrastructure table like rate_limit_counter: no member
-- context exists when a gateway calls, so no RLS; the unique key is what makes
-- processing idempotent.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_billing.webhook_event (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gateway       text NOT NULL,
  event_id      text NOT NULL,
  event_type    text NOT NULL,
  payload       jsonb NOT NULL,
  received_at   timestamptz NOT NULL DEFAULT now(),
  processed_at  timestamptz,
  UNIQUE (gateway, event_id)
);
GRANT SELECT, INSERT, UPDATE ON mangaly_billing.webhook_event TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Profile views — for the viewed person only ("who viewed you"). Never read
-- by discovery; one row per pair, so it is not a counter of anything.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_profile.profile_view (
  viewer_account_id  uuid NOT NULL,
  viewed_account_id  uuid NOT NULL,
  first_viewed_at    timestamptz NOT NULL DEFAULT now(),
  last_viewed_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (viewer_account_id, viewed_account_id)
);
COMMENT ON TABLE mangaly_profile.profile_view IS
  '[DEC-V1-031] Who opened whose profile. Exists for the viewed person''s "who viewed you" list only. Must never feed ranking, "For you" or search order.';
CREATE INDEX IF NOT EXISTS idx_profile_view_viewed
  ON mangaly_profile.profile_view (viewed_account_id, last_viewed_at DESC);
ALTER TABLE mangaly_profile.profile_view ENABLE ROW LEVEL SECURITY;
-- No direct table access for the app: writes and reads go through the two
-- functions below, so a view can only ever be recorded by the viewer and
-- listed by the viewed person or their circle.
REVOKE ALL ON mangaly_profile.profile_view FROM mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_profile.record_profile_view(p_viewer uuid, p_viewed uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_authz, pg_temp
AS $$
BEGIN
    IF mangaly_authz.is_self(p_viewer) IS NOT TRUE THEN
        RAISE EXCEPTION 'a profile view is recorded by the viewer only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF p_viewer = p_viewed THEN
        RETURN;
    END IF;
    -- Only real, searchable candidates are worth telling about a view.
    IF NOT EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.account_id = p_viewed) THEN
        RETURN;
    END IF;
    INSERT INTO mangaly_profile.profile_view (viewer_account_id, viewed_account_id)
    VALUES (p_viewer, p_viewed)
    ON CONFLICT (viewer_account_id, viewed_account_id)
    DO UPDATE SET last_viewed_at = now();
END;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.record_profile_view(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.record_profile_view(uuid, uuid) TO mangaly_app;

-- Who viewed `p_account`: the person, or a circle member with family_info.
CREATE OR REPLACE FUNCTION mangaly_billing.who_viewed(p_account uuid)
RETURNS TABLE (account_id uuid, at timestamptz)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_authz, pg_temp
AS $$
BEGIN
    IF NOT (mangaly_authz.is_self(p_account) OR mangaly_authz.has_scope(p_account, 'family_info')) THEN
        RAISE EXCEPTION 'who viewed a profile is readable by that person and their circle only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN QUERY
    SELECT v.viewer_account_id, v.last_viewed_at
      FROM mangaly_profile.profile_view v
     WHERE v.viewed_account_id = p_account
     ORDER BY v.last_viewed_at DESC
     LIMIT 200;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.who_viewed(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.who_viewed(uuid) TO mangaly_app;

-- Who shortlisted `p_account`: the saved person cannot see shortlist rows
-- under the shortlist policy (they belong to the saver's context), so this
-- is the one read across that line — and it is the whole point of the
-- "see who shortlisted you" entitlement.
CREATE OR REPLACE FUNCTION mangaly_billing.who_shortlisted(p_account uuid)
RETURNS TABLE (account_id uuid, at timestamptz)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = mangaly_discovery, mangaly_authz, pg_temp
AS $$
BEGIN
    IF NOT (mangaly_authz.is_self(p_account) OR mangaly_authz.has_scope(p_account, 'family_info')) THEN
        RAISE EXCEPTION 'who shortlisted a profile is readable by that person and their circle only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN QUERY
    SELECT s.candidate_account_id, s.created_at
      FROM mangaly_discovery.shortlist s
     WHERE s.saved_account_id = p_account
       AND s.candidate_account_id <> p_account
     ORDER BY s.created_at DESC
     LIMIT 200;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.who_shortlisted(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.who_shortlisted(uuid) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Reading a plan: the person, or their circle acting for them.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_billing.active_subscriptions(p_account uuid)
RETURNS TABLE (
    id           uuid,
    plan_code    text,
    term_months  int,
    started_at   timestamptz,
    ends_at      timestamptz,
    auto_renew   boolean,
    cancelled_at timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = mangaly_billing, mangaly_authz, pg_temp
AS $$
BEGIN
    IF NOT (mangaly_authz.is_self(p_account) OR mangaly_authz.has_scope(p_account, 'family_info')) THEN
        RAISE EXCEPTION 'a plan is readable by its holder and their circle only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN QUERY
    SELECT s.id, s.plan_code, s.term_months, s.started_at, s.ends_at, s.auto_renew, s.cancelled_at
      FROM mangaly_billing.plan_subscription s
     WHERE s.account_id = p_account
       AND s.status = 'active'
       AND s.started_at <= now()
       AND s.ends_at > now()
     ORDER BY s.ends_at DESC;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.active_subscriptions(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.active_subscriptions(uuid) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Payment outcomes. Called after the gateway's signature has been verified in
-- the application (or by the sandbox in development). Idempotent: paying a
-- paid order again returns the subscription it already opened.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_billing.mark_order_paid(
    p_order_id            uuid,
    p_gateway_payment_id  text
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_billing, pg_temp
AS $$
DECLARE
    v_order        mangaly_billing."order"%ROWTYPE;
    v_existing     uuid;
    v_starts       timestamptz;
    v_subscription uuid;
BEGIN
    SELECT * INTO v_order FROM mangaly_billing."order" WHERE id = p_order_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'no such order' USING ERRCODE = 'no_data_found';
    END IF;

    IF v_order.status = 'paid' THEN
        SELECT s.id INTO v_existing FROM mangaly_billing.plan_subscription s WHERE s.order_id = p_order_id;
        RETURN v_existing;
    END IF;
    IF v_order.status <> 'created' AND v_order.status <> 'failed' THEN
        RAISE EXCEPTION 'order is %', v_order.status USING ERRCODE = 'invalid_parameter_value';
    END IF;

    UPDATE mangaly_billing."order"
       SET status = 'paid', paid_at = now(), gateway_payment_id = p_gateway_payment_id
     WHERE id = p_order_id;

    -- A renewal of the same plan starts when the current one ends.
    SELECT GREATEST(now(), COALESCE(MAX(s.ends_at), now())) INTO v_starts
      FROM mangaly_billing.plan_subscription s
     WHERE s.account_id = v_order.account_id
       AND s.plan_code = v_order.plan_code
       AND s.status = 'active';

    INSERT INTO mangaly_billing.plan_subscription
        (account_id, plan_code, term_months, status, started_at, ends_at, order_id)
    VALUES
        (v_order.account_id, v_order.plan_code, v_order.term_months, 'active',
         v_starts, v_starts + make_interval(months => v_order.term_months), p_order_id)
    RETURNING id INTO v_subscription;
    RETURN v_subscription;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.mark_order_paid(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.mark_order_paid(uuid, text) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_billing.mark_order_failed(p_order_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_billing, pg_temp
AS $$
    WITH updated AS (
        UPDATE mangaly_billing."order"
           SET status = 'failed'
         WHERE id = p_order_id AND status = 'created'
     RETURNING 1
    )
    SELECT EXISTS (SELECT 1 FROM updated);
$$;
REVOKE ALL ON FUNCTION mangaly_billing.mark_order_failed(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.mark_order_failed(uuid) TO mangaly_app;

-- Which order does a gateway order id belong to? A webhook carries only the
-- gateway's ids and has no member context to read the table under RLS.
CREATE OR REPLACE FUNCTION mangaly_billing.order_id_for_gateway(p_gateway text, p_gateway_order_id text)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_billing, pg_temp
AS $$
    SELECT o.id FROM mangaly_billing."order" o
     WHERE o.gateway = p_gateway AND o.gateway_order_id = p_gateway_order_id;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.order_id_for_gateway(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.order_id_for_gateway(text, text) TO mangaly_app;

-- The gateway's order id is assigned right after the row is created (the
-- gateway needs our id as its receipt first). Owner-only, once.
CREATE OR REPLACE FUNCTION mangaly_billing.attach_gateway_order(p_order_id uuid, p_gateway_order_id text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_billing, mangaly_authz, pg_temp
AS $$
DECLARE
    v_account uuid;
BEGIN
    SELECT account_id INTO v_account FROM mangaly_billing."order" WHERE id = p_order_id;
    IF v_account IS NULL OR mangaly_authz.is_self(v_account) IS NOT TRUE THEN
        RETURN false;
    END IF;
    UPDATE mangaly_billing."order"
       SET gateway_order_id = p_gateway_order_id
     WHERE id = p_order_id AND gateway_order_id IS NULL AND status = 'created';
    RETURN FOUND;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.attach_gateway_order(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.attach_gateway_order(uuid, text) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Contact exchange requests (table from 001, never wired until now). Asking a
-- connection for their phone/email is a Gold capability; the person asked
-- decides, and only they. Both sides of the connection may see the request.
-- ---------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS uq_contact_exchange_request_per_requester
  ON mangaly_communication.contact_exchange_request (connection_id, requester_account_id);

DROP POLICY IF EXISTS contact_exchange_participants ON mangaly_communication.contact_exchange_request;
CREATE POLICY contact_exchange_participants ON mangaly_communication.contact_exchange_request
  USING (mangaly_authz.is_self(requester_account_id)
         OR EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                     WHERE c.id = contact_exchange_request.connection_id
                       AND (mangaly_authz.is_self(c.subject_account_id)
                            OR mangaly_authz.is_self(c.target_profile_id)
                            OR mangaly_authz.has_scope(c.subject_account_id, 'family_info')
                            OR mangaly_authz.has_scope(c.target_profile_id, 'family_info'))))
  WITH CHECK (mangaly_authz.is_self(requester_account_id)
              OR mangaly_authz.is_self(decided_by_account_id));

-- ---------------------------------------------------------------------------
-- Requests sent today for the free tier's daily allowance. Counted per
-- CANDIDATE (the subject of the request), whoever pressed send, on the Indian
-- calendar day. Readable by the candidate and their circle.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_billing.requests_sent_today(p_account uuid)
RETURNS int
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = mangaly_connection, mangaly_authz, pg_temp
AS $$
DECLARE
    v_count int;
BEGIN
    IF NOT (mangaly_authz.is_self(p_account) OR mangaly_authz.has_scope(p_account, 'family_info')) THEN
        RAISE EXCEPTION 'request usage is readable by the person and their circle only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    SELECT count(*) INTO v_count
      FROM mangaly_connection.connection_request c
     WHERE c.subject_account_id = p_account
       AND c.requested_at >= (date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata');
    RETURN v_count;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.requests_sent_today(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.requests_sent_today(uuid) TO mangaly_app;
