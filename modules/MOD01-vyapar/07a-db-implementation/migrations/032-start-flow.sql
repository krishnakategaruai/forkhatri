-- ===========================================================================
-- 032 — The 3-question start (ONBOARDING-REDESIGN-2026-10.md, decisions 1–14,
-- owner-accepted 2026-10-06). Additive and idempotent; nothing existing is
-- dropped, renamed or rewritten, every existing row still passes.
--
--  1. members.date_of_birth — Vyapar is for members 18 and over. The platform
--     identity does not carry a birth date, so Vyapar asks it once, only when
--     it is not already known, and keeps it here (decision "Under 18").
--  2. members.phone_verified — the host adapter says whether the phone it
--     passes was verified by the host's own sign-in (ForKhatri signs in by
--     OTP on that number). A verified identity phone counts as the profile's
--     contact verification (decision 2), so phone OTP is asked only for a
--     DIFFERENT number. ensure_member() gains a 5-argument overload; the
--     4-argument one stays for every existing caller.
--  3. Trades real people named in the audit that were not in the tree
--     (decision 5): kirana / general store, home-made food and pickles,
--     borewell and motor repair, shop helper. Same upsert shape as 022/031,
--     names in all five languages, spoken words in aliases (append only).
--  4. "Health & Wellness" and "Healthcare" read almost alike in Hindi and
--     Telugu (స్వాస్థ్య / ఆరోగ్యం); the first is renamed to what it holds,
--     fitness and wellness (decision 13). The slug does not change.
--
-- Apply: psql -v ON_ERROR_STOP=1 -U vyapar_owner -d vyapar -f 032-start-flow.sql
-- Traces to: FR44, FR04, FR01, FR07, FR53, TR044, TR050
-- ===========================================================================

-- 1 + 2. Member columns --------------------------------------------------------
ALTER TABLE vyapar_identity.members
  ADD COLUMN IF NOT EXISTS date_of_birth date,
  ADD COLUMN IF NOT EXISTS phone_verified boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN vyapar_identity.members.date_of_birth IS
  '[Start flow 2026-10] Asked once by Vyapar when the host identity does not know it; Vyapar is for members 18 and over.';
COMMENT ON COLUMN vyapar_identity.members.phone_verified IS
  '[Start flow 2026-10, decision 2] True when the host adapter passed a phone the host itself verified at sign-in; counts as listing contact verification for that same number.';

-- The 5-argument overload: the same upsert as migration 026 plus the host's
-- verified flag. The flag is set only for the phone it came with; a later
-- different phone from the host (COALESCE keeps the first non-null) does not
-- silently inherit it.
CREATE OR REPLACE FUNCTION vyapar_identity.ensure_member(
  p_member_id text, p_display_name text, p_phone text, p_language text, p_phone_verified boolean
) RETURNS void
LANGUAGE sql SECURITY DEFINER
SET search_path = vyapar_identity, pg_temp
AS $$
  INSERT INTO vyapar_identity.members (id, display_name, phone, language, phone_verified)
  VALUES (p_member_id, p_display_name, p_phone, coalesce(p_language, 'en'), coalesce(p_phone_verified, false) AND p_phone IS NOT NULL)
  ON CONFLICT (id) DO UPDATE SET
    display_name = CASE WHEN EXCLUDED.display_name IS NOT NULL AND EXCLUDED.display_name <> EXCLUDED.id
                        THEN EXCLUDED.display_name ELSE vyapar_identity.members.display_name END,
    phone = COALESCE(EXCLUDED.phone, vyapar_identity.members.phone),
    phone_verified = vyapar_identity.members.phone_verified
                     OR (coalesce(p_phone_verified, false) AND EXCLUDED.phone IS NOT NULL
                         AND EXCLUDED.phone = COALESCE(vyapar_identity.members.phone, EXCLUDED.phone)),
    synced_at = now(), updated_at = now();
$$;
COMMENT ON FUNCTION vyapar_identity.ensure_member(text, text, text, text, boolean) IS
  '[TR050 + start flow 2026-10] The 4-argument ensure_member() plus the host''s "this phone was verified at sign-in" flag.';
REVOKE ALL ON FUNCTION vyapar_identity.ensure_member(text, text, text, text, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_identity.ensure_member(text, text, text, text, boolean) TO vyapar_app;

-- 3. Trades from the audit -------------------------------------------------------
WITH terms(slug, parent, name_en, name_hi, name_te, name_mr, name_kn,
           description_en, description_hi, description_te, description_mr, description_kn, aliases) AS (VALUES
  ('kirana_store',   'textiles_retail',   'Kirana / general store',     'किराना / जनरल स्टोर',        'కిరాణా / జనరల్ స్టోర్',
     'किराणा / जनरल स्टोअर',  'ಕಿರಾಣಿ / ಜನರಲ್ ಸ್ಟೋರ್',
     'Groceries, provisions and everyday goods from a shop',
     'दुकान से किराना, राशन और रोज़मर्रा का सामान',
     'దుకాణం నుంచి కిరాణా, సరుకులు మరియు రోజువారీ వస్తువులు',
     'दुकानातून किराणा, धान्य आणि रोजच्या वस्तू',
     'ಅಂಗಡಿಯಿಂದ ಕಿರಾಣಿ, ದಿನಸಿ ಮತ್ತು ದಿನನಿತ್ಯದ ಸಾಮಾನು',
     ARRAY['kirana','general store','grocery','groceries','provision store','provisions','ration','किराना','राशन','కిరాణా','సరుకులు','किराणा','ಕಿರಾಣಿ','ದಿನಸಿ']::text[]),
  ('home_food',      'food_catering',     'Home-made food & pickles',   'घर का बना खाना और अचार',     'ఇంటి వంటకాలు & పచ్చళ్ళు',
     'घरगुती जेवण आणि लोणची', 'ಮನೆ ಊಟ ಮತ್ತು ಉಪ್ಪಿನಕಾಯಿ',
     'Pickles, tiffins, sweets and snacks made at home',
     'घर पर बने अचार, टिफ़िन, मिठाई और नमकीन',
     'ఇంట్లో చేసిన పచ్చళ్ళు, టిఫిన్లు, స్వీట్లు మరియు స్నాక్స్',
     'घरी बनवलेली लोणची, डबे, मिठाई आणि फराळ',
     'ಮನೆಯಲ್ಲಿ ಮಾಡಿದ ಉಪ್ಪಿನಕಾಯಿ, ಟಿಫಿನ್, ಸಿಹಿ ಮತ್ತು ತಿಂಡಿ',
     ARRAY['pickles','pickle','achar','home food','homemade','tiffin','tiffins','papad','sweets','snacks','अचार','घर का खाना','పచ్చళ్ళు','పచ్చడి','ఇంటి భోజనం','लोणचे','लोणची','ಉಪ್ಪಿನಕಾಯಿ','ಮನೆ ಊಟ']::text[]),
  ('borewell_motor', 'home_repair',       'Borewell & motor repair',    'बोरवेल और मोटर मरम्मत',      'బోర్‌వెల్ & మోటర్ రిపేర్',
     'बोअरवेल आणि मोटर दुरुस्ती', 'ಬೋರ್‌ವೆಲ್ ಮತ್ತು ಮೋಟಾರ್ ರಿಪೇರಿ',
     'Fixes borewell pumps, submersible motors and water lines',
     'बोरवेल पंप, सबमर्सिबल मोटर और पानी की लाइन ठीक करता है',
     'బోర్‌వెల్ పంపులు, సబ్‌మెర్సిబుల్ మోటర్లు మరియు నీటి లైన్లు బాగు చేస్తారు',
     'बोअरवेल पंप, सबमर्सिबल मोटर आणि पाण्याच्या लाईन दुरुस्त करतात',
     'ಬೋರ್‌ವೆಲ್ ಪಂಪ್, ಸಬ್‌ಮರ್ಸಿಬಲ್ ಮೋಟಾರ್ ಮತ್ತು ನೀರಿನ ಲೈನ್ ರಿಪೇರಿ',
     ARRAY['borewell','bore well','motor','motor repair','pump','submersible','water pump','बोरवेल','मोटर','పంపు','బోరు','మోటర్','बोअरवेल','ಬೋರ್‌ವೆಲ್','ಮೋಟಾರ್']::text[]),
  ('shop_helper',    'sales_telecalling', 'Shop helper',                'दुकान हेल्पर',                'షాప్ హెల్పర్',
     'दुकान हेल्पर',          'ಅಂಗಡಿ ಹೆಲ್ಪರ್',
     'Helps at the counter, stocks shelves and packs orders',
     'काउंटर पर मदद, सामान लगाना और ऑर्डर पैक करना',
     'కౌంటర్‌లో సహాయం, సరుకు సర్దడం మరియు ఆర్డర్లు ప్యాక్ చేయడం',
     'काउंटरवर मदत, माल लावणे आणि ऑर्डर पॅक करणे',
     'ಕೌಂಟರ್‌ನಲ್ಲಿ ಸಹಾಯ, ಸಾಮಾನು ಜೋಡಿಸುವುದು ಮತ್ತು ಆರ್ಡರ್ ಪ್ಯಾಕ್',
     ARRAY['helper','shop boy','shop assistant','dukaan helper','store helper','हेल्पर','दुकान का हेल्पर','हेल्पर','హెల్పర్','షాప్ బాయ్','दुकानातील मदतनीस','ಅಂಗಡಿ ಹುಡುಗ']::text[])
)
INSERT INTO vyapar_listings.taxonomy_terms
  (kind, slug, name_en, name_hi, name_te, name_mr, name_kn, parent_id,
   description_en, description_hi, description_te, description_mr, description_kn, aliases)
SELECT 'capability', t.slug, t.name_en, t.name_hi, t.name_te, t.name_mr, t.name_kn, c.id,
       t.description_en, t.description_hi, t.description_te, t.description_mr, t.description_kn, t.aliases
  FROM terms t
  JOIN vyapar_listings.taxonomy_terms c ON c.kind = 'category' AND c.slug = t.parent
ON CONFLICT (kind, slug) DO UPDATE SET
  parent_id      = EXCLUDED.parent_id,
  description_en = COALESCE(vyapar_listings.taxonomy_terms.description_en, EXCLUDED.description_en),
  description_hi = COALESCE(vyapar_listings.taxonomy_terms.description_hi, EXCLUDED.description_hi),
  description_te = COALESCE(vyapar_listings.taxonomy_terms.description_te, EXCLUDED.description_te),
  description_mr = COALESCE(vyapar_listings.taxonomy_terms.description_mr, EXCLUDED.description_mr),
  description_kn = COALESCE(vyapar_listings.taxonomy_terms.description_kn, EXCLUDED.description_kn),
  name_hi        = COALESCE(vyapar_listings.taxonomy_terms.name_hi, EXCLUDED.name_hi),
  name_te        = COALESCE(vyapar_listings.taxonomy_terms.name_te, EXCLUDED.name_te),
  name_mr        = COALESCE(vyapar_listings.taxonomy_terms.name_mr, EXCLUDED.name_mr),
  name_kn        = COALESCE(vyapar_listings.taxonomy_terms.name_kn, EXCLUDED.name_kn),
  aliases        = (SELECT ARRAY(SELECT DISTINCT a FROM unnest(vyapar_listings.taxonomy_terms.aliases || EXCLUDED.aliases) AS a)),
  updated_at     = now();

-- 4. One clear name for fitness and wellness (decision 13) ---------------------
UPDATE vyapar_listings.taxonomy_terms SET
  name_en = 'Fitness & Wellness',
  name_hi = 'फ़िटनेस और वेलनेस',
  name_te = 'ఫిట్‌నెస్ & వెల్‌నెస్',
  name_mr = 'फिटनेस आणि वेलनेस',
  name_kn = 'ಫಿಟ್‌ನೆಸ್ ಮತ್ತು ವೆಲ್‌ನೆಸ್',
  updated_at = now()
WHERE kind = 'category' AND slug = 'health_wellness'
  AND (name_en IS DISTINCT FROM 'Fitness & Wellness' OR name_te IS DISTINCT FROM 'ఫిట్‌నెస్ & వెల్‌నెస్');
