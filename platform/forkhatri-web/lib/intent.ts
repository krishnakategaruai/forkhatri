/**
 * Rule-based, fully client-side intent parser for the command orb.
 * No network and no AI call: a phrase is scored against each module's real
 * scope, and the parts we recognised are returned so the interface can show
 * them as "understanding" chips before anything happens.
 *
 *   "cricket this weekend near me"
 *     -> module milavn · kind activity · time weekend · place near
 */

export type ModuleKey = "mangaly" | "milavn" | "vyapar" | "counsel" | "payments" | "finance";
export type IntentKind =
  | "activity"
  | "matrimony"
  | "business"
  | "service"
  | "opportunity"
  | "advice"
  | "payment"
  | "loan";
export type TimeKey = "today" | "tonight" | "tomorrow" | "weekend";
export type Place = { type: "near" } | { type: "in"; value: string };

export type Intent = {
  module: ModuleKey | null;
  /** Modules tied for the best score when the phrase is ambiguous. */
  candidates: ModuleKey[];
  kind: IntentKind | null;
  time: TimeKey | null;
  place: Place | null;
};

type Term = { term: string; weight: number; kind: IntentKind };

const t = (kind: IntentKind, weight: number, ...terms: string[]): Term[] =>
  terms.map((term) => ({ term, weight, kind }));

/** Keywords stay inside each module's real scope (docs/modules and TR18). */
const RULES: Record<ModuleKey, Term[]> = {
  mangaly: [
    ...t("matrimony", 3, "marriage", "matrimony", "matrimonial", "alliance", "rishta", "bride", "groom", "family introduction"),
    ...t("matrimony", 3, "शादी", "रिश्ता", "रिश्ते", "పెళ్లి", "సంబంధం"),
    ...t("matrimony", 1, "match"),
  ],
  milavn: [
    ...t("activity", 3, "meetup", "meet up", "activity", "activities", "cricket", "yoga", "volunteer", "कार्यक्रम", "కార్యక్రమం", "క్రికెట్", "యోగా", "क्रिकेट", "योग"),
    ...t("activity", 2, "event", "walk", "मिलना"),
    ...t("activity", 1, "join", "circle", "weekend", "near me"),
  ],
  vyapar: [
    ...t("business", 3, "business", "shop", "व्यापार", "व्यवसाय", "వ్యాపారం"),
    ...t("service", 3, "plumber", "electrician", "प्लंबर", "इलेक्ट्रीशियन", "ప్లంబర్", "ఎలక్ట్రీషియన్"),
    ...t("service", 2, "hire", "professional"),
    ...t("service", 1, "service"),
    ...t("opportunity", 3, "opportunity", "opportunities", "job"),
  ],
  counsel: [...t("advice", 3, "lawyer", "advice", "consult", "ca", "सलाह", "సలహా")],
  payments: [...t("payment", 3, "bill", "recharge", "coupon"), ...t("payment", 2, "pay")],
  finance: [...t("loan", 3, "loan", "emi", "credit", "लोन", "ऋण", "రుణం")],
};

const TIME_PATTERNS: [TimeKey, string[]][] = [
  ["tonight", ["tonight", "आज रात", "ఈ రాత్రి"]],
  ["weekend", ["this weekend", "weekend", "saturday", "sunday", "वीकेंड", "सप्ताहांत", "వారాంతం"]],
  ["tomorrow", ["tomorrow", "कल", "రేపు"]],
  ["today", ["today", "आज", "ఈ రోజు", "ఈరోజు"]],
];

const NEAR_PATTERNS = ["near me", "nearby", "around me", "close to me", "पास", "नज़दीक", "नजदीक", "దగ్గర", "సమీపంలో"];

const IN_STOPWORDS = new Set(["the", "a", "an", "my", "this", "next", "morning", "evening", "afternoon", "night", "person", "future"]);

const isLatin = (term: string) => /^[\x20-\x7e]+$/.test(term);
const escape = (term: string) => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function contains(text: string, term: string): boolean {
  if (!isLatin(term)) return text.includes(term);
  // Whole words only, with simple plurals ("bills", "events", "loans").
  return new RegExp(`(^|[^a-z0-9])${escape(term)}(s|es)?(?=[^a-z0-9]|$)`).test(text);
}

export function parseIntent(input: string): Intent {
  const text = input.toLowerCase().replace(/\s+/g, " ").trim();
  const empty: Intent = { module: null, candidates: [], kind: null, time: null, place: null };
  if (!text) return empty;

  const scores = new Map<ModuleKey, { score: number; kinds: Map<IntentKind, number> }>();
  for (const [module, terms] of Object.entries(RULES) as [ModuleKey, Term[]][]) {
    for (const { term, weight, kind } of terms) {
      if (!contains(text, term)) continue;
      const entry = scores.get(module) ?? { score: 0, kinds: new Map() };
      entry.score += weight;
      entry.kinds.set(kind, (entry.kinds.get(kind) ?? 0) + weight);
      scores.set(module, entry);
    }
  }

  const ranked = [...scores.entries()].sort((a, b) => b[1].score - a[1].score);
  const top = ranked[0]?.[1].score ?? 0;
  const candidates = ranked.filter(([, entry]) => entry.score === top).map(([module]) => module);
  const best = candidates.length === 1 ? candidates[0] : null;

  let kind: IntentKind | null = null;
  if (best) {
    const kinds = [...scores.get(best)!.kinds.entries()].sort((a, b) => b[1] - a[1]);
    kind = kinds[0]?.[0] ?? null;
  }

  const time = TIME_PATTERNS.find(([, patterns]) => patterns.some((pattern) => contains(text, pattern)))?.[0] ?? null;

  let place: Place | null = NEAR_PATTERNS.some((pattern) => contains(text, pattern)) ? { type: "near" } : null;
  if (!place) {
    const match = /(?:^|\s)in ([a-z][a-z.]+(?: [a-z][a-z.]+)?)\s*$/.exec(text);
    const words = match?.[1].split(" ") ?? [];
    if (match && !IN_STOPWORDS.has(words[0]) && !TIME_PATTERNS.some(([, p]) => p.includes(match[1]))) {
      place = { type: "in", value: words.map((word) => word[0].toUpperCase() + word.slice(1)).join(" ") };
    }
  }

  return { module: best, candidates: best ? [best] : candidates, kind, time, place };
}
