-- 011 — "Need over noise" (thesis §84 #13): the inbox must not fill with the
-- same message twice. A person who joins, withdraws and joins again within a
-- day produces one "X is going" for the organizer, not three; a re-sent
-- reminder or announcement for the same occurrence is delivered once.
--
-- deliver() gains a duplicate guard: if an entry with the same member, class,
-- title and source occurrence was created in the last 24 hours, the new one
-- is dropped (the outbox row is not written either, so no push goes out).
-- Important-class messages are still never *muted* (FR051); they are only
-- de-duplicated like everything else.

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
  -- Duplicate guard (24h window, same member + class + title + occurrence).
  IF EXISTS (
    SELECT 1 FROM milavn_notification.notification_inbox_entry
     WHERE member_id = p_member_id
       AND notification_class = p_class::milavn_notification.notification_class
       AND title = p_title
       AND source_occurrence_id IS NOT DISTINCT FROM p_occurrence_id
       AND created_at > now() - interval '24 hours'
  ) THEN RETURN; END IF;
  INSERT INTO milavn_notification.notification_inbox_entry (member_id, notification_class, title, body, deep_link, source_occurrence_id)
  VALUES (p_member_id, p_class::milavn_notification.notification_class, p_title, p_body, p_deep_link, p_occurrence_id);
  INSERT INTO milavn_notification.notification_outbox (member_id, notification_class, payload)
  VALUES (p_member_id, p_class::milavn_notification.notification_class,
          jsonb_build_object('title', p_title, 'body', p_body, 'deep_link', p_deep_link, 'occurrence_id', p_occurrence_id));
END;
$$;

GRANT EXECUTE ON FUNCTION milavn_notification.deliver(uuid, text, text, text, text, uuid) TO milavn_app;

-- Organizer announcements: the organizer console lists the last few with a
-- time, and an identical message within an hour is refused by the service
-- (see activity.announce). Nothing structural changes here; this comment is
-- the record that the guard lives in code, not in the schema.
