-- [IMP — Backend workstream D, 2026-09-28] Contracts & milestone payments.
--
-- A client (the side that pays) and a provider (the side that does the work)
-- turn an accepted enquiry — a listing enquiry the provider accepted, or a
-- hired applicant on an opportunity — into a contract: fixed-price with
-- milestones, or hourly with weekly timesheets. Each milestone is paid up
-- front by the client through the existing Payment Bridge (TR051) and is
-- recorded as HELD in `contract_ledger` until the client approves the
-- provider's submission (or 14 days pass), when it is recorded as RELEASED.
--
-- HONEST GAP (09-implementation.md BLOCKER-01, no merchant account):
-- "held" is a ledger fact, not an escrow or payout. Money the client pays
-- through the gateway lands in the platform account; nothing is paid out to
-- the provider by this code. Releasing a milestone records the obligation
-- and notifies the provider. A real payout (Razorpay Route / a nodal
-- account) is the vendor integration to add behind the same ledger when the
-- merchant account exists — no table here needs to change for that.
--
-- Platform fee: `contracts.platform_fee_bps` is copied from configuration
-- (CONTRACT_PLATFORM_FEE_BPS, default 0) when the contract is created. Vyapar
-- takes no cut from workers by default; a `fee` ledger entry is written only
-- when the rate is above zero.
--
-- Design notes:
--  * New schema `vyapar_contracts`, one owning component (Contracts), the
--    schema-per-component rule of MODULE-ARCHITECTURE-STANDARD §4. Cross-
--    schema references (enquiry, opportunity, listing, payment order) are
--    plain uuids, the same "no cross-schema FK" convention 001 uses.
--  * RLS: the two parties, moderation operators, and the background pass
--    (`vyapar.service_role = 'dispatcher'`). Child tables inherit the rule
--    through EXISTS on the contract.
--  * Payment success reaches a milestone through an AFTER UPDATE trigger on
--    `vyapar_payments.payment_orders` (kind = 'contract_milestone'), so the
--    Payment Bridge's own webhook and status-poll paths need no change and
--    the milestone moves in the same transaction as the order. The trigger
--    runs as the owner (SECURITY DEFINER) because the webhook has no member
--    session.
--  * Domain events go to the enquiries outbox (`vyapar_enquiries.outbox_event`,
--    the one the webhook fan-out already reads): a contract is the
--    continuation of an enquiry between the same two members. Payloads carry
--    ids, states and amounts only.
--  * Review invites: `vyapar_reviews.issue_invites('enquiry', …)` now also
--    qualifies an enquiry with a completed contract, so the existing reviews
--    service issues both invites on completion without a new interaction kind.
-- Traces to: FR23 (accepted enquiry), FR27 (review invites), FR51/TR051
-- (Payment Bridge), FR52/TR052 (outbox), REFACTOR-PLAN.md §A

CREATE SCHEMA IF NOT EXISTS vyapar_contracts AUTHORIZATION vyapar_owner;

-- ---------------------------------------------------------------------------
-- 1. Tables
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_contracts.contracts (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id      uuid,                                   -- no cross-schema FK
  enquiry_id          uuid NOT NULL,                          -- no cross-schema FK
  client_member_id    text NOT NULL,
  provider_member_id  text NOT NULL,
  provider_listing_id uuid,                                   -- no cross-schema FK; NULL for a hired applicant without a listing
  title               text NOT NULL CHECK (char_length(title) BETWEEN 3 AND 140),
  description         text CHECK (description IS NULL OR char_length(description) <= 2000),
  kind                text NOT NULL CHECK (kind IN ('fixed','hourly')),
  currency            text NOT NULL DEFAULT 'INR' CHECK (currency = 'INR'),
  total_paise         bigint NOT NULL CHECK (total_paise > 0),  -- fixed: sum of milestones; hourly: budget ceiling
  hourly_rate_paise   bigint CHECK (hourly_rate_paise IS NULL OR hourly_rate_paise > 0),
  weekly_hours_cap    numeric(5,2) CHECK (weekly_hours_cap IS NULL OR (weekly_hours_cap > 0 AND weekly_hours_cap <= 168)),
  platform_fee_bps    int NOT NULL DEFAULT 0 CHECK (platform_fee_bps BETWEEN 0 AND 10000),
  state               text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','proposed','active','completed','cancelled','disputed')),
  proposed_at         timestamptz,
  accepted_at         timestamptz,
  completed_at        timestamptz,
  cancelled_at        timestamptz,
  cancelled_by        text,
  cancel_reason       text CHECK (cancel_reason IS NULL OR char_length(cancel_reason) <= 500),
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  CHECK (client_member_id <> provider_member_id),
  CHECK (kind = 'fixed' OR (hourly_rate_paise IS NOT NULL AND weekly_hours_cap IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS contracts_client_idx ON vyapar_contracts.contracts (client_member_id, created_at DESC);
CREATE INDEX IF NOT EXISTS contracts_provider_idx ON vyapar_contracts.contracts (provider_member_id, created_at DESC);
-- One live contract per enquiry (a cancelled or completed one may be followed by another).
CREATE UNIQUE INDEX IF NOT EXISTS contracts_one_live_per_enquiry
  ON vyapar_contracts.contracts (enquiry_id) WHERE state IN ('draft','proposed','active','disputed');
COMMENT ON TABLE vyapar_contracts.contracts IS '[Workstream D] A client/provider agreement born from an accepted enquiry. Money is recorded in contract_ledger; no escrow/payout until BLOCKER-01 (merchant account) is resolved.';

CREATE TABLE IF NOT EXISTS vyapar_contracts.contract_milestones (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contract_id      uuid NOT NULL REFERENCES vyapar_contracts.contracts(id) ON DELETE CASCADE,
  title            text NOT NULL CHECK (char_length(title) BETWEEN 2 AND 140),
  description      text CHECK (description IS NULL OR char_length(description) <= 2000),
  amount_paise     bigint NOT NULL CHECK (amount_paise > 0),
  due_date         date,
  sort             int NOT NULL DEFAULT 0,
  state            text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','funded','submitted','approved','released','rejected','refunded')),
  funded_order_id  uuid,                                      -- -> vyapar_payments.payment_orders.id (no cross-schema FK)
  checkout_url     text,                                      -- the open checkout for funded_order_id, until it is paid or fails
  funded_at        timestamptz,
  submitted_at     timestamptz,
  submission_note  text CHECK (submission_note IS NULL OR char_length(submission_note) <= 1000),
  approved_at      timestamptz,
  released_at      timestamptz,
  rejected_at      timestamptz,
  reject_note      text CHECK (reject_note IS NULL OR char_length(reject_note) <= 1000),
  auto_release_at  timestamptz,                               -- submitted_at + 14 days; the scheduled pass releases at this time
  auto_approve     boolean NOT NULL DEFAULT false,            -- timesheet-backed milestone: released the moment it is funded
  pending_notice   jsonb,                                     -- pre-rendered en/hi/te texts for the notification the payment trigger sends
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS contract_milestones_contract_idx ON vyapar_contracts.contract_milestones (contract_id, sort, created_at);
CREATE INDEX IF NOT EXISTS contract_milestones_auto_release_idx ON vyapar_contracts.contract_milestones (auto_release_at) WHERE state = 'submitted';

CREATE TABLE IF NOT EXISTS vyapar_contracts.contract_ledger (
  id               bigserial PRIMARY KEY,
  contract_id      uuid NOT NULL REFERENCES vyapar_contracts.contracts(id) ON DELETE CASCADE,
  milestone_id     uuid REFERENCES vyapar_contracts.contract_milestones(id) ON DELETE SET NULL,
  entry            text NOT NULL CHECK (entry IN ('held','released','refunded','fee')),
  amount_paise     bigint NOT NULL CHECK (amount_paise >= 0),
  payment_order_id uuid,                                      -- -> vyapar_payments.payment_orders.id (no cross-schema FK)
  note             text,
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS contract_ledger_contract_idx ON vyapar_contracts.contract_ledger (contract_id, created_at);
COMMENT ON TABLE vyapar_contracts.contract_ledger IS 'held = client paid, money recorded as held for this milestone; released = owed/paid to the provider; refunded = returned to the client; fee = platform share (only when platform_fee_bps > 0). Ledger facts, not escrow (BLOCKER-01).';

CREATE TABLE IF NOT EXISTS vyapar_contracts.contract_events (
  id               bigserial PRIMARY KEY,
  contract_id      uuid NOT NULL REFERENCES vyapar_contracts.contracts(id) ON DELETE CASCADE,
  milestone_id     uuid,
  actor_member_id  text,                                      -- NULL for the system (payment trigger, scheduled pass)
  type             text NOT NULL,
  data             jsonb NOT NULL DEFAULT '{}',
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS contract_events_contract_idx ON vyapar_contracts.contract_events (contract_id, id);

CREATE TABLE IF NOT EXISTS vyapar_contracts.contract_disputes (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contract_id      uuid NOT NULL REFERENCES vyapar_contracts.contracts(id) ON DELETE CASCADE,
  milestone_id     uuid REFERENCES vyapar_contracts.contract_milestones(id) ON DELETE SET NULL,
  opened_by        text NOT NULL,
  reason           text NOT NULL CHECK (char_length(reason) BETWEEN 10 AND 2000),
  state            text NOT NULL DEFAULT 'open' CHECK (state IN ('open','resolved_client','resolved_provider','closed')),
  notes            text CHECK (notes IS NULL OR char_length(notes) <= 2000),
  resolved_by      text,
  resolved_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS contract_disputes_contract_idx ON vyapar_contracts.contract_disputes (contract_id, created_at DESC);
CREATE INDEX IF NOT EXISTS contract_disputes_open_idx ON vyapar_contracts.contract_disputes (created_at) WHERE state = 'open';
COMMENT ON TABLE vyapar_contracts.contract_disputes IS 'In-product mediation only (a moderation operator records the outcome); no arbitration.';

CREATE TABLE IF NOT EXISTS vyapar_contracts.timesheets (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contract_id      uuid NOT NULL REFERENCES vyapar_contracts.contracts(id) ON DELETE CASCADE,
  week_start       date NOT NULL CHECK (extract(isodow FROM week_start) = 1),   -- Monday
  hours            numeric(5,2) NOT NULL CHECK (hours > 0 AND hours <= 168),
  note             text CHECK (note IS NULL OR char_length(note) <= 1000),
  state            text NOT NULL DEFAULT 'submitted' CHECK (state IN ('submitted','approved','paid','rejected')),
  reject_note      text CHECK (reject_note IS NULL OR char_length(reject_note) <= 1000),
  milestone_id     uuid REFERENCES vyapar_contracts.contract_milestones(id) ON DELETE SET NULL,
  submitted_at     timestamptz NOT NULL DEFAULT now(),
  approved_at      timestamptz,
  paid_at          timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (contract_id, week_start)
);

-- ---------------------------------------------------------------------------
-- 2. Row-level security: the two parties, moderation operators, the background pass
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_contracts.is_party(p_contract_id uuid)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_contracts, pg_temp AS $$
  SELECT EXISTS (
    SELECT 1 FROM vyapar_contracts.contracts c
     WHERE c.id = p_contract_id
       AND current_setting('vyapar.authz_context', true) IN (c.client_member_id, c.provider_member_id))
    OR vyapar_identity.is_operator('moderation')
    OR coalesce(current_setting('vyapar.service_role', true), '') = 'dispatcher';
$$;

ALTER TABLE vyapar_contracts.contracts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contracts_parties ON vyapar_contracts.contracts;
CREATE POLICY contracts_parties ON vyapar_contracts.contracts
  USING (client_member_id = current_setting('vyapar.authz_context', true)
      OR provider_member_id = current_setting('vyapar.authz_context', true)
      OR vyapar_identity.is_operator('moderation')
      OR coalesce(current_setting('vyapar.service_role', true), '') = 'dispatcher')
  WITH CHECK (client_member_id = current_setting('vyapar.authz_context', true)
      OR provider_member_id = current_setting('vyapar.authz_context', true)
      OR vyapar_identity.is_operator('moderation')
      OR coalesce(current_setting('vyapar.service_role', true), '') = 'dispatcher');

ALTER TABLE vyapar_contracts.contract_milestones ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contract_milestones_parties ON vyapar_contracts.contract_milestones;
CREATE POLICY contract_milestones_parties ON vyapar_contracts.contract_milestones
  USING (vyapar_contracts.is_party(contract_id)) WITH CHECK (vyapar_contracts.is_party(contract_id));

ALTER TABLE vyapar_contracts.contract_ledger ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contract_ledger_parties ON vyapar_contracts.contract_ledger;
CREATE POLICY contract_ledger_parties ON vyapar_contracts.contract_ledger
  USING (vyapar_contracts.is_party(contract_id)) WITH CHECK (vyapar_contracts.is_party(contract_id));

ALTER TABLE vyapar_contracts.contract_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contract_events_parties ON vyapar_contracts.contract_events;
CREATE POLICY contract_events_parties ON vyapar_contracts.contract_events
  USING (vyapar_contracts.is_party(contract_id)) WITH CHECK (vyapar_contracts.is_party(contract_id));

ALTER TABLE vyapar_contracts.contract_disputes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contract_disputes_parties ON vyapar_contracts.contract_disputes;
CREATE POLICY contract_disputes_parties ON vyapar_contracts.contract_disputes
  USING (vyapar_contracts.is_party(contract_id)) WITH CHECK (vyapar_contracts.is_party(contract_id));

ALTER TABLE vyapar_contracts.timesheets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS timesheets_parties ON vyapar_contracts.timesheets;
CREATE POLICY timesheets_parties ON vyapar_contracts.timesheets
  USING (vyapar_contracts.is_party(contract_id)) WITH CHECK (vyapar_contracts.is_party(contract_id));

-- ---------------------------------------------------------------------------
-- 3. Payment Bridge: milestone orders are a new order kind
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_payments.payment_orders DROP CONSTRAINT IF EXISTS payment_orders_kind_check;
ALTER TABLE vyapar_payments.payment_orders
  ADD CONSTRAINT payment_orders_kind_check CHECK (kind IN ('promotion','entitlement','campaign','contract_milestone'));

-- Notify one party of a contract the caller is part of. Same shape as
-- vyapar_integration.notify_interaction_party (migration 005): texts arrive
-- pre-translated for en/hi/te, the recipient's language is picked here, a
-- block by the recipient silences it. The background pass calls it with the
-- client's context set, so the party check holds there too.
CREATE OR REPLACE FUNCTION vyapar_contracts.notify_party(
  p_contract_id uuid, p_recipient text, p_template text, p_texts jsonb, p_link text, p_idem text
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_contracts, pg_temp AS $$
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
          p_link, jsonb_build_object('contract_id', p_contract_id), p_idem)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$$;

-- Payment outcome -> milestone. Fires from record_gateway_event() (webhook
-- or status poll) and from a refund, in the same transaction. Runs as the
-- owner: the webhook has no member session. Idempotent by milestone state.
CREATE OR REPLACE FUNCTION vyapar_contracts.on_milestone_payment() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_contracts, pg_temp AS $$
DECLARE
  m vyapar_contracts.contract_milestones%ROWTYPE;
  c vyapar_contracts.contracts%ROWTYPE;
  v_fee bigint;
  v_lang text;
  v_texts jsonb;
  v_audience jsonb;
BEGIN
  IF NEW.kind <> 'contract_milestone' OR NEW.state IS NOT DISTINCT FROM OLD.state THEN RETURN NULL; END IF;
  SELECT * INTO m FROM vyapar_contracts.contract_milestones WHERE id = NEW.ref_id FOR UPDATE;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT * INTO c FROM vyapar_contracts.contracts WHERE id = m.contract_id;
  v_audience := jsonb_build_array(c.client_member_id, c.provider_member_id);

  IF NEW.state = 'succeeded' AND m.state = 'pending' THEN
    UPDATE vyapar_contracts.contract_milestones
       SET state = 'funded', funded_order_id = NEW.id, checkout_url = NULL, funded_at = now(), updated_at = now()
     WHERE id = m.id;
    INSERT INTO vyapar_contracts.contract_ledger (contract_id, milestone_id, entry, amount_paise, payment_order_id, note)
    VALUES (c.id, m.id, 'held', m.amount_paise, NEW.id, 'payment_succeeded');
    INSERT INTO vyapar_contracts.contract_events (contract_id, milestone_id, actor_member_id, type, data)
    VALUES (c.id, m.id, NULL, 'milestone.funded', jsonb_build_object('payment_order_id', NEW.id, 'amount_paise', m.amount_paise));
    INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES ('milestone.funded', jsonb_build_object(
      'contract_id', c.id, 'milestone_id', m.id, 'enquiry_id', c.enquiry_id, 'amount_paise', m.amount_paise,
      'client_member_id', c.client_member_id, 'provider_member_id', c.provider_member_id, 'audience', v_audience));

    IF m.pending_notice IS NOT NULL THEN
      SELECT mm.language INTO v_lang FROM vyapar_identity.members mm WHERE mm.id = c.provider_member_id;
      v_lang := coalesce(v_lang, 'en');
      v_texts := m.pending_notice -> 'texts';
      INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
      VALUES (c.provider_member_id, m.pending_notice ->> 'template', m.pending_notice ->> 'template',
              coalesce(v_texts -> v_lang ->> 'title', v_texts -> 'en' ->> 'title'),
              coalesce(v_texts -> v_lang ->> 'body', v_texts -> 'en' ->> 'body'),
              '/contracts/' || c.id, jsonb_build_object('contract_id', c.id, 'milestone_id', m.id),
              'milestone_funded:' || m.id)
      ON CONFLICT (idempotency_key) DO NOTHING;
      UPDATE vyapar_contracts.contract_milestones SET pending_notice = NULL WHERE id = m.id;
    END IF;

    -- A timesheet-backed milestone is already approved: release on funding.
    IF m.auto_approve THEN
      v_fee := floor(m.amount_paise * c.platform_fee_bps / 10000.0);
      UPDATE vyapar_contracts.contract_milestones
         SET state = 'released', approved_at = now(), released_at = now(), updated_at = now()
       WHERE id = m.id;
      INSERT INTO vyapar_contracts.contract_ledger (contract_id, milestone_id, entry, amount_paise, payment_order_id, note)
      VALUES (c.id, m.id, 'released', m.amount_paise - v_fee, NEW.id, 'timesheet_paid');
      IF v_fee > 0 THEN
        INSERT INTO vyapar_contracts.contract_ledger (contract_id, milestone_id, entry, amount_paise, payment_order_id, note)
        VALUES (c.id, m.id, 'fee', v_fee, NEW.id, 'platform_fee');
      END IF;
      UPDATE vyapar_contracts.timesheets SET state = 'paid', paid_at = now(), updated_at = now() WHERE milestone_id = m.id;
      INSERT INTO vyapar_contracts.contract_events (contract_id, milestone_id, actor_member_id, type, data)
      VALUES (c.id, m.id, NULL, 'milestone.released', jsonb_build_object('amount_paise', m.amount_paise, 'fee_paise', v_fee, 'reason', 'timesheet'));
      INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES ('milestone.approved', jsonb_build_object(
        'contract_id', c.id, 'milestone_id', m.id, 'enquiry_id', c.enquiry_id, 'amount_paise', m.amount_paise, 'fee_paise', v_fee,
        'client_member_id', c.client_member_id, 'provider_member_id', c.provider_member_id, 'reason', 'timesheet', 'audience', v_audience));
    END IF;

  ELSIF NEW.state = 'failed' AND m.state = 'pending' THEN
    UPDATE vyapar_contracts.contract_milestones SET funded_order_id = NULL, checkout_url = NULL, updated_at = now() WHERE id = m.id;
    INSERT INTO vyapar_contracts.contract_events (contract_id, milestone_id, actor_member_id, type, data)
    VALUES (c.id, m.id, NULL, 'milestone.payment_failed', jsonb_build_object('payment_order_id', NEW.id));

  ELSIF NEW.state = 'refunded' AND m.state IN ('funded','rejected') THEN
    UPDATE vyapar_contracts.contract_milestones SET state = 'refunded', updated_at = now() WHERE id = m.id;
    INSERT INTO vyapar_contracts.contract_ledger (contract_id, milestone_id, entry, amount_paise, payment_order_id, note)
    VALUES (c.id, m.id, 'refunded', m.amount_paise, NEW.id, 'gateway_refund');
    INSERT INTO vyapar_contracts.contract_events (contract_id, milestone_id, actor_member_id, type, data)
    VALUES (c.id, m.id, NULL, 'milestone.refunded', jsonb_build_object('payment_order_id', NEW.id));
  END IF;
  RETURN NULL;
END $$;

DROP TRIGGER IF EXISTS payment_orders_contract_milestone ON vyapar_payments.payment_orders;
CREATE TRIGGER payment_orders_contract_milestone AFTER UPDATE OF state ON vyapar_payments.payment_orders
  FOR EACH ROW WHEN (NEW.kind = 'contract_milestone') EXECUTE FUNCTION vyapar_contracts.on_milestone_payment();

-- ---------------------------------------------------------------------------
-- 4. Reviews: a completed contract qualifies its enquiry for review invites
--    (in addition to 005's "resolved/closed with a reply from each side").
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_reviews.issue_invites(p_kind text, p_id uuid)
RETURNS TABLE(member_id text, subject_member_id text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_reviews, pg_temp AS $$
#variable_conflict use_column
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  v_a text; v_b text;          -- a = requester side, b = provider/recipient side
  v_la uuid; v_lb uuid;        -- listing reviewed by a (b's listing) / by b (a's listing)
  v_ok boolean := false;
BEGIN
  IF p_kind = 'enquiry' THEN
    SELECT e.sender_id, e.provider_id, e.listing_id, NULL::uuid,
           (e.state IN ('resolved','closed')
            AND EXISTS (SELECT 1 FROM vyapar_enquiries.enquiry_messages m WHERE m.enquiry_id = e.id AND m.sender_id = e.sender_id AND NOT m.system_note)
            AND EXISTS (SELECT 1 FROM vyapar_enquiries.enquiry_messages m WHERE m.enquiry_id = e.id AND m.sender_id = e.provider_id AND NOT m.system_note))
           OR EXISTS (SELECT 1 FROM vyapar_contracts.contracts c WHERE c.enquiry_id = e.id AND c.state = 'completed')
      INTO v_a, v_b, v_la, v_lb, v_ok
      FROM vyapar_enquiries.enquiries e WHERE e.id = p_id;
  ELSIF p_kind = 'partnership' THEN
    SELECT p.sender_id, p.recipient_id, p.recipient_listing_id, p.sender_listing_id,
           p.state = 'closed' AND p.decided_at IS NOT NULL
      INTO v_a, v_b, v_la, v_lb, v_ok
      FROM vyapar_enquiries.partnership_requests p WHERE p.id = p_id;
  END IF;
  IF v_a IS NULL OR v_caller NOT IN (v_a, v_b) THEN RAISE EXCEPTION 'not_a_party'; END IF;
  IF NOT coalesce(v_ok, false) THEN RETURN; END IF;

  RETURN QUERY
  WITH ins AS (
    INSERT INTO vyapar_reviews.review_invites (interaction_kind, interaction_id, member_id, subject_listing_id, subject_member_id, expires_at)
    VALUES (p_kind, p_id, v_a, v_la, v_b, now() + interval '30 days'),
           (p_kind, p_id, v_b, v_lb, v_a, now() + interval '30 days')
    ON CONFLICT (interaction_kind, interaction_id, member_id) DO NOTHING
    RETURNING review_invites.member_id AS mid, review_invites.subject_member_id AS sid
  )
  SELECT ins.mid, ins.sid FROM ins;
END;
$$;

-- ---------------------------------------------------------------------------
-- 5. Grants (vyapar_app is the non-owning runtime role; RLS applies to it)
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA vyapar_contracts TO vyapar_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapar_contracts TO vyapar_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vyapar_contracts TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_contracts.is_party(uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_contracts.notify_party(uuid, text, text, jsonb, text, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_reviews.issue_invites(text, uuid) TO vyapar_app;
