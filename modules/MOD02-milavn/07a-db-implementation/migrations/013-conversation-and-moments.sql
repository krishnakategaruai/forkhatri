-- 013 — Beyond the MVP (thesis §57 "copy validated behaviours"): Meetup's
-- event chat and photos, WhatsApp's simple coordination, and Strava's
-- "repeated activity creates identity" — done the Milavn way.
--
--   occurrence_message  — a coordination thread per occurrence, readable and
--                         writable only by the organizer(s) and people who
--                         RSVP'd (attendance stays private, FR040).
--   occurrence_photo    — "moments": photos added after the activity by the
--                         people who were there; visible to the same set.
--   circle_post         — a members-only board per circle (FR023: nothing
--                         outside the Circle package reads membership; the
--                         policy uses the existing definer helper).
--   circle_peer_ids     — who from *your* circles is going, as ids, so the
--                         detail page can name them (they already share a
--                         circle with you, so nothing new is revealed).
--
-- All visibility is decided by one definer helper, can_view_thread(), so the
-- rule lives in one place.

CREATE OR REPLACE FUNCTION milavn_activity.can_view_thread(p_occurrence_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT EXISTS (
    SELECT 1 FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id AND o.creator_member_id = p_member_id
  ) OR EXISTS (
    SELECT 1 FROM milavn_activity.occurrence_co_organizer c
    WHERE c.occurrence_id = p_occurrence_id AND c.member_id = p_member_id AND c.revoked_at IS NULL
  ) OR EXISTS (
    SELECT 1 FROM milavn_activity.participation p
    WHERE p.occurrence_id = p_occurrence_id AND p.member_id = p_member_id
      AND p.status IN ('going','interested','waitlisted','checked_in','attended')
  );
$$;

CREATE OR REPLACE FUNCTION milavn_activity.was_there(p_occurrence_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT EXISTS (
    SELECT 1 FROM milavn_activity.occurrence o WHERE o.id = p_occurrence_id AND o.creator_member_id = p_member_id
  ) OR EXISTS (
    SELECT 1 FROM milavn_activity.occurrence_co_organizer c
    WHERE c.occurrence_id = p_occurrence_id AND c.member_id = p_member_id AND c.revoked_at IS NULL
  ) OR EXISTS (
    SELECT 1 FROM milavn_activity.participation p
    WHERE p.occurrence_id = p_occurrence_id AND p.member_id = p_member_id AND p.status IN ('checked_in','attended')
  );
$$;

CREATE OR REPLACE FUNCTION milavn_activity.circle_peer_ids(p_occurrence_id uuid, p_member_id uuid)
RETURNS SETOF uuid LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, milavn_circle, pg_catalog AS $$
  SELECT DISTINCT p.member_id
  FROM milavn_activity.participation p
  WHERE p.occurrence_id = p_occurrence_id
    AND p.status IN ('going','checked_in','attended')
    AND p.member_id <> p_member_id
    AND EXISTS (
      SELECT 1 FROM milavn_circle.circle_membership a
      JOIN milavn_circle.circle_membership b ON a.circle_id = b.circle_id
      WHERE a.member_id = p_member_id AND a.left_at IS NULL
        AND b.member_id = p.member_id AND b.left_at IS NULL
    )
  LIMIT 12;
$$;

CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_message (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  member_id     uuid NOT NULL,
  body          text NOT NULL CHECK (length(body) BETWEEN 1 AND 1000),
  created_at    timestamptz NOT NULL DEFAULT now(),
  deleted_at    timestamptz
);
CREATE INDEX IF NOT EXISTS occurrence_message_occ_idx ON milavn_activity.occurrence_message (occurrence_id, created_at);

ALTER TABLE milavn_activity.occurrence_message ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_message_thread ON milavn_activity.occurrence_message;
CREATE POLICY occurrence_message_thread ON milavn_activity.occurrence_message
  FOR SELECT USING (milavn_activity.can_view_thread(occurrence_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS occurrence_message_write ON milavn_activity.occurrence_message;
CREATE POLICY occurrence_message_write ON milavn_activity.occurrence_message
  FOR INSERT WITH CHECK (
    member_id = current_setting('milavn.member_id', true)::uuid
    AND milavn_activity.can_view_thread(occurrence_id, current_setting('milavn.member_id', true)::uuid)
  );
DROP POLICY IF EXISTS occurrence_message_own_delete ON milavn_activity.occurrence_message;
CREATE POLICY occurrence_message_own_delete ON milavn_activity.occurrence_message
  FOR UPDATE USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

CREATE TABLE IF NOT EXISTS milavn_activity.occurrence_photo (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurrence_id uuid NOT NULL REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  member_id     uuid NOT NULL,
  storage_ref   text NOT NULL,
  caption       text CHECK (caption IS NULL OR length(caption) <= 200),
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS occurrence_photo_occ_idx ON milavn_activity.occurrence_photo (occurrence_id, created_at DESC);

ALTER TABLE milavn_activity.occurrence_photo ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS occurrence_photo_thread ON milavn_activity.occurrence_photo;
CREATE POLICY occurrence_photo_thread ON milavn_activity.occurrence_photo
  FOR SELECT USING (milavn_activity.can_view_thread(occurrence_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS occurrence_photo_write ON milavn_activity.occurrence_photo;
CREATE POLICY occurrence_photo_write ON milavn_activity.occurrence_photo
  FOR INSERT WITH CHECK (
    member_id = current_setting('milavn.member_id', true)::uuid
    AND milavn_activity.was_there(occurrence_id, current_setting('milavn.member_id', true)::uuid)
  );
DROP POLICY IF EXISTS occurrence_photo_own_delete ON milavn_activity.occurrence_photo;
CREATE POLICY occurrence_photo_own_delete ON milavn_activity.occurrence_photo
  FOR DELETE USING (member_id = current_setting('milavn.member_id', true)::uuid);

CREATE TABLE IF NOT EXISTS milavn_circle.circle_post (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id  uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  member_id  uuid NOT NULL,
  body       text NOT NULL CHECK (length(body) BETWEEN 1 AND 1000),
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);
CREATE INDEX IF NOT EXISTS circle_post_circle_idx ON milavn_circle.circle_post (circle_id, created_at DESC);

ALTER TABLE milavn_circle.circle_post ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS circle_post_members ON milavn_circle.circle_post;
CREATE POLICY circle_post_members ON milavn_circle.circle_post
  FOR SELECT USING (
    milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
    OR milavn_circle.is_circle_creator(circle_id, current_setting('milavn.member_id', true)::uuid)
  );
DROP POLICY IF EXISTS circle_post_write ON milavn_circle.circle_post;
CREATE POLICY circle_post_write ON milavn_circle.circle_post
  FOR INSERT WITH CHECK (
    member_id = current_setting('milavn.member_id', true)::uuid
    AND (
      milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid)
      OR milavn_circle.is_circle_creator(circle_id, current_setting('milavn.member_id', true)::uuid)
    )
  );
DROP POLICY IF EXISTS circle_post_own_delete ON milavn_circle.circle_post;
CREATE POLICY circle_post_own_delete ON milavn_circle.circle_post
  FOR UPDATE USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);

GRANT SELECT, INSERT, UPDATE ON milavn_activity.occurrence_message TO milavn_app;
GRANT SELECT, INSERT, DELETE ON milavn_activity.occurrence_photo TO milavn_app;
GRANT SELECT, INSERT, UPDATE ON milavn_circle.circle_post TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.can_view_thread(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.was_there(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_activity.circle_peer_ids(uuid, uuid) TO milavn_app;

-- Public member card (beyond-MVP "person page"): the non-sensitive projection
-- of a profile another member may see — bio, photo, interests. Locality is
-- served separately through the person's own precision setting (FR041);
-- language preference is never shown to others.
CREATE OR REPLACE FUNCTION milavn_profile.public_card(p_member_id uuid)
RETURNS TABLE (bio text, photo_ref text, interest_tags text[])
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_profile, pg_catalog AS $$
  SELECT p.bio,
         m.storage_ref,
         COALESCE((SELECT array_agg(i.interest_tag ORDER BY i.created_at) FROM milavn_profile.member_interest i WHERE i.member_id = p.member_id), ARRAY[]::text[])
  FROM milavn_profile.member_profile p
  LEFT JOIN milavn_profile.member_profile_media m ON m.id = p.photo_media_id AND m.upload_status = 'completed'
  WHERE p.member_id = p_member_id;
$$;
GRANT EXECUTE ON FUNCTION milavn_profile.public_card(uuid) TO milavn_app;

-- Activities a person hosts (public/community ones only), for their page.
CREATE OR REPLACE FUNCTION milavn_activity.hosted_public_ids(p_member_id uuid)
RETURNS SETOF uuid LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT o.id FROM milavn_activity.occurrence o
  WHERE o.creator_member_id = p_member_id AND o.status = 'active'
    AND o.visibility_scope IN ('public','community') AND o.time_start > now() - interval '3 hours'
  ORDER BY o.time_start LIMIT 10;
$$;
GRANT EXECUTE ON FUNCTION milavn_activity.hosted_public_ids(uuid) TO milavn_app;
