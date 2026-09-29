-- =============================================================================
-- 042 — Erasing a profile that someone else made for a person
--       (product owner, 2026-09-21; DEC-V1-019).
--
-- WHY:
--   A parent can create a profile for their son or daughter with the child's
--   mobile number (041). Two cases need it gone:
--     1. "This isn't me" — the person who owns that number signs in, finds a
--        profile made in their name that they did not ask for, and removes it.
--     2. Never used — the owner's rule: accounts nobody uses are removed after
--        about six months. A profile made for someone who never signs in to
--        take it over is removed 180 days after it was made (the creator is
--        told a week before).
--
-- WHAT IS ERASED:
--   The profile row (its attributes and photos go with it, ON DELETE CASCADE),
--   its discovery index row, its trust-layer rows, and every circle membership
--   and pending invitation for it. Access grants to or from it are REVOKED and
--   its connection requests WITHDRAWN rather than deleted — the other party's
--   history of having sent or received a request is theirs, and the sharing
--   tables reference those rows. The member-link account row stays: it is the
--   person's own account, and they may still use ForKhatri.
--
-- `erase_made_for_profile(uuid)` is the worker and is NOT granted to the app
-- role; only `disown_profile_made_for_me()` (self, unclaimed, made by someone
-- else) is, and the six-month job runs as the schema owner.
-- =============================================================================

ALTER TABLE mangaly_profile.profile
    ADD COLUMN IF NOT EXISTS removal_notice_at timestamptz;

CREATE OR REPLACE FUNCTION mangaly_profile.erase_made_for_profile(p_account uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_profile, pg_temp
AS $$
DECLARE
    v_profile uuid;
BEGIN
    SELECT id INTO v_profile FROM mangaly_profile.profile
     WHERE account_id = p_account
       AND created_by_account_id IS NOT NULL
       AND claimed_at IS NULL;
    IF v_profile IS NULL THEN
        RETURN false;
    END IF;

    UPDATE mangaly_connection.connection_request
       SET status = 'withdrawn', updated_at = now()
     WHERE status IN ('pending', 'accepted')
       AND (subject_account_id = p_account OR target_profile_id = p_account);

    UPDATE mangaly_authz."grant"
       SET status = 'revoked', revoked_at = now(), updated_at = now()
     WHERE status <> 'revoked'
       AND (target_profile_id = p_account OR subject_id = p_account);

    UPDATE mangaly_home_circle.membership
       SET status = 'removed', removed_at = now(), updated_at = now()
     WHERE candidate_profile_id = p_account AND status = 'active';

    UPDATE mangaly_home_circle.invitation
       SET status = 'expired', updated_at = now()
     WHERE candidate_profile_id = p_account AND status = 'pending';

    DELETE FROM mangaly_discovery.discovery_profile_index WHERE profile_id = p_account;
    DELETE FROM mangaly_discovery.shortlist WHERE saved_account_id = p_account OR candidate_account_id = p_account;
    DELETE FROM mangaly_trust.verification_layer_status WHERE profile_id = v_profile;
    DELETE FROM mangaly_profile.profile WHERE id = v_profile;
    RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.erase_made_for_profile(uuid) FROM PUBLIC;

-- "This isn't me": only the person themselves, only a profile someone else
-- made that they have not taken over.
CREATE OR REPLACE FUNCTION mangaly_profile.disown_profile_made_for_me(p_account uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_authz, pg_temp
AS $$
BEGIN
    IF mangaly_authz.is_self(p_account) IS NOT TRUE THEN
        RETURN false;
    END IF;
    RETURN mangaly_profile.erase_made_for_profile(p_account);
END;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.disown_profile_made_for_me(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.disown_profile_made_for_me(uuid) TO mangaly_app;
