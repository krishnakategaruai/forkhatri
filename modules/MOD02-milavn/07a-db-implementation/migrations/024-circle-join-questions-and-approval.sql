-- 024 — Joining a circle: a question or two, and the organizer's yes (FR115).
--
-- WHY (2026-09-17, owner's picks 2 and 3 from the competitor research): every product that runs
-- real communities screens who joins. Meetup lets an organizer ask up to five questions and hold
-- each request as "pending" until they accept; Luma has approval-required registration; Geneva and
-- Heylo both screen applicants before admission, and Heylo reports that admission friction is what
-- makes members trust the group. Milavn's circles were join-instantly, so a neighbourhood or
-- women-only circle had no way to ask "how do you know us?" before letting someone in.
--
--   circle.join_policy      'open' (unchanged default) or 'approval'
--   circle.join_questions   up to 3 short questions the organizer asks (no answer is ever required)
--   join_request            one pending request per person per circle, with their answers
--   request_to_join()       creates the request (or joins outright when the circle is open)
--   pending_join_requests() what the organizer sees — their own circle only
--   decide_join_request()   approve (creates the membership) or decline, once, by the organizer
--
-- The definers carry the role rules so the table's own policy can stay "your own rows only":
-- an organizer reading requests is a different question from a member reading their own.

ALTER TABLE milavn_circle.circle
  ADD COLUMN IF NOT EXISTS join_policy text NOT NULL DEFAULT 'open',
  ADD COLUMN IF NOT EXISTS join_questions text[] NOT NULL DEFAULT '{}';

DO $$ BEGIN
  ALTER TABLE milavn_circle.circle ADD CONSTRAINT circle_join_policy_known CHECK (join_policy IN ('open', 'approval'));
EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE milavn_circle.circle ADD CONSTRAINT circle_join_questions_few CHECK (cardinality(join_questions) <= 3);
EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS milavn_circle.join_request (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id            uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  member_id            uuid NOT NULL,
  answers              text[] NOT NULL DEFAULT '{}',
  status               text NOT NULL DEFAULT 'pending',
  created_at           timestamptz NOT NULL DEFAULT now(),
  decided_at           timestamptz,
  decided_by_member_id uuid,
  CONSTRAINT join_request_status_known CHECK (status IN ('pending', 'approved', 'declined', 'withdrawn'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_join_request_one_pending
  ON milavn_circle.join_request (circle_id, member_id) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_join_request_circle ON milavn_circle.join_request (circle_id, status);

ALTER TABLE milavn_circle.join_request ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS join_request_own ON milavn_circle.join_request;
CREATE POLICY join_request_own ON milavn_circle.join_request
  FOR SELECT USING (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT ON milavn_circle.join_request TO milavn_app;

-- Who may decide: the circle's creator, or a member carrying the organizer role.
CREATE OR REPLACE FUNCTION milavn_circle.is_circle_organizer(p_circle_id uuid, p_member_id uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM milavn_circle.circle c WHERE c.id = p_circle_id AND c.created_by_member_id = p_member_id)
      OR EXISTS (SELECT 1 FROM milavn_circle.circle_membership m
                 WHERE m.circle_id = p_circle_id AND m.member_id = p_member_id
                   AND m.left_at IS NULL AND m.member_role = 'organizer');
$$;

-- 'joined' | 'pending' | 'already_pending' | 'already_member' | NULL (no such circle)
CREATE OR REPLACE FUNCTION milavn_circle.request_to_join(p_circle_id uuid, p_member_id uuid, p_answers text[])
RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE policy text;
BEGIN
  IF p_member_id IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN NULL; END IF;
  SELECT c.join_policy INTO policy FROM milavn_circle.circle c WHERE c.id = p_circle_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  IF EXISTS (SELECT 1 FROM milavn_circle.circle_membership m
             WHERE m.circle_id = p_circle_id AND m.member_id = p_member_id AND m.left_at IS NULL) THEN
    RETURN 'already_member';
  END IF;
  IF policy <> 'approval' THEN
    INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
    VALUES (p_circle_id, p_member_id, 'member') ON CONFLICT DO NOTHING;
    RETURN 'joined';
  END IF;
  IF EXISTS (SELECT 1 FROM milavn_circle.join_request r
             WHERE r.circle_id = p_circle_id AND r.member_id = p_member_id AND r.status = 'pending') THEN
    RETURN 'already_pending';
  END IF;
  INSERT INTO milavn_circle.join_request (circle_id, member_id, answers)
  VALUES (p_circle_id, p_member_id, coalesce(p_answers, '{}'));
  RETURN 'pending';
END;
$$;

CREATE OR REPLACE FUNCTION milavn_circle.pending_join_requests(p_circle_id uuid, p_viewer uuid)
RETURNS TABLE (request_id uuid, member_id uuid, answers text[], created_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT r.id, r.member_id, r.answers, r.created_at
  FROM milavn_circle.join_request r
  WHERE r.circle_id = p_circle_id AND r.status = 'pending'
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND milavn_circle.is_circle_organizer(p_circle_id, p_viewer)
  ORDER BY r.created_at;
$$;

-- Returns the member the decision was about, so the caller can tell them. NULL when not allowed.
CREATE OR REPLACE FUNCTION milavn_circle.decide_join_request(p_request_id uuid, p_actor uuid, p_approve boolean)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_circle, pg_catalog AS $$
DECLARE r record;
BEGIN
  IF p_actor IS DISTINCT FROM current_setting('milavn.member_id', true)::uuid THEN RETURN NULL; END IF;
  SELECT jr.id, jr.circle_id, jr.member_id INTO r
  FROM milavn_circle.join_request jr WHERE jr.id = p_request_id AND jr.status = 'pending';
  IF NOT FOUND OR NOT milavn_circle.is_circle_organizer(r.circle_id, p_actor) THEN RETURN NULL; END IF;
  UPDATE milavn_circle.join_request
     SET status = CASE WHEN p_approve THEN 'approved' ELSE 'declined' END,
         decided_at = now(), decided_by_member_id = p_actor
   WHERE id = r.id;
  IF p_approve THEN
    INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
    VALUES (r.circle_id, r.member_id, 'member') ON CONFLICT DO NOTHING;
  END IF;
  RETURN r.member_id;
END;
$$;

-- What the member themselves sees: "waiting to be let in", so the button can say so.
CREATE OR REPLACE FUNCTION milavn_circle.my_join_request_status(p_circle_id uuid, p_member_id uuid)
RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT r.status FROM milavn_circle.join_request r
  WHERE r.circle_id = p_circle_id AND r.member_id = p_member_id
    AND p_member_id = current_setting('milavn.member_id', true)::uuid
  ORDER BY r.created_at DESC LIMIT 1;
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.is_circle_organizer(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.request_to_join(uuid, uuid, text[]) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.pending_join_requests(uuid, uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.decide_join_request(uuid, uuid, boolean) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.my_join_request_status(uuid, uuid) TO milavn_app;
