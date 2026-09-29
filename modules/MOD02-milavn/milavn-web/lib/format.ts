const IST = 'Asia/Kolkata';
const LOCALE: Record<string, string> = { en: 'en-IN', hi: 'hi-IN', te: 'te-IN' };
const TODAY: Record<string, string> = { en: 'Today', hi: 'आज', te: 'ఈరోజు' };
const YESTERDAY: Record<string, string> = { en: 'Yesterday', hi: 'कल', te: 'నిన్న' };

// FR002: dates render in the person's language (Intl locale + native "Today").
export function formatWhen(iso: string, lang = 'en'): string {
  const d = new Date(iso);
  const now = new Date();
  const loc = LOCALE[lang] ?? 'en-IN';
  const day = new Intl.DateTimeFormat(loc, { timeZone: IST, weekday: 'short', day: 'numeric', month: 'short' }).format(d);
  const time = new Intl.DateTimeFormat(loc, { timeZone: IST, hour: 'numeric', minute: '2-digit' }).format(d);
  const sameDay = new Intl.DateTimeFormat('en-IN', { timeZone: IST, dateStyle: 'short' }).format(d) === new Intl.DateTimeFormat('en-IN', { timeZone: IST, dateStyle: 'short' }).format(now);
  return `${sameDay ? (TODAY[lang] ?? 'Today') : day} · ${time}`;
}

// Day separators on a board or chat: Today / Yesterday in the person's own
// words, then "Sun, 14 Sep" — always the IST day, like every date in Milavn.
export function formatDayLabel(iso: string, lang = 'en'): string {
  const key = (d: Date) => new Intl.DateTimeFormat('en-IN', { timeZone: IST, dateStyle: 'short' }).format(d);
  const d = new Date(iso);
  const now = new Date();
  if (key(d) === key(now)) return TODAY[lang] ?? 'Today';
  if (key(d) === key(new Date(now.getTime() - 86400000))) return YESTERDAY[lang] ?? 'Yesterday';
  return new Intl.DateTimeFormat(LOCALE[lang] ?? 'en-IN', { timeZone: IST, weekday: 'short', day: 'numeric', month: 'short' }).format(d);
}

export function formatTime(iso: string, lang = 'en'): string {
  return new Intl.DateTimeFormat(LOCALE[lang] ?? 'en-IN', { timeZone: IST, hour: 'numeric', minute: '2-digit' }).format(new Date(iso));
}

export function formatDateLong(iso: string, lang = 'en'): string {
  return new Intl.DateTimeFormat(LOCALE[lang] ?? 'en-IN', { timeZone: IST, weekday: 'long', day: 'numeric', month: 'long', hour: 'numeric', minute: '2-digit' }).format(new Date(iso));
}

// FR102: rupees in the person's language, whole rupees without decimals (₹200, ₹1,250.50).
export function formatInr(paise: number, lang = 'en'): string {
  const digits = paise % 100 === 0 ? 0 : 2;
  return new Intl.NumberFormat(LOCALE[lang] ?? 'en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(paise / 100);
}

export function formatRelative(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`;
  return `${Math.floor(diff / 86400)} d ago`;
}

export function toLocalInputValue(iso: string): string {
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export function initials(name: string): string {
  return name.split(/\s+/).map((s) => s[0]).filter(Boolean).slice(0, 2).join('').toUpperCase();
}
