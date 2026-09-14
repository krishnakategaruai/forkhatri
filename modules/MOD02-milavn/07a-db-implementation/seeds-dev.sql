-- =============================================================================
-- Milavn (MOD02) — richer DEVELOPMENT demo data (Step 9). Run as milavn_owner
-- AFTER seeds.sql. Idempotent (fixed ids). Never run against staging/prod.
-- Times are relative to now() so the demo always has Today / Tomorrow /
-- This weekend / Coming up content. Member ids match
-- milavn-service/app/config/dev_identities.json.
-- =============================================================================

-- Profiles for the remaining development identities (FR001)
INSERT INTO milavn_profile.member_profile (member_id, locality_city, locality_zone, locality_locality, language_preference, bio) VALUES
  ('66666666-6666-6666-6666-666666666666','Hyderabad','West Zone','Kondapur','en','Runs a weekend cycling group.'),
  ('77777777-7777-7777-7777-777777777777','Hyderabad','Central Zone','Ameerpet','hi','Book club host, chai enthusiast.')
ON CONFLICT (member_id) DO NOTHING;
INSERT INTO milavn_profile.member_interest (member_id, interest_tag) VALUES
  ('66666666-6666-6666-6666-666666666666','cycling'),('66666666-6666-6666-6666-666666666666','trekking'),
  ('77777777-7777-7777-7777-777777777777','book-club'),('77777777-7777-7777-7777-777777777777','coffee-meetups'),
  ('11111111-1111-1111-1111-111111111111','trekking'),('22222222-2222-2222-2222-222222222222','street-food'),
  ('33333333-3333-3333-3333-333333333333','yoga')
ON CONFLICT DO NOTHING;
INSERT INTO milavn_locationprivacy.location_precision_setting (member_id, precision_level) VALUES
  ('66666666-6666-6666-6666-666666666666','locality'),('77777777-7777-7777-7777-777777777777','zone')
ON CONFLICT (member_id) DO NOTHING;

-- A recurring series (FR011): Wednesday evening cycling, Kondapur
INSERT INTO milavn_activity.activity (id, creator_member_id, title, intent_category, recurrence_rule) VALUES
  ('aaaaaaaa-0000-0000-0000-000000000002','66666666-6666-6666-6666-666666666666','Wednesday evening ride','play','{"freq":"weekly","by_day":"WED"}')
ON CONFLICT (id) DO NOTHING;

-- Occurrences across the next two weeks (all relative to now, IST evenings)
INSERT INTO milavn_activity.occurrence
  (id, activity_id, creator_member_id, title, description, intent_category, time_start, locality_city, locality_zone, locality_locality, capacity, visibility_scope, circle_id, high_risk, canonical_url_slug)
VALUES
  ('d0000000-0000-0000-0000-000000000001', NULL, '77777777-7777-7777-7777-777777777777', 'Chai & chapters: book club', 'This month: The Covenant of Water. Bring the book or just come listen.', 'learn', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '18 hours 30 minutes', 'Hyderabad','Central Zone','Ameerpet', 10, 'public', NULL, false, 'occ-seed-bookclub-1'),
  ('d0000000-0000-0000-0000-000000000002', NULL, '22222222-2222-2222-2222-222222222222', 'Late-night biryani run', 'Meet at Bawarchi, RTC X Roads. Cash-friendly, split the bill.', 'eat', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '21 hours', 'Hyderabad','Central Zone','Abids', NULL, 'community', NULL, false, 'occ-seed-biryani-1'),
  ('d0000000-0000-0000-0000-000000000003', NULL, '33333333-3333-3333-3333-333333333333', 'Sunrise yoga at KBR Park', 'Gentle flow, all levels. Bring a mat and water.', 'play', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '1 day 6 hours 15 minutes', 'Hyderabad','West Zone','Banjara Hills', 15, 'public', NULL, false, 'occ-seed-yoga-1'),
  ('d0000000-0000-0000-0000-000000000004', 'aaaaaaaa-0000-0000-0000-000000000002', '66666666-6666-6666-6666-666666666666', 'Wednesday evening ride — 25 km', 'Kondapur to Gandipet and back. Helmets required, lights after 7.', 'play', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '3 days 17 hours 45 minutes', 'Hyderabad','West Zone','Kondapur', 12, 'public', NULL, true, 'occ-seed-ride-1'),
  ('d0000000-0000-0000-0000-000000000005', 'aaaaaaaa-0000-0000-0000-000000000002', '66666666-6666-6666-6666-666666666666', 'Wednesday evening ride — 25 km', 'Same loop, same crew.', 'play', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '10 days 17 hours 45 minutes', 'Hyderabad','West Zone','Kondapur', 12, 'public', NULL, true, 'occ-seed-ride-2'),
  ('d0000000-0000-0000-0000-000000000006', NULL, '11111111-1111-1111-1111-111111111111', 'Board games at Prism Café', 'Catan, Codenames, Ticket to Ride. Beginners welcome.', 'meet', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '2 days 19 hours', 'Hyderabad','West Zone','Jubilee Hills', 8, 'public', NULL, false, 'occ-seed-boardgames-1'),
  ('d0000000-0000-0000-0000-000000000007', NULL, '55555555-5555-5555-5555-555555555555', 'Lake clean-up drive, Durgam Cheruvu', 'Gloves and bags provided. Two hours, then breakfast.', 'help', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '5 days 7 hours', 'Hyderabad','West Zone','Madhapur', 40, 'community', NULL, false, 'occ-seed-cleanup-1'),
  ('d0000000-0000-0000-0000-000000000008', NULL, '44444444-4444-4444-4444-444444444444', 'Startup founders coffee', 'Informal, no pitches. Just people building things in Hyderabad.', 'work', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '4 days 8 hours 30 minutes', 'Hyderabad','West Zone','Hitech City', 20, 'public', NULL, false, 'occ-seed-founders-1'),
  ('d0000000-0000-0000-0000-000000000009', NULL, '77777777-7777-7777-7777-777777777777', 'Bathukamma evening', 'Flowers, songs, and dinner after. Families welcome.', 'celebrate', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '6 days 17 hours', 'Hyderabad','North Zone','Secunderabad', NULL, 'community', NULL, false, 'occ-seed-bathukamma-1'),
  ('d0000000-0000-0000-0000-000000000010', NULL, '11111111-1111-1111-1111-111111111111', 'Circle-only: doubles ladder night', 'For circle members. Ladder rules on the pinned note.', 'play', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '8 days 19 hours', 'Hyderabad','West Zone','Jubilee Hills', 8, 'circle', 'dddddddd-0000-0000-0000-000000000001', false, 'occ-seed-ladder-1'),
  ('d0000000-0000-0000-0000-000000000011', NULL, '66666666-6666-6666-6666-666666666666', 'Photo walk: old city at dawn', 'Charminar lanes before the crowds. Any camera, even a phone.', 'explore', date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' + interval '12 days 5 hours 45 minutes', 'Hyderabad','South Zone','Charminar', 12, 'public', NULL, false, 'occ-seed-photowalk-1'),
  ('d0000000-0000-0000-0000-000000000012', NULL, '22222222-2222-2222-2222-222222222222', 'Held last week: street cricket', 'Already happened — here for history.', 'play', now() - interval '7 days', 'Hyderabad','West Zone','Madhapur', NULL, 'public', NULL, false, 'occ-seed-cricket-past')
ON CONFLICT (id) DO NOTHING;

-- Trust statuses (FR030: exactly one per item)
INSERT INTO milavn_trust.trust_status (subject_type, subject_id, trust_level) VALUES
  ('occurrence','d0000000-0000-0000-0000-000000000001','community_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000002','community_submitted'),
  ('occurrence','d0000000-0000-0000-0000-000000000003','forkhatri_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000004','community_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000005','community_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000006','forkhatri_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000007','partner_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000008','community_submitted'),
  ('occurrence','d0000000-0000-0000-0000-000000000009','community_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000010','forkhatri_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000011','community_verified'),
  ('occurrence','d0000000-0000-0000-0000-000000000012','community_submitted'),
  ('organizer','66666666-6666-6666-6666-666666666666','community_verified'),
  ('organizer','77777777-7777-7777-7777-777777777777','community_verified'),
  ('organizer','33333333-3333-3333-3333-333333333333','forkhatri_verified')
ON CONFLICT (subject_type, subject_id) DO NOTHING;

-- Participation (FR015/FR016) — enough for "N going" and circle-peer reasons
INSERT INTO milavn_activity.participation (occurrence_id, member_id, status) VALUES
  ('d0000000-0000-0000-0000-000000000001','22222222-2222-2222-2222-222222222222','going'),
  ('d0000000-0000-0000-0000-000000000001','44444444-4444-4444-4444-444444444444','interested'),
  ('d0000000-0000-0000-0000-000000000003','11111111-1111-1111-1111-111111111111','going'),
  ('d0000000-0000-0000-0000-000000000003','22222222-2222-2222-2222-222222222222','going'),
  ('d0000000-0000-0000-0000-000000000003','66666666-6666-6666-6666-666666666666','going'),
  ('d0000000-0000-0000-0000-000000000004','11111111-1111-1111-1111-111111111111','going'),
  ('d0000000-0000-0000-0000-000000000004','44444444-4444-4444-4444-444444444444','going'),
  ('d0000000-0000-0000-0000-000000000006','22222222-2222-2222-2222-222222222222','going'),
  ('d0000000-0000-0000-0000-000000000006','33333333-3333-3333-3333-333333333333','going'),
  ('d0000000-0000-0000-0000-000000000006','77777777-7777-7777-7777-777777777777','interested'),
  ('d0000000-0000-0000-0000-000000000007','11111111-1111-1111-1111-111111111111','going'),
  ('d0000000-0000-0000-0000-000000000007','66666666-6666-6666-6666-666666666666','going'),
  ('d0000000-0000-0000-0000-000000000008','66666666-6666-6666-6666-666666666666','interested'),
  ('d0000000-0000-0000-0000-000000000012','11111111-1111-1111-1111-111111111111','attended'),
  ('d0000000-0000-0000-0000-000000000012','33333333-3333-3333-3333-333333333333','attended'),
  ('d0000000-0000-0000-0000-000000000012','44444444-4444-4444-4444-444444444444','no_show')
ON CONFLICT DO NOTHING;

-- More circles (FR020/FR021): an interest circle and a private one
INSERT INTO milavn_circle.circle (id, name, circle_type, description, created_by_member_id) VALUES
  ('dddddddd-0000-0000-0000-000000000002','Kondapur Riders','interest','Weekly rides, all paces. Helmets always.','66666666-6666-6666-6666-666666666666'),
  ('dddddddd-0000-0000-0000-000000000003','Ameerpet Readers','community','Books, chai, opinions.','77777777-7777-7777-7777-777777777777'),
  ('dddddddd-0000-0000-0000-000000000004','Reddy family planning group','private','Invite only.','11111111-1111-1111-1111-111111111111')
ON CONFLICT (id) DO NOTHING;
-- Home localities (migration 012): "Near you" in Discover circles.
UPDATE milavn_circle.circle SET locality_city = 'Hyderabad', locality_locality = 'Kondapur' WHERE id = 'dddddddd-0000-0000-0000-000000000002';
UPDATE milavn_circle.circle SET locality_city = 'Hyderabad', locality_locality = 'Ameerpet' WHERE id = 'dddddddd-0000-0000-0000-000000000003';
UPDATE milavn_circle.circle SET locality_city = 'Hyderabad', locality_locality = 'Jubilee Hills' WHERE id IN ('dddddddd-0000-0000-0000-000000000001', 'dddddddd-0000-0000-0000-000000000004');
INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role) VALUES
  ('dddddddd-0000-0000-0000-000000000002','66666666-6666-6666-6666-666666666666','organizer'),
  ('dddddddd-0000-0000-0000-000000000002','11111111-1111-1111-1111-111111111111','member'),
  ('dddddddd-0000-0000-0000-000000000002','44444444-4444-4444-4444-444444444444','member'),
  ('dddddddd-0000-0000-0000-000000000003','77777777-7777-7777-7777-777777777777','organizer'),
  ('dddddddd-0000-0000-0000-000000000003','22222222-2222-2222-2222-222222222222','member'),
  ('dddddddd-0000-0000-0000-000000000004','11111111-1111-1111-1111-111111111111','organizer'),
  ('dddddddd-0000-0000-0000-000000000004','33333333-3333-3333-3333-333333333333','member')
ON CONFLICT DO NOTHING;

-- An organization scope (FR028, TR23 minimal)
INSERT INTO milavn_circle.organization_scope (organization_scope_id, display_name, created_by_member_id) VALUES
  ('e0000000-0000-0000-0000-000000000001','Khatri Sabha Hyderabad','77777777-7777-7777-7777-777777777777')
ON CONFLICT (organization_scope_id) DO NOTHING;
UPDATE milavn_activity.occurrence SET visibility_scope = 'organization', organization_scope_id = 'e0000000-0000-0000-0000-000000000001'
 WHERE id = 'd0000000-0000-0000-0000-000000000009' AND organization_scope_id IS NULL;

-- Reputation signals (FR034) so qualitative labels vary
INSERT INTO milavn_trust.reputation_signal (member_id, signal_type, source_occurrence_id, weight) VALUES
  ('66666666-6666-6666-6666-666666666666','event_completed',NULL,1),('66666666-6666-6666-6666-666666666666','event_completed',NULL,1),('66666666-6666-6666-6666-666666666666','event_completed',NULL,1),
  ('77777777-7777-7777-7777-777777777777','event_completed',NULL,1),('77777777-7777-7777-7777-777777777777','community_contribution',NULL,0.5),('77777777-7777-7777-7777-777777777777','community_contribution',NULL,0.5),
  ('11111111-1111-1111-1111-111111111111','attendance_reliable','d0000000-0000-0000-0000-000000000012',1),('11111111-1111-1111-1111-111111111111','attendance_reliable',NULL,1),('11111111-1111-1111-1111-111111111111','attendance_reliable',NULL,1),('11111111-1111-1111-1111-111111111111','identity_verified',NULL,1),
  ('33333333-3333-3333-3333-333333333333','identity_verified',NULL,1);

-- Beyond-MVP seeds (migration 013): a thread on Sunday Badminton (past, attended), moments from it, and a circle board post.
INSERT INTO milavn_activity.occurrence_message (id, occurrence_id, member_id, body, created_at) VALUES
  ('eeeeeeee-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000001','11111111-1111-1111-1111-111111111111','Courts 3 and 4 are ours till 9. Come to gate B.', now() - interval '8 days'),
  ('eeeeeeee-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000001','33333333-3333-3333-3333-333333333333','Bringing two spare rackets if anyone needs one.', now() - interval '8 days' + interval '20 minutes'),
  ('eeeeeeee-0000-0000-0000-000000000003','bbbbbbbb-0000-0000-0000-000000000001','22222222-2222-2222-2222-222222222222','Running 10 min late, start without me!', now() - interval '7 days')
ON CONFLICT (id) DO NOTHING;
INSERT INTO milavn_activity.occurrence_photo (id, occurrence_id, member_id, storage_ref, caption, created_at) VALUES
  ('ffffffff-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000001','33333333-3333-3333-3333-333333333333','moments/seed-badminton-1.jpg','Match point', now() - interval '7 days'),
  ('ffffffff-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000001','11111111-1111-1111-1111-111111111111','moments/seed-badminton-2.jpg','Full house on court 4', now() - interval '7 days')
ON CONFLICT (id) DO NOTHING;
INSERT INTO milavn_circle.circle_post (id, circle_id, member_id, body, created_at) VALUES
  ('99999999-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000002','66666666-6666-6666-6666-666666666666','Helmets are not optional. New riders: we regroup at every signal.', now() - interval '3 days')
ON CONFLICT (id) DO NOTHING;
