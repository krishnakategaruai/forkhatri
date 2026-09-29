-- ===========================================================================
-- 022 — Taxonomy: the everyday trade roles migration 018 left out.
--
-- [FE1 — 2026-09-28, critique finding L3] Posting a job for a mason, a
-- welder, a gardener (mali), a packer/loader or a tile fitter found nothing
-- in the skill picker: these are among the most-posted blue-collar roles in
-- the WorkIndia/Apna audience Vyapar serves, and a role that is not in the
-- tree cannot be matched (capability_fit) or filtered on.
--
-- Same shape and rules as 018 §4b: idempotent upsert on (kind, slug), the
-- parent resolved by category slug, real Hindi and Telugu names in the word
-- people actually use (राजमिस्त्री / తాపీ మేస్త్రి, माली / తోటమాలి), a
-- one-line description per language. Names an operator has already set are
-- never overwritten.
--
-- Apply: psql -v ON_ERROR_STOP=1 -U vyapar_owner -d vyapar -f 022-taxonomy-trade-roles.sql
-- The API's taxonomy cache picks the rows up on its next refresh (startup,
-- an admin edit, or hourly).
-- ===========================================================================

WITH terms(slug, parent, name_en, name_hi, name_te, description_en, description_hi, description_te, aliases) AS (VALUES
  ('mason',        'home_repair',              'Mason',                'राजमिस्त्री',               'తాపీ మేస్త్రి',
     'Builds and repairs brick, block and plaster work',            'ईंट, ब्लॉक और प्लास्टर का काम बनाता और सुधारता है',          'ఇటుక, బ్లాక్ మరియు ప్లాస్టర్ పనులు కట్టి, మరమ్మతు చేస్తారు', ARRAY['mistri','raj mistri','construction']::text[]),
  ('tile_fitter',  'home_repair',              'Tile fitter',          'टाइल मिस्त्री',               'టైల్స్ ఫిట్టర్',
     'Lays floor and wall tiles, granite and marble',               'फ़र्श और दीवार की टाइलें, ग्रेनाइट और मार्बल लगाता है',        'నేల మరియు గోడ టైల్స్, గ్రానైట్, మార్బుల్ వేస్తారు', ARRAY['tiles','tiling','flooring']::text[]),
  ('welder',       'manufacturing_labour',     'Welder',               'वेल्डर',                      'వెల్డర్',
     'Welds and fabricates gates, grills and steel frames',         'गेट, ग्रिल और स्टील फ़्रेम की वेल्डिंग और फ़ैब्रिकेशन करता है', 'గేట్లు, గ్రిల్స్ మరియు స్టీల్ ఫ్రేమ్‌ల వెల్డింగ్, ఫ్యాబ్రికేషన్ చేస్తారు', ARRAY['welding','fabricator','fabrication']::text[]),
  ('packer',       'logistics',                'Packer / loader',      'पैकर / लोडर',                'ప్యాకర్ / లోడర్',
     'Packs, loads and unloads goods at warehouses and shops',      'गोदाम और दुकानों में सामान पैक, लोड और अनलोड करता है',        'గిడ్డంగులు, దుకాణాల్లో సరుకు ప్యాక్ చేసి, ఎక్కించి దించుతారు', ARRAY['loader','packing','warehouse helper']::text[]),
  ('gardener',     'hospitality_housekeeping', 'Gardener (mali)',      'माली',                        'తోటమాలి',
     'Looks after gardens, lawns and plants at homes and offices',  'घर और ऑफ़िस के बगीचे, लॉन और पौधों की देखभाल करता है',          'ఇళ్లు, ఆఫీసుల తోటలు, లాన్లు మరియు మొక్కల సంరక్షణ చేస్తారు', ARRAY['mali','garden','landscaping']::text[])
)
INSERT INTO vyapar_listings.taxonomy_terms (kind, slug, name_en, name_hi, name_te, parent_id, description_en, description_hi, description_te, aliases)
SELECT 'capability', t.slug, t.name_en, t.name_hi, t.name_te, c.id, t.description_en, t.description_hi, t.description_te, t.aliases
  FROM terms t
  JOIN vyapar_listings.taxonomy_terms c ON c.kind = 'category' AND c.slug = t.parent
ON CONFLICT (kind, slug) DO UPDATE SET
  parent_id      = EXCLUDED.parent_id,
  description_en = EXCLUDED.description_en,
  description_hi = EXCLUDED.description_hi,
  description_te = EXCLUDED.description_te,
  name_hi        = COALESCE(vyapar_listings.taxonomy_terms.name_hi, EXCLUDED.name_hi),
  name_te        = COALESCE(vyapar_listings.taxonomy_terms.name_te, EXCLUDED.name_te),
  -- search words people type (mali, mistri); an operator's own list is kept
  aliases        = CASE WHEN cardinality(vyapar_listings.taxonomy_terms.aliases) = 0 THEN EXCLUDED.aliases ELSE vyapar_listings.taxonomy_terms.aliases END,
  updated_at     = now();

-- ---------------------------------------------------------------------------
-- Tree corrections (coordinator review of the composer, 2026-09-28):
--  - "Delivery & logistics" as a role repeated its own category's name, so
--    a poster read "Drivers, Delivery & Logistics → Delivery & logistics".
--    The role is what people call the person: a delivery rider.
--  - Wholesale supply is trade, not transport: it moves under Textiles &
--    Retail, and both category one-liners say what they now hold.
-- Idempotent: plain UPDATEs to fixed values.
-- ---------------------------------------------------------------------------
UPDATE vyapar_listings.taxonomy_terms SET
  name_en = 'Delivery rider', name_hi = 'डिलीवरी राइडर', name_te = 'డెలివరీ రైడర్',
  aliases = CASE WHEN cardinality(aliases) = 0 THEN ARRAY['delivery boy','delivery partner','courier','logistics']::text[] ELSE aliases END,
  updated_at = now()
WHERE kind = 'capability' AND slug = 'delivery';

UPDATE vyapar_listings.taxonomy_terms SET
  parent_id = (SELECT id FROM vyapar_listings.taxonomy_terms WHERE kind = 'category' AND slug = 'textiles_retail'),
  updated_at = now()
WHERE kind = 'capability' AND slug = 'wholesale';

UPDATE vyapar_listings.taxonomy_terms SET
  description_en = 'Drivers, delivery riders, packers and transport',
  description_hi = 'ड्राइवर, डिलीवरी राइडर, पैकर और परिवहन',
  description_te = 'డ్రైవర్లు, డెలివరీ రైడర్లు, ప్యాకర్లు మరియు రవాణా',
  updated_at = now()
WHERE kind = 'category' AND slug = 'logistics';

UPDATE vyapar_listings.taxonomy_terms SET
  description_en = 'Textiles, garments, tailoring, retail and wholesale',
  description_hi = 'वस्त्र, कपड़े, सिलाई, खुदरा और थोक',
  description_te = 'వస్త్రాలు, దుస్తులు, కుట్టుపని, రిటైల్ మరియు హోల్‌సేల్',
  updated_at = now()
WHERE kind = 'category' AND slug = 'textiles_retail';
