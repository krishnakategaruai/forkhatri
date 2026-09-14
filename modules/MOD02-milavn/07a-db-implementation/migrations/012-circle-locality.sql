-- 012 — Circles get a home locality (thesis §84 #6 "local relevance"; FR025
-- discovery). A circle can be city-wide (locality NULL) or anchored to a
-- locality; both are approximate places, never addresses (FR038). Discovery
-- lists circles in the viewer's own locality first ("Near you").

ALTER TABLE milavn_circle.circle
  ADD COLUMN IF NOT EXISTS locality_city text,
  ADD COLUMN IF NOT EXISTS locality_locality text;

CREATE INDEX IF NOT EXISTS circle_locality_idx ON milavn_circle.circle (locality_city, locality_locality);

-- Development seed: anchor the seeded circles so "Near you" has something to show.
UPDATE milavn_circle.circle SET locality_city = 'Hyderabad', locality_locality = 'Kondapur'
 WHERE id = 'dddddddd-0000-0000-0000-000000000002' AND locality_city IS NULL;
UPDATE milavn_circle.circle SET locality_city = 'Hyderabad', locality_locality = 'Ameerpet'
 WHERE id = 'dddddddd-0000-0000-0000-000000000003' AND locality_city IS NULL;
UPDATE milavn_circle.circle SET locality_city = 'Hyderabad', locality_locality = 'Jubilee Hills'
 WHERE id = 'dddddddd-0000-0000-0000-000000000004' AND locality_city IS NULL;
UPDATE milavn_circle.circle SET locality_city = 'Hyderabad', locality_locality = 'Jubilee Hills'
 WHERE name = 'Jubilee Hills Badminton Circle' AND locality_city IS NULL;
