-- [IMP-B — contact actions, seeker protection, count badges, service
-- packages, discovery filters and saved searches] Backend workstream B,
-- 2026-09-28. Additive only: no existing column, constraint value or
-- function signature is removed or renamed.
--
-- 1. Contact preferences (poster control over how they are reached). A
--    member's own defaults live on vyapar_identity.members; a listing may
--    override any of them (NULL = inherit). Contact attempts ("I am calling
--    X now") are recorded per enquiry so the callee's daily cap works and
--    both parties can see "you called X on ...". Phone numbers themselves
--    are never stored here: the number still comes from
--    vyapar_listings.contacts_for_viewer() after acceptance, exactly as
--    before (TR002/TR024).
-- 2. "Nobody charges job seekers." Report reason 'asked_for_money' is added
--    (values only appended). Two independent reports on one opportunity
--    pause it and raise the case to High; that write crosses RLS (a
--    reporter cannot pause someone else's post, or read other reporters'
--    rows), so it is one narrow SECURITY DEFINER function under the same
--    constraints as 004/013 (exact id, minimal projection, checks inside).
-- 3. Count-based badges (FR28: counts, never a star score). The inputs are
--    counts other members cannot read directly (enquiries are party-only,
--    members are self-only), gathered by one SECURITY DEFINER reader in the
--    same style as 013's poster_summary(). The result is cached on the
--    member row (badges + badges_computed_at) through a narrow writer, so a
--    viewer's session never needs UPDATE on another member's row.
-- 4. Tiered service packages on listings (basic/standard/premium, max 3).
--    Enquiries gain a nullable package_id; sub_choice 'request_package' is
--    documented here (sub_choice has no CHECK; existing values untouched).
-- 5. Saved searches with optional alerts, read by the notification pass.
-- 6. Access-token scope 'contracts:write' for workstream D's contracts API.
-- Traces to: FR02, FR18, FR19, FR21, FR22, FR24, FR28, FR39, FR40, TR002,
--   TR018, TR019, TR021, TR024, TR028, TR039, TR040, SP019, SP024, SP040

-- ---------------------------------------------------------------------------
-- 1. Contact preferences
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_identity.members
  ADD COLUMN IF NOT EXISTS call_hours_start   time,
  ADD COLUMN IF NOT EXISTS call_hours_end     time,
  ADD COLUMN IF NOT EXISTS call_days          text[] NOT NULL DEFAULT '{}'
    CHECK (call_days <@ ARRAY['mon','tue','wed','thu','fri','sat','sun']::text[]),
  ADD COLUMN IF NOT EXISTS max_calls_per_day  int CHECK (max_calls_per_day IS NULL OR max_calls_per_day BETWEEN 1 AND 500),
  ADD COLUMN IF NOT EXISTS calls_from         text NOT NULL DEFAULT 'anyone' CHECK (calls_from IN ('anyone','matching_only')),
  ADD COLUMN IF NOT EXISTS whatsapp_ok        boolean NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS call_ok            boolean NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS badges             jsonb NOT NULL DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS badges_computed_at timestamptz;
COMMENT ON COLUMN vyapar_identity.members.call_days IS '[IMP-B] Empty array = every day. Values mon..sun.';
COMMENT ON COLUMN vyapar_identity.members.max_calls_per_day IS '[IMP-B] NULL = unlimited. Counted from vyapar_enquiries.contact_attempts per IST day.';
COMMENT ON COLUMN vyapar_identity.members.badges IS '[IMP-B/FR28] On-read cache of count-based badges: [{key, earned_at}]. Recomputed when badges_computed_at is older than the configured max age.';

-- Listing-level overrides: NULL means "use the owner''s member setting".
ALTER TABLE vyapar_listings.listings
  ADD COLUMN IF NOT EXISTS call_hours_start  time,
  ADD COLUMN IF NOT EXISTS call_hours_end    time,
  ADD COLUMN IF NOT EXISTS call_days         text[]
    CHECK (call_days IS NULL OR call_days <@ ARRAY['mon','tue','wed','thu','fri','sat','sun']::text[]),
  ADD COLUMN IF NOT EXISTS max_calls_per_day int CHECK (max_calls_per_day IS NULL OR max_calls_per_day BETWEEN 1 AND 500),
  ADD COLUMN IF NOT EXISTS calls_from        text CHECK (calls_from IS NULL OR calls_from IN ('anyone','matching_only')),
  ADD COLUMN IF NOT EXISTS whatsapp_ok       boolean,
  ADD COLUMN IF NOT EXISTS call_ok           boolean;

-- Another member's row is RLS-private; the callee's preferences are the
-- one thing a caller needs from it, so this returns exactly those columns.
CREATE OR REPLACE FUNCTION vyapar_identity.contact_preferences_for(p_member_id text)
RETURNS TABLE(member_id text, call_hours_start time, call_hours_end time, call_days text[],
              max_calls_per_day int, calls_from text, whatsapp_ok boolean, call_ok boolean,
              capabilities text[], language text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_identity, pg_temp AS $$
  SELECT m.id, m.call_hours_start, m.call_hours_end, m.call_days, m.max_calls_per_day,
         m.calls_from, m.whatsapp_ok, m.call_ok, m.capabilities, m.language
    FROM vyapar_identity.members m
   WHERE m.id = p_member_id AND NOT m.anonymized AND m.deleted_at IS NULL
   LIMIT 1;
$$;
REVOKE ALL ON FUNCTION vyapar_identity.contact_preferences_for(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_identity.contact_preferences_for(text) TO vyapar_app;

CREATE TABLE IF NOT EXISTS vyapar_enquiries.contact_attempts (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  enquiry_id  uuid NOT NULL REFERENCES vyapar_enquiries.enquiries(id) ON DELETE CASCADE,
  caller_id   text NOT NULL,
  callee_id   text NOT NULL,
  channel     text NOT NULL CHECK (channel IN ('call','whatsapp')),
  at          timestamptz NOT NULL DEFAULT now(),
  CHECK (caller_id <> callee_id)
);
CREATE INDEX IF NOT EXISTS contact_attempts_callee_idx ON vyapar_enquiries.contact_attempts (callee_id, at DESC);
CREATE INDEX IF NOT EXISTS contact_attempts_enquiry_idx ON vyapar_enquiries.contact_attempts (enquiry_id, at DESC);
COMMENT ON TABLE vyapar_enquiries.contact_attempts IS '[IMP-B/FR24] Who tapped call/WhatsApp to whom, from which accepted enquiry, when. No phone numbers. Both parties read; only the caller writes.';

ALTER TABLE vyapar_enquiries.contact_attempts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contact_attempts_parties ON vyapar_enquiries.contact_attempts;
CREATE POLICY contact_attempts_parties ON vyapar_enquiries.contact_attempts
  USING (caller_id = current_setting('vyapar.authz_context', true)
      OR callee_id = current_setting('vyapar.authz_context', true)
      OR vyapar_identity.is_operator('moderation'))
  WITH CHECK (caller_id = current_setting('vyapar.authz_context', true));
GRANT SELECT, INSERT ON vyapar_enquiries.contact_attempts TO vyapar_app;

-- The daily cap counts every caller''s attempts to one callee, which a
-- single caller cannot see under the policy above. Count only, per IST day.
CREATE OR REPLACE FUNCTION vyapar_enquiries.contact_attempts_today(p_callee text, p_channel text, p_offset_minutes int)
RETURNS int
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
  SELECT count(*)::int
    FROM vyapar_enquiries.contact_attempts a
   WHERE a.callee_id = p_callee
     AND (p_channel IS NULL OR a.channel = p_channel)
     AND (a.at + make_interval(mins => p_offset_minutes))::date = (now() + make_interval(mins => p_offset_minutes))::date;
$$;
REVOKE ALL ON FUNCTION vyapar_enquiries.contact_attempts_today(text, text, int) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_enquiries.contact_attempts_today(text, text, int) TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 2. Seeker protection: report reason 'asked_for_money', two-report pause
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_trust_safety.reports DROP CONSTRAINT IF EXISTS reports_reason_check;
ALTER TABLE vyapar_trust_safety.reports ADD CONSTRAINT reports_reason_check
  CHECK (reason IN ('scam','fake','impersonation','harassment','discrimination','spam','stale','privacy','other','asked_for_money'));

-- Replaces 004''s version (fix-forward): 'asked_for_money' opens the case at
-- Medium so ONE report never limits a post by itself; the second
-- independent report (below) is what pauses it and raises it to High.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.severity_for_reason(p_reason text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE WHEN p_reason IN ('scam','impersonation','harassment','discrimination') THEN 'high'
              WHEN p_reason IN ('fake','privacy','asked_for_money') THEN 'medium' ELSE 'low' END;
$$;

-- Called by the reporter''s own request right after file_report(). Counts
-- DISTINCT reporters with reason 'asked_for_money' on the open case for
-- this opportunity; at p_threshold or more it pauses the opportunity
-- (state_reason 'seeker_charge_reports'), raises the case to High with
-- distribution limited, and tells the poster in their own language
-- (p_texts = {"en": {"title","body"}, "hi": ..., "te": ...}). Idempotent:
-- an already-paused post is left as it is.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.apply_seeker_charge_reports(
  p_opportunity_id uuid, p_threshold int, p_texts jsonb
) RETURNS TABLE(reporters int, paused boolean, case_id uuid)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_trust_safety, pg_temp AS $$
DECLARE
  v_case uuid;
  v_poster text;
  v_state text;
  v_title text;
  v_n int := 0;
  v_paused boolean := false;
  v_lang text;
BEGIN
  SELECT c.id INTO v_case FROM vyapar_trust_safety.moderation_cases c
   WHERE c.object_kind = 'opportunity' AND c.object_id = p_opportunity_id AND c.state IN ('open','in_review','escalated')
   ORDER BY c.created_at LIMIT 1;
  IF v_case IS NULL THEN RETURN QUERY SELECT 0, false, NULL::uuid; RETURN; END IF;

  SELECT count(DISTINCT r.reporter_id)::int INTO v_n FROM vyapar_trust_safety.reports r
   WHERE r.case_id = v_case AND r.reason = 'asked_for_money';

  IF v_n >= p_threshold THEN
    SELECT o.poster_id, o.state, o.title INTO v_poster, v_state, v_title
      FROM vyapar_opportunities.opportunities o WHERE o.id = p_opportunity_id FOR UPDATE;
    IF v_state IN ('active','stale') THEN
      UPDATE vyapar_opportunities.opportunities
         SET state = 'paused', state_reason = 'seeker_charge_reports', distribution_limited = true, updated_at = now()
       WHERE id = p_opportunity_id;
      v_paused := true;
      SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = v_poster;
      v_lang := coalesce(v_lang, 'en');
      INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
      VALUES (v_poster, 'opportunityPausedSeekerCharge', 'opportunityPausedSeekerCharge',
              coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
              coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
              '/opportunities/' || p_opportunity_id::text,
              jsonb_build_object('opportunity_id', p_opportunity_id, 'case_id', v_case),
              'seeker_charge_paused:' || p_opportunity_id::text)
      ON CONFLICT (idempotency_key) DO NOTHING;
    END IF;
    UPDATE vyapar_trust_safety.moderation_cases c
       SET severity = CASE WHEN c.severity = 'critical' THEN c.severity ELSE 'high' END,
           distribution_limited = true,
           primary_reason = 'asked_for_money',
           target_due_at = LEAST(c.target_due_at, now() + vyapar_trust_safety.target_interval('high')),
           updated_at = now()
     WHERE c.id = v_case;
  END IF;
  RETURN QUERY SELECT v_n, v_paused, v_case;
END;
$$;
REVOKE ALL ON FUNCTION vyapar_trust_safety.apply_seeker_charge_reports(uuid, int, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.apply_seeker_charge_reports(uuid, int, jsonb) TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 3. Count-based badges
-- ---------------------------------------------------------------------------
-- The raw counts behind every badge, for a batch of members. Reviews are the
-- revealed, published ones (the same rule reputation_for_listings uses);
-- "hires" are enquiries the member answered that reached resolved/closed;
-- response time is the 180-day median of first replies.
CREATE OR REPLACE FUNCTION vyapar_identity.badge_inputs(p_ids text[])
RETURNS TABLE(member_id text, member_since timestamptz, verified_business boolean,
              reviews int, recommends int, repeat_hirers int, answered int, median_minutes int)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_identity, pg_temp AS $$
  WITH vis AS (
    SELECT r.subject_member_id, r.recommend
      FROM vyapar_reviews.reviews r
     WHERE r.subject_member_id = ANY (p_ids) AND r.state = 'published'
       AND vyapar_reviews.is_revealed(r.interaction_kind, r.interaction_id, r.subject_member_id)
  ), answered AS (
    SELECT e.provider_id, count(*)::int AS n,
           (percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM e.first_reply_at - e.created_at)) / 60)::int AS med
      FROM vyapar_enquiries.enquiries e
     WHERE e.provider_id = ANY (p_ids) AND e.first_reply_at IS NOT NULL AND e.created_at > now() - interval '180 days'
     GROUP BY e.provider_id
  ), hirers AS (
    SELECT h.provider_id, count(*)::int AS n FROM (
      SELECT e.provider_id, e.sender_id FROM vyapar_enquiries.enquiries e
       WHERE e.provider_id = ANY (p_ids) AND e.state IN ('resolved','closed')
       GROUP BY e.provider_id, e.sender_id HAVING count(*) >= 2
    ) h GROUP BY h.provider_id
  )
  SELECT m.id, m.created_at,
         EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.owner_id = m.id AND l.state = 'active_verified'),
         (SELECT count(*)::int FROM vis v WHERE v.subject_member_id = m.id),
         (SELECT count(*)::int FROM vis v WHERE v.subject_member_id = m.id AND v.recommend),
         coalesce((SELECT h.n FROM hirers h WHERE h.provider_id = m.id), 0),
         coalesce((SELECT a.n FROM answered a WHERE a.provider_id = m.id), 0),
         (SELECT a.med FROM answered a WHERE a.provider_id = m.id)
    FROM vyapar_identity.members m
   WHERE m.id = ANY (p_ids) AND NOT m.anonymized AND m.deleted_at IS NULL;
$$;
REVOKE ALL ON FUNCTION vyapar_identity.badge_inputs(text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_identity.badge_inputs(text[]) TO vyapar_app;

-- The cache read: badges plus whether they are still fresh.
CREATE OR REPLACE FUNCTION vyapar_identity.member_badges(p_ids text[], p_max_age_seconds int)
RETURNS TABLE(member_id text, badges jsonb, computed_at timestamptz, fresh boolean)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_identity, pg_temp AS $$
  SELECT m.id, m.badges, m.badges_computed_at,
         m.badges_computed_at IS NOT NULL AND m.badges_computed_at > now() - make_interval(secs => p_max_age_seconds)
    FROM vyapar_identity.members m
   WHERE m.id = ANY (p_ids) AND NOT m.anonymized AND m.deleted_at IS NULL;
$$;
REVOKE ALL ON FUNCTION vyapar_identity.member_badges(text[], int) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_identity.member_badges(text[], int) TO vyapar_app;

-- The cache write. Only known keys, each with an earned_at, nothing else.
CREATE OR REPLACE FUNCTION vyapar_identity.store_badges(p_member_id text, p_badges jsonb)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_identity, pg_temp AS $$
BEGIN
  IF jsonb_typeof(p_badges) <> 'array' THEN RAISE EXCEPTION 'badges_not_array'; END IF;
  IF EXISTS (
    SELECT 1 FROM jsonb_array_elements(p_badges) b
     WHERE NOT (b ? 'key') OR NOT (b ? 'earned_at')
        OR NOT (b->>'key' = ANY (ARRAY['responds_fast','reliable','rising','top_recommended','verified_business','repeat_hires']))
  ) THEN RAISE EXCEPTION 'unknown_badge'; END IF;
  UPDATE vyapar_identity.members SET badges = p_badges, badges_computed_at = now() WHERE id = p_member_id;
END;
$$;
REVOKE ALL ON FUNCTION vyapar_identity.store_badges(text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_identity.store_badges(text, jsonb) TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 4. Tiered service packages
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_listings.listing_packages (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id     uuid NOT NULL REFERENCES vyapar_listings.listings(id) ON DELETE CASCADE,
  tier           text NOT NULL CHECK (tier IN ('basic','standard','premium')),
  name           text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 80),
  name_hi        text,
  name_te        text,
  description    text CHECK (description IS NULL OR char_length(description) <= 600),
  description_hi text,
  description_te text,
  price_paise    bigint NOT NULL CHECK (price_paise >= 0),
  delivery_days  int CHECK (delivery_days IS NULL OR delivery_days BETWEEN 0 AND 365),
  revisions      int CHECK (revisions IS NULL OR revisions BETWEEN 0 AND 99),
  includes       text[] NOT NULL DEFAULT '{}' CHECK (cardinality(includes) <= 12),
  sort           smallint NOT NULL DEFAULT 0,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (listing_id, tier)                     -- at most one of each tier, so at most 3 per listing
);
CREATE INDEX IF NOT EXISTS listing_packages_listing_idx ON vyapar_listings.listing_packages (listing_id, sort);
COMMENT ON TABLE vyapar_listings.listing_packages IS '[IMP-B] Up to three priced tiers per listing (Fiverr/Upwork project-catalog style). Localizable text stored as given plus optional _hi/_te.';

ALTER TABLE vyapar_listings.listing_packages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS listing_packages_visibility ON vyapar_listings.listing_packages;
CREATE POLICY listing_packages_visibility ON vyapar_listings.listing_packages
  USING (EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.id = listing_packages.listing_id
                   AND (l.state IN ('active_unverified','active_verified')
                        OR l.owner_id = current_setting('vyapar.authz_context', true)
                        OR vyapar_identity.is_operator('content'))))
  WITH CHECK (EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.id = listing_packages.listing_id
                        AND l.owner_id = current_setting('vyapar.authz_context', true)));
GRANT SELECT, INSERT, UPDATE, DELETE ON vyapar_listings.listing_packages TO vyapar_app;

-- Enquiry sub_choice values (documented, no CHECK): existing free-text values
-- stay valid; 'request_package' is the new value a package request uses,
-- together with the package it refers to.
ALTER TABLE vyapar_enquiries.enquiries ADD COLUMN IF NOT EXISTS package_id uuid;
COMMENT ON COLUMN vyapar_enquiries.enquiries.package_id IS '[IMP-B] vyapar_listings.listing_packages(id), no cross-schema FK. Set when sub_choice = ''request_package''.';

-- ---------------------------------------------------------------------------
-- 5. Saved searches
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_opportunities.saved_searches (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id       text NOT NULL,
  query           text NOT NULL DEFAULT '' CHECK (char_length(query) <= 200),
  filters         jsonb NOT NULL DEFAULT '{}',
  alert           boolean NOT NULL DEFAULT false,
  last_alerted_at timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS saved_searches_member_idx ON vyapar_opportunities.saved_searches (member_id, created_at DESC);
CREATE INDEX IF NOT EXISTS saved_searches_alert_idx ON vyapar_opportunities.saved_searches (alert) WHERE alert;
COMMENT ON TABLE vyapar_opportunities.saved_searches IS '[IMP-B/FR21] A member''s saved opportunity searches; alert=true lets the strong-match pass notify on new matches under the same daily cap.';

ALTER TABLE vyapar_opportunities.saved_searches ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS saved_searches_self ON vyapar_opportunities.saved_searches;
-- The alert pass runs as the dispatcher (operator context) and must be able
-- to stamp last_alerted_at on a member's row; nothing else may write another
-- member's saved searches.
CREATE POLICY saved_searches_self ON vyapar_opportunities.saved_searches
  USING (member_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator(NULL))
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true)
              OR current_setting('vyapar.service_role', true) = 'dispatcher');
GRANT SELECT, INSERT, UPDATE, DELETE ON vyapar_opportunities.saved_searches TO vyapar_app;


-- ---------------------------------------------------------------------------
-- 6. Access-token scope 'contracts:write' (workstream D's contracts API;
--    app/integrations/identity/scopes.py maps /v1/contracts writes to it).
--    Values only appended.
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_integration.access_tokens DROP CONSTRAINT IF EXISTS access_tokens_scopes_check;
ALTER TABLE vyapar_integration.access_tokens ADD CONSTRAINT access_tokens_scopes_check CHECK (
  cardinality(scopes) > 0 AND scopes <@ ARRAY[
    'read','opportunities:write','listings:write','enquiries:write',
    'reviews:write','partnerships:write','notifications:write','contracts:write'
  ]::text[]);
