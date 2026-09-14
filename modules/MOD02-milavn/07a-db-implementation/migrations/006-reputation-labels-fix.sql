-- =============================================================================
-- Milavn (MOD02) — migration 006: fix reputation_labels() array building.
-- Run as milavn_owner. Fix-forward (applied migrations are immutable).
--
-- Found live in Step 9: `labels || 'identity_verified'` is parsed by Postgres
-- as text[] || text[]-literal and fails with "malformed array literal" the
-- moment a member has any signal. array_append() is unambiguous.
-- =============================================================================
CREATE OR REPLACE FUNCTION milavn_trust.reputation_labels(p_member_id uuid)
RETURNS text[] LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_trust, pg_catalog AS $$
DECLARE
  completed integer; reliable integer; no_shows integer; cancels integer; contribs integer; identity integer;
  labels text[] := ARRAY[]::text[];
BEGIN
  SELECT count(*) FILTER (WHERE signal_type = 'event_completed'),
         count(*) FILTER (WHERE signal_type = 'attendance_reliable'),
         count(*) FILTER (WHERE signal_type = 'no_show'),
         count(*) FILTER (WHERE signal_type = 'cancellation'),
         count(*) FILTER (WHERE signal_type = 'community_contribution'),
         count(*) FILTER (WHERE signal_type = 'identity_verified')
    INTO completed, reliable, no_shows, cancels, contribs, identity
  FROM milavn_trust.reputation_signal WHERE member_id = p_member_id;

  IF identity > 0 THEN labels := array_append(labels, 'identity_verified'); END IF;
  IF completed >= 3 THEN labels := array_append(labels, 'experienced_organizer');
  ELSIF completed >= 1 THEN labels := array_append(labels, 'has_hosted'); END IF;
  IF reliable >= 3 AND no_shows <= 1 THEN labels := array_append(labels, 'reliable_attendee'); END IF;
  IF contribs >= 2 THEN labels := array_append(labels, 'community_contributor'); END IF;
  IF cardinality(labels) = 0 THEN labels := ARRAY['new_to_community']; END IF;
  RETURN labels;
END;
$$;
