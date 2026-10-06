-- 052 — Large events with tickets (Step 3 of PLAN-places-events-groups.md).
--
-- Adds, on top of the paid spots in 017 (nothing there is rewritten except two functions that now know about ticket types):
--   * a "professional" event category, so professionals' and consulting events are easy to find
--       (work = jobs / co-working / networking, learn = classes: neither says "an expert is speaking", so one value is added)
--   * ticket types per event (Standard, Early bird, VIP ...), each with its own price and quota
--   * discount codes per event (percent or fixed, usage limit, expiry)
--   * on each ticket: the chosen type, the code used, the list price and discount, and a private QR code for entry
--   * the organizer's contact (phone / email), shown after a confirmed booking or to every signed-in member, as the organizer chooses
--
-- Rules live in the database, not only in the screens:
--   * Capacity is one number for the whole event. Every tier's quota is checked on top of it, under the same per-event lock
--     the join and the payment confirmation already use, so two buyers can never take the last seat of a tier or of the event.
--   * A code never takes a price below Rs 1 (a ticket with no payment is a free join, which is a different flow).
--   * Ticket types and codes are written only by the organizer or a co-organizer (definer functions, same check as the venue).
--   * The QR code is read only by its owner (ticket RLS) and by the organizer's check-in function.

ALTER TYPE milavn_activity.intent_category ADD VALUE IF NOT EXISTS 'professional';

-- ---------------------------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS milavn_ticketing.ticket_type (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id uuid NOT NULL,                       -- cross-schema ref -> milavn_activity.occurrence(id), no FK (§4)
  name          text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 60),
  price_paise   integer NOT NULL CHECK (price_paise BETWEEN 100 AND 10000000),
  quota         integer NOT NULL CHECK (quota BETWEEN 1 AND 100000),
  position      integer NOT NULL DEFAULT 0,
  active        boolean NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ticket_type_name_unique ON milavn_ticketing.ticket_type (occurrence_id, lower(btrim(name)));
CREATE INDEX IF NOT EXISTS ticket_type_occurrence_idx ON milavn_ticketing.ticket_type (occurrence_id, position);

CREATE TABLE IF NOT EXISTS milavn_ticketing.discount_code (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id uuid NOT NULL,
  code          text NOT NULL CHECK (code ~ '^[A-Z0-9_-]{3,24}$'),
  kind          text NOT NULL CHECK (kind IN ('percent', 'fixed')),
  value         integer NOT NULL CHECK (value > 0),    -- percent: 1..90 ; fixed: paise, at least 100
  max_uses      integer CHECK (max_uses IS NULL OR max_uses BETWEEN 1 AND 100000),
  expires_at    timestamptz,
  active        boolean NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT discount_code_value_range CHECK ((kind = 'percent' AND value BETWEEN 1 AND 90) OR (kind = 'fixed' AND value BETWEEN 100 AND 10000000))
);
CREATE UNIQUE INDEX IF NOT EXISTS discount_code_unique ON milavn_ticketing.discount_code (occurrence_id, code);

ALTER TABLE milavn_ticketing.ticket_type ENABLE ROW LEVEL SECURITY;   -- no policy: definer functions only
ALTER TABLE milavn_ticketing.discount_code ENABLE ROW LEVEL SECURITY; -- no policy: definer functions only

ALTER TABLE milavn_ticketing.ticket
  ADD COLUMN IF NOT EXISTS ticket_type_id   uuid,
  ADD COLUMN IF NOT EXISTS discount_code_id uuid,
  ADD COLUMN IF NOT EXISTS list_price_paise integer,
  ADD COLUMN IF NOT EXISTS discount_paise   integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS qr_code          text NOT NULL DEFAULT substr(replace(gen_random_uuid()::text, '-', ''), 1, 20);
CREATE UNIQUE INDEX IF NOT EXISTS ticket_qr_code_unique ON milavn_ticketing.ticket (qr_code);
CREATE INDEX IF NOT EXISTS ticket_type_tickets_idx ON milavn_ticketing.ticket (ticket_type_id) WHERE ticket_type_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ticket_discount_code_idx ON milavn_ticketing.ticket (discount_code_id) WHERE discount_code_id IS NOT NULL;

-- ---------------------------------------------------------------------------------------------------------------------
-- Counting. A ticket takes a seat of its type while it is paid, being refunded, or held for someone who is paying right now.
CREATE OR REPLACE FUNCTION milavn_ticketing.type_taken(p_type_id uuid, p_except uuid DEFAULT NULL)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT count(*)::integer FROM milavn_ticketing.ticket t
  WHERE t.ticket_type_id = p_type_id AND (p_except IS NULL OR t.id <> p_except)
    AND (t.status IN ('paid', 'refund_pending') OR (t.status = 'awaiting_payment' AND t.hold_expires_at > now()));
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.code_uses(p_code_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT count(*)::integer FROM milavn_ticketing.ticket t
  WHERE t.discount_code_id = p_code_id
    AND (t.status IN ('paid', 'refund_pending') OR (t.status = 'awaiting_payment' AND t.hold_expires_at > now()));
$$;

-- What a member sees on the event page: every ticket type with how many are left. Safe for any signed-in member.
CREATE OR REPLACE FUNCTION milavn_ticketing.ticket_types_for(p_occurrence_id uuid)
RETURNS TABLE (id uuid, name text, price_paise integer, quota integer, taken integer, active boolean, pos integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, pg_catalog AS $$
  SELECT tt.id, tt.name, tt.price_paise, tt.quota, milavn_ticketing.type_taken(tt.id), tt.active, tt.position
  FROM milavn_ticketing.ticket_type tt WHERE tt.occurrence_id = p_occurrence_id ORDER BY tt.position, tt.created_at;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
-- Price for one booking, in one place (used for the preview and again, under the event lock, when the hold is made).
-- error: NULL | 'not_paid' | 'type_required' | 'no_type' | 'sold_out' | 'code_invalid' | 'code_expired' | 'code_used_up'
CREATE OR REPLACE FUNCTION milavn_ticketing.quote_ticket(p_occurrence_id uuid, p_type_id uuid, p_code text)
RETURNS TABLE (error text, ticket_type_id uuid, list_price_paise integer, discount_paise integer, amount_paise integer, discount_code_id uuid)
LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE
  occ_price integer; tt record; dc record; list integer; disc integer := 0; final integer; norm text;
  has_types boolean;
BEGIN
  SELECT o.price_paise INTO occ_price FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
  has_types := EXISTS (SELECT 1 FROM milavn_ticketing.ticket_type x WHERE x.occurrence_id = p_occurrence_id);
  ticket_type_id := NULL; discount_code_id := NULL;
  IF has_types THEN
    IF p_type_id IS NULL THEN error := 'type_required'; RETURN NEXT; RETURN; END IF;
    SELECT * INTO tt FROM milavn_ticketing.ticket_type x WHERE x.id = p_type_id AND x.occurrence_id = p_occurrence_id AND x.active;
    IF NOT FOUND THEN error := 'no_type'; RETURN NEXT; RETURN; END IF;
    IF milavn_ticketing.type_taken(tt.id) >= tt.quota THEN error := 'sold_out'; RETURN NEXT; RETURN; END IF;
    list := tt.price_paise; ticket_type_id := tt.id;
  ELSE
    IF p_type_id IS NOT NULL THEN error := 'no_type'; RETURN NEXT; RETURN; END IF;
    IF occ_price IS NULL THEN error := 'not_paid'; RETURN NEXT; RETURN; END IF;
    list := occ_price;
  END IF;
  norm := upper(btrim(coalesce(p_code, '')));
  IF norm <> '' THEN
    SELECT * INTO dc FROM milavn_ticketing.discount_code c WHERE c.occurrence_id = p_occurrence_id AND c.code = norm AND c.active;
    IF NOT FOUND THEN error := 'code_invalid'; RETURN NEXT; RETURN; END IF;
    IF dc.expires_at IS NOT NULL AND dc.expires_at <= now() THEN error := 'code_expired'; RETURN NEXT; RETURN; END IF;
    IF dc.max_uses IS NOT NULL AND milavn_ticketing.code_uses(dc.id) >= dc.max_uses THEN error := 'code_used_up'; RETURN NEXT; RETURN; END IF;
    disc := CASE WHEN dc.kind = 'percent' THEN (list::bigint * dc.value / 100)::integer ELSE dc.value END;
    discount_code_id := dc.id;
  END IF;
  final := greatest(list - disc, 100);         -- never below Rs 1: a free ticket is a different flow
  error := NULL; list_price_paise := list; discount_paise := list - final; amount_paise := final;
  RETURN NEXT;
END;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
-- Organizer writes. Result text: 'ok' | 'not_allowed' | 'not_found' | 'cancelled' | 'locked' | 'quota_below_sold' | 'too_many' | 'duplicate'
-- After any change the event's own price is the cheapest active ticket ("from"), so the existing paid-spot flow keeps working.
CREATE OR REPLACE FUNCTION milavn_ticketing.sync_event_price(p_occurrence_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE cheapest integer;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM milavn_ticketing.ticket_type WHERE occurrence_id = p_occurrence_id) THEN RETURN; END IF;
  SELECT min(price_paise) INTO cheapest FROM milavn_ticketing.ticket_type WHERE occurrence_id = p_occurrence_id AND active;
  IF cheapest IS NOT NULL THEN
    UPDATE milavn_activity.occurrence SET price_paise = cheapest, updated_at = now() WHERE id = p_occurrence_id AND price_paise IS DISTINCT FROM cheapest;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.organizer_gate(p_occurrence_id uuid, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE st text;
BEGIN
  IF p_actor IS NULL OR p_actor IS DISTINCT FROM nullif(current_setting('milavn.member_id', true), '')::uuid THEN RETURN 'not_allowed'; END IF;
  SELECT status::text INTO st FROM milavn_activity.occurrence WHERE id = p_occurrence_id;
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  IF NOT milavn_activity.is_event_organizer(p_occurrence_id, p_actor) THEN RETURN 'not_allowed'; END IF;
  IF st = 'cancelled' THEN RETURN 'cancelled'; END IF;
  RETURN 'ok';
END;
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.save_ticket_type(p_occurrence_id uuid, p_actor uuid, p_id uuid, p_name text, p_price integer, p_quota integer, p_active boolean)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE gate text; cur record; n integer; taken integer;
BEGIN
  gate := milavn_ticketing.organizer_gate(p_occurrence_id, p_actor);
  IF gate <> 'ok' THEN RETURN gate; END IF;
  PERFORM pg_advisory_xact_lock(hashtext(p_occurrence_id::text));
  IF p_id IS NULL THEN
    SELECT count(*) INTO n FROM milavn_ticketing.ticket_type WHERE occurrence_id = p_occurrence_id;
    IF n >= 8 THEN RETURN 'too_many'; END IF;
    BEGIN
      INSERT INTO milavn_ticketing.ticket_type (occurrence_id, name, price_paise, quota, position, active)
      VALUES (p_occurrence_id, btrim(p_name), p_price, p_quota, n, coalesce(p_active, true));
    EXCEPTION WHEN unique_violation THEN RETURN 'duplicate';
    END;
  ELSE
    SELECT * INTO cur FROM milavn_ticketing.ticket_type WHERE id = p_id AND occurrence_id = p_occurrence_id FOR UPDATE;
    IF NOT FOUND THEN RETURN 'not_found'; END IF;
    taken := milavn_ticketing.type_taken(p_id);
    -- Anyone paying or paid keeps the price they saw; the quota can grow, or shrink down to what is already taken.
    IF taken > 0 AND p_price IS DISTINCT FROM cur.price_paise THEN RETURN 'locked'; END IF;
    IF p_quota < taken THEN RETURN 'quota_below_sold'; END IF;
    BEGIN
      UPDATE milavn_ticketing.ticket_type SET name = btrim(p_name), price_paise = p_price, quota = p_quota, active = coalesce(p_active, active) WHERE id = p_id;
    EXCEPTION WHEN unique_violation THEN RETURN 'duplicate';
    END;
  END IF;
  PERFORM milavn_ticketing.sync_event_price(p_occurrence_id);
  RETURN 'ok';
END;
$$;

-- A type nobody ever booked is removed; one with bookings is only switched off (stops new sales, keeps every ticket's record).
CREATE OR REPLACE FUNCTION milavn_ticketing.remove_ticket_type(p_occurrence_id uuid, p_actor uuid, p_id uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE gate text;
BEGIN
  gate := milavn_ticketing.organizer_gate(p_occurrence_id, p_actor);
  IF gate <> 'ok' AND gate <> 'cancelled' THEN RETURN gate; END IF;
  PERFORM pg_advisory_xact_lock(hashtext(p_occurrence_id::text));
  IF NOT EXISTS (SELECT 1 FROM milavn_ticketing.ticket_type WHERE id = p_id AND occurrence_id = p_occurrence_id) THEN RETURN 'not_found'; END IF;
  IF EXISTS (SELECT 1 FROM milavn_ticketing.ticket WHERE ticket_type_id = p_id) THEN
    UPDATE milavn_ticketing.ticket_type SET active = false WHERE id = p_id;
  ELSE
    DELETE FROM milavn_ticketing.ticket_type WHERE id = p_id;
    -- The last type gone and nobody mid-payment: the event goes back to the price it had no tickets for (free).
    IF NOT EXISTS (SELECT 1 FROM milavn_ticketing.ticket_type WHERE occurrence_id = p_occurrence_id)
       AND milavn_ticketing.open_ticket_count(p_occurrence_id) = 0 THEN
      UPDATE milavn_activity.occurrence SET price_paise = NULL, updated_at = now() WHERE id = p_occurrence_id;
    END IF;
  END IF;
  PERFORM milavn_ticketing.sync_event_price(p_occurrence_id);
  RETURN 'ok';
END;
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.save_discount_code(p_occurrence_id uuid, p_actor uuid, p_code text, p_kind text, p_value integer, p_max_uses integer, p_expires_at timestamptz)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE gate text; n integer; norm text := upper(btrim(coalesce(p_code, '')));
BEGIN
  gate := milavn_ticketing.organizer_gate(p_occurrence_id, p_actor);
  IF gate <> 'ok' THEN RETURN gate; END IF;
  SELECT count(*) INTO n FROM milavn_ticketing.discount_code WHERE occurrence_id = p_occurrence_id;
  IF n >= 20 THEN RETURN 'too_many'; END IF;
  BEGIN
    INSERT INTO milavn_ticketing.discount_code (occurrence_id, code, kind, value, max_uses, expires_at) VALUES (p_occurrence_id, norm, p_kind, p_value, p_max_uses, p_expires_at);
  EXCEPTION WHEN unique_violation THEN RETURN 'duplicate';
            WHEN check_violation THEN RETURN 'invalid';
  END;
  RETURN 'ok';
END;
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.set_discount_active(p_occurrence_id uuid, p_actor uuid, p_id uuid, p_active boolean)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE gate text;
BEGIN
  gate := milavn_ticketing.organizer_gate(p_occurrence_id, p_actor);
  IF gate <> 'ok' AND gate <> 'cancelled' THEN RETURN gate; END IF;
  UPDATE milavn_ticketing.discount_code SET active = p_active WHERE id = p_id AND occurrence_id = p_occurrence_id;
  IF NOT FOUND THEN RETURN 'not_found'; END IF;
  RETURN 'ok';
END;
$$;

-- Organizer-only reads: the codes with their use, and sales per type. Counts only; never who bought.
CREATE OR REPLACE FUNCTION milavn_ticketing.discount_codes_for(p_occurrence_id uuid, p_actor uuid)
RETURNS TABLE (id uuid, code text, kind text, value integer, max_uses integer, expires_at timestamptz, active boolean, uses integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
  SELECT c.id, c.code, c.kind, c.value, c.max_uses, c.expires_at, c.active, milavn_ticketing.code_uses(c.id)
  FROM milavn_ticketing.discount_code c
  WHERE c.occurrence_id = p_occurrence_id
    AND p_actor IS NOT DISTINCT FROM nullif(current_setting('milavn.member_id', true), '')::uuid
    AND milavn_activity.is_event_organizer(p_occurrence_id, p_actor)
  ORDER BY c.created_at;
$$;

CREATE OR REPLACE FUNCTION milavn_ticketing.sales_by_type(p_occurrence_id uuid, p_actor uuid)
RETURNS TABLE (ticket_type_id uuid, name text, price_paise integer, quota integer, active boolean, sold integer, held integer, checked_in integer, revenue_paise bigint)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
  SELECT tt.id, tt.name, tt.price_paise, tt.quota, tt.active,
         count(t.id) FILTER (WHERE t.status = 'paid')::integer,
         count(t.id) FILTER (WHERE t.status = 'awaiting_payment' AND t.hold_expires_at > now())::integer,
         count(t.id) FILTER (WHERE t.status = 'paid' AND p.status IN ('checked_in', 'attended'))::integer,
         coalesce(sum(t.amount_paise) FILTER (WHERE t.status = 'paid'), 0)::bigint
  FROM milavn_ticketing.ticket_type tt
  LEFT JOIN milavn_ticketing.ticket t ON t.ticket_type_id = tt.id
  LEFT JOIN milavn_activity.participation p ON p.occurrence_id = t.occurrence_id AND p.member_id = t.member_id
  WHERE tt.occurrence_id = p_occurrence_id
    AND p_actor IS NOT DISTINCT FROM nullif(current_setting('milavn.member_id', true), '')::uuid
    AND milavn_activity.is_event_organizer(p_occurrence_id, p_actor)
  GROUP BY tt.id ORDER BY tt.position, tt.created_at;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
-- Check-in by ticket: the organizer scans (or types) the attendee's QR code.
-- Returns the ticket holder and where the ticket stands; 'wrong_event' / 'not_found' leak nothing about other events.
CREATE OR REPLACE FUNCTION milavn_ticketing.ticket_for_checkin(p_occurrence_id uuid, p_actor uuid, p_code text)
RETURNS TABLE (result text, member_id uuid, type_name text, participation_status text)
LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE t record; ps text; tn text;
BEGIN
  IF p_actor IS NULL OR p_actor IS DISTINCT FROM nullif(current_setting('milavn.member_id', true), '')::uuid
     OR NOT milavn_activity.is_event_organizer(p_occurrence_id, p_actor) THEN
    result := 'not_allowed'; RETURN NEXT; RETURN;
  END IF;
  SELECT x.id, x.occurrence_id, x.member_id, x.status, x.ticket_type_id INTO t FROM milavn_ticketing.ticket x WHERE x.qr_code = lower(btrim(p_code));
  IF NOT FOUND OR t.occurrence_id <> p_occurrence_id THEN result := 'not_found'; RETURN NEXT; RETURN; END IF;
  SELECT name INTO tn FROM milavn_ticketing.ticket_type WHERE id = t.ticket_type_id;
  SELECT p.status::text INTO ps FROM milavn_activity.participation p WHERE p.occurrence_id = t.occurrence_id AND p.member_id = t.member_id;
  result := CASE WHEN t.status = 'paid' THEN 'ok' ELSE 'not_valid' END;
  member_id := t.member_id; type_name := tn; participation_status := ps;
  RETURN NEXT;
END;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
-- The two 017 functions that now respect ticket types (everything else in them is unchanged).

-- A payment succeeded after the hold lapsed: the event capacity AND the ticket type's quota must still have room.
CREATE OR REPLACE FUNCTION milavn_ticketing.mark_paid(p_ticket_id uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE
  t milavn_ticketing.ticket%ROWTYPE;
  occ record;
  p record;
  hold_valid boolean;
  tier_full boolean := false;
BEGIN
  SELECT * INTO t FROM milavn_ticketing.ticket WHERE id = p_ticket_id FOR UPDATE;
  IF NOT FOUND THEN RETURN 'missing'; END IF;
  IF t.status = 'paid' THEN RETURN 'already'; END IF;
  IF t.status NOT IN ('awaiting_payment', 'expired', 'failed') THEN RETURN 'ignored'; END IF;
  PERFORM pg_advisory_xact_lock(hashtext(t.occurrence_id::text));
  SELECT capacity, status::text AS status INTO occ FROM milavn_activity.occurrence WHERE id = t.occurrence_id;
  hold_valid := t.status = 'awaiting_payment' AND t.hold_expires_at > now();
  IF t.ticket_type_id IS NOT NULL AND NOT hold_valid THEN
    tier_full := milavn_ticketing.type_taken(t.ticket_type_id, t.id) >= (SELECT quota FROM milavn_ticketing.ticket_type WHERE id = t.ticket_type_id);
  END IF;
  UPDATE milavn_ticketing.ticket SET status = 'paid', paid_at = now(), hold_expires_at = NULL, updated_at = now() WHERE id = t.id;
  IF occ.status = 'cancelled' THEN RETURN 'refund_cancelled'; END IF;
  IF NOT hold_valid AND (
       tier_full OR (occ.capacity IS NOT NULL
                     AND milavn_activity.going_count(t.occurrence_id) + milavn_activity.held_spot_count(t.occurrence_id) >= occ.capacity)) THEN
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

-- A freed seat on a ticketed event is offered at the cheapest ticket type that still has room.
CREATE OR REPLACE FUNCTION milavn_ticketing.create_waitlist_offer(p_occurrence_id uuid, p_hold_until timestamptz)
RETURNS TABLE (ticket_id uuid, member_id uuid, amount_paise integer)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE occ record; nxt uuid; tid uuid; tt record; price integer; has_types boolean;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext(p_occurrence_id::text));
  SELECT capacity, price_paise, status::text AS status INTO occ FROM milavn_activity.occurrence WHERE id = p_occurrence_id;
  IF NOT FOUND OR occ.status <> 'active' OR occ.price_paise IS NULL THEN RETURN; END IF;
  IF occ.capacity IS NOT NULL
     AND milavn_activity.going_count(p_occurrence_id) + milavn_activity.held_spot_count(p_occurrence_id) >= occ.capacity THEN
    RETURN;
  END IF;
  has_types := EXISTS (SELECT 1 FROM milavn_ticketing.ticket_type x WHERE x.occurrence_id = p_occurrence_id);
  price := occ.price_paise;
  IF has_types THEN
    SELECT x.id, x.price_paise INTO tt FROM milavn_ticketing.ticket_type x
    WHERE x.occurrence_id = p_occurrence_id AND x.active AND milavn_ticketing.type_taken(x.id) < x.quota
    ORDER BY x.price_paise, x.position LIMIT 1;
    IF NOT FOUND THEN RETURN; END IF;
    price := tt.price_paise;
  END IF;
  SELECT p.member_id INTO nxt FROM milavn_activity.participation p
  WHERE p.occurrence_id = p_occurrence_id AND p.status = 'waitlisted'
    AND NOT EXISTS (SELECT 1 FROM milavn_ticketing.ticket t WHERE t.occurrence_id = p.occurrence_id AND t.member_id = p.member_id
                    AND (t.status IN ('awaiting_payment', 'paid', 'refund_pending')
                         OR (t.kind = 'waitlist_offer' AND t.status IN ('expired', 'failed'))))
  ORDER BY p.waitlist_position ASC LIMIT 1;
  IF nxt IS NULL THEN RETURN; END IF;
  INSERT INTO milavn_ticketing.ticket (occurrence_id, member_id, kind, amount_paise, list_price_paise, ticket_type_id, status, hold_expires_at)
  VALUES (p_occurrence_id, nxt, 'waitlist_offer', price, price, CASE WHEN has_types THEN tt.id END, 'awaiting_payment', p_hold_until)
  RETURNING id INTO tid;
  ticket_id := tid; member_id := nxt; amount_paise := price;
  RETURN NEXT;
END;
$$;

-- ---------------------------------------------------------------------------------------------------------------------
-- Organizer contact. Either of phone and email may be empty. The organizer chooses who sees it:
--   'confirmed' (default)  organizers and people with a confirmed spot (a paid ticket makes the spot 'going')
--   'public'               any signed-in member
-- offer_counsel: show the "book a one-to-one with this expert" link (the URL itself comes from configuration, never from here).
CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_contact (
  occurrence_id uuid PRIMARY KEY REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  phone         text CHECK (phone IS NULL OR phone ~ '^\+?[0-9 ()-]{7,20}$'),
  email         text CHECK (email IS NULL OR (length(email) <= 120 AND email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$')),
  visibility    text NOT NULL DEFAULT 'confirmed' CHECK (visibility IN ('confirmed', 'public')),
  offer_counsel boolean NOT NULL DEFAULT false,
  updated_at    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE milavn_activity.occurrence_contact IS
  'Organizer phone / email for a large event. Readable by organizers and, per the organizer''s choice, by confirmed attendees or any signed-in member (RLS below); never part of a public read.';
ALTER TABLE milavn_activity.occurrence_contact ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_contact_by_choice ON milavn_activity.occurrence_contact;
CREATE POLICY occurrence_contact_by_choice ON milavn_activity.occurrence_contact
  FOR SELECT USING (
    nullif(current_setting('milavn.member_id', true), '') IS NOT NULL
    AND (visibility = 'public' OR milavn_activity.can_see_venue(occurrence_id, nullif(current_setting('milavn.member_id', true), '')::uuid))
  );
GRANT SELECT ON milavn_activity.occurrence_contact TO milavn_app;

CREATE OR REPLACE FUNCTION milavn_activity.set_event_contact(p_occurrence_id uuid, p_actor uuid, p_phone text, p_email text, p_visibility text, p_offer_counsel boolean)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM nullif(current_setting('milavn.member_id', true), '')::uuid THEN RETURN 'not_allowed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM milavn_activity.occurrence WHERE id = p_occurrence_id) THEN RETURN 'not_found'; END IF;
  IF NOT milavn_activity.is_event_organizer(p_occurrence_id, p_actor) THEN RETURN 'not_allowed'; END IF;
  INSERT INTO milavn_activity.occurrence_contact (occurrence_id, phone, email, visibility, offer_counsel)
  VALUES (p_occurrence_id, nullif(btrim(p_phone), ''), nullif(btrim(p_email), ''), coalesce(p_visibility, 'confirmed'), coalesce(p_offer_counsel, false))
  ON CONFLICT (occurrence_id) DO UPDATE
    SET phone = EXCLUDED.phone, email = EXCLUDED.email, visibility = EXCLUDED.visibility, offer_counsel = EXCLUDED.offer_counsel, updated_at = now();
  RETURN 'ok';
EXCEPTION WHEN check_violation THEN RETURN 'invalid';
END;
$$;

-- The organizer's "book a one-to-one" switch is public information (the link itself is configuration), so it is readable on its own.
CREATE OR REPLACE FUNCTION milavn_activity.offers_counsel(p_occurrence_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT coalesce((SELECT offer_counsel FROM milavn_activity.occurrence_contact WHERE occurrence_id = p_occurrence_id), false);
$$;

-- ---------------------------------------------------------------------------------------------------------------------
REVOKE ALL ON FUNCTION milavn_ticketing.type_taken(uuid, uuid), milavn_ticketing.code_uses(uuid), milavn_ticketing.ticket_types_for(uuid),
  milavn_ticketing.quote_ticket(uuid, uuid, text), milavn_ticketing.sync_event_price(uuid), milavn_ticketing.organizer_gate(uuid, uuid),
  milavn_ticketing.save_ticket_type(uuid, uuid, uuid, text, integer, integer, boolean), milavn_ticketing.remove_ticket_type(uuid, uuid, uuid),
  milavn_ticketing.save_discount_code(uuid, uuid, text, text, integer, integer, timestamptz), milavn_ticketing.set_discount_active(uuid, uuid, uuid, boolean),
  milavn_ticketing.discount_codes_for(uuid, uuid), milavn_ticketing.sales_by_type(uuid, uuid), milavn_ticketing.ticket_for_checkin(uuid, uuid, text),
  milavn_activity.set_event_contact(uuid, uuid, text, text, text, boolean), milavn_activity.offers_counsel(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_ticketing.ticket_types_for(uuid), milavn_ticketing.quote_ticket(uuid, uuid, text),
  milavn_ticketing.save_ticket_type(uuid, uuid, uuid, text, integer, integer, boolean), milavn_ticketing.remove_ticket_type(uuid, uuid, uuid),
  milavn_ticketing.save_discount_code(uuid, uuid, text, text, integer, integer, timestamptz), milavn_ticketing.set_discount_active(uuid, uuid, uuid, boolean),
  milavn_ticketing.discount_codes_for(uuid, uuid), milavn_ticketing.sales_by_type(uuid, uuid), milavn_ticketing.ticket_for_checkin(uuid, uuid, text),
  milavn_activity.set_event_contact(uuid, uuid, text, text, text, boolean), milavn_activity.offers_counsel(uuid) TO milavn_app;
-- mark_paid / create_waitlist_offer keep the grants they got in 017 (CREATE OR REPLACE preserves them).

-- Whether the organizer has shared contact details, and with whom, without revealing them: lets a member's screen say
-- "the organizer's phone and email appear once your booking is confirmed" only when that is true.
CREATE OR REPLACE FUNCTION milavn_activity.contact_visibility(p_occurrence_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT visibility FROM milavn_activity.occurrence_contact WHERE occurrence_id = p_occurrence_id AND (phone IS NOT NULL OR email IS NOT NULL);
$$;
REVOKE ALL ON FUNCTION milavn_activity.contact_visibility(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_activity.contact_visibility(uuid) TO milavn_app;
