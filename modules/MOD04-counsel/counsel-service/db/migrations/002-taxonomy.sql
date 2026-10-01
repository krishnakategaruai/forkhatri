-- Starting expertise taxonomy (reference data, every environment). A starting
-- point, not a restriction: consultants propose new areas, admins approve.
SET search_path TO counsel, public;

INSERT INTO expertise_area (id, name_en, name_hi, name_te, regulated, sort_order) VALUES
  ('business',      'Business & Entrepreneurship', 'व्यवसाय और उद्यमिता',        'వ్యాపారం & వ్యవస్థాపకత',        false, 10),
  ('career',        'Career & Employment',         'करियर और रोज़गार',           'కెరీర్ & ఉద్యోగం',               false, 20),
  ('freelancing',   'Freelancing & Creators',      'फ्रीलांसिंग और क्रिएटर',     'ఫ్రీలాన్సింగ్ & క్రియేటర్లు',    false, 30),
  ('technology',    'Technology & IT',             'टेक्नोलॉजी और आईटी',          'టెక్నాలజీ & ఐటీ',               false, 40),
  ('agriculture',   'Agriculture & Farming',       'कृषि और खेती',               'వ్యవసాయం',                      false, 50),
  ('education',     'Education & Academia',        'शिक्षा और अकादमिक',          'విద్య & అకడమిక్స్',              false, 60),
  ('legal',         'Legal',                       'कानूनी',                     'చట్టపరమైన',                     true,  70),
  ('finance',       'Finance & Tax',               'वित्त और कर',                'ఫైనాన్స్ & పన్ను',               true,  80),
  ('investment',    'Insurance & Investment',      'बीमा और निवेश',              'బీమా & పెట్టుబడి',               true,  90),
  ('health',        'Medical & Health',            'चिकित्सा और स्वास्थ्य',      'వైద్యం & ఆరోగ్యం',               true,  100),
  ('mental-health', 'Mental Health',               'मानसिक स्वास्थ्य',           'మానసిక ఆరోగ్యం',                true,  110),
  ('nutrition',     'Nutrition',                   'पोषण',                       'పోషకాహారం',                     false, 120),
  ('fitness',       'Fitness & Sports',            'फिटनेस और खेल',              'ఫిట్‌నెస్ & క్రీడలు',            false, 130),
  ('architecture',  'Architecture & Construction', 'वास्तुकला और निर्माण',       'ఆర్కిటెక్చర్ & నిర్మాణం',        false, 140),
  ('property',      'Property & Real Estate',      'संपत्ति और रियल एस्टेट',     'ఆస్తి & రియల్ ఎస్టేట్',          false, 150),
  ('design',        'Design & Creative',           'डिज़ाइन और रचनात्मक',        'డిజైన్ & క్రియేటివ్',            false, 160),
  ('media',         'Media & Content',             'मीडिया और कंटेंट',           'మీడియా & కంటెంట్',               false, 170),
  ('travel',        'Travel & Adventure',          'यात्रा और रोमांच',           'ప్రయాణం & సాహసం',                false, 180),
  ('trades',        'Skilled Trades',              'कुशल व्यवसाय',               'నైపుణ్య వృత్తులు',               false, 190),
  ('manufacturing', 'Manufacturing & Industrial',  'विनिर्माण और औद्योगिक',      'తయారీ & పారిశ్రామిక',           false, 200),
  ('logistics',     'Logistics & Supply Chain',    'लॉजिस्टिक्स और सप्लाई चेन',  'లాజిస్టిక్స్ & సప్లై చైన్',      false, 210),
  ('food',          'Food & Hospitality',          'भोजन और आतिथ्य',             'ఆహారం & ఆతిథ్యం',               false, 220),
  ('personal',      'Personal Development',        'व्यक्तिगत विकास',            'వ్యక్తిగత అభివృద్ధి',            false, 230),
  ('community',     'Community & Social Work',     'समुदाय और सामाजिक कार्य',    'సమాజం & సామాజిక సేవ',           false, 240),
  ('science',       'Science & Research',          'विज्ञान और अनुसंधान',        'సైన్స్ & పరిశోధన',               false, 250),
  ('other',         'Other Specialist Expertise',  'अन्य विशेषज्ञता',            'ఇతర ప్రత్యేక నైపుణ్యం',          false, 900)
ON CONFLICT (id) DO UPDATE SET name_en = EXCLUDED.name_en, name_hi = EXCLUDED.name_hi, name_te = EXCLUDED.name_te,
  regulated = EXCLUDED.regulated, sort_order = EXCLUDED.sort_order;

-- Regulated areas: which verification dimensions must be cleared, and the
-- disclaimer shown before payment. Jurisdiction-aware ('*' = every country).
INSERT INTO compliance_rule (area_id, jurisdiction, required_dimensions, disclaimer_key, recording_allowed) VALUES
  ('legal',         '*',  '{identity,qualification,registration}', 'disclaimer.legal',      false),
  ('finance',       '*',  '{identity,qualification}',              'disclaimer.finance',    true),
  ('investment',    'IN', '{identity,qualification,registration}', 'disclaimer.investment', true),
  ('investment',    '*',  '{identity,qualification}',              'disclaimer.investment', true),
  ('health',        '*',  '{identity,qualification,registration}', 'disclaimer.health',     false),
  ('mental-health', '*',  '{identity,qualification}',              'disclaimer.health',     false)
ON CONFLICT (area_id, jurisdiction) DO UPDATE SET required_dimensions = EXCLUDED.required_dimensions,
  disclaimer_key = EXCLUDED.disclaimer_key, recording_allowed = EXCLUDED.recording_allowed;
