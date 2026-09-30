-- =============================================================================
-- 061 — A relationship manager or agent sees their own clients' photos.
--
-- WHY (owner walkthrough, 2026-09-30): an agent opening a client family's file
-- got a broken photo. The media route serves a photo only to its owner, a
-- searchable profile's main photo, openly shared photos, the candidate's own
-- Home Circle, and conversation participants — never to the RM or agent the
-- family chose. DEC-V1-033/034 keep an agent's OWN clients unrestricted
-- (only other families' details are counted and capped), so a client's
-- photos belong in that agent's view.
--
-- Scope: photos (not voice) of a member with an ACTIVE assignment to the
-- caller. Ending the assignment ends the access.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_operations.is_client_photo(p_storage_ref text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM mangaly_profile.profile_media pm
          JOIN mangaly_profile.profile p ON p.id = pm.profile_id
          JOIN mangaly_operations.rm_assignment a ON a.member_account_id = p.account_id
         WHERE pm.storage_ref = p_storage_ref
           AND pm.media_type::text = 'photo'
           AND a.status = 'active'
           AND mangaly_authz.is_self(a.rm_account_id)
    );
$$;

REVOKE ALL ON FUNCTION mangaly_operations.is_client_photo(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.is_client_photo(text) TO mangaly_app;
