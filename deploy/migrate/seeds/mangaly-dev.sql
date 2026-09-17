-- =============================================================================
-- Mangaly (MOD03) development seed for the deployment kit (2026-09-14).
--
-- Loaded ONLY by `migrate.py --seed-dev --i-understand-this-loads-development-data`.
-- Same rows as modules/MOD03-mangaly/07a-db-implementation/seeds.sql, adjusted to
-- the current schema: migration 005 made `relationship_type` NOT NULL (that
-- seed file predates it and fails), and migration 014 made `credential_hash`
-- nullable because members sign in through the ForKhatri platform.
-- The module's own file is left unchanged.
-- =============================================================================

BEGIN;

INSERT INTO mangaly_identity.account (id, phone_identifier, email_identifier, credential_hash, status, identifier_verified_at)
VALUES
  ('11111111-1111-1111-1111-111111111111', '+919800000001', 'candidate.one@example.test', NULL, 'active', now()),
  ('22222222-2222-2222-2222-222222222222', '+919800000002', 'family.member@example.test', NULL, 'active', now())
ON CONFLICT (id) DO NOTHING;

INSERT INTO mangaly_profile.profile (id, account_id, name, date_of_birth, gender, city_locality, language_preference, status)
VALUES
  ('33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111',
   'Seed Candidate One', '1996-04-12', 'female', 'Hyderabad, Telangana', 'en', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO mangaly_profile.profile_attribute (profile_id, category, attribute_key, state, value)
VALUES
  ('33333333-3333-3333-3333-333333333333', 'education', 'education_level', 'value', '"Postgraduate"'),
  ('33333333-3333-3333-3333-333333333333', 'profession', 'profession', 'value', '"Software Engineer"'),
  ('33333333-3333-3333-3333-333333333333', 'marital_history', 'marital_history', 'value', '"never_married"'),
  ('33333333-3333-3333-3333-333333333333', 'relocation', 'relocation_willingness', 'value', '"open_to_relocate"'),
  ('33333333-3333-3333-3333-333333333333', 'partner_preference', 'age_range', 'value', '{"min": 27, "max": 34}'),
  ('33333333-3333-3333-3333-333333333333', 'lifestyle', 'hobbies', 'declined', 'null')
ON CONFLICT (profile_id, category, attribute_key) DO NOTHING;

INSERT INTO mangaly_discovery.discovery_profile_index (profile_id, searchable, locality, relocation_willingness, education_level, profession, search_vector)
VALUES
  ('33333333-3333-3333-3333-333333333333', true, 'Hyderabad, Telangana', 'open_to_relocate', 'Postgraduate', 'Software Engineer',
   to_tsvector('english', 'Hyderabad Telangana Postgraduate Software Engineer'))
ON CONFLICT (profile_id) DO NOTHING;

INSERT INTO mangaly_home_circle.invitation (id, candidate_profile_id, inviter_account_id, invitee_account_id, status, relationship_type)
VALUES
  ('44444444-4444-4444-4444-444444444444', '33333333-3333-3333-3333-333333333333',
   '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'accepted', 'parent')
ON CONFLICT (id) DO NOTHING;

INSERT INTO mangaly_home_circle.membership (id, candidate_profile_id, member_account_id, invitation_id, status, relationship_type)
VALUES
  ('55555555-5555-5555-5555-555555555555', '33333333-3333-3333-3333-333333333333',
   '22222222-2222-2222-2222-222222222222', '44444444-4444-4444-4444-444444444444', 'active', 'parent')
ON CONFLICT (id) DO NOTHING;

INSERT INTO mangaly_authz.grant (subject_id, target_profile_id, scope, grant_type, status, source_component, source_reference_id)
VALUES
  ('22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333',
   'family_info', 'home_circle_membership', 'active', 'home_circle', '55555555-5555-5555-5555-555555555555')
ON CONFLICT DO NOTHING;

INSERT INTO mangaly_trust.verification_layer_status (profile_id, layer, status, provenance, verified_at)
VALUES
  ('33333333-3333-3333-3333-333333333333', 'account_authenticity', 'verified', 'OTP verification (FR095)', now())
ON CONFLICT (profile_id, layer) DO NOTHING;

INSERT INTO mangaly_notification.inbox_entry (recipient_account_id, source_component, event_type, payload)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'profile', 'ProfileCreated', '{"message": "Your profile is live."}')
ON CONFLICT DO NOTHING;

COMMIT;
