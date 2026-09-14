-- =============================================================================
-- Milavn (MOD02) — migration 002: RLS-safe read-model helpers.
-- Run as milavn_owner (the table owner), same as 001.
--
-- Why this exists (found during Step 9 implementation, not on paper):
--   * FR006 requires every Discovery card to answer "how many are going", and
--     FR008 names "3 people from your circles are going" as a legitimate
--     "why this?" reason. But `milavn_activity.participation`'s RLS policy
--     (FR040, private attendance by default) correctly hides every OTHER
--     member's participation row from an ordinary viewer — so a plain
--     COUNT(*) as milavn_app returns only the viewer's own row.
--   * FR037/TR28 require reputation to surface QUALITATIVELY while
--     `milavn_trust.reputation_signal` is internal-only (zero rows for any
--     ordinary request).
--
-- Both are aggregate, non-identifying facts. The same SECURITY DEFINER
-- pattern migration 001 already uses for `milavn_circle.is_active_member`
-- resolves them without weakening any row-level policy: the functions run
-- as the owning role, return only a count / a qualitative label, and never
-- expose which member is behind a row. This is infrastructure required to
-- implement already-cited requirements (FR006/FR008/FR037), not new scope —
-- recorded in 07a-er-model.md's revision log and 09-implementation.md.
-- =============================================================================

-- [FR006] "How many are going" — count only.
CREATE OR REPLACE FUNCTION milavn_activity.going_count(p_occurrence_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT count(*)::integer FROM milavn_activity.participation
  WHERE occurrence_id = p_occurrence_id AND status IN ('going','checked_in','attended');
$$;

-- [FR006] "Interested" count — shown alongside going.
CREATE OR REPLACE FUNCTION milavn_activity.interested_count(p_occurrence_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT count(*)::integer FROM milavn_activity.participation
  WHERE occurrence_id = p_occurrence_id AND status = 'interested';
$$;

-- [FR008] "N people from your circles are going" — a count, never identities.
CREATE OR REPLACE FUNCTION milavn_activity.circle_peers_going(p_occurrence_id uuid, p_member_id uuid)
RETURNS integer LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, milavn_circle, pg_catalog AS $$
  SELECT count(DISTINCT p.member_id)::integer
  FROM milavn_activity.participation p
  WHERE p.occurrence_id = p_occurrence_id
    AND p.status IN ('going','checked_in','attended','interested')
    AND p.member_id <> p_member_id
    AND EXISTS (
      SELECT 1 FROM milavn_circle.circle_membership a
      JOIN milavn_circle.circle_membership b ON a.circle_id = b.circle_id
      WHERE a.member_id = p_member_id AND a.left_at IS NULL
        AND b.member_id = p.member_id AND b.left_at IS NULL
    );
$$;

-- [FR024] Community memory: aggregate stats a circle's members may see.
CREATE OR REPLACE FUNCTION milavn_circle.community_memory(p_circle_id uuid)
RETURNS TABLE(member_count integer, activities_held integer, upcoming_count integer, first_activity_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, milavn_activity, pg_catalog AS $$
  SELECT
    (SELECT count(*)::integer FROM milavn_circle.circle_membership WHERE circle_id = p_circle_id AND left_at IS NULL),
    (SELECT count(*)::integer FROM milavn_activity.occurrence WHERE circle_id = p_circle_id AND status = 'active' AND time_start < now()),
    (SELECT count(*)::integer FROM milavn_activity.occurrence WHERE circle_id = p_circle_id AND status = 'active' AND time_start >= now()),
    (SELECT min(time_start) FROM milavn_activity.occurrence WHERE circle_id = p_circle_id AND status = 'active');
$$;

-- [FR034/FR037/TR28] Qualitative reputation — the ONLY way a request may
-- observe reputation. Returns labels, never the underlying score.
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

  IF identity > 0 THEN labels := labels || 'identity_verified'; END IF;
  IF completed >= 3 THEN labels := labels || 'experienced_organizer'; ELSIF completed >= 1 THEN labels := labels || 'has_hosted'; END IF;
  IF reliable >= 3 AND no_shows <= 1 THEN labels := labels || 'reliable_attendee'; END IF;
  IF contribs >= 2 THEN labels := labels || 'community_contributor'; END IF;
  IF cardinality(labels) = 0 THEN labels := ARRAY['new_to_community']; END IF;
  RETURN labels;
END;
$$;

-- [FR034] Internal writer for named behaviours — only called by the
-- application's own reputation path (a request never reads this table).
CREATE OR REPLACE FUNCTION milavn_trust.record_signal(p_member_id uuid, p_signal text, p_occurrence_id uuid, p_weight numeric)
RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_trust, pg_catalog AS $$
  INSERT INTO milavn_trust.reputation_signal (member_id, signal_type, source_occurrence_id, weight)
  VALUES (p_member_id, p_signal::milavn_trust.reputation_signal_type, p_occurrence_id, p_weight);
$$;

-- [FR062] Shared block check — usable from either side without exposing the
-- other party's block list (block RLS is blocking-member-only).
CREATE OR REPLACE FUNCTION milavn_safety.is_blocked_either_way(p_a uuid, p_b uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_safety, pg_catalog AS $$
  SELECT EXISTS (
    SELECT 1 FROM milavn_safety.block
    WHERE (blocking_member_id = p_a AND blocked_member_id = p_b)
       OR (blocking_member_id = p_b AND blocked_member_id = p_a)
  );
$$;

-- [FR022] Co-participation pairs for the circle-formation suggestion job.
CREATE OR REPLACE FUNCTION milavn_circle.co_participation_pairs(p_min_shared integer)
RETURNS TABLE(member_a uuid, member_b uuid, shared_count integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT a.member_id, b.member_id, count(*)::integer
  FROM milavn_activity.participation a
  JOIN milavn_activity.participation b
    ON a.occurrence_id = b.occurrence_id AND a.member_id < b.member_id
  WHERE a.status IN ('attended','checked_in','going') AND b.status IN ('attended','checked_in','going')
  GROUP BY a.member_id, b.member_id
  HAVING count(*) >= p_min_shared;
$$;

-- [FR056/FR057/FR017] Participant member ids for an occurrence — organizer
-- tooling and Notification Dispatch use this from the owning component only.
CREATE OR REPLACE FUNCTION milavn_activity.participant_member_ids(p_occurrence_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT coalesce(array_agg(member_id), ARRAY[]::uuid[]) FROM milavn_activity.participation
  WHERE occurrence_id = p_occurrence_id AND status IN ('interested','going','waitlisted','checked_in');
$$;

-- [FR053] Notification Dispatch writes inbox rows for OTHER members after an
-- event commits; the inbox table's RLS is member-self-only, so the dispatcher
-- needs a definer-owned insert path.
CREATE OR REPLACE FUNCTION milavn_notification.deliver(
  p_member_id uuid, p_class text, p_title text, p_body text, p_deep_link text, p_occurrence_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_notification, pg_catalog AS $$
DECLARE muted_pref boolean;
BEGIN
  SELECT muted INTO muted_pref FROM milavn_notification.notification_preference
   WHERE member_id = p_member_id AND notification_class = p_class::milavn_notification.notification_class;
  -- [FR051] Important is never suppressible; other classes honour the preference.
  IF p_class <> 'important' AND coalesce(muted_pref, false) THEN RETURN; END IF;
  INSERT INTO milavn_notification.notification_inbox_entry (member_id, notification_class, title, body, deep_link, source_occurrence_id)
  VALUES (p_member_id, p_class::milavn_notification.notification_class, p_title, p_body, p_deep_link, p_occurrence_id);
  INSERT INTO milavn_notification.notification_outbox (member_id, notification_class, payload)
  VALUES (p_member_id, p_class::milavn_notification.notification_class,
          jsonb_build_object('title', p_title, 'body', p_body, 'deep_link', p_deep_link, 'occurrence_id', p_occurrence_id));
END;
$$;

-- [FR030] Default trust status for a new occurrence, and organizer-level
-- resolution used by Trust & Reputation.
CREATE OR REPLACE FUNCTION milavn_trust.ensure_default_trust(p_subject_type text, p_subject_id uuid, p_level text)
RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_trust, pg_catalog AS $$
  INSERT INTO milavn_trust.trust_status (subject_type, subject_id, trust_level)
  VALUES (p_subject_type::milavn_trust.trust_subject_type, p_subject_id, p_level::milavn_trust.trust_level)
  ON CONFLICT (subject_type, subject_id) DO NOTHING;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.going_count(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.interested_count(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.circle_peers_going(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.participant_member_ids(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.community_memory(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.co_participation_pairs(integer) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_trust.reputation_labels(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_trust.record_signal(uuid, text, uuid, numeric) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_trust.ensure_default_trust(text, uuid, text) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_safety.is_blocked_either_way(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_notification.deliver(uuid, text, text, text, text, uuid) TO milavn_app;

-- [TR05] Seed the active ranking-weight version if none exists (milavn_app is
-- read-only on this table by design).
INSERT INTO milavn_discovery.ranking_weight_config (version, locality_weight, interest_weight, trust_weight, freshness_weight)
SELECT 1, 0.35, 0.30, 0.20, 0.15
WHERE NOT EXISTS (SELECT 1 FROM milavn_discovery.ranking_weight_config WHERE effective_to IS NULL);

-- Circle & suggestion writes by the batch job / creator need DELETE on
-- membership for "leave" soft-deletes (UPDATE already granted).
GRANT SELECT, INSERT, UPDATE ON milavn_circle.circle_formation_suggestion TO milavn_app;
