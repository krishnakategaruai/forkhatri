-- =============================================================================
-- 020 — Discover shows each candidate's main photo and age (DEC-V1-016).
--
-- WHY (product-owner decision 2026-09-15): a text-only Discover card gives a
-- member nothing to decide on. The main photo and age of a SEARCHABLE
-- candidate are now visible to signed-in members; name, additional photos,
-- contact details and full biodata stay consent-gated.
--
-- A searching member holds no grant on the candidate, so `profile` and
-- `profile_media` RLS (owner or `candidate_info`) hide both. Two narrow
-- SECURITY DEFINER reads expose exactly the decided fields:
--   * `discovery_cards(ids)`: for searchable candidates in the list only, the
--     main photo's storage reference and the age in years. Nothing else.
--   * `is_discoverable_primary_photo(ref)`: true only when that reference is a
--     complete main photo of a searchable candidate; the media route uses it
--     to serve that one file.
-- Both require a bound `mangaly.account_id` (a signed-in caller).
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_discovery.discovery_cards(p_account_ids uuid[])
RETURNS TABLE (account_id uuid, photo_ref text, age integer)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_discovery, mangaly_profile, pg_temp
AS $$
    SELECT i.profile_id,
           (SELECT m.storage_ref
              FROM mangaly_profile.profile_media m
             WHERE m.profile_id = p.id
               AND m.is_primary
               AND m.media_type::text = 'photo'
               AND m.upload_status::text = 'complete'
             LIMIT 1),
           date_part('year', age(current_date, p.date_of_birth))::integer
      FROM mangaly_discovery.discovery_profile_index i
      JOIN mangaly_profile.profile p ON p.account_id = i.profile_id
     WHERE i.profile_id = ANY(p_account_ids)
       AND i.searchable
       AND NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL;
$$;

CREATE OR REPLACE FUNCTION mangaly_profile.is_discoverable_primary_photo(p_storage_ref text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_discovery, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM mangaly_profile.profile_media m
          JOIN mangaly_profile.profile p ON p.id = m.profile_id
          JOIN mangaly_discovery.discovery_profile_index i ON i.profile_id = p.account_id
         WHERE m.storage_ref = p_storage_ref
           AND m.is_primary
           AND m.media_type::text = 'photo'
           AND m.upload_status::text = 'complete'
           AND i.searchable
           AND NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
    );
$$;

REVOKE ALL ON FUNCTION mangaly_discovery.discovery_cards(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_discovery.discovery_cards(uuid[]) TO mangaly_app;
REVOKE ALL ON FUNCTION mangaly_profile.is_discoverable_primary_photo(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.is_discoverable_primary_photo(text) TO mangaly_app;
