/* i18n — ADR-010, FR002. Every user-visible string lives in locales/<lang>/common.json.
 * English is complete; Hindi/Telugu may be partial and fall back per key. */

import i18next, { type i18n as I18nInstance } from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from '@/locales/en/common.json';
import hi from '@/locales/hi/common.json';
import te from '@/locales/te/common.json';

export const SUPPORTED_LANGUAGES = ['en', 'hi', 'te'] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = 'en';
export const LANGUAGE_NATIVE: Record<Language, string> = { en: 'English', hi: 'हिंदी', te: 'తెలుగు' };

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
