-- [Backend A, 2026-09-30 — owner decision] ONE Vyapar profile per member.
--
-- Owner, seeing Meena's hub say "3 Profiles": "how do a person have 3
-- profiles ... each user will get one profile." A member is one person on
-- the ForKhatri identity; Vyapar gives them exactly one profile. A business
-- is an optional SECTION of that profile, not a second profile.
--
-- Lower-risk shape, chosen on purpose: the profile IS the existing
-- `vyapar_listings.listings` row (same table, same id). Every reference that
-- already points at a listing id (verification records, reviews and review
-- invites, packages, contacts, promotions, impressions, enquiries,
-- partnership requests, opportunities, campaigns, entitlements, workspace
-- members, contracts, moderation cases, reports, saved/viewed rows) keeps
-- pointing at a valid id; nothing is re-keyed except where two listings of
-- one member are merged. The business section is four columns on that row:
--   business_name, business_headline, business_description  (the business)
--   merged_from jsonb  (what was folded in, for the record)
-- Business verification (GST/Udyam) stays where it is: verification_state /
-- verification_records on the same row. `kind` keeps its meaning for every
-- existing reader: 'business' when the profile has a business section,
-- 'professional' otherwise, so the Businesses directory still works.
-- `name` becomes the PERSON's name (the identity display name), so a card
-- reads "Meena Sahni · Meena's Oven".
--
-- Suspended listings are moderation history: they are never folded into a
-- live profile (that would launder a suspension) and are not "the profile";
-- the one-profile rule counts live states only (draft, submitted,
-- active_unverified, active_verified). The API refuses a new profile while
-- any non-archived listing exists.
--
-- Dry run first: `SELECT * FROM vyapar_listings.profile_consolidation_plan();`
-- lists, per member, the surviving id and every listing that will be merged
-- into it, before anything changes. The migration then applies exactly that
-- plan. Idempotent: a merged listing is archived, so a re-run finds nothing
-- left to merge; every other step is IF NOT EXISTS / CREATE OR REPLACE.
-- Traces to: FR01, FR03, FR04, FR16, FR44, TR001, TR050, owner 2026-09-30

-- ---------------------------------------------------------------------------
-- 1. Business section on the profile row
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_listings.listings
  ADD COLUMN IF NOT EXISTS business_name        text,
  ADD COLUMN IF NOT EXISTS business_headline    text,
  ADD COLUMN IF NOT EXISTS business_description text,
  ADD COLUMN IF NOT EXISTS merged_from          jsonb NOT NULL DEFAULT '[]';

-- Search finds a profile by the person's name AND the business name.
CREATE OR REPLACE FUNCTION vyapar_listings.listings_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.search_tsv :=
    setweight(to_tsvector('simple', coalesce(NEW.name,'') || ' ' || coalesce(NEW.business_name,'')), 'A') ||
    setweight(to_tsvector('simple', array_to_string(NEW.categories || NEW.capabilities || NEW.unmapped_labels, ' ')), 'B') ||
    setweight(to_tsvector('simple', coalesce(NEW.description,'') || ' ' || coalesce(NEW.business_headline,'') || ' ' || coalesce(NEW.business_description,'')), 'C') ||
    setweight(to_tsvector('simple', coalesce(NEW.locality,'')), 'C');
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- 2. The identity is the source of truth for name and phone. ensure_member()
--    only ever inserted; a changed ForKhatri display name or phone never
--    reached Vyapar, so prefill could be stale. The dev stub passes the id
--    as the name and no phone, which never overwrites real values.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_identity.ensure_member(
  p_member_id text, p_display_name text, p_phone text, p_language text
) RETURNS void
LANGUAGE sql SECURITY DEFINER
SET search_path = vyapar_identity, pg_temp
AS $$
  INSERT INTO vyapar_identity.members (id, display_name, phone, language)
  VALUES (p_member_id, p_display_name, p_phone, coalesce(p_language, 'en'))
  ON CONFLICT (id) DO UPDATE SET
    display_name = CASE WHEN EXCLUDED.display_name IS NOT NULL AND EXCLUDED.display_name <> EXCLUDED.id
                        THEN EXCLUDED.display_name ELSE vyapar_identity.members.display_name END,
    phone = COALESCE(EXCLUDED.phone, vyapar_identity.members.phone),
    synced_at = now(), updated_at = now();
$$;

-- ---------------------------------------------------------------------------
-- 3. Dry run: the consolidation plan
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_listings.profile_consolidation_plan()
RETURNS TABLE(owner_id text, survivor_id uuid, survivor_name text, merged_id uuid, merged_name text, merged_kind text, merged_state text)
LANGUAGE sql STABLE AS $$
  WITH live AS (
    SELECT l.*,
           (SELECT count(*) FROM vyapar_enquiries.enquiries e WHERE e.listing_id = l.id)
         + (SELECT count(*) FROM vyapar_reviews.reviews r WHERE r.subject_listing_id = l.id) AS history
      FROM vyapar_listings.listings l
     WHERE l.state IN ('draft','submitted','active_unverified','active_verified')
  ), ranked AS (
    SELECT live.*,
           row_number() OVER (PARTITION BY live.owner_id ORDER BY
             (live.verification_state IN ('verified','expiring')) DESC,
             CASE live.state WHEN 'active_verified' THEN 0 WHEN 'active_unverified' THEN 1 WHEN 'submitted' THEN 2 ELSE 3 END,
             live.history DESC,
             live.created_at ASC, live.id) AS rnk,
           count(*) OVER (PARTITION BY live.owner_id) AS n
      FROM live
  )
  SELECT s.owner_id, s.id, s.name, m.id, m.name, m.kind, m.state
    FROM ranked s JOIN ranked m ON m.owner_id = s.owner_id AND m.rnk > 1
   WHERE s.rnk = 1 AND s.n > 1
   ORDER BY s.owner_id, m.rnk;
$$;
COMMENT ON FUNCTION vyapar_listings.profile_consolidation_plan() IS
  '[026] Dry run of the one-profile consolidation: survivor per member and the listings merged into it. Empty once consolidated.';

-- ---------------------------------------------------------------------------
-- 4. Consolidate (applies exactly the plan above)
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  g record;
  s vyapar_listings.listings%ROWTYPE;
  b vyapar_listings.listings%ROWTYPE;
  p vyapar_listings.listings%ROWTYPE;
  loser uuid;
  losers uuid[];
BEGIN
  FOR g IN SELECT survivor_id, array_agg(merged_id) AS merged FROM vyapar_listings.profile_consolidation_plan() GROUP BY survivor_id LOOP
    losers := g.merged;
    SELECT * INTO s FROM vyapar_listings.listings WHERE id = g.survivor_id;

    -- The business part comes from the survivor when it is a business, else
    -- from the best business listing merged into it.
    b := NULL;
    IF s.kind = 'business' THEN
      b := s;
    ELSE
      SELECT * INTO b FROM vyapar_listings.listings
       WHERE id = ANY(losers) AND kind = 'business'
       ORDER BY (verification_state IN ('verified','expiring')) DESC, (state = 'active_verified') DESC, created_at LIMIT 1;
    END IF;
    -- The person part comes from a real (non-draft) professional listing.
    p := NULL;
    IF s.kind = 'professional' THEN
      p := s;
    ELSE
      SELECT * INTO p FROM vyapar_listings.listings
       WHERE id = ANY(losers) AND kind = 'professional' AND state <> 'draft'
       ORDER BY (state = 'active_verified') DESC, (state = 'active_unverified') DESC, created_at LIMIT 1;
    END IF;

    UPDATE vyapar_listings.listings t SET
      business_name        = COALESCE(t.business_name, b.name),
      business_headline    = COALESCE(t.business_headline, b.headline),
      business_description = COALESCE(t.business_description, b.description),
      headline             = CASE WHEN p.id IS NOT NULL AND p.id <> t.id THEN COALESCE(p.headline, t.headline) ELSE t.headline END,
      description          = CASE WHEN p.id IS NOT NULL AND p.id <> t.id THEN COALESCE(p.description, t.description) ELSE t.description END,
      availability         = COALESCE(p.availability, t.availability),
      experience_years     = (SELECT max(x.experience_years) FROM vyapar_listings.listings x WHERE x.id = t.id OR (x.id = ANY(losers) AND x.state <> 'draft')),
      categories           = ARRAY(SELECT DISTINCT unnest(x.categories) FROM vyapar_listings.listings x WHERE x.id = t.id OR (x.id = ANY(losers) AND x.state <> 'draft')),
      capabilities         = ARRAY(SELECT DISTINCT unnest(x.capabilities) FROM vyapar_listings.listings x WHERE x.id = t.id OR (x.id = ANY(losers) AND x.state <> 'draft')),
      languages            = ARRAY(SELECT DISTINCT unnest(x.languages) FROM vyapar_listings.listings x WHERE x.id = t.id OR (x.id = ANY(losers) AND x.state <> 'draft')),
      evidence_links       = ARRAY(SELECT DISTINCT unnest(x.evidence_links) FROM vyapar_listings.listings x WHERE x.id = t.id OR (x.id = ANY(losers) AND x.state <> 'draft')),
      services             = COALESCE((SELECT jsonb_agg(DISTINCT e) FROM vyapar_listings.listings x, jsonb_array_elements(x.services) e
                                        WHERE x.id = t.id OR (x.id = ANY(losers) AND x.state <> 'draft')), '[]'::jsonb),
      merged_from          = t.merged_from || COALESCE((SELECT jsonb_agg(jsonb_build_object('id', x.id, 'name', x.name, 'kind', x.kind, 'headline', x.headline, 'state', x.state))
                                                          FROM vyapar_listings.listings x WHERE x.id = ANY(losers)), '[]'::jsonb),
      kind                 = CASE WHEN COALESCE(t.business_name, b.name) IS NOT NULL THEN 'business' ELSE 'professional' END
     WHERE t.id = s.id;

    FOREACH loser IN ARRAY losers LOOP
      -- contacts: keep the survivor's, add only channels/values it lacks
      DELETE FROM vyapar_listings.listing_contacts c WHERE c.listing_id = loser
        AND EXISTS (SELECT 1 FROM vyapar_listings.listing_contacts k WHERE k.listing_id = s.id AND k.channel = c.channel AND k.value = c.value);
      UPDATE vyapar_listings.listing_contacts SET listing_id = s.id WHERE listing_id = loser;
      -- packages: one per tier; the survivor's tier wins
      DELETE FROM vyapar_listings.listing_packages pk WHERE pk.listing_id = loser
        AND EXISTS (SELECT 1 FROM vyapar_listings.listing_packages k WHERE k.listing_id = s.id AND k.tier = pk.tier);
      UPDATE vyapar_listings.listing_packages SET listing_id = s.id WHERE listing_id = loser;
      -- saved / viewed: merge per member
      INSERT INTO vyapar_listings.member_listing (member_id, listing_id, saved_at, viewed_at)
        SELECT member_id, s.id, saved_at, viewed_at FROM vyapar_listings.member_listing WHERE listing_id = loser
      ON CONFLICT (member_id, listing_id) DO UPDATE SET
        saved_at = COALESCE(vyapar_listings.member_listing.saved_at, EXCLUDED.saved_at),
        viewed_at = GREATEST(vyapar_listings.member_listing.viewed_at, EXCLUDED.viewed_at);
      DELETE FROM vyapar_listings.member_listing WHERE listing_id = loser;
      DELETE FROM vyapar_listings.otp_challenges WHERE listing_id = loser;
      UPDATE vyapar_listings.verification_records SET listing_id = s.id WHERE listing_id = loser;
      -- enquiries: one open enquiry per sender per target; a duplicate open
      -- thread to the merged listing is closed, never silently dropped
      UPDATE vyapar_enquiries.enquiries e SET state = 'closed', state_reason = 'merged_duplicate', updated_at = now()
       WHERE e.listing_id = loser AND e.state NOT IN ('resolved','closed','withdrawn')
         AND EXISTS (SELECT 1 FROM vyapar_enquiries.enquiries k WHERE k.listing_id = s.id AND k.sender_id = e.sender_id
                      AND k.state NOT IN ('resolved','closed','withdrawn'));
      UPDATE vyapar_enquiries.enquiries SET listing_id = s.id WHERE listing_id = loser;
      UPDATE vyapar_enquiries.partnership_requests SET sender_listing_id = s.id WHERE sender_listing_id = loser;
      UPDATE vyapar_enquiries.partnership_requests SET recipient_listing_id = s.id WHERE recipient_listing_id = loser;
      UPDATE vyapar_opportunities.opportunities SET listing_id = s.id WHERE listing_id = loser;
      UPDATE vyapar_reviews.reviews SET subject_listing_id = s.id WHERE subject_listing_id = loser;
      UPDATE vyapar_reviews.review_invites SET subject_listing_id = s.id WHERE subject_listing_id = loser;
      UPDATE vyapar_commercial.promotions SET target_id = s.id WHERE target_kind = 'listing' AND target_id = loser;
      UPDATE vyapar_commercial.impressions SET target_id = s.id WHERE target_kind = 'listing' AND target_id = loser;
      UPDATE vyapar_commercial.campaigns SET listing_id = s.id::text WHERE listing_id = loser::text;
      UPDATE vyapar_commercial.entitlements SET listing_id = s.id::text WHERE listing_id = loser::text;
      UPDATE vyapar_commercial.workspace_members SET listing_id = s.id::text WHERE listing_id = loser::text;
      UPDATE vyapar_contracts.contracts SET provider_listing_id = s.id WHERE provider_listing_id = loser;
      UPDATE vyapar_trust_safety.moderation_cases SET object_id = s.id WHERE object_kind = 'listing' AND object_id = loser;
      UPDATE vyapar_trust_safety.reports SET object_id = s.id WHERE object_kind = 'listing' AND object_id = loser;
      UPDATE vyapar_analytics.analytics_events SET object_id = s.id::text WHERE object_id = loser::text;
      -- the merged listing itself: archived, pointing at its survivor
      UPDATE vyapar_listings.listings SET state = 'archived', state_reason = 'merged_into:' || s.id, discoverable = false WHERE id = loser;
    END LOOP;
  END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- 5. The profile's name is the person's (identity display name). A business
--    listing's own name moves to business_name. Skipped for members whose
--    identity name is still their id (the dev stub) and where the new name
--    would collide with another row of the same member (owner,name,locality).
-- ---------------------------------------------------------------------------
UPDATE vyapar_listings.listings l SET
  business_name = CASE WHEN l.kind = 'business' THEN COALESCE(l.business_name, l.name) ELSE l.business_name END,
  headline = CASE WHEN l.kind = 'professional' AND l.headline IS NULL AND position(' — ' IN l.name) > 0
                  THEN split_part(l.name, ' — ', 2) ELSE l.headline END,
  name = m.display_name
  FROM vyapar_identity.members m
 WHERE m.id = l.owner_id
   AND l.state IN ('draft','submitted','active_unverified','active_verified')
   AND m.display_name IS NOT NULL AND m.display_name <> m.id
   AND l.name <> m.display_name
   AND NOT EXISTS (SELECT 1 FROM vyapar_listings.listings x
                    WHERE x.owner_id = l.owner_id AND x.id <> l.id AND x.name = m.display_name AND x.locality = l.locality);

-- ---------------------------------------------------------------------------
-- 6. One live profile per member, enforced by the database
-- ---------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS listings_one_profile_per_owner
  ON vyapar_listings.listings (owner_id)
  WHERE state IN ('draft','submitted','active_unverified','active_verified');

-- ---------------------------------------------------------------------------
-- 7. "Use my current location": the nearest locality Vyapar already knows
--    (from profiles, opportunities and members that carry coordinates),
--    within 15 km. Returns an area name and the area's centre only — never
--    whose row it came from. SECURITY DEFINER because member rows are
--    private; the projection is aggregate place names, per
--    MODULE-ARCHITECTURE-STANDARD §4's escape-hatch constraints.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_listings.nearest_locality(p_lat double precision, p_lng double precision)
RETURNS TABLE(locality text, lat double precision, lng double precision, distance_km double precision)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_listings, pg_temp AS $$
  WITH places AS (
    SELECT trim(locality) AS name, lat, lng FROM vyapar_listings.listings
     WHERE lat IS NOT NULL AND lng IS NOT NULL AND coalesce(trim(locality), '') <> '' AND state <> 'archived'
    UNION ALL
    SELECT trim(location), lat, lng FROM vyapar_opportunities.opportunities
     WHERE lat IS NOT NULL AND lng IS NOT NULL AND coalesce(trim(location), '') <> ''
    UNION ALL
    SELECT trim(locality), lat, lng FROM vyapar_identity.members
     WHERE lat IS NOT NULL AND lng IS NOT NULL AND coalesce(trim(locality), '') <> ''
  ), centres AS (
    SELECT min(name) AS name, avg(lat) AS lat, avg(lng) AS lng FROM places GROUP BY lower(name)
  )
  SELECT c.name, c.lat, c.lng, vyapar_platform.distance_km(p_lat, p_lng, c.lat, c.lng) AS d
    FROM centres c
   WHERE p_lat BETWEEN -90 AND 90 AND p_lng BETWEEN -180 AND 180
     AND vyapar_platform.distance_km(p_lat, p_lng, c.lat, c.lng) <= 15
   ORDER BY d
   LIMIT 1;
$$;
REVOKE ALL ON FUNCTION vyapar_listings.nearest_locality(double precision, double precision) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_listings.nearest_locality(double precision, double precision) TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 8. [2026-09-30, second pass] Workspaces after consolidation: one member,
--    at most one workspace, on the surviving profile. Section 4 already
--    re-points entitlements, workspace members and campaigns from merged
--    listings to the survivor; here any duplicates that creates are retired
--    (never deleted: payments stay attached to their entitlement rows).
--    Idempotent.
-- ---------------------------------------------------------------------------
-- One open plan per profile: the one that runs longest stays, others close.
UPDATE vyapar_commercial.entitlements e SET state = 'cancelled', updated_at = now()
 WHERE e.state IN ('awaiting_payment','active','paused')
   AND EXISTS (SELECT 1 FROM vyapar_commercial.entitlements k
                WHERE k.listing_id = e.listing_id AND k.id <> e.id AND k.state IN ('awaiting_payment','active','paused')
                  AND (CASE k.state WHEN 'active' THEN 0 WHEN 'paused' THEN 1 ELSE 2 END,
                       -extract(epoch FROM coalesce(k.renews_at, k.created_at)), k.id::text)
                    < (CASE e.state WHEN 'active' THEN 0 WHEN 'paused' THEN 1 ELSE 2 END,
                       -extract(epoch FROM coalesce(e.renews_at, e.created_at)), e.id::text));
-- One seat per person per workspace: the strongest role stays, others expire.
UPDATE vyapar_commercial.workspace_members w SET state = 'expired'
 WHERE w.state IN ('pending','active') AND w.member_id IS NOT NULL
   AND EXISTS (SELECT 1 FROM vyapar_commercial.workspace_members k
                WHERE k.listing_id = w.listing_id AND k.member_id = w.member_id AND k.id <> w.id AND k.state IN ('pending','active')
                  AND ((k.state = 'active')::int, (k.role = 'admin')::int, k.id::text) > ((w.state = 'active')::int, (w.role = 'admin')::int, w.id::text));
