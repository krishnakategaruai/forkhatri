-- =============================================================================
-- 004 — Pre-authorization session lookup function.
--
-- WHY (Step 9 finding, 2026-09-13, found by running /auth/me against the live
-- database rather than by reading the policy):
-- `session_self_only` restricts mangaly_identity.session to
--   account_id = current_setting('mangaly.account_id')
-- but validating a bearer token is by definition what RESOLVES that setting.
-- At validation time no account context exists yet, so the SELECT matched zero
-- rows, `validate_session()` returned None, and every authenticated request
-- failed with 401 — RLS silently returning "no rows" rather than an error,
-- which is exactly the fail-quiet shape TR017 warns about.
--
-- This is the SAME class of chicken-and-egg problem SP103 already documented
-- for `lookup_by_identifier()`: an inherently pre-authentication read cannot be
-- constrained by a predicate that only exists post-authentication. SP103
-- analysed it for the identifier lookup and did not extend the analysis to
-- session validation, which has the identical shape.
--
-- FIX: one more SECURITY DEFINER function, held to the same four constraints
-- SP103 imposes on its sibling, so this does not become a general escape hatch:
--   1. EXACT MATCH ONLY on the full session id — no pattern match, no range,
--      no caller-supplied predicate. The id is a server-generated UUIDv4 the
--      client never influences, so it is not guessable.
--   2. MINIMAL PROJECTION — returns account_id and nothing else. Not the row,
--      not expiry, not last_seen; a caller learns who, never anything more.
--   3. LIVENESS IS ENFORCED INSIDE THE FUNCTION, not by the caller: revoked or
--      expired sessions return zero rows, so a caller cannot forget to check
--      and cannot opt out of checking.
--   4. AT MOST ONE ROW.
--
-- Being SECURITY DEFINER, it runs as the owner and bypasses RLS by design —
-- which is precisely why the constraints above are structural rather than
-- conventional. `search_path` is pinned so the definer context cannot be
-- redirected at call time.
--
-- Idempotent and safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_identity.lookup_session(p_session_id uuid)
RETURNS TABLE (account_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
  SELECT s.account_id
  FROM mangaly_identity.session s
  WHERE s.id = p_session_id
    AND s.revoked_at IS NULL
    AND s.expires_at > now()
  LIMIT 1;
$$;

COMMENT ON FUNCTION mangaly_identity.lookup_session(uuid) IS
  '[TR090/SP103-class] Pre-authorization session validation. Exact-match on a server-generated session id, returns account_id only, and only for a session that is neither revoked nor expired. SECURITY DEFINER because validating the token is what establishes the context RLS would otherwise require. Frozen surface: changing its signature, projection or predicate needs security review, not ordinary review.';

REVOKE ALL ON FUNCTION mangaly_identity.lookup_session(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.lookup_session(uuid) TO mangaly_app;
