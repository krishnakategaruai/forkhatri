-- =============================================================================
-- 063 — Guides: short articles (and later videos) that teach families how to
-- use Mangalya well — making a better profile, taking good photos, style,
-- reporting and blocking, and different family situations.
--
-- WHY (owner, 2026-10-01): "one more tab ... educational video or posts, how
-- to report, how to make profile better, how to support for different
-- situations, how to get good photos, style references and many more".
-- Guides live in the database so new posts and videos can be added without a
-- release. The first set is written in English, Hindi and Telugu and loaded
-- by migration 064 (generated from mangaly-service/app/components/guides/
-- content.json by scripts/build_guides_migration.py).
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS mangaly_content AUTHORIZATION mangaly_owner;
GRANT USAGE ON SCHEMA mangaly_content TO mangaly_app;

CREATE TABLE IF NOT EXISTS mangaly_content.guide (
  slug         text PRIMARY KEY,
  category     text NOT NULL,              -- start, profile, photos, safety, family, next
  sort_order   integer NOT NULL DEFAULT 100,
  minutes      integer NOT NULL DEFAULT 2, -- reading time
  video_url    text,                       -- optional: an https video to play above the text
  action_href  text,                       -- optional: the screen the guide leads to
  -- {"en": {"title", "summary", "sections": [{"h"?, "p"?, "points"?}]}, "hi": …, "te": …}
  content      jsonb NOT NULL,
  published    boolean NOT NULL DEFAULT true,
  updated_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_guide_published
  ON mangaly_content.guide (category, sort_order) WHERE published;

-- Public reading material: no row-level rules; the app may only read.
GRANT SELECT ON mangaly_content.guide TO mangaly_app;
