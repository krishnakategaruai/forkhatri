/**
 * Interface text in English, Hindi and Telugu (TR21, ADR-010).
 * `hi` and `te` are typed against `en`, so a missing key fails type-checking
 * and a raw key can never reach the screen.
 */
import type { Lang } from "./api";

const en = {
  skipToContent: "Skip to content",
  loadingLabel: "Loading ForKhatri",
  retry: "Try again",
  close: "Close",
  cancel: "Cancel",
  save: "Save",
  edit: "Edit",
  change: "Change",
  back: "Back",

  // Arrival
  arrivalKicker: "Welcome to ForKhatri",
  arrivalPromise: "Your community. Your opportunities. Your support. Your growth.",
  askIdentifier: "Let's begin. What's your mobile number or email?",
  identifierLabel: "Mobile number or email",
  identifierPlaceholder: "Mobile number or email",
  continueIn: "Continue in {module}",
  identifierInvalid: "Enter a 10-digit Indian mobile number or an email address.",
  privacyNumber: "Your number is never shown to other members.",
  sendCode: "Send code",
  sending: "Sending…",
  askCode: "Enter the 6-digit code sent to {destination}",
  codeLabel: "6-digit code",
  resendIn: "New code in {seconds}s",
  resendCode: "Send a new code",
  codeResent: "A new code is on its way.",
  devCode: "Development code",
  devCodeFill: "Fill",
  verifying: "Checking…",
  askName: "Welcome to the community. What should we call you?",
  nameLabel: "Your name",
  namePlaceholder: "The name members will see",
  languageLabel: "Language",
  appearanceLabel: "Appearance",
  themeSystem: "System",
  themeLight: "Light",
  themeDark: "Dark",
  finish: "Enter ForKhatri",
  usePassword: "Use a password instead",
  useCode: "Use a one-time code instead",
  askPassword: "Enter your password",
  passwordLabel: "Password",
  showPassword: "Show password",
  hidePassword: "Hide password",
  signIn: "Sign in",
  continueTo: "Sign in to continue to {module}",
  stepAnnounce: "Step changed: {question}",

  // Errors (by detail.code)
  err_invalid_identifier: "That doesn't look like a mobile number or email. Please check it.",
  err_rate_limited: "Too many attempts. Please try again in {time}.",
  err_rate_limited_generic: "Too many attempts. Please wait a little and try again.",
  err_code_invalid: "That code isn't right. Please check and try again.",
  err_code_expired: "That code has expired. Let's send you a new one.",
  err_code_attempts_exhausted: "Too many tries for this code. Please request a new one.",
  err_invalid_credentials: "That number, email or password doesn't match. Please try again.",
  err_not_signed_in: "Your session has ended. Please sign in again.",
  err_module_unavailable: "This module isn't open yet.",
  err_module_unknown: "We couldn't find that module.",
  err_validation_failed: "Something in that entry needs a second look.",
  err_origin_not_allowed: "This request came from a page we don't recognise, so we stopped it.",
  err_delivery_unavailable: "We can't send a sign-in code there right now. Please use your password, or sign in with your email address.",
  err_network: "We can't reach ForKhatri right now. Check your connection and try again.",
  err_unknown: "Something went wrong on our side. Please try again.",
  minutes: "{n} min",
  seconds: "{n} sec",

  // Hub
  greetMorning: "Good morning, {name}",
  greetAfternoon: "Good afternoon, {name}",
  greetEvening: "Good evening, {name}",
  hubSubtitle: "One community, many ways to grow. Where to today?",
  portalsLabel: "Your ForKhatri modules",
  sectionOpen: "Open now",
  comingTitle: "Coming to ForKhatri",
  deityName: "Bhagwan Kartavirya Sahasrarjun",
  enterModule: "Enter",
  continueModule: "Continue",
  lastVisited: "Visited {when}",
  statusInDevelopment: "Being built",
  statusPlanned: "Planned",
  notOpenYet: "Not open yet",
  entering: "Entering {module}",
  enterFailed: "We couldn't open {module}. Please try again.",
  cachedNotice: "Showing modules from your last visit. They'll open again once we reconnect.",
  askPrompt: "What would you like to do?",
  trustLine: "One ForKhatri account for every module. Private by default.",

  // Intent orb
  clearInput: "Clear",
  intentNotOpenDev: "{module} isn't open yet. It's being built.",
  intentNotOpenPlanned: "{module} isn't open yet. It's planned for later.",
  intentNoMatch: "Not sure yet. Try words like “yoga”, “plumber” or “rishta”.",
  intentAmbiguous: "This could fit more than one place.",
  intentTry: "Try",
  voiceStart: "Speak instead",
  voiceStop: "Stop listening",
  listening: "Listening…",
  voiceError: "Voice input didn't work. You can type instead.",
  suggestActivity: "Yoga this weekend near me",
  suggestMatch: "Family introduction for a rishta",
  suggestService: "Hire a trusted electrician",
  kind_activity: "activity",
  kind_matrimony: "matrimony",
  kind_business: "business",
  kind_service: "service",
  kind_opportunity: "opportunity",
  kind_advice: "advice",
  kind_payment: "payment",
  kind_loan: "loan",
  time_today: "today",
  time_tonight: "tonight",
  time_tomorrow: "tomorrow",
  time_weekend: "this weekend",
  place_near: "near you",
  place_in: "in {place}",

  // Header and sheets
  notifications: "Notifications",
  account: "Account",
  openAccount: "Account for {name}",
  notificationsEmptyTitle: "You're all caught up",
  notificationsEmptyBody: "Updates from your modules will appear here.",
  accountTitle: "Your account",
  nameField: "Name",
  moduleDetailsNote: "Your details in each module, like your matrimonial profile or activity location, are managed inside that module.",
  notSet: "Not set",
  phoneHint: "Mobile",
  emailHint: "Email",
  privacyQuiet: "Your number and email are never shown to other members.",
  saved: "Saved",
  saving: "Saving…",
  saveFailed: "Couldn't save. Please try again.",
  signOut: "Sign out",
  signOutEverywhere: "Sign out on all devices",
  signOutEverywhereConfirm: "This signs you out on every phone and computer.",
  signOutEverywhereYes: "Sign out everywhere",
  signedOut: "You've signed out. See you soon.",

  // Offline
  offlineTitle: "We can't reach ForKhatri right now",
  offlineBody: "Your account is safe. This is usually a brief connection hiccup.",
  offlineRetrying: "Trying again…",
  offlineCached: "From your last visit",
};

export type MessageKey = keyof typeof en;
type Dictionary = Record<MessageKey, string>;

const hi: Dictionary = {
  skipToContent: "मुख्य सामग्री पर जाएँ",
  loadingLabel: "ForKhatri लोड हो रहा है",
  retry: "फिर कोशिश करें",
  close: "बंद करें",
  cancel: "रद्द करें",
  save: "सहेजें",
  edit: "बदलें",
  change: "बदलें",
  back: "वापस",

  arrivalKicker: "ForKhatri में आपका स्वागत है",
  arrivalPromise: "आपका समुदाय। आपके अवसर। आपका साथ। आपकी प्रगति।",
  askIdentifier: "चलिए शुरू करें। आपका मोबाइल नंबर या ईमेल क्या है?",
  identifierLabel: "मोबाइल नंबर या ईमेल",
  identifierPlaceholder: "मोबाइल नंबर या ईमेल",
  continueIn: "{module} में जारी रखें",
  identifierInvalid: "10 अंकों का भारतीय मोबाइल नंबर या ईमेल पता दर्ज करें।",
  privacyNumber: "आपका नंबर कभी भी दूसरे सदस्यों को नहीं दिखाया जाता।",
  sendCode: "कोड भेजें",
  sending: "भेजा जा रहा है…",
  askCode: "{destination} पर भेजा गया 6 अंकों का कोड दर्ज करें",
  codeLabel: "6 अंकों का कोड",
  resendIn: "नया कोड {seconds} सेकंड में",
  resendCode: "नया कोड भेजें",
  codeResent: "नया कोड भेजा जा रहा है।",
  devCode: "डेवलपमेंट कोड",
  devCodeFill: "भरें",
  verifying: "जाँच हो रही है…",
  askName: "समुदाय में स्वागत है। हम आपको किस नाम से बुलाएँ?",
  nameLabel: "आपका नाम",
  namePlaceholder: "जो नाम सदस्य देखेंगे",
  languageLabel: "भाषा",
  appearanceLabel: "रूप-रंग",
  themeSystem: "सिस्टम",
  themeLight: "लाइट",
  themeDark: "डार्क",
  finish: "ForKhatri में प्रवेश करें",
  usePassword: "पासवर्ड से साइन इन करें",
  useCode: "एक-बार वाले कोड से साइन इन करें",
  askPassword: "अपना पासवर्ड दर्ज करें",
  passwordLabel: "पासवर्ड",
  showPassword: "पासवर्ड दिखाएँ",
  hidePassword: "पासवर्ड छिपाएँ",
  signIn: "साइन इन करें",
  continueTo: "{module} पर जारी रखने के लिए साइन इन करें",
  stepAnnounce: "अगला चरण: {question}",

  err_invalid_identifier: "यह मोबाइल नंबर या ईमेल जैसा नहीं लगता। कृपया जाँच लें।",
  err_rate_limited: "बहुत अधिक प्रयास। कृपया {time} बाद फिर कोशिश करें।",
  err_rate_limited_generic: "बहुत अधिक प्रयास। कृपया थोड़ा रुककर फिर कोशिश करें।",
  err_code_invalid: "यह कोड सही नहीं है। कृपया जाँचकर फिर कोशिश करें।",
  err_code_expired: "इस कोड की समय-सीमा खत्म हो गई। नया कोड भेजते हैं।",
  err_code_attempts_exhausted: "इस कोड के लिए बहुत प्रयास हो गए। कृपया नया कोड मँगाएँ।",
  err_invalid_credentials: "नंबर, ईमेल या पासवर्ड मेल नहीं खाता। कृपया फिर कोशिश करें।",
  err_not_signed_in: "आपका सत्र समाप्त हो गया। कृपया फिर से साइन इन करें।",
  err_module_unavailable: "यह मॉड्यूल अभी खुला नहीं है।",
  err_module_unknown: "यह मॉड्यूल नहीं मिला।",
  err_validation_failed: "इस जानकारी में कुछ दोबारा देखने की ज़रूरत है।",
  err_origin_not_allowed: "यह अनुरोध किसी अनजान पेज से आया, इसलिए रोक दिया गया।",
  err_delivery_unavailable: "अभी वहाँ साइन-इन कोड नहीं भेज पा रहे। कृपया अपना पासवर्ड इस्तेमाल करें, या अपने ईमेल से साइन इन करें।",
  err_network: "अभी ForKhatri से जुड़ नहीं पा रहे। कनेक्शन जाँचकर फिर कोशिश करें।",
  err_unknown: "हमारी ओर से कुछ गड़बड़ हुई। कृपया फिर कोशिश करें।",
  minutes: "{n} मिनट",
  seconds: "{n} सेकंड",

  greetMorning: "सुप्रभात, {name}",
  greetAfternoon: "नमस्ते, {name}",
  greetEvening: "शुभ संध्या, {name}",
  hubSubtitle: "एक समुदाय, आगे बढ़ने के कई रास्ते। आज कहाँ चलें?",
  portalsLabel: "आपके ForKhatri मॉड्यूल",
  sectionOpen: "अभी खुले",
  comingTitle: "ForKhatri पर जल्द आ रहे",
  deityName: "भगवान कार्तवीर्य सहस्रार्जुन",
  enterModule: "प्रवेश करें",
  continueModule: "जारी रखें",
  lastVisited: "{when} देखा",
  statusInDevelopment: "बन रहा है",
  statusPlanned: "योजना में",
  notOpenYet: "अभी खुला नहीं",
  entering: "{module} में प्रवेश",
  enterFailed: "{module} नहीं खुल सका। कृपया फिर कोशिश करें।",
  cachedNotice: "पिछली बार के मॉड्यूल दिखाए जा रहे हैं। दोबारा जुड़ते ही ये खुल जाएँगे।",
  askPrompt: "आप क्या करना चाहेंगे?",
  trustLine: "हर मॉड्यूल के लिए एक ForKhatri खाता। निजता पहले से।",

  clearInput: "मिटाएँ",
  intentNotOpenDev: "{module} अभी खुला नहीं है। यह बन रहा है।",
  intentNotOpenPlanned: "{module} अभी खुला नहीं है। यह आगे की योजना में है।",
  intentNoMatch: "अभी पक्का नहीं। “योग”, “प्लंबर” या “रिश्ता” जैसे शब्द आज़माएँ।",
  intentAmbiguous: "यह एक से ज़्यादा जगह पर फिट हो सकता है।",
  intentTry: "आज़माएँ",
  voiceStart: "बोलकर बताएँ",
  voiceStop: "सुनना बंद करें",
  listening: "सुन रहे हैं…",
  voiceError: "आवाज़ से इनपुट नहीं हो सका। आप लिख सकते हैं।",
  suggestActivity: "इस वीकेंड पास में योग",
  suggestMatch: "रिश्ते के लिए पारिवारिक परिचय",
  suggestService: "भरोसेमंद इलेक्ट्रीशियन चाहिए",
  kind_activity: "गतिविधि",
  kind_matrimony: "वैवाहिक",
  kind_business: "व्यवसाय",
  kind_service: "सेवा",
  kind_opportunity: "अवसर",
  kind_advice: "सलाह",
  kind_payment: "भुगतान",
  kind_loan: "ऋण",
  time_today: "आज",
  time_tonight: "आज रात",
  time_tomorrow: "कल",
  time_weekend: "इस वीकेंड",
  place_near: "आपके पास",
  place_in: "{place} में",

  notifications: "सूचनाएँ",
  account: "खाता",
  openAccount: "{name} का खाता",
  notificationsEmptyTitle: "सब देख लिया",
  notificationsEmptyBody: "आपके मॉड्यूल की नई जानकारी यहाँ दिखेगी।",
  accountTitle: "आपका खाता",
  nameField: "नाम",
  moduleDetailsNote: "हर मॉड्यूल की आपकी जानकारी, जैसे वैवाहिक प्रोफ़ाइल या गतिविधि का स्थान, उसी मॉड्यूल के अंदर संभाली जाती है।",
  notSet: "जोड़ा नहीं गया",
  phoneHint: "मोबाइल",
  emailHint: "ईमेल",
  privacyQuiet: "आपका नंबर और ईमेल कभी भी दूसरे सदस्यों को नहीं दिखाए जाते।",
  saved: "सहेजा गया",
  saving: "सहेजा जा रहा है…",
  saveFailed: "सहेजा नहीं जा सका। कृपया फिर कोशिश करें।",
  signOut: "साइन आउट करें",
  signOutEverywhere: "सभी डिवाइस से साइन आउट करें",
  signOutEverywhereConfirm: "इससे आप हर फ़ोन और कंप्यूटर से साइन आउट हो जाएँगे।",
  signOutEverywhereYes: "हर जगह से साइन आउट करें",
  signedOut: "आप साइन आउट हो गए। फिर मिलेंगे।",

  offlineTitle: "अभी ForKhatri से जुड़ नहीं पा रहे",
  offlineBody: "आपका खाता सुरक्षित है। यह अक्सर कनेक्शन की छोटी-सी रुकावट होती है।",
  offlineRetrying: "फिर कोशिश हो रही है…",
  offlineCached: "आपकी पिछली विज़िट से",
};

const te: Dictionary = {
  skipToContent: "ప్రధాన విషయానికి వెళ్ళండి",
  loadingLabel: "ForKhatri లోడ్ అవుతోంది",
  retry: "మళ్ళీ ప్రయత్నించండి",
  close: "మూసివేయండి",
  cancel: "రద్దు చేయండి",
  save: "సేవ్ చేయండి",
  edit: "మార్చండి",
  change: "మార్చండి",
  back: "వెనక్కి",

  arrivalKicker: "ForKhatri కి స్వాగతం",
  arrivalPromise: "మీ సమాజం. మీ అవకాశాలు. మీ తోడు. మీ ఎదుగుదల.",
  askIdentifier: "మొదలుపెడదాం. మీ మొబైల్ నంబర్ లేదా ఈమెయిల్ ఏమిటి?",
  identifierLabel: "మొబైల్ నంబర్ లేదా ఈమెయిల్",
  identifierPlaceholder: "మొబైల్ నంబర్ లేదా ఈమెయిల్",
  continueIn: "{module} లో కొనసాగించండి",
  identifierInvalid: "10 అంకెల భారతీయ మొబైల్ నంబర్ లేదా ఈమెయిల్ ఇవ్వండి.",
  privacyNumber: "మీ నంబర్ ఇతర సభ్యులకు ఎప్పుడూ కనిపించదు.",
  sendCode: "కోడ్ పంపండి",
  sending: "పంపుతోంది…",
  askCode: "{destination} కి పంపిన 6 అంకెల కోడ్ ఇవ్వండి",
  codeLabel: "6 అంకెల కోడ్",
  resendIn: "{seconds} సె. లో కొత్త కోడ్",
  resendCode: "కొత్త కోడ్ పంపండి",
  codeResent: "కొత్త కోడ్ వస్తోంది.",
  devCode: "డెవలప్‌మెంట్ కోడ్",
  devCodeFill: "నింపండి",
  verifying: "తనిఖీ చేస్తోంది…",
  askName: "సమాజానికి స్వాగతం. మిమ్మల్ని ఏ పేరుతో పిలవాలి?",
  nameLabel: "మీ పేరు",
  namePlaceholder: "సభ్యులు చూసే పేరు",
  languageLabel: "భాష",
  appearanceLabel: "రూపం",
  themeSystem: "సిస్టమ్",
  themeLight: "లైట్",
  themeDark: "డార్క్",
  finish: "ForKhatri లోకి ప్రవేశించండి",
  usePassword: "పాస్‌వర్డ్‌తో సైన్ ఇన్ చేయండి",
  useCode: "ఒకసారి కోడ్‌తో సైన్ ఇన్ చేయండి",
  askPassword: "మీ పాస్‌వర్డ్ ఇవ్వండి",
  passwordLabel: "పాస్‌వర్డ్",
  showPassword: "పాస్‌వర్డ్ చూపించండి",
  hidePassword: "పాస్‌వర్డ్ దాచండి",
  signIn: "సైన్ ఇన్ చేయండి",
  continueTo: "{module} కొనసాగించడానికి సైన్ ఇన్ చేయండి",
  stepAnnounce: "తదుపరి దశ: {question}",

  err_invalid_identifier: "ఇది మొబైల్ నంబర్ లేదా ఈమెయిల్ లాగా లేదు. దయచేసి సరిచూడండి.",
  err_rate_limited: "చాలా ప్రయత్నాలు జరిగాయి. {time} తర్వాత మళ్ళీ ప్రయత్నించండి.",
  err_rate_limited_generic: "చాలా ప్రయత్నాలు జరిగాయి. కొంచెం ఆగి మళ్ళీ ప్రయత్నించండి.",
  err_code_invalid: "ఈ కోడ్ సరైనది కాదు. సరిచూసి మళ్ళీ ప్రయత్నించండి.",
  err_code_expired: "ఈ కోడ్ గడువు ముగిసింది. కొత్త కోడ్ పంపుదాం.",
  err_code_attempts_exhausted: "ఈ కోడ్‌కు చాలా ప్రయత్నాలు జరిగాయి. కొత్త కోడ్ అడగండి.",
  err_invalid_credentials: "నంబర్, ఈమెయిల్ లేదా పాస్‌వర్డ్ సరిపోలలేదు. మళ్ళీ ప్రయత్నించండి.",
  err_not_signed_in: "మీ సెషన్ ముగిసింది. దయచేసి మళ్ళీ సైన్ ఇన్ చేయండి.",
  err_module_unavailable: "ఈ మాడ్యూల్ ఇంకా తెరవబడలేదు.",
  err_module_unknown: "ఆ మాడ్యూల్ కనబడలేదు.",
  err_validation_failed: "ఇచ్చిన వివరాల్లో ఒకటి మళ్ళీ చూడాలి.",
  err_origin_not_allowed: "ఈ అభ్యర్థన తెలియని పేజీ నుంచి వచ్చింది, కాబట్టి ఆపేశాం.",
  err_delivery_unavailable: "ప్రస్తుతం అక్కడికి సైన్-ఇన్ కోడ్ పంపలేకపోతున్నాం. దయచేసి మీ పాస్‌వర్డ్ వాడండి, లేదా మీ ఈమెయిల్‌తో సైన్ ఇన్ చేయండి.",
  err_network: "ప్రస్తుతం ForKhatri ని చేరుకోలేకపోతున్నాం. కనెక్షన్ చూసి మళ్ళీ ప్రయత్నించండి.",
  err_unknown: "మా వైపు ఏదో పొరపాటు జరిగింది. మళ్ళీ ప్రయత్నించండి.",
  minutes: "{n} నిమిషాలు",
  seconds: "{n} సెకన్లు",

  greetMorning: "శుభోదయం, {name}",
  greetAfternoon: "నమస్కారం, {name}",
  greetEvening: "శుభ సాయంత్రం, {name}",
  hubSubtitle: "ఒకే సమాజం, ఎదగడానికి ఎన్నో దారులు. ఈ రోజు ఎక్కడికి?",
  portalsLabel: "మీ ForKhatri మాడ్యూల్స్",
  sectionOpen: "ఇప్పుడు తెరిచి ఉన్నవి",
  comingTitle: "ForKhatri లో త్వరలో",
  deityName: "భగవాన్ కార్తవీర్య సహస్రార్జున",
  enterModule: "ప్రవేశించండి",
  continueModule: "కొనసాగించండి",
  lastVisited: "{when} చూశారు",
  statusInDevelopment: "తయారవుతోంది",
  statusPlanned: "ప్రణాళికలో ఉంది",
  notOpenYet: "ఇంకా తెరవలేదు",
  entering: "{module} లోకి ప్రవేశిస్తోంది",
  enterFailed: "{module} తెరవలేకపోయాం. మళ్ళీ ప్రయత్నించండి.",
  cachedNotice: "మీ గత సందర్శన నాటి మాడ్యూల్స్ చూపిస్తున్నాం. మళ్ళీ కనెక్ట్ అయ్యాక తెరుచుకుంటాయి.",
  askPrompt: "మీరు ఏమి చేయాలనుకుంటున్నారు?",
  trustLine: "ప్రతి మాడ్యూల్‌కు ఒకే ForKhatri ఖాతా. గోప్యత మొదటి నుంచే.",

  clearInput: "తొలగించండి",
  intentNotOpenDev: "{module} ఇంకా తెరవలేదు. ఇది తయారవుతోంది.",
  intentNotOpenPlanned: "{module} ఇంకా తెరవలేదు. ఇది తర్వాతి ప్రణాళికలో ఉంది.",
  intentNoMatch: "ఇంకా స్పష్టంగా లేదు. “యోగా”, “ప్లంబర్” లేదా “సంబంధం” వంటి పదాలు ప్రయత్నించండి.",
  intentAmbiguous: "ఇది ఒకటి కంటే ఎక్కువ చోట్లకు సరిపోవచ్చు.",
  intentTry: "ప్రయత్నించండి",
  voiceStart: "మాట్లాడి చెప్పండి",
  voiceStop: "వినడం ఆపండి",
  listening: "వింటోంది…",
  voiceError: "వాయిస్ ఇన్‌పుట్ పని చేయలేదు. మీరు టైప్ చేయవచ్చు.",
  suggestActivity: "ఈ వారాంతం దగ్గరలో యోగా",
  suggestMatch: "సంబంధం కోసం కుటుంబ పరిచయం",
  suggestService: "నమ్మకమైన ఎలక్ట్రీషియన్ కావాలి",
  kind_activity: "కార్యక్రమం",
  kind_matrimony: "వివాహ సంబంధం",
  kind_business: "వ్యాపారం",
  kind_service: "సేవ",
  kind_opportunity: "అవకాశం",
  kind_advice: "సలహా",
  kind_payment: "చెల్లింపు",
  kind_loan: "రుణం",
  time_today: "ఈ రోజు",
  time_tonight: "ఈ రాత్రి",
  time_tomorrow: "రేపు",
  time_weekend: "ఈ వారాంతం",
  place_near: "మీ దగ్గరలో",
  place_in: "{place} లో",

  notifications: "నోటిఫికేషన్లు",
  account: "ఖాతా",
  openAccount: "{name} ఖాతా",
  notificationsEmptyTitle: "అన్నీ చూసేశారు",
  notificationsEmptyBody: "మీ మాడ్యూల్స్ నుంచి వచ్చే కొత్త సమాచారం ఇక్కడ కనిపిస్తుంది.",
  accountTitle: "మీ ఖాతా",
  nameField: "పేరు",
  moduleDetailsNote: "ప్రతి మాడ్యూల్‌లోని మీ వివరాలు, ఉదా. వివాహ ప్రొఫైల్ లేదా కార్యక్రమ ప్రాంతం, ఆ మాడ్యూల్‌లోనే నిర్వహించబడతాయి.",
  notSet: "ఇవ్వలేదు",
  phoneHint: "మొబైల్",
  emailHint: "ఈమెయిల్",
  privacyQuiet: "మీ నంబర్, ఈమెయిల్ ఇతర సభ్యులకు ఎప్పుడూ కనిపించవు.",
  saved: "సేవ్ అయింది",
  saving: "సేవ్ చేస్తోంది…",
  saveFailed: "సేవ్ కాలేదు. మళ్ళీ ప్రయత్నించండి.",
  signOut: "సైన్ అవుట్",
  signOutEverywhere: "అన్ని పరికరాల నుంచి సైన్ అవుట్",
  signOutEverywhereConfirm: "దీనితో ప్రతి ఫోన్, కంప్యూటర్ నుంచి సైన్ అవుట్ అవుతారు.",
  signOutEverywhereYes: "అన్ని చోట్ల సైన్ అవుట్",
  signedOut: "మీరు సైన్ అవుట్ అయ్యారు. మళ్ళీ కలుద్దాం.",

  offlineTitle: "ప్రస్తుతం ForKhatri ని చేరుకోలేకపోతున్నాం",
  offlineBody: "మీ ఖాతా సురక్షితంగా ఉంది. ఇది సాధారణంగా చిన్న కనెక్షన్ అంతరాయం మాత్రమే.",
  offlineRetrying: "మళ్ళీ ప్రయత్నిస్తోంది…",
  offlineCached: "మీ గత సందర్శన నుంచి",
};

const dictionaries: Record<Lang, Dictionary> = { en, hi, te };

export const LANGUAGES: { code: Lang; native: string }[] = [
  { code: "en", native: "English" },
  { code: "hi", native: "हिन्दी" },
  { code: "te", native: "తెలుగు" },
];

export type Translate = (key: MessageKey, vars?: Record<string, string | number>) => string;

export function translator(lang: Lang): Translate {
  const dictionary = dictionaries[lang] ?? en;
  return (key, vars) => {
    const template = dictionary[key] ?? en[key];
    if (!vars) return template;
    return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match));
  };
}

export function langFromNavigator(): Lang {
  if (typeof navigator === "undefined") return "en";
  for (const candidate of navigator.languages ?? [navigator.language]) {
    const base = candidate.toLowerCase().split("-")[0];
    if (base === "hi" || base === "te" || base === "en") return base;
  }
  return "en";
}

/** Maps a service error code to localized text; `retryAfter` feeds rate_limited. */
export function errorText(t: Translate, code: string, retryAfter: number | null = null): string {
  switch (code) {
    case "rate_limited": {
      if (!retryAfter) return t("err_rate_limited_generic");
      const time = retryAfter >= 90 ? t("minutes", { n: Math.ceil(retryAfter / 60) }) : t("seconds", { n: retryAfter });
      return t("err_rate_limited", { time });
    }
    case "invalid_identifier":
    case "code_invalid":
    case "code_expired":
    case "code_attempts_exhausted":
    case "invalid_credentials":
    case "not_signed_in":
    case "module_unavailable":
    case "module_unknown":
    case "validation_failed":
    case "origin_not_allowed":
    case "delivery_unavailable":
    case "network":
      return t(`err_${code}` as MessageKey);
    default:
      return t("err_unknown");
  }
}

export function relativeTime(lang: Lang, iso: string): string {
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return "";
  const diffSeconds = Math.round((then - Date.now()) / 1000);
  const format = new Intl.RelativeTimeFormat(lang === "en" ? "en-IN" : `${lang}-IN`, { numeric: "auto" });
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["year", 31_536_000],
    ["month", 2_592_000],
    ["week", 604_800],
    ["day", 86_400],
    ["hour", 3_600],
    ["minute", 60],
  ];
  for (const [unit, size] of units) {
    if (Math.abs(diffSeconds) >= size) return format.format(Math.round(diffSeconds / size), unit);
  }
  return format.format(0, "minute");
}
