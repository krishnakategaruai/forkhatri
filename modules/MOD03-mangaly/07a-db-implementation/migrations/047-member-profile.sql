-- 047 — Every account has its own Mangaly "My profile" (DEC-V1-027)
--
-- Owner, 2026-09-22: "basic authentication of login happens in ForKhatri and
-- each module has its own way of my profile." A parent, sibling or relative
-- who is not looking for a match still signs up in ForKhatri, logs into
-- Mangaly, and has a Mangaly profile of their own: a photo of themselves, a
-- line about them, their city and work. It is not a candidate profile: it is
-- never searchable, never matched, and carries no biodata. It is how the
-- families they meet in Mangaly see who they are talking to, and it is what a
-- parent's face check compares against before they may make a profile for
-- their child (DEC-V1-025).
--
-- Who sees a member's photo: the member, and the people Mangaly lets them
-- message (their own family and the families of accepted connections, the
-- same link that allows a direct chat, migration 046).

CREATE TABLE IF NOT EXISTS mangaly_profile.member_profile (
    account_id  uuid PRIMARY KEY,
    photo_ref   text,
    about       text CHECK (about IS NULL OR length(about) <= 500),
    city        text CHECK (city IS NULL OR length(city) <= 200),
    occupation  text CHECK (occupation IS NULL OR length(occupation) <= 200),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_profile.member_profile IS
  '[DEC-V1-027] The Mangaly profile of an account that is not a candidate (a parent, sibling or relative). Never searchable; no biodata.';

ALTER TABLE mangaly_profile.member_profile ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_profile_owner ON mangaly_profile.member_profile;
CREATE POLICY member_profile_owner ON mangaly_profile.member_profile
  USING (account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid)
  WITH CHECK (account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
GRANT SELECT, INSERT, UPDATE, DELETE ON mangaly_profile.member_profile TO mangaly_app;

-- May the signed-in account load this member photo?
CREATE OR REPLACE FUNCTION mangaly_profile.is_member_photo_visible(p_ref text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_communication, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_profile.member_profile mp
         WHERE mp.photo_ref = p_ref
           AND (mp.account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
                OR mangaly_communication.can_direct(mp.account_id)
                OR EXISTS (SELECT 1 FROM mangaly_communication.conversation_participant a
                             JOIN mangaly_communication.conversation_participant b
                               ON b.conversation_id = a.conversation_id
                            WHERE a.account_id = mp.account_id
                              AND b.account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid)));
$$;
REVOKE ALL ON FUNCTION mangaly_profile.is_member_photo_visible(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.is_member_photo_visible(text) TO mangaly_app;

-- Member photos for a set of accounts, only those the caller may see: used to
-- put a face on chat rosters, the "New message" list and circle members.
CREATE OR REPLACE FUNCTION mangaly_profile.member_photos(p_ids uuid[])
RETURNS TABLE (account_id uuid, photo_ref text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, pg_temp
AS $$
    SELECT mp.account_id, mp.photo_ref
      FROM mangaly_profile.member_profile mp
     WHERE mp.account_id = ANY (p_ids)
       AND mp.photo_ref IS NOT NULL
       AND mangaly_profile.is_member_photo_visible(mp.photo_ref);
$$;
REVOKE ALL ON FUNCTION mangaly_profile.member_photos(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.member_photos(uuid[]) TO mangaly_app;

-- The face check for a member. Verification rows elsewhere are keyed by the
-- candidate profile, so a member's result lives here: outcome and dates only,
-- never an image or an embedding (DEC-V1-016).
CREATE TABLE IF NOT EXISTS mangaly_trust.member_face_match (
    account_id   uuid PRIMARY KEY,
    verified_at  timestamptz NOT NULL,
    expires_at   timestamptz NOT NULL
);
ALTER TABLE mangaly_trust.member_face_match ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_face_match_owner ON mangaly_trust.member_face_match;
CREATE POLICY member_face_match_owner ON mangaly_trust.member_face_match
  FOR SELECT USING (account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
GRANT SELECT ON mangaly_trust.member_face_match TO mangaly_app;

-- A new member photo was never compared, so it removes the confirmation.
CREATE OR REPLACE FUNCTION mangaly_trust.member_face_match_void_on_new_photo()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_trust, pg_temp
AS $$
BEGIN
    IF NEW.photo_ref IS DISTINCT FROM OLD.photo_ref THEN
        DELETE FROM mangaly_trust.member_face_match WHERE account_id = NEW.account_id;
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_trust.member_face_match_void_on_new_photo() FROM PUBLIC;
DROP TRIGGER IF EXISTS trg_member_face_match_void ON mangaly_profile.member_profile;
CREATE TRIGGER trg_member_face_match_void
    AFTER UPDATE OF photo_ref ON mangaly_profile.member_profile
    FOR EACH ROW EXECUTE FUNCTION mangaly_trust.member_face_match_void_on_new_photo();

-- Status: a candidate is checked against their profile photos (unchanged); an
-- account without a candidate profile is checked against its member photo.
CREATE OR REPLACE FUNCTION mangaly_trust.face_match_status(p_account uuid)
RETURNS TABLE (
    has_profile     boolean,
    verified        boolean,
    verified_at     timestamptz,
    expires_at      timestamptz,
    consent_at      timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = mangaly_trust, mangaly_profile, mangaly_authz, pg_temp
AS $$
DECLARE
    v_profile uuid;
    v_member_photo text;
BEGIN
    IF mangaly_authz.is_self(p_account) IS NOT TRUE THEN
        RAISE EXCEPTION 'face match status is readable by the person only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    SELECT p.id INTO v_profile FROM mangaly_profile.profile p WHERE p.account_id = p_account;

    IF v_profile IS NULL THEN
        SELECT mp.photo_ref INTO v_member_photo
          FROM mangaly_profile.member_profile mp WHERE mp.account_id = p_account;
        RETURN QUERY
        SELECT v_member_photo IS NOT NULL,
               m.account_id IS NOT NULL,
               m.verified_at,
               m.expires_at,
               (SELECT c.granted_at FROM mangaly_trust.biometric_consent c
                 WHERE c.account_id = p_account
                   AND c.purpose = 'face_match_own_photos'
                   AND c.withdrawn_at IS NULL)
          FROM (SELECT 1) one
          LEFT JOIN mangaly_trust.member_face_match m
            ON m.account_id = p_account AND m.expires_at > now();
        RETURN;
    END IF;

    RETURN QUERY
    SELECT true,
           v.id IS NOT NULL,
           v.verified_at,
           v.freshness_expires_at,
           (SELECT c.granted_at FROM mangaly_trust.biometric_consent c
             WHERE c.account_id = p_account
               AND c.purpose = 'face_match_own_photos'
               AND c.withdrawn_at IS NULL)
      FROM (SELECT 1) one
      LEFT JOIN mangaly_trust.verification_layer_status v
        ON v.profile_id = v_profile
       AND v.layer = 'profile_facts'
       AND v.source_category = 'face_match'
       AND v.status = 'verified'
       AND (v.freshness_expires_at IS NULL OR v.freshness_expires_at > now());
END;
$$;
REVOKE ALL ON FUNCTION mangaly_trust.face_match_status(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_trust.face_match_status(uuid) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_trust.record_face_match(
    p_account         uuid,
    p_passed          boolean,
    p_notice_version  text
)
RETURNS TABLE (
    verified     boolean,
    verified_at  timestamptz,
    expires_at   timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_trust, mangaly_profile, mangaly_authz, pg_temp
AS $$
DECLARE
    v_profile uuid;
    v_member_photo text;
BEGIN
    IF mangaly_authz.is_self(p_account) IS NOT TRUE THEN
        RAISE EXCEPTION 'a face match can be recorded by the person only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    SELECT p.id INTO v_profile FROM mangaly_profile.profile p WHERE p.account_id = p_account;
    IF v_profile IS NULL THEN
        SELECT mp.photo_ref INTO v_member_photo
          FROM mangaly_profile.member_profile mp WHERE mp.account_id = p_account;
        IF v_member_photo IS NULL THEN
            RAISE EXCEPTION 'no profile photos to compare against' USING ERRCODE = 'MG045';
        END IF;
    END IF;

    INSERT INTO mangaly_trust.biometric_consent (account_id, purpose, notice_version)
    VALUES (p_account, 'face_match_own_photos', p_notice_version)
    ON CONFLICT (account_id, purpose) WHERE withdrawn_at IS NULL DO NOTHING;

    IF p_passed AND v_profile IS NULL THEN
        INSERT INTO mangaly_trust.member_face_match (account_id, verified_at, expires_at)
        VALUES (p_account, now(), now() + interval '2 years')
        ON CONFLICT (account_id) DO UPDATE SET verified_at = now(), expires_at = now() + interval '2 years';
    ELSIF p_passed THEN
        INSERT INTO mangaly_trust.verification_layer_status
            (profile_id, layer, status, provenance, source_category,
             verified_at, freshness_expires_at, updated_at)
        VALUES
            (v_profile, 'profile_facts', 'verified',
             'Live face match against the member''s own photos',
             'face_match', now(), now() + interval '2 years', now())
        ON CONFLICT (profile_id, layer) DO UPDATE SET
            status               = 'verified',
            provenance           = EXCLUDED.provenance,
            source_category      = 'face_match',
            verified_at          = now(),
            freshness_expires_at = now() + interval '2 years',
            updated_at           = now();
    END IF;

    RETURN QUERY
    SELECT s.verified, s.verified_at, s.expires_at
      FROM mangaly_trust.face_match_status(p_account) s;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_trust.record_face_match(uuid, boolean, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_trust.record_face_match(uuid, boolean, text) TO mangaly_app;

-- Withdrawing consent also removes a member's confirmation.
CREATE OR REPLACE FUNCTION mangaly_trust.withdraw_face_match(p_account uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_trust, mangaly_profile, mangaly_authz, pg_temp
AS $$
DECLARE
    v_consents int;
    v_rows     int;
    v_member   int;
BEGIN
    IF mangaly_authz.is_self(p_account) IS NOT TRUE THEN
        RAISE EXCEPTION 'face match consent can be withdrawn by the person only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    UPDATE mangaly_trust.biometric_consent
       SET withdrawn_at = now()
     WHERE account_id = p_account
       AND purpose = 'face_match_own_photos'
       AND withdrawn_at IS NULL;
    GET DIAGNOSTICS v_consents = ROW_COUNT;

    DELETE FROM mangaly_trust.verification_layer_status v
     USING mangaly_profile.profile p
     WHERE p.account_id = p_account
       AND v.profile_id = p.id
       AND v.layer = 'profile_facts'
       AND v.source_category = 'face_match';
    GET DIAGNOSTICS v_rows = ROW_COUNT;

    DELETE FROM mangaly_trust.member_face_match WHERE account_id = p_account;
    GET DIAGNOSTICS v_member = ROW_COUNT;

    RETURN (v_consents + v_rows + v_member) > 0;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_trust.withdraw_face_match(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_trust.withdraw_face_match(uuid) TO mangaly_app;
