-- 040 — Circles are communities, not pairs and not chats (owner review, 2026-09-28).
--
-- Three corrections from the same live review of the circle page:
--
-- 1. [Pairs are not circles] The formation-suggestion job (migration 008, FR022/TR17) suggested a
--    "circle" for every co-participation PAIR, and one person's acceptance created a real circle
--    containing only that one person ("Asha & Arjun's circle", 1 member). The owner: a connection
--    with one person is a connection/chat, never a circle. A suggestion now needs a genuine group
--    (3+ people), members record an explicit accept/decline, and the circle is created only once a
--    second person has accepted — everyone who accepted is in it from the start.
--
-- 2. [Admin-only posting] Some communities are announcement-style: only the organizer(s) post
--    (WhatsApp announcement groups, admin-post-only Facebook groups). That is a per-circle setting,
--    editable by the organizer.
--
-- 3. [Posts, not messages] A circle's content is Instagram/Facebook-style posts — text and a photo
--    (documents later) — plus its events. `circle_post` gains the photo reference.
--
-- Also: the sealed `circle_modify` policy (001) let only the circle's CREATOR update the row, but
-- circles get handed over; management belongs to whoever is the organizer today.

-- (1) Suggestions: explicit consent, group-sized, one created circle.
ALTER TABLE milavn_circle.circle_formation_suggestion_member
  ADD COLUMN IF NOT EXISTS accepted boolean;
ALTER TABLE milavn_circle.circle_formation_suggestion
  ADD COLUMN IF NOT EXISTS created_circle_id uuid REFERENCES milavn_circle.circle(id);

-- Pending pair-sized suggestions predate this rule; close them out.
UPDATE milavn_circle.circle_formation_suggestion s
SET status = 'declined', responded_at = now()
WHERE s.status = 'pending'
  AND (SELECT count(*) FROM milavn_circle.circle_formation_suggestion_member sm WHERE sm.suggestion_id = s.id) < 3;

-- (2) Per-circle posting policy.
ALTER TABLE milavn_circle.circle
  ADD COLUMN IF NOT EXISTS posting_policy text NOT NULL DEFAULT 'members'
  CHECK (posting_policy IN ('members', 'organizers'));

-- (3) A post can carry one photo (same local-disk object-storage stand-in as Moments).
ALTER TABLE milavn_circle.circle_post
  ADD COLUMN IF NOT EXISTS photo_ref text;

-- Management follows today's organizer role, not the original creator.
DROP POLICY IF EXISTS circle_modify ON milavn_circle.circle;
CREATE POLICY circle_modify ON milavn_circle.circle
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM milavn_circle.circle_membership m
      WHERE m.circle_id = circle.id
        AND m.member_id = current_setting('milavn.member_id', true)::uuid
        AND m.member_role = 'organizer'
        AND m.left_at IS NULL
    )
  );

-- Polls are posts in the circle's feed (FB/WhatsApp model): alongside "which day?"
-- ('date') and "which one?" ('activity'), a plain question with text answers.
ALTER TABLE milavn_circle.poll DROP CONSTRAINT IF EXISTS poll_kind_known;
ALTER TABLE milavn_circle.poll ADD CONSTRAINT poll_kind_known CHECK (kind IN ('date', 'activity', 'question'));

-- A photo can be the whole post (body optional when a photo is attached).
ALTER TABLE milavn_circle.circle_post DROP CONSTRAINT IF EXISTS circle_post_body_check;
ALTER TABLE milavn_circle.circle_post ADD CONSTRAINT circle_post_body_check
  CHECK (length(body) <= 1000 AND (length(body) >= 1 OR photo_ref IS NOT NULL));
