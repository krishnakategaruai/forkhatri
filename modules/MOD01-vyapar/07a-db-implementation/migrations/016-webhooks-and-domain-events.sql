-- [IMP37 — Refactor B: outbound webhooks] External systems subscribe to
-- Vyapar's domain events and receive signed HTTP deliveries.
--
-- Event source is the EXISTING transactional outbox (MODULE-ARCHITECTURE-
-- STANDARD §6, app/outbox.py). Before this migration the outbox only
-- carried operator-side events (opportunity.queue_decided, taxonomy.changed)
-- — the member-facing happenings an integration actually cares about
-- (an opportunity going live, an enquiry arriving, a reply, a review) were
-- never written to it. They are added here as AFTER triggers on the owning
-- tables, so:
--   * the event row commits in the same transaction as the state change it
--     describes (the outbox guarantee), whichever code path made the change
--     — web app, agent token, operator tool or background job — with no
--     change to any router or service;
--   * payloads carry identifiers and states only, never message bodies,
--     phone numbers or other personal data. A receiver that needs detail
--     calls the API with its own access token, where RLS decides again.
--   * `audience` lists the member ids the event concerns; a member's
--     subscription only ever receives events whose audience includes them.
--     Operator subscriptions (all_events) receive everything, including the
--     pre-existing operator events that carry no audience.
--
-- Two schemas that emit domain events had no outbox table of their own
-- (vyapar_enquiries, vyapar_reviews). Each gets one, same shape and same
-- RLS as the three existing ones, so no schema writes into another's table.
--
-- Webhook tables live in vyapar_integration. The signing secret is stored
-- encrypted (AES-GCM, application-layer key), never in plaintext, and shown
-- to the member exactly once at creation.
-- Traces to: REFACTOR-PLAN.md §B, FR52 (integration bridges), TR052

-- ---------------------------------------------------------------------------
-- 1. Outbox tables for the two schemas that lacked one
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_enquiries.outbox_event (
  id           bigserial PRIMARY KEY,
  event_type   text NOT NULL,
  payload      jsonb NOT NULL,
  published_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS vyapar_reviews.outbox_event (
  id           bigserial PRIMARY KEY,
  event_type   text NOT NULL,
  payload      jsonb NOT NULL,
  published_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE vyapar_enquiries.outbox_event ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outbox_insert_any ON vyapar_enquiries.outbox_event;
CREATE POLICY outbox_insert_any ON vyapar_enquiries.outbox_event FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS outbox_select_dispatcher ON vyapar_enquiries.outbox_event;
CREATE POLICY outbox_select_dispatcher ON vyapar_enquiries.outbox_event FOR SELECT
  USING (current_setting('vyapar.service_role', true) = 'dispatcher');
DROP POLICY IF EXISTS outbox_update_dispatcher ON vyapar_enquiries.outbox_event;
CREATE POLICY outbox_update_dispatcher ON vyapar_enquiries.outbox_event FOR UPDATE
  USING (current_setting('vyapar.service_role', true) = 'dispatcher');

ALTER TABLE vyapar_reviews.outbox_event ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outbox_insert_any ON vyapar_reviews.outbox_event;
CREATE POLICY outbox_insert_any ON vyapar_reviews.outbox_event FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS outbox_select_dispatcher ON vyapar_reviews.outbox_event;
CREATE POLICY outbox_select_dispatcher ON vyapar_reviews.outbox_event FOR SELECT
  USING (current_setting('vyapar.service_role', true) = 'dispatcher');
DROP POLICY IF EXISTS outbox_update_dispatcher ON vyapar_reviews.outbox_event;
CREATE POLICY outbox_update_dispatcher ON vyapar_reviews.outbox_event FOR UPDATE
  USING (current_setting('vyapar.service_role', true) = 'dispatcher');

GRANT SELECT, INSERT, UPDATE ON vyapar_enquiries.outbox_event, vyapar_reviews.outbox_event TO vyapar_app;
GRANT USAGE, SELECT ON SEQUENCE vyapar_enquiries.outbox_event_id_seq, vyapar_reviews.outbox_event_id_seq TO vyapar_app;

-- ---------------------------------------------------------------------------
-- 2. Domain-event triggers (identifiers and states only)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vyapar_opportunities.emit_opportunity_event() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_opportunities, pg_temp AS $$
DECLARE
  v_type text;
  v_prev text := CASE WHEN TG_OP = 'UPDATE' THEN OLD.state END;
BEGIN
  IF TG_OP = 'UPDATE' AND NEW.state IS NOT DISTINCT FROM OLD.state THEN
    RETURN NULL;
  END IF;
  IF NEW.state = 'active' THEN
    v_type := CASE WHEN v_prev IS NULL OR v_prev IN ('draft', 'pending_review') THEN 'opportunity.published'
                   ELSE 'opportunity.reactivated' END;
  ELSIF TG_OP = 'UPDATE' AND NEW.state IN ('paused', 'stale', 'expired', 'closed', 'removed') THEN
    v_type := 'opportunity.' || NEW.state;
  ELSE
    RETURN NULL;
  END IF;
  INSERT INTO vyapar_opportunities.outbox_event (event_type, payload) VALUES (v_type, jsonb_build_object(
    'id', NEW.id, 'poster_id', NEW.poster_id, 'listing_id', NEW.listing_id, 'type', NEW.type,
    'state', NEW.state, 'previous_state', v_prev, 'audience', jsonb_build_array(NEW.poster_id)));
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS opportunities_emit_event ON vyapar_opportunities.opportunities;
CREATE TRIGGER opportunities_emit_event AFTER INSERT OR UPDATE OF state ON vyapar_opportunities.opportunities
  FOR EACH ROW EXECUTE FUNCTION vyapar_opportunities.emit_opportunity_event();

CREATE OR REPLACE FUNCTION vyapar_listings.emit_listing_event() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_listings, pg_temp AS $$
DECLARE
  v_prev text := CASE WHEN TG_OP = 'UPDATE' THEN OLD.state END;
  v_live boolean := NEW.state IN ('active_unverified', 'active_verified');
  v_was_live boolean := TG_OP = 'UPDATE' AND OLD.state IN ('active_unverified', 'active_verified');
  v_payload jsonb := jsonb_build_object('id', NEW.id, 'owner_id', NEW.owner_id, 'kind', NEW.kind,
    'state', NEW.state, 'previous_state', v_prev, 'verification_state', NEW.verification_state,
    'audience', jsonb_build_array(NEW.owner_id));
BEGIN
  IF v_live AND NOT v_was_live THEN
    INSERT INTO vyapar_listings.outbox_event (event_type, payload) VALUES ('listing.published', v_payload);
  ELSIF TG_OP = 'UPDATE' AND NEW.state IS DISTINCT FROM OLD.state AND NEW.state IN ('suspended', 'archived') THEN
    INSERT INTO vyapar_listings.outbox_event (event_type, payload) VALUES ('listing.' || NEW.state, v_payload);
  END IF;
  IF TG_OP = 'UPDATE' AND NEW.verification_state IS DISTINCT FROM OLD.verification_state
     AND NEW.verification_state IN ('verified', 'revoked', 'expired') THEN
    INSERT INTO vyapar_listings.outbox_event (event_type, payload)
      VALUES ('listing.verification_' || NEW.verification_state, v_payload);
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS listings_emit_event ON vyapar_listings.listings;
CREATE TRIGGER listings_emit_event AFTER INSERT OR UPDATE OF state, verification_state ON vyapar_listings.listings
  FOR EACH ROW EXECUTE FUNCTION vyapar_listings.emit_listing_event();

CREATE OR REPLACE FUNCTION vyapar_enquiries.emit_enquiry_event() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES ('enquiry.received', jsonb_build_object(
      'id', NEW.id, 'sender_id', NEW.sender_id, 'provider_id', NEW.provider_id, 'listing_id', NEW.listing_id,
      'opportunity_id', NEW.opportunity_id, 'action_type', NEW.action_type, 'state', NEW.state,
      'audience', jsonb_build_array(NEW.provider_id)));
  ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
    INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES ('enquiry.state_changed', jsonb_build_object(
      'id', NEW.id, 'sender_id', NEW.sender_id, 'provider_id', NEW.provider_id, 'state', NEW.state,
      'previous_state', OLD.state, 'audience', jsonb_build_array(NEW.sender_id, NEW.provider_id)));
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS enquiries_emit_event ON vyapar_enquiries.enquiries;
CREATE TRIGGER enquiries_emit_event AFTER INSERT OR UPDATE OF state ON vyapar_enquiries.enquiries
  FOR EACH ROW EXECUTE FUNCTION vyapar_enquiries.emit_enquiry_event();

CREATE OR REPLACE FUNCTION vyapar_enquiries.emit_enquiry_message_event() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
DECLARE
  v_enq vyapar_enquiries.enquiries%ROWTYPE;
  v_recipient text;
BEGIN
  IF NEW.system_note THEN
    RETURN NULL;
  END IF;
  SELECT * INTO v_enq FROM vyapar_enquiries.enquiries WHERE id = NEW.enquiry_id;
  IF NOT FOUND THEN
    RETURN NULL;
  END IF;
  -- The opening message of an enquiry is already announced by enquiry.received.
  IF NOT EXISTS (SELECT 1 FROM vyapar_enquiries.enquiry_messages m
                  WHERE m.enquiry_id = NEW.enquiry_id AND m.id <> NEW.id AND NOT m.system_note) THEN
    RETURN NULL;
  END IF;
  v_recipient := CASE WHEN NEW.sender_id = v_enq.sender_id THEN v_enq.provider_id ELSE v_enq.sender_id END;
  INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES (
    CASE WHEN NEW.sender_id = v_enq.provider_id THEN 'enquiry.replied' ELSE 'enquiry.message_received' END,
    jsonb_build_object('id', NEW.enquiry_id, 'message_id', NEW.id, 'sender_id', NEW.sender_id,
      'recipient_id', v_recipient, 'audience', jsonb_build_array(v_recipient)));
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS enquiry_messages_emit_event ON vyapar_enquiries.enquiry_messages;
CREATE TRIGGER enquiry_messages_emit_event AFTER INSERT ON vyapar_enquiries.enquiry_messages
  FOR EACH ROW EXECUTE FUNCTION vyapar_enquiries.emit_enquiry_message_event();

CREATE OR REPLACE FUNCTION vyapar_enquiries.emit_partnership_event() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.state = 'draft' THEN
      RETURN NULL;
    END IF;
    INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES ('partnership.requested', jsonb_build_object(
      'id', NEW.id, 'sender_id', NEW.sender_id, 'recipient_id', NEW.recipient_id,
      'sender_listing_id', NEW.sender_listing_id, 'recipient_listing_id', NEW.recipient_listing_id,
      'state', NEW.state, 'audience', jsonb_build_array(NEW.recipient_id)));
  ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
    INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES ('partnership.' || NEW.state, jsonb_build_object(
      'id', NEW.id, 'sender_id', NEW.sender_id, 'recipient_id', NEW.recipient_id, 'state', NEW.state,
      'previous_state', OLD.state, 'audience', jsonb_build_array(NEW.sender_id, NEW.recipient_id)));
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS partnership_requests_emit_event ON vyapar_enquiries.partnership_requests;
CREATE TRIGGER partnership_requests_emit_event AFTER INSERT OR UPDATE OF state ON vyapar_enquiries.partnership_requests
  FOR EACH ROW EXECUTE FUNCTION vyapar_enquiries.emit_partnership_event();

CREATE OR REPLACE FUNCTION vyapar_reviews.emit_review_event() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_reviews, pg_temp AS $$
DECLARE
  v_audience jsonb := CASE WHEN NEW.subject_member_id IS NULL THEN jsonb_build_array(NEW.author_id)
                           ELSE jsonb_build_array(NEW.subject_member_id, NEW.author_id) END;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.state <> 'published' THEN
      RETURN NULL;
    END IF;
    INSERT INTO vyapar_reviews.outbox_event (event_type, payload) VALUES ('review.published', jsonb_build_object(
      'id', NEW.id, 'author_id', NEW.author_id, 'subject_member_id', NEW.subject_member_id,
      'subject_listing_id', NEW.subject_listing_id, 'recommend', NEW.recommend, 'state', NEW.state,
      'audience', v_audience));
  ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
    INSERT INTO vyapar_reviews.outbox_event (event_type, payload) VALUES ('review.' || NEW.state, jsonb_build_object(
      'id', NEW.id, 'author_id', NEW.author_id, 'subject_member_id', NEW.subject_member_id,
      'subject_listing_id', NEW.subject_listing_id, 'state', NEW.state, 'previous_state', OLD.state,
      'audience', v_audience));
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS reviews_emit_event ON vyapar_reviews.reviews;
CREATE TRIGGER reviews_emit_event AFTER INSERT OR UPDATE OF state ON vyapar_reviews.reviews
  FOR EACH ROW EXECUTE FUNCTION vyapar_reviews.emit_review_event();

-- ---------------------------------------------------------------------------
-- 3. Webhook subscriptions, deliveries, fan-out cursors
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vyapar_integration.webhook_subscriptions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id       text NOT NULL,
  url             text NOT NULL CHECK (url ~ '^https?://' AND char_length(url) <= 2000),
  description     text CHECK (description IS NULL OR char_length(description) <= 200),
  event_types     text[] NOT NULL CHECK (cardinality(event_types) > 0),
  all_events      boolean NOT NULL DEFAULT false,   -- operator-only: receive every event, not just ones about them
  secret_enc      text NOT NULL,                    -- AES-GCM ciphertext; plaintext shown once at creation
  secret_prefix   text NOT NULL,
  active          boolean NOT NULL DEFAULT true,
  failure_streak  int NOT NULL DEFAULT 0,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  deleted_at      timestamptz
);
CREATE INDEX IF NOT EXISTS webhook_subscriptions_member_idx ON vyapar_integration.webhook_subscriptions (member_id) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS vyapar_integration.webhook_deliveries (
  id               bigserial PRIMARY KEY,
  subscription_id  uuid NOT NULL REFERENCES vyapar_integration.webhook_subscriptions(id) ON DELETE CASCADE,
  member_id        text NOT NULL,                   -- denormalized owner, for RLS
  event_id         text NOT NULL,
  event_type       text NOT NULL,
  payload          jsonb NOT NULL,
  status           text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'delivered', 'failed')),
  attempts         int NOT NULL DEFAULT 0,
  next_attempt_at  timestamptz NOT NULL DEFAULT now(),
  last_status_code int,
  last_error       text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  delivered_at     timestamptz,
  UNIQUE (subscription_id, event_id)
);
CREATE INDEX IF NOT EXISTS webhook_deliveries_due_idx ON vyapar_integration.webhook_deliveries (next_attempt_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS webhook_deliveries_sub_idx ON vyapar_integration.webhook_deliveries (subscription_id, created_at DESC);

CREATE TABLE IF NOT EXISTS vyapar_integration.webhook_cursors (
  source     text PRIMARY KEY,
  last_id    bigint NOT NULL DEFAULT 0,
  updated_at timestamptz NOT NULL DEFAULT now()
);
-- Start every cursor at "now": subscriptions receive events from the moment
-- webhooks exist, never a replay of history recorded before anyone subscribed.
INSERT INTO vyapar_integration.webhook_cursors (source, last_id) VALUES
  ('listing',     (SELECT coalesce(max(id), 0) FROM vyapar_listings.outbox_event)),
  ('opportunity', (SELECT coalesce(max(id), 0) FROM vyapar_opportunities.outbox_event)),
  ('commercial',  (SELECT coalesce(max(id), 0) FROM vyapar_commercial.outbox_event)),
  ('enquiry',     (SELECT coalesce(max(id), 0) FROM vyapar_enquiries.outbox_event)),
  ('review',      (SELECT coalesce(max(id), 0) FROM vyapar_reviews.outbox_event))
ON CONFLICT (source) DO NOTHING;

ALTER TABLE vyapar_integration.webhook_subscriptions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS webhook_subscriptions_owner_or_dispatcher ON vyapar_integration.webhook_subscriptions;
CREATE POLICY webhook_subscriptions_owner_or_dispatcher ON vyapar_integration.webhook_subscriptions
  USING (member_id = current_setting('vyapar.authz_context', true)
         OR current_setting('vyapar.service_role', true) = 'dispatcher')
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true)
              OR current_setting('vyapar.service_role', true) = 'dispatcher');

ALTER TABLE vyapar_integration.webhook_deliveries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS webhook_deliveries_owner_or_dispatcher ON vyapar_integration.webhook_deliveries;
CREATE POLICY webhook_deliveries_owner_or_dispatcher ON vyapar_integration.webhook_deliveries
  USING (member_id = current_setting('vyapar.authz_context', true)
         OR current_setting('vyapar.service_role', true) = 'dispatcher')
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true)
              OR current_setting('vyapar.service_role', true) = 'dispatcher');

ALTER TABLE vyapar_integration.webhook_cursors ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS webhook_cursors_dispatcher_only ON vyapar_integration.webhook_cursors;
CREATE POLICY webhook_cursors_dispatcher_only ON vyapar_integration.webhook_cursors
  USING (current_setting('vyapar.service_role', true) = 'dispatcher')
  WITH CHECK (current_setting('vyapar.service_role', true) = 'dispatcher');

-- Subscriptions are soft-deleted (deleted_at) so the delivery log survives;
-- no DELETE grant to the runtime role.
GRANT SELECT, INSERT, UPDATE ON vyapar_integration.webhook_subscriptions, vyapar_integration.webhook_deliveries,
  vyapar_integration.webhook_cursors TO vyapar_app;
GRANT USAGE, SELECT ON SEQUENCE vyapar_integration.webhook_deliveries_id_seq TO vyapar_app;
