-- =============================================================================
-- 018 — A candidate can read the suggestions made to them (FR014 / TR014).
--
-- WHY (found live 2026-09-15, testing with a real parent): Lakshmi Reddy, a
-- Home Circle parent, suggested a profile to her daughter Ananya from
-- Discover. Lakshmi could list it, but Ananya's own `GET /home-circle/
-- suggestions` returned []. `hc_suggestion_family` only admits
-- `has_scope(candidate_profile_id, 'family_info')`, and a candidate never
-- holds a family grant on herself, so the person every suggestion is FOR
-- could never see one. `home_circle.list_suggestions()` already documents
-- the intended "self-read"; the policy never allowed it.
--
-- Fix: an additional SELECT-only policy for the candidate. Permissive
-- policies combine with OR, so family members keep their existing access,
-- and the candidate gains read access only; creating or changing a
-- suggestion stays family-only.
-- Idempotent: safe to re-run.
-- =============================================================================

DROP POLICY IF EXISTS hc_suggestion_candidate_read ON mangaly_home_circle.suggestion;
CREATE POLICY hc_suggestion_candidate_read ON mangaly_home_circle.suggestion
  FOR SELECT
  USING (mangaly_authz.is_self(candidate_profile_id));
