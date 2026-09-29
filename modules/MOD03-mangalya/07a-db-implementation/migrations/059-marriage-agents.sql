-- =============================================================================
-- 059 — Marriage agents: brokers and bureaus on Mangaly (DEC-V1-033)
--
-- WHY (product owner, 2026-09-29): "a person who will act as broker, without
-- app also he exists, so I don't want to kill his job rather I want to
-- enhance him giving best platform." In Indian communities a marriage agent
-- (bureau, mediator, pelli peddalu) holds many families' biodata and matches
-- them by hand. Mangaly gives that person a paid Agent membership with the
-- tools bureau software sells (research, 2026-09-29: bulk upload, biodata
-- PDF and Excel export, contact access, a per-client pipeline, a log of
-- calls and meetings) — without the abuse the big sites ban bureaus for
-- (data harvesting, fake bureaus): agents are checked by Mangaly before they
-- go live, every look at a phone number and every export is written down
-- where the family can read it, and a family can close their number to
-- agents.
--
-- HOW (reuse, not a second system): an agent IS a relationship manager of
-- kind 'agent' (migration 052). Their clients are rm_assignment rows, so the
-- client's own search, suggestions with a note, the call/meeting log, chat
-- with the family and the /rm workspace work unchanged. What is new:
--   relationship_manager   kind, business details, verification.
--   billing                the AGENT plan (the membership); is_rm() admits an
--                          agent only while verified AND the plan is active.
--   rm_assignment          rm_kind, stage (the pipeline), origin, consent.
--                          A family may have Mangaly's own RM and any number
--                          of agents, as in real life; one active row per
--                          (agent, family).
--   profile                agents_may_see_contact (default on, the family can
--                          turn it off).
--   agent_contact_view     every time an agent opens a number.
--   agent_export           every export an agent makes.
-- Idempotent: safe to re-run.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Who the agent is
-- ---------------------------------------------------------------------------
ALTER TABLE mangaly_operations.relationship_manager
    ADD COLUMN IF NOT EXISTS kind                text NOT NULL DEFAULT 'staff',
    ADD COLUMN IF NOT EXISTS business_name       text,
    ADD COLUMN IF NOT EXISTS business_phone      text,
    ADD COLUMN IF NOT EXISTS city                text,
    ADD COLUMN IF NOT EXISTS years_active        integer,
    ADD COLUMN IF NOT EXISTS communities         text[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS about               text,
    ADD COLUMN IF NOT EXISTS verification_status text NOT NULL DEFAULT 'verified',
    ADD COLUMN IF NOT EXISTS verified_at         timestamptz,
    ADD COLUMN IF NOT EXISTS applied_at          timestamptz;

DO $$ BEGIN
  ALTER TABLE mangaly_operations.relationship_manager
    ADD CONSTRAINT relationship_manager_kind_check CHECK (kind IN ('staff', 'agent'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE mangaly_operations.relationship_manager
    ADD CONSTRAINT relationship_manager_verification_check
    CHECK (verification_status IN ('pending', 'verified', 'rejected'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE mangaly_operations.relationship_manager
    ADD CONSTRAINT relationship_manager_years_check CHECK (years_active IS NULL OR years_active BETWEEN 0 AND 80);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

COMMENT ON COLUMN mangaly_operations.relationship_manager.kind IS
  '[DEC-V1-033] staff = Mangaly''s own relationship manager; agent = an independent marriage agent with an Agent membership.';

-- ---------------------------------------------------------------------------
-- The Agent membership is a plan like Gold, held by the agent's own account.
-- ---------------------------------------------------------------------------
DO $$
DECLARE c record;
BEGIN
  FOR c IN
    SELECT conrelid::regclass AS tbl, conname
      FROM pg_constraint
     WHERE conrelid IN ('mangaly_billing."order"'::regclass, 'mangaly_billing.plan_subscription'::regclass)
       AND contype = 'c'
       AND pg_get_constraintdef(oid) LIKE '%plan_code%'
  LOOP
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', c.tbl, c.conname);
  END LOOP;
END $$;
ALTER TABLE mangaly_billing."order"
  ADD CONSTRAINT order_plan_code_check CHECK (plan_code IN ('GOLD', 'ASSISTED', 'AGENT', 'AGENT_CONNECT'));
ALTER TABLE mangaly_billing.plan_subscription
  ADD CONSTRAINT plan_subscription_plan_code_check CHECK (plan_code IN ('GOLD', 'ASSISTED', 'AGENT', 'AGENT_CONNECT'));

CREATE OR REPLACE FUNCTION mangaly_operations.agent_membership_until(p_account uuid)
RETURNS timestamptz
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_billing, pg_temp
AS $$
    SELECT MAX(s.ends_at) FROM mangaly_billing.plan_subscription s
     WHERE s.account_id = p_account
       AND s.plan_code = 'AGENT'
       AND s.status = 'active'
       AND s.started_at <= now()
       AND s.ends_at > now();
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_membership_until(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_membership_until(uuid) TO mangaly_app;

-- May this account work as an RM or agent right now?
CREATE OR REPLACE FUNCTION mangaly_operations.can_work_as_rm(p_account uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_operations.relationship_manager r
         WHERE r.account_id = p_account
           AND r.active
           AND (r.kind = 'staff'
                OR (r.verification_status = 'verified'
                    AND mangaly_operations.agent_membership_until(r.account_id) IS NOT NULL)));
$$;
REVOKE ALL ON FUNCTION mangaly_operations.can_work_as_rm(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.can_work_as_rm(uuid) TO mangaly_app;

-- 052's is_rm(), now also requiring a live membership for an agent.
CREATE OR REPLACE FUNCTION mangaly_operations.is_rm()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT mangaly_operations.can_work_as_rm(NULLIF(current_setting('mangaly.account_id', true), '')::uuid)
       AND current_setting('mangaly.operator_role', true) = 'relationship_manager';
$$;
REVOKE ALL ON FUNCTION mangaly_operations.is_rm() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.is_rm() TO mangaly_app;

-- Is the signed-in account, acting as an RM, an agent (not Mangaly staff)?
CREATE OR REPLACE FUNCTION mangaly_operations.is_agent()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT mangaly_operations.is_rm() AND EXISTS (
        SELECT 1 FROM mangaly_operations.relationship_manager r
         WHERE r.account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
           AND r.kind = 'agent');
$$;
REVOKE ALL ON FUNCTION mangaly_operations.is_agent() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.is_agent() TO mangaly_app;

-- A signed-in member applies to be an agent, or updates their details while
-- they wait or after they are verified. Mangaly staff rows are never touched.
CREATE OR REPLACE FUNCTION mangaly_operations.apply_as_agent(
    p_display_name   text,
    p_business_name  text,
    p_business_phone text,
    p_city           text,
    p_languages      text[],
    p_communities    text[],
    p_years_active   integer,
    p_about          text
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
DECLARE
    v_me   uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_kind text;
    v_status text;
BEGIN
    IF v_me IS NULL THEN
        RAISE EXCEPTION 'apply_as_agent: sign in first' USING ERRCODE = 'insufficient_privilege';
    END IF;
    SELECT kind, verification_status INTO v_kind, v_status
      FROM mangaly_operations.relationship_manager WHERE account_id = v_me;
    IF v_kind = 'staff' THEN
        RAISE EXCEPTION 'apply_as_agent: already Mangaly staff' USING ERRCODE = 'MGL09';
    END IF;
    IF v_kind IS NULL THEN
        INSERT INTO mangaly_operations.relationship_manager
            (account_id, display_name, languages, region, kind, business_name, business_phone,
             city, years_active, communities, about, verification_status, applied_at, active)
        VALUES
            (v_me, p_display_name, COALESCE(p_languages, '{}'), p_city, 'agent', p_business_name,
             p_business_phone, p_city, p_years_active, COALESCE(p_communities, '{}'), p_about,
             'pending', now(), true);
        RETURN 'pending';
    END IF;
    UPDATE mangaly_operations.relationship_manager
       SET display_name = p_display_name,
           languages = COALESCE(p_languages, '{}'),
           region = p_city,
           business_name = p_business_name,
           business_phone = p_business_phone,
           city = p_city,
           years_active = p_years_active,
           communities = COALESCE(p_communities, '{}'),
           about = p_about,
           -- a rejected applicant who corrects their details asks again
           verification_status = CASE WHEN verification_status = 'rejected' THEN 'pending' ELSE verification_status END,
           applied_at = CASE WHEN verification_status = 'rejected' THEN now() ELSE applied_at END
     WHERE account_id = v_me;
    RETURN (SELECT verification_status FROM mangaly_operations.relationship_manager WHERE account_id = v_me);
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.apply_as_agent(text, text, text, text, text[], text[], integer, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.apply_as_agent(text, text, text, text, text[], text[], integer, text) TO mangaly_app;

-- A Mangaly moderator checks an application ('operations' operator role).
CREATE OR REPLACE FUNCTION mangaly_operations.review_agent(p_account uuid, p_status text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
BEGIN
    IF current_setting('mangaly.operator_role', true) IS DISTINCT FROM 'operations' THEN
        RAISE EXCEPTION 'review_agent: operators only' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF p_status NOT IN ('verified', 'rejected') THEN
        RAISE EXCEPTION 'review_agent: bad status' USING ERRCODE = 'invalid_parameter_value';
    END IF;
    UPDATE mangaly_operations.relationship_manager
       SET verification_status = p_status,
           verified_at = CASE WHEN p_status = 'verified' THEN now() ELSE NULL END
     WHERE account_id = p_account AND kind = 'agent';
    RETURN FOUND;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.review_agent(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.review_agent(uuid, text) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- The client pipeline
-- ---------------------------------------------------------------------------
ALTER TABLE mangaly_operations.rm_assignment
    ADD COLUMN IF NOT EXISTS rm_kind             text NOT NULL DEFAULT 'staff',
    ADD COLUMN IF NOT EXISTS stage               text NOT NULL DEFAULT 'searching',
    ADD COLUMN IF NOT EXISTS stage_changed_at    timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS origin              text NOT NULL DEFAULT 'assigned',
    ADD COLUMN IF NOT EXISTS consent_recorded_at timestamptz;

DO $$ BEGIN
  ALTER TABLE mangaly_operations.rm_assignment
    ADD CONSTRAINT rm_assignment_rm_kind_check CHECK (rm_kind IN ('staff', 'agent'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE mangaly_operations.rm_assignment
    ADD CONSTRAINT rm_assignment_stage_check
    CHECK (stage IN ('searching', 'proposal_sent', 'meeting', 'engaged', 'married', 'paused'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE mangaly_operations.rm_assignment
    ADD CONSTRAINT rm_assignment_origin_check
    CHECK (origin IN ('assigned', 'added_by_agent', 'family_chose'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- One Mangaly RM per family; any number of agents, one row per agent.
DROP INDEX IF EXISTS mangaly_operations.rm_assignment_one_active_per_member;
CREATE UNIQUE INDEX IF NOT EXISTS rm_assignment_one_active_staff_per_member
  ON mangaly_operations.rm_assignment (member_account_id) WHERE status = 'active' AND rm_kind = 'staff';
CREATE UNIQUE INDEX IF NOT EXISTS rm_assignment_one_active_per_rm_and_member
  ON mangaly_operations.rm_assignment (rm_account_id, member_account_id) WHERE status = 'active';

-- Who may start a client row, and what may never change on one. An agent's
-- client is either a profile the agent made (origin 'added_by_agent') or a
-- family that chose the agent (`choose_agent`, run by the family). An agent
-- can never make someone their client by writing the row themselves — that
-- would open the family's numbers without the family's say.
CREATE OR REPLACE FUNCTION mangaly_operations.rm_assignment_guard()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, pg_temp
AS $$
DECLARE
    v_me   uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_kind text;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.rm_account_id IS DISTINCT FROM OLD.rm_account_id
           OR NEW.member_account_id IS DISTINCT FROM OLD.member_account_id
           OR NEW.rm_kind IS DISTINCT FROM OLD.rm_kind
           OR NEW.origin IS DISTINCT FROM OLD.origin THEN
            RAISE EXCEPTION 'rm_assignment: who a client row joins never changes' USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN NEW;
    END IF;
    SELECT kind INTO v_kind FROM mangaly_operations.relationship_manager WHERE account_id = NEW.rm_account_id;
    NEW.rm_kind := COALESCE(v_kind, 'staff');
    IF NEW.rm_kind = 'agent' THEN
        IF v_me = NEW.rm_account_id THEN
            IF NEW.origin <> 'added_by_agent' OR NOT EXISTS (
                 SELECT 1 FROM mangaly_profile.profile p
                  WHERE p.account_id = NEW.member_account_id AND p.created_by_account_id = NEW.rm_account_id) THEN
                RAISE EXCEPTION 'rm_assignment: an agent''s client is a profile they made or a family that chose them'
                    USING ERRCODE = 'insufficient_privilege';
            END IF;
            NEW.consent_recorded_at := COALESCE(NEW.consent_recorded_at, now());
        ELSIF NEW.origin <> 'family_chose' THEN
            RAISE EXCEPTION 'rm_assignment: bad origin for an agent' USING ERRCODE = 'insufficient_privilege';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS rm_assignment_guard ON mangaly_operations.rm_assignment;
CREATE TRIGGER rm_assignment_guard
  BEFORE INSERT OR UPDATE ON mangaly_operations.rm_assignment
  FOR EACH ROW EXECUTE FUNCTION mangaly_operations.rm_assignment_guard();

-- The member's own Mangaly RM (052 answered any active row).
CREATE OR REPLACE FUNCTION mangaly_operations.rm_of(p_member uuid)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT a.rm_account_id FROM mangaly_operations.rm_assignment a
     WHERE a.member_account_id = p_member AND a.status = 'active' AND a.rm_kind = 'staff'
     LIMIT 1;
$$;

-- An agent changes a client's stage (the pipeline column the family also sees).
CREATE OR REPLACE FUNCTION mangaly_operations.set_client_stage(p_assignment uuid, p_stage text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
BEGIN
    IF NOT mangaly_operations.rm_owns_assignment(p_assignment) THEN
        RETURN false;
    END IF;
    UPDATE mangaly_operations.rm_assignment
       SET stage = p_stage, stage_changed_at = now()
     WHERE id = p_assignment AND stage IS DISTINCT FROM p_stage;
    RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.set_client_stage(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.set_client_stage(uuid, text) TO mangaly_app;

-- A family chooses an agent from the directory: the candidate, or a parent or
-- guardian in their circle, starts the assignment. The agent must be live.
CREATE OR REPLACE FUNCTION mangaly_operations.choose_agent(p_member uuid, p_agent uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
DECLARE
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_id uuid;
BEGIN
    IF v_me IS NULL OR NOT (
         v_me = p_member
      OR EXISTS (SELECT 1 FROM mangaly_home_circle.membership m
                  WHERE m.candidate_profile_id = p_member AND m.member_account_id = v_me
                    AND m.status = 'active' AND m.relationship_type::text IN ('parent', 'guardian'))) THEN
        RAISE EXCEPTION 'choose_agent: the candidate or a parent chooses' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM mangaly_operations.relationship_manager r
                    WHERE r.account_id = p_agent AND r.kind = 'agent')
       OR NOT mangaly_operations.can_work_as_rm(p_agent) THEN
        RAISE EXCEPTION 'choose_agent: not an active agent' USING ERRCODE = 'no_data_found';
    END IF;
    SELECT id INTO v_id FROM mangaly_operations.rm_assignment
     WHERE rm_account_id = p_agent AND member_account_id = p_member AND status = 'active';
    IF v_id IS NOT NULL THEN
        RETURN v_id;
    END IF;
    INSERT INTO mangaly_operations.rm_assignment
        (rm_account_id, member_account_id, rm_kind, origin, consent_recorded_at)
    VALUES (p_agent, p_member, 'agent', 'family_chose', now())
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.choose_agent(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.choose_agent(uuid, uuid) TO mangaly_app;

-- The family (candidate or parent) stops an agent's work for them.
CREATE OR REPLACE FUNCTION mangaly_operations.release_agent(p_member uuid, p_agent uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_home_circle, pg_temp
AS $$
DECLARE
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
BEGIN
    IF v_me IS NULL OR NOT (
         v_me = p_member
      OR EXISTS (SELECT 1 FROM mangaly_home_circle.membership m
                  WHERE m.candidate_profile_id = p_member AND m.member_account_id = v_me
                    AND m.status = 'active' AND m.relationship_type::text IN ('parent', 'guardian'))) THEN
        RAISE EXCEPTION 'release_agent: the candidate or a parent decides' USING ERRCODE = 'insufficient_privilege';
    END IF;
    UPDATE mangaly_operations.rm_assignment
       SET status = 'ended', ended_at = now()
     WHERE rm_account_id = p_agent AND member_account_id = p_member
       AND status = 'active' AND rm_kind = 'agent';
    RETURN FOUND;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.release_agent(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.release_agent(uuid, uuid) TO mangaly_app;

-- Live agents a family can choose from (the directory). Business details
-- only; the agent's own phone is theirs to publish.
CREATE OR REPLACE FUNCTION mangaly_operations.agent_directory()
RETURNS TABLE (
    account_id     uuid,
    display_name   text,
    business_name  text,
    business_phone text,
    city           text,
    languages      text[],
    communities    text[],
    years_active   integer,
    about          text,
    photo_ref      text,
    verified_at    timestamptz,
    families       bigint,
    marriages      bigint
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT r.account_id, r.display_name, r.business_name, r.business_phone, r.city, r.languages,
           r.communities, r.years_active, r.about, r.photo_ref, r.verified_at,
           (SELECT count(*) FROM mangaly_operations.rm_assignment a
             WHERE a.rm_account_id = r.account_id AND a.status = 'active'),
           (SELECT count(*) FROM mangaly_operations.rm_assignment a
             WHERE a.rm_account_id = r.account_id AND a.stage = 'married')
      FROM mangaly_operations.relationship_manager r
     WHERE NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
       AND r.kind = 'agent'
       AND mangaly_operations.can_work_as_rm(r.account_id)
     ORDER BY r.verified_at;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_directory() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_directory() TO mangaly_app;

-- The agents working for a family, for the family's own screen.
CREATE OR REPLACE FUNCTION mangaly_operations.agents_of(p_member uuid)
RETURNS TABLE (assignment_id uuid, agent_account_id uuid, stage text, origin text, assigned_at timestamptz)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_authz, pg_temp
AS $$
    SELECT a.id, a.rm_account_id, a.stage, a.origin, a.assigned_at
      FROM mangaly_operations.rm_assignment a
     WHERE a.member_account_id = p_member
       AND a.status = 'active'
       AND a.rm_kind = 'agent'
       AND (mangaly_authz.is_self(p_member) OR mangaly_authz.has_scope(p_member, 'family_info'))
     ORDER BY a.assigned_at;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agents_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agents_of(uuid) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Profiles an agent adds (041's "made for someone", with the agent as maker).
-- The phone owner takes it over or removes it exactly as for a parent's.
-- The agent's client row is written in the same request (origin
-- 'added_by_agent', consent recorded: the agent confirmed they hold the
-- family's permission, DPDP Act 2023 s.6).
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- Contact numbers
-- ---------------------------------------------------------------------------
ALTER TABLE mangaly_profile.profile
    ADD COLUMN IF NOT EXISTS agents_may_see_contact boolean NOT NULL DEFAULT true;
COMMENT ON COLUMN mangaly_profile.profile.agents_may_see_contact IS
  '[DEC-V1-033] Verified marriage agents may open this family''s number (each look is logged for the family). The family can turn it off.';

CREATE TABLE IF NOT EXISTS mangaly_operations.agent_contact_view (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_account_id   uuid NOT NULL,
  member_account_id  uuid NOT NULL,
  viewed_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agent_contact_view_member
  ON mangaly_operations.agent_contact_view (member_account_id, viewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_contact_view_agent
  ON mangaly_operations.agent_contact_view (agent_account_id, viewed_at DESC);
ALTER TABLE mangaly_operations.agent_contact_view ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS agent_contact_view_read ON mangaly_operations.agent_contact_view;
CREATE POLICY agent_contact_view_read ON mangaly_operations.agent_contact_view
  FOR SELECT USING (mangaly_authz.is_self(member_account_id)
                    OR mangaly_authz.has_scope(member_account_id, 'family_info')
                    OR agent_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
GRANT SELECT ON mangaly_operations.agent_contact_view TO mangaly_app;

-- The numbers an agent may open for one person, written down as opened.
-- Own client: the candidate and the parents/guardian in their circle.
-- Anyone else in Discover: the candidate's number, unless the family has
-- closed it to agents.
CREATE OR REPLACE FUNCTION mangaly_operations.agent_contact(p_member uuid)
RETURNS TABLE (account_id uuid, display_name text, relation text, phone text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_discovery, mangaly_safety, pg_temp
AS $$
DECLARE
    v_me     uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_client boolean;
    v_open   boolean;
BEGIN
    IF NOT mangaly_operations.is_agent() THEN
        RAISE EXCEPTION 'agent_contact: agents only' USING ERRCODE = 'insufficient_privilege';
    END IF;
    v_client := EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a
                         WHERE a.rm_account_id = v_me AND a.member_account_id = p_member AND a.status = 'active');
    SELECT p.agents_may_see_contact
           AND EXISTS (SELECT 1 FROM mangaly_discovery.discovery_profile_index i
                        WHERE i.profile_id = p.account_id AND i.searchable)
      INTO v_open
      FROM mangaly_profile.profile p WHERE p.account_id = p_member;
    IF NOT v_client AND NOT COALESCE(v_open, false) THEN
        RETURN;
    END IF;
    IF NOT v_client AND mangaly_safety.is_blocked_between(v_me, p_member) THEN
        RETURN;
    END IF;

    INSERT INTO mangaly_operations.agent_contact_view (agent_account_id, member_account_id)
    VALUES (v_me, p_member);

    RETURN QUERY
    SELECT a.id, COALESCE(p.name, a.display_name), 'self'::text, a.phone_identifier
      FROM mangaly_identity.account a
      LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id
     WHERE a.id = p_member
    UNION ALL
    SELECT a.id, a.display_name, COALESCE(m.relation, m.relationship_type::text), a.phone_identifier
      FROM mangaly_home_circle.membership m
      JOIN mangaly_identity.account a ON a.id = m.member_account_id
     WHERE v_client
       AND m.candidate_profile_id = p_member
       AND m.status = 'active'
       AND m.relationship_type::text IN ('parent', 'guardian');
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_contact(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_contact(uuid) TO mangaly_app;

-- Which of these people may the agent open a number for (no logging: this
-- only draws the "Call" buttons)?
CREATE OR REPLACE FUNCTION mangaly_operations.agent_contact_open(p_members uuid[])
RETURNS TABLE (account_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, mangaly_discovery, pg_temp
AS $$
    SELECT p.account_id
      FROM mangaly_profile.profile p
     WHERE mangaly_operations.is_agent()
       AND p.account_id = ANY (p_members)
       AND (EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a
                     WHERE a.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
                       AND a.member_account_id = p.account_id AND a.status = 'active')
            OR (p.agents_may_see_contact
                AND EXISTS (SELECT 1 FROM mangaly_discovery.discovery_profile_index i
                             WHERE i.profile_id = p.account_id AND i.searchable)));
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_contact_open(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_contact_open(uuid[]) TO mangaly_app;

-- Who opened the family's number, for the family's own screen.
CREATE OR REPLACE FUNCTION mangaly_operations.contact_views_of(p_member uuid)
RETURNS TABLE (agent_account_id uuid, display_name text, business_name text, city text, viewed_at timestamptz)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_authz, pg_temp
AS $$
    SELECT v.agent_account_id, r.display_name, r.business_name, r.city, MAX(v.viewed_at)
      FROM mangaly_operations.agent_contact_view v
      JOIN mangaly_operations.relationship_manager r ON r.account_id = v.agent_account_id
     WHERE v.member_account_id = p_member
       AND (mangaly_authz.is_self(p_member) OR mangaly_authz.has_scope(p_member, 'family_info'))
     GROUP BY v.agent_account_id, r.display_name, r.business_name, r.city
     ORDER BY MAX(v.viewed_at) DESC
     LIMIT 100;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.contact_views_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.contact_views_of(uuid) TO mangaly_app;

-- The family's switch.
CREATE OR REPLACE FUNCTION mangaly_profile.set_agents_may_see_contact(p_member uuid, p_open boolean)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_home_circle, pg_temp
AS $$
DECLARE
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
BEGIN
    IF v_me IS NULL OR NOT (
         v_me = p_member
      OR EXISTS (SELECT 1 FROM mangaly_home_circle.membership m
                  WHERE m.candidate_profile_id = p_member AND m.member_account_id = v_me
                    AND m.status = 'active' AND m.relationship_type::text IN ('parent', 'guardian'))) THEN
        RAISE EXCEPTION 'set_agents_may_see_contact: the candidate or a parent decides' USING ERRCODE = 'insufficient_privilege';
    END IF;
    UPDATE mangaly_profile.profile SET agents_may_see_contact = p_open, updated_at = now()
     WHERE account_id = p_member;
    RETURN FOUND;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_profile.set_agents_may_see_contact(uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.set_agents_may_see_contact(uuid, boolean) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_profile.agents_may_see_contact(p_member uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_authz, pg_temp
AS $$
    SELECT p.agents_may_see_contact FROM mangaly_profile.profile p
     WHERE p.account_id = p_member
       AND (mangaly_authz.is_self(p_member) OR mangaly_authz.has_scope(p_member, 'family_info'));
$$;
REVOKE ALL ON FUNCTION mangaly_profile.agents_may_see_contact(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.agents_may_see_contact(uuid) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Exports
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_operations.agent_export (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_account_id  uuid NOT NULL,
  kind              text NOT NULL CHECK (kind IN ('excel', 'biodata')),
  member_ids        uuid[] NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agent_export_agent
  ON mangaly_operations.agent_export (agent_account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_export_members
  ON mangaly_operations.agent_export USING gin (member_ids);
ALTER TABLE mangaly_operations.agent_export ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS agent_export_own ON mangaly_operations.agent_export;
CREATE POLICY agent_export_own ON mangaly_operations.agent_export
  USING (agent_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid)
  WITH CHECK (mangaly_operations.is_agent()
              AND agent_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
GRANT SELECT, INSERT ON mangaly_operations.agent_export TO mangaly_app;

-- Exports that included the family, for the family's own screen.
CREATE OR REPLACE FUNCTION mangaly_operations.exports_of(p_member uuid)
RETURNS TABLE (agent_account_id uuid, display_name text, business_name text, kind text, created_at timestamptz)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_authz, pg_temp
AS $$
    SELECT e.agent_account_id, r.display_name, r.business_name, e.kind, e.created_at
      FROM mangaly_operations.agent_export e
      JOIN mangaly_operations.relationship_manager r ON r.account_id = e.agent_account_id
     WHERE p_member = ANY (e.member_ids)
       AND (mangaly_authz.is_self(p_member) OR mangaly_authz.has_scope(p_member, 'family_info'))
     ORDER BY e.created_at DESC
     LIMIT 100;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.exports_of(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.exports_of(uuid) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Moderator view of applications ('operations' operator role).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_operations.agent_applications()
RETURNS TABLE (
    account_id uuid, display_name text, business_name text, business_phone text, city text,
    languages text[], communities text[], years_active integer, about text,
    verification_status text, applied_at timestamptz, verified_at timestamptz, membership_until timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT r.account_id, r.display_name, r.business_name, r.business_phone, r.city, r.languages,
           r.communities, r.years_active, r.about, r.verification_status, r.applied_at, r.verified_at,
           mangaly_operations.agent_membership_until(r.account_id)
      FROM mangaly_operations.relationship_manager r
     WHERE r.kind = 'agent'
       AND current_setting('mangaly.operator_role', true) = 'operations'
     ORDER BY (r.verification_status = 'pending') DESC, r.applied_at DESC;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_applications() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_applications() TO mangaly_app;

-- The signed-in account's own agent record (any status), for /agent.
CREATE OR REPLACE FUNCTION mangaly_operations.my_agent_record()
RETURNS TABLE (
    kind text, display_name text, business_name text, business_phone text, city text,
    languages text[], communities text[], years_active integer, about text,
    verification_status text, applied_at timestamptz, verified_at timestamptz, membership_until timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT r.kind, r.display_name, r.business_name, r.business_phone, r.city, r.languages,
           r.communities, r.years_active, r.about, r.verification_status, r.applied_at, r.verified_at,
           mangaly_operations.agent_membership_until(r.account_id)
      FROM mangaly_operations.relationship_manager r
     WHERE r.account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.my_agent_record() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.my_agent_record() TO mangaly_app;

-- ---------------------------------------------------------------------------
-- A client's whole biodata, for the agent who works for them (the export and
-- the client page). Only for the agent's own active clients; other profiles
-- are exported from their public biodata (migration 027) like any member
-- sees them.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_operations.agent_client_biodata(p_member uuid)
RETURNS TABLE (category text, attribute_key text, value jsonb)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, pg_temp
AS $$
    SELECT pa.category::text, pa.attribute_key, pa.value
      FROM mangaly_profile.profile p
      JOIN mangaly_profile.profile_attribute pa ON pa.profile_id = p.id
     WHERE p.account_id = p_member
       AND pa.state::text = 'value'
       AND pa.value IS NOT NULL
       AND mangaly_operations.is_agent()
       AND EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a
                    WHERE a.member_account_id = p_member AND a.status = 'active'
                      AND a.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_client_biodata(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_client_biodata(uuid) TO mangaly_app;

-- A client's core row (name, birth date, gender, city, taken over or not, who
-- made it) and main photo, for the agent's list and exports.
CREATE OR REPLACE FUNCTION mangaly_operations.agent_client_cores(p_members uuid[])
RETURNS TABLE (
    account_id uuid, name text, date_of_birth date, gender text, city text,
    made_by_me boolean, claimed boolean, photo_ref text, looking_for text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, mangaly_discovery, pg_temp
AS $$
    SELECT p.account_id, p.name, p.date_of_birth, p.gender, p.city_locality,
           p.created_by_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid,
           p.claimed_at IS NOT NULL,
           (SELECT pm.storage_ref FROM mangaly_profile.profile_media pm
             WHERE pm.profile_id = p.id AND pm.is_primary
               AND pm.media_type::text = 'photo' AND pm.upload_status::text = 'complete' LIMIT 1),
           (SELECT d.looking_for FROM mangaly_discovery.discovery_profile_index d WHERE d.profile_id = p.account_id)
      FROM mangaly_profile.profile p
     WHERE p.account_id = ANY (p_members)
       AND mangaly_operations.is_agent()
       AND EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a
                    WHERE a.member_account_id = p.account_id AND a.status = 'active'
                      AND a.rm_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_client_cores(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_client_cores(uuid[]) TO mangaly_app;

-- =============================================================================
-- Part 2 (owner, 2026-09-29, later the same day): families connect to agents.
--   "people in Mangaly can connect to an agent to enhance their profiling, so
--   the agent can share them profiles which are not in Mangaly or which are in
--   Mangaly also ... connecting to an agent is a premium tier which admin can
--   decide, and they get an agent dashboard where all profiles are shared."
--
--   AGENT_CONNECT     the family's plan that lets them choose agents. Its
--                     price (like every plan's) can be set by a Mangaly
--                     administrator in `plan_price`, over the catalogue.
--   offline_profile   a biodata an agent holds for someone NOT on Mangaly
--                     (photo, facts, the biodata file). Shared only by that
--                     agent, only with families that chose the agent, and
--                     always labelled as not a Mangaly member, not verified.
--   rm_suggestion     now carries either a Mangaly profile or an offline one;
--                     the family answers liked / passed / ask (a question for
--                     the agent about this profile).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Prices an administrator sets (over config/plans.py's placeholders).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_billing.plan_price (
  plan_code     text NOT NULL CHECK (plan_code IN ('GOLD', 'ASSISTED', 'AGENT', 'AGENT_CONNECT')),
  term_months   int  NOT NULL CHECK (term_months IN (3, 6, 12)),
  amount_paise  bigint NOT NULL CHECK (amount_paise > 0),
  active        boolean NOT NULL DEFAULT true,
  updated_by    uuid,
  updated_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (plan_code, term_months)
);
COMMENT ON TABLE mangaly_billing.plan_price IS
  '[DEC-V1-033] An administrator''s price for a plan term, used instead of the catalogue placeholder. active=false withdraws the term.';
ALTER TABLE mangaly_billing.plan_price ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS plan_price_read ON mangaly_billing.plan_price;
CREATE POLICY plan_price_read ON mangaly_billing.plan_price FOR SELECT USING (true);
GRANT SELECT ON mangaly_billing.plan_price TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_billing.set_plan_price(
    p_plan text, p_months int, p_amount_paise bigint, p_active boolean
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_billing, pg_temp
AS $$
BEGIN
    IF current_setting('mangaly.operator_role', true) IS DISTINCT FROM 'operations' THEN
        RAISE EXCEPTION 'set_plan_price: administrators only' USING ERRCODE = 'insufficient_privilege';
    END IF;
    INSERT INTO mangaly_billing.plan_price (plan_code, term_months, amount_paise, active, updated_by, updated_at)
    VALUES (p_plan, p_months, p_amount_paise, p_active,
            NULLIF(current_setting('mangaly.account_id', true), '')::uuid, now())
    ON CONFLICT (plan_code, term_months) DO UPDATE
       SET amount_paise = EXCLUDED.amount_paise, active = EXCLUDED.active,
           updated_by = EXCLUDED.updated_by, updated_at = now();
END;
$$;
REVOKE ALL ON FUNCTION mangaly_billing.set_plan_price(text, int, bigint, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_billing.set_plan_price(text, int, bigint, boolean) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Agent Connect: does this family hold it? Bought by the candidate, or by a
-- parent or guardian in their circle — in Indian families the parents very
-- often pay, and a parent's Agent Connect covers the children they help.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_operations.agent_connect_until(p_member uuid)
RETURNS timestamptz
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_billing, mangaly_home_circle, pg_temp
AS $$
    SELECT MAX(s.ends_at) FROM mangaly_billing.plan_subscription s
     WHERE s.plan_code = 'AGENT_CONNECT'
       AND s.status = 'active'
       AND s.started_at <= now()
       AND s.ends_at > now()
       AND (s.account_id = p_member
            OR s.account_id IN (SELECT m.member_account_id FROM mangaly_home_circle.membership m
                                 WHERE m.candidate_profile_id = p_member AND m.status = 'active'
                                   AND m.relationship_type::text IN ('parent', 'guardian')));
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_connect_until(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_connect_until(uuid) TO mangaly_app;

-- choose_agent, now also requiring Agent Connect.
CREATE OR REPLACE FUNCTION mangaly_operations.choose_agent(p_member uuid, p_agent uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_home_circle, mangaly_authz, pg_temp
AS $$
DECLARE
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_id uuid;
BEGIN
    IF v_me IS NULL OR NOT (
         v_me = p_member
      OR EXISTS (SELECT 1 FROM mangaly_home_circle.membership m
                  WHERE m.candidate_profile_id = p_member AND m.member_account_id = v_me
                    AND m.status = 'active' AND m.relationship_type::text IN ('parent', 'guardian'))) THEN
        RAISE EXCEPTION 'choose_agent: the candidate or a parent chooses' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF mangaly_operations.agent_connect_until(p_member) IS NULL THEN
        RAISE EXCEPTION 'choose_agent: needs Agent Connect' USING ERRCODE = 'MGL02';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM mangaly_operations.relationship_manager r
                    WHERE r.account_id = p_agent AND r.kind = 'agent')
       OR NOT mangaly_operations.can_work_as_rm(p_agent) THEN
        RAISE EXCEPTION 'choose_agent: not an active agent' USING ERRCODE = 'no_data_found';
    END IF;
    SELECT id INTO v_id FROM mangaly_operations.rm_assignment
     WHERE rm_account_id = p_agent AND member_account_id = p_member AND status = 'active';
    IF v_id IS NOT NULL THEN
        RETURN v_id;
    END IF;
    INSERT INTO mangaly_operations.rm_assignment
        (rm_account_id, member_account_id, rm_kind, origin, consent_recorded_at)
    VALUES (p_agent, p_member, 'agent', 'family_chose', now())
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.choose_agent(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.choose_agent(uuid, uuid) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Offline profiles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_operations.offline_profile (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_account_id     uuid NOT NULL,
  name                 text NOT NULL,
  gender               text NOT NULL CHECK (gender IN ('male', 'female')),
  date_of_birth        date,
  city                 text,
  details              jsonb NOT NULL DEFAULT '{}'::jsonb,
  photo_refs           text[] NOT NULL DEFAULT '{}',
  biodata_ref          text,
  contact_note         text,
  consent_confirmed_at timestamptz NOT NULL,
  archived_at          timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_offline_profile_agent
  ON mangaly_operations.offline_profile (agent_account_id, created_at DESC);
COMMENT ON TABLE mangaly_operations.offline_profile IS
  '[DEC-V1-033] Biodata an agent holds for someone who is not on Mangaly: details are the biodata facts, biodata_ref the file as received, consent_confirmed_at the agent''s confirmation of the family''s permission. Seen only by the agent and the families the agent shared it with; never in Discover.';

ALTER TABLE mangaly_operations.rm_suggestion
    ALTER COLUMN suggested_account_id DROP NOT NULL;
ALTER TABLE mangaly_operations.rm_suggestion
    ADD COLUMN IF NOT EXISTS offline_profile_id uuid REFERENCES mangaly_operations.offline_profile(id),
    ADD COLUMN IF NOT EXISTS question text;
DO $$ BEGIN
  ALTER TABLE mangaly_operations.rm_suggestion
    ADD CONSTRAINT rm_suggestion_one_subject
    CHECK ((suggested_account_id IS NULL) <> (offline_profile_id IS NULL));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
CREATE UNIQUE INDEX IF NOT EXISTS rm_suggestion_one_offline_per_assignment
  ON mangaly_operations.rm_suggestion (assignment_id, offline_profile_id) WHERE offline_profile_id IS NOT NULL;
DO $$
DECLARE c record;
BEGIN
  FOR c IN
    SELECT conname FROM pg_constraint
     WHERE conrelid = 'mangaly_operations.rm_suggestion'::regclass AND contype = 'c'
       AND pg_get_constraintdef(oid) LIKE '%member_decision%'
  LOOP
    EXECUTE format('ALTER TABLE mangaly_operations.rm_suggestion DROP CONSTRAINT %I', c.conname);
  END LOOP;
END $$;
ALTER TABLE mangaly_operations.rm_suggestion
  ADD CONSTRAINT rm_suggestion_member_decision_check
  CHECK (member_decision IS NULL OR member_decision IN ('liked', 'passed', 'ask'));

ALTER TABLE mangaly_operations.offline_profile ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS offline_profile_agent ON mangaly_operations.offline_profile;
CREATE POLICY offline_profile_agent ON mangaly_operations.offline_profile
  USING (mangaly_operations.is_agent()
         AND agent_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid)
  WITH CHECK (mangaly_operations.is_agent()
              AND agent_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid);
DROP POLICY IF EXISTS offline_profile_shared_family ON mangaly_operations.offline_profile;
CREATE POLICY offline_profile_shared_family ON mangaly_operations.offline_profile
  FOR SELECT USING (EXISTS (
      SELECT 1 FROM mangaly_operations.rm_suggestion s
       WHERE s.offline_profile_id = offline_profile.id
         AND mangaly_operations.rm_assignment_visible(s.assignment_id)));
GRANT SELECT, INSERT, UPDATE ON mangaly_operations.offline_profile TO mangaly_app;

-- May the signed-in account see this offline profile's photo or file?
CREATE OR REPLACE FUNCTION mangaly_operations.offline_media_visible(p_ref text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM mangaly_operations.offline_profile o
         WHERE (p_ref = ANY (o.photo_refs) OR p_ref = o.biodata_ref)
           AND (o.agent_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
                OR EXISTS (SELECT 1 FROM mangaly_operations.rm_suggestion s
                            WHERE s.offline_profile_id = o.id
                              AND mangaly_operations.rm_assignment_visible(s.assignment_id))));
$$;
REVOKE ALL ON FUNCTION mangaly_operations.offline_media_visible(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.offline_media_visible(text) TO mangaly_app;

-- The family may write a question with 'ask' (052's policy, re-stated).
DROP POLICY IF EXISTS rm_suggestion_member_decides ON mangaly_operations.rm_suggestion;
CREATE POLICY rm_suggestion_member_decides ON mangaly_operations.rm_suggestion
  FOR UPDATE USING (mangaly_operations.rm_assignment_visible(assignment_id)
                    AND NOT mangaly_operations.is_rm())
  WITH CHECK (mangaly_operations.rm_assignment_visible(assignment_id));
