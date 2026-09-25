-- =============================================================================
-- 052 — Assisted matching: a named relationship manager (DEC-V1-032)
--
-- WHY (2026-09-22): BharatMatrimony's Assisted Service gives a family a
-- dedicated relationship manager from their region who speaks their language,
-- shortlists and contacts prospects for them, and sets up calls and meetings.
-- It is a large revenue line for older and less tech-savvy families. Mangaly
-- keeps the person and drops the sales: the RM is a real, named person the
-- family can see and message; the RM never sells visibility and never touches
-- ranking (DEC-V1-002); everything the RM does for a member is written down
-- where the member and their Home Circle can read it — the same transparency
-- the circle itself has.
--
-- Tables (all in `mangaly_operations`, since an RM is operations staff):
--   relationship_manager  who the RMs are (name, languages, region, photo).
--                         NOTE: another stream is building a general
--                         `mangaly_operations.operator` table (migration 048,
--                         roles text[]); this table is to be merged into it
--                         later (backlog). It is kept separate now so the two
--                         streams do not clash.
--   rm_assignment         one RM helping one member (the candidate); at most
--                         one active assignment per member.
--   rm_suggestion         a profile the RM put forward, with a note in the
--                         member's language, and the member's decision.
--   rm_interaction        the log the family reads: a call scheduled, a
--                         meeting held, a note.
--
-- RLS: the member and their circle (`family_info` on the member) read the
-- assignment, suggestions and interactions; the RM reads and writes their own
-- assignments under `mangaly.operator_role = 'relationship_manager'`.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE TABLE IF NOT EXISTS mangaly_operations.relationship_manager (
  account_id    uuid PRIMARY KEY,          -- cross-schema ref to mangaly_identity.account, no FK
  display_name  text NOT NULL,
  languages     text[] NOT NULL DEFAULT '{}',
  region        text,
  photo_ref     text,
  active        boolean NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_operations.relationship_manager IS
  '[DEC-V1-032] A named relationship manager. To be merged into mangaly_operations.operator (migration 048 stream) later.';

CREATE TABLE IF NOT EXISTS mangaly_operations.rm_assignment (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rm_account_id      uuid NOT NULL REFERENCES mangaly_operations.relationship_manager(account_id),
  member_account_id  uuid NOT NULL,        -- the candidate being helped
  status             text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ended')),
  assigned_at        timestamptz NOT NULL DEFAULT now(),
  ended_at           timestamptz,
  note               text
);
CREATE UNIQUE INDEX IF NOT EXISTS rm_assignment_one_active_per_member
  ON mangaly_operations.rm_assignment (member_account_id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_rm_assignment_rm
  ON mangaly_operations.rm_assignment (rm_account_id, status);

CREATE TABLE IF NOT EXISTS mangaly_operations.rm_suggestion (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  assignment_id         uuid NOT NULL REFERENCES mangaly_operations.rm_assignment(id) ON DELETE CASCADE,
  suggested_account_id  uuid NOT NULL,
  note                  text,
  created_at            timestamptz NOT NULL DEFAULT now(),
  member_decision       text CHECK (member_decision IS NULL OR member_decision IN ('liked', 'passed')),
  decided_at            timestamptz,
  UNIQUE (assignment_id, suggested_account_id)
);
CREATE INDEX IF NOT EXISTS idx_rm_suggestion_assignment
  ON mangaly_operations.rm_suggestion (assignment_id, created_at DESC);

CREATE TABLE IF NOT EXISTS mangaly_operations.rm_interaction (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  assignment_id  uuid NOT NULL REFERENCES mangaly_operations.rm_assignment(id) ON DELETE CASCADE,
  kind           text NOT NULL CHECK (kind IN ('call', 'meeting', 'note')),
  scheduled_at   timestamptz,
  summary        text,
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_rm_interaction_assignment
  ON mangaly_operations.rm_interaction (assignment_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- Helpers (SECURITY DEFINER, held to migration 010's rules: a signed-in
-- caller, answers derived from rows, never contact details).
-- ---------------------------------------------------------------------------

-- Is the signed-in account an active relationship manager, acting as one?
CREATE OR REPLACE FUNCTION mangaly_operations.is_rm()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_operations.relationship_manager r
         WHERE r.active
           AND r.account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid)
       AND current_setting('mangaly.operator_role', true) = 'relationship_manager';
$$;
REVOKE ALL ON FUNCTION mangaly_operations.is_rm() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.is_rm() TO mangaly_app;

-- The active RM of a member, or NULL. No caller check: it answers an id only,
-- and is what `can_direct` and the chat roster use.
CREATE OR REPLACE FUNCTION mangaly_operations.rm_of(p_member uuid)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT a.rm_account_id FROM mangaly_operations.rm_assignment a
     WHERE a.member_account_id = p_member AND a.status = 'active'
     LIMIT 1;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.rm_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.rm_of(uuid) TO mangaly_app;

-- May the signed-in account read this assignment? The member, their circle
-- (`family_info`, bound by authz.resolve()), or the RM it belongs to.
CREATE OR REPLACE FUNCTION mangaly_operations.rm_assignment_visible(p_assignment_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_authz, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_operations.rm_assignment a
         WHERE a.id = p_assignment_id
           AND (mangaly_authz.is_self(a.member_account_id)
                OR mangaly_authz.has_scope(a.member_account_id, 'family_info')
                OR (mangaly_operations.is_rm()
                    AND a.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid)));
$$;
REVOKE ALL ON FUNCTION mangaly_operations.rm_assignment_visible(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.rm_assignment_visible(uuid) TO mangaly_app;

-- Is the signed-in account the RM of this assignment (acting as an RM)?
CREATE OR REPLACE FUNCTION mangaly_operations.rm_owns_assignment(p_assignment_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT mangaly_operations.is_rm() AND EXISTS (
        SELECT 1 FROM mangaly_operations.rm_assignment a
         WHERE a.id = p_assignment_id
           AND a.status = 'active'
           AND a.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
$$;
REVOKE ALL ON FUNCTION mangaly_operations.rm_owns_assignment(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.rm_owns_assignment(uuid) TO mangaly_app;

-- Row visibility.
ALTER TABLE mangaly_operations.relationship_manager ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS relationship_manager_signed_in ON mangaly_operations.relationship_manager;
-- Name, languages and region of an RM are what a member is shown when one is
-- assigned; the row carries no contact detail. Writes happen only through
-- operations (seed / future console), never through the app role.
CREATE POLICY relationship_manager_signed_in ON mangaly_operations.relationship_manager
  FOR SELECT USING (NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL);

ALTER TABLE mangaly_operations.rm_assignment ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS rm_assignment_member_circle_or_rm ON mangaly_operations.rm_assignment;
CREATE POLICY rm_assignment_member_circle_or_rm ON mangaly_operations.rm_assignment
  USING (mangaly_authz.is_self(member_account_id)
         OR mangaly_authz.has_scope(member_account_id, 'family_info')
         OR (mangaly_operations.is_rm()
             AND rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid))
  WITH CHECK (mangaly_operations.is_rm()
              AND rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);

ALTER TABLE mangaly_operations.rm_suggestion ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS rm_suggestion_read ON mangaly_operations.rm_suggestion;
CREATE POLICY rm_suggestion_read ON mangaly_operations.rm_suggestion
  FOR SELECT USING (mangaly_operations.rm_assignment_visible(assignment_id));
DROP POLICY IF EXISTS rm_suggestion_rm_writes ON mangaly_operations.rm_suggestion;
CREATE POLICY rm_suggestion_rm_writes ON mangaly_operations.rm_suggestion
  FOR INSERT WITH CHECK (mangaly_operations.rm_owns_assignment(assignment_id));
-- The member (or a parent acting for them) records the decision; the RM may
-- not decide for them. Only the decision columns are touched by the API.
DROP POLICY IF EXISTS rm_suggestion_member_decides ON mangaly_operations.rm_suggestion;
CREATE POLICY rm_suggestion_member_decides ON mangaly_operations.rm_suggestion
  FOR UPDATE USING (mangaly_operations.rm_assignment_visible(assignment_id)
                    AND NOT mangaly_operations.is_rm())
  WITH CHECK (mangaly_operations.rm_assignment_visible(assignment_id));

ALTER TABLE mangaly_operations.rm_interaction ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS rm_interaction_read ON mangaly_operations.rm_interaction;
CREATE POLICY rm_interaction_read ON mangaly_operations.rm_interaction
  FOR SELECT USING (mangaly_operations.rm_assignment_visible(assignment_id));
DROP POLICY IF EXISTS rm_interaction_rm_writes ON mangaly_operations.rm_interaction;
CREATE POLICY rm_interaction_rm_writes ON mangaly_operations.rm_interaction
  FOR INSERT WITH CHECK (mangaly_operations.rm_owns_assignment(assignment_id));

GRANT USAGE ON SCHEMA mangaly_operations TO mangaly_app;
GRANT SELECT ON mangaly_operations.relationship_manager TO mangaly_app;
GRANT SELECT, INSERT, UPDATE ON mangaly_operations.rm_assignment TO mangaly_app;
GRANT SELECT, INSERT, UPDATE ON mangaly_operations.rm_suggestion TO mangaly_app;
GRANT SELECT, INSERT ON mangaly_operations.rm_interaction TO mangaly_app;

-- ---------------------------------------------------------------------------
-- What an RM may read about the member they help: the fields needed to search
-- well for them — never a phone, email or address. RLS on the profile keeps
-- the RM out of the profile rows themselves; this narrow read is the whole
-- window, and it opens only for the member's own active RM.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_operations.rm_member_summary(p_member uuid)
RETURNS TABLE (
    name text,
    age integer,
    city text,
    gender text,
    looking_for text,
    mother_tongue text,
    education_level text,
    profession text,
    partner_preference jsonb,
    family_involvement jsonb,
    language_preference text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, mangaly_discovery, pg_temp
AS $$
    SELECT p.name,
           date_part('year', age(current_date, p.date_of_birth))::integer,
           p.city_locality,
           p.gender,
           d.looking_for,
           d.mother_tongue,
           d.education_level,
           d.profession,
           (SELECT jsonb_object_agg(pa.attribute_key, pa.value)
              FROM mangaly_profile.profile_attribute pa
             WHERE pa.profile_id = p.id AND pa.category = 'partner_preference'
               AND pa.state = 'value' AND pa.value IS NOT NULL),
           (SELECT jsonb_object_agg(pa.attribute_key, pa.value)
              FROM mangaly_profile.profile_attribute pa
             WHERE pa.profile_id = p.id AND pa.category = 'family_involvement_expectations'
               AND pa.state = 'value' AND pa.value IS NOT NULL),
           p.language_preference
      FROM mangaly_profile.profile p
      LEFT JOIN mangaly_discovery.discovery_profile_index d ON d.profile_id = p.account_id
     WHERE p.account_id = p_member
       AND mangaly_operations.is_rm()
       AND EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a
                    WHERE a.member_account_id = p_member AND a.status = 'active'
                      AND a.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
$$;
REVOKE ALL ON FUNCTION mangaly_operations.rm_member_summary(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.rm_member_summary(uuid) TO mangaly_app;

-- The member's Home Circle as the RM sees it: who is helping, and how they are
-- related — so the RM knows whom to call. Names only.
CREATE OR REPLACE FUNCTION mangaly_operations.rm_member_family(p_member uuid)
RETURNS TABLE (member_account_id uuid, display_name text, relationship_type text, relation text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_home_circle, mangaly_identity, pg_temp
AS $$
    SELECT m.member_account_id, a.display_name, m.relationship_type::text, m.relation
      FROM mangaly_home_circle.membership m
      LEFT JOIN mangaly_identity.account a ON a.id = m.member_account_id
     WHERE m.candidate_profile_id = p_member
       AND m.status = 'active'
       AND mangaly_operations.is_rm()
       AND EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment x
                    WHERE x.member_account_id = p_member AND x.status = 'active'
                      AND x.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid)
     ORDER BY m.joined_at;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.rm_member_family(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.rm_member_family(uuid) TO mangaly_app;

-- The names of members an RM helps (the console's list), and of a member's
-- RM for the member's own screen. Display names only.
CREATE OR REPLACE FUNCTION mangaly_operations.rm_people_names(p_ids uuid[])
RETURNS TABLE (account_id uuid, display_name text, photo_ref text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_identity, mangaly_profile, pg_temp
AS $$
    SELECT a.id,
           COALESCE(p.name, a.display_name),
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1)
      FROM mangaly_identity.account a
      LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id
     WHERE a.id = ANY (p_ids)
       AND (
            -- the RM asks about the members they help
            (mangaly_operations.is_rm() AND EXISTS (
                SELECT 1 FROM mangaly_operations.rm_assignment x
                 WHERE x.member_account_id = a.id
                   AND x.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid))
            -- or anyone asks about an RM
            OR EXISTS (SELECT 1 FROM mangaly_operations.relationship_manager r WHERE r.account_id = a.id));
$$;
REVOKE ALL ON FUNCTION mangaly_operations.rm_people_names(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.rm_people_names(uuid[]) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Chat. The RM and the member — and the member's parents or guardian in their
-- circle — may message each other directly (DEC-V1-026's `direct` kind).
-- `can_direct` from 046 is re-created with its body intact plus the RM link;
-- `direct_contacts` gains the RM rows; the roster names the RM's role.
-- ---------------------------------------------------------------------------

-- The people an RM link joins: the member, and the parents/guardian in the
-- member's active circle.
CREATE OR REPLACE FUNCTION mangaly_operations.rm_linked(p_a uuid, p_b uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_home_circle, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_operations.rm_assignment ra
         WHERE ra.status = 'active'
           AND (
                (ra.rm_account_id = p_a AND (ra.member_account_id = p_b OR EXISTS (
                    SELECT 1 FROM mangaly_home_circle.membership m
                     WHERE m.candidate_profile_id = ra.member_account_id AND m.status = 'active'
                       AND m.member_account_id = p_b
                       AND m.relationship_type::text IN ('parent', 'guardian'))))
             OR (ra.rm_account_id = p_b AND (ra.member_account_id = p_a OR EXISTS (
                    SELECT 1 FROM mangaly_home_circle.membership m
                     WHERE m.candidate_profile_id = ra.member_account_id AND m.status = 'active'
                       AND m.member_account_id = p_a
                       AND m.relationship_type::text IN ('parent', 'guardian'))))));
$$;
REVOKE ALL ON FUNCTION mangaly_operations.rm_linked(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.rm_linked(uuid, uuid) TO mangaly_app;

-- May the signed-in account message p_other directly? (046's body, plus the
-- RM link as a third kind of real link between two people.)
CREATE OR REPLACE FUNCTION mangaly_communication.can_direct(p_other uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_safety, mangaly_operations, pg_temp
AS $$
    WITH me AS (SELECT NULLIF(current_setting('mangaly.account_id', true), '')::uuid AS id)
    SELECT COALESCE((
      SELECT me.id IS NOT NULL
         AND p_other IS NOT NULL
         AND p_other <> me.id
         AND NOT mangaly_safety.is_blocked_between(me.id, p_other)
         -- the two connected candidates talk only in their incognito session
         AND NOT EXISTS (
               SELECT 1 FROM mangaly_connection.connection_request cr
                WHERE cr.status = 'accepted'
                  AND ((cr.subject_account_id = me.id AND cr.target_profile_id = p_other)
                    OR (cr.subject_account_id = p_other AND cr.target_profile_id = me.id)))
         AND (
               -- the same family
               EXISTS (SELECT 1 FROM mangaly_communication.sides_of(me.id) a
                         JOIN mangaly_communication.sides_of(p_other) b
                           ON a.candidate_account_id = b.candidate_account_id)
               -- the two families of an accepted connection
            OR EXISTS (
               SELECT 1 FROM mangaly_connection.connection_request cr
                WHERE cr.status = 'accepted'
                  AND ((cr.subject_account_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(me.id))
                        AND cr.target_profile_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(p_other)))
                    OR (cr.target_profile_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(me.id))
                        AND cr.subject_account_id IN (SELECT candidate_account_id FROM mangaly_communication.sides_of(p_other)))))
               -- [052] a relationship manager and the family they help
            OR mangaly_operations.rm_linked(me.id, p_other)
         )
      FROM me), false);
$$;
REVOKE ALL ON FUNCTION mangaly_communication.can_direct(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.can_direct(uuid) TO mangaly_app;

-- The "New message" list: 046's rows, plus the RM link. For a member or a
-- parent, their RM appears as role 'relationship_manager' on the member's
-- own side (`mine` = true, `side` = the member). For the RM, each family they
-- help is a side of its own (`mine` = false, `side_name` = the member).
CREATE OR REPLACE FUNCTION mangaly_communication.direct_contacts()
RETURNS TABLE (
    account_id uuid,
    display_name text,
    photo_ref text,
    role text,
    relation text,
    side_account_id uuid,
    side_name text,
    mine boolean
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_home_circle, mangaly_profile, mangaly_identity, mangaly_operations, pg_temp
AS $$
    WITH me AS (SELECT NULLIF(current_setting('mangaly.account_id', true), '')::uuid AS id),
    my_sides AS (SELECT s.candidate_account_id FROM me, mangaly_communication.sides_of(me.id) s),
    their_sides AS (
        SELECT CASE WHEN cr.subject_account_id IN (SELECT candidate_account_id FROM my_sides)
                    THEN cr.target_profile_id ELSE cr.subject_account_id END AS candidate_account_id
          FROM mangaly_connection.connection_request cr
         WHERE cr.status = 'accepted'
           AND (cr.subject_account_id IN (SELECT candidate_account_id FROM my_sides)
             OR cr.target_profile_id IN (SELECT candidate_account_id FROM my_sides))),
    sides AS (
        SELECT candidate_account_id, true AS mine FROM my_sides
        UNION
        SELECT candidate_account_id, false FROM their_sides
         WHERE candidate_account_id NOT IN (SELECT candidate_account_id FROM my_sides)),
    people AS (
        SELECT s.candidate_account_id AS account_id, 'candidate'::text AS role, NULL::text AS relation,
               s.candidate_account_id AS side_account_id, s.mine
          FROM sides s
         WHERE EXISTS (SELECT 1 FROM mangaly_profile.profile p WHERE p.account_id = s.candidate_account_id)
        UNION ALL
        SELECT m.member_account_id, m.relationship_type::text, m.relation, m.candidate_profile_id, s.mine
          FROM sides s
          JOIN mangaly_home_circle.membership m
            ON m.candidate_profile_id = s.candidate_account_id AND m.status = 'active'
        UNION ALL
        -- [052] my RM (I am the member, or a parent/guardian in their circle)
        SELECT ra.rm_account_id, 'relationship_manager'::text, NULL::text, ra.member_account_id, true
          FROM me, mangaly_operations.rm_assignment ra
         WHERE ra.status = 'active'
           AND (ra.member_account_id = me.id OR EXISTS (
                SELECT 1 FROM mangaly_home_circle.membership m
                 WHERE m.candidate_profile_id = ra.member_account_id AND m.status = 'active'
                   AND m.member_account_id = me.id
                   AND m.relationship_type::text IN ('parent', 'guardian')))
        UNION ALL
        -- [052] I am the RM: each member I help, and their parents/guardian
        SELECT ra.member_account_id, 'candidate'::text, NULL::text, ra.member_account_id, false
          FROM me, mangaly_operations.rm_assignment ra
         WHERE ra.status = 'active' AND ra.rm_account_id = me.id
        UNION ALL
        SELECT m.member_account_id, m.relationship_type::text, m.relation, ra.member_account_id, false
          FROM me, mangaly_operations.rm_assignment ra
          JOIN mangaly_home_circle.membership m
            ON m.candidate_profile_id = ra.member_account_id AND m.status = 'active'
           AND m.relationship_type::text IN ('parent', 'guardian')
         WHERE ra.status = 'active' AND ra.rm_account_id = me.id)
    SELECT DISTINCT ON (pp.account_id)
           pp.account_id,
           COALESCE(rm.display_name, pr.name, a.display_name),
           COALESCE(rm.photo_ref,
             (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
               WHERE pm.profile_id = pr.id AND pm.is_primary
                 AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1)),
           pp.role, pp.relation, pp.side_account_id,
           COALESCE(sp.name, sa.display_name),
           pp.mine
      FROM people pp CROSS JOIN me
      LEFT JOIN mangaly_profile.profile pr ON pr.account_id = pp.account_id
      LEFT JOIN mangaly_identity.account a ON a.id = pp.account_id
      LEFT JOIN mangaly_operations.relationship_manager rm
        ON rm.account_id = pp.account_id AND pp.role = 'relationship_manager'
      LEFT JOIN mangaly_profile.profile sp ON sp.account_id = pp.side_account_id
      LEFT JOIN mangaly_identity.account sa ON sa.id = pp.side_account_id
     WHERE pp.account_id <> me.id
       AND mangaly_communication.can_direct(pp.account_id)
     ORDER BY pp.account_id, (pp.role = 'relationship_manager') DESC, pp.mine DESC;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.direct_contacts() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.direct_contacts() TO mangaly_app;

-- The thread roster (046) names an RM by their role rather than as a
-- candidate or relative: "Asha · relationship manager of Varun".
DROP FUNCTION IF EXISTS mangaly_communication.conversation_people(uuid);
CREATE FUNCTION mangaly_communication.conversation_people(p_conversation_id uuid)
RETURNS TABLE (
    account_id uuid,
    display_name text,
    role text,
    photo_ref text,
    last_read_at timestamptz,
    relation text,
    side_account_id uuid,
    side_name text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_communication, mangaly_connection, mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_authz, mangaly_operations, pg_temp
AS $$
    SELECT cp.account_id,
           COALESCE(rmx.display_name, p.name, a.display_name),
           CASE WHEN rmx.member_account_id IS NOT NULL THEN 'relationship_manager'
                WHEN cr.id IS NOT NULL AND cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN 'candidate'
                WHEN mm.relationship_type IS NOT NULL THEN mm.relationship_type::text
                WHEN p.id IS NOT NULL THEN 'candidate'
                ELSE 'relative' END,
           COALESCE(rmx.photo_ref,
             (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
               WHERE pm.profile_id = p.id AND pm.is_primary
                 AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1)),
           cp.last_read_at,
           CASE WHEN rmx.member_account_id IS NOT NULL THEN NULL
                WHEN cr.id IS NOT NULL AND cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN NULL
                ELSE mm.relation END,
           CASE WHEN rmx.member_account_id IS NOT NULL THEN rmx.member_account_id
                WHEN cr.id IS NOT NULL AND cp.account_id IN (cr.subject_account_id, cr.target_profile_id) THEN cp.account_id
                WHEN mm.candidate_profile_id IS NOT NULL THEN mm.candidate_profile_id
                ELSE cp.account_id END,
           COALESCE(rsp.name, rsa.display_name, sp.name, sa.display_name)
      FROM mangaly_communication.conversation_participant cp
      JOIN mangaly_communication.conversation cv ON cv.id = cp.conversation_id
      LEFT JOIN mangaly_connection.connection_request cr ON cr.id = cv.connection_id
      LEFT JOIN mangaly_profile.profile p ON p.account_id = cp.account_id
      LEFT JOIN mangaly_identity.account a ON a.id = cp.account_id
      LEFT JOIN LATERAL (
            SELECT m.relationship_type, m.relation, m.candidate_profile_id
              FROM mangaly_home_circle.membership m
             WHERE m.member_account_id = cp.account_id
               AND m.status = 'active'
               AND (cr.id IS NULL OR m.candidate_profile_id IN (cr.subject_account_id, cr.target_profile_id))
             ORDER BY m.joined_at LIMIT 1) mm ON true
      -- [052] this participant is the active RM of another participant's side
      LEFT JOIN LATERAL (
            SELECT r.display_name, r.photo_ref, ra.member_account_id
              FROM mangaly_operations.relationship_manager r
              JOIN mangaly_operations.rm_assignment ra
                ON ra.rm_account_id = r.account_id AND ra.status = 'active'
             WHERE r.account_id = cp.account_id
               AND cv.kind = 'direct'
               AND EXISTS (
                    SELECT 1 FROM mangaly_communication.conversation_participant o
                     WHERE o.conversation_id = cv.id AND o.account_id <> cp.account_id
                       AND mangaly_operations.rm_linked(cp.account_id, o.account_id)
                       AND (o.account_id = ra.member_account_id OR EXISTS (
                            SELECT 1 FROM mangaly_home_circle.membership m2
                             WHERE m2.candidate_profile_id = ra.member_account_id AND m2.status = 'active'
                               AND m2.member_account_id = o.account_id)))
             ORDER BY ra.assigned_at DESC LIMIT 1) rmx ON true
      LEFT JOIN mangaly_profile.profile sp
        ON sp.account_id = COALESCE(mm.candidate_profile_id, cp.account_id)
      LEFT JOIN mangaly_identity.account sa
        ON sa.id = COALESCE(mm.candidate_profile_id, cp.account_id)
      LEFT JOIN mangaly_profile.profile rsp ON rsp.account_id = rmx.member_account_id
      LEFT JOIN mangaly_identity.account rsa ON rsa.id = rmx.member_account_id
     WHERE cp.conversation_id = p_conversation_id
       AND mangaly_communication.is_participant(p_conversation_id)
     ORDER BY cp.joined_at;
$$;
REVOKE ALL ON FUNCTION mangaly_communication.conversation_people(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_communication.conversation_people(uuid) TO mangaly_app;

-- An RM's photo is a member-style photo (047): visible to the people who may
-- message them. `member_photos` already answers through `can_direct`, which
-- now includes the RM link, so nothing more is needed for photos.
