-- 032 — Follow someone's calendar, not just one activity (FR122).
--
-- WHY (2026-09-17, owner's pick 23): Luma's strongest idea is that a Calendar is a first-class
-- thing you follow — every new date the host posts lands in your own calendar app automatically,
-- which is precisely what a weekly badminton or a temple's monthly satsang needs. Milavn could only
-- export one activity at a time, so a regular host's community had to remember to come back and
-- look.
--
--   calendar_follow          who I follow (their public activities appear in my calendar)
--   followed_host_ids(me)    for the in-app calendar
--   public_activities_of()   for the subscribable .ics feed — PUBLIC activities only, ever
--
-- The feed is deliberately built from public activities alone: a circle-only or personal activity
-- never leaves the app, because a calendar feed is an unauthenticated URL by nature.

CREATE TABLE IF NOT EXISTS milavn_activity.calendar_follow (
  member_id      uuid NOT NULL,
  host_member_id uuid NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, host_member_id),
  CONSTRAINT calendar_follow_not_self CHECK (member_id <> host_member_id)
);
ALTER TABLE milavn_activity.calendar_follow ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS calendar_follow_self ON milavn_activity.calendar_follow;
CREATE POLICY calendar_follow_self ON milavn_activity.calendar_follow
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, DELETE ON milavn_activity.calendar_follow TO milavn_app;

CREATE OR REPLACE FUNCTION milavn_activity.followed_host_ids(p_member_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, milavn_safety, pg_catalog AS $$
  SELECT coalesce(array_agg(f.host_member_id), ARRAY[]::uuid[])
  FROM milavn_activity.calendar_follow f
  WHERE f.member_id = p_member_id
    AND p_member_id = current_setting('milavn.member_id', true)::uuid
    AND NOT milavn_safety.is_blocked_either_way(f.member_id, f.host_member_id);
$$;

-- The feed's contents. No session is involved (a calendar app cannot sign in), so this returns only
-- what is already public on the web, and only around the present.
CREATE OR REPLACE FUNCTION milavn_activity.public_activities_of(p_host_member_id uuid)
RETURNS TABLE (id uuid, title text, description text, time_start timestamptz, time_end timestamptz, locality text, slug text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT o.id, o.title, o.description, o.time_start, o.time_end,
         COALESCE(o.locality_locality, o.locality_city), o.canonical_url_slug
  FROM milavn_activity.occurrence o
  WHERE o.creator_member_id = p_host_member_id
    AND o.status = 'active'
    AND o.visibility_scope = 'public'
    AND o.time_start > now() - interval '30 days'
  ORDER BY o.time_start
  LIMIT 200;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.followed_host_ids(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.public_activities_of(uuid) TO milavn_app;
