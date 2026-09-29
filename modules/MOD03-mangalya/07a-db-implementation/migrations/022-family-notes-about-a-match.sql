-- =============================================================================
-- 022 — Private family notes are about one match, private to their author,
--       and reach the candidate only when the author asks and the candidate
--       agrees (FR016 / TR016, UX13, TS035–TS037).
--
-- WHY (2026-09-15):
--   * M01-B §12 / M01-I: parents keep private working notes "while evaluating
--     potential matches"; notes are not automatically visible to the
--     candidate or the prospective family; a selected note can be taken
--     forward to the candidate with the candidate's approval. UX13: "My notes
--     on [Profile]", a per-note "Request to forward this note" with a preview
--     of exactly what would be shared, and a candidate decision that can be a
--     decline without any explanation.
--   * What existed did not match: a note had no match it was about, every
--     family member with `family_info` could read every other member's notes
--     (TS035 says no other Home Circle member may), there was no request step
--     (every note was simply "pending" for the candidate), and no decline.
--   * `subject_account_id` holds the match's ACCOUNT id, the same id space as
--     `discovery_profile_index.profile_id` and `suggestion.suggested_profile_id`.
--   * The three existing rows were written by a retired check script, have no
--     match, and their authors' memberships have ended; they are removed.
--   * The author's own rows are guarded by RLS through
--     `is_active_note_author` (the author must still be an active member of
--     that candidate's circle). The candidate sees a request's author and
--     match but never its content until they choose to read it, so request
--     listing and the decision are narrow SECURITY DEFINER functions held to
--     migration 010's rules: the caller must be the candidate, every value is
--     re-derived from rows, and one row changes. After agreeing, the candidate
--     reads the note through `hc_note_candidate_reads_shared`.
--   * The 1000-character limit and the "never paste private messages" copy
--     are the product-level guardrail TR016 describes; no API copies message
--     content into a note.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_home_circle.home_circle_note
  ADD COLUMN IF NOT EXISTS subject_account_id uuid,
  ADD COLUMN IF NOT EXISTS forward_requested_at timestamptz,
  ADD COLUMN IF NOT EXISTS forward_declined_at timestamptz,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DELETE FROM mangaly_home_circle.home_circle_note WHERE subject_account_id IS NULL;

ALTER TABLE mangaly_home_circle.home_circle_note
  ALTER COLUMN subject_account_id SET NOT NULL;

DO $$ BEGIN
  ALTER TABLE mangaly_home_circle.home_circle_note
    ADD CONSTRAINT home_circle_note_content_length
    CHECK (char_length(btrim(content)) BETWEEN 1 AND 1000);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE mangaly_home_circle.home_circle_note
    ADD CONSTRAINT home_circle_note_forward_order
    CHECK ((forwarded_at IS NULL OR forward_requested_at IS NOT NULL)
           AND NOT (forwarded_at IS NOT NULL AND forward_declined_at IS NOT NULL));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_hc_note_author_subject
  ON mangaly_home_circle.home_circle_note (author_membership_id, subject_account_id);

CREATE OR REPLACE FUNCTION mangaly_home_circle.is_active_note_author(
    p_membership_id uuid,
    p_candidate_account_id uuid
) RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_home_circle.membership m
         WHERE m.id = p_membership_id
           AND m.candidate_profile_id = p_candidate_account_id
           AND m.status = 'active'
           AND mangaly_authz.is_self(m.member_account_id)
    );
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.is_active_note_author(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.is_active_note_author(uuid, uuid) TO mangaly_app;

DROP POLICY IF EXISTS hc_note_family_or_forwarded ON mangaly_home_circle.home_circle_note;
DROP POLICY IF EXISTS hc_note_author ON mangaly_home_circle.home_circle_note;
CREATE POLICY hc_note_author ON mangaly_home_circle.home_circle_note
  USING (mangaly_home_circle.is_active_note_author(author_membership_id, candidate_profile_id))
  WITH CHECK (mangaly_home_circle.is_active_note_author(author_membership_id, candidate_profile_id)
              AND forwarded_at IS NULL);

DROP POLICY IF EXISTS hc_note_candidate_reads_shared ON mangaly_home_circle.home_circle_note;
CREATE POLICY hc_note_candidate_reads_shared ON mangaly_home_circle.home_circle_note
  FOR SELECT
  USING (forwarded_at IS NOT NULL AND mangaly_authz.is_self(candidate_profile_id));

GRANT SELECT, INSERT, UPDATE, DELETE ON mangaly_home_circle.home_circle_note TO mangaly_app;

-- The candidate's old blind "pending" list and one-step approval are replaced.
DROP FUNCTION IF EXISTS mangaly_home_circle.list_own_pending_notes();
DROP FUNCTION IF EXISTS mangaly_home_circle.approve_note_forward(uuid);

CREATE OR REPLACE FUNCTION mangaly_home_circle.list_note_forward_requests(p_candidate_account_id uuid)
RETURNS TABLE (
    note_id uuid,
    author_name text,
    relationship_type text,
    subject_account_id uuid,
    requested_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
    SELECT n.id,
           COALESCE((SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = m.member_account_id),
                    (SELECT a.display_name FROM mangaly_identity.account a WHERE a.id = m.member_account_id)),
           m.relationship_type::text,
           n.subject_account_id,
           n.forward_requested_at
      FROM mangaly_home_circle.home_circle_note n
      JOIN mangaly_home_circle.membership m ON m.id = n.author_membership_id
     WHERE mangaly_authz.is_self(p_candidate_account_id)
       AND n.candidate_profile_id = p_candidate_account_id
       AND n.forward_requested_at IS NOT NULL
       AND n.forwarded_at IS NULL
       AND n.forward_declined_at IS NULL
       AND m.status = 'active'
     ORDER BY n.forward_requested_at;
$$;

CREATE OR REPLACE FUNCTION mangaly_home_circle.decide_note_forward(
    p_note_id uuid,
    p_candidate_account_id uuid,
    p_approve boolean
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_authz, pg_temp
AS $$
BEGIN
    IF mangaly_authz.is_self(p_candidate_account_id) IS NOT TRUE THEN
        RETURN false;
    END IF;

    UPDATE mangaly_home_circle.home_circle_note n
       SET forwarded_at = CASE WHEN p_approve THEN now() END,
           forward_declined_at = CASE WHEN p_approve THEN NULL ELSE now() END
     WHERE n.id = p_note_id
       AND n.candidate_profile_id = p_candidate_account_id
       AND n.forward_requested_at IS NOT NULL
       AND n.forwarded_at IS NULL
       AND n.forward_declined_at IS NULL
       AND EXISTS (SELECT 1 FROM mangaly_home_circle.membership m
                    WHERE m.id = n.author_membership_id AND m.status = 'active');
    RETURN FOUND;
END;
$$;

CREATE OR REPLACE FUNCTION mangaly_home_circle.list_shared_notes(p_candidate_account_id uuid)
RETURNS TABLE (
    note_id uuid,
    content text,
    author_name text,
    relationship_type text,
    subject_account_id uuid,
    forwarded_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_home_circle, mangaly_profile, mangaly_identity, mangaly_authz, pg_temp
AS $$
    SELECT n.id,
           n.content,
           COALESCE((SELECT p.name FROM mangaly_profile.profile p WHERE p.account_id = m.member_account_id),
                    (SELECT a.display_name FROM mangaly_identity.account a WHERE a.id = m.member_account_id)),
           m.relationship_type::text,
           n.subject_account_id,
           n.forwarded_at
      FROM mangaly_home_circle.home_circle_note n
      JOIN mangaly_home_circle.membership m ON m.id = n.author_membership_id
     WHERE mangaly_authz.is_self(p_candidate_account_id)
       AND n.candidate_profile_id = p_candidate_account_id
       AND n.forwarded_at IS NOT NULL
     ORDER BY n.forwarded_at DESC;
$$;

REVOKE ALL ON FUNCTION mangaly_home_circle.list_note_forward_requests(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_note_forward_requests(uuid) TO mangaly_app;
REVOKE ALL ON FUNCTION mangaly_home_circle.decide_note_forward(uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.decide_note_forward(uuid, uuid, boolean) TO mangaly_app;
REVOKE ALL ON FUNCTION mangaly_home_circle.list_shared_notes(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_home_circle.list_shared_notes(uuid) TO mangaly_app;
