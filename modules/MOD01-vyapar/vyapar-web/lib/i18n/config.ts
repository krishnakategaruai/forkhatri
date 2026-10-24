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
import enWorkspace from '@/locales/en/workspace.json';
import enAdminCommercial from '@/locales/en/adminCommercial.json';
import enPrivacy from '@/locales/en/privacy.json';
import enAdminOps from '@/locales/en/adminOps.json';
import enListings from '@/locales/en/listings.json';
import enNotifications from '@/locales/en/notifications.json';
import enOpportunities from '@/locales/en/opportunities.json';
import enProfile from '@/locales/en/profile.json';
import enRanking from '@/locales/en/ranking.json';
import enHiring from '@/locales/en/hiring.json';
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
import hiWorkspace from '@/locales/hi/workspace.json';
import hiAdminCommercial from '@/locales/hi/adminCommercial.json';
import hiPrivacy from '@/locales/hi/privacy.json';
import hiAdminOps from '@/locales/hi/adminOps.json';
import hiListings from '@/locales/hi/listings.json';
import hiNotifications from '@/locales/hi/notifications.json';
import hiOpportunities from '@/locales/hi/opportunities.json';
import hiProfile from '@/locales/hi/profile.json';
import hiRanking from '@/locales/hi/ranking.json';
import hiHiring from '@/locales/hi/hiring.json';
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
import teWorkspace from '@/locales/te/workspace.json';
import teAdminCommercial from '@/locales/te/adminCommercial.json';
import tePrivacy from '@/locales/te/privacy.json';
import teAdminOps from '@/locales/te/adminOps.json';
import teListings from '@/locales/te/listings.json';
import teNotifications from '@/locales/te/notifications.json';
import teOpportunities from '@/locales/te/opportunities.json';
import teProfile from '@/locales/te/profile.json';
import teRanking from '@/locales/te/ranking.json';
import teHiring from '@/locales/te/hiring.json';
// [FE2] contact control, contracts, service packages, Hire/Find work + outcomes + Discover filters
import enContact from '@/locales/en/contact.json';
import enContracts from '@/locales/en/contracts.json';
import enPackages from '@/locales/en/packages.json';
import enExplore from '@/locales/en/explore.json';
import hiContact from '@/locales/hi/contact.json';
import hiContracts from '@/locales/hi/contracts.json';
import hiPackages from '@/locales/hi/packages.json';
import hiExplore from '@/locales/hi/explore.json';
import teContact from '@/locales/te/contact.json';
import teContracts from '@/locales/te/contracts.json';
import tePackages from '@/locales/te/packages.json';
import teExplore from '@/locales/te/explore.json';
// [Voice interview 2026-09-30] the guided voice conversation
import enVoice from '@/locales/en/voice.json';
import hiVoice from '@/locales/hi/voice.json';
import teVoice from '@/locales/te/voice.json';
// [2026-10-06] Marathi (mr) and Kannada (kn)
import mrActivity from '@/locales/mr/activity.json';
import mrCommon from '@/locales/mr/common.json';
import mrDiscover from '@/locales/mr/discover.json';
import mrFirstRun from '@/locales/mr/firstRun.json';
import mrEnquiries from '@/locales/mr/enquiries.json';
import mrVerification from '@/locales/mr/verification.json';
import mrTrustSafety from '@/locales/mr/trustSafety.json';
import mrReviews from '@/locales/mr/reviews.json';
import mrPartnerships from '@/locales/mr/partnerships.json';
import mrCommercial from '@/locales/mr/commercial.json';
import mrWorkspace from '@/locales/mr/workspace.json';
import mrAdminCommercial from '@/locales/mr/adminCommercial.json';
import mrPrivacy from '@/locales/mr/privacy.json';
import mrAdminOps from '@/locales/mr/adminOps.json';
import mrListings from '@/locales/mr/listings.json';
import mrNotifications from '@/locales/mr/notifications.json';
import mrOpportunities from '@/locales/mr/opportunities.json';
import mrProfile from '@/locales/mr/profile.json';
import mrRanking from '@/locales/mr/ranking.json';
import mrHiring from '@/locales/mr/hiring.json';
import mrContact from '@/locales/mr/contact.json';
import mrContracts from '@/locales/mr/contracts.json';
import mrPackages from '@/locales/mr/packages.json';
import mrExplore from '@/locales/mr/explore.json';
import mrVoice from '@/locales/mr/voice.json';
import knActivity from '@/locales/kn/activity.json';
import knCommon from '@/locales/kn/common.json';
import knDiscover from '@/locales/kn/discover.json';
import knFirstRun from '@/locales/kn/firstRun.json';
import knEnquiries from '@/locales/kn/enquiries.json';
import knVerification from '@/locales/kn/verification.json';
import knTrustSafety from '@/locales/kn/trustSafety.json';
import knReviews from '@/locales/kn/reviews.json';
import knPartnerships from '@/locales/kn/partnerships.json';
import knCommercial from '@/locales/kn/commercial.json';
import knWorkspace from '@/locales/kn/workspace.json';
import knAdminCommercial from '@/locales/kn/adminCommercial.json';
import knPrivacy from '@/locales/kn/privacy.json';
import knAdminOps from '@/locales/kn/adminOps.json';
import knListings from '@/locales/kn/listings.json';
import knNotifications from '@/locales/kn/notifications.json';
import knOpportunities from '@/locales/kn/opportunities.json';
import knProfile from '@/locales/kn/profile.json';
import knRanking from '@/locales/kn/ranking.json';
import knHiring from '@/locales/kn/hiring.json';
import knContact from '@/locales/kn/contact.json';
import knContracts from '@/locales/kn/contracts.json';
import knPackages from '@/locales/kn/packages.json';
import knExplore from '@/locales/kn/explore.json';
import knVoice from '@/locales/kn/voice.json';

import { DEFAULT_LANGUAGE, LANGUAGE_COOKIE, SUPPORTED_LANGUAGES, isSupported, type Language } from './languages';
export { DEFAULT_LANGUAGE, LANGUAGE_COOKIE, SUPPORTED_LANGUAGES, isSupported, type Language };

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
  'workspace',
  'adminCommercial',
  'privacy',
  'adminOps',
  // [FE1] posting composer, response composers, applicants board, voice input, taxonomy picker
  'hiring',
  // [FE2] contact control, contracts, service packages, Hire/Find work menu + outcomes + Discover filters
  'contact',
  'contracts',
  'packages',
  'explore',
  // [Voice interview 2026-09-30]
  'voice',
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
    workspace: enWorkspace,
    adminCommercial: enAdminCommercial,
    privacy: enPrivacy,
    adminOps: enAdminOps,
    hiring: enHiring,
    contact: enContact,
    contracts: enContracts,
    packages: enPackages,
    explore: enExplore,
    voice: enVoice,
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
    workspace: hiWorkspace,
    adminCommercial: hiAdminCommercial,
    privacy: hiPrivacy,
    adminOps: hiAdminOps,
    hiring: hiHiring,
    contact: hiContact,
    contracts: hiContracts,
    packages: hiPackages,
    explore: hiExplore,
    voice: hiVoice,
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
    workspace: teWorkspace,
    adminCommercial: teAdminCommercial,
    privacy: tePrivacy,
    adminOps: teAdminOps,
    hiring: teHiring,
    contact: teContact,
    contracts: teContracts,
    packages: tePackages,
    explore: teExplore,
    voice: teVoice,
  },
  mr: {
    common: mrCommon,
    firstRun: mrFirstRun,
    listings: mrListings,
    opportunities: mrOpportunities,
    discover: mrDiscover,
    activity: mrActivity,
    profile: mrProfile,
    ranking: mrRanking,
    notifications: mrNotifications,
    enquiries: mrEnquiries,
    verification: mrVerification,
    trustSafety: mrTrustSafety,
    reviews: mrReviews,
    partnerships: mrPartnerships,
    commercial: mrCommercial,
    workspace: mrWorkspace,
    adminCommercial: mrAdminCommercial,
    privacy: mrPrivacy,
    adminOps: mrAdminOps,
    hiring: mrHiring,
    contact: mrContact,
    contracts: mrContracts,
    packages: mrPackages,
    explore: mrExplore,
    voice: mrVoice,
  },
  kn: {
    common: knCommon,
    firstRun: knFirstRun,
    listings: knListings,
    opportunities: knOpportunities,
    discover: knDiscover,
    activity: knActivity,
    profile: knProfile,
    ranking: knRanking,
    notifications: knNotifications,
    enquiries: knEnquiries,
    verification: knVerification,
    trustSafety: knTrustSafety,
    reviews: knReviews,
    partnerships: knPartnerships,
    commercial: knCommercial,
    workspace: knWorkspace,
    adminCommercial: knAdminCommercial,
    privacy: knPrivacy,
    adminOps: knAdminOps,
    hiring: knHiring,
    contact: knContact,
    contracts: knContracts,
    packages: knPackages,
    explore: knExplore,
    voice: knVoice,
  },
} as const;


let instance: I18nInstance | null = null;

// [Critique N10] On the server every request gets its OWN instance in the
// request's language (a shared singleton would leak one visitor's language
// into the next). In the browser there is one instance, created on the
// first render with the language the server rendered.
export function getI18n(initialLanguage: Language = DEFAULT_LANGUAGE): I18nInstance {
  if (instance && typeof window !== 'undefined') return instance;
  return createI18n(initialLanguage);
}

/**
 * A fresh instance in `language` (and, in the browser, the one getI18n
 * returns from now on). The provider swaps to one of these to change the
 * language right after hydration: the instance the server-matching HTML
 * was hydrated with is never mutated, so a Suspense boundary that is still
 * hydrating reads the language the server rendered (see provider.tsx).
 */
export function createI18n(language: Language): I18nInstance {
  const initialLanguage = language;
  const i18n = i18next.createInstance();
  void i18n.use(initReactI18next).init({
    resources,
    // resources are bundled: initialise synchronously so the first render
    // (server and client) is already translated
    initAsync: false,
    lng: initialLanguage,
    fallbackLng: DEFAULT_LANGUAGE,
    ns: NAMESPACES,
    defaultNS: 'common',
    interpolation: {
      // React escapes for us; double-escaping mangles Hindi/Telugu text.
      escapeValue: false,
    },
    returnEmptyString: false,
    // [TR042 gap-fix] a missing key falls back to English (already the
    // default above) AND is logged as an operational analytics event
    // instead of failing silently — the fallback itself is never hidden.
    saveMissing: true,
    missingKeyHandler: (_langs, ns, key) => {
      if (typeof window === 'undefined') return;
      void import('@/lib/api').then(({ api }) =>
        api.post('/v1/events', { events: [{ event: 'i18n_fallback', level: 'operational', props: { ns, key } }] }).catch(() => undefined),
      );
    },
  });

  if (typeof window !== 'undefined') instance = i18n;
  return i18n;
}
