/* i18n setup — ADR-010 (shared i18n library, English/Hindi/Telugu at launch).
 *
 * Two rules this file exists to enforce:
 *
 *  1. No user-visible string is written in a component. Every one lives in
 *     `locales/<lang>/<namespace>.json` and is reached by key. FR089 makes
 *     language a person-level preference, so a hardcoded string is not a
 *     cosmetic problem — it is a string one third of the intended audience
 *     cannot read.
 *
 *  2. English is the fallback for every key. Hindi and Telugu files start
 *     empty and fill in over time; an untranslated key renders the English
 *     text rather than a missing-key placeholder, so a partial translation is
 *     never worse than no translation.
 *
 * Typing: `Namespace`/`TranslationKey` below are derived from the English
 * files, so `t('auth:login.title')` is checked at compile time and a renamed
 * key breaks the build instead of silently rendering its own name.
 */

import i18next, { type i18n as I18nInstance } from "i18next";
import { initReactI18next } from "react-i18next";

import enAuth from "@/locales/en/auth.json";
import enCircle from "@/locales/en/circle.json";
import enCommon from "@/locales/en/common.json";
import enDiscover from "@/locales/en/discover.json";
import enMessages from "@/locales/en/messages.json";
import enProfile from "@/locales/en/profile.json";
import hiAuth from "@/locales/hi/auth.json";
import hiCircle from "@/locales/hi/circle.json";
import hiCommon from "@/locales/hi/common.json";
import hiDiscover from "@/locales/hi/discover.json";
import hiMessages from "@/locales/hi/messages.json";
import hiProfile from "@/locales/hi/profile.json";
import teAuth from "@/locales/te/auth.json";
import teCircle from "@/locales/te/circle.json";
import teCommon from "@/locales/te/common.json";
import teDiscover from "@/locales/te/discover.json";
import enHome from "@/locales/en/home.json";
import hiHome from "@/locales/hi/home.json";
import teHome from "@/locales/te/home.json";
import teMessages from "@/locales/te/messages.json";
import teProfile from "@/locales/te/profile.json";
import enVerify from "@/locales/en/verify.json";
import hiVerify from "@/locales/hi/verify.json";
import teVerify from "@/locales/te/verify.json";
import enMember from "@/locales/en/member.json";
import hiMember from "@/locales/hi/member.json";
import teMember from "@/locales/te/member.json";
import enRm from "@/locales/en/rm.json";
import hiRm from "@/locales/hi/rm.json";
import teRm from "@/locales/te/rm.json";
import enHoroscope from "@/locales/en/horoscope.json";
import hiHoroscope from "@/locales/hi/horoscope.json";
import teHoroscope from "@/locales/te/horoscope.json";
import enBilling from "@/locales/en/billing.json";
import hiBilling from "@/locales/hi/billing.json";
import teBilling from "@/locales/te/billing.json";
// [Owner walkthrough, 2026-09-30] The agent (marriage broker) screens' text
// was written in all three languages but never registered here, so every
// agent screen showed raw keys ("workspace.title", "status.verified").
import enAgents from "@/locales/en/agents.json";
import hiAgents from "@/locales/hi/agents.json";
import teAgents from "@/locales/te/agents.json";
import enHelp from "@/locales/en/help.json";
import hiHelp from "@/locales/hi/help.json";
import teHelp from "@/locales/te/help.json";
import enWedding from "@/locales/en/wedding.json";
import hiWedding from "@/locales/hi/wedding.json";
import teWedding from "@/locales/te/wedding.json";
import enGuides from "@/locales/en/guides.json";
import hiGuides from "@/locales/hi/guides.json";
import teGuides from "@/locales/te/guides.json";

export const SUPPORTED_LANGUAGES = ["en", "hi", "te"] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = "en";

/** Namespaces map 1:1 to files in `locales/<lang>/`. */
export const NAMESPACES = [
  "common",
  "auth",
  "profile",
  "circle",
  "discover",
  "messages",
  "home",
  "verify",
  "member",
  "rm",
  "horoscope",
  "billing",
  "agents",
  "help",
  "wedding",
  "guides",
] as const;
export type Namespace = (typeof NAMESPACES)[number];

const resources = {
  en: {
    common: enCommon,
    auth: enAuth,
    profile: enProfile,
    circle: enCircle,
    discover: enDiscover,
    messages: enMessages,
    home: enHome,
    verify: enVerify,
    member: enMember,
    rm: enRm,
    horoscope: enHoroscope,
    billing: enBilling,
    agents: enAgents,
    help: enHelp,
    wedding: enWedding,
    guides: enGuides,
  },
  hi: {
    common: hiCommon,
    auth: hiAuth,
    profile: hiProfile,
    circle: hiCircle,
    discover: hiDiscover,
    messages: hiMessages,
    home: hiHome,
    verify: hiVerify,
    member: hiMember,
    rm: hiRm,
    horoscope: hiHoroscope,
    billing: hiBilling,
    agents: hiAgents,
    help: hiHelp,
    wedding: hiWedding,
    guides: hiGuides,
  },
  te: {
    common: teCommon,
    auth: teAuth,
    profile: teProfile,
    circle: teCircle,
    discover: teDiscover,
    messages: teMessages,
    home: teHome,
    verify: teVerify,
    member: teMember,
    rm: teRm,
    horoscope: teHoroscope,
    billing: teBilling,
    agents: teAgents,
    help: teHelp,
    wedding: teWedding,
    guides: teGuides,
  },
} as const;

export function isSupported(
  value: string | null | undefined,
): value is Language {
  return !!value && (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}

let instance: I18nInstance | null = null;

export function getI18n(
  initialLanguage: Language = DEFAULT_LANGUAGE,
): I18nInstance {
  if (instance) return instance;

  const i18n = i18next.createInstance();
  void i18n.use(initReactI18next).init({
    resources,
    lng: initialLanguage,
    fallbackLng: DEFAULT_LANGUAGE,
    ns: NAMESPACES,
    defaultNS: "common",
    interpolation: {
      // React escapes for us; double-escaping mangles Hindi/Telugu text.
      escapeValue: false,
    },
    returnEmptyString: false,
  });

  instance = i18n;
  return i18n;
}
