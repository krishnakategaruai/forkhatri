-- [Original-Vyapar upgrade, queued 2026-09-17, approved by product owner
-- as a pure UX upgrade within FR44's existing behavior contract] FR44's
-- own acceptance criteria explicitly names "capture capabilities via
-- structured choices plus free text" as one of the 5 first-run screens —
-- this was never built at all (not just "plainer", genuinely absent; the
-- existing 4 screens are name/language, locality, "what do you want help
-- with", and a completion screen). Adds the two columns first_run needs to
-- actually satisfy this criterion, in the same table the rest of
-- first-run state already lives on.
-- Traces to: FR44, TR044

ALTER TABLE vyapar_identity.members
  ADD COLUMN IF NOT EXISTS capabilities text[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS capabilities_other text;
