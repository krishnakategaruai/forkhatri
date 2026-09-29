-- =============================================================================
-- 030 — Roles are relations to a candidate, held per membership; every account
--       is a full user; a family member may invite a candidate (DEC-V1-022).
--
-- WHY (2026-09-17, product owner, rework contract §1/§6):
--   * "Roles are relations to a particular candidate, a person can hold several
--     at once." The membership row already carries `relationship_type` per
--     (candidate, member); this migration adds `guardian` to that vocabulary
--     and stops every read that assumed "a family member has no profile" or
--     "a candidate always has a profile".
--   * "A parent ... is also a user; he still can search users and add them into
--     a circle." A person with no profile and no circle must be able to start a
--     circle by inviting the candidate. `invitation.direction` records which
--     way an invitation runs:
--       - `to_member`    (existing): the candidate, or a member of their circle,
--                         invites someone to join the candidate's circle;
--       - `to_candidate` (new):      someone invites a candidate to let them
--                         join THAT candidate's circle. `candidate_profile_id`
--                         is the invitee's account; on acceptance the inviter
--                         becomes the member.
--   * People are found by name or phone (`search_people`), so an invitation may
--     name the invitee's account directly (`invitee_account_id` set at invite
--     time) as well as by phone/email string. Both response functions match on
--     either.
--   * `list_member_contexts()` now LEFT JOINs the profile (a candidate invited
--     before creating a profile still appears, named from the platform display
--     name) and returns what the identity payload needs: the real profile id,
--     the main photo reference, the candidate's "looking for" and the circle's
--     member count. Same rules as 017/019/025: caller must be the member, values
--     come from rows, minimal projection.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TYPE mangaly_home_circle.relationship_type ADD VALUE IF NOT EXISTS 'guardian';

ALTER TABLE mangaly_home_circle.invitation
  ADD COLUMN IF NOT EXISTS direction text NOT NULL DEFAULT 'to_member';

DO $$ BEGIN
  ALTER TABLE mangaly_home_circle.invitation
    ADD CONSTRAINT invitation_direction_check CHECK (direction IN ('to_member', 'to_candidate'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_hc_invitation_invitee_account
  ON mangaly_home_circle.invitation (invitee_account_id, status);

-- ---------------------------------------------------------------------------
-- Pending invitations addressed to the caller: by identifier OR by account id.
-- Returns the names the invitee needs to decide (who invites, for whom).
-- ---------------------------------------------------------------------------
DROP FUNCTION IF EXISTS mangaly_home_circle.list_pending_invitations_for_identifiers(text[]);
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
    candidate_name text
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
                    ca.display_name)
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

-- ---------------------------------------------------------------------------
-- Respond (accept/decline). Returns enough for the caller to create the
-- membership in the right direction.
-- ---------------------------------------------------------------------------
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
    direction text
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
    RETURNING inv.candidate_profile_id, inv.relationship_type, inv.inviter_account_id, inv.direction
    INTO v_candidate, v_relationship, v_inviter, v_direction;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    RETURN QUERY SELECT v_candidate, v_relationship, v_inviter, v_direction;
END;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.respond_to_invitation(uuid, uuid, text[], mangaly_home_circle.invitation_status) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.respond_to_invitation(uuid, uuid, text[], mangaly_home_circle.invitation_status) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- A membership created by an ACCEPTED `to_candidate` invitation is inserted by
-- the candidate's session, but names the inviter as the member. The membership
-- RLS policy (`hc_membership_participants`) admits the candidate, so a plain
-- INSERT works; the family_info grant, however, must be written for the
-- inviter (subject) on the candidate (target) — `mangaly_authz.grant`'s policy
-- admits is_self(target) too, so a plain INSERT through the authz interface
-- also works. Nothing else to add here.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- The circles a member acts in, with what the identity payload needs.
-- ---------------------------------------------------------------------------
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
    primary_photo_ref text
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
             LIMIT 1)
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

-- ---------------------------------------------------------------------------
-- The candidate's main photo for a circle member's context switcher: served
-- by the media route only when the reference is that candidate's main photo
-- and the caller is an active member of their circle.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_home_circle.is_candidate_primary_photo_for_member(p_storage_ref text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM mangaly_profile.profile_media pm
          JOIN mangaly_profile.profile p ON p.id = pm.profile_id
          JOIN mangaly_home_circle.membership m ON m.candidate_profile_id = p.account_id
         WHERE pm.storage_ref = p_storage_ref
           AND pm.is_primary
           AND pm.media_type::text = 'photo'
           AND m.status = 'active'
           AND mangaly_authz.is_self(m.member_account_id)
    );
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.is_candidate_primary_photo_for_member(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.is_candidate_primary_photo_for_member(text) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- People search for circles (rework contract §6). The identity service offers
-- only an id-based member lookup, so this searches Mangaly's own member-link
-- rows (id = platform member id) by name or phone. Requires a signed-in
-- caller; never returns the caller; masks the phone; at most 20 rows.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_identity.search_people(p_q text)
RETURNS TABLE (
    account_id uuid,
    display_name text,
    phone_masked text,
    has_profile boolean
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_identity, mangaly_profile, pg_temp
AS $$
    WITH q AS (
        SELECT btrim(p_q) AS name_q,
               regexp_replace(p_q, '\D', '', 'g') AS digits_q,
               NULLIF(current_setting('mangaly.account_id', true), '')::uuid AS me
    )
    SELECT a.id,
           COALESCE(a.display_name, p.name),
           CASE WHEN a.phone_identifier IS NULL THEN NULL
                ELSE left(a.phone_identifier, 3) || '••••••' || right(a.phone_identifier, 4) END,
           p.id IS NOT NULL
      FROM mangaly_identity.account a
      LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id
      CROSS JOIN q
     WHERE q.me IS NOT NULL
       AND a.id <> q.me
       AND a.status = 'active'
       AND char_length(q.name_q) >= 2
       AND (
             COALESCE(a.display_name, p.name, '') ILIKE '%' || q.name_q || '%'
          OR (char_length(q.digits_q) >= 4
              AND regexp_replace(COALESCE(a.phone_identifier, ''), '\D', '', 'g') LIKE '%' || q.digits_q || '%')
          OR (position('@' in q.name_q) > 1 AND a.email_identifier = lower(q.name_q))
       )
     ORDER BY COALESCE(a.display_name, p.name)
     LIMIT 20;
$$;

REVOKE ALL ON FUNCTION mangaly_identity.search_people(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.search_people(text) TO mangaly_app;

-- The identifier of a person chosen from people search, so an invitation by
-- account id also carries the phone/email the response functions match on.
CREATE OR REPLACE FUNCTION mangaly_identity.primary_identifier_of(p_account_id uuid)
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
    SELECT COALESCE(a.phone_identifier, a.email_identifier)
      FROM mangaly_identity.account a
     WHERE a.id = p_account_id
       AND a.status = 'active'
       AND NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL;
$$;

REVOKE ALL ON FUNCTION mangaly_identity.primary_identifier_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.primary_identifier_of(uuid) TO mangaly_app;

-- The account behind a phone/email typed into the invite form, so an invitation
-- can notify that person and, for `to_candidate`, name the candidate's account.
CREATE OR REPLACE FUNCTION mangaly_identity.account_id_for_identifier(p_identifier text)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
    SELECT a.id
      FROM mangaly_identity.account a
     WHERE (a.phone_identifier = btrim(p_identifier) OR a.email_identifier = lower(btrim(p_identifier)))
       AND a.status = 'active'
       AND NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
     LIMIT 1;
$$;

REVOKE ALL ON FUNCTION mangaly_identity.account_id_for_identifier(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.account_id_for_identifier(text) TO mangaly_app;
