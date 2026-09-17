-- 019 — Belonging (FR107 thank the host + would you come again?, FR108 welcome newcomers).
--
-- Research (RESEARCH-BEHAVIOUR-2026.md §1.2, §1.6): people underestimate how much thanks is worth to the person
-- thanked (Kumar & Epley 2018) and how much others liked them (Boothby et al. 2018); a short, specific thank-you
-- keeps volunteers going (Grant & Gino 2010); newcomers stay when someone welcomes them (Choi et al. 2010;
-- Morgan & Halfaker 2018). Feedback is one tap, private, and never a rating anyone sees (owner decision:
-- no public star ratings; Zervas et al. 2021 on rating inflation).
--
--   trust.thanks          one thank-you per attendee per activity, readable by the sender and the host only
--   trust.feedback        + come_again (yes | maybe | no) replacing the 1–5 prompt in the product
--   first-timer helper    "has never checked in to an earlier activity"
--   after_summary         what the host sees afterwards: came, first-timers, would come again, thanks (counts)
--   reputation_labels     + "appreciated_host" once a host has been thanked three times

CREATE TABLE IF NOT EXISTS milavn_trust.thanks (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id  uuid NOT NULL,   -- cross-schema ref -> milavn_activity.occurrence(id), no FK (§4)
  from_member_id uuid NOT NULL,
  to_member_id   uuid NOT NULL,
  message        text NOT NULL CHECK (length(btrim(message)) BETWEEN 1 AND 140),
  created_at     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT thanks_once_per_activity UNIQUE (occurrence_id, from_member_id),
  CONSTRAINT thanks_not_self CHECK (from_member_id <> to_member_id)
);
CREATE INDEX IF NOT EXISTS thanks_to_member_idx ON milavn_trust.thanks (to_member_id);

ALTER TABLE milavn_trust.thanks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS thanks_sender_or_host ON milavn_trust.thanks;
CREATE POLICY thanks_sender_or_host ON milavn_trust.thanks
  FOR SELECT USING (from_member_id = current_setting('milavn.member_id', true)::uuid
                    OR to_member_id = current_setting('milavn.member_id', true)::uuid);
DROP POLICY IF EXISTS thanks_sender_inserts ON milavn_trust.thanks;
CREATE POLICY thanks_sender_inserts ON milavn_trust.thanks
  FOR INSERT WITH CHECK (from_member_id = current_setting('milavn.member_id', true)::uuid);
DROP POLICY IF EXISTS thanks_sender_updates ON milavn_trust.thanks;
CREATE POLICY thanks_sender_updates ON milavn_trust.thanks
  FOR UPDATE USING (from_member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (from_member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, UPDATE ON milavn_trust.thanks TO milavn_app;

ALTER TABLE milavn_trust.feedback ADD COLUMN IF NOT EXISTS come_again text;
DO $$ BEGIN
  ALTER TABLE milavn_trust.feedback ADD CONSTRAINT feedback_come_again_values CHECK (come_again IS NULL OR come_again IN ('yes', 'maybe', 'no'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- The notification dispatcher has no acting member: it reads the thank-you text through this helper.
CREATE OR REPLACE FUNCTION milavn_trust.thanks_message(p_occurrence_id uuid, p_from_member_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_trust, pg_catalog AS $$
  SELECT message FROM milavn_trust.thanks WHERE occurrence_id = p_occurrence_id AND from_member_id = p_from_member_id;
$$;

-- A first-timer has never checked in to (or been marked at) an activity that started before this one.
CREATE OR REPLACE FUNCTION milavn_activity.is_first_timer(p_member_id uuid, p_before timestamptz)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT NOT EXISTS (
    SELECT 1 FROM milavn_activity.participation p
    JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id
    WHERE p.member_id = p_member_id AND p.status IN ('checked_in', 'attended') AND o.time_start < p_before
  );
$$;

-- What a host sees after the activity. Counts only; the thank-you notes themselves are read under RLS by the host.
CREATE OR REPLACE FUNCTION milavn_activity.after_summary(p_occurrence_id uuid)
RETURNS TABLE (came integer, first_timers integer, come_again_yes integer, answered integer, thanks_count integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, milavn_trust, pg_catalog AS $$
  SELECT
    (SELECT count(*)::integer FROM milavn_activity.participation p
      WHERE p.occurrence_id = p_occurrence_id AND p.status IN ('checked_in', 'attended')),
    (SELECT count(*)::integer FROM milavn_activity.participation p JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id
      WHERE p.occurrence_id = p_occurrence_id AND p.status IN ('checked_in', 'attended') AND milavn_activity.is_first_timer(p.member_id, o.time_start)),
    (SELECT count(*)::integer FROM milavn_trust.feedback f WHERE f.occurrence_id = p_occurrence_id AND f.come_again = 'yes'),
    (SELECT count(*)::integer FROM milavn_trust.feedback f WHERE f.occurrence_id = p_occurrence_id AND f.come_again IS NOT NULL),
    (SELECT count(*)::integer FROM milavn_trust.thanks t WHERE t.occurrence_id = p_occurrence_id);
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
  IF completed >= 3 THEN labels := array_append(labels, 'experienced_organizer');
  ELSIF completed >= 1 THEN labels := array_append(labels, 'has_hosted'); END IF;
  IF thanked >= 3 THEN labels := array_append(labels, 'appreciated_host'); END IF;
  IF reliable >= 3 AND no_shows <= 1 THEN labels := array_append(labels, 'reliable_attendee'); END IF;
  IF contribs >= 2 THEN labels := array_append(labels, 'community_contributor'); END IF;
  IF cardinality(labels) = 0 THEN labels := ARRAY['new_to_community']; END IF;
  RETURN labels;
END;
$$;

-- Fix found by the belonging scenario: the event bus marks each event dispatched after delivery, but the app role
-- could only INSERT into milavn_trust.outbox_event (thanks are the first trust events published from a request),
-- so the first thank-you crashed the response after commit. Every component's outbox gets the same grants.
GRANT SELECT, INSERT, UPDATE ON milavn_activity.outbox_event, milavn_circle.outbox_event, milavn_trust.outbox_event, milavn_safety.outbox_event TO milavn_app;

GRANT EXECUTE ON FUNCTION milavn_trust.thanks_message(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.is_first_timer(uuid, timestamptz) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.after_summary(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_trust.reputation_labels(uuid) TO milavn_app;
