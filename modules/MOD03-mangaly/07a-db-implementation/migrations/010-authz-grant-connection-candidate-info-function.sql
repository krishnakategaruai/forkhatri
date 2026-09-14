-- 010 — Connection accept needs a cross-party grant escape hatch
--
-- [Fifth instance of the third RLS failure mode, found live 2026-09-14 —
-- and a genuinely new sub-case of it] `connection.interface.accept()` must
-- create TWO `candidate_info` grants on acceptance, one per direction. The
-- accepting party's OWN session can insert a grant where THEY are the
-- `subject_id` (an ordinary self-authored "I may see X" row — this already
-- works through `authz.grant()`'s normal `mangaly_authz.grant` RLS, no
-- escape hatch needed). But the SECOND grant — subject = the OTHER party,
-- target = the accepting party's own real `profile.id` — cannot be
-- inserted by either party's own session at all:
-- `grant_visible_to_subject_or_target`'s `is_self(subject_id) OR
-- is_self(target_profile_id)` only ever matches the CURRENT session's own
-- ACCOUNT id, but `candidate_info`'s `target_profile_id` must hold the real
-- `profile.id` (a different id space — see `connection/models.py`'s module
-- docstring) for `mangaly_profile.profile`'s own RLS to later honour it.
-- Neither `is_self()` clause can ever be satisfied by anyone for that row:
-- not the accepting party (their account id isn't the subject, and their
-- profile id isn't equal to their own account id), not the other party
-- either (they aren't in the transaction at all). This is a genuine,
-- structural id-space mismatch in the sealed schema, not an application
-- bug — raised against Step 7a for ratification.
--
-- Fixed with one SECURITY DEFINER function that creates both directions of
-- the grant atomically, re-deriving every value itself from the connection
-- row rather than trusting caller-supplied ids: exact-match on an
-- `accepted` connection the caller is actually a participant in (so this
-- cannot be used to grant visibility into an arbitrary, unrelated pair),
-- minimal work (nothing returned), one connection row only.

CREATE FUNCTION mangaly_authz.grant_connection_candidate_info(
    p_connection_id uuid,
    p_caller_account_id uuid
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_authz, mangaly_connection, mangaly_profile, pg_temp
AS $$
DECLARE
    v_acting_account_id uuid;
    v_target_account_id uuid;
    v_acting_profile_id uuid;
    v_target_profile_id uuid;
BEGIN
    SELECT acting_account_id, target_profile_id
    INTO v_acting_account_id, v_target_account_id
    FROM mangaly_connection.connection_request
    WHERE id = p_connection_id
      AND status = 'accepted'
      AND (acting_account_id = p_caller_account_id OR target_profile_id = p_caller_account_id);

    IF v_acting_account_id IS NULL THEN
        RETURN; -- not an accepted connection the caller is actually part of
    END IF;

    SELECT id INTO v_acting_profile_id FROM mangaly_profile.profile WHERE account_id = v_acting_account_id;
    SELECT id INTO v_target_profile_id FROM mangaly_profile.profile WHERE account_id = v_target_account_id;

    IF v_acting_profile_id IS NULL OR v_target_profile_id IS NULL THEN
        RETURN;
    END IF;

    INSERT INTO mangaly_authz.grant
        (id, subject_id, target_profile_id, scope, grant_type, status, source_component, source_reference_id)
    VALUES
        (gen_random_uuid(), v_target_account_id, v_acting_profile_id, 'candidate_info',
         'connection_accepted', 'active', 'connection', p_connection_id);

    INSERT INTO mangaly_authz.grant
        (id, subject_id, target_profile_id, scope, grant_type, status, source_component, source_reference_id)
    VALUES
        (gen_random_uuid(), v_acting_account_id, v_target_profile_id, 'candidate_info',
         'connection_accepted', 'active', 'connection', p_connection_id);
END;
$$;

REVOKE ALL ON FUNCTION mangaly_authz.grant_connection_candidate_info(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_authz.grant_connection_candidate_info(uuid, uuid) TO mangaly_app;
