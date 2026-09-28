-- =============================================================================
-- 055 — Horoscope answers as fixed keys (2026-09-27).
--
-- The editor now offers nakshatra as a pick-list of the 27 (it was free text)
-- and validates horoscope values on save (components/profile/horoscope_fields
-- .py). Earlier free-text nakshatra answers that name a nakshatra are rewritten
-- to its key ("Magha" → "magha", "Purva Phalguni" → "purva_phalguni"), so
-- they display in every language. Anything unrecognised is left untouched for
-- the member to re-pick. Birth time and place are not changed here.
-- Idempotent: safe to re-run.
-- =============================================================================

UPDATE mangaly_profile.profile_attribute a
   SET value = to_jsonb(k.key), updated_at = now()
  FROM (VALUES
    ('ashwini'), ('bharani'), ('krittika'), ('rohini'), ('mrigashira'), ('ardra'), ('punarvasu'),
    ('pushya'), ('ashlesha'), ('magha'), ('purva_phalguni'), ('uttara_phalguni'), ('hasta'),
    ('chitra'), ('swati'), ('vishakha'), ('anuradha'), ('jyeshtha'), ('mula'), ('purva_ashadha'),
    ('uttara_ashadha'), ('shravana'), ('dhanishta'), ('shatabhisha'), ('purva_bhadrapada'),
    ('uttara_bhadrapada'), ('revati')
  ) AS k(key)
 WHERE a.category = 'horoscope'
   AND a.attribute_key = 'nakshatra'
   AND a.state = 'value'
   AND jsonb_typeof(a.value) = 'string'
   AND regexp_replace(lower(a.value #>> '{}'), '[^a-z]+', '_', 'g') = k.key
   AND a.value #>> '{}' <> k.key;
