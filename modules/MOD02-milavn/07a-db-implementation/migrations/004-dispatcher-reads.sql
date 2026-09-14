-- =============================================================================
-- Milavn (MOD02) — migration 004: dispatcher-side reads. Run as milavn_owner.
--
-- Notification Dispatch runs AFTER a request's transaction commits, in its
-- own transaction with no acting member (there is no "member" behind a
-- fan-out). `occurrence`'s SELECT policy casts `milavn.member_id` to uuid, so
-- an unset variable is a cast error, not an empty result. The dispatcher
-- reads the few non-sensitive fields it needs (title, slug, creator) through
-- a definer-owned function instead of widening any policy.
-- =============================================================================

CREATE OR REPLACE FUNCTION milavn_activity.occurrence_brief(p_occurrence_id uuid)
RETURNS TABLE(title text, canonical_url_slug text, creator_member_id uuid, visibility_scope text, circle_id uuid)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_activity, pg_catalog AS $$
  SELECT title, canonical_url_slug, creator_member_id, visibility_scope::text, circle_id
  FROM milavn_activity.occurrence WHERE id = p_occurrence_id;
$$;

-- Circle member ids for the opportunity-class fan-out (FR054) — ids only.
CREATE OR REPLACE FUNCTION milavn_circle.active_member_ids(p_circle_id uuid)
RETURNS uuid[] LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(array_agg(member_id), ARRAY[]::uuid[]) FROM milavn_circle.circle_membership
  WHERE circle_id = p_circle_id AND left_at IS NULL;
$$;

GRANT EXECUTE ON FUNCTION milavn_activity.occurrence_brief(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.active_member_ids(uuid) TO milavn_app;
