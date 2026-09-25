-- =============================================================================
-- 054 — A candidate's parents and guardians can READ what the match shared.
--
-- WHY (owner decision, 2026-09-25): once both sides accept, the parents and
-- guardians in each candidate's Home Circle may see the match's full name,
-- and contact details "follow the existing per-item sharing controls: shared
-- only if the candidate shares them". Until now a share (FR046) reached only
-- the other CANDIDATE: `sharing_grant_participants` admits only the two
-- people on the connection, so a parent read nothing even after the match
-- chose to share their phone.
--
-- This adds one SELECT-only policy. A caller may read a grant on an ACCEPTED
-- connection when they are an active parent or guardian in the Home Circle
-- of the candidate on the OTHER side of that grant (i.e. the grant was made
-- to their candidate). Siblings and relatives are not included; nothing can
-- be written through it; the grantor's own controls are untouched.
--
-- The check lives in a SECURITY DEFINER function with a pinned search_path so
-- the policy does not depend on the caller's visibility of the membership and
-- connection tables (no RLS recursion), and it keys on `is_self()` — the
-- caller's bound authorization context — like every other policy here.
--
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_connection.parent_of_share_recipient(
    p_connection_id uuid,
    p_granted_by uuid
) RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_connection, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM mangaly_connection.connection_request c
          JOIN mangaly_home_circle.membership m
            ON m.candidate_profile_id = CASE WHEN c.subject_account_id = p_granted_by
                                             THEN c.target_profile_id
                                             ELSE c.subject_account_id END
         WHERE c.id = p_connection_id
           AND c.status = 'accepted'
           AND p_granted_by IN (c.subject_account_id, c.target_profile_id)
           AND m.status = 'active'
           AND m.relationship_type::text IN ('parent', 'guardian')
           AND mangaly_authz.is_self(m.member_account_id)
    );
$$;
REVOKE ALL ON FUNCTION mangaly_connection.parent_of_share_recipient(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_connection.parent_of_share_recipient(uuid, uuid) TO mangaly_app;

DROP POLICY IF EXISTS sharing_grant_recipient_parents_read ON mangaly_connection.sharing_grant;
CREATE POLICY sharing_grant_recipient_parents_read ON mangaly_connection.sharing_grant
  FOR SELECT
  USING (mangaly_connection.parent_of_share_recipient(connection_id, granted_by_account_id));
