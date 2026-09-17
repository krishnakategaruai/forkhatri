-- 036 — Samaj updates: one announcement, every chapter (FR126).
--
-- WHY (2026-09-18, owner request, completing FR123): an umbrella (a samaj, an alumni body) was
-- findable but voiceless — its chapters had no way to hear from the community as a whole, only from
-- their own circle's board. Meetup Pro's own network events feature is exactly this: a network
-- administrator puts one update in front of every group in the network. A samaj needs the same
-- thing for a festival date, a collective decision, or news that matters to every chapter at once.
--
--   circle_group_update      one message from the umbrella's admin (its creator), to every chapter
--   is_group_member()        true for anyone with an active membership in ANY chapter under it
--   is_group_admin()         true only for the umbrella's own creator (no delegation here yet)
--   group_member_ids()       every distinct member across every chapter, for the notification fan-out
--
-- Posting is deliberately admin-only and not delegated to chapter organizers: a chapter organizer
-- already has their own board for their own chapter; the umbrella-wide channel is reserved for the
-- one person accountable for the umbrella itself, the same way Meetup Pro reserves network-wide
-- events for the Network Administrator, not every group's own organizer.

CREATE TABLE IF NOT EXISTS milavn_circle.circle_group_update (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id             uuid NOT NULL REFERENCES milavn_circle.circle_group(id) ON DELETE CASCADE,
  created_by_member_id uuid NOT NULL,
  message              text NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT group_update_message_sane CHECK (length(message) BETWEEN 1 AND 1000)
);
CREATE INDEX IF NOT EXISTS idx_group_update_group ON milavn_circle.circle_group_update (group_id, created_at DESC);

CREATE OR REPLACE FUNCTION milavn_circle.is_group_member(p_group_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (
    SELECT 1 FROM milavn_circle.circle c
    WHERE c.group_id = p_group_id AND milavn_circle.is_active_member(c.id, p_member_id)
  );
$$;

CREATE OR REPLACE FUNCTION milavn_circle.is_group_admin(p_group_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_circle.circle_group g WHERE g.id = p_group_id AND g.created_by_member_id = p_member_id);
$$;

-- Every distinct member across every chapter — the fan-out list for one update's notifications.
CREATE OR REPLACE FUNCTION milavn_circle.group_member_ids(p_group_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(array_agg(DISTINCT m.member_id), ARRAY[]::uuid[])
  FROM milavn_circle.circle c
  JOIN milavn_circle.circle_membership m ON m.circle_id = c.id AND m.left_at IS NULL
  WHERE c.group_id = p_group_id;
$$;

ALTER TABLE milavn_circle.circle_group_update ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS group_update_readable ON milavn_circle.circle_group_update;
CREATE POLICY group_update_readable ON milavn_circle.circle_group_update
  FOR SELECT USING (
    milavn_circle.is_group_member(group_id, current_setting('milavn.member_id', true)::uuid)
    OR milavn_circle.is_group_admin(group_id, current_setting('milavn.member_id', true)::uuid)
  );
DROP POLICY IF EXISTS group_update_admin_writes ON milavn_circle.circle_group_update;
CREATE POLICY group_update_admin_writes ON milavn_circle.circle_group_update
  FOR INSERT WITH CHECK (
    created_by_member_id = current_setting('milavn.member_id', true)::uuid
    AND milavn_circle.is_group_admin(group_id, created_by_member_id)
  );
GRANT SELECT, INSERT ON milavn_circle.circle_group_update TO milavn_app;

GRANT EXECUTE ON FUNCTION milavn_circle.is_group_member(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.is_group_admin(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.group_member_ids(uuid) TO milavn_app;
