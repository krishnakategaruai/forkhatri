-- Discovery research (1 Oct 2026): consultants see how they are found.
-- Modelled on Fiverr's impressions -> clicks -> orders funnel and Upwork's
-- profile stats. Two small counters, no personal data:
--   * search_impression: how many times a consultant appeared in search results, per day.
--   * profile_view: one row per viewer per consultant per day (viewer_key is a
--     one-way hash, never a member id), so a refresh does not count twice.
SET search_path TO counsel, public;

CREATE TABLE IF NOT EXISTS search_impression (
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  day         date NOT NULL DEFAULT current_date,
  count       int  NOT NULL DEFAULT 0,
  PRIMARY KEY (provider_id, day)
);

CREATE TABLE IF NOT EXISTS profile_view (
  provider_id uuid NOT NULL REFERENCES provider(member_id) ON DELETE CASCADE,
  viewer_key  text NOT NULL,
  day         date NOT NULL DEFAULT current_date,
  PRIMARY KEY (provider_id, day, viewer_key)
);

-- Reply time comes from time requests and paid questions.
CREATE INDEX IF NOT EXISTS question_service_idx ON question(service_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON search_impression, profile_view TO counsel_app;
