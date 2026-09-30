// [Voice interview 2026-09-30] DEVELOPMENT-ONLY stand-in for
// /v1/voice/interview/{next,interpret}, used by domains/voice.ts only while
// the live routes answer 404 in a development build. It plays the server's
// part, so its questions arrive already in the member's language, exactly as
// the API sends them. It is loaded lazily and never reached in production.
import type {
  VoiceDone,
  VoiceInterpretRequest,
  VoiceInterpretation,
  VoiceNextRequest,
  VoiceNextResponse,
  VoiceOption,
  VoiceQuestionKind,
} from "./domains/voice";

type Lang = "en" | "hi" | "te";
type Text = Record<Lang, string>;
const L = (en: string, hi: string, te: string): Text => ({ en, hi, te });

interface MockQ {
  field: string;
  kind: VoiceQuestionKind;
  optional?: boolean;
  label: Text;
  question: Text;
  hint?: Text;
  reprompt?: Text;
  options?: { value: string; label: Text }[];
  unit?: "month" | "total";
}

const SHIFT = [
  { value: "day", label: L("Day", "दिन", "పగలు") },
  { value: "night", label: L("Night", "रात", "రాత్రి") },
  { value: "rotational", label: L("Rotating", "बदलती शिफ्ट", "మారే షిఫ్ట్") },
  { value: "flexible", label: L("Flexible", "लचीला", "వీలును బట్టి") },
];
const EXPERIENCE = [
  { value: "0", label: L("Fresher is fine", "फ्रेशर चलेगा", "ఫ్రెషర్ సరే") },
  { value: "12", label: L("1 year", "1 साल", "1 సంవత్సరం") },
  { value: "24", label: L("2 years or more", "2 साल या ज़्यादा", "2 సంవత్సరాలు లేదా ఎక్కువ") },
];
const DURATION = [
  { value: "under_1_week", label: L("Less than a week", "एक हफ़्ते से कम", "వారం లోపు") },
  { value: "1_4_weeks", label: L("1 to 4 weeks", "1 से 4 हफ़्ते", "1 నుండి 4 వారాలు") },
  { value: "1_3_months", label: L("1 to 3 months", "1 से 3 महीने", "1 నుండి 3 నెలలు") },
  { value: "ongoing", label: L("Ongoing", "लगातार", "కొనసాగుతుంది") },
];
const LEVEL = [
  { value: "entry", label: L("Beginner", "शुरुआती", "ప్రారంభ స్థాయి") },
  { value: "intermediate", label: L("Some experience", "थोड़ा अनुभव", "కొంత అనుభవం") },
  { value: "expert", label: L("Expert", "विशेषज्ञ", "నిపుణులు") },
];
const URGENCY = [
  { value: "today", label: L("Today", "आज", "ఈ రోజు") },
  { value: "this_week", label: L("This week", "इस हफ़्ते", "ఈ వారం") },
  { value: "flexible", label: L("Any time", "कभी भी", "ఎప్పుడైనా") },
];
const MODE = [
  { value: "on_site", label: L("I go to the customer", "मैं ग्राहक के पास जाता हूँ", "నేను కస్టమర్ దగ్గరికి వెళ్తాను") },
  { value: "remote", label: L("From my place or online", "अपनी जगह से या ऑनलाइन", "నా చోటు నుండి లేదా ఆన్‌లైన్") },
  { value: "both", label: L("Both", "दोनों", "రెండూ") },
];

const WHERE = L("Where is the work? Say the area.", "काम कहाँ है? इलाके का नाम बताइए।", "పని ఎక్కడ? ప్రాంతం పేరు చెప్పండి.");
const WHERE_HINT = L("For example: Madhapur, Hyderabad", "जैसे: माधापुर, हैदराबाद", "ఉదాహరణ: మాదాపూర్, హైదరాబాద్");

const FLOWS: Record<VoiceNextRequest["flow"], MockQ[]> = {
  post_job: [
    {
      field: "title",
      kind: "text",
      label: L("Work", "काम", "పని"),
      question: L("What work do you need someone for?", "आपको किस काम के लिए आदमी चाहिए?", "మీకు ఏ పని కోసం మనిషి కావాలి?"),
      hint: L("For example: a cook for my restaurant", "जैसे: मेरे होटल के लिए रसोइया", "ఉదాహరణ: నా హోటల్‌కి వంటమనిషి"),
    },
    { field: "location", kind: "text", label: L("Place", "जगह", "ప్రదేశం"), question: WHERE, hint: WHERE_HINT },
    {
      field: "salary",
      kind: "number",
      unit: "month",
      label: L("Pay", "तनख़्वाह", "జీతం"),
      question: L("How much will you pay in a month?", "महीने में कितनी तनख़्वाह देंगे?", "నెలకు ఎంత జీతం ఇస్తారు?"),
      hint: L("Say an amount, like 15,000", "रकम बताइए, जैसे 15,000", "మొత్తం చెప్పండి, ఉదా. 15,000"),
      reprompt: L("Please say the pay as a number, like fifteen thousand.", "कृपया तनख़्वाह अंकों में बताइए, जैसे पंद्रह हज़ार।", "దయచేసి జీతం సంఖ్యలో చెప్పండి, ఉదా. పదిహేను వేలు."),
    },
    {
      field: "openings",
      kind: "number",
      optional: true,
      label: L("People needed", "कितने लोग", "ఎంత మంది"),
      question: L("How many people do you need?", "कितने लोग चाहिए?", "ఎంత మంది కావాలి?"),
      hint: L("You can say skip", "आप 'छोड़ो' कह सकते हैं", "మీరు 'వదిలేయండి' అనవచ్చు"),
    },
    {
      field: "shift",
      kind: "choice",
      label: L("Shift", "शिफ्ट", "షిఫ్ట్"),
      question: L("Is it a day job or a night job?", "काम दिन का है या रात का?", "పని పగలా, రాత్రా?"),
      options: SHIFT,
    },
    {
      field: "experience",
      kind: "choice",
      optional: true,
      label: L("Experience", "अनुभव", "అనుభవం"),
      question: L("How much experience should they have?", "कितना अनुभव होना चाहिए?", "ఎంత అనుభవం ఉండాలి?"),
      options: EXPERIENCE,
    },
  ],
  post_project: [
    {
      field: "title",
      kind: "text",
      label: L("Project", "प्रोजेक्ट", "ప్రాజెక్ట్"),
      question: L("What do you want to get done?", "आप क्या काम करवाना चाहते हैं?", "మీరు ఏ పని చేయించుకోవాలి?"),
      hint: L("For example: a logo for my shop", "जैसे: मेरी दुकान का लोगो", "ఉదాహరణ: నా షాప్‌కి లోగో"),
    },
    {
      field: "description",
      kind: "text",
      label: L("Details", "विवरण", "వివరాలు"),
      question: L("Tell me a little more about it.", "इसके बारे में थोड़ा और बताइए।", "దాని గురించి ఇంకొంచెం చెప్పండి."),
    },
    {
      field: "budget",
      kind: "number",
      unit: "total",
      label: L("Budget", "बजट", "బడ్జెట్"),
      question: L("What is your budget for the whole work?", "पूरे काम का बजट कितना है?", "మొత్తం పనికి బడ్జెట్ ఎంత?"),
      reprompt: L("Please say the budget as a number.", "कृपया बजट अंकों में बताइए।", "దయచేసి బడ్జెట్ సంఖ్యలో చెప్పండి."),
    },
    {
      field: "duration",
      kind: "choice",
      label: L("How long", "कितना समय", "ఎంత కాలం"),
      question: L("How long will the work take?", "काम में कितना समय लगेगा?", "పనికి ఎంత సమయం పడుతుంది?"),
      options: DURATION,
    },
    {
      field: "experience_level",
      kind: "choice",
      optional: true,
      label: L("Level", "स्तर", "స్థాయి"),
      question: L("What level of person do you want?", "किस स्तर का व्यक्ति चाहिए?", "ఏ స్థాయి వ్యక్తి కావాలి?"),
      options: LEVEL,
    },
  ],
  post_local: [
    {
      field: "title",
      kind: "text",
      label: L("Service", "सेवा", "సేవ"),
      question: L("What do you need done at home or shop?", "घर या दुकान पर क्या काम करवाना है?", "ఇంట్లో లేదా షాప్‌లో ఏ పని కావాలి?"),
      hint: L("For example: fix a leaking tap", "जैसे: टपकता नल ठीक करना", "ఉదాహరణ: కారుతున్న నల్లా బాగు చేయడం"),
    },
    { field: "location", kind: "text", label: L("Place", "जगह", "ప్రదేశం"), question: WHERE, hint: WHERE_HINT },
    {
      field: "urgency",
      kind: "choice",
      label: L("When", "कब", "ఎప్పుడు"),
      question: L("When do you need it?", "यह कब चाहिए?", "ఇది ఎప్పుడు కావాలి?"),
      options: URGENCY,
    },
    {
      field: "budget",
      kind: "number",
      optional: true,
      unit: "total",
      label: L("Pay", "भुगतान", "చెల్లింపు"),
      question: L("How much will you pay for it?", "इसके लिए कितना देंगे?", "దీనికి ఎంత ఇస్తారు?"),
    },
  ],
  profile: [
    {
      field: "name",
      kind: "text",
      label: L("Name", "नाम", "పేరు"),
      question: L("What is your name?", "आपका नाम क्या है?", "మీ పేరు ఏమిటి?"),
    },
    {
      field: "work",
      kind: "text",
      label: L("Your work", "आपका काम", "మీ పని"),
      question: L("What work do you do?", "आप क्या काम करते हैं?", "మీరు ఏ పని చేస్తారు?"),
      hint: L("For example: electrician, AC repair", "जैसे: इलेक्ट्रीशियन, एसी रिपेयर", "ఉదాహరణ: ఎలక్ట్రీషియన్, ఏసీ రిపేర్"),
    },
    {
      field: "locality",
      kind: "text",
      label: L("Area", "इलाका", "ప్రాంతం"),
      question: L("Which area do you live or work in?", "आप किस इलाके में रहते या काम करते हैं?", "మీరు ఏ ప్రాంతంలో ఉంటారు లేదా పని చేస్తారు?"),
      hint: WHERE_HINT,
    },
    {
      field: "service_mode",
      kind: "choice",
      label: L("How you work", "कैसे काम करते हैं", "ఎలా పని చేస్తారు"),
      question: L("Do you go to the customer, or work from your place?", "आप ग्राहक के पास जाते हैं या अपनी जगह से काम करते हैं?", "మీరు కస్టమర్ దగ్గరికి వెళ్తారా, లేక మీ చోటు నుండి పని చేస్తారా?"),
      options: MODE,
    },
    {
      field: "headline",
      kind: "text",
      optional: true,
      label: L("About you", "आपके बारे में", "మీ గురించి"),
      question: L("In one line, why should people choose you?", "एक लाइन में, लोग आपको क्यों चुनें?", "ఒక్క మాటలో, ప్రజలు మిమ్మల్ని ఎందుకు ఎంచుకోవాలి?"),
      hint: L("You can say skip", "आप 'छोड़ो' कह सकते हैं", "మీరు 'వదిలేయండి' అనవచ్చు"),
    },
  ],
};

const lang = (l: string): Lang => (l === "hi" || l === "te" ? l : "en");
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function optionsOf(q: MockQ, l: Lang): VoiceOption[] | null {
  return q.options ? q.options.map((o) => ({ value: o.value, label: o.label[l] })) : null;
}

function money(n: number): string {
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

function valueLabel(q: MockQ, v: unknown, l: Lang): string {
  if (q.kind === "choice") return q.options?.find((o) => o.value === String(v))?.label[l] ?? String(v);
  if (q.kind === "yesno") return v ? L("Yes", "हाँ", "అవును")[l] : L("No", "नहीं", "కాదు")[l];
  if (q.kind === "number" && typeof v === "number") {
    if (q.unit === "month") return `${money(v)} ${L("a month", "महीना", "నెలకు")[l]}`;
    if (q.unit === "total") return money(v);
    return String(v);
  }
  return String(v ?? "");
}

export async function mockNext(b: VoiceNextRequest): Promise<VoiceNextResponse> {
  await sleep(250);
  const l = lang(b.language);
  const qs = FLOWS[b.flow];
  const pending = qs.find((q) => !(q.field in b.answers) && !b.skipped.includes(q.field));
  const asked = qs.filter((q) => q.field in b.answers || b.skipped.includes(q.field)).length;
  if (pending) {
    return {
      done: false,
      field: pending.field,
      question: pending.question[l],
      hint: pending.hint?.[l] ?? null,
      kind: pending.kind,
      options: optionsOf(pending, l),
      optional: !!pending.optional,
      progress: { asked: asked + 1, total: qs.length },
    };
  }
  const summary = qs
    .filter((q) => q.field in b.answers)
    .map((q) => ({ field: q.field, label: q.label[l], value_label: valueLabel(q, b.answers[q.field], l) }));
  return { done: true, summary, draft: buildDraft(b) };
}

function buildDraft(b: VoiceNextRequest): VoiceDone["draft"] {
  const a = b.answers;
  const str = (k: string) => (typeof a[k] === "string" ? (a[k] as string) : null);
  const num = (k: string) => (typeof a[k] === "number" ? (a[k] as number) : null);
  if (b.flow === "profile") {
    return {
      name: str("name"),
      capabilities: [],
      capabilities_other: str("work"),
      locality: str("locality"),
      service_mode: str("service_mode"),
      headline: str("headline"),
    };
  }
  const base = {
    title: str("title"),
    description: str("description") ?? str("title"),
    location: str("location"),
    work_mode: null,
    timing: null,
    required_capabilities: [] as string[],
    capability_labels: [] as string[],
    employment: null as unknown,
    freelance: null as unknown,
    local_service: null as unknown,
    confidence: {} as Record<string, number>,
    missing: [] as string[],
    questions: [] as string[],
    source: "rules",
    language: b.language,
  };
  if (b.flow === "post_job") {
    const pay = num("salary");
    const exp = str("experience");
    return {
      ...base,
      type: "employment",
      employment: {
        salary_min_paise: pay ? pay * 100 : null,
        salary_max_paise: pay ? pay * 100 : null,
        incentive_type: null,
        openings: num("openings"),
        shift: str("shift"),
        job_timings: null,
        interview_details: null,
        min_qualification: null,
        english_level: null,
        experience_min_months: exp ? Number(exp) : null,
        experience_max_months: null,
        requires_assets: [],
      },
    };
  }
  if (b.flow === "post_project") {
    const budget = num("budget");
    return {
      ...base,
      type: "freelance",
      freelance: {
        budget_type: "fixed",
        budget_min_paise: budget ? budget * 100 : null,
        budget_max_paise: budget ? budget * 100 : null,
        hourly_rate_min_paise: null,
        hourly_rate_max_paise: null,
        duration: str("duration"),
        experience_level: str("experience_level"),
        screening_questions: [],
      },
    };
  }
  const budget = num("budget");
  return {
    ...base,
    type: "local_service",
    local_service: { preferred_date: null, budget_paise: budget ? budget * 100 : null, urgency: str("urgency") },
  };
}

// ---- interpret ---------------------------------------------------------------

const WORDS = {
  repeat: ["repeat", "again", "pardon", "what did you say", "say again", "फिर से", "दोबारा", "क्या कहा", "మళ్ళీ", "మళ్లీ", "ఏమన్నారు"],
  skip: ["skip", "later", "don't know", "dont know", "no idea", "छोड़ो", "छोड़ दो", "बाद में", "पता नहीं", "వదిలేయండి", "వదిలేయ్", "తర్వాత", "తెలియదు"],
  yes: ["yes", "yeah", "yep", "right", "correct", "ok", "okay", "sure", "haan", "han", "हाँ", "हां", "सही", "ठीक", "जी", "అవును", "ఔను", "సరే", "కరెక్ట్"],
  no: ["no", "nope", "wrong", "not right", "nahi", "नहीं", "नही", "गलत", "ग़लत", "కాదు", "లేదు", "తప్పు"],
};

function norm(s: string): string {
  return s.toLowerCase().replace(/[.,!?।]/g, " ").replace(/\s+/g, " ").trim();
}
function hasWord(text: string, list: string[]): boolean {
  const t = ` ${text} `;
  return list.some((w) => t.includes(` ${w} `) || (/[^\x00-\x7f]/.test(w) && text.includes(w)));
}

/** "15000", "15,000", "15k", "15 thousand", "15 हज़ार", "15 వేలు", "1.5 lakh". */
function parseAmount(text: string): number | null {
  const m = text.replace(/,/g, "").match(/(\d+(?:\.\d+)?)\s*(k|thousand|हज़ार|हजार|వేలు|వేల|lakh|lac|लाख|లక్ష|లక్షలు)?/);
  if (!m) return null;
  let n = parseFloat(m[1]);
  const unit = m[2] ?? "";
  if (/^(k|thousand|हज़ार|हजार|వేలు|వేల)$/.test(unit)) n *= 1000;
  if (/^(lakh|lac|लाख|లక్ష|లక్షలు)$/.test(unit)) n *= 100000;
  return Number.isFinite(n) ? Math.round(n) : null;
}

const READBACK = L("I heard {v} — is that right?", "मैंने सुना: {v} — क्या यह सही है?", "నేను విన్నది: {v} — ఇది సరేనా?");
const UNCLEAR = L("Sorry, I didn't get that. Please say it once more.", "माफ़ कीजिए, समझ नहीं आया। एक बार फिर बताइए।", "క్షమించండి, అర్థం కాలేదు. ఇంకోసారి చెప్పండి.");
const PICK = L("Please pick one of the options.", "कृपया कोई एक विकल्प चुनिए।", "దయచేసి ఒక ఎంపికను ఎంచుకోండి.");

export async function mockInterpret(b: VoiceInterpretRequest): Promise<VoiceInterpretation> {
  await sleep(300);
  const l = lang(b.language);
  const q = FLOWS[b.flow].find((x) => x.field === b.field);
  const text = norm(b.text);
  const short = text.split(" ").length <= 3;
  const out = (p: Partial<VoiceInterpretation>): VoiceInterpretation => ({
    understood: false,
    value: null,
    readback: null,
    confidence: 0,
    alternatives: [],
    intent: "unclear",
    reprompt: null,
    needs_confirmation: true,
    also: {},
    source: "rules",
    ...p,
  });
  if (!q || !text) return out({ reprompt: UNCLEAR[l] });
  if (hasWord(text, WORDS.repeat) && short) return out({ intent: "repeat" });
  if (hasWord(text, WORDS.skip) && short) return out({ intent: "skip" });
  if (short && q.kind !== "text" && hasWord(text, WORDS.no)) {
    return q.kind === "yesno" ? out({ understood: true, value: false, intent: "answer", confidence: 0.9, readback: READBACK[l].replace("{v}", valueLabel(q, false, l)) }) : out({ intent: "no" });
  }
  if (short && hasWord(text, WORDS.yes) && parseAmount(text) === null) {
    return q.kind === "yesno" ? out({ understood: true, value: true, intent: "answer", confidence: 0.9, readback: READBACK[l].replace("{v}", valueLabel(q, true, l)) }) : out({ intent: "yes" });
  }
  if (short && hasWord(text, WORDS.no)) return out({ intent: "no" });

  if (q.kind === "number") {
    const n = parseAmount(text);
    if (n === null) return out({ reprompt: q.reprompt?.[l] ?? UNCLEAR[l] });
    return out({ understood: true, value: n, intent: "answer", confidence: 0.85, readback: READBACK[l].replace("{v}", valueLabel(q, n, l)) });
  }
  if (q.kind === "choice" && q.options) {
    const hit = q.options.find((o) => (["en", "hi", "te"] as Lang[]).some((x) => text.includes(norm(o.label[x]))) || text.includes(o.value.replace(/_/g, " ")));
    if (!hit) return out({ reprompt: `${PICK[l]} ${q.options.map((o) => o.label[l]).join(", ")}` });
    return out({ understood: true, value: hit.value, intent: "answer", confidence: 0.8, readback: READBACK[l].replace("{v}", hit.label[l]) });
  }
  const value = b.text.trim();
  if (value.length < 2) return out({ reprompt: UNCLEAR[l] });
  return out({ understood: true, value, intent: "answer", confidence: 0.75, readback: READBACK[l].replace("{v}", value) });
}
