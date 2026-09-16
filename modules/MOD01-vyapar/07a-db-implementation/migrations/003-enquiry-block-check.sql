-- [TR022/TR024 gap, found during Step 9 curl testing of FR22's blocked-
-- sender handling — fixed forward with a new migration, per the same
-- "001-initial.sql is applied history, not edited in place" rule as
-- migration 002.]
--
-- FR22's own text: "provider has blocked the member -> silently not
-- delivered and shown as Submitted to the sender (no block disclosure)."
-- Implementing this requires `create_enquiry()` (running as the SENDER's
-- own session) to check whether the PROVIDER has a `blocks` row naming the
-- sender. But `vyapar_enquiries.blocks`' own RLS policy
-- (blocks_blocker_only) is correctly scoped to "only the blocker can see
-- their own block list" — which also means the SENDER's session cannot see
-- a row where THEY are the blocked_id, even to answer a narrow yes/no
-- question. Before this migration, that check silently always returned
-- false (RLS filtered the row to nothing), so a blocked sender's enquiry
-- was delivered anyway — not a crash, just quietly wrong, found via direct
-- curl+psql testing, not assumed correct from reading the code.
--
-- Fix: one narrow SECURITY DEFINER boolean check — same pattern as
-- vyapar_listings.contacts_for_viewer()'s own "narrow, callable-by-anyone,
-- answers exactly one question" shape. Deliberately NOT gated to
-- dispatcher/operator (unlike migration 002's notification_targets()):
-- every member legitimately needs this exact check to run as part of
-- their OWN enquiry-creation flow, and the function reveals nothing beyond
-- a boolean (never row contents, never "who else blocked you").
SET search_path TO vyapar_enquiries, pg_temp;

CREATE OR REPLACE FUNCTION vyapar_enquiries.is_blocked(p_blocker_id text, p_blocked_id text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_enquiries, pg_temp
AS $$
  SELECT EXISTS (SELECT 1 FROM vyapar_enquiries.blocks WHERE blocker_id = p_blocker_id AND blocked_id = p_blocked_id);
$$;
COMMENT ON FUNCTION vyapar_enquiries.is_blocked(text, text) IS
  '[TR022/TR024 gap-fix] The one call site create_enquiry() uses to check blocked-sender status — reveals a boolean only, never block-list contents, so it stays consistent with blocks_blocker_only''s own privacy intent while still being answerable from the sender''s own session.';

GRANT EXECUTE ON FUNCTION vyapar_enquiries.is_blocked(text, text) TO vyapar_app;
