-- =============================================================================
-- 056 — Kundli charts and Guna Milan results from the horoscope service.
--
-- WHY (2026-09-27):
--   * Guna Milan and Mangal Dosha are calculated by
--     modules/MOD03-mangaly/horoscope-service (a pinned astronomy library for
--     planet positions, Mangaly's own koota tables verified against Drik
--     Panchang and AstroSage). mangaly-service stores what it returns here.
--   * This replaces migration 049, whose in-process Python engine was never
--     switched on (049 was never applied to the development database). The
--     schema is recreated so either history ends in the same state.
--   * Append-only: a chart or match, once stored, is never rewritten. A change
--     to someone's birth details, or a new rules version, adds a new row;
--     `current_chart` reads the newest. Historical results stay explainable.
--   * Birth time and place are public biodata by the owner's decision
--     (2026-09-27), so a chart may be read by anyone who may read the person's
--     biodata: themselves, any signed-in member for a searchable candidate, or
--     someone connected with them. Writing is the person (or a parent managing
--     the profile they created) only.
--   * rashi / nakshatra / moon_sign_half / mangal_status / mangal_level are copied into
--     columns so Discover can filter on horoscope without parsing JSON.
-- Idempotent: safe to re-run.
-- =============================================================================

DROP SCHEMA IF EXISTS mangaly_horoscope CASCADE;
CREATE SCHEMA mangaly_horoscope AUTHORIZATION mangaly_owner;
GRANT USAGE ON SCHEMA mangaly_horoscope TO mangaly_app;

CREATE TABLE mangaly_horoscope.chart (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id          uuid NOT NULL,
    calculation_id      text NOT NULL,
    calculation_version text NOT NULL,
    rules_version       text NOT NULL,
    provider            text NOT NULL,
    rashi               smallint CHECK (rashi BETWEEN 1 AND 12),
    nakshatra           smallint CHECK (nakshatra BETWEEN 1 AND 27),
    moon_sign_half      smallint CHECK (moon_sign_half IN (1, 2)),
    mangal_status       text CHECK (mangal_status IN ('PRESENT', 'ABSENT', 'CANCELLED', 'INDETERMINATE')),
    mangal_level        text CHECK (mangal_level IN ('HIGH', 'LOW')),
    chart               jsonb NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (account_id, calculation_id)
);
CREATE INDEX chart_account_newest ON mangaly_horoscope.chart (account_id, created_at DESC);
COMMENT ON TABLE mangaly_horoscope.chart IS
  '[056] Canonical kundli per person from horoscope-service, append-only; newest row is current.';

CREATE TABLE mangaly_horoscope.match (
    match_id          text PRIMARY KEY,
    groom_account_id  uuid NOT NULL,
    bride_account_id  uuid NOT NULL,
    groom_calculation text NOT NULL,
    bride_calculation text NOT NULL,
    rules_version     text NOT NULL,
    total_score       numeric(4, 1),
    porutham_agreed   smallint CHECK (porutham_agreed BETWEEN 0 AND 10),
    result            jsonb NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX match_pair ON mangaly_horoscope.match (groom_account_id, bride_account_id, created_at DESC);
COMMENT ON TABLE mangaly_horoscope.match IS
  '[056] Guna Milan + Mangal result for a pair of stored charts, append-only; match_id is deterministic.';

ALTER TABLE mangaly_horoscope.chart ENABLE ROW LEVEL SECURITY;
ALTER TABLE mangaly_horoscope.match ENABLE ROW LEVEL SECURITY;
-- Direct table access is the person's own rows only; everything else goes
-- through the functions below.
CREATE POLICY chart_self ON mangaly_horoscope.chart
  USING (mangaly_authz.is_self(account_id)) WITH CHECK (mangaly_authz.is_self(account_id));
CREATE POLICY match_party ON mangaly_horoscope.match
  USING (mangaly_authz.is_self(groom_account_id) OR mangaly_authz.is_self(bride_account_id));
GRANT SELECT, INSERT ON mangaly_horoscope.chart TO mangaly_app;
GRANT SELECT ON mangaly_horoscope.match TO mangaly_app;

-- Who may read this person's chart: exactly who may read their biodata.
CREATE OR REPLACE FUNCTION mangaly_horoscope.can_read(p_account uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_horoscope, mangaly_profile, mangaly_discovery, mangaly_authz, pg_temp
AS $$
    SELECT NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
       AND (
            mangaly_authz.is_self(p_account)
         OR EXISTS (SELECT 1 FROM mangaly_discovery.discovery_profile_index i
                     WHERE i.profile_id = p_account AND i.searchable)
         OR EXISTS (SELECT 1
                      FROM mangaly_authz.grant g
                      JOIN mangaly_profile.profile p ON p.id = g.target_profile_id
                     WHERE p.account_id = p_account
                       AND g.scope = 'candidate_info'
                       AND g.status = 'active'
                       AND g.subject_id IN (
                             NULLIF(current_setting('mangaly.account_id', true), '')::uuid,
                             NULLIF(current_setting('mangaly.authz_context', true), '')::uuid))
       );
$$;
REVOKE ALL ON FUNCTION mangaly_horoscope.can_read(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_horoscope.can_read(uuid) TO mangaly_app;

-- The newest chart, with the person's gender (the groom/bride order of
-- Ashtakoota needs it, and a family member cannot read profile rows directly).
DROP FUNCTION IF EXISTS mangaly_horoscope.current_chart(uuid);
CREATE OR REPLACE FUNCTION mangaly_horoscope.current_chart(p_account uuid)
RETURNS TABLE (account_id uuid, calculation_id text, rules_version text, chart jsonb, created_at timestamptz, gender text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_horoscope, mangaly_profile, pg_temp
AS $$
    SELECT c.account_id, c.calculation_id, c.rules_version, c.chart, c.created_at, p.gender::text
      FROM mangaly_horoscope.chart c
      JOIN mangaly_profile.profile p ON p.account_id = c.account_id
     WHERE c.account_id = p_account
       AND mangaly_horoscope.can_read(p_account)
     ORDER BY c.created_at DESC
     LIMIT 1;
$$;
REVOKE ALL ON FUNCTION mangaly_horoscope.current_chart(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_horoscope.current_chart(uuid) TO mangaly_app;

-- A match may be stored by anyone who may read both charts; the result holds
-- no birth inputs. Never overwritten: the same match_id is a no-op.
CREATE OR REPLACE FUNCTION mangaly_horoscope.save_match(
    p_match_id text, p_groom uuid, p_bride uuid, p_groom_calc text, p_bride_calc text,
    p_rules_version text, p_total numeric, p_porutham smallint, p_result jsonb)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_horoscope, pg_temp
AS $$
BEGIN
    IF NOT (mangaly_horoscope.can_read(p_groom) AND mangaly_horoscope.can_read(p_bride)) THEN
        RAISE EXCEPTION 'not allowed to store this match' USING ERRCODE = 'insufficient_privilege';
    END IF;
    INSERT INTO mangaly_horoscope.match
        (match_id, groom_account_id, bride_account_id, groom_calculation, bride_calculation, rules_version, total_score, porutham_agreed, result)
    VALUES (p_match_id, p_groom, p_bride, p_groom_calc, p_bride_calc, p_rules_version, p_total, p_porutham, p_result)
    ON CONFLICT (match_id) DO NOTHING;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_horoscope.save_match(text, uuid, uuid, text, text, text, numeric, smallint, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_horoscope.save_match(text, uuid, uuid, text, text, text, numeric, smallint, jsonb) TO mangaly_app;

-- For the Discover horoscope filter: the current Moon placement and Mangal
-- result of each listed person who is searchable (the same people Discover
-- may show). Derived values only; no birth details.
CREATE OR REPLACE FUNCTION mangaly_horoscope.placements(p_accounts uuid[])
RETURNS TABLE (account_id uuid, rashi smallint, nakshatra smallint, moon_sign_half smallint,
               mangal_status text, mangal_level text, rules_version text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_horoscope, mangaly_discovery, pg_temp
AS $$
    SELECT DISTINCT ON (c.account_id)
           c.account_id, c.rashi, c.nakshatra, c.moon_sign_half, c.mangal_status, c.mangal_level, c.rules_version
      FROM mangaly_horoscope.chart c
      JOIN mangaly_discovery.discovery_profile_index i ON i.profile_id = c.account_id AND i.searchable
     WHERE c.account_id = ANY(p_accounts)
       AND NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
     ORDER BY c.account_id, c.created_at DESC;
$$;
REVOKE ALL ON FUNCTION mangaly_horoscope.placements(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_horoscope.placements(uuid[]) TO mangaly_app;
