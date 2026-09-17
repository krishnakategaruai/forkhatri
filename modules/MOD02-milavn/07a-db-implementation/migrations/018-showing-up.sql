-- 018 — Showing up (FR103 still coming?, FR104 two reminders, FR105 plan prompt).
--
-- Research (RESEARCH-BEHAVIOUR-2026.md §1.3): asking *how* someone will get there raises follow-through
-- (Milkman et al. 2011; Nickerson & Rogers 2010: +9.1 points for people living alone); two reminders beat one
-- (Steiner et al. 2018); a message saying a missed spot affects someone else cut no-shows from 21.1% to 14.2%
-- and raised early cancellations (Berliner Senderey et al. 2020). No penalties, no reliability scores.
--
--   participation.plan_travel / plan_with   the member's own one-tap plan (private to them and the host)
--   participation.confirmed_at               "Still coming" answered
--   notification.reminder_sent               one row per member/activity/kind, so no reminder is sent twice

ALTER TABLE milavn_activity.participation
  ADD COLUMN IF NOT EXISTS plan_travel text,
  ADD COLUMN IF NOT EXISTS plan_with text,
  ADD COLUMN IF NOT EXISTS confirmed_at timestamptz;
DO $$ BEGIN
  ALTER TABLE milavn_activity.participation ADD CONSTRAINT participation_plan_travel_values
    CHECK (plan_travel IS NULL OR plan_travel IN ('walk', 'two_wheeler', 'car', 'cab_auto', 'metro_bus'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE milavn_activity.participation ADD CONSTRAINT participation_plan_with_values
    CHECK (plan_with IS NULL OR plan_with IN ('alone', 'friend', 'family'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS milavn_notification.reminder_sent (
  member_id     uuid NOT NULL,
  occurrence_id uuid NOT NULL,
  kind          text NOT NULL CHECK (kind IN ('three_days', 'still_coming', 'two_hours')),
  sent_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, occurrence_id, kind)
);
ALTER TABLE milavn_notification.reminder_sent ENABLE ROW LEVEL SECURITY;  -- definer function only

-- Claims the reminders that are due for one kind and records them in the same statement, so a reminder is never
-- sent twice even if two job runs overlap. Windows are wide (the job runs every 10 minutes):
--   three_days    66–78 h before     still_coming  20–28 h before (not yet confirmed)     two_hours  90–150 min before
-- Only people Going (not the host). Someone who joined in the last 3 hours is not asked "still coming?".
CREATE OR REPLACE FUNCTION milavn_notification.claim_reminders(p_kind text)
RETURNS TABLE (member_id uuid, occurrence_id uuid, title text, slug text, time_start timestamptz, locality text,
               plan_travel text, plan_with text, waitlisted integer, paid boolean)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, milavn_notification, pg_catalog AS $$
#variable_conflict use_column
DECLARE lo interval; hi interval;
BEGIN
  IF p_kind = 'three_days' THEN lo := interval '66 hours'; hi := interval '78 hours';
  ELSIF p_kind = 'still_coming' THEN lo := interval '20 hours'; hi := interval '28 hours';
  ELSIF p_kind = 'two_hours' THEN lo := interval '90 minutes'; hi := interval '150 minutes';
  ELSE RAISE EXCEPTION 'unknown reminder kind %', p_kind;
  END IF;
  RETURN QUERY
  WITH due AS (
    SELECT p.member_id AS m, o.id AS o_id, o.title AS t, o.canonical_url_slug AS s, o.time_start AS ts,
           COALESCE(o.locality_locality, o.locality_city) AS loc, p.plan_travel AS pt, p.plan_with AS pw,
           (SELECT count(*)::integer FROM milavn_activity.participation w WHERE w.occurrence_id = o.id AND w.status = 'waitlisted') AS wl,
           (o.price_paise IS NOT NULL) AS pd
    FROM milavn_activity.participation p
    JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id
    WHERE p.status = 'going' AND o.status = 'active' AND o.creator_member_id <> p.member_id
      AND o.time_start > now() + lo AND o.time_start <= now() + hi
      AND (p_kind <> 'still_coming' OR (p.confirmed_at IS NULL AND p.updated_at < now() - interval '3 hours'))
      AND NOT EXISTS (SELECT 1 FROM milavn_notification.reminder_sent r WHERE r.member_id = p.member_id AND r.occurrence_id = o.id AND r.kind = p_kind)
  ),
  claimed AS (
    INSERT INTO milavn_notification.reminder_sent (member_id, occurrence_id, kind)
    SELECT d.m, d.o_id, p_kind FROM due d
    ON CONFLICT DO NOTHING
    RETURNING reminder_sent.member_id AS cm, reminder_sent.occurrence_id AS co
  )
  SELECT d.m, d.o_id, d.t, d.s, d.ts, d.loc, d.pt, d.pw, d.wl, d.pd
  FROM due d JOIN claimed c ON c.cm = d.m AND c.co = d.o_id;
END;
$$;
GRANT EXECUTE ON FUNCTION milavn_notification.claim_reminders(text) TO milavn_app;

-- The earlier 24-hour reminder (migration 009) now covers people who are only Interested: one gentle nudge.
-- People Going get the staged reminders above instead, so nobody receives both.
CREATE OR REPLACE FUNCTION milavn_notification.reminder_candidates()
RETURNS TABLE(member_id uuid, occurrence_id uuid, title text, canonical_url_slug text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, milavn_notification, pg_catalog AS $$
  SELECT p.member_id, o.id, o.title, o.canonical_url_slug
  FROM milavn_activity.participation p
  JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id
  WHERE p.status = 'interested' AND o.status = 'active'
    AND o.time_start BETWEEN now() + interval '23 hours' AND now() + interval '25 hours'
    AND NOT EXISTS (
      SELECT 1 FROM milavn_notification.notification_inbox_entry n
      WHERE n.member_id = p.member_id AND n.source_occurrence_id = o.id AND n.notification_class = 'useful'
    );
$$;
