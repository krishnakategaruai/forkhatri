-- 016 — Chat room v3 (FR096 trust-scoped messaging, FR097 expressive avatars).
--
-- Two read helpers the redesigned conversation screen needs:
--
--   presence_of(uuid[])            + last_seen_at, so a person who is not here
--                                    reads "Active 12 min ago" instead of a flat
--                                    "Not active" (the owner judged the v2 room
--                                    "not a 2040 app"; honest recency is the
--                                    modern baseline in every messenger).
--   shared_context(viewer, other)  the reason these two people can talk at all:
--                                    the next activity they are both part of,
--                                    else a circle they share. Trust-scoped
--                                    messaging (FR096) exists only because of
--                                    that shared context, so the room shows it
--                                    and links to it instead of hiding it.
--
-- Privacy: the context is a title, a start time and an approximate locality
-- (FR038 — never an address). shared_context only answers for the member whose
-- id is set as the request context, so the app role cannot probe what two
-- other people have in common.

DROP FUNCTION IF EXISTS milavn_connect.presence_of(uuid[]);
CREATE FUNCTION milavn_connect.presence_of(p_member_ids uuid[])
RETURNS TABLE (member_id uuid, active boolean, expression text, at_occurrence_id uuid, last_seen_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, pg_catalog AS $$
  SELECT p.member_id, p.last_seen_at > now() - interval '2 minutes', p.expression, p.at_occurrence_id, p.last_seen_at
  FROM milavn_connect.presence p WHERE p.member_id = ANY(p_member_ids);
$$;
GRANT EXECUTE ON FUNCTION milavn_connect.presence_of(uuid[]) TO milavn_app;

CREATE OR REPLACE FUNCTION milavn_connect.shared_context(p_viewer uuid, p_other uuid)
RETURNS TABLE (kind text, title text, ref text, starts_at timestamptz, locality text)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_connect, milavn_circle, milavn_activity, pg_catalog AS $$
  WITH allowed AS (
    SELECT p_viewer = current_setting('milavn.member_id', true)::uuid
       AND milavn_connect.can_message(p_viewer, p_other) AS ok
  ),
  candidates AS (
    -- An activity both are in (as participant or organizer) that has not finished: soonest first.
    SELECT 1 AS rnk, 'activity'::text AS kind, o.title, o.canonical_url_slug AS ref, o.time_start AS starts_at,
           COALESCE(o.locality_locality, o.locality_city) AS locality
    FROM milavn_activity.occurrence o
    WHERE o.status = 'active' AND COALESCE(o.time_end, o.time_start + interval '3 hours') > now()
      AND (o.creator_member_id = p_viewer OR EXISTS (
            SELECT 1 FROM milavn_activity.participation p WHERE p.occurrence_id = o.id AND p.member_id = p_viewer
              AND p.status IN ('going','interested','checked_in','attended')))
      AND (o.creator_member_id = p_other OR EXISTS (
            SELECT 1 FROM milavn_activity.participation p WHERE p.occurrence_id = o.id AND p.member_id = p_other
              AND p.status IN ('going','interested','checked_in','attended')))
    UNION ALL
    -- Otherwise a circle both currently belong to.
    SELECT 2, 'circle', c.name, c.id::text, NULL::timestamptz, COALESCE(c.locality_locality, c.locality_city)
    FROM milavn_circle.circle c
    WHERE EXISTS (SELECT 1 FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.member_id = p_viewer AND m.left_at IS NULL)
      AND EXISTS (SELECT 1 FROM milavn_circle.circle_membership m WHERE m.circle_id = c.id AND m.member_id = p_other AND m.left_at IS NULL)
  )
  SELECT c.kind, c.title, c.ref, c.starts_at, c.locality
  FROM candidates c, allowed a
  WHERE a.ok
  ORDER BY c.rnk, c.starts_at NULLS LAST, c.title
  LIMIT 1;
$$;
GRANT EXECUTE ON FUNCTION milavn_connect.shared_context(uuid, uuid) TO milavn_app;
