// [FE2] Indian formats for dates, times and rupees, in the member's language.
// Dates read "28 Sep 2026" (day first, never US order), times "10 am",
// money "₹1,49,900" with Indian digit grouping and no ".00" on whole rupees.
// lib/money.ts's formatPaise stays as it is for the commercial screens.

const locale = (language: string) => `${(language || "en").slice(0, 2)}-IN`;

/** "₹3,000" — whole rupees without decimals, paise shown only when present. */
export function formatRupees(paise: number, language: string): string {
  const whole = paise % 100 === 0;
  return new Intl.NumberFormat(locale(language), {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: whole ? 0 : 2,
    maximumFractionDigits: whole ? 0 : 2,
  }).format(paise / 100);
}

/**
 * [Critique L2] One rupee parser for the whole app: lib/money.ts's
 * rupeesToPaise ("1,499", "1499.50", "15k", "1.5 lakh", "15 हज़ार",
 * Devanagari/Telugu digits; two numbers → null). Re-exported here so the
 * contract, package and filter screens that import it from lib/format keep
 * working and can never drift from the composer's reading of an amount.
 */
export { rupeesToPaise } from "./money";

/** Paise → the plain number a rupee input field shows ("1499" / "1499.5"). */
export function paiseToInput(paise: number | null | undefined): string {
  if (paise == null) return "";
  return String(paise / 100);
}

/** A date-only ISO string ("2026-10-28") must not shift a day across timezones. */
function toDate(value: string | Date): Date {
  if (value instanceof Date) return value;
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split("-").map(Number);
    return new Date(y, m - 1, d);
  }
  return new Date(value);
}

/** "28 Sep 2026" */
export function formatDate(value: string | Date, language: string): string {
  return new Intl.DateTimeFormat(locale(language), { day: "numeric", month: "short", year: "numeric" }).format(toDate(value));
}

/** "28 Sep" — for dates in the current year where the year is noise. */
export function formatDayMonth(value: string | Date, language: string): string {
  return new Intl.DateTimeFormat(locale(language), { day: "numeric", month: "short" }).format(toDate(value));
}

/** "September 2026" — month and year, Indian locale. */
export function formatMonthYear(value: string | Date, language: string): string {
  return new Intl.DateTimeFormat(locale(language), { month: "long", year: "numeric" }).format(toDate(value));
}

/** "28 Sep 2026, 2:05 pm" — always India time, whatever the device clock's zone. */
export function formatDateTime(value: string | Date, language: string): string {
  return new Intl.DateTimeFormat(locale(language), {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(toDate(value));
}

/** "HH:MM" (24 h) → "10 am" / "6:30 pm" in the member's language. */
export function formatClock(hhmm: string, language: string): string {
  const [h, m] = hhmm.split(":").map(Number);
  const d = new Date(2000, 0, 1, h, m || 0);
  return new Intl.DateTimeFormat(locale(language), { hour: "numeric", minute: m ? "2-digit" : undefined }).format(d);
}

/** Whole days from now until `iso` (0 when due or past). */
export function daysUntil(iso: string, now: number = Date.now()): number {
  return Math.max(0, Math.ceil((new Date(iso).getTime() - now) / 86_400_000));
}
