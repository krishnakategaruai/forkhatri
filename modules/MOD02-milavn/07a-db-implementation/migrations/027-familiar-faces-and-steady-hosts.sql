-- 027 — Familiar faces (FR116) and a host who keeps showing up for everyone (FR117).
--
-- WHY (2026-09-17, owner's picks 27 and 20):
--   * Meetup marks people on an attendee list you have been to something with before ("Familiar
--     Faces"), which is exactly the repeated-exposure effect this module's own research rests on
--     (Hall 2019; Reis 2011): the second and third meeting is where an acquaintance becomes a
--     friend, so saying "you have met before" is worth more than any new-people suggestion.
--   * Meetup's 2026 roadmap adds a "Super Organizer" badge for hosts running consistently good
--     groups. Milavn already earns "appreciated host" from real thank-yous; this adds the other
--     half a community actually notices — the host who keeps turning up and rarely cancels.
--
--   familiar_count(viewer, other)   how many activities the two of them have both been to
--   reputation_labels               + 'steady_host' (five or more held, at most one cancellation)

-- Only answers for the member making the request, and only counts activities BOTH were at.
CREATE OR REPLACE FUNCTION milavn_activity.familiar_count(p_viewer uuid, p_other uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT count(*)::integer
  FROM milavn_activity.participation a
  JOIN milavn_activity.participation b ON b.occurrence_id = a.occurrence_id
  JOIN milavn_activity.occurrence o ON o.id = a.occurrence_id
  WHERE a.member_id = p_viewer AND b.member_id = p_other AND p_viewer <> p_other
    AND a.status IN ('checked_in', 'attended') AND b.status IN ('checked_in', 'attended')
    AND o.status = 'active' AND o.time_start < now()
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND NOT milavn_safety.is_blocked_either_way(p_viewer, p_other);
$$;

CREATE OR REPLACE FUNCTION milavn_trust.reputation_labels(p_member_id uuid)
RETURNS text[] LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_trust, pg_catalog AS $$
DECLARE
  completed integer; reliable integer; no_shows integer; cancels integer; contribs integer; identity integer; thanked integer;
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
  SELECT count(*) INTO thanked FROM milavn_trust.thanks WHERE to_member_id = p_member_id;

  IF identity > 0 THEN labels := array_append(labels, 'identity_verified'); END IF;
  -- [FR117] The host the community can count on: five or more activities actually held, and they
  -- almost never cancel. Deliberately NOT a score, a rank or a streak — it is a plain statement
  -- about what they have done, and it disappears again if they start cancelling.
  IF completed >= 5 AND cancels <= 1 THEN labels := array_append(labels, 'steady_host');
  ELSIF completed >= 3 THEN labels := array_append(labels, 'experienced_organizer');
  ELSIF completed >= 1 THEN labels := array_append(labels, 'has_hosted'); END IF;
  IF thanked >= 3 THEN labels := array_append(labels, 'appreciated_host'); END IF;
  IF reliable >= 3 AND no_shows <= 1 THEN labels := array_append(labels, 'reliable_attendee'); END IF;
  IF contribs >= 2 THEN labels := array_append(labels, 'community_contributor'); END IF;
  IF cardinality(labels) = 0 THEN labels := ARRAY['new_to_community']; END IF;
  RETURN labels;
END;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.familiar_count(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_trust.reputation_labels(uuid) TO milavn_app;
