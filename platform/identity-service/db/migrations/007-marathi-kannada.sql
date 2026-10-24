-- =============================================================================
-- 007 — Marathi (mr) and Kannada (kn) join English, Hindi and Telugu (owner
-- request 2026-10-06, docs/LANGUAGES-MR-KN-PLAN.md).
--
-- Additive only:
--   * identity.member.preferred_language accepts 'mr' and 'kn' as well. The
--     CHECK is replaced by a wider one; every existing value ('en', 'hi', 'te')
--     stays valid and no member's language is changed.
--   * registry.module gains tagline_mr and tagline_kn, filled for every module.
--     Existing columns and their text are untouched. identity_app's table-level
--     SELECT grant (001) already covers the new columns.
-- Re-running is safe.
-- =============================================================================

BEGIN;

ALTER TABLE identity.member DROP CONSTRAINT IF EXISTS member_preferred_language_check;
ALTER TABLE identity.member
  ADD CONSTRAINT member_preferred_language_check
  CHECK (preferred_language IN ('en', 'hi', 'te', 'mr', 'kn'));

ALTER TABLE registry.module ADD COLUMN IF NOT EXISTS tagline_mr text;
ALTER TABLE registry.module ADD COLUMN IF NOT EXISTS tagline_kn text;

UPDATE registry.module AS m SET
  tagline_mr = v.tagline_mr,
  tagline_kn = v.tagline_kn,
  updated_at = now()
FROM (VALUES
  ('mangaly',
   'कुटुंबाच्या साथीने, विश्वासार्ह विवाह प्रवास.',
   'ನಿಮ್ಮ ಕುಟುಂಬದೊಂದಿಗೆ, ನಂಬಿಕೆಯ ವಿವಾಹ ಪಯಣ.'),
  ('milavn',
   'तुमच्या जवळचे उपक्रम शोधा आणि लोकांना प्रत्यक्ष भेटा.',
   'ನಿಮ್ಮ ಹತ್ತಿರದ ಚಟುವಟಿಕೆಗಳನ್ನು ಹುಡುಕಿ, ಜನರನ್ನು ನೇರವಾಗಿ ಭೇಟಿಯಾಗಿ.'),
  ('vyapar',
   'विश्वासार्ह व्यवसाय, व्यावसायिक आणि खऱ्या संधी.',
   'ನಂಬಿಕಸ್ಥ ವ್ಯಾಪಾರಗಳು, ವೃತ್ತಿಪರರು ಮತ್ತು ನಿಜವಾದ ಅವಕಾಶಗಳು.'),
  ('counsel',
   'गरज असेल तेव्हा पडताळलेल्या तज्ज्ञांकडून मार्गदर्शन.',
   'ಅಗತ್ಯವಿದ್ದಾಗ ಪರಿಶೀಲಿಸಿದ ತಜ್ಞರಿಂದ ಮಾರ್ಗದರ್ಶನ.'),
  ('payments',
   'रोजचे पेमेंट आणि सदस्यांचे फायदे, एकाच ठिकाणी.',
   'ದಿನನಿತ್ಯದ ಪಾವತಿಗಳು ಮತ್ತು ಸದಸ್ಯರ ಪ್ರಯೋಜನಗಳು, ಒಂದೇ ಕಡೆ.'),
  ('finance',
   'आर्थिक पर्याय आणि विश्वासार्ह भागीदार मार्ग समजून घ्या.',
   'ಹಣಕಾಸಿನ ಆಯ್ಕೆಗಳು ಮತ್ತು ನಂಬಿಕೆಯ ಪಾಲುದಾರ ಮಾರ್ಗಗಳನ್ನು ತಿಳಿಯಿರಿ.')
) AS v(key, tagline_mr, tagline_kn)
WHERE m.key = v.key;

-- The new columns stay nullable so 002's upsert (which names only en/hi/te)
-- keeps working when re-run. The registry reads COALESCE(tagline_<lang>,
-- tagline_en), so a module added later without Marathi/Kannada text shows its
-- English tagline until translated, never an empty line.

COMMIT;
