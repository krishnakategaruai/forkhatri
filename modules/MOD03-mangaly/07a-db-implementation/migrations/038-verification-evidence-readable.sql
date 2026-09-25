-- =============================================================================
-- 038 — Make verification evidence readable (baseline §13).
--
-- WHY (2026-09-21): `mangaly_trust.verification_layer_status` has existed since
-- migration 001 and nothing has ever read it, so two problems went unnoticed.
--
-- 1. Its RLS predicate is `is_self(profile_id) OR has_scope(profile_id,
--    'candidate_info')`. Rows are keyed by `profile.id`, but `is_self()`
--    compares its argument with `mangaly.authz_context` / `mangaly.account_id`,
--    both of which hold an ACCOUNT id — "the id every other people-column in
--    this module holds" (migration 033). A candidate therefore could not read
--    their own verification. `trust_layer_self_by_account` fixes that by
--    resolving the profile to its owning account.
--
-- 2. Discovery has to show evidence BEFORE a connection exists — §15.1 says a
--    recipient inspects trust signals before accepting, and §8.1 forbids
--    withholding meaningful information to force acceptance. RLS correctly
--    refuses that, so this adds the same narrow SECURITY DEFINER read the
--    module already uses for pre-connection data (`discovery_cards()` in 020,
--    `blocked_account_ids()` in 033).
--
-- What the function deliberately does NOT return is the free-text `provenance`
-- column. `layer`, `verified_at` and `source_category` are enough to weigh the
-- evidence and are non-identifying; the prose may name a verifier or a
-- document, and that is for the owner and connected parties only.
--
-- Expired layers are excluded here rather than by the caller: a stale check
-- shown as current is worse than no check, because it is trusted more (§13.4
-- freshness). There is no score and no aggregate: callers receive facts.
-- Idempotent: safe to re-run.
-- =============================================================================

-- 1. The owner can read their own evidence.
DROP POLICY IF EXISTS trust_layer_self_by_account ON mangaly_trust.verification_layer_status;
CREATE POLICY trust_layer_self_by_account
  ON mangaly_trust.verification_layer_status
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1
        FROM mangaly_profile.profile p
       WHERE p.id = verification_layer_status.profile_id
         AND mangaly_authz.is_self(p.account_id)
    )
  );

-- 2. The pre-connection-safe summary, keyed by the candidate's ACCOUNT id so
--    callers use the same id space as the rest of the module.
CREATE OR REPLACE FUNCTION mangaly_trust.verified_layers_for(p_account_ids uuid[])
RETURNS TABLE (
  account_id       uuid,
  layer            text,
  verified_at      timestamptz,
  source_category  text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO 'mangaly_trust', 'mangaly_profile', 'pg_temp'
AS $$
  SELECT p.account_id,
         v.layer::text,
         v.verified_at,
         v.source_category
    FROM mangaly_trust.verification_layer_status v
    JOIN mangaly_profile.profile p ON p.id = v.profile_id
   WHERE p.account_id = ANY(p_account_ids)
     AND v.status = 'verified'
     AND (v.freshness_expires_at IS NULL OR v.freshness_expires_at > now());
$$;

REVOKE ALL ON FUNCTION mangaly_trust.verified_layers_for(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_trust.verified_layers_for(uuid[]) TO mangaly_app;
