-- [TR021 gap, found during Step 9 implementation of FR21's notification
-- matcher/digest job — fixed forward with a new migration, per this
-- project's protected-path rule that 001-initial.sql (already applied) is
-- immutable history, not edited in place.]
--
-- vyapar_privacy.privacy_settings' own RLS policy (privacy_settings_
-- self_only) is intentionally self-only with NO operator/service-role
-- bypass — correct for every member-facing read/write path, but it also
-- silently blocks the ONE legitimate background-job read this schema
-- needs: the notification matcher/digest pass (running as
-- vyapar.service_role='dispatcher', per the same pattern outbox_event
-- tables already use) has to see notifications_enabled/digest_enabled/
-- digest_hour/muted_types across ALL members to decide who to notify.
-- Before this migration, that query silently returned zero rows (RLS
-- filtered every row, since no per-request authz_context matches a
-- background job) — not an error, just quietly wrong, exactly the kind of
-- gap this project's own "no code path independently re-deriving a check"
-- discipline exists to catch.
--
-- Fix: one narrow, audited SECURITY DEFINER function — the same pattern
-- vyapar_identity.ensure_member()/vyapar_listings.contacts_for_viewer()
-- already established — callable ONLY by the dispatcher service role
-- (enforced inside the function body, not by a wider GRANT), returning
-- exactly the columns the notification job needs and nothing else (no
-- capability_visible/seeking_visible/contact_disclosure exposure beyond
-- what this one job requires).
SET search_path TO vyapar_privacy, vyapar_identity, pg_temp;

CREATE OR REPLACE FUNCTION vyapar_privacy.notification_targets()
RETURNS TABLE(member_id text, notifications_enabled boolean, digest_enabled boolean, digest_hour smallint, muted_types text[])
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = vyapar_privacy, pg_temp
AS $$
BEGIN
  IF current_setting('vyapar.service_role', true) IS DISTINCT FROM 'dispatcher' THEN
    RAISE EXCEPTION 'notification_targets() is dispatcher-only';
  END IF;
  RETURN QUERY
    SELECT ps.member_id, ps.notifications_enabled, ps.digest_enabled, ps.digest_hour, ps.muted_types
    FROM vyapar_privacy.privacy_settings ps;
END;
$$;
COMMENT ON FUNCTION vyapar_privacy.notification_targets() IS
  '[TR021 gap-fix] The ONLY cross-member read of privacy_settings — dispatcher-only, narrow column list. Every other caller still goes through the self-only RLS policy unchanged.';

GRANT EXECUTE ON FUNCTION vyapar_privacy.notification_targets() TO vyapar_app;
