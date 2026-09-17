-- =============================================================================
-- 021 — A family contact share ends when its reason ends (FR048 / TR048, FR010),
--       and `is_self` never answers NULL.
--
-- WHY (2026-09-15):
--   * Found live: a Home Circle member's phone stayed recorded on a
--     connection after the member had left the circle, and after the
--     candidate withdrew the share the `family_contact_share` row still said
--     "granted" while the recipient-visible `sharing_grant` was revoked. The
--     two records disagreed and a former member's phone was still stored
--     against a match.
--   * When a membership ends (removed or left), every family contact request
--     and approved share naming that member must go, and the candidate's
--     recipient-visible grant carrying that member's phone must be revoked.
--     The member who leaves cannot write the candidate's `sharing_grant`
--     under migration 015's WITH CHECK, so this is one SECURITY DEFINER
--     function held to migration 010's rules: the caller must be the
--     candidate or the member, every value is re-derived from rows, and it
--     does nothing while the membership is still active.
--   * Found while testing that function: `mangaly_authz.is_self` returned
--     NULL, not false, for someone else's id when `mangaly.authz_context` is
--     unset (`id = NULL` is NULL). RLS policies treat NULL as "deny", but a
--     PL/pgSQL guard written `IF NOT is_self(...) THEN RETURN` does not fire
--     on NULL, so a third party passed it. `is_self` now always returns true
--     or false, which fixes every such guard (including migration 016's
--     `decide_family_contact_share`) without changing any policy's meaning.
--   * Also found live: the shared family contact carried no name for a
--     member without a Mangaly profile of their own (a parent). The name now
--     falls back to the member's ForKhatri display name (migration 019).
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_authz.is_self(p_profile_or_account_id uuid)
RETURNS boolean
LANGUAGE sql STABLE
AS $$
  SELECT COALESCE(
           p_profile_or_account_id = NULLIF(current_setting('mangaly.authz_context', true), '')::uuid
           OR p_profile_or_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid,
           false);
$$;

CREATE OR REPLACE FUNCTION mangaly_connection.end_family_contact_for_member(
    p_candidate_account_id uuid,
    p_member_account_id uuid
) RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_connection, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
DECLARE
    v_now timestamptz := now();
    v_ended integer;
BEGIN
    IF (mangaly_authz.is_self(p_candidate_account_id) OR mangaly_authz.is_self(p_member_account_id))
       IS NOT TRUE THEN
        RETURN 0;
    END IF;

    PERFORM 1 FROM mangaly_home_circle.membership
     WHERE candidate_profile_id = p_candidate_account_id
       AND member_account_id = p_member_account_id
       AND status = 'active';
    IF FOUND THEN
        RETURN 0;
    END IF;

    UPDATE mangaly_connection.sharing_grant g
       SET revoked_at = v_now,
           shared_value = NULL
      FROM mangaly_connection.family_contact_share s
     WHERE s.candidate_account_id = p_candidate_account_id
       AND s.family_member_account_id = p_member_account_id
       AND s.granted_at IS NOT NULL
       AND g.connection_id = s.connection_id
       AND g.category = 'family_contact'
       AND g.granted_by_account_id = p_candidate_account_id
       AND g.revoked_at IS NULL
       AND g.shared_value::json ->> 'phone' = s.family_member_phone;

    DELETE FROM mangaly_connection.family_contact_share
     WHERE candidate_account_id = p_candidate_account_id
       AND family_member_account_id = p_member_account_id;
    GET DIAGNOSTICS v_ended = ROW_COUNT;
    RETURN v_ended;
END;
$$;

REVOKE ALL ON FUNCTION mangaly_connection.end_family_contact_for_member(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_connection.end_family_contact_for_member(uuid, uuid) TO mangaly_app;

-- Same as migration 016, except the shared name falls back to the member's
-- ForKhatri display name and the caller guard is NULL-proof.
CREATE OR REPLACE FUNCTION mangaly_connection.decide_family_contact_share(
    p_share_id uuid,
    p_family_account_id uuid,
    p_approve boolean
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_connection, mangaly_home_circle, mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
DECLARE
    v_share mangaly_connection.family_contact_share%ROWTYPE;
    v_relationship text;
    v_name text;
    v_phone text;
    v_now timestamptz := now();
BEGIN
    IF mangaly_authz.is_self(p_family_account_id) IS NOT TRUE THEN
        RETURN false;
    END IF;

    SELECT * INTO v_share
      FROM mangaly_connection.family_contact_share
     WHERE id = p_share_id
       AND family_member_account_id = p_family_account_id
       AND candidate_authz_resolved_at IS NOT NULL
       AND family_authz_resolved_at IS NULL
       AND declined_at IS NULL
     FOR UPDATE;
    IF NOT FOUND THEN
        RETURN false;
    END IF;

    SELECT relationship_type::text INTO v_relationship
      FROM mangaly_home_circle.membership
     WHERE candidate_profile_id = v_share.candidate_account_id
       AND member_account_id = p_family_account_id
       AND status = 'active'
     LIMIT 1;
    IF v_relationship IS NULL THEN
        RETURN false;
    END IF;

    PERFORM 1 FROM mangaly_connection.connection_request
     WHERE id = v_share.connection_id AND status = 'accepted';
    IF NOT FOUND THEN
        RETURN false;
    END IF;

    IF NOT p_approve THEN
        UPDATE mangaly_connection.family_contact_share SET declined_at = v_now WHERE id = p_share_id;
        RETURN true;
    END IF;

    SELECT phone_identifier,
           COALESCE((SELECT name FROM mangaly_profile.profile WHERE account_id = p_family_account_id),
                    display_name)
      INTO v_phone, v_name
      FROM mangaly_identity.account
     WHERE id = p_family_account_id;
    IF v_phone IS NULL THEN
        RETURN false;
    END IF;

    UPDATE mangaly_connection.family_contact_share
       SET family_authz_resolved_at = v_now,
           granted_at = v_now,
           family_member_phone = v_phone
     WHERE id = p_share_id;

    INSERT INTO mangaly_connection.sharing_grant
        (connection_id, category, granted_by_account_id, granted_at, shared_value)
    VALUES
        (v_share.connection_id, 'family_contact', v_share.candidate_account_id, v_now,
         json_build_object('name', v_name, 'relationship', v_relationship, 'phone', v_phone)::text)
    ON CONFLICT (connection_id, category, granted_by_account_id)
    DO UPDATE SET granted_at = EXCLUDED.granted_at,
                  revoked_at = NULL,
                  shared_value = EXCLUDED.shared_value;
    RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION mangaly_connection.decide_family_contact_share(uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_connection.decide_family_contact_share(uuid, uuid, boolean) TO mangaly_app;
