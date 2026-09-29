-- =============================================================================
-- 033 — Blocking (rework contract §3).
--
-- WHY (2026-09-17): a member may block another; a blocked person vanishes from
-- both sides' Discover, lists and request sending. A block row is private to
-- the blocker (RLS), but the EFFECT has to be visible from the other side's
-- session too (a person who has been blocked must not see the blocker either),
-- so two narrow SECURITY DEFINER reads expose only the yes/no of it:
--   * `blocked_account_ids(account)` — every account blocked by, or blocking,
--     the given account; readable by that account and by anyone holding
--     `family_info` on it (a circle acting for their candidate).
--   * `is_blocked_between(a, b)` — for the connection-request gate.
-- `mangaly_safety.report` (migration 001) already exists and is reused for
-- `POST /safety/report`; `reported_profile_id` holds the reported person's
-- ACCOUNT id, the id every other people-column in this module holds.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE TABLE IF NOT EXISTS mangaly_safety.block (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  blocker_account_id uuid NOT NULL,
  blocked_account_id uuid NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (blocker_account_id, blocked_account_id),
  CHECK (blocker_account_id <> blocked_account_id)
);
CREATE INDEX IF NOT EXISTS idx_safety_block_blocked ON mangaly_safety.block (blocked_account_id);

ALTER TABLE mangaly_safety.block ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS safety_block_blocker_only ON mangaly_safety.block;
CREATE POLICY safety_block_blocker_only ON mangaly_safety.block
  USING (mangaly_authz.is_self(blocker_account_id))
  WITH CHECK (mangaly_authz.is_self(blocker_account_id));

GRANT SELECT, INSERT, UPDATE, DELETE ON mangaly_safety.block TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_safety.blocked_account_ids(p_account_id uuid)
RETURNS SETOF uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_safety, mangaly_authz, pg_temp
AS $$
    SELECT b.blocked_account_id FROM mangaly_safety.block b
     WHERE b.blocker_account_id = p_account_id
       AND (mangaly_authz.is_self(p_account_id) OR mangaly_authz.has_scope(p_account_id, 'family_info'))
    UNION
    SELECT b.blocker_account_id FROM mangaly_safety.block b
     WHERE b.blocked_account_id = p_account_id
       AND (mangaly_authz.is_self(p_account_id) OR mangaly_authz.has_scope(p_account_id, 'family_info'));
$$;

CREATE OR REPLACE FUNCTION mangaly_safety.is_blocked_between(p_a uuid, p_b uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_safety, pg_temp
AS $$
    SELECT NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
       AND EXISTS (
        SELECT 1 FROM mangaly_safety.block b
         WHERE (b.blocker_account_id = p_a AND b.blocked_account_id = p_b)
            OR (b.blocker_account_id = p_b AND b.blocked_account_id = p_a)
    );
$$;

REVOKE ALL ON FUNCTION mangaly_safety.blocked_account_ids(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_safety.blocked_account_ids(uuid) TO mangaly_app;
REVOKE ALL ON FUNCTION mangaly_safety.is_blocked_between(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_safety.is_blocked_between(uuid, uuid) TO mangaly_app;

-- The reporter writes their own report row (RLS: reporter only), so no
-- function is needed for `POST /safety/report`.
