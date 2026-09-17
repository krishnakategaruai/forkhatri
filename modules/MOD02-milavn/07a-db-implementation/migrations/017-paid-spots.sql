-- 017 — Paid spots (FR102): Milavn's side of paid activities.
--
-- Money never touches Milavn. Payment Services (MOD06) captures, holds and
-- refunds; Milavn stores only the returned reference (ARCHITECTURE.md: "stores
-- only that reference", ADR-008) plus what a member and an organizer need to
-- understand a spot: price, refund window, a short hold while payment is in
-- progress, paid / refunded state.
--
-- Values (thesis §53–§55): monetise value creation, not belonging — free stays
-- the default; nobody ever sees who has or has not paid; trust and ranking
-- never read payment data (FR036).
--
--   occurrence.price_paise / refund_cutoff_hours   organizer's choice (NULL price = free)
--   milavn_ticketing.ticket                        one open ticket per member per activity
--   milavn_ticketing.payment_event                 idempotent log of Payment Services events
--
-- Every cross-member write (webhook, hold expiry, waitlist offers, refunds on
-- cancellation) goes through a SECURITY DEFINER function; members read and
-- create only their own tickets under RLS.

CREATE SCHEMA IF NOT EXISTS milavn_ticketing;
GRANT USAGE ON SCHEMA milavn_ticketing TO milavn_app;

ALTER TABLE milavn_activity.occurrence
  ADD COLUMN IF NOT EXISTS price_paise integer,
  ADD COLUMN IF NOT EXISTS refund_cutoff_hours integer NOT NULL DEFAULT 24;
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_price_range CHECK (price_paise IS NULL OR price_paise BETWEEN 100 AND 10000000);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_refund_cutoff_range CHECK (refund_cutoff_hours BETWEEN 0 AND 168);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS milavn_ticketing.ticket (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id       uuid NOT NULL,          -- cross-schema ref -> milavn_activity.occurrence(id), no FK (§4)
  member_id           uuid NOT NULL,
  kind                text NOT NULL DEFAULT 'join' CHECK (kind IN ('join', 'waitlist_offer')),
  amount_paise        integer NOT NULL CHECK (amount_paise > 0),
  currency            text NOT NULL DEFAULT 'INR' CHECK (currency = 'INR'),
  status              text NOT NULL CHECK (status IN ('awaiting_payment', 'paid', 'expired', 'failed', 'void', 'refund_pending', 'refunded')),
  payment_reference   text,                   -- Payment Services charge reference; never card or UPI data
  checkout_url        text,
  hold_expires_at     timestamptz,
  paid_at             timestamptz,
  refund_reference    text,
  refund_amount_paise integer,
  refund_reason       text CHECK (refund_reason IS NULL OR refund_reason IN ('member_withdrew', 'organizer_cancelled', 'no_spot', 'duplicate')),
  refunded_at         timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ticket_one_open_per_member ON milavn_ticketing.ticket (occurrence_id, member_id)
  WHERE status IN ('awaiting_payment', 'paid', 'refund_pending');
CREATE UNIQUE INDEX IF NOT EXISTS ticket_payment_reference_unique ON milavn_ticketing.ticket (payment_reference) WHERE payment_reference IS NOT NULL;
CREATE INDEX IF NOT EXISTS ticket_holds_idx ON milavn_ticketing.ticket (hold_expires_at) WHERE status = 'awaiting_payment';
CREATE INDEX IF NOT EXISTS ticket_member_idx ON milavn_ticketing.ticket (member_id, created_at DESC);

CREATE TABLE IF NOT EXISTS milavn_ticketing.payment_event (
  event_id          text PRIMARY KEY,         -- Payment Services' own event id: a redelivery is a no-op
  event_type        text NOT NULL,
  payment_reference text NOT NULL,
  received_at       timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE milavn_ticketing.ticket ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ticket_self ON milavn_ticketing.ticket;
CREATE POLICY ticket_self ON milavn_ticketing.ticket
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
ALTER TABLE milavn_ticketing.payment_event ENABLE ROW LEVEL SECURITY;  -- no policy: definer functions only

GRANT SELECT, INSERT, UPDATE ON milavn_ticketing.ticket TO milavn_app;

-- ---- helpers ---------------------------------------------------------------------

-- Spots held for people who are paying right now count against capacity, so two people can never pay for one spot.
CREATE OR REPLACE FUNCTION milavn_activity.held_spot_count(p_occurrence_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT count(*)::integer FROM milavn_ticketing.ticket
  WHERE occurrence_id = p_occurrence_id AND status = 'awaiting_payment' AND hold_expires_at > now();
$$;

-- Tickets that lock the price: once anyone is paying or has paid, the price cannot change under them.
CREATE OR REPLACE FUNCTION milavn_ticketing.open_ticket_count(p_occurrence_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT count(*)::integer FROM milavn_ticketing.ticket
  WHERE occurrence_id = p_occurrence_id AND status IN ('awaiting_payment', 'paid', 'refund_pending');
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.ticket_by_reference(p_reference text)
RETURNS TABLE (id uuid, occurrence_id uuid, member_id uuid, kind text, status text, amount_paise integer, hold_expires_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT t.id, t.occurrence_id, t.member_id, t.kind, t.status, t.amount_paise, t.hold_expires_at
  FROM milavn_ticketing.ticket t WHERE t.payment_reference = p_reference OR t.refund_reference = p_reference LIMIT 1;
$$;

-- Records a Payment Services event once; false means it was already processed.
CREATE OR REPLACE FUNCTION milavn_ticketing.record_payment_event(p_event_id text, p_event_type text, p_reference text)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, pg_catalog AS $$
BEGIN
  INSERT INTO milavn_ticketing.payment_event (event_id, event_type, payment_reference) VALUES (p_event_id, p_event_type, p_reference);
  RETURN true;
EXCEPTION WHEN unique_violation THEN
  RETURN false;
END;
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.attach_charge(p_ticket_id uuid, p_reference text, p_checkout_url text)
RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_ticketing, pg_catalog AS $$
  UPDATE milavn_ticketing.ticket SET payment_reference = p_reference, checkout_url = p_checkout_url, updated_at = now() WHERE id = p_ticket_id;
$$;

-- A payment succeeded. Under the same per-activity lock the participation toggle uses (TR39):
--   'going'           the member is in (their hold was still valid, or a spot is free)
--   'refund_no_spot'  the hold had lapsed and the activity filled up meanwhile — the caller refunds in full
--   'refund_cancelled' the organizer cancelled meanwhile — the caller refunds in full
--   'already' / 'ignored' / 'missing'
CREATE OR REPLACE FUNCTION milavn_ticketing.mark_paid(p_ticket_id uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE
  t milavn_ticketing.ticket%ROWTYPE;
  occ record;
  p record;
  hold_valid boolean;
BEGIN
  SELECT * INTO t FROM milavn_ticketing.ticket WHERE id = p_ticket_id FOR UPDATE;
  IF NOT FOUND THEN RETURN 'missing'; END IF;
  IF t.status = 'paid' THEN RETURN 'already'; END IF;
  IF t.status NOT IN ('awaiting_payment', 'expired', 'failed') THEN RETURN 'ignored'; END IF;
  PERFORM pg_advisory_xact_lock(hashtext(t.occurrence_id::text));
  SELECT capacity, status::text AS status INTO occ FROM milavn_activity.occurrence WHERE id = t.occurrence_id;
  hold_valid := t.status = 'awaiting_payment' AND t.hold_expires_at > now();
  UPDATE milavn_ticketing.ticket SET status = 'paid', paid_at = now(), hold_expires_at = NULL, updated_at = now() WHERE id = t.id;
  IF occ.status = 'cancelled' THEN RETURN 'refund_cancelled'; END IF;
  IF NOT hold_valid AND occ.capacity IS NOT NULL
     AND milavn_activity.going_count(t.occurrence_id) + milavn_activity.held_spot_count(t.occurrence_id) >= occ.capacity THEN
    RETURN 'refund_no_spot';
  END IF;
  SELECT id, status::text AS status INTO p FROM milavn_activity.participation WHERE occurrence_id = t.occurrence_id AND member_id = t.member_id;
  IF NOT FOUND THEN
    INSERT INTO milavn_activity.participation (id, occurrence_id, member_id, status) VALUES (gen_random_uuid(), t.occurrence_id, t.member_id, 'going')
    RETURNING id INTO p.id;
    INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
    VALUES (p.id, NULL, 'going', t.member_id);
  ELSIF p.status NOT IN ('going', 'checked_in', 'attended') THEN
    UPDATE milavn_activity.participation SET status = 'going', waitlist_position = NULL, updated_at = now() WHERE id = p.id;
    INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
    VALUES (p.id, CAST(p.status AS milavn_activity.participation_status), 'going', t.member_id);
  END IF;
  RETURN 'going';
END;
$$;

-- A payment failed for good. A failed waitlist offer lapses like an expired one: that member goes back to interested,
-- so the spot can be offered to the next person.
CREATE OR REPLACE FUNCTION milavn_ticketing.mark_failed(p_ticket_id uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE t record; p record;
BEGIN
  UPDATE milavn_ticketing.ticket SET status = 'failed', hold_expires_at = NULL, updated_at = now()
  WHERE id = p_ticket_id AND status = 'awaiting_payment'
  RETURNING kind, occurrence_id, member_id INTO t;
  IF NOT FOUND THEN RETURN NULL; END IF;
  IF t.kind = 'waitlist_offer' THEN
    SELECT id INTO p FROM milavn_activity.participation WHERE occurrence_id = t.occurrence_id AND member_id = t.member_id AND status = 'waitlisted';
    IF FOUND THEN
      UPDATE milavn_activity.participation SET status = 'interested', waitlist_position = NULL, updated_at = now() WHERE id = p.id;
      INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
      VALUES (p.id, 'waitlisted', 'interested', t.member_id);
    END IF;
  END IF;
  RETURN t.kind;
END;
$$;

-- What the ticketing flow needs about an activity in any context (member request, webhook, scheduled job).
CREATE OR REPLACE FUNCTION milavn_ticketing.offer_context(p_occurrence_id uuid)
RETURNS TABLE (title text, slug text, time_start timestamptz, price_paise integer, refund_cutoff_hours integer, status text, capacity integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT o.title, o.canonical_url_slug, o.time_start, o.price_paise, o.refund_cutoff_hours, o.status::text, o.capacity
  FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.mark_void(p_ticket_id uuid)
RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_ticketing, pg_catalog AS $$
  UPDATE milavn_ticketing.ticket SET status = 'void', hold_expires_at = NULL, updated_at = now()
  WHERE id = p_ticket_id AND status IN ('awaiting_payment', 'paid');
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.mark_refund_pending(p_ticket_id uuid, p_amount integer, p_reason text, p_refund_reference text)
RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_ticketing, pg_catalog AS $$
  UPDATE milavn_ticketing.ticket
  SET status = 'refund_pending', refund_amount_paise = p_amount, refund_reason = p_reason, refund_reference = p_refund_reference, updated_at = now()
  WHERE id = p_ticket_id AND status = 'paid';
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.mark_refunded(p_ticket_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_ticketing, pg_catalog AS $$
  WITH u AS (
    UPDATE milavn_ticketing.ticket SET status = 'refunded', refunded_at = now(), updated_at = now()
    WHERE id = p_ticket_id AND status = 'refund_pending' RETURNING 1
  ) SELECT EXISTS (SELECT 1 FROM u);
$$;

-- Holds that ran out: the spot goes back. A lapsed waitlist offer moves that member from waitlisted to interested
-- (they did not take the spot) so the next person can be offered it.
CREATE OR REPLACE FUNCTION milavn_ticketing.expire_holds()
RETURNS TABLE (ticket_id uuid, occurrence_id uuid, member_id uuid, kind text, payment_reference text)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE r record; p record;
BEGIN
  FOR r IN
    UPDATE milavn_ticketing.ticket t SET status = 'expired', updated_at = now()
    WHERE t.status = 'awaiting_payment' AND t.hold_expires_at <= now()
    RETURNING t.id, t.occurrence_id, t.member_id, t.kind, t.payment_reference
  LOOP
    IF r.kind = 'waitlist_offer' THEN
      SELECT id INTO p FROM milavn_activity.participation WHERE participation.occurrence_id = r.occurrence_id AND participation.member_id = r.member_id AND status = 'waitlisted';
      IF FOUND THEN
        UPDATE milavn_activity.participation SET status = 'interested', waitlist_position = NULL, updated_at = now() WHERE id = p.id;
        INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
        VALUES (p.id, 'waitlisted', 'interested', r.member_id);
      END IF;
    END IF;
    ticket_id := r.id; occurrence_id := r.occurrence_id; member_id := r.member_id; kind := r.kind; payment_reference := r.payment_reference;
    RETURN NEXT;
  END LOOP;
END;
$$;

-- For a paid activity, a freed spot is OFFERED to the first waitlisted member without an open ticket (they must pay
-- to take it) instead of being assigned outright as for free activities.
CREATE OR REPLACE FUNCTION milavn_ticketing.create_waitlist_offer(p_occurrence_id uuid, p_hold_until timestamptz)
RETURNS TABLE (ticket_id uuid, member_id uuid, amount_paise integer)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE occ record; nxt uuid; tid uuid;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext(p_occurrence_id::text));
  SELECT capacity, price_paise, status::text AS status INTO occ FROM milavn_activity.occurrence WHERE id = p_occurrence_id;
  IF NOT FOUND OR occ.status <> 'active' OR occ.price_paise IS NULL THEN RETURN; END IF;
  IF occ.capacity IS NOT NULL
     AND milavn_activity.going_count(p_occurrence_id) + milavn_activity.held_spot_count(p_occurrence_id) >= occ.capacity THEN
    RETURN;
  END IF;
  SELECT p.member_id INTO nxt FROM milavn_activity.participation p
  WHERE p.occurrence_id = p_occurrence_id AND p.status = 'waitlisted'
    AND NOT EXISTS (SELECT 1 FROM milavn_ticketing.ticket t WHERE t.occurrence_id = p.occurrence_id AND t.member_id = p.member_id
                    AND (t.status IN ('awaiting_payment', 'paid', 'refund_pending')
                         OR (t.kind = 'waitlist_offer' AND t.status IN ('expired', 'failed'))))
  ORDER BY p.waitlist_position ASC LIMIT 1;
  IF nxt IS NULL THEN RETURN; END IF;
  INSERT INTO milavn_ticketing.ticket (occurrence_id, member_id, kind, amount_paise, status, hold_expires_at)
  VALUES (p_occurrence_id, nxt, 'waitlist_offer', occ.price_paise, 'awaiting_payment', p_hold_until)
  RETURNING id INTO tid;
  ticket_id := tid; member_id := nxt; amount_paise := occ.price_paise;
  RETURN NEXT;
END;
$$;

-- Everything that must be settled when an organizer cancels.
CREATE OR REPLACE FUNCTION milavn_ticketing.tickets_to_settle(p_occurrence_id uuid)
RETURNS TABLE (ticket_id uuid, member_id uuid, status text, amount_paise integer, payment_reference text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT id, member_id, status, amount_paise, payment_reference FROM milavn_ticketing.ticket
  WHERE occurrence_id = p_occurrence_id AND status IN ('awaiting_payment', 'paid');
$$;

-- Aggregates only, for the organizer console: never who paid, never who did not.
CREATE OR REPLACE FUNCTION milavn_ticketing.money_summary(p_occurrence_id uuid)
RETURNS TABLE (paid_spots integer, collected_paise bigint, refunds_paise bigint, refunds_pending integer, holds_active integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT
    count(*) FILTER (WHERE status = 'paid')::integer,
    coalesce(sum(amount_paise) FILTER (WHERE status IN ('paid', 'refund_pending', 'refunded')), 0)::bigint,
    coalesce(sum(refund_amount_paise) FILTER (WHERE status IN ('refund_pending', 'refunded')), 0)::bigint,
    count(*) FILTER (WHERE status = 'refund_pending')::integer,
    count(*) FILTER (WHERE status = 'awaiting_payment' AND hold_expires_at > now())::integer
  FROM milavn_ticketing.ticket WHERE occurrence_id = p_occurrence_id;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.held_spot_count(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.open_ticket_count(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.ticket_by_reference(text) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.record_payment_event(text, text, text) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.attach_charge(uuid, text, text) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.mark_paid(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.mark_failed(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.mark_void(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.mark_refund_pending(uuid, integer, text, text) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.mark_refunded(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.expire_holds() TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.create_waitlist_offer(uuid, timestamptz) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.tickets_to_settle(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.money_summary(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_ticketing.offer_context(uuid) TO milavn_app;
