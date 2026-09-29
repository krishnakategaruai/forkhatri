-- =============================================================================
-- 041 — A parent creates a candidate profile for their son or daughter
--       (product owner, 2026-09-21; DEC-V1-019).
--
-- WHY:
--   Indian matrimony profiles are very often made by a parent. Shaadi.com's
--   registration asks who the profile is for — Self, Son, Daughter, Brother,
--   Sister, Friend or Relative — and supports registering on a relative's
--   behalf. Before 041 a Mangaly parent could only ask to join a child who had
--   already signed up, so a parent could not start a search at all.
--
-- HOW (no re-keying, by construction):
--   A Mangaly account's id IS the person's ForKhatri member id (TR10/TR23), and
--   ~50 columns reference it without foreign keys. So the child's account is
--   created with its FINAL id from the start: Mangaly asks the ForKhatri
--   Identity & Trust Service to provision a member for the child's mobile
--   number (identity level 0, no credential), then builds the profile on that
--   id. When the child later signs in with an OTP to that number, the platform
--   finds the same member — the profile is simply theirs.
--
--   `created_by_account_id` records who made it; `claimed_at` records when the
--   candidate took it over. While unclaimed, the creator may edit the profile
--   (the API binds the candidate's account for /profile and /media requests
--   that carry `X-Mangaly-Manage`, after `can_manage()` says yes). Once
--   claimed, only the candidate may — the creator stays in the circle as the
--   relation they are.
-- =============================================================================

ALTER TABLE mangaly_profile.profile
    ADD COLUMN IF NOT EXISTS created_by_account_id uuid,
    ADD COLUMN IF NOT EXISTS claimed_at timestamptz;

-- The child's member-link row, created by the parent's request. The row's own
-- RLS admits only the account itself, which does not exist as a session yet —
-- hence SECURITY DEFINER, and the caller must be signed in as someone else.
CREATE OR REPLACE FUNCTION mangaly_identity.create_account_for_child(
    p_member_id uuid,
    p_phone     text,
    p_name      text
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
BEGIN
    IF current_setting('mangaly.account_id', true) IS NULL
       OR current_setting('mangaly.account_id', true) = ''
       OR current_setting('mangaly.account_id', true)::uuid = p_member_id THEN
        RAISE EXCEPTION 'create_account_for_child: must be called by another signed-in account';
    END IF;
    IF EXISTS (SELECT 1 FROM mangaly_identity.account
                WHERE id = p_member_id OR phone_identifier = p_phone) THEN
        RAISE EXCEPTION 'create_account_for_child: account already exists' USING ERRCODE = 'MGL09';
    END IF;
    INSERT INTO mangaly_identity.account (id, phone_identifier, status, display_name)
    VALUES (p_member_id, p_phone, 'active', p_name);
END;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.create_account_for_child(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.create_account_for_child(uuid, text, text) TO mangaly_app;

-- May `p_creator` still edit `p_candidate`'s profile?
CREATE OR REPLACE FUNCTION mangaly_profile.can_manage(p_creator uuid, p_candidate uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_profile.profile
         WHERE account_id = p_candidate
           AND created_by_account_id = p_creator
           AND claimed_at IS NULL
    );
$$;
REVOKE ALL ON FUNCTION mangaly_profile.can_manage(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.can_manage(uuid, uuid) TO mangaly_app;

-- The profiles the caller created and still manages.
CREATE OR REPLACE FUNCTION mangaly_profile.managed_profiles_of(p_creator uuid)
RETURNS TABLE (account_id uuid, name text, primary_photo_ref text, phone_masked text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
    SELECT p.account_id,
           p.name,
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete'
             LIMIT 1),
           left(a.phone_identifier, 3) || '••••••' || right(a.phone_identifier, 4)
      FROM mangaly_profile.profile p
      JOIN mangaly_identity.account a ON a.id = p.account_id
     WHERE mangaly_authz.is_self(p_creator)
       AND p.created_by_account_id = p_creator
       AND p.claimed_at IS NULL
     ORDER BY p.created_at;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.managed_profiles_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.managed_profiles_of(uuid) TO mangaly_app;

-- Who made the caller's own profile (for "Your father created this for you").
CREATE OR REPLACE FUNCTION mangaly_profile.created_for_me(p_account uuid)
RETURNS TABLE (creator_name text, relation text, relationship_type text, claimed_at timestamptz)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
    SELECT a.display_name, m.relation, m.relationship_type::text, p.claimed_at
      FROM mangaly_profile.profile p
      JOIN mangaly_identity.account a ON a.id = p.created_by_account_id
      LEFT JOIN mangaly_home_circle.membership m
             ON m.candidate_profile_id = p.account_id
            AND m.member_account_id = p.created_by_account_id
            AND m.status = 'active'
     WHERE mangaly_authz.is_self(p_account)
       AND p.account_id = p_account
       AND p.created_by_account_id IS NOT NULL;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.created_for_me(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.created_for_me(uuid) TO mangaly_app;
