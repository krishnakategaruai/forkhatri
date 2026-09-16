/* [Product-owner standing rule, 2026-09-15] ForKhatri is multilingual
 * (English, Hindi, Telugu) — no user-visible text may be hardcoded in any
 * language anywhere in this codebase. Follows MOD03 Mangaly's exact i18n
 * pattern (mangaly-web/lib/i18n/config.ts, read but not edited) so the
 * two modules share one mental model for whoever maintains translations
 * across the platform, rather than each module inventing its own shape.
 *
 * Unlike Mangaly's own stated fallback design (English complete, Hindi/
 * Telugu allowed to be partial), the product owner's rule for Vyapar is
 * stricter: every key must have a REAL Hindi and Telugu value from the
 * start — an empty/fallback-only translation file does not satisfy the
 * rule. `locales/hi/*.json` and `locales/te/*.json` are fully translated,
 * not placeholders.
 *
 * Typing: `Namespace` is derived from the English files' own keys via
 * TypeScript's `resources` inference, so a renamed/typo'd key fails at
 * compile time rather than silently rendering nothing.
 */

import i18next, { type i18n as I18nInstance } from 'i18next';
import { initReactI18next } from 'react-i18next';

import enActivity from '@/locales/en/activity.json';
import enCommon from '@/locales/en/common.json';
import enDiscover from '@/locales/en/discover.json';
import enFirstRun from '@/locales/en/firstRun.json';
import enEnquiries from '@/locales/en/enquiries.json';
import enVerification from '@/locales/en/verification.json';
import enTrustSafety from '@/locales/en/trustSafety.json';
import enReviews from '@/locales/en/reviews.json';
import enPartnerships from '@/locales/en/partnerships.json';
import enCommercial from '@/locales/en/commercial.json';
import enListings from '@/locales/en/listings.json';
import enNotifications from '@/locales/en/notifications.json';
import enOpportunities from '@/locales/en/opportunities.json';
import enProfile from '@/locales/en/profile.json';
import enRanking from '@/locales/en/ranking.json';
import hiActivity from '@/locales/hi/activity.json';
import hiCommon from '@/locales/hi/common.json';
import hiDiscover from '@/locales/hi/discover.json';
import hiFirstRun from '@/locales/hi/firstRun.json';
import hiEnquiries from '@/locales/hi/enquiries.json';
import hiVerification from '@/locales/hi/verification.json';
import hiTrustSafety from '@/locales/hi/trustSafety.json';
import hiReviews from '@/locales/hi/reviews.json';
import hiPartnerships from '@/locales/hi/partnerships.json';
import hiCommercial from '@/locales/hi/commercial.json';
import hiListings from '@/locales/hi/listings.json';
import hiNotifications from '@/locales/hi/notifications.json';
import hiOpportunities from '@/locales/hi/opportunities.json';
import hiProfile from '@/locales/hi/profile.json';
import hiRanking from '@/locales/hi/ranking.json';
import teActivity from '@/locales/te/activity.json';
import teCommon from '@/locales/te/common.json';
import teDiscover from '@/locales/te/discover.json';
import teFirstRun from '@/locales/te/firstRun.json';
import teEnquiries from '@/locales/te/enquiries.json';
import teVerification from '@/locales/te/verification.json';
import teTrustSafety from '@/locales/te/trustSafety.json';
import teReviews from '@/locales/te/reviews.json';
import tePartnerships from '@/locales/te/partnerships.json';
import teCommercial from '@/locales/te/commercial.json';
import teListings from '@/locales/te/listings.json';
import teNotifications from '@/locales/te/notifications.json';
import teOpportunities from '@/locales/te/opportunities.json';
import teProfile from '@/locales/te/profile.json';
import teRanking from '@/locales/te/ranking.json';

export const SUPPORTED_LANGUAGES = ['en', 'hi', 'te'] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = 'en';

/** Namespaces map 1:1 to files in `locales/<lang>/`. */
export const NAMESPACES = [
  'common',
  'firstRun',
  'listings',
  'opportunities',
  'discover',
  'activity',
  'profile',
  'ranking',
  'notifications',
  'enquiries',
  'verification',
  'trustSafety',
  'reviews',
  'partnerships',
  'commercial',
] as const;
export type Namespace = (typeof NAMESPACES)[number];

const resources = {
  en: {
    common: enCommon,
    firstRun: enFirstRun,
    listings: enListings,
    opportunities: enOpportunities,
    discover: enDiscover,
    activity: enActivity,
    profile: enProfile,
    ranking: enRanking,
    notifications: enNotifications,
    enquiries: enEnquiries,
    verification: enVerification,
    trustSafety: enTrustSafety,
    reviews: enReviews,
    partnerships: enPartnerships,
    commercial: enCommercial,
  },
  hi: {
    common: hiCommon,
    firstRun: hiFirstRun,
    listings: hiListings,
    opportunities: hiOpportunities,
    discover: hiDiscover,
    activity: hiActivity,
    profile: hiProfile,
    ranking: hiRanking,
    notifications: hiNotifications,
    enquiries: hiEnquiries,
    verification: hiVerification,
    trustSafety: hiTrustSafety,
    reviews: hiReviews,
    partnerships: hiPartnerships,
    commercial: hiCommercial,
  },
  te: {
    common: teCommon,
    firstRun: teFirstRun,
    listings: teListings,
    opportunities: teOpportunities,
    discover: teDiscover,
    activity: teActivity,
    profile: teProfile,
    ranking: teRanking,
    notifications: teNotifications,
    enquiries: teEnquiries,
    verification: teVerification,
    trustSafety: teTrustSafety,
    reviews: teReviews,
    partnerships: tePartnerships,
    commercial: teCommercial,
  },
} as const;

export function isSupported(value: string | null | undefined): value is Language {
  return !!value && (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}

let instance: I18nInstance | null = null;

export function getI18n(initialLanguage: Language = DEFAULT_LANGUAGE): I18nInstance {
  if (instance) return instance;

  const i18n = i18next.createInstance();
  void i18n.use(initReactI18next).init({
    resources,
    lng: initialLanguage,
    fallbackLng: DEFAULT_LANGUAGE,
    ns: NAMESPACES,
    defaultNS: 'common',
    interpolation: {
      // React escapes for us; double-escaping mangles Hindi/Telugu text.
      escapeValue: false,
    },
    returnEmptyString: false,
  });

  instance = i18n;
  return i18n;
}
