-- [IMP-B — owner, 2026-09-30: "all the real functionality is actually created
-- as dummy"] Two data fixes behind "tap Plumbers, get 0 opportunities".
--
-- 1. Trade words people actually type. Most skills had no aliases, so a post
--    whose skill was typed as "plumber" (free text) or titled "Need a
--    plumber" never matched the Plumbing skill, and a listing typed as
--    "Electrician" was stored as an unmapped label. Each skill now carries the
--    words a person uses for the worker and the work, in English, Hinglish,
--    Hindi and Telugu. The trade matcher (app/trade_match.py) and the listing
--    taxonomy matcher both read these. Additive: aliases are only appended.
-- 2. seed_batch: a nullable marker on members, listings and opportunities so
--    scripts/seed_marketplace.py can tell its own rows apart, re-run safely
--    and clean up. NULL for every real row; nothing reads it at request time.
-- Traces to: FR04, FR15, FR18, FR48

CREATE OR REPLACE FUNCTION pg_temp.add_aliases(p_slug text, p_aliases text[]) RETURNS void LANGUAGE sql AS $$
  UPDATE vyapar_listings.taxonomy_terms
     SET aliases = ARRAY(SELECT DISTINCT a FROM unnest(aliases || p_aliases) a WHERE a <> '' ORDER BY a),
         updated_at = now()
   WHERE kind = 'capability' AND slug = p_slug;
$$;

SELECT pg_temp.add_aliases('plumbing', ARRAY['plumber','plumbing work','pipe fitting','nal wala','प्लंबर','नलसाज','ప్లంబర్']);
SELECT pg_temp.add_aliases('electrical', ARRAY['electrician','wiring','electrical work','bijli mistri','इलेक्ट्रीशियन','बिजली मिस्त्री','ఎలక్ట్రీషియన్']);
SELECT pg_temp.add_aliases('carpenter', ARRAY['carpentry','woodwork','furniture work','कारपेंटर','बढ़ई','కార్పెంటర్','వడ్రంగి']);
SELECT pg_temp.add_aliases('painter', ARRAY['painting','wall painting','house painting','पेंटर','పెయింటర్']);
SELECT pg_temp.add_aliases('ac_technician', ARRAY['ac repair','ac service','ac mechanic','एसी मैकेनिक','ఏసీ టెక్నీషియన్']);
SELECT pg_temp.add_aliases('tile_fitter', ARRAY['tile fitter','tiles work','टाइल मिस्त्री']);
SELECT pg_temp.add_aliases('mason', ARRAY['masonry','construction worker','राज मिस्त्री','మేస్త్రీ']);
SELECT pg_temp.add_aliases('cook', ARRAY['chef','cooking','kitchen staff','रसोइया','कुक','వంటవాడు','కుక్']);
SELECT pg_temp.add_aliases('driver', ARRAY['driving','cab driver','car driver','ड्राइवर','డ్రైవర్']);
SELECT pg_temp.add_aliases('delivery', ARRAY['delivery executive','delivery rider','डिलीवरी','డెలివరీ']);
SELECT pg_temp.add_aliases('tailoring', ARRAY['tailor','stitching','darzi','दर्जी','टेलर','దర్జీ']);
SELECT pg_temp.add_aliases('beautician', ARRAY['beauty parlour','makeup artist','salon','ब्यूटीशियन','బ్యూటీషియన్']);
SELECT pg_temp.add_aliases('security_guard', ARRAY['security','watchman','guard','सिक्योरिटी गार्ड','సెక్యూరిటీ గార్డ్']);
SELECT pg_temp.add_aliases('maid', ARRAY['house maid','domestic help','kaamwali','घरेलू काम','పనిమనిషి']);
SELECT pg_temp.add_aliases('housekeeping', ARRAY['housekeeper','cleaning staff','हाउसकीपिंग','హౌస్‌కీపింగ్']);
SELECT pg_temp.add_aliases('tutoring', ARRAY['tutor','tuition','home tuition','ट्यूशन','ట్యూషన్']);
SELECT pg_temp.add_aliases('teacher', ARRAY['teaching','टीचर','शिक्षक','టీచర్']);
SELECT pg_temp.add_aliases('accounting', ARRAY['bookkeeping','tally','अकाउंटिंग','అకౌంటింగ్']);
SELECT pg_temp.add_aliases('accountant', ARRAY['accounts assistant','accounts executive','अकाउंटेंट','అకౌంటెంట్']);
SELECT pg_temp.add_aliases('gst_filing', ARRAY['gst','gst return','जीएसटी','జీఎస్టీ']);
SELECT pg_temp.add_aliases('tax', ARRAY['income tax','itr','tax filing','टैक्स','ట్యాక్స్']);
SELECT pg_temp.add_aliases('mechanic', ARRAY['bike mechanic','motor mechanic','मैकेनिक','మెకానిక్']);
SELECT pg_temp.add_aliases('car_repair', ARRAY['car mechanic','garage','car service']);
SELECT pg_temp.add_aliases('telecaller', ARRAY['telecalling','calling executive','टेलीकॉलर','టెలికాలర్']);
SELECT pg_temp.add_aliases('sales', ARRAY['salesman','sales executive','सेल्स','సేల్స్']);
SELECT pg_temp.add_aliases('field_sales', ARRAY['field sales executive','field executive']);
SELECT pg_temp.add_aliases('counter_sales', ARRAY['shop sales','counter staff','showroom sales']);
SELECT pg_temp.add_aliases('data_entry', ARRAY['data entry operator','computer operator','डेटा एंट्री']);
SELECT pg_temp.add_aliases('receptionist', ARRAY['front desk','front office','रिसेप्शनिस्ट']);
SELECT pg_temp.add_aliases('office_assistant', ARRAY['office boy','peon','office helper']);
SELECT pg_temp.add_aliases('software', ARRAY['developer','programmer','software engineer']);
SELECT pg_temp.add_aliases('python', ARRAY['python developer','django']);
SELECT pg_temp.add_aliases('react', ARRAY['react developer','frontend developer','front-end developer']);
SELECT pg_temp.add_aliases('graphic_designer', ARRAY['graphic design','designer','ग्राफिक डिजाइनर']);
SELECT pg_temp.add_aliases('photography', ARRAY['photographer','फोटोग्राफर','ఫోటోగ్రాఫర్']);
SELECT pg_temp.add_aliases('video_editing', ARRAY['video editor','वीडियो एडिटर']);
SELECT pg_temp.add_aliases('bakery', ARRAY['baker','बेकर','బేకర్']);
SELECT pg_temp.add_aliases('cakes', ARRAY['cake maker','home baker']);
SELECT pg_temp.add_aliases('catering', ARRAY['caterer','catering staff','कैटरिंग','క్యాటరింగ్']);
SELECT pg_temp.add_aliases('nurse', ARRAY['nursing','staff nurse','नर्स','నర్స్']);
SELECT pg_temp.add_aliases('labourer', ARRAY['helper','labour','mazdoor','मजदूर','కూలీ']);
SELECT pg_temp.add_aliases('machine_operator', ARRAY['cnc operator','machine operator']);
SELECT pg_temp.add_aliases('digital_marketer', ARRAY['digital marketing','seo']);
SELECT pg_temp.add_aliases('content_writing', ARRAY['content writer','copywriter']);
SELECT pg_temp.add_aliases('social_media', ARRAY['social media manager','instagram marketing']);
SELECT pg_temp.add_aliases('interior_design', ARRAY['interior designer','इंटीरियर डिजाइनर']);
SELECT pg_temp.add_aliases('architecture', ARRAY['architect','आर्किटेक्ट']);
SELECT pg_temp.add_aliases('legal', ARRAY['lawyer','advocate','वकील','న్యాయవాది']);
SELECT pg_temp.add_aliases('yoga', ARRAY['yoga teacher','yoga trainer','योग']);

-- 2 -------------------------------------------------------------------------
ALTER TABLE vyapar_identity.members ADD COLUMN IF NOT EXISTS seed_batch text;
ALTER TABLE vyapar_listings.listings ADD COLUMN IF NOT EXISTS seed_batch text;
ALTER TABLE vyapar_opportunities.opportunities ADD COLUMN IF NOT EXISTS seed_batch text;
COMMENT ON COLUMN vyapar_opportunities.opportunities.seed_batch IS '[IMP-B] Set only by scripts/seed_marketplace.py (dev data); NULL for real posts.';
CREATE INDEX IF NOT EXISTS opportunities_seed_batch_idx ON vyapar_opportunities.opportunities (seed_batch) WHERE seed_batch IS NOT NULL;
CREATE INDEX IF NOT EXISTS listings_seed_batch_idx ON vyapar_listings.listings (seed_batch) WHERE seed_batch IS NOT NULL;
