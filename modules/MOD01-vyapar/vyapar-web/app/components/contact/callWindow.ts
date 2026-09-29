// [FE2] Turning calling preferences into words a person reads: "Mon–Sat",
// "10 am–6 pm". Day names come from Intl in the member's language (no
// translation keys to drift); the surrounding sentences are i18n keys in
// locales/<lang>/contact.json.
import type { Weekday } from "@/lib/sdk";
import { formatClock } from "@/lib/format";

export const WEEKDAYS: Weekday[] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

/** Short localized weekday ("Mon", "सोम", "సోమ"). 1 Jan 2024 was a Monday. */
export function dayShort(day: Weekday, language: string): string {
  const d = new Date(2024, 0, 1 + WEEKDAYS.indexOf(day));
  return new Intl.DateTimeFormat(`${language.slice(0, 2)}-IN`, { weekday: "short" }).format(d);
}

/** ["mon".."sat"] → "Mon–Sat"; ["mon","wed","fri"] → "Mon, Wed, Fri"; [] or all seven → null (every day). */
export function describeDays(days: readonly string[], language: string): string | null {
  const idx = [...new Set(days.map((d) => WEEKDAYS.indexOf(d as Weekday)).filter((i) => i >= 0))].sort((a, b) => a - b);
  if (idx.length === 0 || idx.length === 7) return null;
  const runs: [number, number][] = [];
  for (const i of idx) {
    const last = runs[runs.length - 1];
    if (last && last[1] === i - 1) last[1] = i;
    else runs.push([i, i]);
  }
  return runs
    .map(([a, b]) => {
      const from = dayShort(WEEKDAYS[a], language);
      if (a === b) return from;
      const to = dayShort(WEEKDAYS[b], language);
      return b === a + 1 ? `${from}, ${to}` : `${from}–${to}`;
    })
    .join(", ");
}

/** "09:00","18:00" → "9 am–6 pm"; a missing or whole-day window → null (any time). */
export function describeHours(start: string | null | undefined, end: string | null | undefined, language: string): string | null {
  if (!start || !end) return null;
  if (start.slice(0, 5) === "00:00" && end.slice(0, 5) >= "23:59") return null;
  return `${formatClock(start.slice(0, 5), language)}–${formatClock(end.slice(0, 5), language)}`;
}

/**
 * The server's compact window ("mon-sat 09:00-18:00", "mon,wed,fri 10:00-19:00",
 * "mon-sun 00:00-23:59") → { days, hours } in words, either null when unrestricted.
 * Returns null when the string is not in a shape we recognise (never shown raw).
 */
export function describeWindow(window: string | null | undefined, language: string): { days: string | null; hours: string | null } | null {
  if (!window) return null;
  const m = window.trim().match(/^([a-z,-]+)\s+(\d{2}:\d{2})-(\d{2}:\d{2})$/);
  if (!m) return null;
  const [, dayPart, start, end] = m;
  let days: string[] = [];
  for (const piece of dayPart.split(",")) {
    const range = piece.split("-");
    if (range.length === 2) {
      const a = WEEKDAYS.indexOf(range[0] as Weekday);
      const b = WEEKDAYS.indexOf(range[1] as Weekday);
      if (a < 0 || b < 0) return null;
      for (let i = a; i <= b; i++) days.push(WEEKDAYS[i]);
    } else if (WEEKDAYS.includes(piece as Weekday)) {
      days.push(piece);
    } else {
      return null;
    }
  }
  days = [...new Set(days)];
  return { days: describeDays(days, language), hours: describeHours(start, end, language) };
}
