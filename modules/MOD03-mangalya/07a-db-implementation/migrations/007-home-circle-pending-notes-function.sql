-- 007 — Home Circle: let a candidate discover their own unforwarded notes
--
-- FR016 requires the candidate's explicit approval BEFORE a note's content
-- becomes visible to them — `hc_note_family_or_forwarded`'s RLS already
-- enforces that half correctly (a not-yet-forwarded note is invisible to
-- the candidate). But that leaves the candidate with no way to even
-- discover that an unforwarded note EXISTS in order to approve it: they
-- cannot SELECT the row (RLS hides it) and therefore cannot learn its id.
--
-- Fixed with a minimal-projection SECURITY DEFINER function returning only
-- `(id, created_at)` for a candidate's own unforwarded notes — never the
-- content, never the author's identity, so approving is a genuinely blind
-- decision to trust family judgement, not a preview that defeats the
-- approval gate. This is the same escape-hatch class as migration 006's two
-- functions, held to the same constraints.

-- No caller-supplied candidate id: the function reads `mangaly.account_id`
-- itself (already bound by `api/deps.py`'s per-request authentication) so it
-- can only ever return the CALLING account's own pending notes. A version
-- that took a candidate id as a parameter would let any authenticated
-- caller probe whether an arbitrary account has pending notes — a real,
-- if minor, enumeration leak this avoids by construction rather than by a
-- caller-side check that could be forgotten.
CREATE FUNCTION mangaly_home_circle.list_own_pending_notes()
RETURNS TABLE (
    id uuid,
    created_at timestamptz
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_home_circle, pg_temp
AS $$
    SELECT id, created_at
    FROM mangaly_home_circle.home_circle_note
    WHERE candidate_profile_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
      AND forwarded_at IS NULL
    ORDER BY created_at DESC;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.list_own_pending_notes() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_own_pending_notes() TO mangaly_app;
