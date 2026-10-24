/* The language list and the cookie name, with no React import, so the server
 * root layout can read the person's language (config.ts pulls in react-i18next,
 * which only runs in client components). */

export const SUPPORTED_LANGUAGES = ["en", "hi", "te", "mr", "kn"] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = "en";

/** Cookie the server reads to render in the person's language. */
export const LANGUAGE_COOKIE = "mangaly.language";

export function isSupported(value: string | null | undefined): value is Language {
  return !!value && (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}
