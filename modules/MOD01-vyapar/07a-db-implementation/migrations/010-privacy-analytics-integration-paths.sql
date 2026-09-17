-- [TR038/TR052 gaps, found during Step 9 design of slice 10 — fixed forward;
-- 001-009 are applied history and are not edited.]
--
-- Gap 1 (FR38): derived_preferences RLS is self-only (member_id = caller).
--   The DETECTION pass that proposes a preference runs as the scheduled
--   dispatcher, on behalf of whichever member the pattern was found for —
--   not the caller's own row. Fix: propose_derived_preference(), gated on
--   service_role='dispatcher', with a 30-day re-propose cooldown enforced
--   in the function itself (never re-inserted while an identical key was
--   declined within 30 days).
-- Gap 2 (FR52): the Dashboard Read Bridge (MOD05) has no member session at
--   all — it is a server-to-server call. Fix: dashboard_summary(), a
--   response-shape ALLOW-LIST (five columns named explicitly, not
--   SELECT * filtered down) so a future listings column can never leak
--   through this bridge without a deliberate change here. Public rows only
--   (Active states), matching FR52(e)'s "no contact, no private intent".
SET search_path TO pg_temp;

CREATE OR REPLACE FUNCTION vyapar_privacy.propose_derived_preference(
  p_member_id text, p_key text, p_value jsonb, p_evidence text, p_source text
) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_privacy, pg_temp AS $$
DECLARE
  v_recent record;
  v_id uuid;
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') <> 'dispatcher' THEN
    RAISE EXCEPTION 'service_role_required';
  END IF;

  -- [FR38] "declined proposal is not re-proposed for 30 days" — checked
  -- against the most recent decision for this exact (member, key), whatever
  -- its outcome; an existing 'proposed' or 'active' row is left alone too,
  -- so this never duplicates an open or already-accepted preference.
  SELECT * INTO v_recent FROM vyapar_privacy.derived_preferences
   WHERE member_id = p_member_id AND key = p_key
   ORDER BY proposed_at DESC LIMIT 1;
  IF v_recent.id IS NOT NULL THEN
    IF v_recent.state IN ('proposed', 'active') THEN RETURN v_recent.id; END IF;
    IF v_recent.state = 'declined' AND v_recent.decided_at > now() - interval '30 days' THEN RETURN NULL; END IF;
  END IF;

  INSERT INTO vyapar_privacy.derived_preferences (member_id, key, value, evidence, source, state)
  VALUES (p_member_id, p_key, p_value, p_evidence, p_source, 'proposed')
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

-- [FR52(e)] "an explicit response-shape allow-list, not a filtered version
-- of the full row" — every column below is named, and nothing else is ever
-- added without touching this function directly.
CREATE OR REPLACE FUNCTION vyapar_listings.dashboard_summary(p_listing_id uuid)
RETURNS TABLE(name text, category text, locality text, verification_state text, freshness text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_listings, pg_temp AS $$
  SELECT l.name, l.categories[1], l.locality, l.verification_state,
         CASE WHEN l.updated_at > now() - interval '7 days' THEN 'active_this_week'
              WHEN l.updated_at > now() - interval '30 days' THEN 'active_this_month'
              ELSE 'inactive' END
    FROM vyapar_listings.listings l
   WHERE l.id = p_listing_id AND l.state IN ('active_unverified', 'active_verified') AND l.discoverable;
$$;

GRANT EXECUTE ON FUNCTION vyapar_privacy.propose_derived_preference(text, text, jsonb, text, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_listings.dashboard_summary(uuid) TO vyapar_app;
