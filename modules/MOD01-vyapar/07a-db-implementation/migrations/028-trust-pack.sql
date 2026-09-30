-- [Trust pack, 2026-09-30 — VISION-2040 items 1-5, "next 3 builds" #1]
-- Additive and idempotent (safe to run twice). Five parts:
--
--   1. Profession rules (VISION item 5). A per-taxonomy-term config table,
--      not per-member code: advocates (Bar Council of India Rules, Part VI,
--      Chapter II, Rule 36) and architects (Council of Architecture,
--      Architects (Professional Conduct) Regulations 1989) may not advertise
--      or solicit. Their profiles get no promotion, no public reviews or
--      recommendation counts, no ranking boost, no public prices or
--      discounts, and only the fields the councils allow on a website.
--      Chartered accountants (ICAI) may advertise non-assurance services from
--      1 Apr 2026, so they carry a wording note and no restriction. Any
--      promotion already running or queued on a restricted profile is
--      cancelled (reason `profession_rules`) — none existed on the dev DB.
--   2. "Paid on time" (VISION item 2). One question to the PAID person after
--      a contract stage is released or 30 days after being hired; the payer
--      shows "Paid on time: 12 of 13" once 3 people answered. No stars.
--   3. Council-verified badges (VISION item 4). Claimed register numbers
--      with council, status (claimed/verified/expired/failed) and when they
--      were last really checked. Registry lookups are vendor integrations
--      (09a-external-dependencies.md); until then an operator checks by hand
--      through the existing verification queue.
--   4. Human appeal for every restriction (VISION item 3). Operator actions
--      that bypassed the case table (listing suspend, opportunity removal
--      from the review queue) now record a decided case so the member can
--      appeal it; an interim hold (auto-flag, seeker-charge report pause)
--      can be appealed while it is still waiting for a decision.
--   5. `my_restriction_cases()` for the member's "what is restricted and how
--      do I appeal" read.
-- Traces to: FR28, FR30, FR39, FR40, FR41, FR09, FR10, VISION-2040 §3 items 1-5

-- ---------------------------------------------------------------------------
-- 1. Profession rules
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_listings.profession_rules (
  id                       serial PRIMARY KEY,
  term_kind                text NOT NULL CHECK (term_kind IN ('category','capability')),
  term_slug                text NOT NULL,
  profession               text NOT NULL,           -- advocate | architect | chartered_accountant
  regulator                text NOT NULL,           -- shown as-is (a proper name)
  rule_reference           text NOT NULL,
  allow_promotion          boolean NOT NULL DEFAULT true,
  allow_public_reviews     boolean NOT NULL DEFAULT true,
  allow_ranking_boost      boolean NOT NULL DEFAULT true,
  allow_public_prices      boolean NOT NULL DEFAULT true,
  -- NULL: every profile field may be shown. Otherwise the only ListingOut
  -- fields a non-owner sees besides identity, contact and locality.
  permitted_profile_fields text[],
  note_key                 text,                    -- i18n key of an "information only" / wording note
  rules_checked_on         date NOT NULL,
  source_url               text,
  active                   boolean NOT NULL DEFAULT true,
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  UNIQUE (term_kind, term_slug)
);
COMMENT ON TABLE vyapar_listings.profession_rules IS
  '[Trust pack] What a regulated profession may show and buy on Vyapar, per taxonomy term. The most restrictive matching rule wins. Re-check with a lawyer and bump rules_checked_on when a council changes its rules.';

INSERT INTO vyapar_listings.profession_rules
  (term_kind, term_slug, profession, regulator, rule_reference, allow_promotion, allow_public_reviews, allow_ranking_boost,
   allow_public_prices, permitted_profile_fields, note_key, rules_checked_on, source_url)
VALUES
  ('category', 'legal', 'advocate', 'Bar Council of India',
   'Bar Council of India Rules, Part VI, Chapter II, Section IV, Rule 36 (with the 2008 amendment on websites)',
   false, false, false, false,
   ARRAY['name','business_name','categories','capabilities','languages','locality','experience_years','council_credentials','contacts'],
   'profession.note.advocate', DATE '2026-09-30', 'https://www.barcouncilofindia.org/about/professional-standards/rules-on-professional-standards'),
  ('capability', 'architecture', 'architect', 'Council of Architecture',
   'Architects (Professional Conduct) Regulations, 1989, Regulation 2(1)(xiii) and 2(1)(xiv); CoA guidelines on advertisement',
   false, false, false, false,
   ARRAY['name','business_name','categories','capabilities','languages','locality','experience_years','council_credentials','contacts'],
   'profession.note.architect', DATE '2026-09-30', 'https://www.coa.gov.in/index1.php?lang=1&level=0&linkid=26&lid=31'),
  ('category', 'accounting_tax', 'chartered_accountant', 'Institute of Chartered Accountants of India',
   'ICAI Code of Ethics, Clause (6) of Part I of the First Schedule to the CA Act, 1949 (advertisement of non-assurance services permitted from 1 Apr 2026)',
   true, true, true, true, NULL,
   'profession.note.charteredAccountant', DATE '2026-09-30', 'https://www.icai.org/')
ON CONFLICT (term_kind, term_slug) DO NOTHING;

GRANT SELECT ON vyapar_listings.profession_rules TO vyapar_app;

-- Does a listing (by its categories and skills) fall under a rule that
-- forbids promotion? SQL twin of app/services/profession_rules.py, used by
-- the one-time cancellation below and by operators' ad-hoc checks. A skill's
-- parent category counts too (a listing with only `property_law` is legal).
CREATE OR REPLACE FUNCTION vyapar_listings.listing_promotion_forbidden(p_listing_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'vyapar_listings', 'pg_temp'
AS $function$
  WITH l AS (SELECT categories, capabilities FROM vyapar_listings.listings WHERE id = p_listing_id),
  terms AS (
    SELECT 'category'::text AS kind, unnest(l.categories) AS slug FROM l
    UNION SELECT 'capability', unnest(l.capabilities) FROM l
    UNION SELECT 'category', p.slug
      FROM l, vyapar_listings.taxonomy_terms t JOIN vyapar_listings.taxonomy_terms p ON p.id = t.parent_id
     WHERE t.kind = 'capability' AND t.slug = ANY (l.capabilities)
  )
  SELECT EXISTS (SELECT 1 FROM vyapar_listings.profession_rules r JOIN terms ON terms.kind = r.term_kind AND terms.slug = r.term_slug
                  WHERE r.active AND NOT r.allow_promotion);
$function$;
GRANT EXECUTE ON FUNCTION vyapar_listings.listing_promotion_forbidden(uuid) TO vyapar_app;

-- Promotions already bought or queued on a profile whose profession may not
-- advertise are cancelled, never deleted (the order history stays). Rows
-- already cancelled are not touched, so a re-run changes nothing.
UPDATE vyapar_commercial.promotions p
   SET state = 'cancelled', reject_reason = 'profession_rules', updated_at = now()
 WHERE p.target_kind = 'listing'
   AND p.state IN ('draft','awaiting_payment','scheduled','active','paused')
   AND vyapar_listings.listing_promotion_forbidden(p.target_id);

-- ---------------------------------------------------------------------------
-- 2. "Paid on time"
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_reviews.paid_on_time_asks (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_kind    text NOT NULL CHECK (source_kind IN ('milestone','hire')),
  source_id      uuid NOT NULL,                 -- contract_milestones.id or enquiries.id
  payer_id       text NOT NULL,                 -- the poster / client
  payee_id       text NOT NULL,                 -- the person who was paid, the only one asked
  title          text,
  opportunity_id uuid,
  contract_id    uuid,
  asked_at       timestamptz NOT NULL DEFAULT now(),
  answer         boolean,
  answered_at    timestamptz,
  CHECK (payer_id <> payee_id),
  CHECK ((answer IS NULL) = (answered_at IS NULL)),
  UNIQUE (source_kind, source_id)
);
CREATE INDEX IF NOT EXISTS paid_on_time_asks_payer_idx ON vyapar_reviews.paid_on_time_asks (payer_id) WHERE answer IS NOT NULL;
CREATE INDEX IF NOT EXISTS paid_on_time_asks_payee_idx ON vyapar_reviews.paid_on_time_asks (payee_id, asked_at DESC);
ALTER TABLE vyapar_reviews.paid_on_time_asks ENABLE ROW LEVEL SECURITY;
-- Only the paid person reads or answers their own question; the payer never
-- sees who said what (the same anti-retaliation idea as blind reviews). The
-- public count comes from paid_on_time_counts() below.
DROP POLICY IF EXISTS paid_on_time_payee ON vyapar_reviews.paid_on_time_asks;
CREATE POLICY paid_on_time_payee ON vyapar_reviews.paid_on_time_asks
  USING (payee_id = current_setting('vyapar.authz_context', true) OR vyapar_identity.is_operator('moderation'))
  WITH CHECK (payee_id = current_setting('vyapar.authz_context', true));
GRANT SELECT, INSERT, UPDATE ON vyapar_reviews.paid_on_time_asks TO vyapar_app;

-- Who should be asked now: released contract stages, and hires older than
-- p_hire_days whose enquiry has no contract (a contract's stages ask for it).
CREATE OR REPLACE FUNCTION vyapar_reviews.paid_on_time_due(p_hire_days integer, p_limit integer DEFAULT 200)
 RETURNS TABLE(source_kind text, source_id uuid, payer_id text, payee_id text, title text, opportunity_id uuid, contract_id uuid)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'vyapar_reviews', 'pg_temp'
AS $function$
  (SELECT 'milestone'::text, m.id, c.client_member_id, c.provider_member_id, c.title, c.opportunity_id, c.id
     FROM vyapar_contracts.contract_milestones m
     JOIN vyapar_contracts.contracts c ON c.id = m.contract_id
    WHERE m.state = 'released' AND c.client_member_id <> c.provider_member_id
      AND NOT EXISTS (SELECT 1 FROM vyapar_reviews.paid_on_time_asks a WHERE a.source_kind = 'milestone' AND a.source_id = m.id)
    ORDER BY m.released_at NULLS LAST
    LIMIT p_limit)
  UNION ALL
  (SELECT 'hire'::text, e.id, e.provider_id, e.sender_id, o.title, e.opportunity_id, NULL::uuid
     FROM vyapar_enquiries.enquiries e
     JOIN vyapar_opportunities.opportunities o ON o.id = e.opportunity_id
    WHERE e.stage = 'hired' AND e.stage_changed_at <= now() - make_interval(days => p_hire_days)
      AND e.sender_id <> e.provider_id
      AND NOT EXISTS (SELECT 1 FROM vyapar_contracts.contracts c WHERE c.enquiry_id = e.id AND c.state <> 'cancelled')
      AND NOT EXISTS (SELECT 1 FROM vyapar_reviews.paid_on_time_asks a WHERE a.source_kind = 'hire' AND a.source_id = e.id)
    ORDER BY e.stage_changed_at
    LIMIT p_limit);
$function$;

-- Public, aggregate only: how many paid people answered, and how many said yes.
CREATE OR REPLACE FUNCTION vyapar_reviews.paid_on_time_counts(p_members text[])
 RETURNS TABLE(member_id text, answered integer, paid_on_time integer)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'vyapar_reviews', 'pg_temp'
AS $function$
  SELECT a.payer_id, count(*)::int, count(*) FILTER (WHERE a.answer)::int
    FROM vyapar_reviews.paid_on_time_asks a
   WHERE a.payer_id = ANY (p_members) AND a.answer IS NOT NULL
   GROUP BY a.payer_id;
$function$;
GRANT EXECUTE ON FUNCTION vyapar_reviews.paid_on_time_due(integer, integer) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_reviews.paid_on_time_counts(text[]) TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 3. Council credentials
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_listings.council_credentials (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id             uuid NOT NULL REFERENCES vyapar_listings.listings(id) ON DELETE CASCADE,
  member_id              text NOT NULL,
  credential_type        text NOT NULL CHECK (credential_type IN (
                           'icai_membership','medical_council_registration','allied_health_registration',
                           'bar_council_enrolment','coa_registration','digilocker_document')),
  council                text NOT NULL,          -- the register, as the badge names it
  registration_number    text NOT NULL,
  registered_on          date,
  document_uri           text,                   -- DigiLocker document URI (digilocker_document only)
  status                 text NOT NULL DEFAULT 'claimed' CHECK (status IN ('claimed','verified','expired','failed')),
  -- who last looked: dev_stub (nothing was checked), registry (a live council
  -- or DigiLocker lookup), operator (a person checked the public register)
  check_source           text CHECK (check_source IN ('dev_stub','registry','operator')),
  last_attempt_at        timestamptz,            -- any attempt, including the dev stub
  last_checked_at        timestamptz,            -- only a real check (operator or live registry)
  verified_at            timestamptz,
  expires_at             timestamptz,            -- re-checked yearly
  checked_by             text,
  check_note             text CHECK (check_note IS NULL OR char_length(check_note) <= 300),
  verification_record_id uuid REFERENCES vyapar_listings.verification_records(id) ON DELETE SET NULL,
  created_at             timestamptz NOT NULL DEFAULT now(),
  updated_at             timestamptz NOT NULL DEFAULT now(),
  CHECK (char_length(registration_number) BETWEEN 3 AND 60),
  UNIQUE (listing_id, credential_type)
);
CREATE INDEX IF NOT EXISTS council_credentials_member_idx ON vyapar_listings.council_credentials (member_id);
CREATE INDEX IF NOT EXISTS council_credentials_record_idx ON vyapar_listings.council_credentials (verification_record_id);
ALTER TABLE vyapar_listings.council_credentials ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS council_credentials_owner ON vyapar_listings.council_credentials;
CREATE POLICY council_credentials_owner ON vyapar_listings.council_credentials
  USING (member_id = current_setting('vyapar.authz_context', true)
         OR vyapar_identity.is_operator('verification')
         OR coalesce(current_setting('vyapar.service_role', true), '') = 'dispatcher')
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true)
              OR vyapar_identity.is_operator('verification')
              OR coalesce(current_setting('vyapar.service_role', true), '') = 'dispatcher');
-- A claimed or verified register entry is public on a visible profile (the
-- Bar Council itself requires the enrolment number on an advocate's
-- website); failed and expired entries are the owner's only.
DROP POLICY IF EXISTS council_credentials_public_read ON vyapar_listings.council_credentials;
CREATE POLICY council_credentials_public_read ON vyapar_listings.council_credentials FOR SELECT
  USING (status IN ('claimed','verified')
         AND EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.id = listing_id));
GRANT SELECT, INSERT, UPDATE, DELETE ON vyapar_listings.council_credentials TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 4. Appeals for every restriction
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_trust_safety.moderation_cases DROP CONSTRAINT IF EXISTS moderation_cases_source_check;
ALTER TABLE vyapar_trust_safety.moderation_cases ADD CONSTRAINT moderation_cases_source_check
  CHECK (source = ANY (ARRAY['report'::text, 'auto_flag'::text, 'review_dispute'::text, 'operator'::text]));

-- An operator action taken outside the moderation queue (suspend a listing,
-- remove a post from the review queue) is recorded as an already-decided
-- case, so the member sees it in their outcomes and can appeal it.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.record_operator_action(
  p_kind text, p_object_id uuid, p_subject text, p_action text, p_reason text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_trust_safety', 'pg_temp'
AS $function$
DECLARE
  v_operator text := current_setting('vyapar.authz_context', true);
  v_id uuid;
BEGIN
  IF NOT vyapar_identity.is_operator(NULL) THEN RAISE EXCEPTION 'operator_required'; END IF;
  INSERT INTO vyapar_trust_safety.moderation_cases
    (object_kind, object_id, subject_member_id, source, severity, state, primary_reason, distribution_limited,
     target_due_at, action, reason_code, operator_id, decided_at)
  VALUES (p_kind, p_object_id, p_subject, 'operator', 'medium', 'actioned', p_reason, false,
          now(), p_action, p_reason, v_operator, now())
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$function$;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.record_operator_action(text, uuid, text, text, text) TO vyapar_app;

-- Appeals: a decided restrictive action (as before), or an interim hold that
-- is still waiting for a person (an auto-flag, or the seeker-charge report
-- pause) — "a human looks at it" should never have to wait for the queue.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.file_appeal(p_case_id uuid, p_text text, p_evidence_urls text[] DEFAULT '{}'::text[])
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_trust_safety', 'pg_temp'
AS $function$
DECLARE
  v_member text := current_setting('vyapar.authz_context', true);
  v_case vyapar_trust_safety.moderation_cases%ROWTYPE;
  v_reviewer text;
  v_id uuid;
  v_interim boolean;
BEGIN
  SELECT * INTO v_case FROM vyapar_trust_safety.moderation_cases WHERE id = p_case_id;
  IF NOT FOUND OR v_case.subject_member_id IS DISTINCT FROM v_member THEN RAISE EXCEPTION 'case_not_found'; END IF;
  v_interim := v_case.decided_at IS NULL AND v_case.state IN ('open','in_review','escalated')
               AND vyapar_trust_safety.object_is_held(v_case.object_kind, v_case.object_id);
  IF NOT v_interim AND (v_case.decided_at IS NULL OR v_case.action IS NULL OR v_case.action IN ('dismiss','restore')) THEN
    RAISE EXCEPTION 'not_appealable';
  END IF;
  IF now() > coalesce(v_case.decided_at, v_case.created_at) + interval '15 days' THEN RAISE EXCEPTION 'window_closed'; END IF;

  SELECT m.id INTO v_reviewer FROM vyapar_identity.members m
   WHERE m.is_operator AND 'moderation' = ANY (m.operator_permissions) AND m.id IS DISTINCT FROM v_case.operator_id
   ORDER BY m.id LIMIT 1;
  IF v_reviewer IS NULL THEN v_reviewer := v_case.operator_id; END IF;

  INSERT INTO vyapar_trust_safety.appeals (case_id, member_id, text, evidence_urls, reviewer_id)
  VALUES (p_case_id, v_member, p_text, COALESCE(p_evidence_urls, '{}'), v_reviewer) RETURNING id INTO v_id;
  RETURN v_id;
END;
$function$;

-- Is the object currently held back by the platform (not by its owner)?
CREATE OR REPLACE FUNCTION vyapar_trust_safety.object_is_held(p_kind text, p_object_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'vyapar_trust_safety', 'pg_temp'
AS $function$
  SELECT CASE p_kind
    WHEN 'opportunity' THEN EXISTS (SELECT 1 FROM vyapar_opportunities.opportunities o WHERE o.id = p_object_id
                                      AND (o.distribution_limited OR o.state = 'removed' OR (o.state = 'paused' AND o.state_reason IS NOT NULL)))
    WHEN 'listing' THEN EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.id = p_object_id
                                  AND (l.distribution_limited OR l.state = 'suspended' OR (l.state = 'submitted' AND l.state_reason IS NOT NULL)))
    WHEN 'review' THEN EXISTS (SELECT 1 FROM vyapar_reviews.reviews r WHERE r.id = p_object_id AND r.state IN ('hidden','removed'))
    ELSE false END;
$function$;

-- Every case about the caller that restricts something now or did recently:
-- decided restrictive actions and interim holds, with the appeal state.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.my_restriction_cases()
 RETURNS TABLE(case_id uuid, object_kind text, object_id uuid, source text, state text, action text, reason_code text,
               primary_reason text, decided_at timestamptz, created_at timestamptz, appeal_deadline timestamptz,
               appeal_state text, held boolean)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'vyapar_trust_safety', 'pg_temp'
AS $function$
  SELECT c.id, c.object_kind, c.object_id, c.source, c.state, c.action, c.reason_code, c.primary_reason, c.decided_at, c.created_at,
         coalesce(c.decided_at, c.created_at) + interval '15 days', a.state,
         vyapar_trust_safety.object_is_held(c.object_kind, c.object_id)
    FROM vyapar_trust_safety.moderation_cases c
    LEFT JOIN vyapar_trust_safety.appeals a ON a.case_id = c.id AND a.member_id = c.subject_member_id
   WHERE c.subject_member_id = current_setting('vyapar.authz_context', true)
     AND ((c.decided_at IS NOT NULL AND c.action IS NOT NULL AND c.action NOT IN ('dismiss','restore'))
          OR (c.decided_at IS NULL AND c.state IN ('open','in_review','escalated')))
   ORDER BY coalesce(c.decided_at, c.created_at) DESC;
$function$;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.object_is_held(text, uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.my_restriction_cases() TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 6. "Verified business owner" means a business document was checked
-- ---------------------------------------------------------------------------
-- Found while checking Kavita Dhawan's profile: the badge rule was "owns an
-- active_verified listing", so an advocate verified by her Bar Council
-- credential read "Verified business owner". The badge now needs a business
-- document (GST, Udyam, PAN, shop licence) on a profile with a business
-- section, the same test as ListingOut.business_verified. Only that one
-- expression changes; cached badges are recomputed on the next read.
CREATE OR REPLACE FUNCTION vyapar_identity.badge_inputs(p_ids text[])
 RETURNS TABLE(member_id text, member_since timestamp with time zone, verified_business boolean, reviews integer, recommends integer, repeat_hirers integer, answered integer, median_minutes integer)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'vyapar_identity', 'pg_temp'
AS $function$
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
         EXISTS (SELECT 1 FROM vyapar_listings.listings l
                  WHERE l.owner_id = m.id AND l.state = 'active_verified'
                    AND l.verification_state IN ('verified','expiring')
                    AND l.verification_document IN ('gst','udyam','pan','shops_est')
                    AND nullif(l.business_name, '') IS NOT NULL),
         (SELECT count(*)::int FROM vis v WHERE v.subject_member_id = m.id),
         (SELECT count(*)::int FROM vis v WHERE v.subject_member_id = m.id AND v.recommend),
         coalesce((SELECT h.n FROM hirers h WHERE h.provider_id = m.id), 0),
         coalesce((SELECT a.n FROM answered a WHERE a.provider_id = m.id), 0),
         (SELECT a.med FROM answered a WHERE a.provider_id = m.id)
    FROM vyapar_identity.members m
   WHERE m.id = ANY (p_ids) AND NOT m.anonymized AND m.deleted_at IS NULL;
$function$;
UPDATE vyapar_identity.members SET badges_computed_at = NULL WHERE badges_computed_at IS NOT NULL
   AND badges @> '[{"key": "verified_business"}]'::jsonb;

-- ---------------------------------------------------------------------------
-- 7. The hourly trust pass cancels promotions on profiles that now fall under
-- a no-advertising rule (e.g. a member adds "Legal services" to a promoted
-- profile). promotions' WITH CHECK admits only the owner, so the pass uses
-- this narrow function: it can only move live promotions on such profiles to
-- `cancelled` with reason `profession_rules`, and writes the order history.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_commercial.cancel_profession_restricted_promotions()
 RETURNS TABLE(promotion_id uuid, owner_id text, from_state text)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'vyapar_commercial', 'pg_temp'
AS $function$
BEGIN
  IF coalesce(current_setting('vyapar.service_role', true), '') <> 'dispatcher' AND NOT vyapar_identity.is_operator('commercial') THEN
    RAISE EXCEPTION 'dispatcher_or_operator_required';
  END IF;
  RETURN QUERY
  WITH hit AS (
    SELECT p.id, p.owner_id AS owner, p.state AS prev FROM vyapar_commercial.promotions p
     WHERE p.target_kind = 'listing' AND p.state IN ('draft','awaiting_payment','scheduled','active','paused')
       AND vyapar_listings.listing_promotion_forbidden(p.target_id)
     FOR UPDATE
  ), upd AS (
    UPDATE vyapar_commercial.promotions p SET state = 'cancelled', reject_reason = 'profession_rules', updated_at = now()
      FROM hit WHERE p.id = hit.id
    RETURNING p.id, hit.owner, hit.prev
  ), hist AS (
    INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason)
    SELECT 'promotion', upd.id, upd.prev, 'cancelled', 'profession_rules' FROM upd
    RETURNING order_id
  )
  SELECT upd.id, upd.owner, upd.prev FROM upd;
END;
$function$;
GRANT EXECUTE ON FUNCTION vyapar_commercial.cancel_profession_restricted_promotions() TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 8. The post or profile a thread is about, for its two parties, whatever
-- state the post is in now. Found in the trust-pack web pass: once a post
-- closed, expired or was removed, the opportunities RLS hid it from the
-- applicant, so their Requests row and thread read "Untitled". This returns
-- only the title/name and state, and only for threads the caller is a party
-- to, so no other field of a closed post leaks. Works for old rows too (no
-- snapshot needed).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_enquiries.enquiry_targets(p_ids uuid[])
 RETURNS TABLE(enquiry_id uuid, target_kind text, target_title text, target_state text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'vyapar_enquiries', 'pg_temp'
AS $function$
  SELECT e.id,
         CASE WHEN e.opportunity_id IS NOT NULL THEN 'opportunity' ELSE 'listing' END,
         coalesce(o.title, l.name),
         coalesce(o.state, l.state)
    FROM vyapar_enquiries.enquiries e
    LEFT JOIN vyapar_opportunities.opportunities o ON o.id = e.opportunity_id
    LEFT JOIN vyapar_listings.listings l ON l.id = e.listing_id
   WHERE e.id = ANY (p_ids)
     AND current_setting('vyapar.authz_context', true) IN (e.sender_id, e.provider_id);
$function$;
GRANT EXECUTE ON FUNCTION vyapar_enquiries.enquiry_targets(uuid[]) TO vyapar_app;
