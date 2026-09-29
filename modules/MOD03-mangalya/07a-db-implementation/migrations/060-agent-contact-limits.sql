-- 060 — Marriage agents: fair-use limits on numbers and exports, and reports
-- of unwanted calls (DEC-V1-034).
--
-- The product owner (2026-09-29): whatever an agent does on his own WhatsApp
-- groups is his business, but on Mangaly a number or email sits behind the
-- eye button, so Mangaly can count how many families' details an agent takes
-- and limit it. A family that gets spam calls reports it, and the record of
-- who opened their number shows who to look at.
--
--   agent_limit            the numbers administrators tune (no code change)
--   agent_contact_view     + counted / is_client / via
--   agent_contact(...)     now also returns the email, and enforces the limits
--   agent_quota()          what the agent has used today and this month
--   agent_export           + others_count (people who are not the agent's clients)
--   contact_report         a family's report of an unwanted call or message
--   relationship_manager   + contact_suspended_at: the eye is shut for this agent
--
-- Idempotent.

-- ---------------------------------------------------------------------------
-- Suspension
-- ---------------------------------------------------------------------------
ALTER TABLE mangaly_operations.relationship_manager
    ADD COLUMN IF NOT EXISTS contact_suspended_at timestamptz;
COMMENT ON COLUMN mangaly_operations.relationship_manager.contact_suspended_at IS
  '[DEC-V1-034] Set when families'' reports reach the limit: the agent keeps their clients but cannot open anyone else''s number until a moderator clears it.';

ALTER TABLE mangaly_operations.relationship_manager
    DROP CONSTRAINT IF EXISTS relationship_manager_verification_check;
ALTER TABLE mangaly_operations.relationship_manager
    ADD CONSTRAINT relationship_manager_verification_check
    CHECK (verification_status IN ('pending', 'verified', 'rejected', 'suspended'));

-- A moderator verifies, rejects or suspends an agent. Verifying again also
-- lifts a contact suspension.
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
    IF p_status NOT IN ('verified', 'rejected', 'suspended') THEN
        RAISE EXCEPTION 'review_agent: bad status' USING ERRCODE = 'invalid_parameter_value';
    END IF;
    UPDATE mangaly_operations.relationship_manager
       SET verification_status = p_status,
           verified_at = CASE WHEN p_status = 'verified' THEN COALESCE(verified_at, now())
                              WHEN p_status = 'suspended' THEN verified_at
                              ELSE NULL END,
           contact_suspended_at = CASE WHEN p_status = 'verified' THEN NULL ELSE contact_suspended_at END
     WHERE account_id = p_account AND kind = 'agent';
    RETURN FOUND;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.review_agent(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.review_agent(uuid, text) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Limits administrators tune
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_operations.agent_limit (
  name        text PRIMARY KEY CHECK (name IN (
                'contacts_per_day', 'contacts_per_month', 'export_others_per_day',
                'profiles_added_per_day', 'reports_to_suspend')),
  value       integer NOT NULL CHECK (value >= 0),
  updated_by  uuid,
  updated_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_operations.agent_limit IS
  '[DEC-V1-034] Fair-use limits for marriage agents. Own clients never count against them.';
-- Starting values (DEC-V1-034 explains each).
INSERT INTO mangaly_operations.agent_limit (name, value) VALUES
  ('contacts_per_day', 20),
  ('contacts_per_month', 300),
  ('export_others_per_day', 50),
  ('profiles_added_per_day', 100),
  ('reports_to_suspend', 3)
ON CONFLICT (name) DO NOTHING;
ALTER TABLE mangaly_operations.agent_limit ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS agent_limit_read ON mangaly_operations.agent_limit;
CREATE POLICY agent_limit_read ON mangaly_operations.agent_limit FOR SELECT USING (true);
GRANT SELECT ON mangaly_operations.agent_limit TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_operations.agent_limit_value(p_name text)
RETURNS integer
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT value FROM mangaly_operations.agent_limit WHERE name = p_name;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_limit_value(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_limit_value(text) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_operations.set_agent_limit(p_name text, p_value integer)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
BEGIN
    IF current_setting('mangaly.operator_role', true) IS DISTINCT FROM 'operations' THEN
        RAISE EXCEPTION 'set_agent_limit: administrators only' USING ERRCODE = 'insufficient_privilege';
    END IF;
    UPDATE mangaly_operations.agent_limit
       SET value = p_value, updated_at = now(),
           updated_by = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
     WHERE name = p_name;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'set_agent_limit: unknown limit' USING ERRCODE = 'invalid_parameter_value';
    END IF;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.set_agent_limit(text, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.set_agent_limit(text, integer) TO mangaly_app;

-- The start of today in India, where every agent works.
CREATE OR REPLACE FUNCTION mangaly_operations.india_today_start()
RETURNS timestamptz
LANGUAGE sql
STABLE
AS $$
    SELECT date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata';
$$;
GRANT EXECUTE ON FUNCTION mangaly_operations.india_today_start() TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Opening a number
-- ---------------------------------------------------------------------------
ALTER TABLE mangaly_operations.agent_contact_view
    ADD COLUMN IF NOT EXISTS counted   boolean NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS is_client boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS via       text NOT NULL DEFAULT 'eye';
DO $$ BEGIN
  ALTER TABLE mangaly_operations.agent_contact_view
    ADD CONSTRAINT agent_contact_view_via_check CHECK (via IN ('eye', 'export'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
COMMENT ON COLUMN mangaly_operations.agent_contact_view.counted IS
  '[DEC-V1-034] True when this look used one of the agent''s daily and monthly opens: a family who is not their client, not opened by them in the last 30 days.';

-- The return type changes (email added), so the old function goes first.
DROP FUNCTION IF EXISTS mangaly_operations.agent_contact(uuid);
DROP FUNCTION IF EXISTS mangaly_operations.agent_contact(uuid, text);

-- The number and email an agent may open for one person, written down as
-- opened.
--   Own client: the candidate and the parents/guardian in their circle, always.
--   Anyone else in Discover: the candidate's own, unless the family closed it
--   to agents — and only within the agent's limits. Opening the same family
--   again within 30 days is free. An export ('export') never opens a new
--   family: it repeats only numbers the agent opened in the last 30 days.
-- Errors: MGL41 today's opens used up, MGL42 this month's, MGL43 the eye is
-- shut for this agent after families' reports.
CREATE OR REPLACE FUNCTION mangaly_operations.agent_contact(p_member uuid, p_via text DEFAULT 'eye')
RETURNS TABLE (account_id uuid, display_name text, relation text, phone text, email text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, mangaly_identity, mangaly_home_circle, mangaly_discovery, mangaly_safety, pg_temp
AS $$
DECLARE
    v_me       uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_client   boolean;
    v_open     boolean;
    v_recent   boolean;
    v_today    integer;
    v_month    integer;
BEGIN
    IF NOT mangaly_operations.is_agent() THEN
        RAISE EXCEPTION 'agent_contact: agents only' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF p_via NOT IN ('eye', 'export') THEN
        RAISE EXCEPTION 'agent_contact: bad via' USING ERRCODE = 'invalid_parameter_value';
    END IF;
    v_client := EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a
                         WHERE a.rm_account_id = v_me AND a.member_account_id = p_member AND a.status = 'active');

    IF NOT v_client THEN
        SELECT p.agents_may_see_contact
               AND EXISTS (SELECT 1 FROM mangaly_discovery.discovery_profile_index i
                            WHERE i.profile_id = p.account_id AND i.searchable)
          INTO v_open
          FROM mangaly_profile.profile p WHERE p.account_id = p_member;
        IF NOT COALESCE(v_open, false) OR mangaly_safety.is_blocked_between(v_me, p_member) THEN
            RETURN;
        END IF;
        IF EXISTS (SELECT 1 FROM mangaly_operations.relationship_manager r
                    WHERE r.account_id = v_me AND r.contact_suspended_at IS NOT NULL) THEN
            RAISE EXCEPTION 'agent_contact: suspended' USING ERRCODE = 'MGL43';
        END IF;
        v_recent := EXISTS (SELECT 1 FROM mangaly_operations.agent_contact_view v
                             WHERE v.agent_account_id = v_me AND v.member_account_id = p_member
                               AND v.viewed_at > now() - interval '30 days');
        IF NOT v_recent THEN
            IF p_via = 'export' THEN
                RETURN;
            END IF;
            SELECT count(*) FILTER (WHERE v.viewed_at >= mangaly_operations.india_today_start()),
                   count(*)
              INTO v_today, v_month
              FROM mangaly_operations.agent_contact_view v
             WHERE v.agent_account_id = v_me AND v.counted
               AND v.viewed_at > now() - interval '30 days';
            IF v_today >= mangaly_operations.agent_limit_value('contacts_per_day') THEN
                RAISE EXCEPTION 'agent_contact: daily limit' USING ERRCODE = 'MGL41';
            END IF;
            IF v_month >= mangaly_operations.agent_limit_value('contacts_per_month') THEN
                RAISE EXCEPTION 'agent_contact: monthly limit' USING ERRCODE = 'MGL42';
            END IF;
        END IF;
        INSERT INTO mangaly_operations.agent_contact_view (agent_account_id, member_account_id, counted, is_client, via)
        VALUES (v_me, p_member, NOT v_recent, false, p_via);
    ELSE
        INSERT INTO mangaly_operations.agent_contact_view (agent_account_id, member_account_id, counted, is_client, via)
        VALUES (v_me, p_member, false, true, p_via);
    END IF;

    RETURN QUERY
    SELECT a.id, COALESCE(p.name, a.display_name), 'self'::text, a.phone_identifier, a.email_identifier
      FROM mangaly_identity.account a
      LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id
     WHERE a.id = p_member
    UNION ALL
    SELECT a.id, a.display_name, COALESCE(m.relation, m.relationship_type::text), a.phone_identifier, a.email_identifier
      FROM mangaly_home_circle.membership m
      JOIN mangaly_identity.account a ON a.id = m.member_account_id
     WHERE v_client
       AND m.candidate_profile_id = p_member
       AND m.status = 'active'
       AND m.relationship_type::text IN ('parent', 'guardian');
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_contact(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_contact(uuid, text) TO mangaly_app;

-- Which of these people did the agent open in the last 30 days (opening
-- them again is free)?
CREATE OR REPLACE FUNCTION mangaly_operations.agent_opened_recently(p_members uuid[])
RETURNS TABLE (account_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    SELECT DISTINCT v.member_account_id
      FROM mangaly_operations.agent_contact_view v
     WHERE v.agent_account_id = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
       AND v.member_account_id = ANY (p_members)
       AND v.viewed_at > now() - interval '30 days';
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_opened_recently(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_opened_recently(uuid[]) TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Exports and new profiles
-- ---------------------------------------------------------------------------
ALTER TABLE mangaly_operations.agent_export
    ADD COLUMN IF NOT EXISTS others_count integer NOT NULL DEFAULT 0;

-- What the agent has used of each limit.
CREATE OR REPLACE FUNCTION mangaly_operations.agent_quota()
RETURNS TABLE (
    contacts_today integer, contacts_per_day integer,
    contacts_month integer, contacts_per_month integer,
    exported_others_today integer, export_others_per_day integer,
    added_today integer, profiles_added_per_day integer,
    contact_suspended boolean
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
    WITH me AS (SELECT NULLIF(current_setting('mangaly.account_id', true), '')::uuid AS id)
    SELECT
      (SELECT count(*)::int FROM mangaly_operations.agent_contact_view v, me
        WHERE v.agent_account_id = me.id AND v.counted AND v.viewed_at >= mangaly_operations.india_today_start()),
      mangaly_operations.agent_limit_value('contacts_per_day'),
      (SELECT count(*)::int FROM mangaly_operations.agent_contact_view v, me
        WHERE v.agent_account_id = me.id AND v.counted AND v.viewed_at > now() - interval '30 days'),
      mangaly_operations.agent_limit_value('contacts_per_month'),
      (SELECT COALESCE(sum(e.others_count), 0)::int FROM mangaly_operations.agent_export e, me
        WHERE e.agent_account_id = me.id AND e.created_at >= mangaly_operations.india_today_start()),
      mangaly_operations.agent_limit_value('export_others_per_day'),
      (SELECT count(*)::int FROM mangaly_operations.rm_assignment a, me
        WHERE a.rm_account_id = me.id AND a.origin = 'added_by_agent'
          AND a.assigned_at >= mangaly_operations.india_today_start())
      + (SELECT count(*)::int FROM mangaly_operations.offline_profile o, me
          WHERE o.agent_account_id = me.id AND o.created_at >= mangaly_operations.india_today_start()),
      mangaly_operations.agent_limit_value('profiles_added_per_day'),
      COALESCE((SELECT r.contact_suspended_at IS NOT NULL FROM mangaly_operations.relationship_manager r, me
                 WHERE r.account_id = me.id), false)
    WHERE mangaly_operations.is_agent();
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_quota() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_quota() TO mangaly_app;

-- ---------------------------------------------------------------------------
-- Reports of unwanted calls and messages
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mangaly_operations.contact_report (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_account_id  uuid NOT NULL,
  reported_by        uuid NOT NULL,
  channel            text NOT NULL CHECK (channel IN ('call', 'whatsapp', 'sms', 'email')),
  happened_on        date NOT NULL,
  note               text CHECK (note IS NULL OR length(note) <= 2000),
  named_agent_id     uuid,
  suspect_agent_ids  uuid[] NOT NULL DEFAULT '{}',
  status             text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'dismissed', 'warned', 'suspended')),
  reviewed_by        uuid,
  reviewed_at        timestamptz,
  review_note        text,
  created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_contact_report_member
  ON mangaly_operations.contact_report (member_account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_report_named
  ON mangaly_operations.contact_report (named_agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_report_suspects
  ON mangaly_operations.contact_report USING gin (suspect_agent_ids);
COMMENT ON TABLE mangaly_operations.contact_report IS
  '[DEC-V1-034] A family''s report of an unwanted call or message. suspect_agent_ids are the agents who opened or exported their number in the 30 days before; named_agent_id is the agent the family says it was, if they know.';
ALTER TABLE mangaly_operations.contact_report ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contact_report_family ON mangaly_operations.contact_report;
CREATE POLICY contact_report_family ON mangaly_operations.contact_report
  FOR SELECT USING (reported_by = NULLIF(current_setting('mangaly.account_id', true), '')::uuid
                    OR mangaly_authz.is_self(member_account_id)
                    OR mangaly_authz.has_scope(member_account_id, 'family_info'));
GRANT SELECT ON mangaly_operations.contact_report TO mangaly_app;

-- The agents who opened or exported this family's number in the 30 days up
-- to a day. Shown to the family on the report form, and kept on the report.
CREATE OR REPLACE FUNCTION mangaly_operations.contact_suspects(p_member uuid, p_day date)
RETURNS TABLE (agent_account_id uuid, display_name text, business_name text, city text, last_at timestamptz)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_authz, pg_temp
AS $$
    WITH touches AS (
        SELECT v.agent_account_id, v.viewed_at AS at
          FROM mangaly_operations.agent_contact_view v
         WHERE v.member_account_id = p_member AND NOT v.is_client
        UNION ALL
        SELECT e.agent_account_id, e.created_at
          FROM mangaly_operations.agent_export e
         WHERE p_member = ANY (e.member_ids)
    )
    SELECT t.agent_account_id, r.display_name, r.business_name, r.city, max(t.at)
      FROM touches t
      JOIN mangaly_operations.relationship_manager r ON r.account_id = t.agent_account_id
     WHERE t.at >= (p_day - 30)::timestamptz
       AND t.at < (p_day + 1)::timestamptz
       AND (mangaly_authz.is_self(p_member) OR mangaly_authz.has_scope(p_member, 'family_info')
            OR current_setting('mangaly.operator_role', true) = 'operations')
     GROUP BY t.agent_account_id, r.display_name, r.business_name, r.city
     ORDER BY max(t.at) DESC;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.contact_suspects(uuid, date) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.contact_suspects(uuid, date) TO mangaly_app;

-- A family member reports an unwanted call or message. When the same agent
-- is named — or is the only agent who touched the number — by enough
-- different families within 90 days, their eye is shut until a moderator
-- looks. Returns the report and whether that happened.
CREATE OR REPLACE FUNCTION mangaly_operations.report_contact_misuse(
    p_member uuid, p_channel text, p_happened_on date, p_note text, p_named_agent uuid
) RETURNS TABLE (report_id uuid, suspended_agent uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_authz, pg_temp
AS $$
DECLARE
    v_me       uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
    v_suspects uuid[];
    v_accused  uuid;
    v_id       uuid;
    v_families integer;
    v_shut     uuid;
BEGIN
    IF v_me IS NULL OR NOT (mangaly_authz.is_self(p_member) OR mangaly_authz.has_scope(p_member, 'family_info')) THEN
        RAISE EXCEPTION 'report_contact_misuse: the family reports' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF p_happened_on > (now() AT TIME ZONE 'Asia/Kolkata')::date OR p_happened_on < (now() AT TIME ZONE 'Asia/Kolkata')::date - 90 THEN
        RAISE EXCEPTION 'report_contact_misuse: date out of range' USING ERRCODE = 'invalid_parameter_value';
    END IF;
    IF p_named_agent IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM mangaly_operations.relationship_manager r WHERE r.account_id = p_named_agent AND r.kind = 'agent') THEN
        RAISE EXCEPTION 'report_contact_misuse: not an agent' USING ERRCODE = 'invalid_parameter_value';
    END IF;
    SELECT COALESCE(array_agg(s.agent_account_id), '{}') INTO v_suspects
      FROM mangaly_operations.contact_suspects(p_member, p_happened_on) s;

    INSERT INTO mangaly_operations.contact_report
        (member_account_id, reported_by, channel, happened_on, note, named_agent_id, suspect_agent_ids)
    VALUES (p_member, v_me, p_channel, p_happened_on, NULLIF(btrim(p_note), ''), p_named_agent, v_suspects)
    RETURNING id INTO v_id;

    v_accused := COALESCE(p_named_agent, CASE WHEN cardinality(v_suspects) = 1 THEN v_suspects[1] END);
    IF v_accused IS NOT NULL THEN
        SELECT count(DISTINCT c.member_account_id) INTO v_families
          FROM mangaly_operations.contact_report c
         WHERE c.status <> 'dismissed'
           AND c.created_at > now() - interval '90 days'
           AND (c.named_agent_id = v_accused
                OR (c.named_agent_id IS NULL AND c.suspect_agent_ids = ARRAY[v_accused]));
        IF v_families >= mangaly_operations.agent_limit_value('reports_to_suspend') THEN
            UPDATE mangaly_operations.relationship_manager
               SET contact_suspended_at = now()
             WHERE account_id = v_accused AND kind = 'agent' AND contact_suspended_at IS NULL
            RETURNING account_id INTO v_shut;
        END IF;
    END IF;
    RETURN QUERY SELECT v_id, v_shut;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.report_contact_misuse(uuid, text, date, text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.report_contact_misuse(uuid, text, date, text, uuid) TO mangaly_app;

-- Moderators: every report with names, newest open first.
CREATE OR REPLACE FUNCTION mangaly_operations.contact_reports_admin()
RETURNS TABLE (
    id uuid, member_account_id uuid, member_name text, reported_by uuid, reporter_name text,
    channel text, happened_on date, note text,
    named_agent_id uuid, named_agent_name text,
    suspects jsonb, status text, review_note text, created_at timestamptz,
    agent_reports_90d integer
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, mangaly_profile, mangaly_identity, pg_temp
AS $$
    SELECT c.id, c.member_account_id, COALESCE(p.name, ma.display_name),
           c.reported_by, ra.display_name, c.channel, c.happened_on, c.note,
           c.named_agent_id, COALESCE(nr.business_name, nr.display_name),
           COALESCE((SELECT jsonb_agg(jsonb_build_object(
                        'account_id', r.account_id,
                        'name', COALESCE(r.business_name, r.display_name),
                        'city', r.city,
                        'suspended', r.contact_suspended_at IS NOT NULL OR r.verification_status = 'suspended'))
                       FROM mangaly_operations.relationship_manager r
                      WHERE r.account_id = ANY (c.suspect_agent_ids)), '[]'::jsonb),
           c.status, c.review_note, c.created_at,
           (SELECT count(DISTINCT c2.member_account_id)::int FROM mangaly_operations.contact_report c2
             WHERE c2.created_at > now() - interval '90 days' AND c2.status <> 'dismissed'
               AND (c2.named_agent_id = COALESCE(c.named_agent_id, c.suspect_agent_ids[1])
                    OR c2.suspect_agent_ids @> ARRAY[COALESCE(c.named_agent_id, c.suspect_agent_ids[1])]))
      FROM mangaly_operations.contact_report c
      LEFT JOIN mangaly_profile.profile p ON p.account_id = c.member_account_id
      LEFT JOIN mangaly_identity.account ma ON ma.id = c.member_account_id
      LEFT JOIN mangaly_identity.account ra ON ra.id = c.reported_by
      LEFT JOIN mangaly_operations.relationship_manager nr ON nr.account_id = c.named_agent_id
     WHERE current_setting('mangaly.operator_role', true) = 'operations'
     ORDER BY (c.status = 'open') DESC, c.created_at DESC
     LIMIT 500;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.contact_reports_admin() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.contact_reports_admin() TO mangaly_app;

-- A moderator closes a report: dismissed (not the agent), warned, or the
-- agent suspended (their whole workspace closes). A dismissed report no
-- longer counts towards the automatic suspension.
CREATE OR REPLACE FUNCTION mangaly_operations.review_contact_report(
    p_report uuid, p_status text, p_agent uuid, p_note text
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
BEGIN
    IF current_setting('mangaly.operator_role', true) IS DISTINCT FROM 'operations' THEN
        RAISE EXCEPTION 'review_contact_report: moderators only' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF p_status NOT IN ('dismissed', 'warned', 'suspended') THEN
        RAISE EXCEPTION 'review_contact_report: bad status' USING ERRCODE = 'invalid_parameter_value';
    END IF;
    UPDATE mangaly_operations.contact_report
       SET status = p_status, review_note = NULLIF(btrim(p_note), ''), reviewed_at = now(),
           reviewed_by = NULLIF(current_setting('mangaly.account_id', true), '')::uuid,
           named_agent_id = COALESCE(named_agent_id, p_agent)
     WHERE id = p_report;
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    IF p_status = 'suspended' AND p_agent IS NOT NULL THEN
        UPDATE mangaly_operations.relationship_manager
           SET verification_status = 'suspended',
               contact_suspended_at = COALESCE(contact_suspended_at, now())
         WHERE account_id = p_agent AND kind = 'agent';
    END IF;
    RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.review_contact_report(uuid, text, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.review_contact_report(uuid, text, uuid, text) TO mangaly_app;

-- Moderators may lift a contact suspension without re-verifying.
CREATE OR REPLACE FUNCTION mangaly_operations.lift_contact_suspension(p_agent uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
BEGIN
    IF current_setting('mangaly.operator_role', true) IS DISTINCT FROM 'operations' THEN
        RAISE EXCEPTION 'lift_contact_suspension: moderators only' USING ERRCODE = 'insufficient_privilege';
    END IF;
    UPDATE mangaly_operations.relationship_manager SET contact_suspended_at = NULL
     WHERE account_id = p_agent AND kind = 'agent' AND contact_suspended_at IS NOT NULL;
    RETURN FOUND;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.lift_contact_suspension(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.lift_contact_suspension(uuid) TO mangaly_app;

-- Suspended agents appear in the moderators' list too.
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
           r.communities, r.years_active, r.about,
           CASE WHEN r.verification_status = 'verified' AND r.contact_suspended_at IS NOT NULL
                THEN 'contact_suspended' ELSE r.verification_status END,
           r.applied_at, r.verified_at,
           mangaly_operations.agent_membership_until(r.account_id)
      FROM mangaly_operations.relationship_manager r
     WHERE r.kind = 'agent'
       AND current_setting('mangaly.operator_role', true) = 'operations'
     ORDER BY (r.verification_status = 'pending' OR r.contact_suspended_at IS NOT NULL) DESC, r.applied_at DESC;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.agent_applications() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.agent_applications() TO mangaly_app;

-- Looks written before this migration: mark the agent's own clients.
UPDATE mangaly_operations.agent_contact_view v
   SET is_client = true, counted = false
 WHERE NOT v.is_client
   AND EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a
                WHERE a.rm_account_id = v.agent_account_id AND a.member_account_id = v.member_account_id);
