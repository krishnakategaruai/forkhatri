-- 049 — Kundli matching: one cached chart per account, read in pairs (DEC-V1-029)
--
-- A family compares the two kundlis before a match goes further. Mangaly
-- computes each person's Moon chart (rashi, nakshatra, Lagna when time and
-- place are known, Mangal dosha) from the birth details already on the
-- profile (`horoscope.birth_time`, `horoscope.birth_place`, the profile's
-- date of birth) and keeps only the derived chart here — never the birth
-- time or place themselves, which stay in `profile_attribute` under its own
-- rules. The chart is keyed by a hash of its inputs, so a changed birth
-- detail is recomputed on the next read and nothing else ever rewrites it.
--
-- Privacy: a pair's Guna Milan is computed by the service only when BOTH
-- have a chart and at least ONE said "horoscope matching: yes"; the SQL here
-- enforces who may read whose chart at all, and tells the service whether
-- the two are connected (the `candidate_info` grant acceptance creates), so
-- that before acceptance only the total and the reading go out and after
-- it the eight-koota breakdown.

CREATE SCHEMA IF NOT EXISTS mangaly_horoscope AUTHORIZATION mangaly_owner;

CREATE TABLE IF NOT EXISTS mangaly_horoscope.chart (
    account_id         uuid PRIMARY KEY,
    inputs_hash        text NOT NULL,
    chart              jsonb NOT NULL,
    matching_required  boolean NOT NULL DEFAULT false,
    computed_at        timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE mangaly_horoscope.chart IS
  '[DEC-V1-029] Derived Moon chart per account (rashi, nakshatra, lagna, mangal dosha flags). Never the birth time or place. Recomputed when inputs_hash no longer matches the profile''s birth details.';

ALTER TABLE mangaly_horoscope.chart ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS chart_owner ON mangaly_horoscope.chart;
CREATE POLICY chart_owner ON mangaly_horoscope.chart
  USING (mangaly_authz.is_self(account_id))
  WITH CHECK (mangaly_authz.is_self(account_id));
GRANT USAGE ON SCHEMA mangaly_horoscope TO mangaly_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON mangaly_horoscope.chart TO mangaly_app;

-- May the signed-in account work with this person's chart? Themselves, a
-- searchable candidate (the same gate `mangaly_profile.public_biodata` uses:
-- anyone signed in may be shown a searchable candidate), or someone they
-- are connected with. The service never returns the inputs it reads through
-- this gate; it returns the derived chart only.
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

-- The birth details a chart is computed from. Text extraction (`#>> '{}'`)
-- so a jsonb string comes back without its quotes and a jsonb boolean as
-- 'true'/'false'. Only rows the person actually answered (state = 'value').
CREATE OR REPLACE FUNCTION mangaly_horoscope.birth_inputs(p_account uuid)
RETURNS TABLE (
    dob                date,
    gender             text,
    birth_time         text,
    birth_place        text,
    rashi              text,
    nakshatra          text,
    manglik            text,
    matching_required  text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_horoscope, mangaly_profile, pg_temp
AS $$
    SELECT p.date_of_birth,
           p.gender::text,
           (SELECT a.value #>> '{}' FROM mangaly_profile.profile_attribute a
             WHERE a.profile_id = p.id AND a.category = 'horoscope'
               AND a.attribute_key = 'birth_time' AND a.state = 'value'),
           (SELECT a.value #>> '{}' FROM mangaly_profile.profile_attribute a
             WHERE a.profile_id = p.id AND a.category = 'horoscope'
               AND a.attribute_key = 'birth_place' AND a.state = 'value'),
           (SELECT a.value #>> '{}' FROM mangaly_profile.profile_attribute a
             WHERE a.profile_id = p.id AND a.category = 'horoscope'
               AND a.attribute_key = 'rashi' AND a.state = 'value'),
           (SELECT a.value #>> '{}' FROM mangaly_profile.profile_attribute a
             WHERE a.profile_id = p.id AND a.category = 'horoscope'
               AND a.attribute_key = 'nakshatra' AND a.state = 'value'),
           (SELECT a.value #>> '{}' FROM mangaly_profile.profile_attribute a
             WHERE a.profile_id = p.id AND a.category = 'horoscope'
               AND a.attribute_key = 'manglik' AND a.state = 'value'),
           (SELECT a.value #>> '{}' FROM mangaly_profile.profile_attribute a
             WHERE a.profile_id = p.id AND a.category = 'horoscope'
               AND a.attribute_key = 'matching_required' AND a.state = 'value')
      FROM mangaly_profile.profile p
     WHERE p.account_id = p_account
       AND mangaly_horoscope.can_read(p_account);
$$;
REVOKE ALL ON FUNCTION mangaly_horoscope.birth_inputs(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_horoscope.birth_inputs(uuid) TO mangaly_app;

CREATE OR REPLACE FUNCTION mangaly_horoscope.save_chart(
    p_account           uuid,
    p_inputs_hash       text,
    p_chart             jsonb,
    p_matching_required boolean
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_horoscope, pg_temp
AS $$
BEGIN
    IF NOT mangaly_horoscope.can_read(p_account) THEN
        RAISE EXCEPTION 'not allowed to compute this chart' USING ERRCODE = 'insufficient_privilege';
    END IF;
    INSERT INTO mangaly_horoscope.chart (account_id, inputs_hash, chart, matching_required, computed_at)
    VALUES (p_account, p_inputs_hash, p_chart, p_matching_required, now())
    ON CONFLICT (account_id) DO UPDATE SET
        inputs_hash       = EXCLUDED.inputs_hash,
        chart             = EXCLUDED.chart,
        matching_required = EXCLUDED.matching_required,
        computed_at       = now();
END;
$$;
REVOKE ALL ON FUNCTION mangaly_horoscope.save_chart(uuid, text, jsonb, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_horoscope.save_chart(uuid, text, jsonb, boolean) TO mangaly_app;

-- The two stored charts of a pair, for the candidate `p_viewer` (themselves,
-- or a Home Circle member acting for them with `family_info`) looking at
-- `p_other`. `connected` is whether `p_viewer` holds `candidate_info` on
-- `p_other`'s profile — what acceptance grants — and decides whether the
-- breakdown may be shown. Charts of people `p_viewer` may not read are simply
-- absent.
CREATE OR REPLACE FUNCTION mangaly_horoscope.pair_charts(p_viewer uuid, p_other uuid)
RETURNS TABLE (
    account_id         uuid,
    chart              jsonb,
    inputs_hash        text,
    matching_required  boolean,
    gender             text,
    connected          boolean,
    computed_at        timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = mangaly_horoscope, mangaly_profile, mangaly_authz, pg_temp
AS $$
BEGIN
    IF NOT (mangaly_authz.is_self(p_viewer) OR mangaly_authz.has_scope(p_viewer, 'family_info')) THEN
        RAISE EXCEPTION 'kundli is readable by the candidate or their circle only'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF NOT mangaly_horoscope.can_read(p_other) THEN
        RETURN;
    END IF;
    RETURN QUERY
    SELECT c.account_id,
           c.chart,
           c.inputs_hash,
           c.matching_required,
           p.gender::text,
           (c.account_id = p_viewer) OR EXISTS (
               SELECT 1 FROM mangaly_authz.grant g
                WHERE g.subject_id = p_viewer
                  AND g.target_profile_id = p.id
                  AND g.scope = 'candidate_info'
                  AND g.status = 'active'),
           c.computed_at
      FROM mangaly_horoscope.chart c
      JOIN mangaly_profile.profile p ON p.account_id = c.account_id
     WHERE c.account_id IN (p_viewer, p_other);
END;
$$;
REVOKE ALL ON FUNCTION mangaly_horoscope.pair_charts(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_horoscope.pair_charts(uuid, uuid) TO mangaly_app;
