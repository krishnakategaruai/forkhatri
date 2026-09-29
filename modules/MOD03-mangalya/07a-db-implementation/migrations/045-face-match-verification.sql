-- =============================================================================
-- 045 — Live face match: the outcome, its biometric consent, and withdrawal
--       (DEC-V1-016; the maker gate of DEC-V1-020 / DEC-V1-025).
--
-- WHAT A FACE MATCH IS HERE:
--   The member's browser captures a live face, runs an active liveness
--   challenge, and compares a face descriptor from that capture against the
--   member's own uploaded photos. Only the OUTCOME reaches the server; the
--   server applies the threshold and records pass/fail through
--   `record_face_match()` below. The claim recorded is "the person in these
--   photos is the person using this account" — the `profile_facts` layer with
--   `source_category = 'face_match'` (M01-F §4.3), never an identity or age
--   claim (DEC-V1-016: those layers are not populated in this product).
--
-- WHAT IS NEVER STORED:
--   No image, no video frame, no face descriptor/embedding, no distance or
--   score. Nothing in this migration has a column that could hold one. The
--   frames are discarded in the browser once the comparison completes; a
--   stored template would turn a one-off check into a standing biometric
--   database (DEC-V1-016, "The constraint that shapes the design").
--
-- CONSENT (DPDP Act 2023 / DPDP Rules 2025):
--   Biometric processing needs its own specific, unbundled consent with a
--   stated purpose, logged and timestamped, and withdrawable. It cannot ride
--   on the sign-up terms. `biometric_consent` is that record. Withdrawal
--   stamps `withdrawn_at` rather than deleting the row: the log has to show
--   that consent WAS given, when, for what, and when it ended — that is what
--   "auditable" means — and the row itself holds no biometric data. The
--   verification the consent supported IS deleted on withdrawal.
--
-- FRESHNESS — two years:
--   Faces change (age, weight, beard, glasses) and members replace photos, so
--   "confirmed as you" cannot be permanent (§13.4: a stale claim shown as
--   current is worse than none, because it is trusted more). Two years is
--   long enough that an honest member is not asked to repeat a biometric
--   check every season — each repeat is another biometric processing event,
--   which data minimisation argues against — and short enough that the
--   confirmed face still resembles the person. `verified_layers_for()` (038)
--   already hides expired rows everywhere.
--
-- NEW PHOTOS INVALIDATE IT:
--   The claim is about THESE photos. A photo added after the check was never
--   compared, so a member who verified and then added someone else's picture
--   would otherwise carry a confirming badge on a false photo — the exact
--   deception §22 exists to stop. The trigger below removes the face-match
--   row whenever a new photo lands; the member confirms again.
--
-- Rows in `verification_layer_status` are keyed by PROFILE id; callers pass
-- their ACCOUNT id and the functions resolve it (the same id-space fix 038
-- made). A person with no profile has no photos to compare against, so there
-- is nothing to verify: `record_face_match` refuses with SQLSTATE MG045.
--
-- Idempotent: safe to re-run.
-- =============================================================================

-- 1. The unbundled biometric consent record. -----------------------------------
CREATE TABLE IF NOT EXISTS mangaly_trust.biometric_consent (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      uuid NOT NULL,          -- ACCOUNT id space, like every other people-column
    purpose         text NOT NULL,          -- 'face_match_own_photos'
    notice_version  text NOT NULL,          -- which consent wording the person saw
    granted_at      timestamptz NOT NULL DEFAULT now(),
    withdrawn_at    timestamptz,
    CONSTRAINT biometric_consent_purpose_chk CHECK (purpose IN ('face_match_own_photos'))
);
-- At most one live consent per person and purpose; history rows stay.
CREATE UNIQUE INDEX IF NOT EXISTS uq_biometric_consent_active
    ON mangaly_trust.biometric_consent (account_id, purpose)
    WHERE withdrawn_at IS NULL;
COMMENT ON TABLE mangaly_trust.biometric_consent IS
    '[DEC-V1-016] Specific, unbundled, withdrawable consent to a live face match. '
    'Holds no biometric data. Withdrawal stamps withdrawn_at (the audit log must '
    'show consent was given and ended); writes only through the functions below.';

ALTER TABLE mangaly_trust.biometric_consent ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS biometric_consent_self ON mangaly_trust.biometric_consent;
CREATE POLICY biometric_consent_self ON mangaly_trust.biometric_consent
    FOR SELECT USING (mangaly_authz.is_self(account_id));
-- Read-only to the app role: every write goes through a function that checks
-- the caller is the person themselves.
REVOKE ALL ON mangaly_trust.biometric_consent FROM mangaly_app;
GRANT SELECT ON mangaly_trust.biometric_consent TO mangaly_app;


-- 2. Status for the caller. -----------------------------------------------------
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
BEGIN
    IF mangaly_authz.is_self(p_account) IS NOT TRUE THEN
        RAISE EXCEPTION 'face match status is readable by the person only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    SELECT p.id INTO v_profile FROM mangaly_profile.profile p WHERE p.account_id = p_account;

    RETURN QUERY
    SELECT v_profile IS NOT NULL,
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


-- 3. Record one attempt's outcome, for the caller only. ------------------------
--    The server has already applied the threshold; this receives pass/fail.
--    Consent is recorded (or kept) on every call, because the API only calls
--    this when the request carried consent = true.
--    A FAILED attempt writes no verification row and does not remove a
--    current one: a retry in poor light must not erase a good result, and
--    nothing about a failure is worth keeping (only the outcome is kept).
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
BEGIN
    IF mangaly_authz.is_self(p_account) IS NOT TRUE THEN
        RAISE EXCEPTION 'a face match can be recorded by the person only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    SELECT p.id INTO v_profile FROM mangaly_profile.profile p WHERE p.account_id = p_account;
    IF v_profile IS NULL THEN
        RAISE EXCEPTION 'no profile photos to compare against' USING ERRCODE = 'MG045';
    END IF;

    INSERT INTO mangaly_trust.biometric_consent (account_id, purpose, notice_version)
    VALUES (p_account, 'face_match_own_photos', p_notice_version)
    ON CONFLICT (account_id, purpose) WHERE withdrawn_at IS NULL DO NOTHING;

    IF p_passed THEN
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


-- 4. Withdraw: consent ends, the verification it supported goes. ---------------
CREATE OR REPLACE FUNCTION mangaly_trust.withdraw_face_match(p_account uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_trust, mangaly_profile, mangaly_authz, pg_temp
AS $$
DECLARE
    v_consents int;
    v_rows     int;
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

    RETURN (v_consents + v_rows) > 0;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_trust.withdraw_face_match(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_trust.withdraw_face_match(uuid) TO mangaly_app;


-- 5. A new photo was never compared: the confirmation no longer covers the
--    profile's photos, so it is removed. -----------------------------------------
CREATE OR REPLACE FUNCTION mangaly_trust.face_match_void_on_new_photo()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_trust, mangaly_profile, pg_temp
AS $$
BEGIN
    IF NEW.media_type = 'photo'
       AND NEW.storage_ref IS NOT NULL
       AND (TG_OP = 'INSERT' OR NEW.storage_ref IS DISTINCT FROM OLD.storage_ref) THEN
        DELETE FROM mangaly_trust.verification_layer_status
         WHERE profile_id = NEW.profile_id
           AND layer = 'profile_facts'
           AND source_category = 'face_match';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_trust.face_match_void_on_new_photo() FROM PUBLIC;

DROP TRIGGER IF EXISTS trg_face_match_void_on_new_photo ON mangaly_profile.profile_media;
CREATE TRIGGER trg_face_match_void_on_new_photo
    AFTER INSERT OR UPDATE OF storage_ref ON mangaly_profile.profile_media
    FOR EACH ROW EXECUTE FUNCTION mangaly_trust.face_match_void_on_new_photo();
