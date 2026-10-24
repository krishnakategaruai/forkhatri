const IST = 'Asia/Kolkata';
// Marathi's ICU default is Devanagari digits; Milavn keeps Latin digits in every language (as Hindi/Telugu show them).
const LOCALE: Record<string, string> = { en: 'en-IN', hi: 'hi-IN', te: 'te-IN', mr: 'mr-IN-u-nu-latn', kn: 'kn-IN' };
/** The Intl locale for a Milavn language (unknown -> en-IN). Use this, never `${lang}-IN`. */
export const intlLocale = (lang: string | undefined): string => LOCALE[lang ?? 'en'] ?? 'en-IN';
const TODAY: Record<string, string> = { en: 'Today', hi: 'आज', te: 'ఈరోజు', mr: 'आज', kn: 'ಇಂದು' };
const YESTERDAY: Record<string, string> = { en: 'Yesterday', hi: 'कल', te: 'నిన్న', mr: 'काल', kn: 'ನಿನ್ನೆ' };

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
  const loc = LOCALE[lang] ?? 'en-IN';
  const d = new Date(iso);
  if (lang === 'hi' || lang === 'te' || lang === 'mr' || lang === 'kn') {
    // ICU's combined Hindi pattern reads "… 12:29 pm बजे", Telugu "… 12:29 PMకి", Marathi "… रोजी 1:29 PM" and
    // Kannada "… ರಂದು 1:29 PM ಸಮಯಕ್ಕೆ"; keep date and time apart.
    const day = new Intl.DateTimeFormat(loc, { timeZone: IST, weekday: 'long', day: 'numeric', month: 'long' }).format(d);
    return `${day} · ${formatTime(iso, lang)}`;
  }
  return new Intl.DateTimeFormat(loc, { timeZone: IST, weekday: 'long', day: 'numeric', month: 'long', hour: 'numeric', minute: '2-digit' }).format(d);
}

// FR102: rupees in the person's language, whole rupees without decimals (₹200, ₹1,250.50).
export function formatInr(paise: number, lang = 'en'): string {
  const digits = paise % 100 === 0 ? 0 : 2;
  return new Intl.NumberFormat(LOCALE[lang] ?? 'en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(paise / 100);
}

export function formatRelative(iso: string, lang?: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  // applyLanguage() (lib/i18n/provider) keeps <html lang> on the person's language.
  const l = lang ?? (typeof document !== 'undefined' ? document.documentElement.lang : 'en') ?? 'en';
  const rtf = new Intl.RelativeTimeFormat(LOCALE[l] ?? 'en-IN', { numeric: 'auto', style: 'short' });
  if (diff < 60) return l === 'hi' ? 'अभी' : l === 'te' ? 'ఇప్పుడే' : l === 'mr' ? 'आत्ताच' : l === 'kn' ? 'ಈಗಷ್ಟೇ' : 'just now';
  if (diff < 3600) return rtf.format(-Math.floor(diff / 60), 'minute');
  if (diff < 86400) return rtf.format(-Math.floor(diff / 3600), 'hour');
  return rtf.format(-Math.floor(diff / 86400), 'day');
}

export function toLocalInputValue(iso: string): string {
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export function initials(name: string): string {
  return name.split(/\s+/).map((s) => s[0]).filter(Boolean).slice(0, 2).join('').toUpperCase();
}
