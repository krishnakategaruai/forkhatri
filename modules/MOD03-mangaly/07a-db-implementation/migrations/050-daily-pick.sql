-- =============================================================================
-- 050 — "Most compatible today": one stable-matching pick per person per day
--        (DEC-V1-030).
--
-- WHY (2026-09-22): Discover's first row shows ONE person chosen because the
-- two of them fit each other's stated preferences — the result of a daily
-- deferred-acceptance (Gale–Shapley) pass over everyone searchable, run by
-- `mangaly-service/scripts/compute_daily_picks.py`. The pass is global (it
-- needs every searchable row at once), so it runs as the owner role in a
-- maintenance script, exactly like `scripts/reindex_discovery.py`; the app
-- role only ever READS this table, under RLS.
--
-- `rank` 1 is the stable partner; ranks 2..n are the fallbacks (the stable
-- matching re-run with earlier pairs excluded) Discover walks through when
-- the first is already connected, requested or blocked by the time the
-- person opens the app.
--
-- `reasons` is a list of language-neutral reason keys with their parameters
-- ({"key": "wantsYourCity", "city": "Hyderabad"}), translated at read time.
-- There is deliberately NO score column: the baseline rules out a displayed
-- compatibility number, and this table must not become a way to store one.
--
-- Both ids are ACCOUNT ids, the same id space as
-- `discovery_profile_index.profile_id`. Idempotent: safe to re-run.
-- =============================================================================

CREATE TABLE IF NOT EXISTS mangaly_discovery.daily_pick (
  account_id      uuid NOT NULL,
  pick_account_id uuid NOT NULL,
  pick_date       date NOT NULL,
  rank            smallint NOT NULL DEFAULT 1 CHECK (rank >= 1),
  reasons         jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (account_id, pick_date, rank),
  CHECK (account_id <> pick_account_id)
);
COMMENT ON TABLE mangaly_discovery.daily_pick IS
  '[DEC-V1-030] The daily stable-matching pick per person (rank 1) and its fallbacks. No score column, by construction.';
CREATE INDEX IF NOT EXISTS idx_daily_pick_date
  ON mangaly_discovery.daily_pick (pick_date DESC);

ALTER TABLE mangaly_discovery.daily_pick ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS daily_pick_self_or_family ON mangaly_discovery.daily_pick;
CREATE POLICY daily_pick_self_or_family ON mangaly_discovery.daily_pick
  FOR SELECT
  USING (mangaly_authz.is_self(account_id)
         OR mangaly_authz.has_scope(account_id, 'family_info'));

-- Read-only for the application role: the daily job (owner) is the only writer.
GRANT SELECT ON mangaly_discovery.daily_pick TO mangaly_app;
