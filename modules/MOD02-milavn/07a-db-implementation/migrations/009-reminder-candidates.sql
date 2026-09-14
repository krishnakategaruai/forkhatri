-- =============================================================================
-- Milavn (MOD02) — migration 009: reminder job read. Run as milavn_owner.
--
-- FR052's 24-hour reminders run as a scheduled job with no acting member;
-- `participation`/`occurrence` policies are member-scoped, so the job reads
-- its candidates through a definer-owned function (ids + title/slug only),
-- the same pattern as migration 004's dispatcher reads.
-- =============================================================================
CREATE OR REPLACE FUNCTION milavn_notification.reminder_candidates()
RETURNS TABLE(member_id uuid, occurrence_id uuid, title text, canonical_url_slug text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, milavn_notification, pg_catalog AS $$
  SELECT p.member_id, o.id, o.title, o.canonical_url_slug
  FROM milavn_activity.participation p
  JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id
  WHERE p.status IN ('going','interested') AND o.status = 'active'
    AND o.time_start BETWEEN now() + interval '23 hours' AND now() + interval '25 hours'
    AND NOT EXISTS (
      SELECT 1 FROM milavn_notification.notification_inbox_entry n
      WHERE n.member_id = p.member_id AND n.source_occurrence_id = o.id AND n.notification_class = 'useful'
    );
$$;
GRANT EXECUTE ON FUNCTION milavn_notification.reminder_candidates() TO milavn_app;
