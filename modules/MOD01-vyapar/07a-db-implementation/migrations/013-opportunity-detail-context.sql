-- [Opportunity detail rebuild — product owner review 2026-09-21: "is this
-- screen and details correct and enough? I don't think any of Upwork or
-- WorkIndia works like this"] Two narrow read paths the detail screen needs
-- and that RLS correctly blocks from a plain SELECT:
--
--   1. How many members have already responded. Upwork shows "Proposals:
--      Less than 5 / 5 to 10 / ..." on every job; WorkIndia shows an
--      applicant-count pill on every job card. Enquiries are visible only to
--      their two parties (enquiries_participants), so a viewer cannot count
--      other people's responses. Returned as a coarse BUCKET, never a raw
--      count or any identity — the minimum a person needs to judge
--      competition, nothing that could reveal who applied.
--
--   2. Who the poster is. Upwork's "About the client" (member since, jobs
--      posted, payment verified) and WorkIndia's company/contact block exist
--      because a person decides whether to trust an opportunity by who is
--      behind it. Other members' rows are RLS-private, so this returns only
--      member-since, count of active opportunities, and the poster's own
--      VERIFIED business listing if one exists — gated exactly like
--      public_names(): only for members who already have a public presence.
--
-- Both follow MODULE-ARCHITECTURE-STANDARD §4's escape-hatch constraints:
-- exact match on a full identifier, minimal projection, validity enforced
-- inside the function, at most one row, search_path pinned.
-- Traces to: FR55, FR16 (trust context), FR28, UX09

CREATE OR REPLACE FUNCTION vyapar_enquiries.opportunity_response_bucket(p_opportunity_id uuid)
RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
  SELECT CASE
           WHEN n = 0 THEN 'none'
           WHEN n < 5 THEN 'under_5'
           WHEN n <= 10 THEN '5_to_10'
           WHEN n <= 20 THEN '10_to_20'
           ELSE '20_plus'
         END
    FROM (
      SELECT count(*) AS n
        FROM vyapar_enquiries.enquiries e
       WHERE e.opportunity_id = p_opportunity_id
         AND e.state <> 'withdrawn'
         AND EXISTS (
           SELECT 1 FROM vyapar_opportunities.opportunities o
            WHERE o.id = p_opportunity_id AND o.state IN ('active', 'paused', 'stale')
         )
    ) c;
$$;

CREATE OR REPLACE FUNCTION vyapar_identity.poster_summary(p_member_id text)
RETURNS TABLE(member_since date, active_opportunities integer, verified_listing_id uuid, verified_listing_name text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_identity, pg_temp AS $$
  SELECT m.created_at::date,
         (SELECT count(*)::integer FROM vyapar_opportunities.opportunities o
           WHERE o.poster_id = m.id AND o.state IN ('active', 'paused', 'stale')),
         vl.id,
         vl.name
    FROM vyapar_identity.members m
    LEFT JOIN LATERAL (
      SELECT l.id, l.name FROM vyapar_listings.listings l
       WHERE l.owner_id = m.id AND l.state = 'active_verified'
       ORDER BY l.verified_at DESC NULLS LAST
       LIMIT 1
    ) vl ON true
   WHERE m.id = p_member_id AND NOT m.anonymized AND m.deleted_at IS NULL
     AND (EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.owner_id = m.id AND l.state IN ('active_unverified','active_verified'))
       OR EXISTS (SELECT 1 FROM vyapar_opportunities.opportunities o WHERE o.poster_id = m.id AND o.state IN ('active','paused','stale')))
   LIMIT 1;
$$;

REVOKE ALL ON FUNCTION vyapar_enquiries.opportunity_response_bucket(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION vyapar_identity.poster_summary(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_enquiries.opportunity_response_bucket(uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_identity.poster_summary(text) TO vyapar_app;
