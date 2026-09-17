-- =============================================================================
-- 002 — Module registry reference data (TR18). Not development seed data: these
-- rows describe the product's modules in every environment. Re-running updates
-- names, taglines, availability and order in place.
--
-- Dashboard is the hub itself (docs/ForKhatri-Unified-Umbrella-App-Interpretation.md),
-- so it has no tile.
-- =============================================================================

INSERT INTO registry.module (key, name, tagline_en, tagline_hi, tagline_te, availability, accent, sort_order) VALUES
  ('mangaly', 'Mangaly',
   'A trusted matrimonial journey, with your family beside you.',
   'परिवार के साथ, भरोसेमंद वैवाहिक यात्रा।',
   'మీ కుటుంబంతో కలిసి, నమ్మకమైన వివాహ ప్రయాణం.',
   'available', '#e0689b', 10),
  ('milavn', 'Milavn',
   'Find activities near you and meet people in real life.',
   'अपने आसपास की गतिविधियाँ खोजें और लोगों से असल में मिलें।',
   'మీ దగ్గరలోని కార్యక్రమాలు కనుగొని, నిజ జీవితంలో కలవండి.',
   'available', '#5b8cff', 20),
  ('vyapar', 'Vyapar',
   'Trusted businesses, professionals and real opportunities.',
   'भरोसेमंद व्यवसाय, पेशेवर और असली अवसर।',
   'నమ్మకమైన వ్యాపారాలు, నిపుణులు, నిజమైన అవకాశాలు.',
   'in_development', '#f2a33a', 30),
  ('counsel', 'Counsel',
   'Guidance from verified professionals when you need it.',
   'ज़रूरत पर सत्यापित विशेषज्ञों से मार्गदर्शन।',
   'అవసరమైనప్పుడు ధృవీకరించిన నిపుణుల మార్గదర్శనం.',
   'planned', '#36c2a8', 40),
  ('payments', 'Payment Services',
   'Everyday payments and member benefits in one place.',
   'रोज़मर्रा के भुगतान और सदस्य लाभ, एक ही जगह।',
   'రోజువారీ చెల్లింపులు, సభ్యుల ప్రయోజనాలు ఒకే చోట.',
   'planned', '#9b7bff', 50),
  ('finance', 'Loans & Finance',
   'Understand financial options and trusted partner pathways.',
   'वित्तीय विकल्प और भरोसेमंद साझेदार मार्ग समझें।',
   'ఆర్థిక ఎంపికలు, నమ్మకమైన భాగస్వామి మార్గాలు తెలుసుకోండి.',
   'planned', '#c8d44e', 60)
ON CONFLICT (key) DO UPDATE SET
  name = EXCLUDED.name,
  tagline_en = EXCLUDED.tagline_en,
  tagline_hi = EXCLUDED.tagline_hi,
  tagline_te = EXCLUDED.tagline_te,
  availability = EXCLUDED.availability,
  accent = EXCLUDED.accent,
  sort_order = EXCLUDED.sort_order,
  updated_at = now();
