-- Marathi (mr) and Kannada (kn) join English, Hindi and Telugu (owner request
-- 2026-10-06). Expertise names get a Marathi and a Kannada column. They stay
-- nullable so older inserts that name only en/hi/te keep working; the API
-- falls back to the English name when a translation is missing.
SET search_path TO counsel, public;

ALTER TABLE expertise_area ADD COLUMN IF NOT EXISTS name_mr text;
ALTER TABLE expertise_area ADD COLUMN IF NOT EXISTS name_kn text;

UPDATE expertise_area a SET name_mr = v.mr, name_kn = v.kn
FROM (VALUES
  ('business',      'व्यवसाय आणि उद्योजकता',        'ವ್ಯಾಪಾರ ಮತ್ತು ಉದ್ಯಮಶೀಲತೆ'),
  ('career',        'करिअर आणि रोजगार',             'ವೃತ್ತಿಜೀವನ ಮತ್ತು ಉದ್ಯೋಗ'),
  ('freelancing',   'फ्रीलान्सिंग आणि क्रिएटर्स',      'ಫ್ರೀಲ್ಯಾನ್ಸಿಂಗ್ ಮತ್ತು ಕ್ರಿಯೇಟರ್‌ಗಳು'),
  ('technology',    'तंत्रज्ञान आणि आयटी',            'ತಂತ್ರಜ್ಞಾನ ಮತ್ತು ಐಟಿ'),
  ('agriculture',   'कृषी आणि शेती',                'ಕೃಷಿ ಮತ್ತು ಬೇಸಾಯ'),
  ('education',     'शिक्षण आणि शैक्षणिक क्षेत्र',     'ಶಿಕ್ಷಣ ಮತ್ತು ಶೈಕ್ಷಣಿಕ ಕ್ಷೇತ್ರ'),
  ('legal',         'कायदेशीर',                     'ಕಾನೂನು'),
  ('finance',       'वित्त आणि कर',                  'ಹಣಕಾಸು ಮತ್ತು ತೆರಿಗೆ'),
  ('investment',    'विमा आणि गुंतवणूक',              'ವಿಮೆ ಮತ್ತು ಹೂಡಿಕೆ'),
  ('health',        'वैद्यकीय आणि आरोग्य',            'ವೈದ್ಯಕೀಯ ಮತ್ತು ಆರೋಗ್ಯ'),
  ('mental-health', 'मानसिक आरोग्य',                'ಮಾನಸಿಕ ಆರೋಗ್ಯ'),
  ('nutrition',     'पोषण आणि आहार',                'ಪೌಷ್ಟಿಕ ಆಹಾರ'),
  ('fitness',       'फिटनेस आणि खेळ',               'ಫಿಟ್‌ನೆಸ್ ಮತ್ತು ಕ್ರೀಡೆ'),
  ('architecture',  'वास्तुकला आणि बांधकाम',          'ವಾಸ್ತುಶಿಲ್ಪ ಮತ್ತು ನಿರ್ಮಾಣ'),
  ('property',      'मालमत्ता आणि रिअल इस्टेट',       'ಆಸ್ತಿ ಮತ್ತು ರಿಯಲ್ ಎಸ್ಟೇಟ್'),
  ('design',        'डिझाइन आणि सर्जनशील कला',       'ವಿನ್ಯಾಸ ಮತ್ತು ಸೃಜನಶೀಲ ಕಲೆ'),
  ('media',         'मीडिया आणि कंटेंट',              'ಮಾಧ್ಯಮ ಮತ್ತು ಕಂಟೆಂಟ್'),
  ('travel',        'प्रवास आणि साहस',               'ಪ್ರವಾಸ ಮತ್ತು ಸಾಹಸ'),
  ('trades',        'कुशल कारागिरी',                 'ಕುಶಲ ವೃತ್ತಿಗಳು'),
  ('manufacturing', 'उत्पादन आणि उद्योग',            'ಉತ್ಪಾದನೆ ಮತ್ತು ಕೈಗಾರಿಕೆ'),
  ('logistics',     'लॉजिस्टिक्स आणि सप्लाय चेन',     'ಲಾಜಿಸ್ಟಿಕ್ಸ್ ಮತ್ತು ಸಪ್ಲೈ ಚೈನ್'),
  ('food',          'खाद्यपदार्थ आणि आदरातिथ्य',      'ಆಹಾರ ಮತ್ತು ಆತಿಥ್ಯ'),
  ('personal',      'वैयक्तिक विकास',                'ವೈಯಕ್ತಿಕ ಅಭಿವೃದ್ಧಿ'),
  ('community',     'समाज आणि सामाजिक कार्य',         'ಸಮುದಾಯ ಮತ್ತು ಸಮಾಜ ಸೇವೆ'),
  ('science',       'विज्ञान आणि संशोधन',             'ವಿಜ್ಞಾನ ಮತ್ತು ಸಂಶೋಧನೆ'),
  ('other',         'इतर विशेष तज्ज्ञता',              'ಇತರ ವಿಶೇಷ ಪರಿಣತಿ')
) AS v(id, mr, kn)
WHERE a.id = v.id AND (a.name_mr IS NULL OR a.name_kn IS NULL);
