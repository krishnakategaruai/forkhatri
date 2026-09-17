-- =============================================================================
-- 016 — Family contact sharing needs the family member's own decision
--       (FR048 / TR048).
--
-- WHY (2026-09-15):
--   * A candidate may ask to share a Home Circle member's phone with a
--     connection, but only that member may say yes. The candidate's session
--     writes the request row (`family_contact_share` RLS already allows the
--     candidate), and the member decides in their own session.
--   * Approval must also create the recipient-visible `sharing_grant` row in
--     the CANDIDATE's name, which the member's session cannot write under
--     migration 015's WITH CHECK, and must read the member's own phone from
--     `mangaly_identity.account`. Both are done here, in one SECURITY DEFINER
--     function held to the same rules as migration 010: every value is
--     re-derived from rows, the caller must be the member named on the
--     request, the membership and the connection must still be live, and one
--     row changes.
--   * A member needs to see who is asking without holding a grant on the
--     candidate's profile, so the pending list is a narrow SECURITY DEFINER
--     read of the caller's own requests only.
--   * `declined_at` records a "no" instead of deleting the request, and a
--     unique key stops duplicate requests for the same member and connection.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_connection.family_contact_share
  ADD COLUMN IF NOT EXISTS declined_at timestamptz;

DO $$ BEGIN
  ALTER TABLE mangaly_connection.family_contact_share
    ADD CONSTRAINT family_contact_share_one_per_member
    UNIQUE (connection_id, candidate_account_id, family_member_account_id);
EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION mangaly_connection.list_family_contact_requests(p_family_account_id uuid)
RETURNS TABLE (
    share_id uuid,
    candidate_account_id uuid,
    candidate_name text,
    relationship_type text,
    requested_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_connection, mangaly_home_circle, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT s.id,
           s.candidate_account_id,
           (SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = s.candidate_account_id),
           (SELECT m.relationship_type::text
              FROM mangaly_home_circle.membership m
             WHERE m.candidate_profile_id = s.candidate_account_id
               AND m.member_account_id = s.family_member_account_id
               AND m.status = 'active'
             LIMIT 1),
           s.candidate_authz_resolved_at
      FROM mangaly_connection.family_contact_share s
     WHERE mangaly_authz.is_self(p_family_account_id)
       AND s.family_member_account_id = p_family_account_id
       AND s.candidate_authz_resolved_at IS NOT NULL
       AND s.family_authz_resolved_at IS NULL
       AND s.declined_at IS NULL
       AND EXISTS (SELECT 1 FROM mangaly_home_circle.membership m
                    WHERE m.candidate_profile_id = s.candidate_account_id
                      AND m.member_account_id = s.family_member_account_id
                      AND m.status = 'active')
       AND EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                    WHERE c.id = s.connection_id AND c.status = 'accepted')
     ORDER BY s.candidate_authz_resolved_at;
$$;

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
    IF NOT mangaly_authz.is_self(p_family_account_id) THEN
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

    SELECT phone_identifier INTO v_phone FROM mangaly_identity.account WHERE id = p_family_account_id;
    IF v_phone IS NULL THEN
        RETURN false;
    END IF;
    SELECT name INTO v_name FROM mangaly_profile.profile WHERE account_id = p_family_account_id;

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

REVOKE ALL ON FUNCTION mangaly_connection.list_family_contact_requests(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_connection.list_family_contact_requests(uuid) TO mangaly_app;
REVOKE ALL ON FUNCTION mangaly_connection.decide_family_contact_share(uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_connection.decide_family_contact_share(uuid, uuid, boolean) TO mangaly_app;
