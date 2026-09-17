-- 038 — Open circles must be visible before they can be discovered (defect fix).
--
-- [Found live, 2026-09-18, while verifying FR125] The sealed `circle_visibility` RLS policy (migration
-- 001) only ever let a signed-in non-member SEE a 'public' or 'community' circle row. 'interest',
-- 'local', 'recurring_activity' — and the new 'temple'/'travel' (FR125) — are all in `OPEN_TYPES`
-- (joinable in one tap, per FR021/FR115's own `join()`/`request_join()`), yet RLS hid every one of
-- them from anyone who was not already a member or the creator. The result: `GET /circles/discover`
-- could never actually return an 'interest' circle to someone who had not already joined it — a
-- "Discover" screen that can only show you what you already have is not discovery at all, and it is
-- exactly why FR115 had to build a whole separate `join_prompt()` SECURITY DEFINER bypass just so a
-- non-member could read a circle's name before asking to join it. Confirmed live: creating a temple
-- and a travel circle as one member, then querying `/circles/discover` as a second member who had
-- joined neither returned zero rows; after joining one of the two, only that one appeared.
--
-- The fix makes circle_visibility match `OPEN_TYPES` exactly: every type a member can join without
-- an invitation is also a type they may see before joining. 'private' and 'organization' — the two
-- invite-only types — are unchanged: still visible only to their own members or creator.

DROP POLICY IF EXISTS circle_visibility ON milavn_circle.circle;
CREATE POLICY circle_visibility ON milavn_circle.circle
  FOR SELECT
  USING (
    circle_type IN ('public','community','interest','local','recurring_activity','temple','travel')
    OR created_by_member_id = current_setting('milavn.member_id', true)::uuid
    OR milavn_circle.is_active_member(circle.id, current_setting('milavn.member_id', true)::uuid)
  );
