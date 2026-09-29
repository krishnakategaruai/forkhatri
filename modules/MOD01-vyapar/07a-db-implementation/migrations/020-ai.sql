-- [IMP42 — Refactor C (AI)] Audit and cost tracking for AI assistance.
--
-- Every call to an /v1/ai/* endpoint or getAiShortlist writes ONE row here,
-- whether Claude answered, the rules engine answered, the call fell back, or
-- it was refused. What is stored is deliberately not the text a person typed
-- (that stays in the request): only who asked, which operation, a sha256 of
-- the input (so a repeated request is recognisable without keeping it), the
-- model, latency, token counts and the outcome. That is enough to bill,
-- rate-limit and debug per member, and nothing a leak could read as a
-- notice, a proposal or a cover letter.
--
-- Rows are self-only under RLS, plus operators with the `analytics`
-- permission for cost reporting. The runtime role may INSERT and SELECT but
-- never UPDATE or DELETE: an audit row is immutable.
--
-- Providers never write anything else: an AI draft, tip, shortlist or
-- proposal lives only in the HTTP response until the person confirms it
-- through the ordinary createOpportunity / createEnquiry endpoints.
-- Traces to: REFACTOR-PLAN.md (AI workstream C), FR49 (audit attribution), TR050

CREATE TABLE IF NOT EXISTS vyapar_integration.ai_events (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id      text NOT NULL,                       -- vyapar_identity.members(id), no cross-schema FK (convention 3)
  kind           text NOT NULL CHECK (kind IN ('draft', 'read_image', 'shortlist', 'tips', 'proposal')),
  provider       text NOT NULL CHECK (provider IN ('anthropic', 'rules')),
  model          text,                                -- Claude model id, NULL for the rules engine
  input_hash     text NOT NULL CHECK (input_hash ~ '^[0-9a-f]{64}$'),
  latency_ms     integer NOT NULL DEFAULT 0 CHECK (latency_ms >= 0),
  tokens_in      integer NOT NULL DEFAULT 0 CHECK (tokens_in >= 0),
  tokens_out     integer NOT NULL DEFAULT 0 CHECK (tokens_out >= 0),
  outcome        text NOT NULL CHECK (outcome IN (
                   'ok', 'fallback', 'unsupported_without_ai', 'refused',
                   'unreachable', 'rate_limited', 'api_error', 'bad_json', 'error'
                 )),
  credential_id  uuid,                                -- the access token that acted for the member, if any (015)
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ai_events_member_day_idx ON vyapar_integration.ai_events (member_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ai_events_created_idx ON vyapar_integration.ai_events (created_at DESC);
COMMENT ON TABLE vyapar_integration.ai_events IS
  '[IMP42] One row per AI-assisted call (draft, read_image, shortlist, tips, proposal): member, provider/model, input hash, latency, tokens, outcome. Never the input text. Immutable; self-only RLS plus analytics operators.';

ALTER TABLE vyapar_integration.ai_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ai_events_self_or_analytics ON vyapar_integration.ai_events;
CREATE POLICY ai_events_self_or_analytics ON vyapar_integration.ai_events
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('analytics'))
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true));

-- No UPDATE or DELETE grant: audit rows are immutable.
GRANT SELECT, INSERT ON vyapar_integration.ai_events TO vyapar_app;
