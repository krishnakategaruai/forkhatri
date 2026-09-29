# Vyapar glossary: the words people see

Owner, 2026-09-29: "Terminology is really important!"

This file is the single source for Vyapar's user-facing words in English, Hindi and Telugu.
Every locale value in `vyapar-web/locales/{en,hi,te}` and `vyapar-service/app/i18n/locales/{en,hi,te}`
must use these terms. Keys and enums (`opportunity`, `listing`, `enquiry`, `employment`,
`milestone`, `boost`…) are storage names. They stay in code and never reach the screen.

## How the words were chosen

1. **Say what Apna, Job Hai and WorkIndia users say.** Blue-collar job apps show pay as a
   monthly figure ("₹10,000–₹13,000 प्रति माह"), use "नौकरी", "सैलरी" and "आवेदन करें", and
   offer "HR को कॉल करें". Delivery and sales jobs show per-order pay plus incentives alongside a
   fixed monthly salary. So Vyapar uses everyday Hindi and Telugu with the English loanwords people
   really say (job, salary, profile, post, online, request, verified), not Sanskritised or
   Telugu-grantham forms that nobody speaks.
2. **Use Upwork's terms only where a professional expects them.** "Proposal", "contract" and
   "client" are fine for a CA or a developer. "Milestone", "funded", "escrow" and "held" confuse a
   carpenter or a rider. Vyapar says **stage** and **paid in advance** instead.
3. **Local services follow Urban Company and JustDial.** The person doing the job is a
   *professional* (Urban Company's word). Customers *ask for a price* or *get a quote*
   (JustDial's "get best price / quotes").
4. **One concept, one word, in all three languages.** Before this pass, "Employment" and "Job"
   named the same thing, and so did "listing" and "profile". "Enquire Now", "Submit a Proposal" and
   "Register" were used as button labels. Hindi mixed सत्यापित/वेरिफ़ाइड, कौशल/हुनर/स्किल,
   अनुबंध/कॉन्ट्रैक्ट and प्रस्ताव/प्रपोज़ल. Telugu mixed ధృవీకరించిన/వెరిఫైడ్, సామర్థ్యాలు/నైపుణ్యాలు,
   విచారణ/అభ్యర్థన and మైలురాయి/మైల్‌స్టోన్.
5. **The Counsel boundary.** Vyapar never calls its own features "mentor", "mentoring",
   "counselling" or "guidance". Those words belong to MOD04 Counsel. The only place Counsel is named
   is the explicit "Refer to Counsel" hand-off.

## Core nouns

| Concept (storage name) | English | हिन्दी | తెలుగు | Definition | Avoid |
|---|---|---|---|---|---|
| Any item in the feed (`opportunity`) | **post** | पोस्ट (feminine: आपकी पोस्ट, नई पोस्ट) | పోస్ట్ | Something a member published: a job, project, local service need, partnership, training or community/government item | opportunity, अवसर, అవకాశం |
| Salaried work (`employment`) | **Job** / Jobs | नौकरी / नौकरियाँ | ఉద్యోగం / ఉద్యోగాలు | A salaried or daily-wage role with an employer | Employment, रोज़गार |
| Paid piece of work (`freelance`) | **Project** / Projects | प्रोजेक्ट | ప్రాజెక్ట్ / ప్రాజెక్టులు | A one-off paid piece of work with a price, usually done by a professional | Freelance, Freelance / Project, परियोजना |
| Service needed at a place (`local_service`) | **Local service** | लोकल सर्विस | లోకల్ సర్వీస్ | A repair, cleaning, catering or similar job someone needs done nearby | Local Business / Professional Service, स्थानीय सेवा, స్థానిక సేవ |
| Business tie-up (`partnership`) | **Business partnership** | बिज़नेस पार्टनरशिप | బిజినెస్ భాగస్వామ్యం | Two businesses working together | Partnership (alone), व्यापार साझेदारी |
| Course or scheme (`training`) | **Training** | ट्रेनिंग | శిక్షణ | A course or skill programme | प्रशिक्षण |
| Samaj or government item (`community`) | **Community & government** | समाज और सरकारी | సంఘం & ప్రభుత్వం | Samaj events, government schemes and drives | Community (alone), समुदाय, సమాజం |
| Business page (`listing`, kind business) | **Business profile** | बिज़नेस प्रोफ़ाइल | బిజినెస్ ప్రొఫైల్ | A shop, firm or service business people can find and contact | listing, लिस्टिंग, లిస్టింగ్ |
| Person's page (`listing`, kind professional) | **Work profile** | काम की प्रोफ़ाइल | పని ప్రొఫైల్ | A person's own page with their skills, experience and area, for every trade, rider or CA | professional listing, professional profile (a rider is not a "professional") |
| Both of the above | **profile** / My profiles | प्रोफ़ाइल / मेरी प्रोफ़ाइल | ప్రొఫైల్ / నా ప్రొఫైల్‌లు | — | My listings |
| What a person can do (`capabilities`) | **skills** (businesses: **services and skills**) | स्किल (सर्विस और स्किल) | నైపుణ్యాలు (సర్వీసులు, నైపుణ్యాలు) | The trades and services on a profile | capabilities, क्षमता, कौशल, हुनर, సామర్థ్యాలు |
| Directory | **Businesses & Professionals** | बिज़नेस और प्रोफ़ेशनल | వ్యాపారాలు & నిపుణులు | The searchable directory of profiles | — |
| A signed-in person | **member** | सदस्य | సభ్యులు | Anyone in the Khatri community on Vyapar | user, entity |
| Who published a post (`poster`) | **the person who posted** / "Posted by {name}" | पोस्ट करने वाले | పోస్ట్ చేసినవారు | — | poster, पोस्टर, పోస్టర్ |
| Who responds to a job | **applicant** | आवेदन करने वाले / आवेदक | అప్లై చేసినవారు / దరఖాస్తుదారులు | Someone who applied to a job post | candidate, seeker |
| Who pays in a contract | **client** | क्लाइंट | క్లయింట్ | The person paying for a project or service | buyer, hirer |
| Who does the work in a contract or local service (`provider`) | **professional** | प्रोफ़ेशनल | ప్రొఫెషనల్ | The person or business doing the paid work (Urban Company's word) | provider, प्रदाता, ప్రొవైడర్ |
| A conversation thread (`enquiry`) | **request** / Requests | रिक्वेस्ट | రిక్వెస్ట్ / రిక్వెస్ట్‌లు | A question, price request, application, proposal or message that opens a conversation | enquiry, पूछताछ, విచారణ (in Telugu this reads as "investigation") |
| Kinds of request | Question · Application · Proposal · Message · Interested | सवाल · आवेदन · प्रपोज़ल · मैसेज · जुड़ना है | ప్రశ్న · అప్లికేషన్ · ప్రపోజల్ · మెసేజ్ · ఆసక్తి ఉంది | — | Enquiry, Registration, Contact request |
| Where a post came from (`source_segment`) | **From your community** / **Shared from elsewhere** | आपके समाज से / बाहर से शेयर की गई | మీ సంఘం నుండి / బయటి నుండి షేర్ చేసినవి | Posted by a member, or forwarded from another website or group | Community / Public, सार्वजनिक, పబ్లిక్ |
| Kind of work a person wants (`intent`) | Looking for work · Open to work · Just looking · Not interested right now | काम ढूँढ रहे हैं · काम के लिए तैयार · बस देख रहे हैं · अभी इच्छुक नहीं | పని కోసం చూస్తున్నాను · పనికి సిద్ధంగా ఉన్నాను · ఊరికే చూస్తున్నాను · ఇప్పుడు ఆసక్తి లేదు | — | intent, seeking status, Curious |

Hindi note: "पोस्ट" is feminine (आपकी पोस्ट रोक दी गई, नई पोस्ट, खुली पोस्ट), as in Facebook's
Hindi interface.

## Actions (buttons)

| Action | English | हिन्दी | తెలుగు | Where it is used | Avoid |
|---|---|---|---|---|---|
| Publish something | **Post** / + Post | पोस्ट करें | పోస్ట్ చేయండి | Composer, nav | Post opportunity |
| Respond to a job | **Apply** | आवेदन करें | అప్లై చేయండి | Job posts (Job Hai uses "आवेदन करें") | Enquire, दरखास्त दें |
| Respond to a project | **Send proposal** | प्रपोज़ल भेजें | ప్రపోజల్ పంపండి | Project posts | Submit a Proposal, प्रस्ताव सबमिट करें |
| Respond to a local-service need | **Send a quote** | रेट बताएँ | రేటు చెప్పండి | Local service posts (the worker replies with a price) | Enquire Now, విచారించండి (reads as "investigate") |
| Ask a business its price | **Ask for a price** | रेट पूछें | రేటు అడగండి | Business profile page | Enquire Now |
| Training / community sign-up | **I'm interested** | मुझे जुड़ना है | నాకు ఆసక్తి ఉంది | Training and community posts | Register, पंजीकरण, నమోదు |
| Start a business tie-up | **Discuss partnership** | पार्टनरशिप पर बात करें | భాగస్వామ్యం గురించి మాట్లాడండి | Business profiles | Propose partnership |
| Reach someone | **Contact** · **Call** · **WhatsApp** · **Message** | संपर्क करें · कॉल करें · WhatsApp · मैसेज | సంప్రదించండి · కాల్ చేయండి · WhatsApp · మెసేజ్ | Contact tiles | संदेश (use मैसेज) |
| Move an applicant forward | **Shortlist** | शॉर्टलिस्ट करें | షార్ట్‌లిస్ట్ చేయండి | Applicants board | — |
| Take someone on | **Hire** | हायर करें | హైర్ చేయండి | Applicants board | Accept (for jobs) |
| Say no | **Decline** | मना करें | వద్దనండి / తిరస్కరించండి | Applicants, partnership requests | Reject (for people) |
| Keep for later | **Save** | सेव करें | సేవ్ చేయండి | — | Bookmark |
| Send to others | **Share** | शेयर करें | షేర్ చేయండి | — | — |
| Flag a problem | **Report** | रिपोर्ट करें | రిపోర్ట్ చేయండి | — | Flag |
| Pay to be seen more | **Promote** (verb) / **promotion** (noun) | प्रमोट करें / प्रमोशन | ప్రమోట్ చేయండి / ప్రమోషన్ | Commercial | Boost, बूस्ट, బూస్ట్ |

## Statuses

| Status | English | हिन्दी | తెలుగు |
|---|---|---|---|
| Applicant, not yet looked at | New | नए | కొత్తవి |
| Applicant shortlisted | Shortlisted | शॉर्टलिस्ट | షార్ట్‌లిస్ట్ చేసినవి |
| Applicant hired | Hired | हायर किए | హైర్ చేసినవి |
| Applicant declined | Declined | मना किए | వద్దన్నవారు |
| Post live (`active`) | Open | खुली | తెరిచి ఉంది |
| Post paused | Paused | रुकी हुई | ఆపబడింది |
| Post closed | Closed | बंद | మూసివేశారు |
| Post past its date | Expired | समय-सीमा ख़त्म | గడువు ముగిసింది |
| Post not updated for a while (`stale`) | No recent update | हाल में अपडेट नहीं | ఇటీవల అప్‌డేట్ లేదు |
| Stage not paid in (`pending`) | Not paid in yet | अभी पैसा जमा नहीं | ఇంకా డబ్బు జమ కాలేదు |
| Stage paid in and held by Vyapar (`funded`) | **Paid in advance** | एडवांस जमा | ముందే జమ అయింది |
| Worker delivered the stage (`submitted`) | Work sent | काम भेजा | పని పంపారు |
| Money released to the worker (`released`) | Paid | पेमेंट हो गया | చెల్లించారు |
| Client asked for changes | Changes requested | बदलाव माँगे | మార్పులు అడిగారు |
| Contract disagreement | In dispute | विवाद में | వివాదంలో ఉంది |

Never show `stale`, `funded`, `held`, `active_unverified`, `pending_review` or any other raw value.

## Pay

| Case | English | हिन्दी | తెలుగు |
|---|---|---|---|
| Monthly salary | ₹18,000 a month | ₹18,000 प्रति माह | నెలకు ₹18,000 |
| Salary range | ₹15,000 to ₹20,000 a month | ₹15,000 से ₹20,000 प्रति माह | నెలకు ₹15,000 నుండి ₹20,000 |
| Daily wage | ₹700 a day | ₹700 रोज़ / प्रति दिन | రోజుకు ₹700 |
| Per visit | ₹300 a visit | ₹300 प्रति विज़िट | ఒక్కో విజిట్‌కు ₹300 |
| Hourly | ₹800 an hour | ₹800 प्रति घंटा | గంటకు ₹800 |
| Project price | Fixed price ₹45,000 | फ़िक्स्ड रेट ₹45,000 | ఫిక్స్‌డ్ రేటు ₹45,000 |
| Local service | Budget ₹2,000 | बजट ₹2,000 | బడ్జెట్ ₹2,000 |
| Take-home | in hand | हाथ में | చేతికి |
| Extra pay | + incentives up to ₹5,000 | + ₹5,000 तक इंसेंटिव | + ₹5,000 వరకు ఇన్సెంటివ్‌లు |
| Professional yearly salary | **₹8–10 lakh a year (₹67,000–₹83,000 a month)** | ₹8–10 लाख सालाना (₹67,000–₹83,000 महीना) | సంవత్సరానికి ₹8–10 లక్షలు (నెలకు ₹67,000–₹83,000) |

- **Never "LPA".** About 78% of Indian job ads use it, but it is recruiter shorthand, and the
  gap between it and in-hand pay surprises most first-time employees. When a post says
  "₹8–10 LPA", the API now returns the "lakh a year" form with the monthly figure alongside
  (`legacy_compensation_label` in `vyapar-service/app/services/opportunities.py`, key
  `opportunities.compensation.yearlyLakh`). Discover cards lead with the monthly figure.
- The field label is **Pay** ("सैलरी / रेट", "జీతం / రేటు"). Never "Compensation": in Hindi
  मुआवज़ा and in Telugu పరిహారం both mean damages paid for a loss.
- Hindi uses सैलरी, not वेतन. Telugu keeps జీతం, which is the everyday word.

## Contracts

| Concept (storage) | English | हिन्दी | తెలుగు | Note |
|---|---|---|---|---|
| Contract | contract | कॉन्ट्रैक्ट | ఒప్పందం | Hindi speakers say "कॉन्ट्रैक्ट". Telugu speakers say ఒప్పందం. |
| Part of the work paid separately (`milestone`) | **stage** | चरण | దశ | Upwork's "milestone" is jargon for a blue-collar user. |
| Client puts the money in first (`fund`) | **pay in advance** | एडवांस जमा करें | ముందే జమ చేయండి | Replaces fund, funded, held and escrow. |
| Vyapar holds it | "Vyapar keeps it safe" | Vyapar उसे सुरक्षित रखता है | Vyapar దాన్ని భద్రంగా ఉంచుతుంది | — |
| Money goes to the worker | released / Paid | जारी / पेमेंट हो गया | విడుదల / చెల్లించారు | — |
| Money goes back to the client | refunded | वापस किया | తిరిగి ఇచ్చారు | — |
| Contract sent for acceptance | Contract sent | कॉन्ट्रैक्ट भेजा गया | ఒప్పందం పంపారు | not "Contract proposed" |
| Price in a proposal | Your price | आपका रेट | మీ రేటు | not "rate or bid" |
| Proposal cover note | Your note | आपका नोट | మీ నోట్ | not "cover letter" |

## Trust

| Concept | English | हिन्दी | తెలుగు | Rule |
|---|---|---|---|---|
| Checked by Vyapar | Verified | वेरिफ़ाइड | వెరిఫైడ్ | Not सत्यापित or ధృవీకరించిన. Hindi and Telugu job apps say "verified". |
| Action | Verify | वेरिफ़ाई करें | వెరిఫై చేయండి | — |
| Business documents checked (on a business) | Business verified | बिज़नेस वेरिफ़ाइड | బిజినెస్ వెరిఫైడ్ | Replaces "Business existence verified". |
| Same fact, shown on a person (`verified_business` badge) | **Verified business owner** | वेरिफ़ाइड बिज़नेस के मालिक | వెరిఫైడ్ బిజినెస్ యజమాని | A person is not "a verified business". |
| Recommendation | Recommended by {n} people | {n} लोगों ने सिफ़ारिश की | {n} మంది సిఫార్సు చేశారు | Not अनुशंसित. |
| Badges | Responds fast · Reliable · Rising · Top recommended · Repeat hires · Verified business owner | तेज़ जवाब · भरोसेमंद · उभरते हुए · सबसे ज़्यादा सिफ़ारिश · दोबारा काम दिया · वेरिफ़ाइड बिज़नेस के मालिक | త్వరగా స్పందిస్తారు · నమ్మదగినవారు · ఎదుగుతున్నవారు · ఎక్కువ మంది సిఫార్సు · మళ్లీ పని ఇచ్చారు · వెరిఫైడ్ బిజినెస్ యజమాని | — |
| Ranking reason | posted by someone verified | किसी वेरिफ़ाइड व्यक्ति की पोस्ट | వెరిఫైడ్ వ్యక్తి పోస్ట్ చేసినది | Not "verified poster". |

## Commercial

| Concept | English | हिन्दी | తెలుగు |
|---|---|---|---|
| Label on a paid item | Sponsored | स्पॉन्सर्ड | స్పాన్సర్డ్ |
| Buying reach | Promote / promotion / My promotions | प्रमोट करें / प्रमोशन / मेरे प्रमोशन | ప్రమోట్ చేయండి / ప్రమోషన్ / నా ప్రమోషన్‌లు |
| Paid plan for a business | Business Workspace | बिज़नेस वर्कस्पेस | బిజినెస్ వర్క్‌స్పేస్ |

Hindi uses स्पॉन्सर्ड, not प्रायोजित/प्रचारित. Telugu uses స్పాన్సర్డ్, not ప్రాయోజితం.

## Discover rows and filters

| Row or filter | English | हिन्दी | తెలుగు |
|---|---|---|---|
| For you | For you | आपके लिए | మీ కోసం |
| Near you | Near you | आपके पास | మీ దగ్గర |
| More to explore | More to explore | और देखें | ఇంకా చూడండి |
| From your community | From your community | आपके समाज से | మీ సంఘం నుండి |
| Shared from elsewhere | Shared from elsewhere | बाहर से शेयर की गई | బయటి నుండి షేర్ చేసినవి |
| Kind-of-work filter | Jobs · Projects · Local services · Business partnerships · Training · Community & government | नौकरियाँ · प्रोजेक्ट · लोकल सर्विस · बिज़नेस पार्टनरशिप · ट्रेनिंग · समाज और सरकारी | ఉద్యోగాలు · ప్రాజెక్టులు · లోకల్ సర్వీసులు · బిజినెస్ భాగస్వామ్యాలు · శిక్షణ · సంఘం & ప్రభుత్వం |
| Pay filter | Pay · Monthly salary · Project budget | सैलरी / बजट · महीने की सैलरी · प्रोजेक्ट बजट | జీతం / బడ్జెట్ · నెల జీతం · ప్రాజెక్ట్ బడ్జెట్ |
| Trust filter | Only from verified people · chip "Verified people" | सिर्फ़ वेरिफ़ाइड लोगों की पोस्ट · वेरिफ़ाइड लोग | వెరిఫైడ్ వారి పోస్ట్‌లు మాత్రమే · వెరిఫైడ్ వారు |
| Community word | community | समाज (as in "खत्री समाज") | సంఘం |

Sentence case everywhere ("For you", not "For You").

## Audience notes

- **Blue-collar (rider, cook, guard, plumber):** Their screens show jobs and local services. They
  use Apply, Send a quote, a month, a day, in hand and incentives, and never see stage, proposal
  or contract unless they take a project.
- **Professionals (CA, developer, designer):** Their screens show projects, proposals and
  contracts. These words match Upwork, but pay is still shown in ₹ with its period, and a yearly
  salary is always "lakh a year" with the monthly figure alongside.
- **Businesses and shop owners:** Business profile, Business Workspace, promote and Sponsored.
- One set of words serves all three. The only differences by audience are which post types a
  person meets, and so which action verb they see.

## Rules for new strings

1. Check this file first. If a concept is missing, add it here before using it.
2. Never show a storage word or enum (listing, capability, opportunity, enquiry, segment, entity,
   stale, sub_choice, employment, milestone, funded, provider, boost, poster, LPA) on screen.
3. Hindi and Telugu use the words people say (नौकरी, सैलरी, स्किल, वेरिफ़ाइड, मैसेज, प्रोफ़ाइल,
   ఉద్యోగం, జీతం, నైపుణ్యాలు, వెరిఫైడ్, అప్లై, ప్రొఫైల్). Avoid literal textbook translations.
4. Admin and operator screens use the same words. Only placeholders such as `{poster}` or
   `{listing}` keep their storage names.

## Sources

Several vendor pages returned HTTP 403 or timed out when fetched directly. For those, the evidence
below comes from search-result extracts of the named pages.

- Job Hai, Hindi job pages and Play listing. Salary is shown as "₹10,000–₹13,000 प्रति माह",
  with "HR को कॉल करें" and "नौकरी के लिए आवेदन करें":
  https://play.google.com/store/apps/details?id=com.jobhai.jobs ·
  https://www.jobhai.com/international-call-center-jobs-in-noida-cjrl
- Apna, which is free to search, apply and save jobs, with monthly salaries:
  https://apna.co/jobs · https://play.google.com/store/apps/details?id=com.apnatime
- WorkIndia, delivery jobs with per-order pay plus incentives next to a fixed monthly salary:
  https://www.workindia.in/delivery-boy-jobs/
- LPA usage, the Naukri 78% figure, and the gap with in-hand pay:
  https://www.in-hand.in/what-is-lpa/ · https://www.keka.com/lpa-salary
- Upwork, for proposal, milestone, funded and escrow:
  https://www.upwork.com/resources/freelancing-terms ·
  https://support.upwork.com/hc/en-us/articles/211063718-How-payments-for-milestones-and-fixed-price-contracts-work ·
  https://support.upwork.com/hc/en-us/articles/360000990428-What-happens-to-the-money-I-deposit-for-future-milestone-payments
- Urban Company, which calls the person doing the job a "professional": https://www.urbancompany.com/
- JustDial, where customers get the best prices and quotes: https://www.justdial.com/india
- PhonePe, in 11 Indian languages, with पैसे भेजें / డబ్బు పంపండి and refunds:
  https://en.wikipedia.org/wiki/PhonePe ·
  https://hindi.goodreturns.in/classroom/2016/12/what-is-phonepe-app-how-use-payment-transfer-000911.html
- Government trade names (e-Shram NCO list, BharatSkills trades, Bhashini). Trades such as
  प्लंबर, इलेक्ट्रीशियन, बढ़ई and राजमिस्त्री are used as spoken:
  https://instapdf.in/e-shram-nco-code-list/ · https://bharatskills.gov.in/ ·
  https://en.wikipedia.org/wiki/Bhashini
