// [Critique N10] The language list and cookie name with NO dependencies, so
// the server root layout can read the language cookie without importing
// i18next / react-i18next (which are client-side) into a Server Component.
export const SUPPORTED_LANGUAGES = ["en", "hi", "te"] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = "en";
export const LANGUAGE_COOKIE = "vyapar_lang";

export function isSupported(value: string | null | undefined): value is Language {
  return !!value && (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}
