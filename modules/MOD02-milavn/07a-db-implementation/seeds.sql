-- =============================================================================
-- Milavn (MOD02) — development/test seed data.
-- Run only when SEED_DB=true (see init.sh). Intentionally small and
-- internally consistent — enough to exercise every schema's own RLS
-- policies and TR08's Activity/Occurrence contract manually (psql or a
-- quick API smoke test), not a load-test dataset.
--
-- member_id values below are fake, fixed UUIDs standing in for Identity &
-- Trust Service records this module never owns — real dev/test setups
-- should point these at actual seeded Identity & Trust Service accounts;
-- here they are placeholders consistent with this project's
-- config-placeholder convention.
-- =============================================================================

-- Fixed member ids used throughout (organizer, two participants, a moderator)
-- 11111111-1111-1111-1111-111111111111  Asha (organizer)
-- 22222222-2222-2222-2222-222222222222  Vikram (participant)
-- 33333333-3333-3333-3333-333333333333  Meera (participant, waitlisted)
-- 99999999-9999-9999-9999-999999999999  Moderator (milavn.moderate scope)

INSERT INTO milavn_profile.member_profile (member_id, locality_city, locality_zone, locality_locality, language_preference, bio)
VALUES
  ('11111111-1111-1111-1111-111111111111','Hyderabad','West Zone','Jubilee Hills','en','Organizes weekend badminton.'),
  ('22222222-2222-2222-2222-222222222222','Hyderabad','West Zone','Madhapur','en',NULL),
  ('33333333-3333-3333-3333-333333333333','Hyderabad','West Zone','Gachibowli','te',NULL)
ON CONFLICT (member_id) DO NOTHING;

INSERT INTO milavn_profile.member_interest (member_id, interest_tag) VALUES
  ('11111111-1111-1111-1111-111111111111','badminton'),
  ('22222222-2222-2222-2222-222222222222','badminton'),
  ('33333333-3333-3333-3333-333333333333','badminton')
ON CONFLICT DO NOTHING;

-- [TR08] A recurring Activity ("Sunday Badminton") with one Occurrence
-- under it, PLUS a standalone one-off Occurrence with no Activity wrapper
-- at all — demonstrating the non-forced-wrapper rule concretely.
INSERT INTO milavn_activity.activity (id, creator_member_id, title, intent_category, recurrence_rule)
VALUES ('aaaaaaaa-0000-0000-0000-000000000001','11111111-1111-1111-1111-111111111111','Sunday Badminton','play','{"freq":"weekly","by_day":"SUN"}')
ON CONFLICT (id) DO NOTHING;

INSERT INTO milavn_activity.occurrence
  (id, activity_id, creator_member_id, title, intent_category, time_start, locality_city, locality_zone, locality_locality, capacity, visibility_scope, canonical_url_slug)
VALUES
  ('bbbbbbbb-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','11111111-1111-1111-1111-111111111111','Sunday Badminton — Sep 21','play','2026-09-21 07:00:00+05:30','Hyderabad','West Zone','Jubilee Hills',2,'public','occ-bbbbbbbb0001'),
  ('cccccccc-0000-0000-0000-000000000001',NULL,'11111111-1111-1111-1111-111111111111','One-off Saturday Trek','explore','2026-09-27 06:00:00+05:30','Hyderabad','North Zone','Kompally',NULL,'public','occ-cccccccc0001')
ON CONFLICT (id) DO NOTHING;

-- Participation: capacity of 2 on the badminton occurrence, one Going, one
-- Waitlisted — exercises TR39's waitlist ordering.
INSERT INTO milavn_activity.participation (occurrence_id, member_id, status, waitlist_position)
VALUES
  ('bbbbbbbb-0000-0000-0000-000000000001','22222222-2222-2222-2222-222222222222','going',NULL),
  ('bbbbbbbb-0000-0000-0000-000000000001','33333333-3333-3333-3333-333333333333','waitlisted',1)
ON CONFLICT DO NOTHING;

INSERT INTO milavn_trust.trust_status (subject_type, subject_id, trust_level)
VALUES
  ('occurrence','bbbbbbbb-0000-0000-0000-000000000001','community_verified'),
  ('occurrence','cccccccc-0000-0000-0000-000000000001','community_submitted')
ON CONFLICT (subject_type, subject_id) DO NOTHING;

INSERT INTO milavn_circle.circle (id, name, circle_type, created_by_member_id)
VALUES ('dddddddd-0000-0000-0000-000000000001','Jubilee Hills Badminton Circle','public','11111111-1111-1111-1111-111111111111')
ON CONFLICT (id) DO NOTHING;

INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role)
VALUES
  ('dddddddd-0000-0000-0000-000000000001','11111111-1111-1111-1111-111111111111','organizer'),
  ('dddddddd-0000-0000-0000-000000000001','22222222-2222-2222-2222-222222222222','member')
ON CONFLICT DO NOTHING;

INSERT INTO milavn_locationprivacy.location_precision_setting (member_id, precision_level) VALUES
  ('11111111-1111-1111-1111-111111111111','locality'),
  ('22222222-2222-2222-2222-222222222222','zone'),
  ('33333333-3333-3333-3333-333333333333','locality')
ON CONFLICT (member_id) DO UPDATE SET precision_level = EXCLUDED.precision_level;

INSERT INTO milavn_safety.report (reporter_member_id, subject_type, subject_id, reason_category, description)
VALUES ('22222222-2222-2222-2222-222222222222','occurrence','cccccccc-0000-0000-0000-000000000001','spam','Looks like a duplicate posting.')
ON CONFLICT DO NOTHING;
