-- =============================================================================
-- 019 — A candidate sees who is in their Home Circle by name.
--
-- WHY (2026-09-15, real test with a parent): Ananya's Members list showed only
-- "Parent" and a date, so she could not tell who had joined. A family member
-- such as her mother Lakshmi has no Mangaly candidate profile; her name lives
-- in the ForKhatri identity (session claims `display_name`).
--
--   * `mangaly_identity.account.display_name` keeps the member's platform name
--     on their own link row. The Identity Bridge writes it in the member's own
--     request under `account_self_only`, so the frozen
--     `ensure_platform_account()` (migration 014) is not changed.
--   * `list_circle_members()` lets the candidate read the names of the people
--     in THEIR OWN circle only (account rows are otherwise self-only). Same
--     rules as migrations 010/016/017: caller must be the candidate, values
--     come from rows, minimal projection.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_identity.account
  ADD COLUMN IF NOT EXISTS display_name text;

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
     WHERE mangaly_authz.is_self(p_candidate_account_id)
       AND m.candidate_profile_id = p_candidate_account_id
       AND m.status = 'active'
     ORDER BY m.joined_at;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.list_circle_members(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_circle_members(uuid) TO mangaly_app;
