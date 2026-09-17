-- 030 — An organizer should not be alone: assistants (FR121).
--
-- WHY (2026-09-17, owner's pick 17): Meetup gives a group co-organizers, assistant organizers and
-- event organizers, each with less power than the last, and its own guidance says groups survive
-- when the organizer is not carrying everything alone — the same finding this module already cites
-- from Liu & Suel's study of thousands of Meetup groups. Milavn circles had exactly two states:
-- the person who created it, and everyone else.
--
--   role 'assistant'          helps run the circle: lets people in, welcomes them, posts
--   can_moderate_circle()     organizer OR assistant — the day-to-day work
--   is_circle_organizer()     unchanged: only the creator and organizers decide who holds a role
--   set_circle_role()         the organizer's own decision, never self-service
--
-- An assistant deliberately cannot appoint other assistants, remove the organizer, or delete the
-- circle: the point is to share the work, not to hand over the group.

DO $$ BEGIN
  ALTER TYPE milavn_circle.circle_member_role ADD VALUE IF NOT EXISTS 'assistant';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION milavn_circle.can_moderate_circle(p_circle_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT milavn_circle.is_circle_organizer(p_circle_id, p_member_id)
      OR EXISTS (SELECT 1 FROM milavn_circle.circle_membership m
                 WHERE m.circle_id = p_circle_id AND m.member_id = p_member_id
                   AND m.left_at IS NULL AND m.member_role = 'assistant');
$$;

-- 'member' or 'assistant' only: the organizer role is the creator's, and is not handed around here.
CREATE OR REPLACE FUNCTION milavn_circle.set_circle_role(p_circle_id uuid, p_actor uuid, p_member_id uuid, p_role text)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN false; END IF;
  IF p_role NOT IN ('member', 'assistant') THEN RETURN false; END IF;
  IF NOT milavn_circle.is_circle_organizer(p_circle_id, p_actor) THEN RETURN false; END IF;
  IF EXISTS (SELECT 1 FROM milavn_circle.circle c WHERE c.id = p_circle_id AND c.created_by_member_id = p_member_id) THEN
    RETURN false;  -- the creator's own role is not editable
  END IF;
  UPDATE milavn_circle.circle_membership
     SET member_role = p_role::milavn_circle.circle_member_role
   WHERE circle_id = p_circle_id AND member_id = p_member_id AND left_at IS NULL;
  RETURN FOUND;
END;
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.can_moderate_circle(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.set_circle_role(uuid, uuid, uuid, text) TO milavn_app;
