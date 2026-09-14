-- 009 — Connection accept needs the OTHER party's real profile.id
--
-- [Fourth instance of the third RLS failure mode, found live 2026-09-14 —
-- same class as BLK-09-01/02/03] `connection.interface.accept()` must
-- create a `candidate_info` grant for EACH party, keyed on the OTHER
-- party's real `profile.id` (not their account id — see
-- `connection/models.py`'s module docstring for why `candidate_info`
-- specifically needs the real profile id). To build that grant, the
-- accepting party needs to resolve the OTHER party's `account_id` to their
-- `profile.id` — but `mangaly_profile.profile`'s own RLS
-- (`profile_owner_or_granted`) is exactly what has not been satisfied yet
-- for that party (the grant this whole call is trying to create is the
-- thing that would satisfy it), so a plain SELECT returns zero rows.
--
-- Fixed the same way as every prior instance: a narrow SECURITY DEFINER
-- function, exact-match only, minimal projection (the id column alone).

CREATE FUNCTION mangaly_profile.lookup_profile_id_by_account(
    p_account_id uuid
) RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_profile, pg_temp
AS $$
    SELECT id FROM mangaly_profile.profile WHERE account_id = p_account_id;
$$;

REVOKE ALL ON FUNCTION mangaly_profile.lookup_profile_id_by_account(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.lookup_profile_id_by_account(uuid) TO mangaly_app;
