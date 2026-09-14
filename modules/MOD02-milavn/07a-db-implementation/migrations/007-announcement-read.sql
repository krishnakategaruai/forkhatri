-- =============================================================================
-- Milavn (MOD02) — migration 007: dispatcher read of an announcement body.
-- Run as milavn_owner. Fix-forward.
--
-- `occurrence_update`'s SELECT policy is participant-or-organizer; Notification
-- Dispatch runs after commit with no acting member, so it reads the message it
-- must deliver (FR057) through this definer-owned function — same pattern as
-- migration 004's occurrence_brief.
-- =============================================================================
CREATE OR REPLACE FUNCTION milavn_activity.occurrence_update_message(p_update_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT message FROM milavn_activity.occurrence_update WHERE id = p_update_id;
$$;
GRANT EXECUTE ON FUNCTION milavn_activity.occurrence_update_message(uuid) TO milavn_app;
