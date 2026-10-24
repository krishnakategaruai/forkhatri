-- =============================================================================
-- 065 — A parent may publish a son's or daughter's profile without the child's
--       own mobile number; the child takes it over later with consent.
--       Plus a place for a family's biodata and horoscope (jathakam) file.
--       (Owner, 2026-10-06: "yes, right — the parent is doing it, then he
--       should be able to". Changes DEC-V1-019; see v1-decisions.md.)
--
-- WHY:
--   Many daughters use a parent's phone, already use another ForKhatri module,
--   or the family prepares the profile quietly first. Requiring the child's own
--   number first stopped those families completely (ONBOARDING-REDESIGN-2026-10
--   §2 item 4).
--
-- HOW (additive; every existing path keeps working):
--   * When the parent gives a number that is free, nothing changes: 041's path
--     provisions the ForKhatri member for it and the child signs in to it.
--   * With no number (or a number that already belongs to a ForKhatri member),
--     Mangalya makes a "managed" account for the child with its own id and no
--     identifier (`managed_by_account_id` = the parent). The profile is the
--     parent's to run ("managed by her mother") until the child takes it over.
--   * `profile.pending_phone` holds the number the parent says is the child's.
--     When a member who signed in with exactly that number (proven by the
--     platform's OTP) opens Mangalya, they are asked; on "yes, this is me" an
--     `account_alias` row maps their ForKhatri member id to the profile's
--     account, consent time recorded, and the profile is claimed. From then on
--     the Identity Bridge binds that account for them (one indexed lookup).
--   * Never claimable by the person who made it, by anyone who already has a
--     Mangalya profile or a Home Circle membership, or twice.
-- =============================================================================

-- 1. A managed account may exist without a phone or email.
ALTER TABLE mangaly_identity.account
    ADD COLUMN IF NOT EXISTS managed_by_account_id uuid;

ALTER TABLE mangaly_identity.account
    DROP CONSTRAINT IF EXISTS account_has_identifier;
ALTER TABLE mangaly_identity.account
    ADD CONSTRAINT account_has_identifier
    CHECK (phone_identifier IS NOT NULL OR email_identifier IS NOT NULL
           OR status = 'deleted' OR managed_by_account_id IS NOT NULL);

-- 2. The number the parent gave for the child (E.164), until taken over.
ALTER TABLE mangaly_profile.profile
    ADD COLUMN IF NOT EXISTS pending_phone text;
CREATE INDEX IF NOT EXISTS idx_profile_pending_phone
    ON mangaly_profile.profile (pending_phone) WHERE pending_phone IS NOT NULL;

-- 3. ForKhatri member -> the Mangalya account they took over.
CREATE TABLE IF NOT EXISTS mangaly_identity.account_alias (
    member_id     uuid PRIMARY KEY,
    account_id    uuid NOT NULL UNIQUE,
    consented_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_identity.account_alias IS
  '[065, owner 2026-10-06] A child who took over a profile their parent made without their number: their ForKhatri member id maps to that profile''s account. consented_at = when they said "yes, this is me". Read only through alias_of().';
ALTER TABLE mangaly_identity.account_alias ENABLE ROW LEVEL SECURITY;
-- No policy and no grant: only the SECURITY DEFINER functions below touch it.

-- 4. Make a managed account for a child (caller = the parent).
CREATE OR REPLACE FUNCTION mangaly_identity.create_managed_account(
    p_account_id uuid,
    p_name       text
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
DECLARE
    v_maker uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
BEGIN
    IF v_maker IS NULL OR v_maker = p_account_id THEN
        RAISE EXCEPTION 'create_managed_account: must be called by another signed-in account';
    END IF;
    IF EXISTS (SELECT 1 FROM mangaly_identity.account WHERE id = p_account_id) THEN
        RAISE EXCEPTION 'create_managed_account: account already exists' USING ERRCODE = 'MGL09';
    END IF;
    INSERT INTO mangaly_identity.account (id, phone_identifier, status, display_name, managed_by_account_id)
    VALUES (p_account_id, NULL, 'active', p_name, v_maker);
END;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.create_managed_account(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.create_managed_account(uuid, text) TO mangaly_app;

-- 5. The parent records (or changes, or clears) the child's number.
CREATE OR REPLACE FUNCTION mangaly_profile.set_pending_phone(
    p_creator   uuid,
    p_candidate uuid,
    p_phone     text
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
BEGIN
    IF NOT mangaly_authz.is_self(p_creator) OR NOT mangaly_profile.can_manage(p_creator, p_candidate) THEN
        RETURN false;
    END IF;
    -- A parent's own number can never be the key to the child's profile.
    IF p_phone IS NOT NULL AND EXISTS (
        SELECT 1 FROM mangaly_identity.account WHERE id = p_creator AND phone_identifier = p_phone
    ) THEN
        RETURN false;
    END IF;
    UPDATE mangaly_profile.profile
       SET pending_phone = NULLIF(btrim(p_phone), ''), updated_at = now()
     WHERE account_id = p_candidate AND claimed_at IS NULL;
    RETURN FOUND;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.set_pending_phone(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.set_pending_phone(uuid, uuid, text) TO mangaly_app;

-- 6. Profiles waiting for the signed-in member's own (proven) number.
CREATE OR REPLACE FUNCTION mangaly_profile.made_for_my_number(p_member uuid)
RETURNS TABLE (account_id uuid, name text, creator_name text, relation text, primary_photo_ref text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
    SELECT p.account_id, p.name, c.display_name, m.relation,
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete'
             LIMIT 1)
      FROM mangaly_identity.account me
      JOIN mangaly_profile.profile p
        ON p.pending_phone = me.phone_identifier
       AND p.claimed_at IS NULL
       AND p.created_by_account_id IS DISTINCT FROM me.id
      LEFT JOIN mangaly_identity.account c ON c.id = p.created_by_account_id
      LEFT JOIN mangaly_home_circle.membership m
             ON m.candidate_profile_id = p.account_id
            AND m.member_account_id = p.created_by_account_id
            AND m.status = 'active'
     WHERE mangaly_authz.is_self(p_member)
       AND me.id = p_member
       AND me.phone_identifier IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM mangaly_identity.account_alias al WHERE al.member_id = p_member);
$$;
REVOKE ALL ON FUNCTION mangaly_profile.made_for_my_number(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.made_for_my_number(uuid) TO mangaly_app;

-- 7. "Yes, this is me": take the profile over, consent recorded.
--    Returns the creator's account id (to tell them), or NULL when refused.
CREATE OR REPLACE FUNCTION mangaly_profile.take_over_profile(p_member uuid, p_candidate uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
DECLARE
    v_phone   text;
    v_creator uuid;
BEGIN
    IF NOT mangaly_authz.is_self(p_member) THEN
        RETURN NULL;
    END IF;
    SELECT phone_identifier INTO v_phone FROM mangaly_identity.account WHERE id = p_member;
    IF v_phone IS NULL THEN
        RETURN NULL;
    END IF;
    -- Someone who already has a Mangalya life of their own keeps it.
    IF EXISTS (SELECT 1 FROM mangaly_profile.profile WHERE account_id = p_member)
       OR EXISTS (SELECT 1 FROM mangaly_home_circle.membership
                   WHERE member_account_id = p_member AND status = 'active')
       OR EXISTS (SELECT 1 FROM mangaly_identity.account_alias WHERE member_id = p_member) THEN
        RETURN NULL;
    END IF;
    SELECT created_by_account_id INTO v_creator
      FROM mangaly_profile.profile
     WHERE account_id = p_candidate
       AND pending_phone = v_phone
       AND claimed_at IS NULL
       AND created_by_account_id IS DISTINCT FROM p_member
     FOR UPDATE;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    INSERT INTO mangaly_identity.account_alias (member_id, account_id, consented_at)
    VALUES (p_member, p_candidate, now());
    UPDATE mangaly_profile.profile
       SET claimed_at = now(), pending_phone = NULL, updated_at = now()
     WHERE account_id = p_candidate;
    UPDATE mangaly_identity.account
       SET managed_by_account_id = NULL, updated_at = now()
     WHERE id = p_candidate;
    RETURN v_creator;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.take_over_profile(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.take_over_profile(uuid, uuid) TO mangaly_app;

-- 8. "This isn't me": the number is cleared; the parent keeps the profile.
CREATE OR REPLACE FUNCTION mangaly_profile.not_my_profile(p_member uuid, p_candidate uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
DECLARE
    v_creator uuid;
BEGIN
    IF NOT mangaly_authz.is_self(p_member) THEN
        RETURN NULL;
    END IF;
    UPDATE mangaly_profile.profile p
       SET pending_phone = NULL, updated_at = now()
      FROM mangaly_identity.account me
     WHERE me.id = p_member
       AND p.account_id = p_candidate
       AND p.pending_phone = me.phone_identifier
       AND p.claimed_at IS NULL
    RETURNING p.created_by_account_id INTO v_creator;
    RETURN v_creator;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.not_my_profile(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.not_my_profile(uuid, uuid) TO mangaly_app;

-- 9. Which Mangalya account a signed-in ForKhatri member acts as. Runs before
--    mangaly.account_id is bound (Identity Bridge), hence SECURITY DEFINER.
CREATE OR REPLACE FUNCTION mangaly_identity.alias_of(p_member uuid)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
    SELECT account_id FROM mangaly_identity.account_alias WHERE member_id = p_member;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.alias_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.alias_of(uuid) TO mangaly_app;

-- 10. The managed list shows the number the parent gave, masked, or nothing.
CREATE OR REPLACE FUNCTION mangaly_profile.managed_profiles_of(p_creator uuid)
RETURNS TABLE (account_id uuid, name text, primary_photo_ref text, phone_masked text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
    SELECT p.account_id,
           p.name,
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete'
             LIMIT 1),
           CASE WHEN COALESCE(a.phone_identifier, p.pending_phone) IS NULL THEN NULL
                ELSE left(COALESCE(a.phone_identifier, p.pending_phone), 3) || '••••••'
                     || right(COALESCE(a.phone_identifier, p.pending_phone), 4) END
      FROM mangaly_profile.profile p
      JOIN mangaly_identity.account a ON a.id = p.account_id
     WHERE mangaly_authz.is_self(p_creator)
       AND p.created_by_account_id = p_creator
       AND p.claimed_at IS NULL
     ORDER BY p.created_at;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.managed_profiles_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.managed_profiles_of(uuid) TO mangaly_app;

-- 11. A family's biodata or horoscope (jathakam) file, kept only when they
--     chose "attach" (Q3, 2026-10-06). Owner (or the managing parent, who acts
--     as the candidate under X-Mangalya-Manage) only.
CREATE TABLE IF NOT EXISTS mangaly_profile.profile_document (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id    uuid NOT NULL REFERENCES mangaly_profile.profile(id) ON DELETE CASCADE,
    kind          text NOT NULL CHECK (kind IN ('biodata', 'horoscope')),
    storage_ref   text NOT NULL,
    content_type  text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_profile_document_profile ON mangaly_profile.profile_document(profile_id);
ALTER TABLE mangaly_profile.profile_document ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS profile_document_owner ON mangaly_profile.profile_document;
CREATE POLICY profile_document_owner ON mangaly_profile.profile_document
  USING (EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.id = profile_document.profile_id
                 AND mangaly_authz.is_self(p.account_id)))
  WITH CHECK (EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.id = profile_document.profile_id
                 AND mangaly_authz.is_self(p.account_id)));
GRANT SELECT, INSERT, DELETE ON mangaly_profile.profile_document TO mangaly_app;
