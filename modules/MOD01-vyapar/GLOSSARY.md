# Vyapar glossary: the words people see

Owner, 2026-09-29: "Terminology is really important!"

This file is the single source for Vyapar's user-facing words in English, Hindi and Telugu.
Every locale value in `vyapar-web/locales/{en,hi,te}` and `vyapar-service/app/i18n/locales/{en,hi,te}`
must use these terms. Keys and enums (`opportunity`, `listing`, `enquiry`, `employment`,
`milestone`, `boost`…) are storage names. They stay in code and never reach the screen.

Marathi (मराठी) and Kannada (ಕನ್ನಡ) were added on 2026-10-06 as extra columns. The same rule
covers `locales/mr` and `locales/kn` in both the web app and the API.

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
6. **Marathi and Kannada follow the meaning of the Hindi and Telugu, not the English word.**
   Marathi is standard Marathi with the polite **तुम्ही** and **-ा** imperatives (करा, पाहा,
   निवडा), never Hindi written in Devanagari (आहे / नाही, not है / नहीं). Kannada is standard
   Kannada with **ನೀವು** and polite imperatives (ಮಾಡಿ, ನೋಡಿ, ಆಯ್ಕೆಮಾಡಿ). Where Marathi or
   Kannada speakers use a native everyday word that Hindi speakers replace with English, the
   native word wins: Marathi पगार (salary), करार (contract), आगाऊ (advance), तक्रार (report);
   Kannada ಸಂಬಳ, ಒಪ್ಪಂದ, ಮುಂಗಡ, ದೂರು. Where Marathi and Kannada job apps also use the English
   loanword (post, profile, verified, request, sponsored), Vyapar uses it too.
7. **Vyapar keeps its own words where the platform list differs.** The platform core list
   (`docs/LANGUAGES-MR-KN-PLAN.md`) gives पडताळलेले / ಪರಿಶೀಲಿಸಲಾಗಿದೆ for "verified" and
   संदेश / ಸಂದೇಶಗಳು for "messages". Vyapar keeps व्हेरिफाइड / ವೆರಿಫೈಡ್ and मेसेज / ಮೆಸೇಜ್,
   because its Hindi and Telugu already chose the job-app loanwords for the same reason.

## Product name

| English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ |
|---|---|---|---|---|
| Vyapar | व्यापार | వ్యాపార్ | व्यापार | ವ್ಯಾಪಾರ್ |
| ForKhatri | ForKhatri | ForKhatri | ForKhatri | ForKhatri |
| Language names (picker) | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ |

## Core nouns

| Concept (storage name) | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ | Definition | Avoid |
|---|---|---|---|---|---|---|---|
| Any item in the feed (`opportunity`) | **post** | पोस्ट (feminine: आपकी पोस्ट, नई पोस्ट) | పోస్ట్ | पोस्ट (feminine: तुमची पोस्ट, नवीन पोस्ट) | ಪೋಸ್ಟ್ / ಪೋಸ್ಟ್‌ಗಳು | Something a member published: a job, project, local service need, partnership, training or community/government item | opportunity, अवसर, అవకాశం, संधी, ಅವಕಾಶ |
| Salaried work (`employment`) | **Job** / Jobs | नौकरी / नौकरियाँ | ఉద్యోగం / ఉద్యోగాలు | नोकरी / नोकऱ्या | ಉದ್ಯೋಗ / ಉದ್ಯೋಗಗಳು | A salaried or daily-wage role with an employer | Employment, रोज़गार, रोजगार, ನೌಕರಿ |
| Paid piece of work (`freelance`) | **Project** / Projects | प्रोजेक्ट | ప్రాజెక్ట్ / ప్రాజెక్టులు | प्रोजेक्ट / प्रोजेक्ट्स | ಪ್ರಾಜೆಕ್ಟ್ / ಪ್ರಾಜೆಕ್ಟ್‌ಗಳು | A one-off paid piece of work with a price, usually done by a professional | Freelance, Freelance / Project, परियोजना, प्रकल्प, ಯೋಜನೆ |
| Service needed at a place (`local_service`) | **Local service** | लोकल सर्विस | లోకల్ సర్వీస్ | लोकल सर्व्हिस | ಲೋಕಲ್ ಸರ್ವಿಸ್ | A repair, cleaning, catering or similar job someone needs done nearby | Local Business / Professional Service, स्थानीय सेवा, స్థానిక సేవ, स्थानिक सेवा, ಸ್ಥಳೀಯ ಸೇವೆ |
| Business tie-up (`partnership`) | **Business partnership** | बिज़नेस पार्टनरशिप | బిజినెస్ భాగస్వామ్యం | बिझनेस पार्टनरशिप | ಬಿಸಿನೆಸ್ ಪಾಲುದಾರಿಕೆ | Two businesses working together | Partnership (alone), व्यापार साझेदारी, व्यावसायिक भागीदारी |
| Course or scheme (`training`) | **Training** | ट्रेनिंग | శిక్షణ | ट्रेनिंग | ತರಬೇತಿ | A course or skill programme | प्रशिक्षण |
| Samaj or government item (`community`) | **Community & government** | समाज और सरकारी | సంఘం & ప్రభుత్వం | समाज आणि सरकारी | ಸಮಾಜ ಮತ್ತು ಸರ್ಕಾರಿ | Samaj events, government schemes and drives | Community (alone), समुदाय, సమాజం, ಸಮುದಾಯ |
| Business page (`listing`, kind business) | **Business profile** | बिज़नेस प्रोफ़ाइल | బిజినెస్ ప్రొఫైల్ | बिझनेस प्रोफाइल | ಬಿಸಿನೆಸ್ ಪ್ರೊಫೈಲ್ | A shop, firm or service business people can find and contact | listing, लिस्टिंग, లిస్టింగ్, ಲಿಸ್ಟಿಂಗ್ |
| Person's page (`listing`, kind professional) | **Work profile** | काम की प्रोफ़ाइल | పని ప్రొఫైల్ | कामाचे प्रोफाइल | ಕೆಲಸದ ಪ್ರೊಫೈಲ್ | A person's own page with their skills, experience and area, for every trade, rider or CA | professional listing, professional profile (a rider is not a "professional") |
| Both of the above | **profile** / My profiles | प्रोफ़ाइल / मेरी प्रोफ़ाइल | ప్రొఫైల్ / నా ప్రొఫైల్‌లు | प्रोफाइल / माझे प्रोफाइल | ಪ್ರೊಫೈಲ್ / ನನ್ನ ಪ್ರೊಫೈಲ್‌ಗಳು | — | My listings |
| What a person can do (`capabilities`) | **skills** (businesses: **services and skills**) | स्किल (सर्विस और स्किल) | నైపుణ్యాలు (సర్వీసులు, నైపుణ్యాలు) | स्किल (सर्व्हिस आणि स्किल) | ಕೌಶಲ್ಯಗಳು (ಸರ್ವಿಸ್‌ಗಳು ಮತ್ತು ಕೌಶಲ್ಯಗಳು) | The trades and services on a profile | capabilities, क्षमता, कौशल, हुनर, సామర్థ్యాలు, ಸಾಮರ್ಥ್ಯ |
| Directory | **Businesses & Professionals** | बिज़नेस और प्रोफ़ेशनल | వ్యాపారాలు & నిపుణులు | बिझनेस आणि प्रोफेशनल | ಬಿಸಿನೆಸ್ ಮತ್ತು ಪ್ರೊಫೆಷನಲ್‌ಗಳು | The searchable directory of profiles | — |
| A signed-in person | **member** | सदस्य | సభ్యులు | सदस्य | ಸದಸ್ಯರು | Anyone in the Khatri community on Vyapar | user, entity, युजर, ಬಳಕೆದಾರ |
| Who published a post (`poster`) | **the person who posted** / "Posted by {name}" | पोस्ट करने वाले | పోస్ట్ చేసినవారు | पोस्ट करणारे | ಪೋಸ್ಟ್ ಮಾಡಿದವರು | — | poster, पोस्टर, పోస్టర్, ಪೋಸ್ಟರ್ |
| Who responds to a job | **applicant** | आवेदन करने वाले / आवेदक | అప్లై చేసినవారు / దరఖాస్తుదారులు | अर्ज करणारे / अर्जदार | ಅರ್ಜಿ ಸಲ್ಲಿಸಿದವರು / ಅರ್ಜಿದಾರರು | Someone who applied to a job post | candidate, seeker, उमेदवार, ಅಭ್ಯರ್ಥಿ |
| Who pays in a contract | **client** | क्लाइंट | క్లయింట్ | क्लायंट | ಕ್ಲೈಂಟ್ | The person paying for a project or service | buyer, hirer, ग्राहक (that is "customer") |
| Who does the work in a contract or local service (`provider`) | **professional** | प्रोफ़ेशनल | ప్రొఫెషనల్ | प्रोफेशनल | ಪ್ರೊಫೆಷನಲ್ | The person or business doing the paid work (Urban Company's word) | provider, प्रदाता, ప్రొవైడర్, पुरवठादार, ಪೂರೈಕೆದಾರ |
| A conversation thread (`enquiry`) | **request** / Requests | रिक्वेस्ट | రిక్వెస్ట్ / రిక్వెస్ట్‌లు | रिक्वेस्ट / रिक्वेस्ट्स | ರಿಕ್ವೆಸ್ಟ್ / ರಿಕ್ವೆಸ್ಟ್‌ಗಳು | A question, price request, application, proposal or message that opens a conversation | enquiry, पूछताछ, విచారణ (in Telugu this reads as "investigation"), चौकशी (reads as "inquiry/investigation"), ವಿಚಾರಣೆ (reads as a hearing or interrogation) |
| Kinds of request | Question · Application · Proposal · Message · Interested | सवाल · आवेदन · प्रपोज़ल · मैसेज · जुड़ना है | ప్రశ్న · అప్లికేషన్ · ప్రపోజల్ · మెసేజ్ · ఆసక్తి ఉంది | प्रश्न · अर्ज · प्रपोजल · मेसेज · सहभागी व्हायचे आहे | ಪ್ರಶ್ನೆ · ಅರ್ಜಿ · ಪ್ರಪೋಸಲ್ · ಮೆಸೇಜ್ · ಆಸಕ್ತಿ ಇದೆ | — | Enquiry, Registration, Contact request |
| Where a post came from (`source_segment`) | **From your community** / **Shared from elsewhere** | आपके समाज से / बाहर से शेयर की गई | మీ సంఘం నుండి / బయటి నుండి షేర్ చేసినవి | तुमच्या समाजातून / बाहेरून शेअर केलेली | ನಿಮ್ಮ ಸಮಾಜದಿಂದ / ಹೊರಗಿನಿಂದ ಹಂಚಿಕೊಂಡವು | Posted by a member, or forwarded from another website or group | Community / Public, सार्वजनिक, పబ్లిక్, ಸಾರ್ವಜನಿಕ |
| Kind of work a person wants (`intent`) | Looking for work · Open to work · Just looking · Not interested right now | काम ढूँढ रहे हैं · काम के लिए तैयार · बस देख रहे हैं · अभी इच्छुक नहीं | పని కోసం చూస్తున్నాను · పనికి సిద్ధంగా ఉన్నాను · ఊరికే చూస్తున్నాను · ఇప్పుడు ఆసక్తి లేదు | काम शोधत आहे · कामासाठी तयार · फक्त पाहत आहे · सध्या इच्छुक नाही | ಕೆಲಸ ಹುಡುಕುತ್ತಿದ್ದೇನೆ · ಕೆಲಸಕ್ಕೆ ಸಿದ್ಧ · ಸುಮ್ಮನೆ ನೋಡುತ್ತಿದ್ದೇನೆ · ಸದ್ಯಕ್ಕೆ ಆಸಕ್ತಿ ಇಲ್ಲ | — | intent, seeking status, Curious |

Hindi note: "पोस्ट" is feminine (आपकी पोस्ट रोक दी गई, नई पोस्ट, खुली पोस्ट), as in Facebook's
Hindi interface.

Marathi note: "पोस्ट" is feminine (तुमची पोस्ट थांबवली आहे, नवीन पोस्ट); "प्रोफाइल" is neuter
(तुमचे प्रोफाइल, कामाचे प्रोफाइल). "Job" is नोकरी and "work" is काम; never use काम for a job
post.

Kannada note: "Job" is ಉದ್ಯೋಗ and "work" is ಕೆಲಸ (as Telugu keeps ఉద్యోగం apart from పని), so
"Looking for work" and "Work profile" use ಕೆಲಸ while the Jobs filter uses ಉದ್ಯೋಗಗಳು. Plurals
add ‌ಗಳು after English loanwords (ಪೋಸ್ಟ್‌ಗಳು, ಪ್ರೊಫೈಲ್‌ಗಳು).

## Actions (buttons)

| Action | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ | Where it is used | Avoid |
|---|---|---|---|---|---|---|---|
| Publish something | **Post** / + Post | पोस्ट करें | పోస్ట్ చేయండి | पोस्ट करा | ಪೋಸ್ಟ್ ಮಾಡಿ | Composer, nav | Post opportunity |
| Respond to a job | **Apply** | आवेदन करें | అప్లై చేయండి | अर्ज करा | ಅರ್ಜಿ ಸಲ್ಲಿಸಿ | Job posts (Job Hai uses "आवेदन करें") | Enquire, दरखास्त दें |
| Respond to a project | **Send proposal** | प्रपोज़ल भेजें | ప్రపోజల్ పంపండి | प्रपोजल पाठवा | ಪ್ರಪೋಸಲ್ ಕಳುಹಿಸಿ | Project posts | Submit a Proposal, प्रस्ताव सबमिट करें |
| Respond to a local-service need | **Send a quote** | रेट बताएँ | రేటు చెప్పండి | रेट सांगा | ರೇಟ್ ತಿಳಿಸಿ | Local service posts (the worker replies with a price) | Enquire Now, విచారించండి (reads as "investigate"), चौकशी करा, ವಿಚಾರಿಸಿ |
| Ask a business its price | **Ask for a price** | रेट पूछें | రేటు అడగండి | रेट विचारा | ರೇಟ್ ಕೇಳಿ | Business profile page | Enquire Now |
| Training / community sign-up | **I'm interested** | मुझे जुड़ना है | నాకు ఆసక్తి ఉంది | मला सहभागी व्हायचे आहे | ನನಗೆ ಆಸಕ್ತಿ ಇದೆ | Training and community posts | Register, पंजीकरण, నమోదు, नोंदणी, ನೋಂದಣಿ |
| Start a business tie-up | **Discuss partnership** | पार्टनरशिप पर बात करें | భాగస్వామ్యం గురించి మాట్లాడండి | पार्टनरशिपबद्दल बोला | ಪಾಲುದಾರಿಕೆ ಬಗ್ಗೆ ಮಾತನಾಡಿ | Business profiles | Propose partnership |
| Reach someone | **Contact** · **Call** · **WhatsApp** · **Message** | संपर्क करें · कॉल करें · WhatsApp · मैसेज | సంప్రదించండి · కాల్ చేయండి · WhatsApp · మెసేజ్ | संपर्क करा · कॉल करा · WhatsApp · मेसेज | ಸಂಪರ್ಕಿಸಿ · ಕಾಲ್ ಮಾಡಿ · WhatsApp · ಮೆಸೇಜ್ | Contact tiles | संदेश (use मैसेज / मेसेज / ಮೆಸೇಜ್) |
| Move an applicant forward | **Shortlist** | शॉर्टलिस्ट करें | షార్ట్‌లిస్ట్ చేయండి | शॉर्टलिस्ट करा | ಶಾರ್ಟ್‌ಲಿಸ್ಟ್ ಮಾಡಿ | Applicants board | — |
| Take someone on | **Hire** | हायर करें | హైర్ చేయండి | कामावर घ्या | ಹೈರ್ ಮಾಡಿ | Applicants board | Accept (for jobs), नियुक्त करा, ನೇಮಕ ಮಾಡಿ |
| Say no | **Decline** | मना करें | వద్దనండి / తిరస్కరించండి | नकार द्या | ನಿರಾಕರಿಸಿ | Applicants, partnership requests | Reject (for people), नाकारा |
| Keep for later | **Save** | सेव करें | సేవ్ చేయండి | सेव्ह करा | ಉಳಿಸಿ | — | Bookmark |
| Send to others | **Share** | शेयर करें | షేర్ చేయండి | शेअर करा | ಹಂಚಿಕೊಳ್ಳಿ | — | — |
| Flag a problem | **Report** | रिपोर्ट करें | రిపోర్ట్ చేయండి | तक्रार करा | ದೂರು ನೀಡಿ | — | Flag |
| Pay to be seen more | **Promote** (verb) / **promotion** (noun) | प्रमोट करें / प्रमोशन | ప్రమోట్ చేయండి / ప్రమోషన్ | प्रमोट करा / प्रमोशन | ಪ್ರಮೋಟ್ ಮಾಡಿ / ಪ್ರಮೋಷನ್ | Commercial | Boost, बूस्ट, బూస్ట్, ಬೂಸ್ಟ್ |

## Statuses

| Status | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ |
|---|---|---|---|---|---|
| Applicant, not yet looked at | New | नए | కొత్తవి | नवीन | ಹೊಸಬರು |
| Applicant shortlisted | Shortlisted | शॉर्टलिस्ट | షార్ట్‌లిస్ట్ చేసినవి | शॉर्टलिस्ट केलेले | ಶಾರ್ಟ್‌ಲಿಸ್ಟ್ ಮಾಡಿದವರು |
| Applicant hired | Hired | हायर किए | హైర్ చేసినవి | कामावर घेतलेले | ಹೈರ್ ಮಾಡಿದವರು |
| Applicant declined | Declined | मना किए | వద్దన్నవారు | नकार दिलेले | ನಿರಾಕರಿಸಿದವರು |
| Post live (`active`) | Open | खुली | తెరిచి ఉంది | सुरू आहे | ತೆರೆದಿದೆ |
| Post paused | Paused | रुकी हुई | ఆపబడింది | थांबवली आहे | ನಿಲ್ಲಿಸಲಾಗಿದೆ |
| Post closed | Closed | बंद | మూసివేశారు | बंद | ಮುಚ್ಚಲಾಗಿದೆ |
| Post past its date | Expired | समय-सीमा ख़त्म | గడువు ముగిసింది | मुदत संपली | ಅವಧಿ ಮುಗಿದಿದೆ |
| Post not updated for a while (`stale`) | No recent update | हाल में अपडेट नहीं | ఇటీవల అప్‌డేట్ లేదు | अलीकडे अपडेट नाही | ಇತ್ತೀಚೆಗೆ ಅಪ್‌ಡೇಟ್ ಇಲ್ಲ |
| Stage not paid in (`pending`) | Not paid in yet | अभी पैसा जमा नहीं | ఇంకా డబ్బు జమ కాలేదు | अजून पैसे जमा नाहीत | ಇನ್ನೂ ಹಣ ಜಮಾ ಆಗಿಲ್ಲ |
| Stage paid in and held by Vyapar (`funded`) | **Paid in advance** | एडवांस जमा | ముందే జమ అయింది | आगाऊ जमा | ಮುಂಗಡ ಜಮಾ ಆಗಿದೆ |
| Worker delivered the stage (`submitted`) | Work sent | काम भेजा | పని పంపారు | काम पाठवले | ಕೆಲಸ ಕಳುಹಿಸಿದ್ದಾರೆ |
| Money released to the worker (`released`) | Paid | पेमेंट हो गया | చెల్లించారు | पेमेंट झाले | ಪಾವತಿಯಾಗಿದೆ |
| Client asked for changes | Changes requested | बदलाव माँगे | మార్పులు అడిగారు | बदल मागितले | ಬದಲಾವಣೆ ಕೇಳಿದ್ದಾರೆ |
| Contract disagreement | In dispute | विवाद में | వివాదంలో ఉంది | वादात आहे | ವಿವಾದದಲ್ಲಿದೆ |

Never show `stale`, `funded`, `held`, `active_unverified`, `pending_review` or any other raw value.

## Pay

| Case | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ |
|---|---|---|---|---|---|
| Monthly salary | ₹18,000 a month | ₹18,000 प्रति माह | నెలకు ₹18,000 | दरमहा ₹18,000 | ತಿಂಗಳಿಗೆ ₹18,000 |
| Salary range | ₹15,000 to ₹20,000 a month | ₹15,000 से ₹20,000 प्रति माह | నెలకు ₹15,000 నుండి ₹20,000 | दरमहा ₹15,000 ते ₹20,000 | ತಿಂಗಳಿಗೆ ₹15,000 ರಿಂದ ₹20,000 |
| Daily wage | ₹700 a day | ₹700 रोज़ / प्रति दिन | రోజుకు ₹700 | रोज ₹700 | ದಿನಕ್ಕೆ ₹700 |
| Per visit | ₹300 a visit | ₹300 प्रति विज़िट | ఒక్కో విజిట్‌కు ₹300 | प्रत्येक व्हिजिटला ₹300 | ಪ್ರತಿ ವಿಸಿಟ್‌ಗೆ ₹300 |
| Hourly | ₹800 an hour | ₹800 प्रति घंटा | గంటకు ₹800 | तासाला ₹800 | ಗಂಟೆಗೆ ₹800 |
| Project price | Fixed price ₹45,000 | फ़िक्स्ड रेट ₹45,000 | ఫిక్స్‌డ్ రేటు ₹45,000 | फिक्स्ड रेट ₹45,000 | ಫಿಕ್ಸ್‌ಡ್ ರೇಟ್ ₹45,000 |
| Local service | Budget ₹2,000 | बजट ₹2,000 | బడ్జెట్ ₹2,000 | बजेट ₹2,000 | ಬಜೆಟ್ ₹2,000 |
| Take-home | in hand | हाथ में | చేతికి | हातात | ಕೈಗೆ |
| Extra pay | + incentives up to ₹5,000 | + ₹5,000 तक इंसेंटिव | + ₹5,000 వరకు ఇన్సెంటివ్‌లు | + ₹5,000 पर्यंत इन्सेंटिव्ह | + ₹5,000 ವರೆಗೆ ಇನ್ಸೆಂಟಿವ್ |
| Professional yearly salary | **₹8–10 lakh a year (₹67,000–₹83,000 a month)** | ₹8–10 लाख सालाना (₹67,000–₹83,000 महीना) | సంవత్సరానికి ₹8–10 లక్షలు (నెలకు ₹67,000–₹83,000) | वर्षाला ₹8–10 लाख (दरमहा ₹67,000–₹83,000) | ವರ್ಷಕ್ಕೆ ₹8–10 ಲಕ್ಷ (ತಿಂಗಳಿಗೆ ₹67,000–₹83,000) |

- **Never "LPA".** About 78% of Indian job ads use it, but it is recruiter shorthand, and the
  gap between it and in-hand pay surprises most first-time employees. When a post says
  "₹8–10 LPA", the API now returns the "lakh a year" form with the monthly figure alongside
  (`legacy_compensation_label` in `vyapar-service/app/services/opportunities.py`, key
  `opportunities.compensation.yearlyLakh`). Discover cards lead with the monthly figure.
- The field label is **Pay** ("सैलरी / रेट", "జీతం / రేటు"). Never "Compensation": in Hindi
  मुआवज़ा and in Telugu పరిహారం both mean damages paid for a loss.
- Hindi uses सैलरी, not वेतन. Telugu keeps జీతం, which is the everyday word.
- Marathi and Kannada: the Pay label is "पगार / रेट" and "ಸಂಬಳ / ರೇಟ್". Marathi नुकसानभरपाई and
  Kannada ಪರಿಹಾರ also mean damages, so never use them for pay. Marathi keeps पगार and Kannada
  ಸಂಬಳ, the everyday words (not वेतन / ವೇತನ).

## Contracts

| Concept (storage) | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ | Note |
|---|---|---|---|---|---|---|
| Contract | contract | कॉन्ट्रैक्ट | ఒప్పందం | करार | ಒಪ್ಪಂದ | Hindi speakers say "कॉन्ट्रैक्ट". Telugu speakers say ఒప్పందం. Marathi and Kannada speakers say करार and ಒಪ್ಪಂದ. |
| Part of the work paid separately (`milestone`) | **stage** | चरण | దశ | टप्पा | ಹಂತ | Upwork's "milestone" is jargon for a blue-collar user. |
| Client puts the money in first (`fund`) | **pay in advance** | एडवांस जमा करें | ముందే జమ చేయండి | आगाऊ जमा करा | ಮುಂಗಡ ಜಮಾ ಮಾಡಿ | Replaces fund, funded, held and escrow. |
| Vyapar holds it | "Vyapar keeps it safe" | Vyapar उसे सुरक्षित रखता है | Vyapar దాన్ని భద్రంగా ఉంచుతుంది | व्यापार ते सुरक्षित ठेवते | ವ್ಯಾಪಾರ್ ಅದನ್ನು ಸುರಕ್ಷಿತವಾಗಿ ಇಡುತ್ತದೆ | — |
| Money goes to the worker | released / Paid | जारी / पेमेंट हो गया | విడుదల / చెల్లించారు | दिले / पेमेंट झाले | ಬಿಡುಗಡೆ / ಪಾವತಿಯಾಗಿದೆ | — |
| Money goes back to the client | refunded | वापस किया | తిరిగి ఇచ్చారు | परत केले | ಹಿಂದಿರುಗಿಸಲಾಗಿದೆ | — |
| Contract sent for acceptance | Contract sent | कॉन्ट्रैक्ट भेजा गया | ఒప్పందం పంపారు | करार पाठवला | ಒಪ್ಪಂದ ಕಳುಹಿಸಲಾಗಿದೆ | not "Contract proposed" |
| Price in a proposal | Your price | आपका रेट | మీ రేటు | तुमचा रेट | ನಿಮ್ಮ ರೇಟ್ | not "rate or bid" |
| Proposal cover note | Your note | आपका नोट | మీ నోట్ | तुमची नोट | ನಿಮ್ಮ ನೋಟ್ | not "cover letter" |

## Trust

| Concept | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ | Rule |
|---|---|---|---|---|---|---|
| Checked by Vyapar | Verified | वेरिफ़ाइड | వెరిఫైడ్ | व्हेरिफाइड | ವೆರಿಫೈಡ್ | Not सत्यापित or ధృవీకరించిన. Hindi and Telugu job apps say "verified". Marathi and Kannada likewise avoid पडताळलेले and ಪರಿಶೀಲಿಸಲಾಗಿದೆ here. |
| Action | Verify | वेरिफ़ाई करें | వెరిఫై చేయండి | व्हेरिफाय करा | ವೆರಿಫೈ ಮಾಡಿ | — |
| Business documents checked (on a business) | Business verified | बिज़नेस वेरिफ़ाइड | బిజినెస్ వెరిఫైడ్ | बिझनेस व्हेरिफाइड | ಬಿಸಿನೆಸ್ ವೆರಿಫೈಡ್ | Replaces "Business existence verified". |
| Same fact, shown on a person (`verified_business` badge) | **Verified business owner** | वेरिफ़ाइड बिज़नेस के मालिक | వెరిఫైడ్ బిజినెస్ యజమాని | व्हेरिफाइड बिझनेसचे मालक | ವೆರಿಫೈಡ್ ಬಿಸಿನೆಸ್ ಮಾಲೀಕರು | A person is not "a verified business". |
| Recommendation | Recommended by {n} people | {n} लोगों ने सिफ़ारिश की | {n} మంది సిఫార్సు చేశారు | {n} जणांनी शिफारस केली | {n} ಜನರು ಶಿಫಾರಸು ಮಾಡಿದ್ದಾರೆ | Not अनुशंसित. |
| Badges | Responds fast · Reliable · Rising · Top recommended · Repeat hires · Verified business owner | तेज़ जवाब · भरोसेमंद · उभरते हुए · सबसे ज़्यादा सिफ़ारिश · दोबारा काम दिया · वेरिफ़ाइड बिज़नेस के मालिक | త్వరగా స్పందిస్తారు · నమ్మదగినవారు · ఎదుగుతున్నవారు · ఎక్కువ మంది సిఫార్సు · మళ్లీ పని ఇచ్చారు · వెరిఫైడ్ బిజినెస్ యజమాని | लवकर उत्तर देतात · विश्वासू · उदयोन्मुख · सर्वाधिक शिफारस · पुन्हा काम दिले · व्हेरिफाइड बिझनेसचे मालक | ಬೇಗ ಉತ್ತರಿಸುತ್ತಾರೆ · ನಂಬಿಕಸ್ಥರು · ಬೆಳೆಯುತ್ತಿರುವವರು · ಹೆಚ್ಚು ಶಿಫಾರಸು · ಮತ್ತೆ ಕೆಲಸ ಕೊಟ್ಟಿದ್ದಾರೆ · ವೆರಿಫೈಡ್ ಬಿಸಿನೆಸ್ ಮಾಲೀಕರು | — |
| Ranking reason | posted by someone verified | किसी वेरिफ़ाइड व्यक्ति की पोस्ट | వెరిఫైడ్ వ్యక్తి పోస్ట్ చేసినది | व्हेरिफाइड व्यक्तीची पोस्ट | ವೆರಿಫೈಡ್ ವ್ಯಕ್ತಿಯ ಪೋಸ್ಟ್ | Not "verified poster". |

## Commercial

| Concept | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ |
|---|---|---|---|---|---|
| Label on a paid item | Sponsored | स्पॉन्सर्ड | స్పాన్సర్డ్ | स्पॉन्सर्ड | ಸ್ಪಾನ್ಸರ್ಡ್ |
| Buying reach | Promote / promotion / My promotions | प्रमोट करें / प्रमोशन / मेरे प्रमोशन | ప్రమోట్ చేయండి / ప్రమోషన్ / నా ప్రమోషన్‌లు | प्रमोट करा / प्रमोशन / माझे प्रमोशन | ಪ್ರಮೋಟ್ ಮಾಡಿ / ಪ್ರಮೋಷನ್ / ನನ್ನ ಪ್ರಮೋಷನ್‌ಗಳು |
| Paid plan for a business | Business Workspace | बिज़नेस वर्कस्पेस | బిజినెస్ వర్క్‌స్పేస్ | बिझनेस वर्कस्पेस | ಬಿಸಿನೆಸ್ ವರ್ಕ್‌ಸ್ಪೇಸ್ |

Hindi uses स्पॉन्सर्ड, not प्रायोजित/प्रचारित. Telugu uses స్పాన్సర్డ్, not ప్రాయోజితం.
Marathi uses स्पॉन्सर्ड, not प्रायोजित. Kannada uses ಸ್ಪಾನ್ಸರ್ಡ್, not ಪ್ರಾಯೋಜಿತ.

## Discover rows and filters

| Row or filter | English | हिन्दी | తెలుగు | मराठी | ಕನ್ನಡ |
|---|---|---|---|---|---|
| For you | For you | आपके लिए | మీ కోసం | तुमच्यासाठी | ನಿಮಗಾಗಿ |
| Near you | Near you | आपके पास | మీ దగ్గర | तुमच्या जवळ | ನಿಮ್ಮ ಹತ್ತಿರ |
| More to explore | More to explore | और देखें | ఇంకా చూడండి | आणखी पाहा | ಇನ್ನಷ್ಟು ನೋಡಿ |
| From your community | From your community | आपके समाज से | మీ సంఘం నుండి | तुमच्या समाजातून | ನಿಮ್ಮ ಸಮಾಜದಿಂದ |
| Shared from elsewhere | Shared from elsewhere | बाहर से शेयर की गई | బయటి నుండి షేర్ చేసినవి | बाहेरून शेअर केलेली | ಹೊರಗಿನಿಂದ ಹಂಚಿಕೊಂಡವು |
| Kind-of-work filter | Jobs · Projects · Local services · Business partnerships · Training · Community & government | नौकरियाँ · प्रोजेक्ट · लोकल सर्विस · बिज़नेस पार्टनरशिप · ट्रेनिंग · समाज और सरकारी | ఉద్యోగాలు · ప్రాజెక్టులు · లోకల్ సర్వీసులు · బిజినెస్ భాగస్వామ్యాలు · శిక్షణ · సంఘం & ప్రభుత్వం | नोकऱ्या · प्रोजेक्ट्स · लोकल सर्व्हिस · बिझनेस पार्टनरशिप · ट्रेनिंग · समाज आणि सरकारी | ಉದ್ಯೋಗಗಳು · ಪ್ರಾಜೆಕ್ಟ್‌ಗಳು · ಲೋಕಲ್ ಸರ್ವಿಸ್‌ಗಳು · ಬಿಸಿನೆಸ್ ಪಾಲುದಾರಿಕೆಗಳು · ತರಬೇತಿ · ಸಮಾಜ ಮತ್ತು ಸರ್ಕಾರಿ |
| Pay filter | Pay · Monthly salary · Project budget | सैलरी / बजट · महीने की सैलरी · प्रोजेक्ट बजट | జీతం / బడ్జెట్ · నెల జీతం · ప్రాజెక్ట్ బడ్జెట్ | पगार / बजेट · महिन्याचा पगार · प्रोजेक्ट बजेट | ಸಂಬಳ / ಬಜೆಟ್ · ತಿಂಗಳ ಸಂಬಳ · ಪ್ರಾಜೆಕ್ಟ್ ಬಜೆಟ್ |
| Trust filter | Only from verified people · chip "Verified people" | सिर्फ़ वेरिफ़ाइड लोगों की पोस्ट · वेरिफ़ाइड लोग | వెరిఫైడ్ వారి పోస్ట్‌లు మాత్రమే · వెరిఫైడ్ వారు | फक्त व्हेरिफाइड लोकांच्या पोस्ट · व्हेरिफाइड लोक | ವೆರಿಫೈಡ್ ಜನರ ಪೋಸ್ಟ್‌ಗಳು ಮಾತ್ರ · ವೆರಿಫೈಡ್ ಜನರು |
| Community word | community | समाज (as in "खत्री समाज") | సంఘం | समाज (as in "खत्री समाज") | ಸಮಾಜ (as in "ಖತ್ರಿ ಸಮಾಜ") |

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
   Marathi and Kannada do the same (नोकरी, पगार, स्किल, व्हेरिफाइड, मेसेज, प्रोफाइल; ಉದ್ಯೋಗ,
   ಸಂಬಳ, ಕೌಶಲ್ಯ, ವೆರಿಫೈಡ್, ಮೆಸೇಜ್, ಪ್ರೊಫೈಲ್), and a new concept is added in all five languages.
4. Admin and operator screens use the same words. Only placeholders such as `{poster}` or
   `{listing}` keep their storage names.
5. Respectful register in every language: Hindi आप, Telugu మీరు, Marathi तुम्ही (आपण only where
   Hindi uses a formal honorific for an elder), Kannada ನೀವು. Never तू, నువ్వు or ನೀನು.

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
- Marathi and Kannada everyday words: Marathi पगार, नोकरी, करार, आगाऊ and Kannada ಸಂಬಳ, ಉದ್ಯೋಗ,
  ಒಪ್ಪಂದ, ಮುಂಗಡ are the words used in Maharashtra and Karnataka government job and rent
  notices and in regional job portals; the Bhashini and e-Shram multilingual lists above cover
  both languages.


## Account deletion terms (added 2026-11-22)
- **Erase**: remove everything Vyapar holds about a member (rows and files), keeping only the retained list.
- **Tombstone**: a one-way hash of the member id (member row del_<hash>) that replaces the member in rows that must stay, shown as "Deleted member"; it cannot be turned back into a person.
- **Deletion receipt**: a one-line record (tombstone, date, counts) proving deletion was done.
- **Kind A**: deleting the whole ForKhatri account from the hub; all modules erase. **Kind B**: deleting only one module's data from that module's settings; the ForKhatri identity stays.
- **Retained**: only what law or other people's safety requires (payment orders, safety records, audit log, receipt).
