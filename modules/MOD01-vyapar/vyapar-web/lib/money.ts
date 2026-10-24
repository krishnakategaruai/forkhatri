// [FR30/FR31/FR54] One money formatter for every commercial screen — amounts
// travel as integer paise (never floats) and are shown in rupees with the
// member's own locale digits and separators.
// Traces to: FR30, FR31, FR54
import { dateLocale, numberLocale } from "@/lib/i18n/languages";

export function formatPaise(paise: number, language: string): string {
  return new Intl.NumberFormat(numberLocale(language), { style: "currency", currency: "INR" }).format(paise / 100);
}

// [FE1 — 2026-09-28] Whole-rupee display for salaries, budgets and bids
// ("₹18,000", not "₹18,000.00"): paise stay the wire unit; people read and
// type whole rupees. Indian digit grouping (lakh/crore) via the -IN locale.
export function formatRupees(paise: number, language: string): string {
  return new Intl.NumberFormat(numberLocale(language), { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(
    Math.round(paise / 100),
  );
}

/** "₹15,000 – ₹18,000", or one amount when only one side (or both equal) is known. */
export function formatRupeeRange(minPaise: number | null | undefined, maxPaise: number | null | undefined, language: string): string | null {
  const lo = minPaise ?? null;
  const hi = maxPaise ?? null;
  if (lo === null && hi === null) return null;
  if (lo === null || hi === null || lo === hi) return formatRupees((lo ?? hi) as number, language);
  return `${formatRupees(lo, language)} – ${formatRupees(hi, language)}`;
}

const DEVANAGARI_DIGITS = "०१२३४५६७८९";
const TELUGU_DIGITS = "౦౧౨౩౪౫౬౭౮౯";
const KANNADA_DIGITS = "೦೧೨೩೪೫೬೭೮೯";

/**
 * What a person types or says for an amount → integer paise, or null.
 * [Critique L2] Reads the way people in India write money: "18000",
 * "18,000", "₹18,000.50", "15k", "15 हज़ार", "15 వేలు", "1.5 lakh",
 * "2 लाख", "2 లక్షలు", "1 crore"; Devanagari and Telugu digits too.
 * [2026-10-06] Also Marathi ("15 हजार", "1 कोटी", "दरमहा") and Kannada
 * ("15 ಸಾವಿರ", "2 ಲಕ್ಷ", "1 ಕೋಟಿ", Kannada digits).
 * Decimals are kept (to the paisa). Two numbers ("15-18k", "15000 18000")
 * are ambiguous for a single amount field, so they return null and the
 * field asks for one amount.
 */
export function rupeesToPaise(input: string): number | null {
  let s = input.normalize("NFC").trim().toLowerCase();
  if (!s) return null;
  s = s
    .replace(/[०-९]/g, (d) => String(DEVANAGARI_DIGITS.indexOf(d)))
    .replace(/[౦-౯]/g, (d) => String(TELUGU_DIGITS.indexOf(d)))
    .replace(/[೦-೯]/g, (d) => String(KANNADA_DIGITS.indexOf(d)))
    .replace(/(\d),(?=\d)/g, "$1")
    .replace(/₹|\brs\.?|\binr\b|rupees?|रुपये|रुपए|रु\.?|రూపాయలు|రూ\.?|ರೂಪಾಯಿಗಳು|ರೂಪಾಯಿ|ರೂ\.?/g, " ");
  const nums = s.match(/\d+(?:\.\d+)?/g);
  if (!nums || nums.length !== 1) return null;
  let value = parseFloat(nums[0]);
  const rest = s.slice(s.indexOf(nums[0]) + nums[0].length).trim();
  if (/^(k\b|thousand|हज|వేల|వేలు|వెయ్య|ಸಾವಿರ)/.test(rest)) value *= 1_000;
  else if (/^(l\b|lakh|lac|लाख|లక్ష|ಲಕ್ಷ)/.test(rest)) value *= 100_000;
  else if (/^(cr\b|crore|करोड|కోటి|కోట్ల|कोटी|ಕೋಟಿ)/.test(rest)) value *= 10_000_000;
  else if (/^(\/|per\b|a\b|an\b|प्रति|ప్రతి|महीना|माह|నెల|दरमहा|महिना|दर|ಪ್ರತಿ|ತಿಂಗಳ)/.test(rest) || !rest) {
    // "/month", "per hour", "a day": the unit belongs to the field, not the amount
  } else if (/^[a-zऀ-౿ಀ-೿]/.test(rest)) {
    return null;
  }
  if (!Number.isFinite(value) || value < 0) return null;
  return Math.round(value * 100);
}

/** Integer paise → the whole-rupee string an input shows ("" for null). */
export function paiseToRupeeInput(paise: number | null | undefined): string {
  return paise === null || paise === undefined ? "" : String(Math.round(paise / 100));
}

/** Indian day-month-year order: "28 Sept 2026" / "28 सित॰ 2026". */
export function formatDateIN(iso: string, language: string, withYear = true): string {
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  return d.toLocaleDateString(dateLocale(language), { day: "numeric", month: "short", ...(withYear ? { year: "numeric" } : {}) });
}
