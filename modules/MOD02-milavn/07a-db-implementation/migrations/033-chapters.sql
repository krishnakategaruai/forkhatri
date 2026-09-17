-- 033 — Chapters under one umbrella (FR123).
--
-- WHY (2026-09-17, owner's pick 18): Meetup Pro exists because one community often runs in several
-- cities — a Network Administrator holds many groups together and can put an event in front of all
-- of them. A samaj is exactly this shape: Hyderabad, Mumbai, Bengaluru and an overseas chapter, one
-- community. Milavn had flat circles with no way to say "these are the same people, elsewhere".
--
--   circle_group          the umbrella (a samaj, an alumni body, a temple trust)
--   circle.group_id       which umbrella a circle belongs to, if any
--   group_chapters()      the chapters anyone may see: name, locality, how many members
--
-- Belonging to an umbrella does NOT grant access to another chapter's circle: it makes them
-- findable and shows their public activities. Joining a chapter still goes through that chapter's
-- own door (open, or ask-first — migration 024).

CREATE TABLE IF NOT EXISTS milavn_circle.circle_group (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                 text NOT NULL,
  description          text,
  created_by_member_id uuid NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT circle_group_name_sane CHECK (length(name) BETWEEN 1 AND 80)
);
ALTER TABLE milavn_circle.circle_group ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_group_readable ON milavn_circle.circle_group;
CREATE POLICY circle_group_readable ON milavn_circle.circle_group
  FOR SELECT USING (current_setting('milavn.member_id', true) <> '');
DROP POLICY IF EXISTS circle_group_author ON milavn_circle.circle_group;
CREATE POLICY circle_group_author ON milavn_circle.circle_group
  FOR INSERT WITH CHECK (created_by_member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT ON milavn_circle.circle_group TO milavn_app;

ALTER TABLE milavn_circle.circle
  ADD COLUMN IF NOT EXISTS group_id uuid REFERENCES milavn_circle.circle_group(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_circle_group ON milavn_circle.circle (group_id);

-- A chapter list is public-ish on purpose: the point of an umbrella is that a member moving to
-- another city can find their people there. Nothing beyond name, place and size is exposed.
CREATE OR REPLACE FUNCTION milavn_circle.group_chapters(p_group_id uuid)
RETURNS TABLE (circle_id uuid, name text, locality text, member_count integer, join_policy text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT c.id, c.name, COALESCE(c.locality_locality, c.locality_city),
         (SELECT count(*)::integer FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.left_at IS NULL),
         c.join_policy
  FROM milavn_circle.circle c
  WHERE c.group_id = p_group_id
    AND current_setting('milavn.member_id', true) <> ''
  ORDER BY c.name;
$$;

-- Only someone who runs a chapter may put it under an umbrella (or take it out again).
CREATE OR REPLACE FUNCTION milavn_circle.set_circle_group(p_circle_id uuid, p_actor uuid, p_group_id uuid)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN false; END IF;
  IF NOT milavn_circle.is_circle_organizer(p_circle_id, p_actor) THEN RETURN false; END IF;
  UPDATE milavn_circle.circle SET group_id = p_group_id, updated_at = now() WHERE id = p_circle_id;
  RETURN FOUND;
END;
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.group_chapters(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.set_circle_group(uuid, uuid, uuid) TO milavn_app;
