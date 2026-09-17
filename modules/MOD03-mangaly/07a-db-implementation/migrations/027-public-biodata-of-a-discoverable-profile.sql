-- =============================================================================
-- 027 — A discoverable candidate's biodata is readable by any signed-in member,
--       without their name or contact details (FR021, DEC-V1-016, DEC-V1-020).
--
-- WHY (2026-09-17):
--   * Product owner: "parents should see details like shaadi.com about other
--     candidate whereas candidate see hing[e] kind of details that user added
--     also". Both roles were seeing four fields — locality, education,
--     profession, age — because everything else sat behind `candidate_info`,
--     which only the two parties of an ACCEPTED connection ever hold. A parent
--     evaluating a match for their daughter could not see marital status,
--     diet, family details or what the person is looking for: the very things
--     an Indian matrimony biodata leads with.
--   * Checked against the reference service: Shaadi.com shows a registered
--     member the full biodata of other members — education, profession,
--     family, lifestyle, horoscope, partner preferences — and gates only
--     identity and contact: photos behind a per-member photo-privacy setting,
--     and phone numbers behind "contact details" settings and acceptance.
--   * So this function returns the profile ATTRIBUTES of a candidate who is
--     searchable, and never `profile.name`, never phone or email, and never a
--     non-primary photo. Identity still moves only on acceptance (FR021),
--     while the matrimonial facts a family needs to judge a match are
--     available before anyone is asked to connect.
--   * Held to migration 010's rules: the caller must be a signed-in member,
--     the subject must be searchable, values are re-derived from rows, and the
--     projection is minimal — a declined field is simply absent, exactly as it
--     is for the owner's own completeness view.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_profile.public_biodata(p_account_id uuid)
RETURNS TABLE (
    category text,
    attribute_key text,
    value jsonb
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_discovery, pg_temp
AS $$
    SELECT a.category::text, a.attribute_key, a.value
      FROM mangaly_profile.profile_attribute a
      JOIN mangaly_profile.profile p ON p.id = a.profile_id
     WHERE p.account_id = p_account_id
       AND a.state = 'value'
       AND NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
       AND EXISTS (
           SELECT 1 FROM mangaly_discovery.discovery_profile_index i
            WHERE i.profile_id = p_account_id AND i.searchable
       );
$$;

REVOKE ALL ON FUNCTION mangaly_profile.public_biodata(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.public_biodata(uuid) TO mangaly_app;
