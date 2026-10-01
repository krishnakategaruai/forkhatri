-- =============================================================================
-- 062 — Wedding arrangements: the stage two families have reached, real
-- places near them, and (later) Mangalya partners with offers.
--
-- WHY (owner, 2026-10-01): once a request is accepted, Mangalya should help
-- the families with what comes next — a place for the first meeting, then
-- function halls, decoration, photography, vehicles, cooks — only for the
-- purpose of the marriage and only for the stage they are at. When Mangalya
-- has many families it negotiates discounts with the best places and shows
-- them here. Research: modules/MOD03-mangalya/research/wedding-services-partners.md.
--
-- Three separate things, kept in separate tables on purpose:
--   * connection_stage — per accepted connection, set by either family.
--   * osm_place        — a local copy of OpenStreetMap places (ODbL), filled
--                        by scripts/import_osm_places.py, never by the app at
--                        request time (the public Overpass server must not be
--                        an app backend). Read-only for the app.
--   * partner / partner_offer — businesses Mangalya has an agreement with.
--                        Kept apart from OSM data (ODbL share-alike), and every
--                        offer is shown labelled as a partner offer.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS mangaly_wedding AUTHORIZATION mangaly_owner;
GRANT USAGE ON SCHEMA mangaly_wedding TO mangaly_app;

-- Stages follow the Telugu/Indian journey: pelli choopulu (first meeting),
-- nischitartham (families agree / engagement), muhurtham fixed (wedding).
CREATE TABLE IF NOT EXISTS mangaly_wedding.connection_stage (
  connection_id          uuid PRIMARY KEY,
  stage                  text NOT NULL CHECK (stage IN ('first_meeting', 'families_agreed', 'wedding_fixed')),
  updated_by_account_id  uuid NOT NULL,
  updated_at             timestamptz NOT NULL DEFAULT now()
);
-- Participation is checked in the service (the connection must be accepted
-- and the caller one of its two sides or their Home Circle) before any read
-- or write, the same check every connection route makes.
GRANT SELECT, INSERT, UPDATE ON mangaly_wedding.connection_stage TO mangaly_app;

CREATE TABLE IF NOT EXISTS mangaly_wedding.osm_place (
  osm_ref        text PRIMARY KEY,           -- "node/123", "way/456"
  category       text NOT NULL,
  name           text NOT NULL,
  latitude       double precision NOT NULL,
  longitude      double precision NOT NULL,
  city           text NOT NULL,              -- the import area it came from
  names          jsonb,                      -- {"en","hi","te"} from OSM name:xx, when mapped
  address        text,
  cuisine        text,
  vegetarian     text,                       -- OSM diet:vegetarian (yes/only/no)
  phone          text,
  website        text,
  opening_hours  text,
  imported_at    timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE mangaly_wedding.osm_place ADD COLUMN IF NOT EXISTS names jsonb;
-- A Wikimedia Commons file of this very place, when OSM links one ("File:…").
ALTER TABLE mangaly_wedding.osm_place ADD COLUMN IF NOT EXISTS photo text;
CREATE INDEX IF NOT EXISTS idx_osm_place_category_city
  ON mangaly_wedding.osm_place (category, city);
GRANT SELECT ON mangaly_wedding.osm_place TO mangaly_app;

CREATE TABLE IF NOT EXISTS mangaly_wedding.partner (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  category       text NOT NULL,
  name           text NOT NULL,
  latitude       double precision NOT NULL,
  longitude      double precision NOT NULL,
  city           text NOT NULL,
  address        text,
  phone          text,
  website        text,
  verified_at    timestamptz,                -- checked by Mangalya staff
  active         boolean NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now()
);
-- The partner's own photo of their place, uploaded when they join.
ALTER TABLE mangaly_wedding.partner ADD COLUMN IF NOT EXISTS photo_url text;
CREATE INDEX IF NOT EXISTS idx_partner_category_city
  ON mangaly_wedding.partner (category, city) WHERE active;

CREATE TABLE IF NOT EXISTS mangaly_wedding.partner_offer (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id       uuid NOT NULL REFERENCES mangaly_wedding.partner (id) ON DELETE CASCADE,
  title            jsonb NOT NULL,           -- {"en": "...", "hi": "...", "te": "..."}
  terms            jsonb,                    -- same shape, optional
  discount_percent integer CHECK (discount_percent BETWEEN 1 AND 90),
  valid_from       date,
  valid_until      date,
  active           boolean NOT NULL DEFAULT true,
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_partner_offer_partner
  ON mangaly_wedding.partner_offer (partner_id) WHERE active;
GRANT SELECT ON mangaly_wedding.partner, mangaly_wedding.partner_offer TO mangaly_app;
