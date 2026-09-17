-- =============================================================================
-- 017 — The candidates a family member helps (FR097 context switcher).
--
-- WHY (2026-09-15): a parent who joins a candidate's Home Circle must be able
-- to switch to "Viewing Ananya's search" and see whose search it is by name.
-- The member can read their own membership rows, but a `family_info` grant
-- does not unlock the candidate's `profile` row (that needs `candidate_info`),
-- so the candidate's name is unreadable from the member's session. This
-- narrow SECURITY DEFINER read returns, for the caller's own active
-- memberships only, the candidate's name and the caller's relationship —
-- nothing else from the profile. Same rules as migrations 010/016: the caller
-- must be the member, values come from rows, minimal projection.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_home_circle.list_member_contexts(p_member_account_id uuid)
RETURNS TABLE (
    membership_id uuid,
    candidate_account_id uuid,
    candidate_name text,
    relationship_type text,
    joined_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT DISTINCT ON (m.candidate_profile_id)
           m.id,
           m.candidate_profile_id,
           p.name,
           m.relationship_type::text,
           m.joined_at
      FROM mangaly_home_circle.membership m
      JOIN mangaly_profile.profile p ON p.account_id = m.candidate_profile_id
     WHERE mangaly_authz.is_self(p_member_account_id)
       AND m.member_account_id = p_member_account_id
       AND m.status = 'active'
     ORDER BY m.candidate_profile_id, m.joined_at;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.list_member_contexts(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_member_contexts(uuid) TO mangaly_app;
