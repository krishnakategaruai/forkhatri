-- 020 — Discovery that fits (FR110 who it's for + food defaults, FR111 honest discovery upgrades).
--
-- Research (RESEARCH-BEHAVIOUR-2026.md §1.7, §1.9): for brand-new events the organizer is the strongest signal
-- (Zhang & Wang 2015); recommenders starve new hosts unless they get a fair, labelled share (Abdollahpouri et al.
-- 2019); people need a way to say "not for me" and why (Harper et al. 2015); 81% of Indians limit meat (Pew 2021)
-- and family, elder and beginner fit decide whether a community member can come at all.
--
--   occurrence.audience_tags   family_friendly | elder_friendly | beginner_friendly
--   occurrence.food_tags       veg | jain_options | non_veg | alcohol_free  (veg and non_veg are exclusive)
--   discovery.hidden_occurrence  "Not interested" with a reason; "not this host" hides that host for 60 days
--   hosts_attended(member)     how often the viewer checked in at each host's activities (own history only)
--   host_track_record(hosts)   how many activities each host has already held (0 = new host)

ALTER TABLE milavn_activity.occurrence
  ADD COLUMN IF NOT EXISTS audience_tags text[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS food_tags text[] NOT NULL DEFAULT '{}';
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_audience_tags_values
    CHECK (audience_tags <@ ARRAY['family_friendly', 'elder_friendly', 'beginner_friendly']::text[]);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_food_tags_values
    CHECK (food_tags <@ ARRAY['veg', 'jain_options', 'non_veg', 'alcohol_free']::text[] AND NOT (food_tags @> ARRAY['veg', 'non_veg']::text[]));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS milavn_discovery.hidden_occurrence (
  member_id       uuid NOT NULL,
  occurrence_id   uuid NOT NULL,   -- cross-schema ref -> milavn_activity.occurrence(id), no FK (§4)
  reason          text NOT NULL CHECK (reason IN ('not_my_thing', 'too_far', 'bad_time', 'not_this_host')),
  host_member_id  uuid,            -- set only for 'not_this_host'
  created_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, occurrence_id)
);
ALTER TABLE milavn_discovery.hidden_occurrence ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hidden_occurrence_self ON milavn_discovery.hidden_occurrence;
CREATE POLICY hidden_occurrence_self ON milavn_discovery.hidden_occurrence
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, UPDATE, DELETE ON milavn_discovery.hidden_occurrence TO milavn_app;

-- The viewer's own check-in history per host. Answers only for the member bound to the request.
CREATE OR REPLACE FUNCTION milavn_activity.hosts_attended(p_member_id uuid)
RETURNS TABLE (host_member_id uuid, times integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT o.creator_member_id, count(*)::integer
  FROM milavn_activity.participation p
  JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id
  WHERE p.member_id = p_member_id AND p_member_id = current_setting('milavn.member_id', true)::uuid
    AND p.status IN ('checked_in', 'attended') AND o.creator_member_id <> p_member_id
  GROUP BY o.creator_member_id;
$$;

-- How many activities each host has already held (active, started in the past). A count, never who came.
CREATE OR REPLACE FUNCTION milavn_activity.host_track_record(p_host_ids uuid[])
RETURNS TABLE (host_member_id uuid, held integer)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT h, (SELECT count(*)::integer FROM milavn_activity.occurrence o WHERE o.creator_member_id = h AND o.status = 'active' AND o.time_start < now())
  FROM unnest(p_host_ids) AS h;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.hosts_attended(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.host_track_record(uuid[]) TO milavn_app;
