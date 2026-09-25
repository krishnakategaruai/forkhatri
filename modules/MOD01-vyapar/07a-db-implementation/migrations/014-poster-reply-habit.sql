-- [Opportunity detail, second pass — product owner pointed to the Upwork and
-- WorkIndia reference screenshots: "we will be more and best over on that,
-- not that we follow them."] Upwork's "About the client" shows hire rate and
-- jobs posted; WorkIndia's Activity tab counts "HR Responses" and "Pending
-- Calls". Both are trying to answer the one question a person really has
-- before spending effort on a response: WILL THIS PERSON GET BACK TO ME?
-- Neither answers it directly. This does: of the enquiries the poster has
-- received in the last 90 days, how many got a first reply, and how fast.
--
-- Returned as coarse buckets only (never a raw count, never who asked), and
-- only once there are at least 3 received enquiries — below that a
-- percentage is noise and would unfairly brand a new member. Enquiries are
-- RLS-private to their two parties, so this needs the same narrow
-- SECURITY DEFINER path as 013's functions, under the same constraints
-- (MODULE-ARCHITECTURE-STANDARD §4): exact-match identifier, minimal
-- projection, at most one row, search_path pinned.
-- Traces to: FR55, FR23 (first_reply_at), FR16/FR28 (trust context), UX09

CREATE OR REPLACE FUNCTION vyapar_enquiries.poster_reply_habit(p_member_id text)
RETURNS TABLE(reply_rate text, reply_speed text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
  WITH recv AS (
    SELECT e.created_at, e.first_reply_at
      FROM vyapar_enquiries.enquiries e
     WHERE e.provider_id = p_member_id
       AND e.state <> 'withdrawn'
       AND e.created_at > now() - interval '90 days'
  ), agg AS (
    SELECT count(*) AS n,
           count(first_reply_at) AS replied,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM first_reply_at - created_at))
             FILTER (WHERE first_reply_at IS NOT NULL) AS median_secs
      FROM recv
  )
  SELECT CASE
           WHEN replied::numeric / n >= 0.7 THEN 'most'
           WHEN replied::numeric / n >= 0.3 THEN 'some'
           ELSE 'few'
         END,
         CASE
           WHEN median_secs IS NULL THEN NULL
           WHEN median_secs <= 6 * 3600 THEN 'hours'
           WHEN median_secs <= 24 * 3600 THEN 'day'
           ELSE 'days'
         END
    FROM agg
   WHERE n >= 3;
$$;

REVOKE ALL ON FUNCTION vyapar_enquiries.poster_reply_habit(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_enquiries.poster_reply_habit(text) TO vyapar_app;
