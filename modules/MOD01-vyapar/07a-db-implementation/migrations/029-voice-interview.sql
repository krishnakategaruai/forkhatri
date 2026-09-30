-- [Voice interview, 2026-09-30 — owner: "Voice should like, we ask questions
-- in their perspective and waits until we receive answer!"]
-- Additive and idempotent (safe to run twice). The interview itself is
-- stateless (the client sends the confirmed answers back on every turn), so
-- it needs no table. Two small changes only:
--
--   1. listings.own_assets — the profile interview asks "Do you have your
--      own tools or vehicle?". Until now there was nowhere to keep the
--      answer, while a job post already says what it `requires_assets`
--      (migration 018). Same closed vocabulary, so a job that needs a bike
--      and a worker who has one can be matched later.
--   2. ai_events.kind gains 'interview' — an interview answer is read by the
--      rules engine, and by Claude only when AI_PROVIDER=anthropic and the
--      rules could not read it. Only that Claude call is recorded (the same
--      audit row as every other AI call: a hash, never the text).
-- Traces to: FR01, FR11, FR12, FR44, TR050, REFACTOR-PLAN.md (AI workstream C)

ALTER TABLE vyapar_listings.listings
  ADD COLUMN IF NOT EXISTS own_assets text[] NOT NULL DEFAULT '{}';
ALTER TABLE vyapar_listings.listings DROP CONSTRAINT IF EXISTS listings_own_assets_check;
ALTER TABLE vyapar_listings.listings ADD CONSTRAINT listings_own_assets_check
  CHECK (own_assets <@ ARRAY['two_wheeler', 'four_wheeler', 'driving_licence', 'smartphone', 'laptop', 'own_tools']::text[]);
COMMENT ON COLUMN vyapar_listings.listings.own_assets IS
  'What the person brings to work (bike, car, licence, smartphone, laptop, own tools); same vocabulary as opportunities.requires_assets.';

ALTER TABLE vyapar_integration.ai_events DROP CONSTRAINT IF EXISTS ai_events_kind_check;
ALTER TABLE vyapar_integration.ai_events ADD CONSTRAINT ai_events_kind_check
  CHECK (kind IN ('draft', 'read_image', 'shortlist', 'tips', 'proposal', 'interview'));
