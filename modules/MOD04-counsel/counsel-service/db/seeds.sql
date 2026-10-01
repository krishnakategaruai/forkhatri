-- Counsel development seed (SEED_DB=true only). Realistic consultants built on
-- existing ForKhatri development members, so "Act as" personas can book them.
-- Re-runnable: every insert is keyed.
SET search_path TO counsel, public;

INSERT INTO member (member_id, display_name) VALUES
  ('33333333-3333-3333-3333-333333333333','Meera Iyer'),
  ('44444444-4444-4444-4444-444444444444','Ravi Kumar'),
  ('55555555-5555-5555-5555-555555555555','Priya Sharma'),
  ('66666666-6666-6666-6666-666666666666','Arjun Nair'),
  ('77777777-7777-7777-7777-777777777777','Neha Verma'),
  ('88888888-8888-8888-8888-888888888888','Kiran Das'),
  ('22222222-2222-2222-2222-222222222222','Vikram Rao'),
  ('c024b254-e792-4bda-8bc7-02be13a28829','Rahul Varma'),
  ('11111111-1111-1111-1111-111111111111','Asha Reddy'),
  ('a0000000-0000-4000-8000-000000000002','New Member')
ON CONFLICT (member_id) DO UPDATE SET display_name = EXCLUDED.display_name;

INSERT INTO provider (member_id, headline, intro, city, country, timezone, languages, links, status, submitted_at, reviewed_at) VALUES
  ('33333333-3333-3333-3333-333333333333',
   'Built and sold two SaaS companies. I review startup ideas honestly.',
   'I started my first company at 24, raised two rounds and sold it in 2019. The second one is profitable and runs without me. I have sat on both sides of the table — founder and angel — and I am direct: if the idea has a hole, you will hear it in the first ten minutes, along with what I would do instead. Best for founders at the idea or first-customers stage.',
   'Hyderabad', 'IN', 'Asia/Kolkata', '{en,te}', '{"linkedin":"https://linkedin.com/in/example-meera","website":"https://example.com/meera"}', 'approved', now() - interval '80 days', now() - interval '78 days'),
  ('44444444-4444-4444-4444-444444444444',
   'Chartered Accountant, 14 years. GST, income tax and small-business books.',
   'I run a CA practice in Vijayawada serving traders, freelancers and small manufacturers. Most of what people book me for: which GST scheme fits, how to file after missed deadlines, tax on freelance income from abroad, and what a clean set of books looks like before you apply for a loan.',
   'Vijayawada', 'IN', 'Asia/Kolkata', '{en,te,hi}', '{"website":"https://example.com/ravi-ca"}', 'approved', now() - interval '70 days', now() - interval '69 days'),
  ('55555555-5555-5555-5555-555555555555',
   'Senior product designer at a fintech. UX reviews that fix conversion, not colours.',
   'Twelve years of product design, the last six leading design for a payments app used by millions. I review websites and apps on a screen share and tell you exactly where people drop off and why. You leave with a prioritised list you can hand to a developer the same day.',
   'Bengaluru', 'IN', 'Asia/Kolkata', '{en,hi}', '{"portfolio":"https://example.com/priya","linkedin":"https://linkedin.com/in/example-priya"}', 'approved', now() - interval '60 days', now() - interval '59 days'),
  ('66666666-6666-6666-6666-666666666666',
   'Advocate, Telangana High Court. Property, family and tenancy matters.',
   'Enrolled with the Bar Council in 2011. I explain where you actually stand — what a notice means, whether a case is worth filing, what documents you need for a property registration — in plain language before you spend money on litigation.',
   'Hyderabad', 'IN', 'Asia/Kolkata', '{en,te}', '{}', 'approved', now() - interval '50 days', now() - interval '48 days'),
  ('77777777-7777-7777-7777-777777777777',
   'Engineering manager at a US product company. Career switches, interviews, offers.',
   'I have hired more than a hundred engineers and coached many more through promotions and switches. Book me before an interview loop, when weighing two offers, or when you feel stuck at the same level for years.',
   'Pune', 'IN', 'Asia/Kolkata', '{en,hi}', '{"linkedin":"https://linkedin.com/in/example-neha"}', 'approved', now() - interval '40 days', now() - interval '39 days'),
  ('88888888-8888-8888-8888-888888888888',
   'Third-generation mango and paddy farmer. Drip, soil and market timing.',
   'Twenty acres near Nuzvid. I moved the whole farm to drip irrigation and organic inputs and doubled net income in four years. I help other farmers plan the same move without the mistakes I made.',
   'Nuzvid', 'IN', 'Asia/Kolkata', '{te,en}', '{"youtube":"https://youtube.com/@example-kiran"}', 'approved', now() - interval '30 days', now() - interval '29 days'),
  ('22222222-2222-2222-2222-222222222222',
   'Himalayan trek leader, 60+ high-altitude treks. Plan a safe first trek.',
   'Certified mountaineer (NIM Uttarkashi). I lead treks from Sandakphu to Stok Kangri and plan routes, gear, fitness timelines and acclimatisation for families and first-timers.',
   'Hyderabad', 'IN', 'Asia/Kolkata', '{en,hi,te}', '{"instagram":"https://instagram.com/example-vikram"}', 'pending_review', now() - interval '2 days', NULL)
ON CONFLICT (member_id) DO UPDATE SET headline = EXCLUDED.headline, intro = EXCLUDED.intro, status = EXCLUDED.status;

INSERT INTO provider_expertise (provider_id, area_id, years, is_primary) VALUES
  ('33333333-3333-3333-3333-333333333333','business',16,true),
  ('33333333-3333-3333-3333-333333333333','technology',12,false),
  ('44444444-4444-4444-4444-444444444444','finance',14,true),
  ('55555555-5555-5555-5555-555555555555','design',12,true),
  ('55555555-5555-5555-5555-555555555555','technology',8,false),
  ('66666666-6666-6666-6666-666666666666','legal',13,true),
  ('66666666-6666-6666-6666-666666666666','property',10,false),
  ('77777777-7777-7777-7777-777777777777','career',15,true),
  ('77777777-7777-7777-7777-777777777777','technology',15,false),
  ('88888888-8888-8888-8888-888888888888','agriculture',22,true),
  ('22222222-2222-2222-2222-222222222222','travel',18,true),
  ('22222222-2222-2222-2222-222222222222','fitness',10,false)
ON CONFLICT DO NOTHING;

INSERT INTO provider_evidence (id, provider_id, kind, title, issuer, year_from, year_to, reference_no, status) VALUES
  ('e0000000-0000-4000-8000-000000000001','33333333-3333-3333-3333-333333333333','experience','Founder & CEO, Cloudsetu (acquired 2019)','Cloudsetu',2012,2019,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000002','33333333-3333-3333-3333-333333333333','experience','Founder, Ledgerly','Ledgerly',2020,NULL,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000003','33333333-3333-3333-3333-333333333333','qualification','B.Tech Computer Science','IIT Madras',2004,2008,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000011','44444444-4444-4444-4444-444444444444','qualification','Chartered Accountant','ICAI',2008,2011,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000012','44444444-4444-4444-4444-444444444444','registration','ICAI Membership','ICAI',2011,NULL,'ICAI-2xxxxx','verified'),
  ('e0000000-0000-4000-8000-000000000013','44444444-4444-4444-4444-444444444444','business','R. Kumar & Associates','Vijayawada',2012,NULL,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000021','55555555-5555-5555-5555-555555555555','experience','Design Lead, PayNow','PayNow',2019,NULL,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000022','55555555-5555-5555-5555-555555555555','portfolio','Case studies (8 shipped products)','example.com/priya',NULL,NULL,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000031','66666666-6666-6666-6666-666666666666','qualification','LL.B.','Osmania University',2006,2009,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000032','66666666-6666-6666-6666-666666666666','registration','Bar Council of Telangana enrolment','Bar Council of Telangana',2011,NULL,'TS/xxxx/2011','verified'),
  ('e0000000-0000-4000-8000-000000000041','77777777-7777-7777-7777-777777777777','experience','Engineering Manager, Northstar Inc.','Northstar Inc.',2018,NULL,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000051','88888888-8888-8888-8888-888888888888','experience','Owner-farmer, 20 acres, Nuzvid','Self',2003,NULL,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000052','88888888-8888-8888-8888-888888888888','certification','Organic certification (NPOP)','APEDA-accredited body',2021,NULL,NULL,'verified'),
  ('e0000000-0000-4000-8000-000000000061','22222222-2222-2222-2222-222222222222','certification','Basic & Advanced Mountaineering','NIM Uttarkashi',2007,2008,NULL,'submitted'),
  ('e0000000-0000-4000-8000-000000000062','22222222-2222-2222-2222-222222222222','experience','Trek leader, 60+ Himalayan treks','Independent',2009,NULL,NULL,'submitted')
ON CONFLICT (id) DO NOTHING;

INSERT INTO verification (provider_id, dimension) VALUES
  ('33333333-3333-3333-3333-333333333333','identity'),('33333333-3333-3333-3333-333333333333','contact'),('33333333-3333-3333-3333-333333333333','experience'),('33333333-3333-3333-3333-333333333333','qualification'),
  ('44444444-4444-4444-4444-444444444444','identity'),('44444444-4444-4444-4444-444444444444','contact'),('44444444-4444-4444-4444-444444444444','qualification'),('44444444-4444-4444-4444-444444444444','registration'),('44444444-4444-4444-4444-444444444444','business'),
  ('55555555-5555-5555-5555-555555555555','identity'),('55555555-5555-5555-5555-555555555555','experience'),('55555555-5555-5555-5555-555555555555','portfolio'),
  ('66666666-6666-6666-6666-666666666666','identity'),('66666666-6666-6666-6666-666666666666','contact'),('66666666-6666-6666-6666-666666666666','qualification'),('66666666-6666-6666-6666-666666666666','registration'),
  ('77777777-7777-7777-7777-777777777777','identity'),('77777777-7777-7777-7777-777777777777','experience'),
  ('88888888-8888-8888-8888-888888888888','identity'),('88888888-8888-8888-8888-888888888888','experience'),('88888888-8888-8888-8888-888888888888','certification')
ON CONFLICT DO NOTHING;

INSERT INTO service (id, provider_id, area_id, title, description, outcomes, duration_min, price_minor, formats, recording_allowed) VALUES
  ('50000000-0000-4000-8000-000000000001','33333333-3333-3333-3333-333333333333','business','Startup idea review','Bring a one-page description or a deck. I will pressure-test the problem, the customer, pricing and the first 90 days.','{"A clear yes/no/not-yet on the idea","The three biggest risks and how to test them cheaply","A 90-day plan"}',45,200000,'{video,screen,files}',true),
  ('50000000-0000-4000-8000-000000000002','33333333-3333-3333-3333-333333333333','business','Pricing and go-to-market discussion','For products that exist and need customers. We work through pricing, first channel and the sales conversation.','{"A pricing model to test","Your first channel, with a weekly plan"}',60,300000,'{video,screen}',false),
  ('50000000-0000-4000-8000-000000000011','44444444-4444-4444-4444-444444444444','finance','GST and tax consultation','Which scheme fits you, what you owe, what to file and when. Bring your invoices or a summary.','{"Your scheme and filing calendar","A list of what to fix before the next return"}',30,120000,'{video,audio,files}',true),
  ('50000000-0000-4000-8000-000000000012','44444444-4444-4444-4444-444444444444','finance','Books review before a loan or investor','A screen-share walk through your books with a lender''s eye.','{"What a lender will question","Fixes in priority order"}',60,250000,'{video,screen,files}',true),
  ('50000000-0000-4000-8000-000000000021','55555555-5555-5555-5555-555555555555','design','Website or app UX review','Live on a screen share. I go through your key flow as a first-time user and narrate every hesitation.','{"A prioritised fix list","Annotated screenshots after the call"}',60,300000,'{video,screen,files}',true),
  ('50000000-0000-4000-8000-000000000022','55555555-5555-5555-5555-555555555555','design','Design portfolio and career chat','For designers: portfolio review, interview prep, moving from agency to product.','{"Portfolio feedback you can act on this week"}',30,150000,'{video}',false),
  ('50000000-0000-4000-8000-000000000031','66666666-6666-6666-6666-666666666666','legal','Legal consultation — property, family, tenancy','Understand your position and options before you act. Not a substitute for representation in court.','{"Where you stand, in plain words","Documents to gather","Whether to negotiate, notice or file"}',30,150000,'{video,audio,files}',false),
  ('50000000-0000-4000-8000-000000000041','77777777-7777-7777-7777-777777777777','career','Career switch and interview strategy','Where you are, where you want to be, and the shortest credible path. Includes one mock question round.','{"A 6-month plan","A resume rewrite outline","Interview focus areas"}',45,180000,'{video,screen}',true),
  ('50000000-0000-4000-8000-000000000042','77777777-7777-7777-7777-777777777777','career','Offer negotiation call','Bring both offers. We decide what to ask for and exactly how to say it.','{"A negotiation script","A decision"}',30,150000,'{video,audio}',false),
  ('50000000-0000-4000-8000-000000000051','88888888-8888-8888-8888-888888888888','agriculture','Drip irrigation and soil plan for your field','Tell me your crop, acreage and water source. We plan the switch, the cost and the season timing.','{"A layout and cost estimate","Season-by-season plan","Where to buy without overpaying"}',45,80000,'{video,audio,files}',true),
  ('50000000-0000-4000-8000-000000000061','22222222-2222-2222-2222-222222222222','travel','Plan your first Himalayan trek','Route, fitness timeline, gear list and acclimatisation for your group.','{"A route and date","A 10-week fitness plan","A gear list"}',45,100000,'{video}',false)
ON CONFLICT (id) DO NOTHING;

-- Weekly availability (provider local time). Weekday 0 = Monday.
INSERT INTO availability_rule (provider_id, weekday, start_time, end_time)
SELECT p, d, s::time, e::time FROM (VALUES
  ('33333333-3333-3333-3333-333333333333'::uuid,1,'18:00','21:00'),('33333333-3333-3333-3333-333333333333',3,'18:00','21:00'),('33333333-3333-3333-3333-333333333333',5,'10:00','13:00'),
  ('44444444-4444-4444-4444-444444444444',0,'17:00','20:00'),('44444444-4444-4444-4444-444444444444',1,'17:00','20:00'),('44444444-4444-4444-4444-444444444444',2,'17:00','20:00'),('44444444-4444-4444-4444-444444444444',3,'17:00','20:00'),('44444444-4444-4444-4444-444444444444',4,'17:00','20:00'),
  ('55555555-5555-5555-5555-555555555555',0,'19:00','22:00'),('55555555-5555-5555-5555-555555555555',2,'19:00','22:00'),('55555555-5555-5555-5555-555555555555',5,'11:00','16:00'),
  ('66666666-6666-6666-6666-666666666666',0,'16:00','19:00'),('66666666-6666-6666-6666-666666666666',1,'16:00','19:00'),('66666666-6666-6666-6666-666666666666',2,'16:00','19:00'),('66666666-6666-6666-6666-666666666666',3,'16:00','19:00'),('66666666-6666-6666-6666-666666666666',5,'10:00','13:00'),
  ('77777777-7777-7777-7777-777777777777',1,'20:00','22:30'),('77777777-7777-7777-7777-777777777777',3,'20:00','22:30'),('77777777-7777-7777-7777-777777777777',6,'10:00','14:00'),
  ('88888888-8888-8888-8888-888888888888',0,'19:00','21:00'),('88888888-8888-8888-8888-888888888888',2,'19:00','21:00'),('88888888-8888-8888-8888-888888888888',4,'19:00','21:00'),('88888888-8888-8888-8888-888888888888',6,'08:00','12:00'),
  ('22222222-2222-2222-2222-222222222222',5,'09:00','13:00'),('22222222-2222-2222-2222-222222222222',6,'09:00','13:00')
) AS v(p,d,s,e)
WHERE NOT EXISTS (SELECT 1 FROM availability_rule r WHERE r.provider_id = v.p);

-- History: completed consultations and reviews, so reputation is real.
INSERT INTO booking (id, service_id, provider_id, seeker_id, starts_at, ends_at, status, brief, service_title, duration_min, currency, gross_minor, platform_fee_minor, provider_payable_minor, cancellation_policy, completed_at, payout_status, formats) VALUES
  ('b0000000-0000-4000-8000-000000000001','50000000-0000-4000-8000-000000000001','33333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111', now()-interval '20 days', now()-interval '20 days'+interval '45 min','completed','A marketplace for home tutors in tier-2 cities.','Startup idea review',45,'INR',200000,4000,196000,'{}', now()-interval '20 days'+interval '50 min','paid','{video}'),
  ('b0000000-0000-4000-8000-000000000002','50000000-0000-4000-8000-000000000001','33333333-3333-3333-3333-333333333333','c024b254-e792-4bda-8bc7-02be13a28829', now()-interval '12 days', now()-interval '12 days'+interval '45 min','completed','B2B SaaS for pharmacies.','Startup idea review',45,'INR',200000,4000,196000,'{}', now()-interval '12 days'+interval '50 min','paid','{video}'),
  ('b0000000-0000-4000-8000-000000000003','50000000-0000-4000-8000-000000000002','33333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111', now()-interval '5 days', now()-interval '5 days'+interval '60 min','completed','Follow-up on pricing.','Pricing and go-to-market discussion',60,'INR',300000,6000,294000,'{}', now()-interval '5 days'+interval '65 min','eligible','{video}'),
  ('b0000000-0000-4000-8000-000000000011','50000000-0000-4000-8000-000000000011','44444444-4444-4444-4444-444444444444','c024b254-e792-4bda-8bc7-02be13a28829', now()-interval '30 days', now()-interval '30 days'+interval '30 min','completed','Freelance income from US clients.','GST and tax consultation',30,'INR',120000,2400,117600,'{}', now()-interval '30 days'+interval '35 min','paid','{video}'),
  ('b0000000-0000-4000-8000-000000000012','50000000-0000-4000-8000-000000000011','44444444-4444-4444-4444-444444444444','11111111-1111-1111-1111-111111111111', now()-interval '9 days', now()-interval '9 days'+interval '30 min','completed','Missed two GST returns.','GST and tax consultation',30,'INR',120000,2400,117600,'{}', now()-interval '9 days'+interval '35 min','paid','{video}'),
  ('b0000000-0000-4000-8000-000000000021','50000000-0000-4000-8000-000000000021','55555555-5555-5555-5555-555555555555','c024b254-e792-4bda-8bc7-02be13a28829', now()-interval '15 days', now()-interval '15 days'+interval '60 min','completed','Checkout drop-off on our store.','Website or app UX review',60,'INR',300000,6000,294000,'{}', now()-interval '15 days'+interval '65 min','paid','{video,screen}'),
  ('b0000000-0000-4000-8000-000000000031','50000000-0000-4000-8000-000000000031','66666666-6666-6666-6666-666666666666','11111111-1111-1111-1111-111111111111', now()-interval '25 days', now()-interval '25 days'+interval '30 min','completed','Tenant not vacating.','Legal consultation — property, family, tenancy',30,'INR',150000,3000,147000,'{}', now()-interval '25 days'+interval '35 min','paid','{video}'),
  ('b0000000-0000-4000-8000-000000000041','50000000-0000-4000-8000-000000000041','77777777-7777-7777-7777-777777777777','c024b254-e792-4bda-8bc7-02be13a28829', now()-interval '8 days', now()-interval '8 days'+interval '45 min','completed','Moving from services to product company.','Career switch and interview strategy',45,'INR',180000,3600,176400,'{}', now()-interval '8 days'+interval '50 min','paid','{video}'),
  ('b0000000-0000-4000-8000-000000000051','50000000-0000-4000-8000-000000000051','88888888-8888-8888-8888-888888888888','11111111-1111-1111-1111-111111111111', now()-interval '18 days', now()-interval '18 days'+interval '45 min','completed','5 acres of mango, borewell.','Drip irrigation and soil plan for your field',45,'INR',80000,1600,78400,'{}', now()-interval '18 days'+interval '50 min','paid','{video}')
ON CONFLICT (id) DO NOTHING;

-- Past bookings carry the same cancellation-rule snapshot a real payment stores.
UPDATE booking SET cancellation_policy = (SELECT value FROM platform_setting WHERE key='cancellation_policy')
WHERE id::text LIKE 'b0000000-%' AND cancellation_policy = '{}'::jsonb;

INSERT INTO review (booking_id, provider_id, reviewer_id, overall, expertise, communication, professionalism, punctuality, body) VALUES
  ('b0000000-0000-4000-8000-000000000001','33333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111',5,5,5,5,5,'Blunt, useful, and she gave me a plan I actually followed. Booked again.'),
  ('b0000000-0000-4000-8000-000000000002','33333333-3333-3333-3333-333333333333','c024b254-e792-4bda-8bc7-02be13a28829',4,5,4,5,4,'Told me the idea was too early and why. Saved me months.'),
  ('b0000000-0000-4000-8000-000000000011','44444444-4444-4444-4444-444444444444','c024b254-e792-4bda-8bc7-02be13a28829',5,5,5,5,5,'Explained LUT and export invoicing in 20 minutes. Clear.'),
  ('b0000000-0000-4000-8000-000000000012','44444444-4444-4444-4444-444444444444','11111111-1111-1111-1111-111111111111',5,5,4,5,5,'Calm and practical about my missed returns.'),
  ('b0000000-0000-4000-8000-000000000021','55555555-5555-5555-5555-555555555555','c024b254-e792-4bda-8bc7-02be13a28829',5,5,5,5,4,'Found three things on the checkout page our team had argued about for weeks.'),
  ('b0000000-0000-4000-8000-000000000031','66666666-6666-6666-6666-666666666666','11111111-1111-1111-1111-111111111111',4,5,4,5,5,'Told me not to file yet and what notice to send first.'),
  ('b0000000-0000-4000-8000-000000000041','77777777-7777-7777-7777-777777777777','c024b254-e792-4bda-8bc7-02be13a28829',5,5,5,5,5,'The mock round alone was worth it.'),
  ('b0000000-0000-4000-8000-000000000051','88888888-8888-8888-8888-888888888888','11111111-1111-1111-1111-111111111111',5,5,5,5,5,'Spoke in Telugu, knew exactly what our soil needed.')
ON CONFLICT (booking_id) DO NOTHING;

INSERT INTO ledger_entry (booking_id, kind, amount_minor, currency)
SELECT id, 'gross', gross_minor, currency FROM booking WHERE id::text LIKE 'b0000000-%' AND NOT EXISTS (SELECT 1 FROM ledger_entry l WHERE l.booking_id = booking.id);
INSERT INTO ledger_entry (booking_id, kind, amount_minor, currency)
SELECT id, 'platform_fee', -platform_fee_minor, currency FROM booking WHERE id::text LIKE 'b0000000-%' AND NOT EXISTS (SELECT 1 FROM ledger_entry l WHERE l.booking_id = booking.id AND l.kind='platform_fee');
INSERT INTO ledger_entry (booking_id, kind, amount_minor, currency)
SELECT id, 'provider_payable', provider_payable_minor, currency FROM booking WHERE id::text LIKE 'b0000000-%' AND NOT EXISTS (SELECT 1 FROM ledger_entry l WHERE l.booking_id = booking.id AND l.kind='provider_payable');

INSERT INTO expertise_request (id, proposed_by, name, parent_id, note) VALUES
  ('e1000000-0000-4000-8000-000000000001','22222222-2222-2222-2222-222222222222','High-altitude trekking','travel','Trekking above 4000 m needs its own area — acclimatisation planning is a specialist skill.')
ON CONFLICT (id) DO NOTHING;
