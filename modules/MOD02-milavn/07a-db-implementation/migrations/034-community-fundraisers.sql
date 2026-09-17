-- 034 — A drive for something the community needs (FR124).
--
-- WHY (2026-09-17, owner's pick 14): this is the one capability the Indian community products have
-- that none of the Western ones do. Mera Samaj's own case study is an admin collecting in a few
-- months what had taken twelve years by hand; Heylo builds recurring dues for clubs. A samaj
-- collects constantly — for a hall, a scholarship, a family in trouble, the annual function — and
-- today that happens in WhatsApp with a screenshot of a UPI payment and a hand-kept list.
--
--   fundraiser        one drive inside a circle: what it is for, how much is needed, by when
--   fundraiser_pledge what each person has promised — the amount is visible to the organizers
--                     and to the person themselves, never to the whole circle
--
-- MONEY DOES NOT MOVE HERE. The payment vendor is an external dependency the owner is handling
-- (blocker B1), so a pledge is a promise recorded in the app, and the drive shows what has been
-- promised versus what is needed. When Payment Services arrives, `paid_at`/`payment_reference` are
-- where a real payment attaches — the shape is ready and nothing else has to change.

CREATE TABLE IF NOT EXISTS milavn_circle.fundraiser (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  circle_id            uuid NOT NULL REFERENCES milavn_circle.circle(id) ON DELETE CASCADE,
  created_by_member_id uuid NOT NULL,
  title                text NOT NULL,
  purpose              text,
  target_paise         bigint,
  closes_on            date,
  created_at           timestamptz NOT NULL DEFAULT now(),
  closed_at            timestamptz,
  CONSTRAINT fundraiser_title_sane CHECK (length(title) BETWEEN 1 AND 120),
  CONSTRAINT fundraiser_target_sane CHECK (target_paise IS NULL OR target_paise BETWEEN 10000 AND 1000000000)
);
CREATE INDEX IF NOT EXISTS idx_fundraiser_circle ON milavn_circle.fundraiser (circle_id, created_at DESC);

CREATE TABLE IF NOT EXISTS milavn_circle.fundraiser_pledge (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fundraiser_id     uuid NOT NULL REFERENCES milavn_circle.fundraiser(id) ON DELETE CASCADE,
  member_id         uuid NOT NULL,
  amount_paise      bigint NOT NULL,
  note              text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  paid_at           timestamptz,           -- filled in when real payments exist (blocker B1)
  payment_reference text,
  CONSTRAINT pledge_amount_sane CHECK (amount_paise BETWEEN 10000 AND 100000000),
  CONSTRAINT pledge_note_short CHECK (note IS NULL OR length(note) <= 140)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pledge_one_per_member ON milavn_circle.fundraiser_pledge (fundraiser_id, member_id);

ALTER TABLE milavn_circle.fundraiser ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fundraiser_circle_members ON milavn_circle.fundraiser;
CREATE POLICY fundraiser_circle_members ON milavn_circle.fundraiser
  FOR SELECT USING (milavn_circle.is_active_member(circle_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS fundraiser_organizer_writes ON milavn_circle.fundraiser;
CREATE POLICY fundraiser_organizer_writes ON milavn_circle.fundraiser
  FOR INSERT WITH CHECK (created_by_member_id = current_setting('milavn.member_id', true)::uuid
                         AND milavn_circle.can_moderate_circle(circle_id, current_setting('milavn.member_id', true)::uuid));
DROP POLICY IF EXISTS fundraiser_organizer_closes ON milavn_circle.fundraiser;
CREATE POLICY fundraiser_organizer_closes ON milavn_circle.fundraiser
  FOR UPDATE USING (milavn_circle.can_moderate_circle(circle_id, current_setting('milavn.member_id', true)::uuid))
  WITH CHECK (milavn_circle.can_moderate_circle(circle_id, current_setting('milavn.member_id', true)::uuid));
GRANT SELECT, INSERT, UPDATE ON milavn_circle.fundraiser TO milavn_app;

-- A pledge is the member's own row. Organizers see the list through the definer below, because
-- who gave what is theirs to reconcile — but it is never readable by the whole circle.
ALTER TABLE milavn_circle.fundraiser_pledge ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS pledge_own ON milavn_circle.fundraiser_pledge;
CREATE POLICY pledge_own ON milavn_circle.fundraiser_pledge
  FOR ALL USING (member_id = current_setting('milavn.member_id', true)::uuid)
  WITH CHECK (member_id = current_setting('milavn.member_id', true)::uuid);
GRANT SELECT, INSERT, UPDATE, DELETE ON milavn_circle.fundraiser_pledge TO milavn_app;

-- What everyone in the circle may see: the totals, never the individual amounts.
CREATE OR REPLACE FUNCTION milavn_circle.fundraiser_totals(p_fundraiser_id uuid)
RETURNS TABLE (promised_paise bigint, people integer, paid_paise bigint)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT coalesce(sum(p.amount_paise), 0)::bigint,
         count(*)::integer,
         coalesce(sum(p.amount_paise) FILTER (WHERE p.paid_at IS NOT NULL), 0)::bigint
  FROM milavn_circle.fundraiser_pledge p
  JOIN milavn_circle.fundraiser f ON f.id = p.fundraiser_id
  WHERE p.fundraiser_id = p_fundraiser_id
    AND milavn_circle.is_active_member(f.circle_id, current_setting('milavn.member_id', true)::uuid);
$$;

-- The organizer's reconciliation list: who promised what, so they can tick it off as it arrives.
CREATE OR REPLACE FUNCTION milavn_circle.fundraiser_pledges(p_fundraiser_id uuid, p_viewer uuid)
RETURNS TABLE (member_id uuid, amount_paise bigint, note text, created_at timestamptz, paid_at timestamptz)
LANGUAGE sql SECURITY DEFINER STABLE
SET search_path = milavn_circle, pg_catalog AS $$
  SELECT p.member_id, p.amount_paise, p.note, p.created_at, p.paid_at
  FROM milavn_circle.fundraiser_pledge p
  JOIN milavn_circle.fundraiser f ON f.id = p.fundraiser_id
  WHERE p.fundraiser_id = p_fundraiser_id
    AND p_viewer = current_setting('milavn.member_id', true)::uuid
    AND milavn_circle.can_moderate_circle(f.circle_id, p_viewer)
  ORDER BY p.created_at;
$$;

GRANT EXECUTE ON FUNCTION milavn_circle.fundraiser_totals(uuid) TO milavn_app;
GRANT EXECUTE ON FUNCTION milavn_circle.fundraiser_pledges(uuid, uuid) TO milavn_app;
