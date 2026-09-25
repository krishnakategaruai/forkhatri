-- =============================================================================
-- 043 — "Shown openly": what a candidate chooses to show before any connection
--       (product owner, 2026-09-22).
--
-- WHY:
--   The owner: "Few people like to share few things openly! Let them have
--   that." Until now the pre-connection card was fixed for everyone: main
--   photo, age, city, education, work; name, other photos and contact only
--   after both sides accept (DEC-V1-016, DEC-V1-020). Individual prompt
--   answers could already be published (migration 039).
--
--   A candidate may now also open, each on their own:
--     * `openly.first_name` — their first name (never the surname; contact
--       details are never openable here, and still need a connection plus a
--       per-item share, FR046/FR047);
--     * `openly.photos`     — all their photos, not only the main one.
--   Both default to closed. They are stored as ordinary profile attributes
--   (category `openly`), so they travel with the profile, are written by the
--   candidate only (the API refuses them from a parent managing the profile),
--   and are read here only for SEARCHABLE candidates — a paused or hidden
--   profile shows nothing openly, whatever the flags say.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_profile.is_open(p_profile uuid, p_key text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_profile.profile_attribute a
         WHERE a.profile_id = p_profile
           AND a.category = 'openly'
           AND a.attribute_key = p_key
           AND a.state::text = 'value'
           AND a.value = 'true'::jsonb
    );
$$;
REVOKE ALL ON FUNCTION mangaly_profile.is_open(uuid, text) FROM PUBLIC;

-- A non-main photo of a searchable candidate who opened their photos.
CREATE OR REPLACE FUNCTION mangaly_profile.is_openly_shared_photo(p_ref text)
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
         WHERE m.storage_ref = p_ref
           AND m.media_type::text = 'photo'
           AND m.upload_status::text = 'complete'
           AND i.searchable
           AND mangaly_profile.is_open(p.id, 'photos')
    );
$$;
REVOKE ALL ON FUNCTION mangaly_profile.is_openly_shared_photo(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.is_openly_shared_photo(text) TO mangaly_app;

-- What each of these searchable candidates chose to show openly.
CREATE OR REPLACE FUNCTION mangaly_profile.open_cards(p_accounts uuid[])
RETURNS TABLE (account_id uuid, first_name text, photo_refs text[])
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_discovery, pg_temp
AS $$
    SELECT p.account_id,
           CASE WHEN mangaly_profile.is_open(p.id, 'first_name')
                THEN split_part(btrim(p.name), ' ', 1) END,
           CASE WHEN mangaly_profile.is_open(p.id, 'photos') THEN
                ARRAY(SELECT m.storage_ref FROM mangaly_profile.profile_media m
                       WHERE m.profile_id = p.id
                         AND m.media_type::text = 'photo'
                         AND m.upload_status::text = 'complete'
                       ORDER BY m.is_primary DESC, m.sort_order, m.uploaded_at)
                ELSE ARRAY[]::text[] END
      FROM mangaly_profile.profile p
      JOIN mangaly_discovery.discovery_profile_index i ON i.profile_id = p.account_id
     WHERE p.account_id = ANY(p_accounts)
       AND i.searchable;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.open_cards(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.open_cards(uuid[]) TO mangaly_app;
