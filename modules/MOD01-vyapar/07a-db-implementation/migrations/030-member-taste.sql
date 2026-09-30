-- [Recommendations that learn, 2026-09-30] A member's learned taste.
-- Additive and idempotent (safe to run twice).
--
-- Vyapar's ranking learns from each member's OWN actions (applied, hired,
-- saved, shared, opened, "More like this", "Not interested" with its reason,
-- withdrawn) over CONTENT attributes of the posts and profiles they acted on:
-- skills, categories, kind of post, work mode, distance band, pay band,
-- shift, experience band and trade words in titles. Never the poster's
-- identity, name, community, gender, religion or any person attribute, and
-- never other members' behaviour. See app/taste.py for the model and
-- references/imp-recommendations.md for the design.
--
--   1. vyapar_privacy.member_taste — one row per member: the learned model
--      (jsonb), a fingerprint of the actions it was built from, the reset
--      point and the items the member removed. It is derived personal data,
--      so it lives next to derived_preferences (FR38) in vyapar_privacy.
--      RLS: only the member and the background dispatcher can read or write
--      it. Operators are deliberately NOT admitted: no admin can read or
--      write a member's taste.
--   2. member_opportunity.more_like_this_at — "More like this" on a post, a
--      strong positive the member gives on purpose.
--   3. privacy_settings.personalised_recommendations — the member's switch
--      for learning (default on). Learning also stops when the existing
--      "Usage analytics" switch (behavioral_analytics) is off, because that
--      switch promises nothing is recorded while it is off.
--   4. Three SECURITY DEFINER reads, each callable only for yourself or by
--      the dispatcher: whether learning is allowed, and the member's own
--      actions with the CONTENT columns of the posts / profiles they touched.
--      Definer is needed because a post the member applied to is often
--      closed or expired later (hidden from them by the visibility policy),
--      and a hire is the strongest signal of all. The functions return no
--      poster id, name or any person column: the structural absence is the
--      fairness control.
-- Traces to: FR19, FR20, FR21, FR36, FR37, FR38, FR55, TR019, TR020, TR021, SP019

CREATE TABLE IF NOT EXISTS vyapar_privacy.member_taste (
  member_id    text PRIMARY KEY,
  model        jsonb NOT NULL DEFAULT '{}',
  fingerprint  text,
  reset_at     timestamptz,
  removed      jsonb NOT NULL DEFAULT '{}',   -- {item_id: iso timestamp}: actions before it no longer count for that item
  updated_at   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE vyapar_privacy.member_taste IS
  'Learned recommendation taste per member, from their own actions over content attributes only. Member and dispatcher only; never operators.';

ALTER TABLE vyapar_privacy.member_taste ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_taste_self_or_dispatcher ON vyapar_privacy.member_taste;
CREATE POLICY member_taste_self_or_dispatcher ON vyapar_privacy.member_taste
  USING (member_id = current_setting('vyapar.authz_context', true)
         OR current_setting('vyapar.service_role', true) = 'dispatcher')
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true)
              OR current_setting('vyapar.service_role', true) = 'dispatcher');
GRANT SELECT, INSERT, UPDATE, DELETE ON vyapar_privacy.member_taste TO vyapar_app;

ALTER TABLE vyapar_opportunities.member_opportunity
  ADD COLUMN IF NOT EXISTS more_like_this_at timestamptz;

ALTER TABLE vyapar_privacy.privacy_settings
  ADD COLUMN IF NOT EXISTS personalised_recommendations boolean NOT NULL DEFAULT true;

-- Whether a member's taste may be learned and used.
CREATE OR REPLACE FUNCTION vyapar_privacy.personalisation_allowed(p_member_id text)
RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = vyapar_privacy, pg_temp
AS $$
DECLARE
  v boolean;
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('vyapar.authz_context', true)
     AND current_setting('vyapar.service_role', true) IS DISTINCT FROM 'dispatcher' THEN
    RAISE EXCEPTION 'personalisation_allowed() is for the member themself or the dispatcher';
  END IF;
  SELECT ps.personalised_recommendations AND ps.behavioral_analytics INTO v
    FROM vyapar_privacy.privacy_settings ps WHERE ps.member_id = p_member_id;
  RETURN coalesce(v, true);
END;
$$;
GRANT EXECUTE ON FUNCTION vyapar_privacy.personalisation_allowed(text) TO vyapar_app;

-- The member's own actions on posts, with the posts' content columns only.
CREATE OR REPLACE FUNCTION vyapar_opportunities.member_taste_events(p_member_id text, p_since timestamptz)
RETURNS TABLE(
  opportunity_id uuid, title text, type text, work_mode text, shift text, required_capabilities text[],
  experience_min_months smallint, salary_min_paise bigint, salary_max_paise bigint,
  budget_min_paise bigint, budget_max_paise bigint, budget_paise bigint, lat double precision, lng double precision,
  saved_at timestamptz, viewed_at timestamptz, hidden_at timestamptz, hidden_reason text, shared_at timestamptz,
  external_opened_at timestamptz, completed_at timestamptz, more_like_this_at timestamptz,
  applied_at timestamptz, hired_at timestamptz, withdrawn_at timestamptz
)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = vyapar_opportunities, pg_temp
AS $$
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('vyapar.authz_context', true)
     AND current_setting('vyapar.service_role', true) IS DISTINCT FROM 'dispatcher' THEN
    RAISE EXCEPTION 'member_taste_events() is for the member themself or the dispatcher';
  END IF;
  RETURN QUERY
    WITH acts AS (
      SELECT mo.opportunity_id AS oid, mo.saved_at, mo.viewed_at, mo.hidden_at, mo.hidden_reason, mo.shared_at,
             mo.external_opened_at, mo.completed_at, mo.more_like_this_at,
             NULL::timestamptz AS applied_at, NULL::timestamptz AS hired_at, NULL::timestamptz AS withdrawn_at
        FROM vyapar_opportunities.member_opportunity mo
       WHERE mo.member_id = p_member_id
      UNION ALL
      SELECT e.opportunity_id, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
             e.created_at,
             CASE WHEN e.stage = 'hired' THEN coalesce(e.stage_changed_at, e.updated_at) END,
             CASE WHEN e.state = 'withdrawn' THEN e.updated_at END
        FROM vyapar_enquiries.enquiries e
       WHERE e.sender_id = p_member_id AND e.opportunity_id IS NOT NULL
    ), merged AS (
      SELECT oid, max(a.saved_at) AS saved_at, max(a.viewed_at) AS viewed_at, max(a.hidden_at) AS hidden_at,
             max(a.hidden_reason) AS hidden_reason, max(a.shared_at) AS shared_at,
             max(a.external_opened_at) AS external_opened_at, max(a.completed_at) AS completed_at,
             max(a.more_like_this_at) AS more_like_this_at, max(a.applied_at) AS applied_at,
             max(a.hired_at) AS hired_at, max(a.withdrawn_at) AS withdrawn_at
        FROM acts a GROUP BY oid
    )
    SELECT o.id, o.title, o.type, o.work_mode, o.shift, o.required_capabilities,
           o.experience_min_months, o.salary_min_paise, o.salary_max_paise,
           o.budget_min_paise, o.budget_max_paise, o.budget_paise, o.lat, o.lng,
           m.saved_at, m.viewed_at, m.hidden_at, m.hidden_reason, m.shared_at,
           m.external_opened_at, m.completed_at, m.more_like_this_at, m.applied_at, m.hired_at, m.withdrawn_at
      FROM merged m
      JOIN vyapar_opportunities.opportunities o ON o.id = m.oid
     WHERE o.poster_id <> p_member_id          -- your own posts teach nothing about what you look for
       AND o.state <> 'removed'                -- a post taken down by moderation teaches nothing
       AND greatest(m.saved_at, m.viewed_at, m.hidden_at, m.shared_at, m.external_opened_at, m.completed_at,
                    m.more_like_this_at, m.applied_at, m.hired_at, m.withdrawn_at) >= p_since
     ORDER BY o.id
     LIMIT 600;
END;
$$;
GRANT EXECUTE ON FUNCTION vyapar_opportunities.member_taste_events(text, timestamptz) TO vyapar_app;

-- The member's own actions on business and work profiles, with the profiles'
-- content columns only (skills only when the owner shows them).
CREATE OR REPLACE FUNCTION vyapar_listings.member_taste_listing_events(p_member_id text, p_since timestamptz)
RETURNS TABLE(
  listing_id uuid, kind text, capabilities text[], categories text[], lat double precision, lng double precision,
  saved_at timestamptz, viewed_at timestamptz, contacted_at timestamptz
)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = vyapar_listings, pg_temp
AS $$
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('vyapar.authz_context', true)
     AND current_setting('vyapar.service_role', true) IS DISTINCT FROM 'dispatcher' THEN
    RAISE EXCEPTION 'member_taste_listing_events() is for the member themself or the dispatcher';
  END IF;
  RETURN QUERY
    WITH acts AS (
      SELECT ml.listing_id AS lid, ml.saved_at, ml.viewed_at, NULL::timestamptz AS contacted_at
        FROM vyapar_listings.member_listing ml WHERE ml.member_id = p_member_id
      UNION ALL
      SELECT e.listing_id, NULL, NULL, e.created_at
        FROM vyapar_enquiries.enquiries e
       WHERE e.sender_id = p_member_id AND e.listing_id IS NOT NULL AND e.opportunity_id IS NULL
    ), merged AS (
      SELECT lid, max(a.saved_at) AS saved_at, max(a.viewed_at) AS viewed_at, max(a.contacted_at) AS contacted_at
        FROM acts a GROUP BY lid
    )
    SELECT l.id, l.kind, CASE WHEN l.capability_visible THEN l.capabilities ELSE '{}'::text[] END,
           l.categories, l.lat, l.lng, m.saved_at, m.viewed_at, m.contacted_at
      FROM merged m
      JOIN vyapar_listings.listings l ON l.id = m.lid
     WHERE l.owner_id <> p_member_id
       AND greatest(m.saved_at, m.viewed_at, m.contacted_at) >= p_since
     ORDER BY l.id
     LIMIT 300;
END;
$$;
GRANT EXECUTE ON FUNCTION vyapar_listings.member_taste_listing_events(text, timestamptz) TO vyapar_app;
