-- Owner request (2026-09-30): consultants earn milestone badges from their work.
-- Awards are kept with the date they were earned (never re-dated), so they can
-- later drive premium price ranges and awards. The level summary is stored per
-- provider for ranking and admin views.
SET search_path TO counsel, public;

CREATE TABLE IF NOT EXISTS badge_award (
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  badge_id    text NOT NULL,
  level       int  NOT NULL DEFAULT 1,       -- tiered badges climb levels; each level is its own row
  awarded_at  timestamptz NOT NULL DEFAULT now(),
  evidence    jsonb NOT NULL DEFAULT '{}'::jsonb,  -- the numbers at the moment it was earned
  PRIMARY KEY (provider_id, badge_id, level)
);
CREATE INDEX IF NOT EXISTS badge_award_provider_idx ON badge_award(provider_id);

ALTER TABLE provider ADD COLUMN IF NOT EXISTS standing text NOT NULL DEFAULT 'new';   -- new | rising | established | senior | distinguished

GRANT SELECT, INSERT, UPDATE, DELETE ON badge_award TO counsel_app;
