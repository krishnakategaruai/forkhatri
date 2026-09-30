-- [Backend workstream A, 2026-09-28] Structured opportunities, structured
-- applications with a hiring pipeline, and a two-level taxonomy.
--
-- Why. Vyapar's Opportunity was one free-text form for every type. A person
-- posting a job on WorkIndia fills salary, shift, timings, qualification and
-- openings as fields, and a person posting on Upwork fills budget type,
-- duration, experience level and screening questions. Those fields are what
-- ranking, filters, suggestions and one-tap applications work from, so they
-- become real nullable columns here, per type. The free-text `compensation`
-- column stays and is kept in sync by the service as a derived display
-- string, so nothing that reads it today changes.
--
-- Applications likewise: a proposal carries a bid, a timeline and
-- milestones; an application carries the sender's profile at the moment of
-- applying (a snapshot, so a later profile edit never rewrites what the
-- poster saw). The poster moves each applicant through a pipeline `stage`
-- (new/shortlisted/hired/declined) that is separate from the thread `state`:
-- a thread can be open while the applicant is shortlisted, and hiring is the
-- one stage that also accepts the thread (contact disclosure follows the
-- existing accept path, never a second one).
--
-- Taxonomy: `parent_id` existed since 001 and was never filled, which is why
-- app/services/first_run.py carried a hard-coded category -> skills map.
-- This migration fills the tree (categories -> capabilities), adds one-line
-- plain-language descriptions per language, and seeds the blue-collar roles
-- WorkIndia's audience actually searches for. The data section is
-- idempotent (upsert on (kind, slug)); seeds.sql re-applies it so a fresh
-- database gets the same tree.
-- Traces to: FR11, FR14, FR22, FR23, FR44, FR48, TR011, TR014, TR022, TR023

-- ---------------------------------------------------------------------------
-- 1. Opportunities: typed fields per type (all nullable; a row of another
--    type simply leaves them NULL). Money is stored in paise (bigint) so a
--    salary is never a float.
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_opportunities.opportunities
  -- employment
  ADD COLUMN IF NOT EXISTS salary_min_paise      bigint CHECK (salary_min_paise IS NULL OR salary_min_paise >= 0),
  ADD COLUMN IF NOT EXISTS salary_max_paise      bigint CHECK (salary_max_paise IS NULL OR salary_max_paise >= 0),
  ADD COLUMN IF NOT EXISTS incentive_type        text CHECK (incentive_type IS NULL OR incentive_type IN ('none','fixed_plus_incentive','incentive_only')),
  ADD COLUMN IF NOT EXISTS incentive_max_paise   bigint CHECK (incentive_max_paise IS NULL OR incentive_max_paise >= 0),
  ADD COLUMN IF NOT EXISTS openings              smallint CHECK (openings IS NULL OR openings >= 1),
  ADD COLUMN IF NOT EXISTS shift                 text CHECK (shift IS NULL OR shift IN ('day','night','rotational','flexible')),
  ADD COLUMN IF NOT EXISTS job_timings           text,
  ADD COLUMN IF NOT EXISTS interview_details     text,
  ADD COLUMN IF NOT EXISTS min_qualification     text CHECK (min_qualification IS NULL OR min_qualification IN ('below_10th','10th','12th','diploma','iti','graduate','postgraduate','any')),
  ADD COLUMN IF NOT EXISTS english_level         text CHECK (english_level IS NULL OR english_level IN ('none','basic','good','fluent')),
  ADD COLUMN IF NOT EXISTS experience_min_months smallint CHECK (experience_min_months IS NULL OR experience_min_months >= 0),
  ADD COLUMN IF NOT EXISTS experience_max_months smallint CHECK (experience_max_months IS NULL OR experience_max_months >= 0),
  ADD COLUMN IF NOT EXISTS requires_assets       text[] NOT NULL DEFAULT '{}',
  -- freelance
  ADD COLUMN IF NOT EXISTS budget_type           text CHECK (budget_type IS NULL OR budget_type IN ('fixed','hourly')),
  ADD COLUMN IF NOT EXISTS budget_min_paise      bigint CHECK (budget_min_paise IS NULL OR budget_min_paise >= 0),
  ADD COLUMN IF NOT EXISTS budget_max_paise      bigint CHECK (budget_max_paise IS NULL OR budget_max_paise >= 0),
  ADD COLUMN IF NOT EXISTS hourly_rate_min_paise bigint CHECK (hourly_rate_min_paise IS NULL OR hourly_rate_min_paise >= 0),
  ADD COLUMN IF NOT EXISTS hourly_rate_max_paise bigint CHECK (hourly_rate_max_paise IS NULL OR hourly_rate_max_paise >= 0),
  ADD COLUMN IF NOT EXISTS duration              text CHECK (duration IS NULL OR duration IN ('under_1_week','1_4_weeks','1_3_months','3_6_months','over_6_months','ongoing')),
  ADD COLUMN IF NOT EXISTS experience_level      text CHECK (experience_level IS NULL OR experience_level IN ('entry','intermediate','expert')),
  ADD COLUMN IF NOT EXISTS screening_questions   jsonb NOT NULL DEFAULT '[]',   -- [{id, text}], at most 5 (service-enforced)
  -- local service
  ADD COLUMN IF NOT EXISTS preferred_date        date,
  ADD COLUMN IF NOT EXISTS budget_paise          bigint CHECK (budget_paise IS NULL OR budget_paise >= 0),
  ADD COLUMN IF NOT EXISTS urgency               text CHECK (urgency IS NULL OR urgency IN ('today','this_week','flexible'));

-- ---------------------------------------------------------------------------
-- 2. Enquiries: structured proposal/application fields and the pipeline stage.
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_enquiries.enquiries
  ADD COLUMN IF NOT EXISTS bid_amount_paise  bigint CHECK (bid_amount_paise IS NULL OR bid_amount_paise > 0),
  ADD COLUMN IF NOT EXISTS bid_type          text CHECK (bid_type IS NULL OR bid_type IN ('fixed','hourly')),
  ADD COLUMN IF NOT EXISTS timeline_days     smallint CHECK (timeline_days IS NULL OR timeline_days > 0),
  ADD COLUMN IF NOT EXISTS milestones        jsonb NOT NULL DEFAULT '[]',   -- [{title, amount_paise, due_days}]
  ADD COLUMN IF NOT EXISTS screening_answers jsonb NOT NULL DEFAULT '[]',   -- [{question_id, answer}]
  ADD COLUMN IF NOT EXISTS applied_via       text NOT NULL DEFAULT 'form' CHECK (applied_via IN ('form','one_tap','voice','agent')),
  ADD COLUMN IF NOT EXISTS profile_snapshot  jsonb,                          -- sender's profile at the moment of applying
  ADD COLUMN IF NOT EXISTS stage             text NOT NULL DEFAULT 'new' CHECK (stage IN ('new','shortlisted','hired','declined')),
  ADD COLUMN IF NOT EXISTS stage_changed_at  timestamptz;

-- The poster's applicant list reads by opportunity and stage.
CREATE INDEX IF NOT EXISTS enquiries_opportunity_stage_idx
  ON vyapar_enquiries.enquiries (opportunity_id, stage, created_at DESC)
  WHERE opportunity_id IS NOT NULL;

-- Pipeline domain events, same outbox and same shape as migration 016's
-- enquiry events: identifiers and states only, never message bodies or
-- contact details; `audience` names the two parties.
CREATE OR REPLACE FUNCTION vyapar_enquiries.emit_applicant_stage_event() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_enquiries, pg_temp AS $$
BEGIN
  IF NEW.stage IS DISTINCT FROM OLD.stage AND NEW.stage IN ('shortlisted','hired','declined') THEN
    INSERT INTO vyapar_enquiries.outbox_event (event_type, payload) VALUES ('applicant.' || NEW.stage, jsonb_build_object(
      'id', NEW.id, 'sender_id', NEW.sender_id, 'provider_id', NEW.provider_id,
      'opportunity_id', NEW.opportunity_id, 'stage', NEW.stage, 'previous_stage', OLD.stage,
      'thread_state', NEW.state,
      'audience', jsonb_build_array(NEW.sender_id, NEW.provider_id)));
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS enquiries_emit_stage_event ON vyapar_enquiries.enquiries;
CREATE TRIGGER enquiries_emit_stage_event AFTER UPDATE OF stage ON vyapar_enquiries.enquiries
  FOR EACH ROW EXECUTE FUNCTION vyapar_enquiries.emit_applicant_stage_event();

-- ---------------------------------------------------------------------------
-- 3. Taxonomy: one-line descriptions per language. `parent_id` already
--    exists (001) and is filled by the data section below.
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_listings.taxonomy_terms
  ADD COLUMN IF NOT EXISTS description_en text,
  ADD COLUMN IF NOT EXISTS description_hi text,
  ADD COLUMN IF NOT EXISTS description_te text;

CREATE INDEX IF NOT EXISTS taxonomy_terms_parent_idx ON vyapar_listings.taxonomy_terms (parent_id);

-- ---------------------------------------------------------------------------
-- 4. Data: the two-level tree. Idempotent: every row is an upsert on
--    (kind, slug). Names of pre-existing rows are left as they are (only
--    description and parent are set); new rows get full names in en/hi/te.
--    Hindi and Telugu use the everyday word where one exists (बढ़ई, वड्रंगి,
--    रसोइया, मज़दूर) and the borrowed word where that is what people say
--    (ड्राइवर, टेलीकॉलर, AC टेक्नीशियन).
-- ---------------------------------------------------------------------------

-- 4a. Categories (parents). New ones are inserted; existing ones get a
--     description (and "logistics" a name that says who it is for).
INSERT INTO vyapar_listings.taxonomy_terms (kind, slug, name_en, name_hi, name_te, icon, description_en, description_hi, description_te) VALUES
('category','accounting_tax',        'Accounting & Tax',              'लेखा और कर',                  'అకౌంటింగ్ & పన్ను',            'calculate',
   'Bookkeeping, tax filing, GST and audit help',            'बहीखाता, टैक्स फाइलिंग, GST और ऑडिट सहायता',            'బుక్కీపింగ్, టాక్స్ ఫైలింగ్, GST మరియు ఆడిట్ సహాయం'),
('category','legal',                 'Legal Services',                'कानूनी सेवाएँ',                'న్యాయ సేవలు',                  'gavel',
   'Legal advice, documentation and compliance',             'कानूनी सलाह, दस्तावेज़ीकरण और अनुपालन',                  'న్యాయ సలహా, డాక్యుమెంటేషన్ మరియు కంప్లయన్స్'),
('category','home_repair',           'Home Repair & Trades',          'घर की मरम्मत',                 'ఇంటి మరమ్మతులు',                'home_repair_service',
   'Plumbing, electrical, carpentry, painting and AC work',  'प्लंबिंग, इलेक्ट्रिकल, बढ़ईगीरी, पुताई और AC का काम',       'ప్లంబింగ్, ఎలక్ట్రికల్, వడ్రంగం, పెయింటింగ్ మరియు AC పని'),
('category','food_catering',         'Food & Catering',               'भोजन और केटरिंग',              'ఆహారం & క్యాటరింగ్',            'restaurant',
   'Catering, baking and food service',                      'कैटरिंग, बेकिंग और फूड सेवा',                            'క్యాటరింగ్, బేకింగ్ మరియు ఫుడ్ సర్వీస్'),
('category','textiles_retail',       'Textiles & Retail',             'वस्त्र और खुदरा',               'వస్త్రాలు & రిటైల్',            'checkroom',
   'Textiles, garments, tailoring and retail',               'कपड़े, परिधान, सिलाई और रिटेल',                          'టెక్స్‌టైల్స్, గార్మెంట్స్, టైలరింగ్ మరియు రిటైల్'),
('category','software_it',           'Software & IT',                 'सॉफ्टवेयर और आईटी',            'సాఫ్ట్‌వేర్ & ఐటీ',              'code',
   'Software, IT and technology services',                   'सॉफ़्टवेयर, IT और टेक्नोलॉजी सेवाएँ',                     'సాఫ్ట్‌వేర్, IT మరియు టెక్నాలజీ సేవలు'),
('category','education',             'Education & Tutoring',          'शिक्षा और ट्यूशन',             'విద్య & ట్యూషన్',               'school',
   'Teaching, tutoring, coaching and skill classes',         'शिक्षण, ट्यूशन, कोचिंग और स्किल क्लासेज़',                 'బోధన, ట్యూషన్, కోచింగ్ మరియు స్కిల్ క్లాసులు'),
('category','design_architecture',   'Design & Architecture',         'डिज़ाइन और वास्तुकला',         'డిజైన్ & ఆర్కిటెక్చర్',         'architecture',
   'Architecture, interiors and design services',            'आर्किटेक्चर, इंटीरियर और डिज़ाइन सेवाएँ',                 'ఆర్కిటెక్చర్, ఇంటీరియర్స్ మరియు డిజైన్ సేవలు'),
('category','media_photo',           'Photography & Media',           'फोटोग्राफी और मीडिया',         'ఫోటోగ్రఫీ & మీడియా',            'photo_camera',
   'Photography, video, graphic design and content',         'फोटोग्राफी, वीडियो, ग्राफ़िक डिज़ाइन और कंटेंट',            'ఫోటోగ్రఫీ, వీడియో, గ్రాఫిక్ డిజైన్ మరియు కంటెంట్'),
('category','health_wellness',       'Health & Wellness',             'स्वास्थ्य',                    'ఆరోగ్యం',                      'spa',
   'Fitness, yoga and wellness services',                    'फिटनेस, योग और वेलनेस सेवाएँ',                            'ఫిట్‌నెస్, యోగా మరియు వెల్‌నెస్ సేవలు'),
('category','automotive',            'Automotive',                    'ऑटोमोटिव',                    'ఆటోమోటివ్',                    'directions_car',
   'Vehicle repair, servicing and parts',                    'वाहन मरम्मत, सर्विसिंग और पार्ट्स',                       'వాహన మరమ్మత్తు, సర్వీసింగ్ మరియు పార్ట్స్'),
('category','events',                'Events & Decor',                'कार्यक्रम और सजावट',           'ఈవెంట్స్ & డెకర్',              'celebration',
   'Event planning, decor and management',                   'इवेंट योजना, सजावट और प्रबंधन',                          'ఈవెంట్ ప్లానింగ్, డెకర్ మరియు మేనేజ్‌మెంట్'),
('category','logistics',             'Drivers, Delivery & Logistics', 'ड्राइवर, डिलीवरी और लॉजिस्टिक्स', 'డ్రైవర్లు, డెలివరీ & లాజిస్టిక్స్', 'local_shipping',
   'Drivers, delivery, transport and wholesale supply',      'ड्राइवर, डिलीवरी, परिवहन और थोक आपूर्ति',                 'డ్రైవర్లు, డెలివరీ, రవాణా మరియు హోల్‌సేల్ సరఫరా'),
('category','printing',              'Printing & Signage',            'प्रिंटिंग',                    'ప్రింటింగ్',                    'print',
   'Printing and signage services',                          'प्रिंटिंग और साइनेज सेवाएँ',                              'ప్రింటింగ్ మరియు సైనేజ్ సేవలు'),
('category','handicraft',            'Handicraft & Artisans',         'हस्तशिल्प',                    'హస్తకళలు',                     'palette',
   'Handmade goods and traditional crafts',                  'हस्तनिर्मित सामान और पारंपरिक शिल्प',                    'చేతితో తయారు చేసిన వస్తువులు మరియు సంప్రదాయ కళలు'),
('category','marketing',             'Marketing & Content',           'मार्केटिंग',                   'మార్కెటింగ్',                   'campaign',
   'Marketing, social media, writing and digital growth',    'मार्केटिंग, सोशल मीडिया, लेखन और डिजिटल ग्रोथ',            'మార్కెటింగ్, సోషల్ మీడియా, రైటింగ్ మరియు డిజిటల్ గ్రోత్'),
-- new categories
('category','hospitality_housekeeping','Hospitality & Housekeeping',  'आतिथ्य और हाउसकीपिंग',         'ఆతిథ్యం & హౌస్‌కీపింగ్',        'cleaning_services',
   'Cooking, cleaning, security and domestic help',          'खाना बनाना, सफ़ाई, सुरक्षा और घरेलू सहायता',                'వంట, శుభ్రత, భద్రత మరియు ఇంటి సహాయం'),
('category','sales_telecalling',     'Sales & Telecalling',           'सेल्स और टेलीकॉलिंग',           'సేల్స్ & టెలీకాలింగ్',           'support_agent',
   'Field sales, counter sales, telecalling and BPO',        'फ़ील्ड सेल्स, काउंटर सेल्स, टेलीकॉलिंग और BPO',             'ఫీల్డ్ సేల్స్, కౌంటర్ సేల్స్, టెలీకాలింగ్ మరియు BPO'),
('category','office_admin',          'Office & Admin',                'ऑफ़िस और प्रशासन',             'ఆఫీస్ & అడ్మిన్',               'badge',
   'Reception, office assistance and data entry',            'रिसेप्शन, ऑफ़िस सहायता और डेटा एंट्री',                     'రిసెప్షన్, ఆఫీస్ సహాయం మరియు డేటా ఎంట్రీ'),
('category','healthcare',            'Healthcare',                    'स्वास्थ्य सेवा',               'ఆరోగ్య సేవలు',                 'medical_services',
   'Nursing, lab and clinic staff',                          'नर्सिंग, लैब और क्लिनिक स्टाफ़',                           'నర్సింగ్, ల్యాబ్ మరియు క్లినిక్ సిబ్బంది'),
('category','manufacturing_labour',  'Manufacturing & Labour',        'निर्माण और श्रमिक',             'తయారీ & కూలీ పని',              'precision_manufacturing',
   'Machine operators, helpers and general labour',          'मशीन ऑपरेटर, हेल्पर और सामान्य श्रमिक',                   'మెషిన్ ఆపరేటర్లు, హెల్పర్లు మరియు సాధారణ కూలీ పని'),
('category','beauty_personal_care',  'Beauty & Personal Care',        'ब्यूटी और पर्सनल केयर',         'బ్యూటీ & పర్సనల్ కేర్',          'face',
   'Beauticians, salon and grooming services',               'ब्यूटीशियन, सैलून और ग्रूमिंग सेवाएँ',                     'బ్యూటీషియన్లు, సెలూన్ మరియు గ్రూమింగ్ సేవలు')
ON CONFLICT (kind, slug) DO UPDATE SET
  description_en = EXCLUDED.description_en,
  description_hi = EXCLUDED.description_hi,
  description_te = EXCLUDED.description_te,
  icon = COALESCE(vyapar_listings.taxonomy_terms.icon, EXCLUDED.icon),
  -- only "logistics" is renamed (it now names drivers and delivery too); every other existing name is kept
  name_en = CASE WHEN vyapar_listings.taxonomy_terms.slug = 'logistics' THEN EXCLUDED.name_en ELSE vyapar_listings.taxonomy_terms.name_en END,
  name_hi = CASE WHEN vyapar_listings.taxonomy_terms.slug = 'logistics' THEN EXCLUDED.name_hi ELSE vyapar_listings.taxonomy_terms.name_hi END,
  name_te = CASE WHEN vyapar_listings.taxonomy_terms.slug = 'logistics' THEN EXCLUDED.name_te ELSE vyapar_listings.taxonomy_terms.name_te END,
  updated_at = now();

-- 4b. Capabilities (children). `parent` is a category slug resolved below.
WITH terms(slug, parent, name_en, name_hi, name_te, description_en, description_hi, description_te) AS (VALUES
  -- existing skills: parent + description (names kept as seeded)
  ('accounting',         'accounting_tax',       'Accounting',              'लेखांकन',                'అకౌంటింగ్',
     'Bookkeeping and accounts for small businesses',              'छोटे व्यवसायों के लिए बहीखाता और हिसाब',                        'చిన్న వ్యాపారాలకు బుక్కీపింగ్ మరియు ఖాతాలు'),
  ('gst_filing',         'accounting_tax',       'GST filing',              'जीएसटी फाइलिंग',          'GST ఫైలింగ్',
     'GST registration and monthly returns',                      'GST पंजीकरण और मासिक रिटर्न',                                 'GST రిజిస్ట్రేషన్ మరియు నెలవారీ రిటర్న్‌లు'),
  ('tax',                'accounting_tax',       'Income tax',              'आयकर',                   'ఆదాయపు పన్ను',
     'Income tax returns and planning',                           'आयकर रिटर्न और योजना',                                        'ఆదాయపు పన్ను రిటర్న్‌లు మరియు ప్లానింగ్'),
  ('plumbing',           'home_repair',          'Plumbing',                'प्लंबिंग',                'ప్లంబింగ్',
     'Pipes, taps, leaks and bathroom fittings',                  'पाइप, नल, रिसाव और बाथरूम फिटिंग',                             'పైపులు, కుళాయిలు, లీకులు మరియు బాత్రూమ్ ఫిట్టింగ్‌లు'),
  ('electrical',         'home_repair',          'Electrical work',         'बिजली का काम',            'ఎలక్ట్రికల్',
     'Wiring, fittings and electrical repairs',                   'वायरिंग, फिटिंग और बिजली की मरम्मत',                           'వైరింగ్, ఫిట్టింగ్‌లు మరియు ఎలక్ట్రికల్ మరమ్మతులు'),
  ('catering',           'food_catering',        'Catering',                'केटरिंग',                 'క్యాటరింగ్',
     'Food for weddings, functions and office meals',             'शादी, समारोह और ऑफ़िस भोजन के लिए खाना',                      'పెళ్లిళ్లు, వేడుకలు మరియు ఆఫీస్ భోజనాలకు ఆహారం'),
  ('events',             'events',               'Event management',        'इवेंट प्रबंधन',            'ఈవెంట్ నిర్వహణ',
     'Plans and runs weddings, functions and corporate events',   'शादी, समारोह और कॉर्पोरेट इवेंट की योजना और संचालन',            'పెళ్లిళ్లు, వేడుకలు మరియు కార్పొరేట్ ఈవెంట్లను ప్లాన్ చేసి నిర్వహిస్తారు'),
  ('textiles',           'textiles_retail',      'Textiles',                'वस्त्र',                  'వస్త్రాలు',
     'Fabrics, sarees and garment supply',                        'कपड़े, साड़ियाँ और परिधान आपूर्ति',                            'బట్టలు, చీరలు మరియు దుస్తుల సరఫరా'),
  ('wholesale',          'logistics',            'Wholesale supply',        'थोक आपूर्ति',              'హోల్‌సేల్',
     'Bulk supply to shops and traders',                          'दुकानों और व्यापारियों को थोक आपूर्ति',                        'దుకాణాలు మరియు వ్యాపారులకు హోల్‌సేల్ సరఫరా'),
  ('software',           'software_it',          'Software development',    'सॉफ्टवेयर विकास',         'సాఫ్ట్‌వేర్ అభివృద్ధి',
     'Builds apps, websites and software systems',                'ऐप, वेबसाइट और सॉफ़्टवेयर सिस्टम बनाता है',                    'యాప్‌లు, వెబ్‌సైట్లు మరియు సాఫ్ట్‌వేర్ సిస్టమ్స్ నిర్మిస్తారు'),
  ('react',              'software_it',          'React / frontend',        'रिएक्ट',                  'రియాక్ట్',
     'Web and mobile front-ends in React',                        'React में वेब और मोबाइल फ़्रंट-एंड',                            'Reactలో వెబ్ మరియు మొబైల్ ఫ్రంట్-ఎండ్'),
  ('python',             'software_it',          'Python / backend',        'पायथन',                   'పైథాన్',
     'Back-end services, scripts and data work in Python',        'Python में बैक-एंड सेवाएँ, स्क्रिप्ट और डेटा काम',              'Pythonలో బ్యాక్-ఎండ్ సేవలు, స్క్రిప్టులు మరియు డేటా పని'),
  ('tutoring',           'education',            'Tutoring',                'ट्यूशन',                  'ట్యూషన్',
     'Home or online tuition for school and college subjects',    'स्कूल और कॉलेज के विषयों की घर या ऑनलाइन ट्यूशन',              'పాఠశాల, కళాశాల సబ్జెక్టులకు ఇంటి లేదా ఆన్‌లైన్ ట్యూషన్'),
  ('mathematics',        'education',            'Mathematics',             'गणित',                    'గణితం',
     'Maths coaching for school and entrance exams',              'स्कूल और प्रवेश परीक्षाओं के लिए गणित कोचिंग',                  'పాఠశాల మరియు ప్రవేశ పరీక్షలకు గణిత కోచింగ్'),
  ('bakery',             'food_catering',        'Baking',                  'बेकरी',                   'బేకరీ',
     'Breads, biscuits and baked snacks',                         'ब्रेड, बिस्किट और बेक्ड स्नैक्स',                               'బ్రెడ్, బిస్కెట్లు మరియు బేక్డ్ స్నాక్స్'),
  ('cakes',              'food_catering',        'Custom cakes',            'कस्टम केक',               'కస్టమ్ కేకులు',
     'Custom cakes for birthdays and occasions',                  'जन्मदिन और अवसरों के लिए कस्टम केक',                          'పుట్టినరోజులు మరియు సందర్భాలకు కస్టమ్ కేకులు'),
  ('architecture',       'design_architecture',  'Architecture',            'वास्तुकला',                'ఆర్కిటెక్చర్',
     'Building plans, approvals and site supervision',            'भवन योजना, स्वीकृति और साइट पर्यवेक्षण',                       'భవన ప్రణాళికలు, అనుమతులు మరియు సైట్ పర్యవేక్షణ'),
  ('interior_design',    'design_architecture',  'Interior design',         'इंटीरियर डिज़ाइन',         'ఇంటీరియర్ డిజైన్',
     'Home and office interiors, furniture and lighting',         'घर और ऑफ़िस इंटीरियर, फ़र्नीचर और लाइटिंग',                    'ఇల్లు మరియు ఆఫీస్ ఇంటీరియర్స్, ఫర్నిచర్ మరియు లైటింగ్'),
  ('legal',              'legal',                'Legal advice',            'कानूनी सलाह',              'న్యాయ సలహా',
     'Advice, notices, agreements and court matters',             'सलाह, नोटिस, समझौते और अदालती मामले',                          'సలహా, నోటీసులు, ఒప్పందాలు మరియు కోర్టు వ్యవహారాలు'),
  ('property_law',       'legal',                'Property law',            'संपत्ति कानून',            'ఆస్తి చట్టం',
     'Property registration, disputes and documents',             'संपत्ति पंजीकरण, विवाद और दस्तावेज़',                          'ఆస్తి రిజిస్ట్రేషన్, వివాదాలు మరియు పత్రాలు'),
  ('photography',        'media_photo',          'Photography',             'फोटोग्राफी',               'ఫోటోగ్రఫీ',
     'Event, product and portrait photography',                   'इवेंट, प्रोडक्ट और पोर्ट्रेट फोटोग्राफी',                       'ఈవెంట్, ప్రొడక్ట్ మరియు పోర్ట్రెయిట్ ఫోటోగ్రఫీ'),
  ('video_editing',      'media_photo',          'Video editing',           'वीडियो संपादन',            'వీడియో ఎడిటింగ్',
     'Edits videos for events, reels and ads',                    'इवेंट, रील और विज्ञापनों के लिए वीडियो एडिट करता है',            'ఈవెంట్లు, రీల్స్ మరియు ప్రకటనల కోసం వీడియోలు ఎడిట్ చేస్తారు'),
  ('car_repair',         'automotive',           'Car repair',              'कार मरम्मत',               'కారు మరమ్మతు',
     'Car servicing, repairs and parts',                          'कार सर्विसिंग, मरम्मत और पार्ट्स',                              'కారు సర్వీసింగ్, మరమ్మతులు మరియు పార్ట్స్'),
  ('yoga',               'health_wellness',      'Yoga instruction',        'योग',                     'యోగా',
     'Yoga classes for individuals and groups',                   'व्यक्तियों और समूहों के लिए योग कक्षाएँ',                        'వ్యక్తులు మరియు సమూహాలకు యోగా తరగతులు'),
  ('product_management', 'software_it',          'Product management',      'उत्पाद प्रबंधन',           'ప్రొడక్ట్ మేనేజ్‌మెంట్',
     'Defines what to build and runs the product roadmap',        'क्या बनाना है तय करता है और प्रोडक्ट रोडमैप चलाता है',           'ఏమి నిర్మించాలో నిర్ణయించి ప్రొడక్ట్ రోడ్‌మ్యాప్ నడిపిస్తారు'),
  ('startup',            'software_it',          'Startup operations',      'स्टार्टअप',                'స్టార్టప్',
     'Early-stage operations, fundraising and growth',            'शुरुआती चरण का संचालन, फ़ंडिंग और ग्रोथ',                       'ప్రారంభ దశ కార్యకలాపాలు, నిధుల సేకరణ మరియు వృద్ధి'),
  ('content_writing',    'marketing',            'Content writing',         'कंटेंट लेखन',              'కంటెంట్ రైటింగ్',
     'Writes website copy, blogs and ad text',                    'वेबसाइट, ब्लॉग और विज्ञापन के लिए लिखता है',                    'వెబ్‌సైట్ కాపీ, బ్లాగులు మరియు ప్రకటన టెక్స్ట్ రాస్తారు'),
  ('social_media',       'marketing',            'Social media',            'सोशल मीडिया',              'సోషల్ మీడియా',
     'Manages pages, posts and followers',                        'पेज, पोस्ट और फ़ॉलोअर्स संभालता है',                           'పేజీలు, పోస్టులు మరియు ఫాలోవర్లను నిర్వహిస్తారు'),
  ('sales',              'sales_telecalling',    'Sales',                   'बिक्री',                   'అమ్మకాలు',
     'Sells products or services to customers',                   'ग्राहकों को उत्पाद या सेवाएँ बेचता है',                        'కస్టమర్లకు ఉత్పత్తులు లేదా సేవలు అమ్ముతారు'),
  ('delivery',           'logistics',            'Delivery & logistics',    'डिलीवरी',                  'డెలివరీ',
     'Delivers parcels, food or goods by bike or van',            'बाइक या वैन से पार्सल, खाना या सामान पहुँचाता है',               'బైక్ లేదా వ్యాన్‌లో పార్సెల్స్, ఆహారం లేదా సరుకులు డెలివరీ చేస్తారు'),
  ('tailoring',          'textiles_retail',      'Tailoring',               'सिलाई',                   'కుట్టుపని',
     'Stitches and alters garments',                              'कपड़े सिलता और बदलता है',                                     'బట్టలు కుడతారు మరియు మార్పులు చేస్తారు'),
  ('printing',           'printing',             'Printing',                'प्रिंटिंग',                'ప్రింటింగ్',
     'Flex, visiting cards, banners and offset printing',         'फ़्लेक्स, विज़िटिंग कार्ड, बैनर और ऑफ़सेट प्रिंटिंग',              'ఫ్లెక్స్, విజిటింగ్ కార్డులు, బ్యానర్లు మరియు ఆఫ్‌సెట్ ప్రింటింగ్'),
  ('handicraft',         'handicraft',           'Handicraft',              'हस्तशिल्प',                'హస్తకళ',
     'Handmade goods, decor and traditional crafts',              'हस्तनिर्मित सामान, सजावट और पारंपरिक शिल्प',                    'చేతితో తయారు చేసిన వస్తువులు, అలంకరణ మరియు సంప్రదాయ కళలు'),
  -- new blue-collar and service roles
  ('driver',             'logistics',            'Driver',                  'ड्राइवर',                  'డ్రైవర్',
     'Drives cars, vans or commercial vehicles for a business or family', 'व्यवसाय या परिवार के लिए कार, वैन या व्यावसायिक वाहन चलाता है', 'వ్యాపారం లేదా కుటుంబం కోసం కారు, వ్యాన్ లేదా వాణిజ్య వాహనాలు నడుపుతారు'),
  ('cook',               'hospitality_housekeeping', 'Cook',                'रसोइया',                   'వంటవారు',
     'Prepares meals at homes, hostels, canteens or restaurants', 'घरों, हॉस्टल, कैंटीन या रेस्तरां में खाना बनाता है',              'ఇళ్లు, హాస్టళ్లు, క్యాంటీన్లు లేదా రెస్టారెంట్లలో భోజనం తయారు చేస్తారు'),
  ('security_guard',     'hospitality_housekeeping', 'Security guard',      'सुरक्षा गार्ड',             'సెక్యూరిటీ గార్డ్',
     'Guards buildings, gates and premises in shifts',            'शिफ्ट में इमारतों, गेट और परिसर की सुरक्षा करता है',              'షిఫ్టుల్లో భవనాలు, గేట్లు మరియు ప్రాంగణాలకు కాపలా కాస్తారు'),
  ('housekeeping',       'hospitality_housekeeping', 'Housekeeping',        'हाउसकीपिंग',               'హౌస్‌కీపింగ్',
     'Cleans and maintains offices, hotels and hospitals',        'ऑफ़िस, होटल और अस्पतालों की सफ़ाई और रखरखाव करता है',            'ఆఫీసులు, హోటళ్లు మరియు ఆసుపత్రులను శుభ్రం చేసి నిర్వహిస్తారు'),
  ('maid',               'hospitality_housekeeping', 'Domestic help',       'घरेलू सहायिका',             'ఇంటి పనిమనిషి',
     'Helps with cleaning, washing and daily chores at home',     'घर में सफ़ाई, धुलाई और रोज़ के काम में मदद करती है',              'ఇంట్లో శుభ్రత, బట్టలు ఉతకడం మరియు రోజువారీ పనుల్లో సహాయం చేస్తారు'),
  ('telecaller',         'sales_telecalling',    'Telecaller / BPO',        'टेलीकॉलर / BPO',            'టెలీకాలర్ / BPO',
     'Makes or answers calls for sales, support or surveys',      'सेल्स, सपोर्ट या सर्वे के लिए कॉल करता या उठाता है',             'సేల్స్, సపోర్ట్ లేదా సర్వేల కోసం కాల్స్ చేస్తారు లేదా అందుకుంటారు'),
  ('field_sales',        'sales_telecalling',    'Field sales',             'फ़ील्ड सेल्स',              'ఫీల్డ్ సేల్స్',
     'Visits shops and customers to sell products',               'उत्पाद बेचने के लिए दुकानों और ग्राहकों के पास जाता है',           'ఉత్పత్తులు అమ్మడానికి దుకాణాలు మరియు కస్టమర్లను సందర్శిస్తారు'),
  ('counter_sales',      'sales_telecalling',    'Counter sales',           'काउंटर सेल्स',              'కౌంటర్ సేల్స్',
     'Serves customers at a shop or showroom counter',            'दुकान या शोरूम के काउंटर पर ग्राहकों को सेवा देता है',             'దుకాణం లేదా షోరూమ్ కౌంటర్ వద్ద కస్టమర్లకు సేవ చేస్తారు'),
  ('receptionist',       'office_admin',         'Receptionist',            'रिसेप्शनिस्ट',              'రిసెప్షనిస్ట్',
     'Greets visitors, handles calls and appointments',           'आगंतुकों का स्वागत, कॉल और अपॉइंटमेंट संभालता है',                'సందర్శకులను స్వాగతించి, కాల్స్ మరియు అపాయింట్‌మెంట్లు నిర్వహిస్తారు'),
  ('office_assistant',   'office_admin',         'Office assistant',        'ऑफ़िस असिस्टेंट',           'ఆఫీస్ అసిస్టెంట్',
     'Handles files, errands and day-to-day office support',      'फ़ाइलें, छोटे-मोटे काम और रोज़ का ऑफ़िस सपोर्ट संभालता है',        'ఫైళ్లు, చిన్న పనులు మరియు రోజువారీ ఆఫీస్ సపోర్ట్ చూసుకుంటారు'),
  ('data_entry',         'office_admin',         'Data entry',              'डेटा एंट्री',               'డేటా ఎంట్రీ',
     'Types records and forms into computers accurately',         'रिकॉर्ड और फ़ॉर्म को सही-सही कंप्यूटर में दर्ज करता है',           'రికార్డులు మరియు ఫారాలను కంప్యూటర్‌లో ఖచ్చితంగా టైప్ చేస్తారు'),
  ('accountant',         'accounting_tax',       'Accountant',              'अकाउंटेंट',                 'అకౌంటెంట్',
     'Keeps books, bills and monthly accounts for a business',    'व्यवसाय के बहीखाते, बिल और मासिक हिसाब रखता है',                 'వ్యాపారానికి ఖాతాలు, బిల్లులు మరియు నెలవారీ లెక్కలు చూసుకుంటారు'),
  ('machine_operator',   'manufacturing_labour', 'Machine operator',        'मशीन ऑपरेटर',               'మెషిన్ ఆపరేటర్',
     'Runs production machines in a factory or workshop',         'फ़ैक्टरी या वर्कशॉप में उत्पादन मशीनें चलाता है',                 'ఫ్యాక్టరీ లేదా వర్క్‌షాప్‌లో ఉత్పత్తి యంత్రాలు నడుపుతారు'),
  ('labourer',           'manufacturing_labour', 'Labourer / helper',       'मज़दूर / हेल्पर',            'కూలీ / హెల్పర్',
     'General manual work: loading, site help and shop help',     'सामान्य शारीरिक काम: लोडिंग, साइट और दुकान में मदद',              'సాధారణ శారీరక పని: లోడింగ్, సైట్ మరియు దుకాణంలో సహాయం'),
  ('carpenter',          'home_repair',          'Carpenter',               'बढ़ई',                     'వడ్రంగి',
     'Makes and repairs furniture, doors and woodwork',           'फ़र्नीचर, दरवाज़े और लकड़ी का काम बनाता और सुधारता है',           'ఫర్నిచర్, తలుపులు మరియు చెక్క పని చేస్తారు, మరమ్మతు చేస్తారు'),
  ('painter',            'home_repair',          'Painter',                 'पेंटर',                    'పెయింటర్',
     'Paints homes, shops and offices, inside and out',           'घर, दुकान और ऑफ़िस की अंदर-बाहर पुताई करता है',                  'ఇళ్లు, దుకాణాలు మరియు ఆఫీసులకు లోపల, బయట రంగులు వేస్తారు'),
  ('ac_technician',      'home_repair',          'AC technician',           'AC टेक्नीशियन',             'AC టెక్నీషియన్',
     'Installs and services air conditioners and coolers',        'एयर कंडीशनर और कूलर लगाता और सर्विस करता है',                    'ఎయిర్ కండిషనర్లు మరియు కూలర్లు అమర్చి, సర్వీస్ చేస్తారు'),
  ('mechanic',           'automotive',           'Mechanic',                'मैकेनिक',                  'మెకానిక్',
     'Repairs and services two-wheelers and cars',                'दोपहिया और कारों की मरम्मत और सर्विस करता है',                   'ద్విచక్ర వాహనాలు మరియు కార్లను మరమ్మతు చేసి సర్వీస్ చేస్తారు'),
  ('beautician',         'beauty_personal_care', 'Beautician',              'ब्यूटीशियन',                'బ్యూటీషియన్',
     'Hair, skin, makeup and salon services',                     'बाल, त्वचा, मेकअप और सैलून सेवाएँ',                             'జుట్టు, చర్మం, మేకప్ మరియు సెలూన్ సేవలు'),
  ('nurse',              'healthcare',           'Nurse',                   'नर्स',                     'నర్స్',
     'Patient care at hospitals, clinics or homes',               'अस्पताल, क्लिनिक या घर पर मरीज़ की देखभाल',                      'ఆసుపత్రులు, క్లినిక్‌లు లేదా ఇళ్లలో రోగుల సంరక్షణ'),
  ('lab_technician',     'healthcare',           'Lab technician',          'लैब टेक्नीशियन',            'ల్యాబ్ టెక్నీషియన్',
     'Collects samples and runs diagnostic tests',                'सैंपल लेता है और जाँच करता है',                                'నమూనాలు సేకరించి డయాగ్నస్టిక్ పరీక్షలు చేస్తారు'),
  ('teacher',            'education',            'Teacher',                 'शिक्षक',                   'ఉపాధ్యాయుడు',
     'Teaches at a school, college or coaching centre',           'स्कूल, कॉलेज या कोचिंग सेंटर में पढ़ाता है',                     'పాఠశాల, కళాశాల లేదా కోచింగ్ సెంటర్‌లో బోధిస్తారు'),
  ('graphic_designer',   'media_photo',          'Graphic design',          'ग्राफ़िक डिज़ाइन',          'గ్రాఫిక్ డిజైన్',
     'Logos, posters, social creatives and print design',         'लोगो, पोस्टर, सोशल क्रिएटिव और प्रिंट डिज़ाइन',                  'లోగోలు, పోస్టర్లు, సోషల్ క్రియేటివ్స్ మరియు ప్రింట్ డిజైన్'),
  ('digital_marketer',   'marketing',            'Digital marketing',       'डिजिटल मार्केटिंग',         'డిజిటల్ మార్కెటింగ్',
     'Runs online ads, SEO and social media growth',              'ऑनलाइन विज्ञापन, SEO और सोशल मीडिया ग्रोथ चलाता है',              'ఆన్‌లైన్ ప్రకటనలు, SEO మరియు సోషల్ మీడియా గ్రోత్ నిర్వహిస్తారు')
)
INSERT INTO vyapar_listings.taxonomy_terms (kind, slug, name_en, name_hi, name_te, parent_id, description_en, description_hi, description_te)
SELECT 'capability', t.slug, t.name_en, t.name_hi, t.name_te, c.id, t.description_en, t.description_hi, t.description_te
  FROM terms t
  JOIN vyapar_listings.taxonomy_terms c ON c.kind = 'category' AND c.slug = t.parent
ON CONFLICT (kind, slug) DO UPDATE SET
  parent_id      = EXCLUDED.parent_id,
  description_en = EXCLUDED.description_en,
  description_hi = EXCLUDED.description_hi,
  description_te = EXCLUDED.description_te,
  -- fill a missing translation, never overwrite one an operator already set
  name_hi        = COALESCE(vyapar_listings.taxonomy_terms.name_hi, EXCLUDED.name_hi),
  name_te        = COALESCE(vyapar_listings.taxonomy_terms.name_te, EXCLUDED.name_te),
  updated_at     = now();

-- ---------------------------------------------------------------------------
-- 5. [Backend A, 2026-09-29 — critique N5] A one-tap application message is
--    built by Vyapar, not written by the applicant, so it is stored as a
--    template key plus its parameters and rendered in each READER's language
--    (the poster reading Telugu text built for a Telugu applicant was the
--    bug). `body` keeps the sender-language rendering as the fallback every
--    old reader already understands. Free-text messages leave both NULL and
--    are shown exactly as written.
-- ---------------------------------------------------------------------------
ALTER TABLE vyapar_enquiries.enquiry_messages
  ADD COLUMN IF NOT EXISTS template_key    text,
  ADD COLUMN IF NOT EXISTS template_params jsonb;

-- Backfill: the first message of every existing one-tap application is the
-- generated one (the applicant sent no text). Idempotent.
UPDATE vyapar_enquiries.enquiry_messages m
   SET template_key = 'oneTap',
       template_params = jsonb_build_object(
         'headline', e.profile_snapshot ->> 'headline',
         'experience_years', e.profile_snapshot -> 'experience_years',
         'locality', e.profile_snapshot ->> 'locality')
  FROM vyapar_enquiries.enquiries e
 WHERE m.enquiry_id = e.id
   AND e.applied_via = 'one_tap'
   AND m.sender_id = e.sender_id
   AND m.template_key IS NULL
   AND NOT m.system_note
   AND m.created_at = (SELECT min(m2.created_at) FROM vyapar_enquiries.enquiry_messages m2 WHERE m2.enquiry_id = e.id);
