/* Formatting in the reader's language and time zone. Indian date order. */

const LOCALE: Record<string, string> = { en: "en-IN", hi: "hi-IN", te: "te-IN" };

export function money(minor: number | null | undefined, currency = "INR", lang = "en"): string {
  if (minor === null || minor === undefined) return "";
  return new Intl.NumberFormat(LOCALE[lang] ?? "en-IN", { style: "currency", currency, maximumFractionDigits: minor % 100 ? 2 : 0 }).format(minor / 100);
}

export function dateLong(iso: string, lang = "en"): string {
  return new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" }).format(new Date(iso));
}

export function dateShort(iso: string, lang = "en"): string {
  return new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { day: "numeric", month: "short" }).format(new Date(iso));
}

export function timeShort(iso: string, lang = "en"): string {
  return new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { hour: "numeric", minute: "2-digit" }).format(new Date(iso));
}

export function dateTime(iso: string, lang = "en"): string {
  return `${dateLong(iso, lang)} · ${timeShort(iso, lang)}`;
}

export function localTimeZone(): string {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Kolkata"; } catch { return "Asia/Kolkata"; }
}

export function relative(iso: string, lang = "en"): string {
  const diff = (new Date(iso).getTime() - Date.now()) / 1000;
  const rtf = new Intl.RelativeTimeFormat(LOCALE[lang] ?? "en-IN", { numeric: "auto" });
  const abs = Math.abs(diff);
  if (abs < 3600) return rtf.format(Math.round(diff / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), "hour");
  return rtf.format(Math.round(diff / 86400), "day");
}

export function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((s) => s[0]?.toUpperCase() ?? "").join("");
}

export function dayKey(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** "India Standard Time" rather than the IANA id the browser reports (e.g. Asia/Calcutta). */
export function timeZoneLabel(lang = "en", tz?: string): string {
  try {
    const parts = new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { timeZone: tz, timeZoneName: "long" }).formatToParts(new Date());
    return parts.find((p) => p.type === "timeZoneName")?.value ?? tz ?? "";
  } catch { return tz ?? ""; }
}

/** "3:00 – 3:45 pm IST": a time range with the reader's short time-zone name. */
export function timeRangeZone(startIso: string, endIso: string, lang = "en"): string {
  const loc = LOCALE[lang] ?? "en-IN";
  try {
    return new Intl.DateTimeFormat(loc, { hour: "numeric", minute: "2-digit", timeZoneName: "short" }).formatRange(new Date(startIso), new Date(endIso));
  } catch {
    return `${timeShort(startIso, lang)} – ${timeShort(endIso, lang)}`;
  }
}

/** Parts for a calendar-style day badge: month, day number, weekday. */
export function dayParts(iso: string, lang = "en"): { month: string; day: string; weekday: string } {
  const loc = LOCALE[lang] ?? "en-IN";
  const d = new Date(iso);
  return {
    month: new Intl.DateTimeFormat(loc, { month: "short" }).format(d),
    day: new Intl.DateTimeFormat(loc, { day: "numeric" }).format(d),
    weekday: new Intl.DateTimeFormat(loc, { weekday: "short" }).format(d),
  };
}

/** A short count-down or count-up: "12 min", "3 h 5 min", "2 days". */
export function span(ms: number, lang = "en"): string {
  const loc = LOCALE[lang] ?? "en-IN";
  const min = Math.max(1, Math.round(Math.abs(ms) / 60000));
  const unit = (n: number, u: "minute" | "hour" | "day") => new Intl.NumberFormat(loc, { style: "unit", unit: u, unitDisplay: "short" }).format(n);
  if (min < 60) return unit(min, "minute");
  if (min < 24 * 60) { const h = Math.floor(min / 60); const m = min % 60; return m ? `${unit(h, "hour")} ${unit(m, "minute")}` : unit(h, "hour"); }
  return unit(Math.round(min / 1440), "day");
}
