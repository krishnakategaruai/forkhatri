-- =============================================================================
-- MOD01 Vyapar — development seed data (Hyderabad / Secunderabad launch geography)
-- Re-runnable: schema.sql resets the schema first.
-- =============================================================================
SET search_path TO vyapar, public;

-- ---------------------------------------------------------------- config
INSERT INTO config (key, value) VALUES
('launch_geography', '{"city":"Hyderabad / Secunderabad","center":{"lat":17.385,"lng":78.4867},"default_radius_km":10,"radius_steps":[5,10,25]}'),
('ranking_weights', '{"capability_fit":0.30,"intent_fit":0.10,"location_fit":0.20,"timing_fit":0.08,"value_fit":0.07,"eligibility_fit":0.10,"freshness":0.10,"trust":0.05,"max_consecutive_same":3}'),
('listing_ranking_weights', '{"text":0.35,"category":0.25,"distance":0.20,"verification":0.10,"freshness":0.10}'),
('notification_limits', '{"strong_match_threshold":0.62,"daily_cap":3,"digest_default_hour":19}'),
('freshness_days', '{"opportunity_reminder":14,"opportunity_stale":21,"opportunity_expire":45,"draft_reminder":5,"draft_archive":7,"verification_reconfirm_months":11,"verification_expiry_months":12}'),
('enquiry_limits', '{"per_day":20,"open_per_target":1,"no_response_days":7,"message_min":20,"message_max":1000}'),
('moderation_targets_hours', '{"low":72,"medium":48,"high":12,"critical":2}'),
('signal_allow_list', '["capability_fit","intent_fit","location_fit","timing_fit","value_fit","eligibility_fit","freshness","trust"]'),
('payment_gateway', '{"provider":"razorpay","mode":"sandbox","checkout":"hosted"}'),
('identity_contract', '{"version":"v1","sync_interval_minutes":60}');

-- ---------------------------------------------------------------- members (identity bridge mirror)
INSERT INTO members (id, display_name, phone, trust_level, language, locality, lat, lng, radius_km, work_mode, help_with, capabilities, is_operator, operator_permissions, first_run_done, avatar_url) VALUES
('m_krishna',  'Krishna Kategaru', '+919000000001', 2, 'en', 'Begumpet',       17.4447, 78.4676, 10, 'both',    '{find_customers,hire,find_work}', '{product_management,software}', false, '{}', true,  NULL),
('m_anita',    'Anita Khatri',     '+919000000002', 2, 'en', 'Banjara Hills',  17.4156, 78.4347, 15, 'both',    '{find_customers}', '{accounting,gst_filing,tax}', false, '{}', true, NULL),
('m_ravi',     'Ravi Mehra',       '+919000000003', 1, 'hi', 'Ameerpet',       17.4375, 78.4483, 8,  'on_site', '{find_customers,find_work}', '{plumbing}', false, '{}', true, NULL),
('m_sunita',   'Sunita Kapoor',    '+919000000004', 2, 'hi', 'Secunderabad',   17.4399, 78.4983, 20, 'on_site', '{find_customers}', '{catering,events}', false, '{}', true, NULL),
('m_vikram',   'Vikram Sethi',     '+919000000005', 2, 'en', 'Charminar',      17.3616, 78.4747, 25, 'both',    '{find_customers,partners}', '{textiles,wholesale}', false, '{}', true, NULL),
('m_priya',    'Priya Malhotra',   '+919000000006', 2, 'en', 'Madhapur',       17.4483, 78.3915, 25, 'remote',  '{find_work}', '{software,react,python}', false, '{}', true, NULL),
('m_rahul',    'Rahul Chadha',     '+919000000007', 1, 'te', 'Kukatpally',     17.4948, 78.3996, 10, 'both',    '{find_customers,find_work}', '{tutoring,mathematics}', false, '{}', true, NULL),
('m_meena',    'Meena Sahni',      '+919000000008', 2, 'en', 'Himayatnagar',   17.4020, 78.4840, 10, 'on_site', '{find_customers}', '{bakery,cakes}', false, '{}', true, NULL),
('m_suresh',   'Suresh Kohli',     '+919000000009', 1, 'te', 'Dilsukhnagar',   17.3688, 78.5247, 12, 'on_site', '{find_customers,find_work}', '{electrical}', false, '{}', true, NULL),
('m_deepak',   'Deepak Bhalla',    '+919000000010', 2, 'en', 'Jubilee Hills',  17.4325, 78.4073, 30, 'both',    '{find_customers,partners}', '{architecture,interior_design}', false, '{}', true, NULL),
('m_kavita',   'Kavita Dhawan',    '+919000000011', 2, 'en', 'Abids',          17.3900, 78.4750, 20, 'both',    '{find_customers}', '{legal,property_law}', false, '{}', true, NULL),
('m_arjun',    'Arjun Tandon',     '+919000000012', 1, 'en', 'Kondapur',       17.4622, 78.3568, 30, 'both',    '{find_work}', '{photography,video_editing}', false, '{}', true, NULL),
('m_neha_ops', 'Neha (Operations)','+919000000013', 2, 'en', 'Secunderabad',   17.4399, 78.4983, 10, 'both',    '{}', '{}', true, '{verification,content,commercial,analytics,moderation}', true, NULL),
('m_new',      'New Member',       '+919000000014', 1, 'en', NULL,             NULL,    NULL,    10, NULL,      '{}', '{}', false, '{}', false, NULL),
('m_gaurav',   'Gaurav Kapur',     '+919000000015', 1, 'en', 'Uppal',          17.4056, 78.5591, 10, 'on_site', '{find_customers}', '{car_repair}', false, '{}', true, NULL),
('m_shreya',   'Shreya Nanda',     '+919000000016', 2, 'en', 'Gachibowli',     17.4401, 78.3489, 15, 'both',    '{hire,find_customers}', '{software,startup}', false, '{}', true, NULL);

INSERT INTO privacy_settings (member_id) SELECT id FROM members;

-- ---------------------------------------------------------------- taxonomy
INSERT INTO taxonomy_terms (kind, slug, name_en, name_hi, name_te, icon) VALUES
('category','accounting_tax',      'Accounting & Tax',           'लेखा और कर',           'అకౌంటింగ్ & పన్ను',       'calculate'),
('category','legal',               'Legal Services',             'कानूनी सेवाएँ',         'న్యాయ సేవలు',            'gavel'),
('category','home_repair',         'Home Repair & Trades',       'घर की मरम्मत',          'ఇంటి మరమ్మతులు',          'home_repair_service'),
('category','food_catering',       'Food & Catering',            'भोजन और केटरिंग',       'ఆహారం & క్యాటరింగ్',      'restaurant'),
('category','textiles_retail',     'Textiles & Retail',          'वस्त्र और खुदरा',        'వస్త్రాలు & రిటైల్',      'checkroom'),
('category','software_it',         'Software & IT',              'सॉफ्टवेयर और आईटी',     'సాఫ్ట్‌వేర్ & ఐటీ',       'code'),
('category','education',           'Education & Tutoring',       'शिक्षा और ट्यूशन',      'విద్య & ట్యూషన్',         'school'),
('category','design_architecture', 'Design & Architecture',      'डिज़ाइन और वास्तुकला',  'డిజైన్ & ఆర్కిటెక్చర్',   'architecture'),
('category','media_photo',         'Photography & Media',        'फोटोग्राफी और मीडिया',  'ఫోటోగ్రఫీ & మీడియా',      'photo_camera'),
('category','health_wellness',     'Health & Wellness',          'स्वास्थ्य',             'ఆరోగ్యం',                'spa'),
('category','automotive',          'Automotive',                 'ऑटोमोटिव',             'ఆటోమోటివ్',              'directions_car'),
('category','events',              'Events & Decor',             'कार्यक्रम और सजावट',    'ఈవెంట్స్ & డెకర్',        'celebration'),
('category','logistics',           'Logistics & Transport',      'लॉजिस्टिक्स',           'లాజిస్టిక్స్',            'local_shipping'),
('category','printing',            'Printing & Signage',         'प्रिंटिंग',             'ప్రింటింగ్',              'print'),
('category','handicraft',          'Handicraft & Artisans',      'हस्तशिल्प',             'హస్తకళలు',               'palette'),
('category','marketing',           'Marketing & Content',        'मार्केटिंग',            'మార్కెటింగ్',             'campaign'),
('capability','accounting',        'Accounting',                 'लेखांकन',              'అకౌంటింగ్', NULL),
('capability','gst_filing',        'GST filing',                 'जीएसटी फाइलिंग',        'GST ఫైలింగ్', NULL),
('capability','tax',               'Income tax',                 'आयकर',                 'ఆదాయపు పన్ను', NULL),
('capability','plumbing',          'Plumbing',                   'प्लंबिंग',              'ప్లంబింగ్', NULL),
('capability','electrical',        'Electrical work',            'बिजली का काम',          'ఎలక్ట్రికల్', NULL),
('capability','catering',          'Catering',                   'केटरिंग',               'క్యాటరింగ్', NULL),
('capability','events',            'Event management',           'इवेंट प्रबंधन',          'ఈవెంట్ నిర్వహణ', NULL),
('capability','textiles',          'Textiles',                   'वस्त्र',                'వస్త్రాలు', NULL),
('capability','wholesale',         'Wholesale supply',           'थोक आपूर्ति',            'హోల్‌సేల్', NULL),
('capability','software',          'Software development',       'सॉफ्टवेयर विकास',       'సాఫ్ట్‌వేర్ అభివృద్ధి', NULL),
('capability','react',             'React / frontend',           'रिएक्ट',                'రియాక్ట్', NULL),
('capability','python',            'Python / backend',           'पायथन',                 'పైథాన్', NULL),
('capability','tutoring',          'Tutoring',                   'ट्यूशन',                'ట్యూషన్', NULL),
('capability','mathematics',       'Mathematics',                'गणित',                  'గణితం', NULL),
('capability','bakery',            'Baking',                     'बेकरी',                 'బేకరీ', NULL),
('capability','cakes',             'Custom cakes',               'कस्टम केक',             'కస్టమ్ కేకులు', NULL),
('capability','architecture',      'Architecture',               'वास्तुकला',              'ఆర్కిటెక్చర్', NULL),
('capability','interior_design',   'Interior design',            'इंटीरियर डिज़ाइन',      'ఇంటీరియర్ డిజైన్', NULL),
('capability','legal',             'Legal advice',               'कानूनी सलाह',           'న్యాయ సలహా', NULL),
('capability','property_law',      'Property law',               'संपत्ति कानून',          'ఆస్తి చట్టం', NULL),
('capability','photography',       'Photography',                'फोटोग्राफी',            'ఫోటోగ్రఫీ', NULL),
('capability','video_editing',     'Video editing',              'वीडियो संपादन',          'వీడియో ఎడిటింగ్', NULL),
('capability','car_repair',        'Car repair',                 'कार मरम्मत',             'కారు మరమ్మతు', NULL),
('capability','yoga',              'Yoga instruction',           'योग',                   'యోగా', NULL),
('capability','product_management','Product management',         'उत्पाद प्रबंधन',         'ప్రొడక్ట్ మేనేజ్‌మెంట్', NULL),
('capability','startup',           'Startup operations',         'स्टार्टअप',              'స్టార్టప్', NULL),
('capability','content_writing',   'Content writing',            'कंटेंट लेखन',            'కంటెంట్ రైటింగ్', NULL),
('capability','social_media',      'Social media',               'सोशल मीडिया',           'సోషల్ మీడియా', NULL),
('capability','sales',             'Sales',                      'बिक्री',                 'అమ్మకాలు', NULL),
('capability','delivery',          'Delivery & logistics',       'डिलीवरी',               'డెలివరీ', NULL),
('capability','tailoring',         'Tailoring',                  'सिलाई',                 'కుట్టుపని', NULL),
('capability','printing',          'Printing',                   'प्रिंटिंग',              'ప్రింటింగ్', NULL),
('capability','handicraft',        'Handicraft',                 'हस्तशिल्प',              'హస్తకళ', NULL);
INSERT INTO taxonomy_terms (kind, slug, name_en, status) VALUES ('capability','pooja-samagri-supply','pooja samagri supply','unmapped');

-- ---------------------------------------------------------------- listings
INSERT INTO listings (id, owner_id, kind, name, headline, description, categories, capabilities, services, locality, lat, lng, service_radius_km, service_mode, primary_phone, contact_verified, experience_years, languages, availability, rates, intent_state, intent_visible, state, verification_state, verification_document, verification_claim, verified_at, verification_expires_at, image_url, response_minutes, published_at, last_confirmed_at, credential_ref) VALUES
('00000000-0000-4000-8000-000000000001','m_anita','business','Khatri & Associates','Chartered Accountants for small businesses','GST registration and monthly filing, income-tax returns, bookkeeping and audit support for shops, traders and startups in Hyderabad. Fixed monthly packages, no surprises.','{accounting_tax}','{accounting,gst_filing,tax}','[{"name":"GST registration","price_hint":"₹1,500"},{"name":"Monthly GST filing","price_hint":"from ₹999/mo"},{"name":"ITR filing","price_hint":"from ₹799"}]','Banjara Hills',17.4156,78.4347,15,'both','+919000000002',true,12,'{en,hi}','this_week',NULL,NULL,false,'active_verified','verified','gst',NULL,now()-interval '40 days',now()+interval '325 days','/assets/accountant.jpg',45,now()-interval '70 days',now()-interval '3 days',NULL),
('00000000-0000-4000-8000-000000000002','m_ravi','professional','Ravi Mehra — Plumbing','Same-day plumbing repairs, Ameerpet & nearby','Leak repair, bathroom fittings, water-tank cleaning, new pipeline work. 15 years in Hyderabad. Call for emergency work after 8 pm too.','{home_repair}','{plumbing}','[{"name":"Leak repair","price_hint":"from ₹300"},{"name":"Bathroom fitting","price_hint":"quote"},{"name":"Tank cleaning","price_hint":"₹800"}]','Ameerpet',17.4375,78.4483,8,'on_site','+919000000003',true,15,'{hi,te}','now','from ₹300 per visit','open',false,'active_unverified','not_started',NULL,NULL,NULL,NULL,'/assets/plumber.jpg',15,now()-interval '20 days',now()-interval '1 day',NULL),
('00000000-0000-4000-8000-000000000003','m_sunita','business','Kapoor Caterers','Pure-veg catering for weddings & functions','Punjabi and Hyderabadi vegetarian menus for 50–2,000 guests. Live counters, dessert stations, staff in uniform. Tasting sessions every Saturday.','{food_catering,events}','{catering,events}','[{"name":"Wedding catering","price_hint":"from ₹450/plate"},{"name":"Corporate lunch","price_hint":"from ₹180/plate"}]','Secunderabad',17.4399,78.4983,25,'on_site','+919000000004',true,18,'{hi,en}','this_week',NULL,NULL,false,'active_verified','verified','udyam',NULL,now()-interval '90 days',now()+interval '275 days','/assets/catering-indian.jpg',120,now()-interval '120 days',now()-interval '6 days',NULL),
('00000000-0000-4000-8000-000000000004','m_vikram','business','Sethi Textiles','Wholesale suiting, shirting and sarees','Three generations at Charminar. Wholesale fabric supply to boutiques and retailers across Telangana; minimum order 50 metres. Also custom uniform fabric.','{textiles_retail}','{textiles,wholesale}','[{"name":"Wholesale fabric","price_hint":"per metre"},{"name":"Uniform fabric","price_hint":"quote"}]','Charminar',17.3616,78.4747,50,'both','+919000000005',true,30,'{hi,en,te}','now',NULL,NULL,false,'active_verified','verified','gst',NULL,now()-interval '200 days',now()+interval '165 days','/assets/textile-shop.jpg',240,now()-interval '210 days',now()-interval '10 days',NULL),
('00000000-0000-4000-8000-000000000005','m_priya','professional','Priya Malhotra — Full-stack developer','React, Next.js and Python for early-stage products','8 years building web products. Available for 3–6 month contracts or fixed-scope builds. Remote-first, Hyderabad meetings possible.','{software_it}','{software,react,python}','[{"name":"MVP build","price_hint":"fixed scope"},{"name":"Contract (monthly)","price_hint":"from ₹1.5L"}]','Madhapur',17.4483,78.3915,50,'remote','+919000000006',true,8,'{en,hi}','this_week','from ₹1.5L / month','looking',false,'active_verified','verified','credential','B.Tech (CSE), JNTU Hyderabad',now()-interval '30 days',now()+interval '335 days','/assets/software-developer.jpg',30,now()-interval '45 days',now()-interval '2 days','{"id":"vc_9f1","claim":"B.Tech (CSE), JNTU Hyderabad","issuer":"Identity & Trust","verified_at":"2026-08-15","last_checked":"2026-09-14T06:00:00Z"}'),
('00000000-0000-4000-8000-000000000006','m_rahul','professional','Rahul Chadha — Maths tutor','Class 8–12 maths, home and online','CBSE and State board. Small batches of 4 at Kukatpally or one-to-one online. Weekend crash courses before exams.','{education}','{tutoring,mathematics}','[{"name":"Home tuition","price_hint":"₹6,000/mo"},{"name":"Online batch","price_hint":"₹3,500/mo"}]','Kukatpally',17.4948,78.3996,10,'both','+919000000007',true,6,'{te,en}','now',NULL,'open',false,'active_unverified','pending',NULL,NULL,NULL,NULL,'/assets/tutor-classroom.jpg',60,now()-interval '12 days',now()-interval '12 days',NULL),
('00000000-0000-4000-8000-000000000007','m_meena','business','Meena''s Oven','Custom cakes, cookies and festive boxes','Eggless custom cakes for birthdays and weddings, Diwali dry-fruit boxes, corporate gifting. Order 48 hours ahead; delivery within 8 km.','{food_catering}','{bakery,cakes}','[{"name":"Custom cake","price_hint":"from ₹900/kg"},{"name":"Festive box","price_hint":"from ₹650"}]','Himayatnagar',17.4020,78.4840,8,'on_site','+919000000008',true,5,'{en,hi}','this_week',NULL,NULL,false,'active_verified','verified','shops_est',NULL,now()-interval '15 days',now()+interval '350 days','/assets/bakery.jpg',20,now()-interval '60 days',now()-interval '1 day',NULL),
('00000000-0000-4000-8000-000000000008','m_suresh','professional','Suresh Kohli — Electrician','Wiring, inverters, fan and MCB work','Licensed electrician. New-house wiring, inverter installation, fault finding. Dilsukhnagar, LB Nagar, Uppal.','{home_repair}','{electrical}','[{"name":"Fault visit","price_hint":"₹250"},{"name":"Inverter install","price_hint":"₹1,200"}]','Dilsukhnagar',17.3688,78.5247,12,'on_site','+919000000009',true,11,'{te,hi}','now','₹250 per visit','curious',false,'active_unverified','not_started',NULL,NULL,NULL,NULL,'/assets/electrician.jpg',25,now()-interval '9 days',now()-interval '9 days',NULL),
('00000000-0000-4000-8000-000000000009','m_deepak','business','Bhalla Design Studio','Architecture and interiors for homes and clinics','Residential architecture, turnkey interiors, clinic and office fit-outs. Registered architect (COA). 60+ completed projects in Hyderabad.','{design_architecture}','{architecture,interior_design}','[{"name":"Home design","price_hint":"from ₹40/sq ft"},{"name":"Turnkey interiors","price_hint":"quote"}]','Jubilee Hills',17.4325,78.4073,30,'both','+919000000010',true,14,'{en,hi}','this_week',NULL,NULL,false,'active_verified','verified','pan',NULL,now()-interval '335 days',now()+interval '30 days','/assets/architect.jpg',180,now()-interval '340 days',now()-interval '30 days',NULL),
('00000000-0000-4000-8000-000000000010','m_kavita','professional','Kavita Dhawan — Advocate','Property, rental and family matters','Advocate, Telangana High Court. Sale-deed review, rental agreements, partition and succession. First 20-minute consultation free.','{legal}','{legal,property_law}','[{"name":"Sale deed review","price_hint":"₹2,500"},{"name":"Rental agreement","price_hint":"₹1,000"}]','Abids',17.3900,78.4750,20,'both','+919000000011',true,16,'{en,hi,te}','this_week',NULL,NULL,false,'active_verified','verified','credential','Bar Council of Telangana enrolment',now()-interval '100 days',now()+interval '265 days','/assets/lawyer.jpg',90,now()-interval '150 days',now()-interval '4 days',NULL),
('00000000-0000-4000-8000-000000000011','m_arjun','professional','Arjun Tandon — Photographer','Weddings, products and reels','Candid wedding coverage, product shoots for small brands, short-form video editing. Drone available.','{media_photo}','{photography,video_editing}','[{"name":"Wedding day","price_hint":"from ₹35,000"},{"name":"Product shoot","price_hint":"from ₹4,000"}]','Kondapur',17.4622,78.3568,40,'both','+919000000012',true,7,'{en,hi}','this_week',NULL,'looking',true,'active_unverified','not_started',NULL,NULL,NULL,NULL,'/assets/photographer.jpg',40,now()-interval '5 days',now()-interval '5 days',NULL),
('00000000-0000-4000-8000-000000000012','m_gaurav','business','Kapur Motors','Car service and denting-painting, Uppal','Multi-brand car servicing, AC repair, denting and painting with pick-up and drop within 10 km.','{automotive}','{car_repair}','[{"name":"General service","price_hint":"from ₹2,500"},{"name":"AC repair","price_hint":"quote"}]','Uppal',17.4056,78.5591,10,'on_site','+919000000015',true,9,'{hi,te}','now',NULL,NULL,false,'active_unverified','rejected',NULL,NULL,NULL,NULL,'/assets/car-mechanic.jpg',35,now()-interval '25 days',now()-interval '8 days',NULL),
('00000000-0000-4000-8000-000000000013','m_shreya','business','Nanda Labs','Product studio building SaaS for Indian SMBs','Small team in Gachibowli building billing and inventory tools. Hiring and partnering with freelancers regularly.','{software_it}','{software,startup}','[{"name":"Custom SaaS","price_hint":"quote"}]','Gachibowli',17.4401,78.3489,50,'both','+919000000016',true,4,'{en}','this_week',NULL,NULL,false,'active_verified','verified','gst',NULL,now()-interval '10 days',now()+interval '355 days','/assets/startup-team.jpg',60,now()-interval '30 days',now()-interval '1 day',NULL),
('00000000-0000-4000-8000-000000000014','m_sunita','business','Kapoor Decor & Events','Mandap, lighting and stage decor','Sister concern of Kapoor Caterers. Floral mandaps, LED walls, stage and haldi setups.','{events}','{events}','[{"name":"Mandap decor","price_hint":"from ₹45,000"}]','Secunderabad',17.4399,78.4983,25,'on_site','+919000000004',true,10,'{hi,en}','this_week',NULL,NULL,false,'active_unverified','not_started',NULL,NULL,NULL,NULL,'/assets/florist.jpg',150,now()-interval '3 days',now()-interval '3 days',NULL),
('00000000-0000-4000-8000-000000000015','m_krishna','business','ForKhatri Studio','Product consulting for community businesses','Draft listing used by the development member.','{marketing}','{product_management}','[]','Begumpet',17.4447,78.4676,10,'both','+919000000001',false,NULL,'{en}',NULL,NULL,NULL,false,'draft','not_started',NULL,NULL,NULL,NULL,NULL,NULL,NULL,now(),NULL),
('00000000-0000-4000-8000-000000000016','m_vikram','business','Sethi Uniforms','School and corporate uniform stitching','Suspended pending review of a member report.','{textiles_retail}','{textiles,tailoring}','[]','Charminar',17.3616,78.4747,25,'on_site','+919000000005',true,12,'{hi}',NULL,NULL,NULL,false,'suspended','not_started',NULL,NULL,NULL,NULL,'/assets/tailor.jpg',NULL,now()-interval '80 days',now()-interval '40 days',NULL),
('00000000-0000-4000-8000-000000000017','m_deepak','professional','Deepak Bhalla — Vastu-aware planning','Vastu-aware layouts for new homes','Consultation on plot orientation and room placement for new construction.','{design_architecture}','{architecture}','[]','Jubilee Hills',17.4325,78.4073,30,'both','+919000000010',true,14,'{en,hi}','later',NULL,NULL,false,'active_unverified','not_started',NULL,NULL,NULL,NULL,'/assets/interior-design.jpg',200,now()-interval '50 days',now()-interval '50 days',NULL),
('00000000-0000-4000-8000-000000000018','m_meena','professional','Meena Sahni — Baking classes','Weekend baking workshops for beginners','Two-day eggless baking workshop, batches of 6, all material included.','{education,food_catering}','{bakery,tutoring}','[{"name":"Weekend workshop","price_hint":"₹2,800"}]','Himayatnagar',17.4020,78.4840,15,'on_site','+919000000008',true,5,'{en,hi}','this_week',NULL,NULL,false,'active_unverified','not_started',NULL,NULL,NULL,NULL,'/assets/yoga.jpg',30,now()-interval '7 days',now()-interval '7 days',NULL);

INSERT INTO listing_contacts (listing_id, channel, value, disclosure) VALUES
('00000000-0000-4000-8000-000000000001','phone','+919000000002','after_accept'),
('00000000-0000-4000-8000-000000000001','email','anita@khatriassociates.in','after_accept'),
('00000000-0000-4000-8000-000000000001','website','https://khatriassociates.example','public'),
('00000000-0000-4000-8000-000000000001','address','Road No. 12, Banjara Hills','public'),
('00000000-0000-4000-8000-000000000002','phone','+919000000003','after_accept'),
('00000000-0000-4000-8000-000000000002','whatsapp','+919000000003','after_accept'),
('00000000-0000-4000-8000-000000000003','phone','+919000000004','after_accept'),
('00000000-0000-4000-8000-000000000003','address','Park Lane, Secunderabad','public'),
('00000000-0000-4000-8000-000000000003','website','https://kapoorcaterers.example','public'),
('00000000-0000-4000-8000-000000000004','phone','+919000000005','public'),
('00000000-0000-4000-8000-000000000004','address','Pathergatti, Charminar','public'),
('00000000-0000-4000-8000-000000000005','email','priya@example.dev','after_accept'),
('00000000-0000-4000-8000-000000000005','website','https://priya.example.dev','public'),
('00000000-0000-4000-8000-000000000006','phone','+919000000007','after_accept'),
('00000000-0000-4000-8000-000000000007','phone','+919000000008','after_accept'),
('00000000-0000-4000-8000-000000000007','whatsapp','+919000000008','public'),
('00000000-0000-4000-8000-000000000007','address','Street No. 5, Himayatnagar','public'),
('00000000-0000-4000-8000-000000000008','phone','+919000000009','after_accept'),
('00000000-0000-4000-8000-000000000009','phone','+919000000010','after_accept'),
('00000000-0000-4000-8000-000000000009','website','https://bhalladesign.example','public'),
('00000000-0000-4000-8000-000000000010','phone','+919000000011','after_accept'),
('00000000-0000-4000-8000-000000000010','address','Chamber 4, Abids','public'),
('00000000-0000-4000-8000-000000000011','email','arjun@example.photo','after_accept'),
('00000000-0000-4000-8000-000000000012','phone','+919000000015','public'),
('00000000-0000-4000-8000-000000000013','email','hello@nandalabs.example','after_accept'),
('00000000-0000-4000-8000-000000000014','phone','+919000000004','after_accept'),
('00000000-0000-4000-8000-000000000017','phone','+919000000010','hidden'),
('00000000-0000-4000-8000-000000000018','phone','+919000000008','after_accept');

-- verification records (FR08/FR09/FR47)
INSERT INTO verification_records (listing_id, member_id, kind, document_type, identifier_masked, identifier_enc, image_url, credential_name, issuer, state, verifier_id, decided_at, expires_at, created_at) VALUES
('00000000-0000-4000-8000-000000000001','m_anita','business','gst','36AAXXXXXXXX1Z5','enc:36AABCK1234A1Z5',NULL,NULL,NULL,'verified','m_neha_ops',now()-interval '40 days',now()+interval '325 days',now()-interval '43 days'),
('00000000-0000-4000-8000-000000000003','m_sunita','business','udyam','UDYAM-TS-XX-XXXX123','enc:UDYAM-TS-09-0012123',NULL,NULL,NULL,'verified','m_neha_ops',now()-interval '90 days',now()+interval '275 days',now()-interval '92 days'),
('00000000-0000-4000-8000-000000000006','m_rahul','credential','credential',NULL,NULL,'/assets/school.jpg','M.Sc Mathematics','Osmania University','pending',NULL,NULL,NULL,now()-interval '2 days'),
('00000000-0000-4000-8000-000000000012','m_gaurav','business','shops_est','TS/XX/XXXX/2021','enc:TS/UPL/0451/2021','/assets/car-mechanic.jpg',NULL,NULL,'rejected','m_neha_ops',now()-interval '5 days',NULL,now()-interval '8 days'),
('00000000-0000-4000-8000-000000000014','m_sunita','business','pan','AAXXX1234X','enc:AABCK1234K','/assets/office-hyderabad.jpg',NULL,NULL,'pending',NULL,NULL,NULL,now()-interval '4 days'),
('00000000-0000-4000-8000-000000000008','m_suresh','credential','credential',NULL,NULL,'/assets/electrician.jpg','Wireman licence','Telangana Electrical Licensing Board','needs_clearer_copy','m_neha_ops',now()-interval '1 day',NULL,now()-interval '3 days');
UPDATE verification_records SET reason_code='document_unreadable' WHERE state='needs_clearer_copy';
UPDATE verification_records SET reason_code='name_mismatch' WHERE state='rejected';

-- ---------------------------------------------------------------- opportunities
INSERT INTO opportunities (id, poster_id, listing_id, title, type, description, requirements, compensation, value_amount, location, lat, lng, work_mode, timing, eligibility, required_capabilities, response_method, deadline, source_segment, source_name, source_url, entry_mode, state, image_url, published_at, last_confirmed_at, confirmed_fields) VALUES
('00000000-0000-4000-8000-000000000101','m_shreya','00000000-0000-4000-8000-000000000013','Frontend developer (React) — Nanda Labs','employment','Build the customer-facing web app for our billing product. Small team, ship weekly, work directly with founders.','3+ years React; TypeScript; comfortable with REST APIs. Bonus: Next.js, accessibility.','₹9–14 LPA',1150000,'Gachibowli',17.4401,78.3489,'both','Full-time, start within 30 days','{"min_experience_years":3}','{react,software}','in_app',now()+interval '20 days','community',NULL,NULL,'create','active','/assets/startup-team.jpg',now()-interval '2 days',now()-interval '2 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000102','m_anita','00000000-0000-4000-8000-000000000001','Accounts assistant (part-time) — Banjara Hills','employment','Data entry in Tally, GST reconciliation, client follow-ups. Three days a week, mornings.','B.Com or equivalent; Tally; 1 year experience preferred.','₹12,000 / month',12000,'Banjara Hills',17.4156,78.4347,'on_site','Part-time, 3 days a week','{"min_experience_years":1}','{accounting}','in_app',now()+interval '15 days','community',NULL,NULL,'create','active','/assets/accountant.jpg',now()-interval '4 days',now()-interval '4 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000103','m_deepak','00000000-0000-4000-8000-000000000009','3D visualiser for two villa projects','freelance','Photorealistic exterior and interior renders for two villas in Kokapet. Files in SketchUp; we need Lumion/Enscape output.','Portfolio of residential renders; 4-week turnaround.','₹60,000 fixed',60000,'Jubilee Hills',17.4325,78.4073,'remote','4 weeks, start immediately','{}','{architecture,interior_design}','in_app',now()+interval '10 days','community',NULL,NULL,'create','active','/assets/interior-design.jpg',now()-interval '1 day',now()-interval '1 day','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000104','m_krishna',NULL,'Need a plumber for a 2BHK — leaking kitchen sink','local_service','Kitchen sink trap leaking, and one bathroom tap needs replacement. Available weekday evenings after 6.','Bring own fittings; quote before work.','Pay per visit',NULL,'Begumpet',17.4447,78.4676,'on_site','This week, evenings','{}','{plumbing}','in_app',now()+interval '6 days','community',NULL,NULL,'create','active','/assets/plumber.jpg',now()-interval '6 hours',now()-interval '6 hours','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000105','m_sunita','00000000-0000-4000-8000-000000000003','Catering staff for a 600-guest wedding (2 days)','employment','Need 20 service staff and 4 counter chefs for a wedding at Secunderabad Club, 27–28 Sept. Uniforms provided.','18+; prior banquet experience; punctual.','₹1,200 / day + meals',1200,'Secunderabad',17.4399,78.4983,'on_site','27–28 Sept, 4 pm to midnight','{}','{catering,events}','in_app',now()+interval '9 days','community',NULL,NULL,'create','active','/assets/catering-indian.jpg',now()-interval '3 days',now()-interval '3 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000106','m_priya',NULL,'Python developer — Telangana e-Governance (contract)','employment','Contract role with a state e-governance vendor. Shared from a WhatsApp group; details on the source page.','Python, Django, PostgreSQL; 2+ years.','₹8–10 LPA',900000,'Hyderabad',17.385,78.4867,'on_site','12-month contract','{"min_experience_years":2}','{python,software}','external',now()+interval '12 days','public','Naukri','https://www.naukri.com/','share','active','/assets/office-hyderabad.jpg',now()-interval '5 days',now()-interval '5 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000107','m_vikram','00000000-0000-4000-8000-000000000004','Looking for boutique partners for a festive saree line','partnership','Sethi Textiles is launching a Diwali handloom saree line and wants 5 boutique partners in Hyderabad for consignment sales.','Boutique with walk-in customers; GST registered.','Consignment, 25% margin',NULL,'Charminar',17.3616,78.4747,'both','Launch mid-October','{}','{textiles,sales}','in_app',now()+interval '25 days','community',NULL,NULL,'create','active','/assets/textile-shop.jpg',now()-interval '7 days',now()-interval '7 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000108','m_rahul','00000000-0000-4000-8000-000000000006','Free maths crash course for Class 10 (community)','training','Two-weekend free crash course for Khatri students appearing for Class 10 boards. 20 seats.','Class 10 student; bring textbook.','Free',0,'Kukatpally',17.4948,78.3996,'on_site','Two weekends in October','{}','{tutoring,mathematics}','in_app',now()+interval '18 days','community',NULL,NULL,'create','active','/assets/tutor-classroom.jpg',now()-interval '1 day',now()-interval '1 day','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000109','m_kavita',NULL,'T-Hub startup grant applications open (state programme)','community','Telangana government innovation grant for early-stage founders. Public notice forwarded from the district office.','Registered startup; Telangana address.','Grant up to ₹10 lakh',1000000,'Hyderabad',17.385,78.4867,'both','Applications close 30 Sept','{}','{startup}','external',now()+interval '16 days','public','T-Hub','https://t-hub.co/','share','active','/assets/coworking.jpg',now()-interval '8 days',now()-interval '8 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000110','m_meena','00000000-0000-4000-8000-000000000007','Delivery partner for cake orders (evenings)','local_service','Need a two-wheeler rider for 5–8 deliveries an evening within 8 km of Himayatnagar. Regular work.','Own two-wheeler; phone with maps.','₹60 per delivery + fuel',60,'Himayatnagar',17.4020,78.4840,'on_site','Evenings 5–9 pm','{}','{delivery}','in_app',NULL,'community',NULL,NULL,'create','active','/assets/logistics-truck.jpg',now()-interval '10 days',now()-interval '10 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000111','m_shreya','00000000-0000-4000-8000-000000000013','Content writer for product blog (10 articles)','freelance','Ten long-form articles on GST and inventory for small shop owners. Hindi-English bilingual preferred.','Samples of published writing; SEO basics.','₹2,500 per article',25000,'Gachibowli',17.4401,78.3489,'remote','6 weeks','{}','{content_writing}','in_app',now()+interval '14 days','community',NULL,NULL,'create','active','/assets/coworking.jpg',now()-interval '3 days',now()-interval '3 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000112','m_arjun',NULL,'Wedding photographer wanted — Warangal, Nov 12','freelance','Family in Warangal needs a candid photographer for a two-day wedding. Forwarded from a family group.','Candid portfolio; own equipment.','₹40,000',40000,'Warangal',17.9689,79.5941,'on_site','12–13 November','{}','{photography}','in_app',now()+interval '40 days','community',NULL,NULL,'share','active','/assets/photographer.jpg',now()-interval '2 days',now()-interval '2 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000113','m_gaurav','00000000-0000-4000-8000-000000000012','Car mechanic (experienced) — Uppal workshop','employment','Multi-brand servicing; AC and electrical diagnostics a plus. Six-day week.','5 years workshop experience.','₹22,000–28,000 / month',25000,'Uppal',17.4056,78.5591,'on_site','Full-time','{"min_experience_years":5}','{car_repair}','in_app',now()+interval '30 days','community',NULL,NULL,'create','active','/assets/car-mechanic.jpg',now()-interval '16 days',now()-interval '16 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000114','m_kavita','00000000-0000-4000-8000-000000000010','Paralegal / office assistant — Abids chambers','employment','Drafting support, court filing, client coordination.','LLB student or graduate; MS Word; Telugu and English.','₹15,000 / month',15000,'Abids',17.3900,78.4750,'on_site','Full-time','{}','{legal}','in_app',now()+interval '20 days','community',NULL,NULL,'create','stale','/assets/lawyer.jpg',now()-interval '30 days',now()-interval '24 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000115','m_vikram',NULL,'GeM seller registration workshop (MSME dept)','training','Free half-day workshop on registering as a seller on the Government e-Marketplace. Public notice.','MSME owners with Udyam.','Free',0,'Secunderabad',17.4399,78.4983,'on_site','Saturday 10 am','{}','{wholesale,sales}','external',now()-interval '1 day','public','MSME Development Institute','https://msmedi-hyderabad.gov.in/','share','expired','/assets/market-india.jpg',now()-interval '20 days',now()-interval '20 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000116','m_priya',NULL,'Junior React developer — Madhapur (from screenshot)','employment','Uploaded from a screenshot; fields inferred and awaiting confirmation.','1–2 years React.','₹4–6 LPA',500000,'Madhapur',17.4483,78.3915,'on_site','Full-time','{"min_experience_years":1}','{react}','external',NULL,'public','Unknown (screenshot)',NULL,'upload','draft','/assets/office-hyderabad.jpg',NULL,now()-interval '3 days','{}'),
('00000000-0000-4000-8000-000000000117','m_suresh','00000000-0000-4000-8000-000000000008','Electrical rewiring helper (2 weeks)','local_service','Need a helper for rewiring a 3-floor building in LB Nagar.','Basic electrical knowledge; fit for site work.','₹700 / day',700,'LB Nagar',17.3457,78.5522,'on_site','2 weeks from next Monday','{}','{electrical}','in_app',now()+interval '8 days','community',NULL,NULL,'create','active','/assets/construction-site.jpg',now()-interval '1 day',now()-interval '1 day','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000118','m_shreya','00000000-0000-4000-8000-000000000013','Sales intern — SMB outreach (Hyderabad)','employment','Visit shops in Ameerpet/Kukatpally to demo our billing app. Stipend + incentives.','Telugu speaking; two-wheeler.','₹10,000 stipend + incentives',10000,'Ameerpet',17.4375,78.4483,'on_site','3 months','{}','{sales}','in_app',now()+interval '12 days','community',NULL,NULL,'create','active','/assets/market-india.jpg',now()-interval '2 days',now()-interval '2 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000119','m_deepak','00000000-0000-4000-8000-000000000009','Site supervisor — villa project Kokapet','employment','Daily site supervision, vendor coordination, quality checks.','Diploma civil; 3 years site experience.','₹30,000 / month',30000,'Kokapet',17.3990,78.3360,'on_site','8 months','{"min_experience_years":3}','{architecture}','in_app',now()+interval '15 days','community',NULL,NULL,'create','pending_review','/assets/construction-site.jpg',NULL,now()-interval '1 day','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000120','m_anita',NULL,'Startup India seed fund — call for applications','community','Public notice from Startup India. Fields shared by a member; source link included.','DPIIT-recognised startup.','Up to ₹20 lakh',2000000,'Hyderabad',17.385,78.4867,'remote','Rolling','{}','{startup}','external',now()+interval '60 days','public','Startup India','https://seedfund.startupindia.gov.in/','share','active','/assets/coworking.jpg',now()-interval '12 days',now()-interval '12 days','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000121','m_meena','00000000-0000-4000-8000-000000000007','Advance-payment training programme (flagged)','training','Pay ₹5,000 registration fee to secure your seat in a guaranteed placement course.','None.','Registration fee ₹5,000',NULL,'Hyderabad',17.385,78.4867,'on_site','Next month','{}','{}','in_app',now()+interval '20 days','community',NULL,NULL,'create','active','/assets/school.jpg',now()-interval '1 day',now()-interval '1 day','{title,type,location,response_method}'),
('00000000-0000-4000-8000-000000000122','m_sunita','00000000-0000-4000-8000-000000000014','Decor helper for Navaratri pandal (5 days)','local_service','Setting up floral and lighting decor for a colony pandal.','Physical work; evenings.','₹800 / day',800,'Secunderabad',17.4399,78.4983,'on_site','5 evenings','{}','{events}','in_app',now()+interval '5 days','community',NULL,NULL,'create','active','/assets/florist.jpg',now()-interval '12 hours',now()-interval '12 hours','{title,type,location,response_method}');
UPDATE opportunities SET unconfirmed_fields='{title,compensation,location,deadline}' WHERE id='00000000-0000-4000-8000-000000000116';
UPDATE opportunities SET distribution_limited=true WHERE id='00000000-0000-4000-8000-000000000121';

-- ---------------------------------------------------------------- member activity (FR55)
INSERT INTO member_opportunity (member_id, opportunity_id, saved_at, viewed_at) VALUES
('m_krishna','00000000-0000-4000-8000-000000000101',now()-interval '1 day',now()-interval '1 day'),
('m_krishna','00000000-0000-4000-8000-000000000109',now()-interval '3 days',now()-interval '3 days'),
('m_krishna','00000000-0000-4000-8000-000000000111',NULL,now()-interval '2 hours'),
('m_krishna','00000000-0000-4000-8000-000000000103',NULL,now()-interval '5 hours');
INSERT INTO member_opportunity (member_id, opportunity_id, hidden_at, hidden_reason) VALUES
('m_krishna','00000000-0000-4000-8000-000000000112',now()-interval '1 day','too_far');
INSERT INTO member_listing (member_id, listing_id, saved_at, viewed_at) VALUES
('m_krishna','00000000-0000-4000-8000-000000000001',now()-interval '2 days',now()-interval '2 days'),
('m_krishna','00000000-0000-4000-8000-000000000007',NULL,now()-interval '1 day');

-- ---------------------------------------------------------------- enquiries (FR22-FR24)
INSERT INTO enquiries (id, sender_id, provider_id, listing_id, opportunity_id, action_type, sub_choice, state, first_reply_at, last_activity_at, created_at) VALUES
('00000000-0000-4000-8000-000000000201','m_krishna','m_anita','00000000-0000-4000-8000-000000000001',NULL,'enquire','request_quote','in_progress',now()-interval '1 day',now()-interval '1 day',now()-interval '2 days'),
('00000000-0000-4000-8000-000000000202','m_krishna','m_shreya',NULL,'00000000-0000-4000-8000-000000000101','apply',NULL,'open',NULL,now()-interval '1 day',now()-interval '1 day'),
('00000000-0000-4000-8000-000000000203','m_ravi','m_krishna',NULL,'00000000-0000-4000-8000-000000000104','enquire',NULL,'open',NULL,now()-interval '3 hours',now()-interval '3 hours'),
('00000000-0000-4000-8000-000000000204','m_rahul','m_anita','00000000-0000-4000-8000-000000000001',NULL,'enquire','ask_question','resolved',now()-interval '20 days',now()-interval '15 days',now()-interval '22 days'),
('00000000-0000-4000-8000-000000000205','m_priya','m_deepak',NULL,'00000000-0000-4000-8000-000000000103','propose',NULL,'awaiting_response',NULL,now()-interval '10 hours',now()-interval '10 hours'),
('00000000-0000-4000-8000-000000000206','m_meena','m_sunita','00000000-0000-4000-8000-000000000003',NULL,'enquire','request_quote','closed',now()-interval '40 days',now()-interval '35 days',now()-interval '42 days'),
('00000000-0000-4000-8000-000000000207','m_gaurav','m_anita','00000000-0000-4000-8000-000000000001',NULL,'enquire','ask_question','closed',now()-interval '60 days',now()-interval '55 days',now()-interval '61 days'),
('00000000-0000-4000-8000-000000000208','m_suresh','m_ravi','00000000-0000-4000-8000-000000000002',NULL,'enquire','ask_question','resolved',now()-interval '12 days',now()-interval '9 days',now()-interval '13 days'),
('00000000-0000-4000-8000-000000000209','m_arjun','m_sunita','00000000-0000-4000-8000-000000000003',NULL,'enquire','request_quote','open',NULL,now()-interval '9 days',now()-interval '9 days');
INSERT INTO enquiry_messages (enquiry_id, sender_id, body, created_at) VALUES
('00000000-0000-4000-8000-000000000201','m_krishna','Hi Anita, I run a small consulting studio and need monthly GST filing plus year-end ITR. Could you share a quote for a yearly package?',now()-interval '2 days'),
('00000000-0000-4000-8000-000000000201','m_anita','Thanks Krishna. For a services business with under 30 invoices a month it is ₹999/month for GST and ₹2,500 for the annual ITR. Happy to start this month.',now()-interval '1 day'),
('00000000-0000-4000-8000-000000000202','m_krishna','Applying for the React role. I have 6 years of frontend experience and have shipped two Next.js products; portfolio on request.',now()-interval '1 day'),
('00000000-0000-4000-8000-000000000203','m_ravi','I can come tomorrow at 6.30 pm. Sink trap replacement is ₹450 with the part; tap depends on the model.',now()-interval '3 hours'),
('00000000-0000-4000-8000-000000000204','m_rahul','Do you handle ITR for tuition income under presumptive taxation?',now()-interval '22 days'),
('00000000-0000-4000-8000-000000000204','m_anita','Yes, 44ADA applies. Send me your receipts summary and we can file in two days.',now()-interval '20 days'),
('00000000-0000-4000-8000-000000000205','m_priya','I can deliver Lumion renders for both villas in 3 weeks. Portfolio: priya.example.dev/renders. Proposal: ₹55,000 including two revision rounds.',now()-interval '10 hours'),
('00000000-0000-4000-8000-000000000206','m_meena','Quote for a 150-guest corporate lunch next month?',now()-interval '42 days'),
('00000000-0000-4000-8000-000000000206','m_sunita','₹220 per plate for the standard menu. Tasting on Saturday if you like.',now()-interval '40 days'),
('00000000-0000-4000-8000-000000000207','m_gaurav','Need help with GST for my workshop.',now()-interval '61 days'),
('00000000-0000-4000-8000-000000000207','m_anita','Sure, let us start with registration. Documents list sent.',now()-interval '60 days'),
('00000000-0000-4000-8000-000000000208','m_suresh','Can you help with a pipeline job in Dilsukhnagar next week? I have an electrical client who needs both.',now()-interval '13 days'),
('00000000-0000-4000-8000-000000000208','m_ravi','Yes, Tuesday works. Share the address.',now()-interval '12 days'),
('00000000-0000-4000-8000-000000000209','m_arjun','Quote for 80 guests, dinner, Kondapur?',now()-interval '9 days');

-- partnership requests (FR25/FR26)
INSERT INTO partnership_requests (id, sender_id, recipient_id, sender_listing_id, recipient_listing_id, need, offer, expectations, category, locality, timing, next_step, state, created_at) VALUES
('00000000-0000-4000-8000-000000000301','m_sunita','m_meena','00000000-0000-4000-8000-000000000003','00000000-0000-4000-8000-000000000007','Dessert counter partner for weddings','Guaranteed 6–8 events a month, our staff handles service','Consistent quality, 48-hour lead time','food_catering','Secunderabad','From October season','A tasting meeting this week','pending',now()-interval '2 days'),
('00000000-0000-4000-8000-000000000302','m_deepak','m_vikram','00000000-0000-4000-8000-000000000009','00000000-0000-4000-8000-000000000004','Upholstery and curtain fabric supply for interiors','Regular orders for 4–5 projects a month','Trade pricing and samples within 3 days','textiles_retail','Charminar','Ongoing','Visit the showroom','accepted',now()-interval '20 days');
UPDATE partnership_requests SET decided_at=now()-interval '18 days' WHERE state='accepted';

-- reviews (FR27-FR29)
INSERT INTO review_invites (interaction_kind, interaction_id, member_id, subject_listing_id, subject_member_id, expires_at, used_at) VALUES
('enquiry','00000000-0000-4000-8000-000000000204','m_rahul','00000000-0000-4000-8000-000000000001','m_anita',now()+interval '15 days',now()-interval '14 days'),
('enquiry','00000000-0000-4000-8000-000000000206','m_meena','00000000-0000-4000-8000-000000000003','m_sunita',now()-interval '5 days',now()-interval '34 days'),
('enquiry','00000000-0000-4000-8000-000000000207','m_gaurav','00000000-0000-4000-8000-000000000001','m_anita',now()-interval '25 days',now()-interval '54 days'),
('enquiry','00000000-0000-4000-8000-000000000208','m_suresh','00000000-0000-4000-8000-000000000002','m_ravi',now()+interval '21 days',now()-interval '8 days'),
('enquiry','00000000-0000-4000-8000-000000000201','m_krishna','00000000-0000-4000-8000-000000000001','m_anita',now()+interval '29 days',NULL);
INSERT INTO reviews (interaction_kind, interaction_id, author_id, subject_listing_id, subject_member_id, recommend, tags, comment, state, created_at) VALUES
('enquiry','00000000-0000-4000-8000-000000000204','m_rahul','00000000-0000-4000-8000-000000000001','m_anita',true,'{responsive,clear_pricing,on_time}','Filed my return in two days and explained presumptive taxation clearly.','published',now()-interval '14 days'),
('enquiry','00000000-0000-4000-8000-000000000207','m_gaurav','00000000-0000-4000-8000-000000000001','m_anita',true,'{clear_pricing,professional}','Registration done without any surprises on fees.','published',now()-interval '54 days'),
('enquiry','00000000-0000-4000-8000-000000000206','m_meena','00000000-0000-4000-8000-000000000003','m_sunita',true,'{quality,on_time}','Corporate lunch was on time and the paneer was excellent, guests asked for the contact.','published',now()-interval '34 days'),
('enquiry','00000000-0000-4000-8000-000000000208','m_suresh','00000000-0000-4000-8000-000000000002','m_ravi',true,'{on_time,fair_price}','Came on the day promised, finished the pipeline job cleanly.','published',now()-interval '8 days');
-- extra history for Anita so counts read "5 verified interactions · 4 of 5 recommend"
INSERT INTO enquiries (id, sender_id, provider_id, listing_id, action_type, state, first_reply_at, last_activity_at, created_at) VALUES
('00000000-0000-4000-8000-000000000210','m_vikram','m_anita','00000000-0000-4000-8000-000000000001','enquire','closed',now()-interval '80 days',now()-interval '75 days',now()-interval '81 days'),
('00000000-0000-4000-8000-000000000211','m_deepak','m_anita','00000000-0000-4000-8000-000000000001','enquire','closed',now()-interval '95 days',now()-interval '90 days',now()-interval '96 days');
INSERT INTO enquiry_messages (enquiry_id, sender_id, body, created_at) VALUES
('00000000-0000-4000-8000-000000000210','m_vikram','GST audit query for wholesale.',now()-interval '81 days'),('00000000-0000-4000-8000-000000000210','m_anita','Let us meet on Monday.',now()-interval '80 days'),
('00000000-0000-4000-8000-000000000211','m_deepak','Need bookkeeping for the studio.',now()-interval '96 days'),('00000000-0000-4000-8000-000000000211','m_anita','Package sent.',now()-interval '95 days');
INSERT INTO reviews (interaction_kind, interaction_id, author_id, subject_listing_id, subject_member_id, recommend, tags, comment, state, created_at) VALUES
('enquiry','00000000-0000-4000-8000-000000000210','m_vikram','00000000-0000-4000-8000-000000000001','m_anita',true,'{professional}','Handled the audit notice well and kept us informed.','published',now()-interval '74 days'),
('enquiry','00000000-0000-4000-8000-000000000211','m_deepak','00000000-0000-4000-8000-000000000001','m_anita',false,'{slow_response}','Bookkeeping was accurate but replies took several days each time.','disputed',now()-interval '89 days');

-- ---------------------------------------------------------------- products (FR30/FR33/FR35)
INSERT INTO products (id, version, kind, name, description, duration_days, billing, price_paise, capabilities) VALUES
('boost_3d',  1,'boost','Boost · 3 days','Extra reach inside the eligible audience for 3 days',3,'one_time',14900,'{}'),
('boost_7d',  1,'boost','Boost · 7 days','Extra reach inside the eligible audience for 7 days',7,'one_time',29900,'{}'),
('boost_14d', 1,'boost','Boost · 14 days','Extra reach inside the eligible audience for 14 days',14,'one_time',49900,'{}'),
('workspace_monthly',1,'workspace','Business Workspace · monthly','Team roles, campaigns, response tracking and provider analytics',30,'monthly',79900,'{multi_user,campaigns,response_tracking,analytics}'),
('workspace_annual', 1,'workspace','Business Workspace · annual','Team roles, campaigns, response tracking and provider analytics — two months free',365,'annual',799000,'{multi_user,campaigns,response_tracking,analytics}'),
('campaign_s',1,'campaign','Campaign · Starter','Up to 10 items, 14 days',14,'one_time',199000,'{}'),
('campaign_m',1,'campaign','Campaign · Season','Up to 10 items, 30 days',30,'one_time',349000,'{}');

-- one active boost on Kapoor Caterers (Sponsored), one completed
INSERT INTO payment_orders (id, kind, ref_id, member_id, amount_paise, tax_paise, gateway, gateway_order_ref, gateway_payment_ref, idempotency_key, state, created_at) VALUES
('00000000-0000-4000-8000-000000000401','promotion','00000000-0000-4000-8000-000000000501','m_sunita',29900,5382,'razorpay','order_SEED0001','pay_SEED0001','seed-promo-1','succeeded',now()-interval '2 days'),
('00000000-0000-4000-8000-000000000402','promotion','00000000-0000-4000-8000-000000000502','m_anita',14900,2682,'razorpay','order_SEED0002','pay_SEED0002','seed-promo-2','succeeded',now()-interval '30 days'),
('00000000-0000-4000-8000-000000000403','entitlement','00000000-0000-4000-8000-000000000601','m_shreya',79900,14382,'razorpay','order_SEED0003','pay_SEED0003','seed-ent-1','succeeded',now()-interval '12 days');
INSERT INTO promotions (id, owner_id, target_kind, target_id, product_id, product_version, price_paise, tax_paise, audience, state, starts_at, ends_at, payment_order_id, created_at) VALUES
('00000000-0000-4000-8000-000000000501','m_sunita','listing','00000000-0000-4000-8000-000000000003','boost_7d',1,29900,5382,'{"locality":"Secunderabad"}','active',now()-interval '2 days',now()+interval '5 days','00000000-0000-4000-8000-000000000401',now()-interval '2 days'),
('00000000-0000-4000-8000-000000000502','m_anita','opportunity','00000000-0000-4000-8000-000000000102','boost_3d',1,14900,2682,'{}','completed',now()-interval '30 days',now()-interval '27 days','00000000-0000-4000-8000-000000000402',now()-interval '30 days');
INSERT INTO promotion_history (promotion_id, from_state, to_state, reason) VALUES
('00000000-0000-4000-8000-000000000501',NULL,'awaiting_payment','created'),('00000000-0000-4000-8000-000000000501','awaiting_payment','active','payment succeeded'),
('00000000-0000-4000-8000-000000000502',NULL,'awaiting_payment','created'),('00000000-0000-4000-8000-000000000502','awaiting_payment','active','payment succeeded'),('00000000-0000-4000-8000-000000000502','active','completed','duration ended');
INSERT INTO entitlements (id, listing_id, owner_id, product_id, product_version, price_paise, tax_paise, state, starts_at, renews_at, payment_order_id, created_at) VALUES
('00000000-0000-4000-8000-000000000601','00000000-0000-4000-8000-000000000013','m_shreya','workspace_monthly',1,79900,14382,'active',now()-interval '12 days',now()+interval '18 days','00000000-0000-4000-8000-000000000403',now()-interval '12 days');
INSERT INTO workspace_members (listing_id, member_id, phone, role, state, invited_by, accepted_at) VALUES
('00000000-0000-4000-8000-000000000013','m_priya','+919000000006','operator','active','m_shreya',now()-interval '10 days');
INSERT INTO workspace_members (listing_id, member_id, phone, role, state, invited_by) VALUES
('00000000-0000-4000-8000-000000000013',NULL,'+919876500000','admin','pending','m_shreya');

-- impressions for FR32 reports
INSERT INTO impressions (target_kind, target_id, member_id, surface, sponsored, kind, at)
SELECT 'listing','00000000-0000-4000-8000-000000000003', NULL, 'businesses', (g % 3 = 0), 'impression', now() - (g || ' hours')::interval FROM generate_series(1, 160) g;
INSERT INTO impressions (target_kind, target_id, member_id, surface, sponsored, kind, at)
SELECT 'listing','00000000-0000-4000-8000-000000000003', NULL, 'listing_detail', (g % 4 = 0), 'view', now() - (g*3 || ' hours')::interval FROM generate_series(1, 38) g;
INSERT INTO impressions (target_kind, target_id, member_id, surface, sponsored, kind, at) VALUES
('listing','00000000-0000-4000-8000-000000000003','m_arjun','listing_detail',true,'save',now()-interval '1 day'),
('listing','00000000-0000-4000-8000-000000000003','m_arjun','listing_detail',true,'enquiry',now()-interval '1 day'),
('listing','00000000-0000-4000-8000-000000000003','m_meena','listing_detail',false,'enquiry',now()-interval '42 days'),
('listing','00000000-0000-4000-8000-000000000003','m_meena','enquiry',false,'outcome',now()-interval '35 days');

-- ---------------------------------------------------------------- moderation (FR39-FR41)
INSERT INTO moderation_cases (id, object_kind, object_id, subject_member_id, source, severity, state, reporter_count, primary_reason, distribution_limited, target_due_at, created_at) VALUES
('00000000-0000-4000-8000-000000000701','opportunity','00000000-0000-4000-8000-000000000121','m_meena','auto_flag','high','open',0,'advance_payment',true,now()+interval '10 hours',now()-interval '2 hours'),
('00000000-0000-4000-8000-000000000702','listing','00000000-0000-4000-8000-000000000016','m_vikram','report','medium','actioned',2,'fake',false,now()-interval '30 days',now()-interval '32 days'),
('00000000-0000-4000-8000-000000000703','review',(SELECT id FROM reviews WHERE state='disputed'),'m_deepak','review_dispute','low','open',0,'retaliation',false,now()+interval '60 hours',now()-interval '12 hours');
UPDATE moderation_cases SET action='suspend', action_duration_days=30, reason_code='fake_listing', operator_id='m_neha_ops', decided_at=now()-interval '31 days' WHERE id='00000000-0000-4000-8000-000000000702';
INSERT INTO reports (reporter_id, case_id, object_kind, object_id, reason, evidence_text, created_at) VALUES
('m_deepak','00000000-0000-4000-8000-000000000702','listing','00000000-0000-4000-8000-000000000016','fake','Shop at this address is a different business.',now()-interval '32 days'),
('m_kavita','00000000-0000-4000-8000-000000000702','listing','00000000-0000-4000-8000-000000000016','impersonation','Uses another tailor''s photos.',now()-interval '31 days');
INSERT INTO review_disputes (review_id, disputer_id, reason, case_id, created_at) VALUES
((SELECT id FROM reviews WHERE state='disputed'),'m_anita','retaliation','00000000-0000-4000-8000-000000000703',now()-interval '12 hours');
INSERT INTO appeals (case_id, member_id, text, state, created_at) VALUES
('00000000-0000-4000-8000-000000000702','m_vikram','Sethi Uniforms is our second shop; the photos are ours from 2023. Attaching the rental agreement.','open',now()-interval '20 days');

-- ---------------------------------------------------------------- legal documents (FR53)
INSERT INTO legal_documents (kind, version, language, title, body) VALUES
('privacy',1,'en','Vyapar privacy notice','What we collect: your listing details, opportunities you post, enquiries and reviews you write, and your privacy settings. Why: to run discovery, enquiries and verification. Who sees it: members see only what you make public; contact channels are shared only after you accept an enquiry. Retention: while your account is active, then 30 days after deletion (audit and dispute records retained as required). Your rights: export, correct, withdraw consent or delete from the Privacy screen. Grievance: grievance@forkhatri.example, replies within 7 days.'),
('privacy',1,'hi','व्यापार गोपनीयता सूचना','हम क्या एकत्र करते हैं: आपकी लिस्टिंग, अवसर, पूछताछ और समीक्षाएँ। क्यों: खोज, पूछताछ और सत्यापन चलाने के लिए। कौन देखता है: केवल वह जो आप सार्वजनिक करते हैं; संपर्क केवल स्वीकृत पूछताछ के बाद। अधिकार: निर्यात, सुधार, सहमति वापसी, हटाना। शिकायत: grievance@forkhatri.example'),
('privacy',1,'te','వ్యాపార్ గోప్యతా నోటీసు','మేము సేకరించేవి: మీ లిస్టింగ్, అవకాశాలు, ఎంక్వైరీలు, సమీక్షలు. ఎందుకు: డిస్కవరీ, ఎంక్వైరీలు, ధృవీకరణ కోసం. ఎవరు చూస్తారు: మీరు పబ్లిక్ చేసినవి మాత్రమే; కాంటాక్ట్ ఆమోదించిన తర్వాతే. హక్కులు: ఎగుమతి, సవరణ, సమ్మతి ఉపసంహరణ, తొలగింపు. ఫిర్యాదు: grievance@forkhatri.example'),
('terms',1,'en','Vyapar terms of use','Vyapar is a community directory and opportunity network. Post only what you are entitled to share; never ask for advance payments through Vyapar; respect the block and report tools. Paid boosts change reach inside the eligible audience only and never change verification, reputation or ranking. Appeals: within 15 days of any moderation outcome from the outcome screen.'),
('terms',1,'hi','व्यापार उपयोग की शर्तें','व्यापार एक सामुदायिक निर्देशिका और अवसर नेटवर्क है। केवल वही पोस्ट करें जिसे साझा करने का आपको अधिकार है; अग्रिम भुगतान न माँगें; ब्लॉक और रिपोर्ट टूल का सम्मान करें। भुगतान की गई बूस्ट केवल पहुँच बदलती है, सत्यापन या रैंकिंग नहीं।'),
('terms',1,'te','వ్యాపార్ వినియోగ నిబంధనలు','వ్యాపార్ ఒక కమ్యూనిటీ డైరెక్టరీ మరియు అవకాశాల నెట్‌వర్క్. మీకు హక్కు ఉన్నదే పోస్ట్ చేయండి; ముందస్తు చెల్లింపులు అడగవద్దు; బ్లాక్ మరియు రిపోర్ట్ సాధనాలను గౌరవించండి. చెల్లింపు బూస్ట్‌లు రీచ్ మాత్రమే మారుస్తాయి, ధృవీకరణ లేదా ర్యాంకింగ్ కాదు.');
INSERT INTO acceptances (member_id, kind, version) SELECT id, 'privacy', 1 FROM members WHERE first_run_done;
INSERT INTO acceptances (member_id, kind, version) SELECT id, 'terms', 1 FROM members WHERE first_run_done;

-- ---------------------------------------------------------------- notifications (FR21)
INSERT INTO notifications (member_id, kind, template_id, title, body, link, created_at, read_at) VALUES
('m_krishna','opportunity_match','opp_strong_match','Strong match: Frontend developer (React) — Nanda Labs','Matches your capability: software · 7 km away · posted 2 days ago','/opportunity/00000000-0000-4000-8000-000000000101',now()-interval '2 days',now()-interval '1 day'),
('m_krishna','enquiry','enquiry_reply','Anita Khatri replied to your enquiry','"For a services business with under 30 invoices a month it is ₹999/month…"','/enquiry/00000000-0000-4000-8000-000000000201',now()-interval '1 day',NULL),
('m_krishna','enquiry','enquiry_new','New enquiry on "Need a plumber for a 2BHK"','Ravi Mehra: "I can come tomorrow at 6.30 pm…"','/enquiry/00000000-0000-4000-8000-000000000203',now()-interval '3 hours',NULL),
('m_krishna','review_invite','review_invite','How did it go with Khatri & Associates?','Your enquiry is in progress. When it is done, tell other members whether you would recommend them.','/review/new?enquiry=00000000-0000-4000-8000-000000000201',now()-interval '6 hours',NULL),
('m_krishna','digest','daily_digest','Your daily digest: 4 new opportunities','Content writer for product blog · Sales intern · Decor helper · Electrical rewiring helper','/discover',now()-interval '18 hours',now()-interval '17 hours');

-- ---------------------------------------------------------------- derived preferences (FR38)
INSERT INTO derived_preferences (member_id, key, value, evidence, source, state) VALUES
('m_krishna','max_distance_km','{"km":15}','You marked 3 opportunities "Too far" in the last 30 days (Warangal, Vijayawada, Karimnagar).','not_interested:too_far','proposed');

-- ---------------------------------------------------------------- data requests (FR37)
INSERT INTO data_requests (member_id, kind, state, due_at, created_at) VALUES
('m_krishna','export','in_progress',now()+interval '60 hours',now()-interval '12 hours');

-- ---------------------------------------------------------------- analytics sample (FR45)
INSERT INTO analytics_events (member_pseudo, object_id, surface, event, level, props, at)
SELECT md5('m_' || (g % 12)), '00000000-0000-4000-8000-0000000001' || lpad((1 + g % 22)::text, 2, '0'), 'discover', 'impression', 'impression', '{}', now() - (g || ' minutes')::interval FROM generate_series(1, 600) g;
INSERT INTO analytics_events (member_pseudo, object_id, surface, event, level, props, at)
SELECT md5('m_' || (g % 12)), '00000000-0000-4000-8000-0000000001' || lpad((1 + g % 22)::text, 2, '0'), 'opportunity_detail', 'detail_view', 'view', '{}', now() - (g*7 || ' minutes')::interval FROM generate_series(1, 140) g;
INSERT INTO analytics_events (member_pseudo, object_id, surface, event, level, props, at)
SELECT md5('m_' || (g % 12)), '00000000-0000-4000-8000-0000000001' || lpad((1 + g % 22)::text, 2, '0'), 'opportunity_detail', 'enquiry_submitted', 'action', '{"relevant":true}', now() - (g*50 || ' minutes')::interval FROM generate_series(1, 26) g;
INSERT INTO analytics_events (member_pseudo, object_id, surface, event, level, props, at)
SELECT md5('m_' || (g % 12)), NULL, 'businesses', 'search', 'action', jsonb_build_object('zero_result', g % 9 = 0), now() - (g*11 || ' minutes')::interval FROM generate_series(1, 90) g;

-- ---------------------------------------------------------------- audit sample
INSERT INTO audit_events (actor_id, object_kind, object_id, action, reason_code, details, at) VALUES
('m_neha_ops','listing','00000000-0000-4000-8000-000000000001','verification.verify','gst_lookup_ok','{"document":"gst"}',now()-interval '40 days'),
('m_neha_ops','listing','00000000-0000-4000-8000-000000000016','moderation.suspend','fake_listing','{"days":30}',now()-interval '31 days'),
('m_sunita','promotion','00000000-0000-4000-8000-000000000501','promotion.activate','payment_succeeded','{}',now()-interval '2 days');
