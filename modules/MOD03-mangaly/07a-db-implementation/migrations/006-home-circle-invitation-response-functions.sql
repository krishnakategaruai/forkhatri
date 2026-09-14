-- 006 — Home Circle invitation-response escape hatches
--
-- [Third RLS failure mode, found live 2026-09-13 — same class as BLK-09-01/
-- BLK-09-02, documented generically in /MODULE-ARCHITECTURE-STANDARD.md ss4]
-- `hc_invitation_participants` grants access via
-- is_self(inviter_account_id) OR is_self(invitee_account_id) OR
-- is_self(candidate_profile_id) — but a PENDING invitation only ever carries
-- `invitee_identifier` (a phone/email string, per TR007's confirmed no-
-- directory-search fallback); `invitee_account_id` stays NULL until
-- acceptance. The invitee therefore satisfies none of the three predicates
-- before responding, so a plain SELECT/UPDATE from their own authenticated
-- session returns zero rows and fails silently — the same "must read/write
-- before the row can prove who you are" bind as account creation and
-- session validation. Fixed the same way: a narrow SECURITY DEFINER escape
-- hatch, held to the same four constraints already named for its two
-- predecessors (exact-match only, minimal projection, liveness enforced
-- inside the function, at most one row).
--
-- Raised against Step 7a for ratification; resolved forward here.

CREATE FUNCTION mangaly_home_circle.list_pending_invitations_for_identifiers(
    p_identifiers text[]
) RETURNS TABLE (
    id uuid,
    candidate_profile_id uuid,
    inviter_account_id uuid,
    relationship_type mangaly_home_circle.relationship_type,
    created_at timestamptz,
    expires_at timestamptz
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = mangaly_home_circle, pg_temp
AS $$
    SELECT id, candidate_profile_id, inviter_account_id, relationship_type, created_at, expires_at
    FROM mangaly_home_circle.invitation
    WHERE invitee_identifier = ANY(p_identifiers)
      AND status = 'pending'
      AND (expires_at IS NULL OR expires_at > now());
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.list_pending_invitations_for_identifiers(text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_pending_invitations_for_identifiers(text[]) TO mangaly_app;

-- Handles both accept and decline in one function: both are "the invitee
-- responds," and both need the identical exact-match + liveness guard —
-- two near-identical functions would be the two-copies-that-can-drift
-- pattern this module's standard already warns about elsewhere.
CREATE FUNCTION mangaly_home_circle.respond_to_invitation(
    p_invitation_id uuid,
    p_account_id uuid,
    p_identifiers text[],
    p_response mangaly_home_circle.invitation_status
) RETURNS TABLE (
    candidate_profile_id uuid,
    relationship_type mangaly_home_circle.relationship_type
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_home_circle, pg_temp
AS $$
DECLARE
    v_candidate uuid;
    v_relationship mangaly_home_circle.relationship_type;
BEGIN
    IF p_response NOT IN ('accepted', 'declined') THEN
        RAISE EXCEPTION 'respond_to_invitation: p_response must be accepted or declined';
    END IF;

    UPDATE mangaly_home_circle.invitation AS inv
    SET status = p_response,
        invitee_account_id = p_account_id,
        updated_at = now()
    WHERE inv.id = p_invitation_id
      AND inv.status = 'pending'
      AND inv.invitee_identifier = ANY(p_identifiers)
      AND (inv.expires_at IS NULL OR inv.expires_at > now())
    RETURNING inv.candidate_profile_id, inv.relationship_type
    INTO v_candidate, v_relationship;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    RETURN QUERY SELECT v_candidate, v_relationship;
END;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.respond_to_invitation(uuid, uuid, text[], mangaly_home_circle.invitation_status) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.respond_to_invitation(uuid, uuid, text[], mangaly_home_circle.invitation_status) TO mangaly_app;
