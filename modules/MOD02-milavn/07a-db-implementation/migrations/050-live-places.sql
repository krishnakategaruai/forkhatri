-- 050 — Live India place search (Step 1 of PLAN-places-events-groups.md).
--
-- Places now come from the shared place-search utility (free OpenStreetMap data,
-- behind forkhatri_integrations.places), not from a hardcoded list of 33 localities.
-- Milavn still stores only an approximate place (city / district / area) and the
-- centre of that area, never an address (FR038, BR09). The centre is what distance
-- and Map pins read, so nothing needs the old list at run time.
--
--   locality_state   the state, so two places with the same name can be told apart
--   locality_lat/lng the centre of the chosen area (not a person's position)
--
-- One-time carry-over: rows that pointed at the old list get the state and the
-- centre that list had for them (by locality, or by city when no locality was set),
-- so existing profiles and events keep their distance and map pins unchanged.

ALTER TABLE milavn_profile.member_profile
  ADD COLUMN IF NOT EXISTS locality_state text,
  ADD COLUMN IF NOT EXISTS locality_lat double precision,
  ADD COLUMN IF NOT EXISTS locality_lng double precision;
ALTER TABLE milavn_activity.occurrence
  ADD COLUMN IF NOT EXISTS locality_state text,
  ADD COLUMN IF NOT EXISTS locality_lat double precision,
  ADD COLUMN IF NOT EXISTS locality_lng double precision;
ALTER TABLE milavn_circle.circle
  ADD COLUMN IF NOT EXISTS locality_state text;

DO $$ BEGIN
  ALTER TABLE milavn_profile.member_profile ADD CONSTRAINT member_profile_lat_lng_range
    CHECK ((locality_lat IS NULL AND locality_lng IS NULL) OR (locality_lat BETWEEN -90 AND 90 AND locality_lng BETWEEN -180 AND 180));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE milavn_activity.occurrence ADD CONSTRAINT occurrence_lat_lng_range
    CHECK ((locality_lat IS NULL AND locality_lng IS NULL) OR (locality_lat BETWEEN -90 AND 90 AND locality_lng BETWEEN -180 AND 180));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- The old list, used once for the carry-over below.
CREATE TEMP TABLE _old_places (city text, zone text, locality text, state text, lat double precision, lng double precision);
INSERT INTO _old_places VALUES
    ('Hyderabad', 'West Zone', 'Jubilee Hills', 'Telangana', 17.4325, 78.4073),
    ('Hyderabad', 'West Zone', 'Banjara Hills', 'Telangana', 17.4156, 78.4347),
    ('Hyderabad', 'West Zone', 'Madhapur', 'Telangana', 17.4483, 78.3915),
    ('Hyderabad', 'West Zone', 'Gachibowli', 'Telangana', 17.4401, 78.3489),
    ('Hyderabad', 'West Zone', 'Kondapur', 'Telangana', 17.4622, 78.3568),
    ('Hyderabad', 'West Zone', 'Hitech City', 'Telangana', 17.4435, 78.3772),
    ('Hyderabad', 'West Zone', 'Manikonda', 'Telangana', 17.4022, 78.3767),
    ('Hyderabad', 'West Zone', 'Kukatpally', 'Telangana', 17.4849, 78.4138),
    ('Hyderabad', 'West Zone', 'Miyapur', 'Telangana', 17.4969, 78.3612),
    ('Hyderabad', 'Central Zone', 'Ameerpet', 'Telangana', 17.4375, 78.4483),
    ('Hyderabad', 'Central Zone', 'Somajiguda', 'Telangana', 17.4239, 78.4586),
    ('Hyderabad', 'Central Zone', 'Begumpet', 'Telangana', 17.444, 78.4676),
    ('Hyderabad', 'Central Zone', 'Punjagutta', 'Telangana', 17.4276, 78.4514),
    ('Hyderabad', 'Central Zone', 'Abids', 'Telangana', 17.3909, 78.4757),
    ('Hyderabad', 'North Zone', 'Secunderabad', 'Telangana', 17.4399, 78.4983),
    ('Hyderabad', 'North Zone', 'Kompally', 'Telangana', 17.5387, 78.4863),
    ('Hyderabad', 'North Zone', 'Alwal', 'Telangana', 17.5045, 78.5124),
    ('Hyderabad', 'North Zone', 'Bowenpally', 'Telangana', 17.4746, 78.4844),
    ('Hyderabad', 'East Zone', 'Uppal', 'Telangana', 17.4056, 78.5591),
    ('Hyderabad', 'East Zone', 'Tarnaka', 'Telangana', 17.4278, 78.5346),
    ('Hyderabad', 'East Zone', 'LB Nagar', 'Telangana', 17.3457, 78.5522),
    ('Hyderabad', 'East Zone', 'Dilsukhnagar', 'Telangana', 17.3688, 78.5247),
    ('Hyderabad', 'South Zone', 'Charminar', 'Telangana', 17.3616, 78.4747),
    ('Hyderabad', 'South Zone', 'Mehdipatnam', 'Telangana', 17.3949, 78.4394),
    ('Hyderabad', 'South Zone', 'Tolichowki', 'Telangana', 17.4009, 78.4147),
    ('Hyderabad', 'South Zone', 'Attapur', 'Telangana', 17.3699, 78.4283),
    ('Warangal', 'Central', 'Hanamkonda', 'Telangana', 18.01, 79.56),
    ('Warangal', 'Central', 'Kazipet', 'Telangana', 17.9722, 79.5),
    ('Vijayawada', 'Central', 'Benz Circle', 'Andhra Pradesh', 16.4989, 80.6555),
    ('Vijayawada', 'West', 'Gollapudi', 'Andhra Pradesh', 16.5453, 80.5807),
    ('Visakhapatnam', 'Central', 'MVP Colony', 'Andhra Pradesh', 17.7408, 83.3346),
    ('Visakhapatnam', 'North', 'Madhurawada', 'Andhra Pradesh', 17.8163, 83.3607);

-- Rows that named a locality from the old list.
UPDATE milavn_profile.member_profile p
   SET locality_state = o.state, locality_lat = o.lat, locality_lng = o.lng
  FROM _old_places o
 WHERE p.locality_lat IS NULL AND lower(p.locality_city) = lower(o.city) AND lower(p.locality_locality) = lower(o.locality);
UPDATE milavn_activity.occurrence p
   SET locality_state = o.state, locality_lat = o.lat, locality_lng = o.lng
  FROM _old_places o
 WHERE p.locality_lat IS NULL AND lower(p.locality_city) = lower(o.city) AND lower(p.locality_locality) = lower(o.locality);

-- Rows that named only a city: the middle of that city's old localities.
UPDATE milavn_profile.member_profile p
   SET locality_state = c.state, locality_lat = c.lat, locality_lng = c.lng
  FROM (SELECT city, min(state) AS state, avg(lat) AS lat, avg(lng) AS lng FROM _old_places GROUP BY city) c
 WHERE p.locality_lat IS NULL AND p.locality_locality IS NULL AND lower(p.locality_city) = lower(c.city);
UPDATE milavn_activity.occurrence p
   SET locality_state = c.state, locality_lat = c.lat, locality_lng = c.lng
  FROM (SELECT city, min(state) AS state, avg(lat) AS lat, avg(lng) AS lng FROM _old_places GROUP BY city) c
 WHERE p.locality_lat IS NULL AND p.locality_locality IS NULL AND lower(p.locality_city) = lower(c.city);

-- Circles keep their city/locality text (their "Near you" match is by name); add the state where it is known.
UPDATE milavn_circle.circle c SET locality_state = o.state
  FROM (SELECT DISTINCT city, state FROM _old_places) o
 WHERE c.locality_state IS NULL AND lower(c.locality_city) = lower(o.city);
DROP TABLE IF EXISTS _old_places;
