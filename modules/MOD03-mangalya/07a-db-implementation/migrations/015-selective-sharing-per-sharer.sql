-- =============================================================================
-- 015 — Selective sharing (FR046/FR047/FR048): one row per sharer, and the
--       value each sharer chose to reveal.
--
-- WHY (found while implementing TR046, 2026-09-15):
--   * `sharing_grant` had UNIQUE (connection_id, category), so only ONE side of
--     a connection could ever share a given category. FR046 says each
--     participant shares independently, so the key must include the sharer.
--   * Phone and email live in the ForKhatri platform identity. Mangaly can read
--     a member's own identifiers but never another member's, so the value the
--     sharer reveals is stored with their grant and cleared when they stop
--     sharing.
--   * The participants-only policy had no WITH CHECK, so either participant
--     could write a grant naming the OTHER as the sharer. Writes now require
--     the sharer to be the caller and the connection to be accepted.
--   * `family_contact_share` gets the family member's revealed phone for the
--     same reason (FR048 is built on this table).
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_connection.sharing_grant
  DROP CONSTRAINT IF EXISTS sharing_grant_connection_id_category_key;

ALTER TABLE mangaly_connection.sharing_grant
  ADD COLUMN IF NOT EXISTS shared_value text;

DO $$ BEGIN
  ALTER TABLE mangaly_connection.sharing_grant
    ADD CONSTRAINT sharing_grant_one_per_sharer UNIQUE (connection_id, category, granted_by_account_id);
EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
END $$;

ALTER TABLE mangaly_connection.sharing_grant
  DROP CONSTRAINT IF EXISTS sharing_grant_category_check;
ALTER TABLE mangaly_connection.sharing_grant
  ADD CONSTRAINT sharing_grant_category_check
  CHECK (category IN ('additional_photos', 'phone', 'email', 'family_contact'));

DROP POLICY IF EXISTS sharing_grant_participants ON mangaly_connection.sharing_grant;
CREATE POLICY sharing_grant_participants ON mangaly_connection.sharing_grant
  USING (EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                 WHERE c.id = sharing_grant.connection_id
                   AND (mangaly_authz.is_self(c.acting_account_id) OR mangaly_authz.is_self(c.target_profile_id))))
  WITH CHECK (mangaly_authz.is_self(granted_by_account_id)
              AND EXISTS (SELECT 1 FROM mangaly_connection.connection_request c
                          WHERE c.id = sharing_grant.connection_id
                            AND c.status = 'accepted'
                            AND (mangaly_authz.is_self(c.acting_account_id) OR mangaly_authz.is_self(c.target_profile_id))));

ALTER TABLE mangaly_connection.family_contact_share
  ADD COLUMN IF NOT EXISTS family_member_phone text;
