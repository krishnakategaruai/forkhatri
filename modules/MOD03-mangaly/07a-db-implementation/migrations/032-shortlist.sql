-- =============================================================================
-- 032 — Shortlist, scoped to a context (rework contract §3).
--
-- WHY (2026-09-17): "Save" on a Discover card keeps a candidate for later.
-- A shortlist belongs to the context it was made in — the candidate's own
-- search, or a circle acting for that candidate — and, like the suggestion
-- feed, is a shared circle activity: a parent's saves for Ananya are visible
-- to Ananya and to the rest of her circle, with who saved recorded. An
-- account with no profile and no circle saves into its own context
-- (`candidate_account_id` = its own account id), so browse mode works too.
-- `saved_account_id` is the saved candidate's ACCOUNT id, the same id space
-- as `discovery_profile_index.profile_id`.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE TABLE IF NOT EXISTS mangaly_discovery.shortlist (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_account_id uuid NOT NULL,
  saved_by_account_id  uuid NOT NULL,
  saved_account_id     uuid NOT NULL,
  note                 text,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (candidate_account_id, saved_account_id)
);
CREATE INDEX IF NOT EXISTS idx_shortlist_candidate
  ON mangaly_discovery.shortlist (candidate_account_id, created_at DESC);

ALTER TABLE mangaly_discovery.shortlist ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS shortlist_context_members ON mangaly_discovery.shortlist;
CREATE POLICY shortlist_context_members ON mangaly_discovery.shortlist
  USING (mangaly_authz.is_self(candidate_account_id)
         OR mangaly_authz.has_scope(candidate_account_id, 'family_info'))
  WITH CHECK (mangaly_authz.is_self(saved_by_account_id)
              AND (mangaly_authz.is_self(candidate_account_id)
                   OR mangaly_authz.has_scope(candidate_account_id, 'family_info')));

GRANT SELECT, INSERT, UPDATE, DELETE ON mangaly_discovery.shortlist TO mangaly_app;
