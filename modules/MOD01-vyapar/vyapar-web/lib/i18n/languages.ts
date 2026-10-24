// [Critique N10] The language list and cookie name with NO dependencies, so
// the server root layout can read the language cookie without importing
// i18next / react-i18next (which are client-side) into a Server Component.
// Marathi (mr) and Kannada (kn) added 2026-10-06.
export const SUPPORTED_LANGUAGES = ["en", "hi", "te", "mr", "kn"] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = "en";
export const LANGUAGE_COOKIE = "vyapar_lang";

// [2026-10-06] Intl locales. Digits stay Latin in every language, with
// Indian lakh/crore grouping. Hindi and Telugu already do that with
// "<lang>-IN"; Marathi defaults to Devanagari digits and Marathi/Kannada
// currency falls back to Western grouping, so their numbers use "en-IN"
// and Marathi dates ask for Latin digits. en/hi/te are unchanged.
export function numberLocale(language: string | null | undefined): string {
  const l = (language || "en").slice(0, 2);
  return l === "mr" || l === "kn" ? "en-IN" : `${l}-IN`;
}

export function dateLocale(language: string | null | undefined): string {
  const l = (language || "en").slice(0, 2);
  return l === "mr" ? "mr-IN-u-nu-latn" : `${l}-IN`;
}

export function isSupported(value: string | null | undefined): value is Language {
  return !!value && (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}
