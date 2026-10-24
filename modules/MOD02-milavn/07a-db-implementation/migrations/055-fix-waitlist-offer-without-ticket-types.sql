-- Fix: freeing a spot on a paid event WITHOUT ticket types failed with
-- 'record "tt" is not assigned yet' (the offer insert read tt.id even when there are no types), so the
-- cancelling member got a 500 and the waitlist never got its offer. Same function as 052, corrected.
-- Safe to re-run.

CREATE OR REPLACE FUNCTION milavn_ticketing.create_waitlist_offer(p_occurrence_id uuid, p_hold_until timestamptz)
RETURNS TABLE (ticket_id uuid, member_id uuid, amount_paise integer)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_ticketing, milavn_activity, pg_catalog AS $$
DECLARE occ record; nxt uuid; tid uuid; tt_id uuid; price integer; has_types boolean;
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
    SELECT x.id, x.price_paise INTO tt_id, price FROM milavn_ticketing.ticket_type x
    WHERE x.occurrence_id = p_occurrence_id AND x.active AND milavn_ticketing.type_taken(x.id) < x.quota
    ORDER BY x.price_paise, x.position LIMIT 1;
    IF NOT FOUND THEN RETURN; END IF;
  END IF;
  SELECT p.member_id INTO nxt FROM milavn_activity.participation p
  WHERE p.occurrence_id = p_occurrence_id AND p.status = 'waitlisted'
    AND NOT EXISTS (SELECT 1 FROM milavn_ticketing.ticket t WHERE t.occurrence_id = p.occurrence_id AND t.member_id = p.member_id
                    AND (t.status IN ('awaiting_payment', 'paid', 'refund_pending')
                         OR (t.kind = 'waitlist_offer' AND t.status IN ('expired', 'failed'))))
  ORDER BY p.waitlist_position ASC LIMIT 1;
  IF nxt IS NULL THEN RETURN; END IF;
  INSERT INTO milavn_ticketing.ticket (occurrence_id, member_id, kind, amount_paise, list_price_paise, ticket_type_id, status, hold_expires_at)
  VALUES (p_occurrence_id, nxt, 'waitlist_offer', price, price, tt_id, 'awaiting_payment', p_hold_until)
  RETURNING id INTO tid;
  ticket_id := tid; member_id := nxt; amount_paise := price;
  RETURN NEXT;
END;
$$;

-- Fix: the "x" on a notification (DELETE /notifications/{id}) failed with 500, "permission denied for table
-- notification_inbox_entry": the app role was never granted DELETE. Row level security (self policy) still limits
-- it to the person's own entries.
GRANT DELETE ON milavn_notification.notification_inbox_entry TO milavn_app;
