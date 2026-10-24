/* i18n — ADR-010, FR002. Every user-visible string lives in locales/<lang>/common.json.
 * English is complete; Hindi/Telugu/Marathi/Kannada may be partial and fall back per key. */

import i18next, { type i18n as I18nInstance } from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from '@/locales/en/common.json';
import hi from '@/locales/hi/common.json';
import te from '@/locales/te/common.json';

export const SUPPORTED_LANGUAGES = ['en', 'hi', 'te', 'mr', 'kn'] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = 'en';
export const LANGUAGE_NATIVE: Record<Language, string> = { en: 'English', hi: 'हिंदी', te: 'తెలుగు', mr: 'मराठी', kn: 'ಕನ್ನಡ' };

export function isSupported(v: string | null | undefined): v is Language {
  return !!v && (SUPPORTED_LANGUAGES as readonly string[]).includes(v);
}

let instance: I18nInstance | null = null;
export function getI18n(lng: Language = DEFAULT_LANGUAGE): I18nInstance {
  if (instance) return instance;
  const i18n = i18next.createInstance();
  void i18n.use(initReactI18next).init({
    resources: { en: { common: en }, hi: { common: hi }, te: { common: te } },
    lng,
    fallbackLng: DEFAULT_LANGUAGE,
    ns: ['common'],
    defaultNS: 'common',
    interpolation: { escapeValue: false },
    returnEmptyString: false,
  });
  instance = i18n;
  return i18n;
}

// Marathi and Kannada are loaded when first chosen, from locales/<lang>/common.json. Until a file exists (or for any key
// it lacks) the person sees English, never a broken page; English, Hindi and Telugu stay bundled exactly as before.
const ON_DEMAND: readonly Language[] = ['mr', 'kn'];
export function needsLoad(lng: Language): boolean {
  return ON_DEMAND.includes(lng) && !getI18n().hasResourceBundle(lng, 'common');
}
export async function loadLanguage(lng: Language): Promise<void> {
  if (!needsLoad(lng)) return;
  try {
    const mod = (await import(`../../locales/${lng}/common.json`)) as { default?: Record<string, unknown> } & Record<string, unknown>;
    getI18n().addResourceBundle(lng, 'common', mod.default ?? mod, true, true);
  } catch { /* not translated yet: English fallback */ }
}
