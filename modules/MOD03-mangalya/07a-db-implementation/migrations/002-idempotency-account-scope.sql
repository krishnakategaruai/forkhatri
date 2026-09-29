-- =============================================================================
-- 002 — Scope the idempotency key uniqueness to the owning account.
--
-- WHY (Step 8 Security & Performance finding, SP102, 2026-09-13):
-- 001-initial.sql created mangaly_platform.idempotency_key with
--   UNIQUE (idempotency_key, endpoint)
-- while the table already carried an account_id column. Because the key is
-- CLIENT-generated (TR102: "the client generates and persists an idempotency
-- key alongside each locally-queued write"), a global key namespace is a real
-- cross-account defect, not a theoretical one:
--
--   1. Information disclosure — if account B issues a request whose key
--      collides with one account A already used on the same endpoint (a weak
--      client key scheme, a replayed key an attacker observed, or a plain
--      collision), the middleware's (idempotency_key, endpoint) lookup finds
--      A's row and returns A's response_snapshot to B.
--   2. Denial of service — B can deliberately burn keys on an endpoint and
--      block A's own writes, since A's insert now conflicts with B's row.
--
-- 001's own trailing comment ("there is no 'another actor's row' concept to
-- leak here") was therefore incorrect for this table, and is corrected below.
--
-- FIX: uniqueness and every middleware lookup are scoped by account_id.
-- Idempotent and safe to re-run.
-- =============================================================================

-- The original constraint's name is Postgres-generated from the table/column
-- list; drop by that generated name, tolerating its absence on a fresh DB
-- where 001 has already been superseded by an updated schema.sql snapshot.
ALTER TABLE mangaly_platform.idempotency_key
  DROP CONSTRAINT IF EXISTS idempotency_key_idempotency_key_endpoint_key;

ALTER TABLE mangaly_platform.idempotency_key
  DROP CONSTRAINT IF EXISTS idempotency_key_account_scope;

ALTER TABLE mangaly_platform.idempotency_key
  ADD CONSTRAINT idempotency_key_account_scope
  UNIQUE (account_id, idempotency_key, endpoint);

COMMENT ON CONSTRAINT idempotency_key_account_scope ON mangaly_platform.idempotency_key IS
  '[SP102] Account-scoped: a client-generated key is unique WITHIN one account, never globally — a global namespace would return one account''s cached response to another.';

-- Defense in depth beneath the middleware's own server-side account scoping:
-- even a middleware bug that omitted account_id from its WHERE clause cannot
-- cross accounts once RLS is enforcing the same predicate. mangaly_app is a
-- non-owning role (TR017), so this policy actually applies to it.
ALTER TABLE mangaly_platform.idempotency_key ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS idempotency_key_self ON mangaly_platform.idempotency_key;
CREATE POLICY idempotency_key_self ON mangaly_platform.idempotency_key
  USING (account_id::text = current_setting('mangaly.account_id', true))
  WITH CHECK (account_id::text = current_setting('mangaly.account_id', true));

COMMENT ON TABLE mangaly_platform.idempotency_key IS
  '[TR102/MODULE-ARCHITECTURE-STANDARD §4b] One shared implementation every client-queueable mutation endpoint honors — never re-derived per component. Rows are account-scoped (SP102): both the UNIQUE constraint and an RLS policy key on account_id, because the idempotency key itself is client-generated and therefore not trustworthy as a global identifier.';
