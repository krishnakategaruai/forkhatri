-- 008 — Home Circle: let the candidate actually perform the forward-approval
--
-- Migration 007 let the candidate discover their own pending note ids
-- without exposing content. But approving one hits the same RLS bind: a
-- plain UPDATE on a not-yet-forwarded note fails `hc_note_family_or_forwarded`
-- for the candidate (their read/write matches neither `has_scope` — they
-- hold no grant on themselves — nor the forwarded-clause, since forwarding
-- is exactly what has not happened yet). Same third-failure-mode class as
-- migrations 006/007's functions; same fix.

CREATE FUNCTION mangaly_home_circle.approve_note_forward(
    p_note_id uuid
) RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_home_circle, pg_temp
AS $$
    UPDATE mangaly_home_circle.home_circle_note
    SET forwarded_at = now()
    WHERE id = p_note_id
      AND candidate_profile_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
      AND forwarded_at IS NULL
    RETURNING true;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.approve_note_forward(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.approve_note_forward(uuid) TO mangaly_app;
