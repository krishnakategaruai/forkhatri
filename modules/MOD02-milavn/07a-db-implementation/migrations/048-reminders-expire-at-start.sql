-- 048 — A reminder stops being shown once its activity has started (whole-app critique, 2026-09-29).
--
-- The Alerts screen still listed "Still coming tomorrow?" and "In 3 days" reminders for
-- activities that ended nearly two weeks earlier. A reminder only makes sense before the thing it
-- reminds about, so it now carries `expires_at` (the occurrence's start): the inbox and the unread
-- count leave out anything past it, and the reminder job clears expired rows. Notifications meant
-- for after an activity (moments, thanks, feedback, updates) have no `expires_at` and stay.
-- Safe to run twice.

ALTER TABLE milavn_notification.notification_inbox_entry ADD COLUMN IF NOT EXISTS expires_at timestamptz;
CREATE INDEX IF NOT EXISTS notification_inbox_entry_expires_idx
  ON milavn_notification.notification_inbox_entry (expires_at) WHERE expires_at IS NOT NULL;

-- Like `deliver`, for a reminder about an occurrence: it expires when the occurrence starts, and a
-- reminder whose occurrence has already started is not written at all.
CREATE OR REPLACE FUNCTION milavn_notification.deliver_reminder(
  p_member_id uuid, p_class text, p_title text, p_body text, p_deep_link text, p_occurrence_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_notification, pg_catalog AS $$
DECLARE
  muted_pref boolean;
  starts timestamptz;
BEGIN
  SELECT o.time_start INTO starts FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
  IF starts IS NULL OR starts <= now() THEN RETURN; END IF;
  SELECT muted INTO muted_pref FROM milavn_notification.notification_preference
   WHERE member_id = p_member_id AND notification_class = p_class::milavn_notification.notification_class;
  IF p_class <> 'important' AND coalesce(muted_pref, false) THEN RETURN; END IF;
  IF EXISTS (
    SELECT 1 FROM milavn_notification.notification_inbox_entry
     WHERE member_id = p_member_id
       AND notification_class = p_class::milavn_notification.notification_class
       AND title = p_title
       AND source_occurrence_id IS NOT DISTINCT FROM p_occurrence_id
       AND created_at > now() - interval '24 hours'
  ) THEN RETURN; END IF;
  INSERT INTO milavn_notification.notification_inbox_entry
    (member_id, notification_class, title, body, deep_link, source_occurrence_id, expires_at)
  VALUES (p_member_id, p_class::milavn_notification.notification_class, p_title, p_body, p_deep_link, p_occurrence_id, starts);
  INSERT INTO milavn_notification.notification_outbox (member_id, notification_class, payload)
  VALUES (p_member_id, p_class::milavn_notification.notification_class,
          jsonb_build_object('title', p_title, 'body', p_body, 'deep_link', p_deep_link, 'occurrence_id', p_occurrence_id));
END;
$$;
REVOKE ALL ON FUNCTION milavn_notification.deliver_reminder(uuid, text, text, text, text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_notification.deliver_reminder(uuid, text, text, text, text, uuid) TO milavn_app;

-- The scheduled job (no acting member) clears reminders whose activity has started.
CREATE OR REPLACE FUNCTION milavn_notification.purge_expired_reminders()
RETURNS integer LANGUAGE sql SECURITY DEFINER
SET search_path = milavn_notification, pg_catalog AS $$
  WITH gone AS (
    DELETE FROM milavn_notification.notification_inbox_entry WHERE expires_at IS NOT NULL AND expires_at <= now() RETURNING 1
  ) SELECT count(*)::integer FROM gone;
$$;
REVOKE ALL ON FUNCTION milavn_notification.purge_expired_reminders() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_notification.purge_expired_reminders() TO milavn_app;

-- Reminders written before this migration: the four reminder kinds the job sends (FR052/FR103/FR104).
UPDATE milavn_notification.notification_inbox_entry e
   SET expires_at = o.time_start
  FROM milavn_activity.occurrence o
 WHERE o.id = e.source_occurrence_id
   AND e.expires_at IS NULL
   AND e.notification_class = 'useful'
   AND (e.title LIKE 'Tomorrow: %' OR e.title LIKE 'Still coming tomorrow? %'
        OR e.title LIKE 'In 3 days: %' OR e.title LIKE 'Starts at %');

SELECT milavn_notification.purge_expired_reminders();
