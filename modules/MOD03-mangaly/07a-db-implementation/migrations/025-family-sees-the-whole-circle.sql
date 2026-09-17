-- =============================================================================
-- 025 — A family member sees the whole Home Circle, not just themselves.
--
-- WHY (2026-09-17, product owner, reviewing the parent role): "focus on circle
-- and improve … that contains home circle people always". Acting as a parent,
-- the Circle screen showed the candidate's name and nothing else: a parent
-- could not see who else is helping, so the people-side of the family role was
-- effectively missing.
--
-- The membership table's own RLS policy (`hc_membership_participants`,
-- migration 001) already allows `has_scope(candidate_profile_id,
-- 'family_info')` — a family member has always been permitted to read the
-- candidate's membership ROWS. What blocked them was only the name lookup:
-- `list_circle_members()` (migration 019) was written for the candidate's own
-- screen and gated on `mangaly_authz.is_self(p_candidate_account_id)` alone,
-- so for a parent it returned zero rows and the screen had nothing to draw.
--
-- This widens that one predicate to match the policy the rows already carry.
-- It grants no new row visibility — it only stops the name projection from
-- being narrower than the table it reads. Everything else migration 019 fixed
-- in place: SECURITY DEFINER with a pinned search_path, minimal projection
-- (no phone, no email, no profile detail beyond a display name), active
-- memberships only, and EXECUTE granted to mangaly_app alone.
--
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_home_circle.list_circle_members(p_candidate_account_id uuid)
RETURNS TABLE (
    membership_id uuid,
    member_account_id uuid,
    member_name text,
    relationship_type text,
    joined_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_identity, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT m.id,
           m.member_account_id,
           COALESCE(
               a.display_name,
               (SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = m.member_account_id)
           ),
           m.relationship_type::text,
           m.joined_at
      FROM mangaly_home_circle.membership m
      LEFT JOIN mangaly_identity.account a ON a.id = m.member_account_id
     WHERE (
               mangaly_authz.is_self(p_candidate_account_id)
               OR mangaly_authz.has_scope(p_candidate_account_id, 'family_info')
           )
       AND m.candidate_profile_id = p_candidate_account_id
       AND m.status = 'active'
     ORDER BY m.joined_at;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.list_circle_members(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_circle_members(uuid) TO mangaly_app;
