-- 047 — One open report per person per reported thing (admin console review, 2026-09-29).
--
-- The shared console's Milavn queue showed seven open "misleading" reports about the same
-- activity, all from the same reporter: nothing stopped a person reporting one thing again and
-- again, and each report became its own queue item. From now on:
--   * a person has at most ONE open (open / in_review) report about a given thing; reporting it
--     again returns that report instead of filing another (the API does this; the unique index
--     below makes it hold under concurrency too);
--   * the queue shows one item per reported thing, with how many people reported it.
-- Earlier repeats are kept (they are the owner's data), marked `duplicate_of` the reporter's
-- earliest open report about the same thing, so the new index can hold without deleting them.
-- Safe to run twice.

ALTER TABLE milavn_safety.report
  ADD COLUMN IF NOT EXISTS duplicate_of uuid REFERENCES milavn_safety.report(id) ON DELETE SET NULL;

-- Mark existing repeats: every open report after the reporter's earliest open one about the same thing.
WITH ranked AS (
  SELECT id,
         first_value(id) OVER w AS first_id,
         row_number() OVER w AS n
    FROM milavn_safety.report
   WHERE status IN ('open', 'in_review') AND duplicate_of IS NULL
  WINDOW w AS (PARTITION BY reporter_member_id, subject_type, subject_id ORDER BY created_at, id)
)
UPDATE milavn_safety.report r
   SET duplicate_of = ranked.first_id
  FROM ranked
 WHERE r.id = ranked.id AND ranked.n > 1;

CREATE UNIQUE INDEX IF NOT EXISTS report_one_open_per_reporter_subject
  ON milavn_safety.report (reporter_member_id, subject_type, subject_id)
  WHERE status IN ('open', 'in_review') AND duplicate_of IS NULL;

-- The console member page counts reports, not one reporter's repeats.
CREATE OR REPLACE FUNCTION milavn_safety.member_admin_summary(p_member_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER STABLE
SET search_path = milavn_safety, pg_catalog AS $$
DECLARE since timestamptz;
BEGIN
  IF coalesce(current_setting('milavn.permission_scope', true), '') NOT LIKE '%milavn.moderate%' THEN RETURN NULL; END IF;
  SELECT created_at INTO since FROM milavn_profile.member_profile WHERE member_id = p_member_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  RETURN jsonb_build_object(
    'member_since', since,
    'reports_total', (SELECT count(*) FROM milavn_safety.report r WHERE r.subject_type = 'user' AND r.subject_id = p_member_id AND r.duplicate_of IS NULL),
    'reports_open', (SELECT count(*) FROM milavn_safety.report r WHERE r.subject_type = 'user' AND r.subject_id = p_member_id AND r.status IN ('open', 'in_review') AND r.duplicate_of IS NULL),
    'restricted', EXISTS (
       SELECT 1 FROM milavn_safety.moderation_action a JOIN milavn_safety.report r ON r.id = a.report_id
        WHERE r.subject_type = 'user' AND r.subject_id = p_member_id AND a.action_type = 'restrict'),
    'blocks_against', (SELECT count(*) FROM milavn_safety.block b WHERE b.blocked_member_id = p_member_id),
    'organizes_count', (SELECT count(*) FROM milavn_circle.circle_membership m
                         WHERE m.member_id = p_member_id AND m.left_at IS NULL AND m.member_role = 'organizer'),
    'organizes_names', coalesce((
       SELECT jsonb_agg(x.name) FROM (
         SELECT c.name FROM milavn_circle.circle_membership m JOIN milavn_circle.circle c ON c.id = m.circle_id
          WHERE m.member_id = p_member_id AND m.left_at IS NULL AND m.member_role = 'organizer'
          ORDER BY c.created_at DESC LIMIT 3) x), '[]'::jsonb),
    'member_of_count', (SELECT count(*) FROM milavn_circle.circle_membership m WHERE m.member_id = p_member_id AND m.left_at IS NULL)
  );
END;
$$;
REVOKE ALL ON FUNCTION milavn_safety.member_admin_summary(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_safety.member_admin_summary(uuid) TO milavn_app;
