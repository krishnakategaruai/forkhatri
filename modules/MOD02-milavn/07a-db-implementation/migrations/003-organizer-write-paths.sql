-- =============================================================================
-- Milavn (MOD02) — migration 003: organizer-side participation writes.
-- Run as milavn_owner.
--
-- Found live while implementing TR12/TR14/TR39 (not on paper):
--   * `participation`'s RLS policy is FOR ALL ... WITH CHECK (member_id = me).
--     That is exactly right for a participant's own toggle, but it also means
--     an organizer marking check-in / no-show (FR018/FR019) and the waitlist
--     promotion that runs inside a *withdrawing* member's transaction (TR39)
--     both fail the WITH CHECK, because the row being written belongs to
--     someone else.
--   * `SELECT ... FOR UPDATE` on `occurrence` must pass the UPDATE policy,
--     so a non-organizer cannot take TR39's row lock. The critical section is
--     therefore serialised with a transaction-scoped advisory lock keyed on
--     the occurrence id — the same "one writer at a time per occurrence"
--     guarantee TR39 asks for, without relaxing any RLS policy.
--
-- Both writes move behind SECURITY DEFINER functions that re-check the
-- organizer relationship themselves (the Authorization Engine checks it
-- first in the application; this is defence in depth, not the only gate).
-- =============================================================================

CREATE OR REPLACE FUNCTION milavn_activity.promote_next_waitlisted(p_occurrence_id uuid, p_actor uuid)
RETURNS TABLE(participation_id uuid, member_id uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE r record;
BEGIN
  SELECT p.id, p.member_id INTO r
  FROM milavn_activity.participation p
  WHERE p.occurrence_id = p_occurrence_id AND p.status = 'waitlisted'
  ORDER BY p.waitlist_position ASC LIMIT 1;
  IF NOT FOUND THEN RETURN; END IF;
  UPDATE milavn_activity.participation SET status = 'going', waitlist_position = NULL, updated_at = now() WHERE id = r.id;
  INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
  VALUES (r.id, 'waitlisted', 'going', p_actor);
  participation_id := r.id; member_id := r.member_id;
  RETURN NEXT;
END;
$$;

CREATE OR REPLACE FUNCTION milavn_activity.organizer_set_status(
  p_occurrence_id uuid, p_member_id uuid, p_new_status text, p_actor uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_activity, pg_catalog AS $$
DECLARE r record; is_org boolean;
BEGIN
  SELECT (o.creator_member_id = p_actor) OR EXISTS (
           SELECT 1 FROM milavn_activity.occurrence_co_organizer c
           WHERE c.occurrence_id = o.id AND c.member_id = p_actor AND c.revoked_at IS NULL)
    INTO is_org FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id;
  IF NOT coalesce(is_org, false) THEN RAISE EXCEPTION 'not organizer' USING ERRCODE = '42501'; END IF;
  SELECT id, status::text INTO r FROM milavn_activity.participation WHERE occurrence_id = p_occurrence_id AND member_id = p_member_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  UPDATE milavn_activity.participation
     SET status = p_new_status::milavn_activity.participation_status,
         waitlist_position = NULL,
         checked_in_at = CASE WHEN p_new_status IN ('checked_in','attended') THEN coalesce(checked_in_at, now()) ELSE checked_in_at END,
         updated_at = now()
   WHERE id = r.id;
  INSERT INTO milavn_activity.participation_status_history (participation_id, old_status, new_status, changed_by_member_id)
  VALUES (r.id, r.status::milavn_activity.participation_status, p_new_status::milavn_activity.participation_status, p_actor);
  RETURN r.status;
END;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.promote_next_waitlisted(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.organizer_set_status(uuid, uuid, text, uuid) TO milavn_app;
