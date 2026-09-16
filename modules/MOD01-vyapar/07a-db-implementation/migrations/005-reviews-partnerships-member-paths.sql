-- [TR024/TR025/TR026/TR027/TR028/TR029 gaps, found during Step 9 design of
-- slice 7 by reading the live RLS policies before writing code — fixed
-- forward; 001-initial.sql and 004 are applied history and are not edited.]
--
-- Gap 1 (FR26): partnership_requests WITH CHECK admits only the SENDER, so
--   the recipient could never Accept/Decline/Restrict.
-- Gap 2 (FR21/FR25/FR27): notifications' policy admits an INSERT only for
--   the caller's own member_id, so a member action can never notify the
--   other party of that same interaction (request received, invite, state).
-- Gap 3 (FR27): review_invites is self-only, so closing an interaction could
--   not issue the OTHER party's invite.
-- Gap 4 (FR29): reviews WITH CHECK admits only the author (deliberately, per
--   TR029), so the subject's dispute could not set state='disputed', and
--   moderation_cases is operator-only, so it could not open the FR40 case.
-- Gap 5 (FR28/FR18): members is self-or-operator, so a listing's reputation
--   (reviewer first names, counts incl. "under review", response time from
--   other members' enquiries) and poster names on feed cards were unreadable
--   by ordinary viewers — feed cards were silently rendering blank names.
--
-- Fix: narrow SECURITY DEFINER functions, same pattern as 002-004. Caller
-- identity always comes from vyapar.authz_context, never a parameter; each
-- function checks the caller's role in the specific interaction itself and
-- returns only what its one job needs.
SET search_path TO pg_temp;

-- Gap 5a. Public names only for members who already have a public presence
-- (an active listing/opportunity or a published review) — not a directory of
-- every member id.
CREATE OR REPLACE FUNCTION vyapar_identity.public_names(p_ids text[])
RETURNS TABLE(id text, display_name text, first_name text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_identity, pg_temp AS $$
  SELECT m.id, m.display_name, split_part(m.display_name, ' ', 1)
    FROM vyapar_identity.members m
   WHERE m.id = ANY (p_ids) AND NOT m.anonymized AND m.deleted_at IS NULL
     AND (EXISTS (SELECT 1 FROM vyapar_listings.listings l WHERE l.owner_id = m.id AND l.state IN ('active_unverified','active_verified'))
       OR EXISTS (SELECT 1 FROM vyapar_opportunities.opportunities o WHERE o.poster_id = m.id AND o.state IN ('active','paused','stale'))
       OR EXISTS (SELECT 1 FROM vyapar_reviews.reviews r WHERE r.author_id = m.id AND r.state = 'published'));
$$;

-- Gap 2. Notify the other party of an interaction the caller is part of.
-- Title/body arrive pre-translated for en/hi/te; the recipient's own language
-- is chosen here (the caller cannot read it). A block silences it.
CREATE OR REPLACE FUNCTION vyapar_integration.notify_interaction_party(
  p_interaction_kind text, p_interaction_id uuid, p_recipient text, p_template text,
  p_texts jsonb, p_link text, p_idem text
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_integration, pg_temp AS $$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  v_ok boolean := false;
  v_lang text;
  v_id uuid;
BEGIN
  IF p_interaction_kind = 'enquiry' THEN
    SELECT true INTO v_ok FROM vyapar_enquiries.enquiries e
     WHERE e.id = p_interaction_id AND v_caller IN (e.sender_id, e.provider_id) AND p_recipient IN (e.sender_id, e.provider_id);
  ELSIF p_interaction_kind = 'partnership' THEN
    SELECT true INTO v_ok FROM vyapar_enquiries.partnership_requests p
     WHERE p.id = p_interaction_id AND v_caller IN (p.sender_id, p.recipient_id) AND p_recipient IN (p.sender_id, p.recipient_id);
  END IF;
  IF NOT coalesce(v_ok, false) THEN RAISE EXCEPTION 'not_a_party'; END IF;
  IF p_recipient <> v_caller AND vyapar_enquiries.is_blocked(p_recipient, v_caller) THEN RETURN false; END IF;

  SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = p_recipient;
  v_lang := coalesce(v_lang, 'en');
  INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
  VALUES (p_recipient, p_template, p_template,
          coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
          coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
          p_link, jsonb_build_object('interaction_kind', p_interaction_kind, 'interaction_id', p_interaction_id), p_idem)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$$;

-- Gap 1. The whole FR26 state machine, one place.
CREATE OR REPLACE FUNCTION vyapar_enquiries.partnership_transition(p_id uuid, p_action text)
RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  r vyapar_enquiries.partnership_requests%ROWTYPE;
  v_new text;
BEGIN
  SELECT * INTO r FROM vyapar_enquiries.partnership_requests WHERE id = p_id FOR UPDATE;
  IF NOT FOUND OR v_caller NOT IN (r.sender_id, r.recipient_id) THEN RAISE EXCEPTION 'not_found'; END IF;

  IF p_action IN ('accept', 'decline', 'restrict') THEN
    IF v_caller <> r.recipient_id THEN RAISE EXCEPTION 'recipient_only'; END IF;
    IF NOT (r.state = 'pending' OR (p_action = 'restrict' AND r.state = 'accepted')) THEN RAISE EXCEPTION 'invalid_transition'; END IF;
    v_new := CASE p_action WHEN 'accept' THEN 'accepted' WHEN 'decline' THEN 'declined' ELSE 'restricted' END;
  ELSIF p_action = 'withdraw' THEN
    IF v_caller <> r.sender_id THEN RAISE EXCEPTION 'sender_only'; END IF;
    IF r.state <> 'pending' THEN RAISE EXCEPTION 'invalid_transition'; END IF;
    v_new := 'withdrawn';
  ELSIF p_action = 'close' THEN
    IF r.state <> 'accepted' THEN RAISE EXCEPTION 'invalid_transition'; END IF;
    v_new := 'closed';
  ELSE
    RAISE EXCEPTION 'invalid_action';
  END IF;

  UPDATE vyapar_enquiries.partnership_requests
     SET state = v_new,
         decided_at = CASE WHEN p_action IN ('accept','decline','restrict') THEN now() ELSE decided_at END,
         updated_at = now()
   WHERE id = p_id;
  RETURN v_new;
END;
$$;

-- Gap 5b. "Responds in ~X" (FR28, from FR23) — an aggregate only, never rows;
-- needs at least 3 answered enquiries so one fast reply isn't a claim.
CREATE OR REPLACE FUNCTION vyapar_enquiries.response_minutes(p_member_ids text[])
RETURNS TABLE(member_id text, minutes int)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
  SELECT e.provider_id,
         (percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM e.first_reply_at - e.created_at)) / 60)::int
    FROM vyapar_enquiries.enquiries e
   WHERE e.provider_id = ANY (p_member_ids) AND e.first_reply_at IS NOT NULL
     AND e.created_at > now() - interval '180 days'
   GROUP BY e.provider_id
  HAVING count(*) >= 3;
$$;

-- Gap 3. Invite each party once when an interaction qualifies (FR27):
-- enquiry Resolved/Closed with a non-system message from BOTH sides, or a
-- partnership Accepted then Closed. Qualification is re-derived here from
-- the source rows, never trusted from the caller.
CREATE OR REPLACE FUNCTION vyapar_reviews.issue_invites(p_kind text, p_id uuid)
RETURNS TABLE(member_id text, subject_member_id text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_reviews, pg_temp AS $$
#variable_conflict use_column
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  v_a text; v_b text;          -- a = requester side, b = provider/recipient side
  v_la uuid; v_lb uuid;        -- listing reviewed by a (b's listing) / by b (a's listing)
  v_ok boolean := false;
BEGIN
  IF p_kind = 'enquiry' THEN
    SELECT e.sender_id, e.provider_id, e.listing_id, NULL::uuid,
           e.state IN ('resolved','closed')
           AND EXISTS (SELECT 1 FROM vyapar_enquiries.enquiry_messages m WHERE m.enquiry_id = e.id AND m.sender_id = e.sender_id AND NOT m.system_note)
           AND EXISTS (SELECT 1 FROM vyapar_enquiries.enquiry_messages m WHERE m.enquiry_id = e.id AND m.sender_id = e.provider_id AND NOT m.system_note)
      INTO v_a, v_b, v_la, v_lb, v_ok
      FROM vyapar_enquiries.enquiries e WHERE e.id = p_id;
  ELSIF p_kind = 'partnership' THEN
    SELECT p.sender_id, p.recipient_id, p.recipient_listing_id, p.sender_listing_id,
           p.state = 'closed' AND p.decided_at IS NOT NULL
      INTO v_a, v_b, v_la, v_lb, v_ok
      FROM vyapar_enquiries.partnership_requests p WHERE p.id = p_id;
  END IF;
  IF v_a IS NULL OR v_caller NOT IN (v_a, v_b) THEN RAISE EXCEPTION 'not_a_party'; END IF;
  IF NOT coalesce(v_ok, false) THEN RETURN; END IF;

  RETURN QUERY
  WITH ins AS (
    INSERT INTO vyapar_reviews.review_invites (interaction_kind, interaction_id, member_id, subject_listing_id, subject_member_id, expires_at)
    VALUES (p_kind, p_id, v_a, v_la, v_b, now() + interval '30 days'),
           (p_kind, p_id, v_b, v_lb, v_a, now() + interval '30 days')
    ON CONFLICT (interaction_kind, interaction_id, member_id) DO NOTHING
    RETURNING review_invites.member_id AS mid, review_invites.subject_member_id AS sid
  )
  SELECT ins.mid, ins.sid FROM ins;
END;
$$;

-- Anti-retaliation reveal rule (Upwork's double-blind feedback, adapted):
-- a review stays out of the subject's sight — and out of public counts, so
-- it can't be inferred — while the subject still holds an unused, unexpired
-- invite for the same interaction. It becomes visible once they have
-- reviewed back or their 30-day window closes.
CREATE OR REPLACE FUNCTION vyapar_reviews.is_revealed(p_kind text, p_interaction_id uuid, p_subject text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_reviews, pg_temp AS $$
  SELECT NOT EXISTS (
    SELECT 1 FROM vyapar_reviews.review_invites i
     WHERE i.interaction_kind = p_kind AND i.interaction_id = p_interaction_id
       AND i.member_id = p_subject AND i.used_at IS NULL AND i.expires_at > now());
$$;

-- Gap 5c. FR28 counts, live from reviews (never a stored score). Disputed
-- rows are excluded from counts and reported only as a number under review.
CREATE OR REPLACE FUNCTION vyapar_reviews.reputation_for_listings(p_ids uuid[])
RETURNS TABLE(listing_id uuid, interactions int, recommends int, top_tags text[], under_review int)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_reviews, pg_temp AS $$
  WITH visible AS (
    SELECT r.subject_listing_id, r.state, r.recommend, r.tags
      FROM vyapar_reviews.reviews r
     WHERE r.subject_listing_id = ANY (p_ids)
       AND vyapar_reviews.is_revealed(r.interaction_kind, r.interaction_id, r.subject_member_id)
  )
  SELECT l.id,
         (SELECT count(*) FROM visible v WHERE v.subject_listing_id = l.id AND v.state = 'published')::int,
         (SELECT count(*) FROM visible v WHERE v.subject_listing_id = l.id AND v.state = 'published' AND v.recommend)::int,
         ARRAY(SELECT t FROM visible v, unnest(v.tags) t
                WHERE v.subject_listing_id = l.id AND v.state = 'published'
                GROUP BY t ORDER BY count(*) DESC, t LIMIT 3),
         (SELECT count(*) FROM visible v WHERE v.subject_listing_id = l.id AND v.state = 'disputed')::int
    FROM unnest(p_ids) AS l(id);
$$;

-- Gap 5d. Review rows for a listing: published+revealed for everyone; a
-- disputed row only to its subject ("Under review" chip) and author; a
-- hidden row only to its author (FR29 "visible to author only").
-- Reviewer shown as first name only (FR27).
CREATE OR REPLACE FUNCTION vyapar_reviews.reviews_for_listing(p_listing_id uuid)
RETURNS TABLE(id uuid, recommend boolean, tags text[], comment text, created_at timestamptz, state text,
              author_first_name text, is_subject boolean, is_author boolean, disputed boolean)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = vyapar_reviews, pg_temp AS $$
  SELECT r.id, r.recommend, r.tags, r.comment, r.created_at, r.state,
         CASE WHEN m.anonymized THEN NULL ELSE split_part(m.display_name, ' ', 1) END,
         r.subject_member_id = current_setting('vyapar.authz_context', true),
         r.author_id = current_setting('vyapar.authz_context', true),
         EXISTS (SELECT 1 FROM vyapar_reviews.review_disputes d WHERE d.review_id = r.id)
    FROM vyapar_reviews.reviews r
    LEFT JOIN vyapar_identity.members m ON m.id = r.author_id
   WHERE r.subject_listing_id = p_listing_id
     AND (   (r.state = 'published' AND vyapar_reviews.is_revealed(r.interaction_kind, r.interaction_id, r.subject_member_id))
          OR (r.state = 'disputed' AND r.subject_member_id = current_setting('vyapar.authz_context', true))
          OR (r.author_id = current_setting('vyapar.authz_context', true) AND r.state IN ('published','disputed','hidden')))
   ORDER BY r.created_at DESC
   LIMIT 20;
$$;

-- Gap 4. FR29 dispute: subject only, once, from Published; opens the FR40
-- moderation case (source review_dispute; case subject = the review's
-- author, whose content is being judged).
CREATE OR REPLACE FUNCTION vyapar_reviews.open_dispute(p_review_id uuid, p_reason text)
RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_reviews, pg_temp AS $$
DECLARE
  v_caller text := current_setting('vyapar.authz_context', true);
  r vyapar_reviews.reviews%ROWTYPE;
  v_sev text := CASE WHEN p_reason = 'abusive' THEN 'high' ELSE 'medium' END;
  v_case uuid;
BEGIN
  SELECT * INTO r FROM vyapar_reviews.reviews WHERE id = p_review_id FOR UPDATE;
  IF NOT FOUND OR r.subject_member_id IS DISTINCT FROM v_caller THEN RAISE EXCEPTION 'not_subject'; END IF;
  IF EXISTS (SELECT 1 FROM vyapar_reviews.review_disputes d WHERE d.review_id = p_review_id) THEN RAISE EXCEPTION 'already_disputed'; END IF;
  IF r.state <> 'published' THEN RAISE EXCEPTION 'not_disputable'; END IF;

  INSERT INTO vyapar_trust_safety.moderation_cases (object_kind, object_id, subject_member_id, source, severity, primary_reason, target_due_at)
  VALUES ('review', p_review_id, r.author_id, 'review_dispute', v_sev, p_reason, now() + vyapar_trust_safety.target_interval(v_sev))
  RETURNING id INTO v_case;
  INSERT INTO vyapar_reviews.review_disputes (review_id, disputer_id, reason, case_id) VALUES (p_review_id, v_caller, p_reason, v_case);
  UPDATE vyapar_reviews.reviews SET state = 'disputed' WHERE id = p_review_id;
  RETURN v_case;
END;
$$;

-- Replaces 004's version (fix-forward): adds 'limit' for reviews (FR29
-- Hidden), records the dispute outcome, and cascades FR27's "reviews tied
-- to a removed thread are hidden" when an enquiry/partnership is hidden.
CREATE OR REPLACE FUNCTION vyapar_trust_safety.set_object_state(p_kind text, p_object_id uuid, p_op text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_trust_safety, pg_temp AS $$
DECLARE v_outcome text;
BEGIN
  IF NOT vyapar_identity.is_operator('moderation') THEN RAISE EXCEPTION 'moderation_permission_required'; END IF;
  IF p_op NOT IN ('hide','restore','limit') THEN RAISE EXCEPTION 'invalid_op'; END IF;
  IF p_kind IN ('enquiry','partnership') THEN
    IF p_kind = 'enquiry' THEN
      UPDATE vyapar_enquiries.enquiries SET state = CASE WHEN p_op = 'restore' THEN 'open' ELSE 'restricted' END, updated_at = now()
       WHERE id = p_object_id AND (p_op <> 'restore' OR state = 'restricted');
    ELSE
      UPDATE vyapar_enquiries.partnership_requests SET state = CASE WHEN p_op = 'restore' THEN 'pending' ELSE 'restricted' END, updated_at = now()
       WHERE id = p_object_id AND (p_op <> 'restore' OR state = 'restricted');
    END IF;
    IF p_op = 'restore' THEN
      UPDATE vyapar_reviews.reviews SET state = 'published' WHERE interaction_kind = p_kind AND interaction_id = p_object_id AND state = 'hidden';
    ELSE
      UPDATE vyapar_reviews.reviews SET state = 'hidden' WHERE interaction_kind = p_kind AND interaction_id = p_object_id AND state IN ('published','disputed');
    END IF;
  ELSIF p_kind = 'review' THEN
    v_outcome := CASE p_op WHEN 'hide' THEN 'removed' WHEN 'limit' THEN 'hidden' ELSE 'published' END;
    UPDATE vyapar_reviews.reviews SET state = v_outcome WHERE id = p_object_id;
    UPDATE vyapar_reviews.review_disputes SET outcome = v_outcome, decided_at = now() WHERE review_id = p_object_id AND decided_at IS NULL;
  END IF;
END;
$$;

GRANT EXECUTE ON FUNCTION vyapar_identity.public_names(text[]) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_integration.notify_interaction_party(text, uuid, text, text, jsonb, text, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_enquiries.partnership_transition(uuid, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_enquiries.response_minutes(text[]) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_reviews.issue_invites(text, uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_reviews.is_revealed(text, uuid, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_reviews.reputation_for_listings(uuid[]) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_reviews.reviews_for_listing(uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_reviews.open_dispute(uuid, text) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_trust_safety.set_object_state(text, uuid, text) TO vyapar_app;
