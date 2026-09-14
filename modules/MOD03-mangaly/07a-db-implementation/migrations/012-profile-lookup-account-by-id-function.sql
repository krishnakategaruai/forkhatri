-- 012 — Connection send_request needs the OWNING account of an
-- on-behalf-of profile.id, to check Home Circle authorization
--
-- [Fifth instance of the third RLS failure mode, found live 2026-09-14 —
-- same class as BLK-09-01/02/03 and migration 009] FR042's own acceptance
-- criterion ("Unauthorized on-behalf-of requests are blocked") was
-- unimplemented: `connection.interface.send_request()` accepted
-- `on_behalf_of_profile_id` (a candidate's real `profile.id`) with no check
-- that the caller is actually an authorized Home Circle member of that
-- candidate at all. Closing that gap requires checking the caller's
-- `family_info` grant — but that grant's `target_profile_id` is stored as
-- the candidate's ACCOUNT id (see `home_circle/interface.py`'s own grant
-- call site: `target_profile_id=candidate_account_id`), while the caller
-- only has the candidate's real `profile.id` in hand. Resolving profile.id
-- -> account_id hits the exact same RLS bind as migration 009 in reverse: a
-- plain SELECT against `mangaly_profile.profile` is denied by
-- `profile_owner_or_granted` for a family member who does not yet hold
-- (and is precisely trying to be checked for) that grant.
--
-- Fixed the same way as every prior instance: a narrow SECURITY DEFINER
-- function, exact-match only, minimal projection (the account_id column
-- alone), no liveness/status filtering needed since `profile.account_id`
-- is immutable for the row's lifetime.

CREATE FUNCTION mangaly_profile.lookup_account_by_profile_id(
    p_profile_id uuid
) RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_profile, pg_temp
AS $$
    SELECT account_id FROM mangaly_profile.profile WHERE id = p_profile_id;
$$;

REVOKE ALL ON FUNCTION mangaly_profile.lookup_account_by_profile_id(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.lookup_account_by_profile_id(uuid) TO mangaly_app;
