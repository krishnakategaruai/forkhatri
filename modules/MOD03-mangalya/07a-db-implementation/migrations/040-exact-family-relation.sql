-- =============================================================================
-- 040 — Two levels of family relation: the ROLE and the EXACT relation
--       (product owner, 2026-09-21).
--
-- WHY:
--   The owner, looking at the Home Circle invite: "I am looking for profile
--   relation (mother, father, etc.), while relative is a role and inside we
--   have exact relations."
--
--   `relationship_type` (parent / guardian / sibling / relative) stays exactly
--   what it is: the ROLE. It groups the circle into Home and Relatives and is
--   what every existing check reads, so no permission changes here — the owner's
--   standing rule is that only profile-viewing style and messaging vary by
--   role, and that is untouched.
--
--   `relation` is new: the exact relation of the MEMBER TO THE CANDIDATE —
--   mother, father, brother, a father's-side uncle (chacha/tau, babai), a
--   mother's-side aunt (mausi, pinni)… Indian families name these precisely,
--   and a circle that says "Relative" where the family would say "Mama" reads
--   as a form, not a family. The role is derived from the relation by the
--   service (`RELATION_ROLE`), so the two can never disagree for new rows.
--
--   Nullable: memberships made before 040 only ever recorded a role, and the
--   app must not invent "father" for a row that said "parent". Those rows show
--   their role until the member states the exact relation.
-- =============================================================================

ALTER TABLE mangaly_home_circle.invitation ADD COLUMN IF NOT EXISTS relation text;
ALTER TABLE mangaly_home_circle.membership ADD COLUMN IF NOT EXISTS relation text;

ALTER TABLE mangaly_home_circle.invitation DROP CONSTRAINT IF EXISTS invitation_relation_known;
ALTER TABLE mangaly_home_circle.invitation ADD CONSTRAINT invitation_relation_known CHECK (
    relation IS NULL OR relation IN (
        'mother', 'father', 'brother', 'sister', 'guardian',
        'grandmother', 'grandfather',
        'paternal_uncle', 'maternal_uncle', 'paternal_aunt', 'maternal_aunt',
        'cousin', 'brother_in_law', 'sister_in_law', 'family_friend'
    )
);
ALTER TABLE mangaly_home_circle.membership DROP CONSTRAINT IF EXISTS membership_relation_known;
ALTER TABLE mangaly_home_circle.membership ADD CONSTRAINT membership_relation_known CHECK (
    relation IS NULL OR relation IN (
        'mother', 'father', 'brother', 'sister', 'guardian',
        'grandmother', 'grandfather',
        'paternal_uncle', 'maternal_uncle', 'paternal_aunt', 'maternal_aunt',
        'cousin', 'brother_in_law', 'sister_in_law', 'family_friend'
    )
);

-- ---------------------------------------------------------------------------
-- The four read/response functions gain a `relation` column. Return types
-- change, so each is dropped and recreated; bodies are 025/030's unchanged
-- apart from the added column.
-- ---------------------------------------------------------------------------

DROP FUNCTION IF EXISTS mangaly_home_circle.list_circle_members(uuid);
CREATE FUNCTION mangaly_home_circle.list_circle_members(p_candidate_account_id uuid)
RETURNS TABLE (
    membership_id uuid,
    member_account_id uuid,
    member_name text,
    relationship_type text,
    joined_at timestamptz,
    relation text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_identity, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT m.id,
           m.member_account_id,
           COALESCE(
               a.display_name,
               (SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = m.member_account_id)
           ),
           m.relationship_type::text,
           m.joined_at,
           m.relation
      FROM mangaly_home_circle.membership m
      LEFT JOIN mangaly_identity.account a ON a.id = m.member_account_id
     WHERE (
               mangaly_authz.is_self(p_candidate_account_id)
               OR mangaly_authz.has_scope(p_candidate_account_id, 'family_info')
           )
       AND m.candidate_profile_id = p_candidate_account_id
       AND m.status = 'active'
     ORDER BY m.joined_at;
$$;
REVOKE ALL ON FUNCTION mangaly_home_circle.list_circle_members(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_circle_members(uuid) TO mangaly_app;

DROP FUNCTION IF EXISTS mangaly_home_circle.list_pending_invitations_for(uuid, text[]);
CREATE FUNCTION mangaly_home_circle.list_pending_invitations_for(
    p_account_id uuid,
    p_identifiers text[]
) RETURNS TABLE (
    id uuid,
    candidate_profile_id uuid,
    inviter_account_id uuid,
    relationship_type mangaly_home_circle.relationship_type,
    created_at timestamptz,
    expires_at timestamptz,
    direction text,
    inviter_name text,
    candidate_name text,
    relation text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_identity, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT i.id,
           i.candidate_profile_id,
           i.inviter_account_id,
           i.relationship_type,
           i.created_at,
           i.expires_at,
           i.direction,
           COALESCE(ia.display_name,
                    (SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = i.inviter_account_id)),
           COALESCE((SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = i.candidate_profile_id),
                    ca.display_name),
           i.relation
      FROM mangaly_home_circle.invitation i
      LEFT JOIN mangaly_identity.account ia ON ia.id = i.inviter_account_id
      LEFT JOIN mangaly_identity.account ca ON ca.id = i.candidate_profile_id
     WHERE mangaly_authz.is_self(p_account_id)
       AND i.status = 'pending'
       AND (i.expires_at IS NULL OR i.expires_at > now())
       AND (i.invitee_account_id = p_account_id OR i.invitee_identifier = ANY(p_identifiers))
     ORDER BY i.created_at DESC;
$$;
REVOKE ALL ON FUNCTION mangaly_home_circle.list_pending_invitations_for(uuid, text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_pending_invitations_for(uuid, text[]) TO mangaly_app;

DROP FUNCTION IF EXISTS mangaly_home_circle.respond_to_invitation(uuid, uuid, text[], mangaly_home_circle.invitation_status);
CREATE FUNCTION mangaly_home_circle.respond_to_invitation(
    p_invitation_id uuid,
    p_account_id uuid,
    p_identifiers text[],
    p_response mangaly_home_circle.invitation_status
) RETURNS TABLE (
    candidate_profile_id uuid,
    relationship_type mangaly_home_circle.relationship_type,
    inviter_account_id uuid,
    direction text,
    relation text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_authz, pg_temp
AS $$
DECLARE
    v_candidate uuid;
    v_relationship mangaly_home_circle.relationship_type;
    v_inviter uuid;
    v_direction text;
    v_relation text;
BEGIN
    IF p_response NOT IN ('accepted', 'declined') THEN
        RAISE EXCEPTION 'respond_to_invitation: p_response must be accepted or declined';
    END IF;
    IF mangaly_authz.is_self(p_account_id) IS NOT TRUE THEN
        RETURN;
    END IF;

    UPDATE mangaly_home_circle.invitation AS inv
    SET status = p_response,
        invitee_account_id = p_account_id,
        updated_at = now()
    WHERE inv.id = p_invitation_id
      AND inv.status = 'pending'
      AND (inv.invitee_account_id = p_account_id OR inv.invitee_identifier = ANY(p_identifiers))
      AND (inv.expires_at IS NULL OR inv.expires_at > now())
    RETURNING inv.candidate_profile_id, inv.relationship_type, inv.inviter_account_id, inv.direction, inv.relation
    INTO v_candidate, v_relationship, v_inviter, v_direction, v_relation;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    RETURN QUERY SELECT v_candidate, v_relationship, v_inviter, v_direction, v_relation;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_home_circle.respond_to_invitation(uuid, uuid, text[], mangaly_home_circle.invitation_status) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.respond_to_invitation(uuid, uuid, text[], mangaly_home_circle.invitation_status) TO mangaly_app;

DROP FUNCTION IF EXISTS mangaly_home_circle.list_member_contexts(uuid);
CREATE FUNCTION mangaly_home_circle.list_member_contexts(p_member_account_id uuid)
RETURNS TABLE (
    membership_id uuid,
    candidate_account_id uuid,
    candidate_profile_id uuid,
    candidate_name text,
    relationship_type text,
    joined_at timestamptz,
    member_count integer,
    looking_for text,
    primary_photo_ref text,
    relation text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_profile, mangaly_identity, mangaly_discovery, mangaly_authz, pg_temp
AS $$
    SELECT DISTINCT ON (m.candidate_profile_id)
           m.id,
           m.candidate_profile_id,
           p.id,
           COALESCE(p.name, a.display_name),
           m.relationship_type::text,
           m.joined_at,
           (SELECT count(*)::integer FROM mangaly_home_circle.membership x
             WHERE x.candidate_profile_id = m.candidate_profile_id AND x.status = 'active'),
           (SELECT i.ranking_input_snapshot->>'looking_for'
              FROM mangaly_discovery.discovery_profile_index i
             WHERE i.profile_id = m.candidate_profile_id),
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete'
             LIMIT 1),
           m.relation
      FROM mangaly_home_circle.membership m
      LEFT JOIN mangaly_profile.profile p ON p.account_id = m.candidate_profile_id
      LEFT JOIN mangaly_identity.account a ON a.id = m.candidate_profile_id
     WHERE mangaly_authz.is_self(p_member_account_id)
       AND m.member_account_id = p_member_account_id
       AND m.status = 'active'
     ORDER BY m.candidate_profile_id, m.joined_at;
$$;
REVOKE ALL ON FUNCTION mangaly_home_circle.list_member_contexts(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_member_contexts(uuid) TO mangaly_app;
