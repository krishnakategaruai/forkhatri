-- =============================================================================
-- Mangaly (MOD03) — development/test seed data
-- NOT run against production. init.sh loads this only when SEED_DB=true.
-- Values are illustrative placeholders — no real PII. UUIDs are fixed
-- literals so seeded rows are stable/referenceable across re-seeds in local
-- development and Step 10/11 test fixtures.
-- =============================================================================

BEGIN;

-- Two interim identity accounts (TR092) — one candidate, one family member.
INSERT INTO mangaly_identity.account (id, phone_identifier, email_identifier, credential_hash, status, identifier_verified_at)
VALUES
  ('11111111-1111-1111-1111-111111111111', '+919800000001', 'candidate.one@example.test', 'CHANGE_ME_bcrypt_hash', 'active', now()),
  ('22222222-2222-2222-2222-222222222222', '+919800000002', 'family.member@example.test', 'CHANGE_ME_bcrypt_hash', 'active', now())
ON CONFLICT (id) DO NOTHING;

-- One profile at existence tier (TR001), owned by the first account.
INSERT INTO mangaly_profile.profile (id, account_id, name, date_of_birth, gender, city_locality, language_preference, status)
VALUES
  ('33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111',
   'Asha Reddy', '1996-04-12', 'female', 'Hyderabad, Telangana', 'en', 'active')
ON CONFLICT (id) DO NOTHING;

-- Discoverability-tier attributes (DEC-V1-001), tri-state per TR002.
INSERT INTO mangaly_profile.profile_attribute (profile_id, category, attribute_key, state, value)
VALUES
  ('33333333-3333-3333-3333-333333333333', 'education', 'highest_education_level', 'value', '"masters"'),
  ('33333333-3333-3333-3333-333333333333', 'profession', 'occupation', 'value', '"Software Engineer"'),
  ('33333333-3333-3333-3333-333333333333', 'marital_history', 'marital_status', 'value', '"never_married"'),
  ('33333333-3333-3333-3333-333333333333', 'relocation', 'relocation_willingness', 'value', '"open_to_relocate"'),
  ('33333333-3333-3333-3333-333333333333', 'partner_preference', 'age_range', 'value', '{"min": 27, "max": 34}'),
  ('33333333-3333-3333-3333-333333333333', 'lifestyle', 'hobbies', 'declined', 'null')
ON CONFLICT (profile_id, category, attribute_key) DO NOTHING;

-- Discovery index row (TR021/TR025), searchable = true.
INSERT INTO mangaly_discovery.discovery_profile_index (profile_id, searchable, locality, relocation_willingness, education_level, profession, search_vector)
VALUES
  ('33333333-3333-3333-3333-333333333333', true, 'Hyderabad, Telangana', 'open_to_relocate', 'Postgraduate', 'Software Engineer',
   to_tsvector('english', 'Hyderabad Telangana Postgraduate Software Engineer'))
ON CONFLICT (profile_id) DO NOTHING;
-- Vikram Rao (2222…, persona mangaly-family) is no longer in Asha's circle: since
-- 2026-09-25 he is the father in his daughter Kavya Rao's circle, built through the
-- product API by mangaly-service/scripts/seed_dev_vikram_family.py.


-- Trust layer status: account authenticity verified (TR095), rest pending.
INSERT INTO mangaly_trust.verification_layer_status (profile_id, layer, status, provenance, verified_at)
VALUES
  ('33333333-3333-3333-3333-333333333333', 'account_authenticity', 'verified', 'OTP verification (FR095)', now())
ON CONFLICT (profile_id, layer) DO NOTHING;

-- One inbox entry (TR098) so the Notification screen has something to show.
-- No unique key on inbox_entry, so ON CONFLICT never fired and every re-seed
-- added another copy; insert only when this seed row is not there yet.
INSERT INTO mangaly_notification.inbox_entry (recipient_account_id, source_component, event_type, payload)
SELECT '11111111-1111-1111-1111-111111111111', 'profile', 'ProfileCreated', '{"message": "Your profile is live."}'
WHERE NOT EXISTS (
  SELECT 1 FROM mangaly_notification.inbox_entry
  WHERE recipient_account_id = '11111111-1111-1111-1111-111111111111' AND event_type = 'ProfileCreated'
);

COMMIT;
