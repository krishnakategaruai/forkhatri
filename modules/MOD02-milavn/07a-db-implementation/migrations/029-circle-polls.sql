-- 029 — Asking the circle: which day, or which one shall we go to? (FR120)
--
-- WHY (2026-09-17, owner's picks 6 and 7): Partiful polls the guests for a date BEFORE the event
-- exists, which is exactly how a family or a badminton group actually decides ("Sunday or next
-- Saturday?"); Dice added Groups so friends can vote on which show to attend together before anyone
-- commits. Both are the same primitive — a small question inside a group, with named answers —
-- so Milavn gets one poll rather than two features:
--
--   kind 'date'      options are times; the winner becomes the activity, prefilled
--   kind 'activity'  options are activities already posted; the winner is where the group goes
--
-- Votes are not secret: inside a circle, "Meera and Ravi can do Sunday" is the useful part, and it
-- is the same thing a WhatsApp poll shows. A member may pick more than one option (most people can
-- do several days) and can change their mind until the poll closes.

CREATE TABLE IF NOT EXISTS milavn_circle.poll (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id            uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  created_by_member_id uuid NOT NULL,
  question             text NOT NULL,
  kind                 text NOT NULL DEFAULT 'date',
  created_at           timestamptz NOT NULL DEFAULT now(),
  closed_at            timestamptz,
  CONSTRAINT poll_kind_known CHECK (kind IN ('date', 'activity')),
  CONSTRAINT poll_question_sane CHECK (length(question) BETWEEN 1 AND 160)
);
CREATE INDEX IF NOT EXISTS idx_poll_circle ON milavn_circle.poll (circle_id, created_at DESC);

CREATE TABLE IF NOT EXISTS milavn_circle.poll_option (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  poll_id       uuid NOT NULL REFERENCES milavn_circle.poll(id) ON DELETE CASCADE,
  label         text NOT NULL,
  option_time   timestamptz,
  occurrence_id uuid REFERENCES milavn_activity.occurrence(id) ON DELETE CASCADE,
  position      integer NOT NULL DEFAULT 0,
  CONSTRAINT poll_option_label_sane CHECK (length(label) BETWEEN 1 AND 120)
);
CREATE INDEX IF NOT EXISTS idx_poll_option_poll ON milavn_circle.poll_option (poll_id, position);

CREATE TABLE IF NOT EXISTS milavn_circle.poll_vote (
  option_id  uuid NOT NULL REFERENCES milavn_circle.poll_option(id) ON DELETE CASCADE,
  member_id  uuid NOT NULL,
  poll_id    uuid NOT NULL REFERENCES milavn_circle.poll(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (option_id, member_id)
);
CREATE INDEX IF NOT EXISTS idx_poll_vote_poll ON milavn_circle.poll_vote (poll_id);

-- Everything here is circle-scoped: you see a poll if you are in its circle, and you write only
-- your own vote. The same `is_active_member` helper every other circle rule already uses.
ALTER TABLE milavn_circle.poll ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS poll_circle_members ON milavn_circle.poll;
CREATE POLICY poll_circle_members ON milavn_circle.poll
  FOR SELECT USING (milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS poll_author_writes ON milavn_circle.poll;
CREATE POLICY poll_author_writes ON milavn_circle.poll
  FOR INSERT WITH CHECK (created_by_member_id = current_setting('milavn.member_id', true)::uuid
                         AND milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS poll_author_closes ON milavn_circle.poll;
CREATE POLICY poll_author_closes ON milavn_circle.poll
  FOR UPDATE USING (created_by_member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (created_by_member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, UPDATE ON milavn_circle.poll TO milavn_app;

ALTER TABLE milavn_circle.poll_option ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS poll_option_circle_members ON milavn_circle.poll_option;
CREATE POLICY poll_option_circle_members ON milavn_circle.poll_option
  FOR SELECT USING (EXISTS (SELECT 1 FROM milavn_circle.poll p WHERE p.id = poll_option.poll_id
                            AND milavn_circle.is_active_member(p.circle_id, current_setting('milavn.member_id', true)::uuid)));
DROP POLICY IF EXISTS poll_option_author_writes ON milavn_circle.poll_option;
CREATE POLICY poll_option_author_writes ON milavn_circle.poll_option
  FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM milavn_circle.poll p WHERE p.id = poll_option.poll_id
                                 AND p.created_by_member_id = current_setting('milavn.member_id', true)::uuid));
GRANT SELECT, INSERT ON milavn_circle.poll_option TO milavn_app;

ALTER TABLE milavn_circle.poll_vote ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS poll_vote_circle_members ON milavn_circle.poll_vote;
CREATE POLICY poll_vote_circle_members ON milavn_circle.poll_vote
  FOR SELECT USING (EXISTS (SELECT 1 FROM milavn_circle.poll p WHERE p.id = poll_vote.poll_id
                            AND milavn_circle.is_active_member(p.circle_id, current_setting('milavn.member_id', true)::uuid)));
DROP POLICY IF EXISTS poll_vote_own ON milavn_circle.poll_vote;
CREATE POLICY poll_vote_own ON milavn_circle.poll_vote
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid
              AND EXISTS (SELECT 1 FROM milavn_circle.poll p WHERE p.id = poll_vote.poll_id AND p.closed_at IS NULL
                          AND milavn_circle.is_active_member(p.circle_id, current_setting('milavn.member_id', true)::uuid)));
GRANT SELECT, INSERT, DELETE ON milavn_circle.poll_vote TO milavn_app;
