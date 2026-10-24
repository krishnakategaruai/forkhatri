'use client';

import { I18nextProvider } from 'react-i18next';
import { useEffect, useLayoutEffect, useState } from 'react';

import {
  DEFAULT_LANGUAGE,
  type Language,
  getI18n,
  isSupported,
} from './config';
import { IDENTITY_API } from '../platform';

const STORAGE_KEY = 'mangaly.language';

/** Set on <html> by the inline script in app/layout.tsx when the saved (or
 * device) language is not English: the page stays hidden until that language
 * is applied, then this attribute is removed. */
export const LANGUAGE_PENDING_ATTR = 'data-i18n-pending';

/** The language to show first: the person's saved choice, then the device
 * locale, then English. Mirrors the inline script in app/layout.tsx. */
function initialLanguage(): Language {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (isSupported(saved)) return saved;
    const device = navigator.language?.split('-')[0];
    if (isSupported(device)) return device;
  } catch {
    // Private mode or blocked storage: fall through to English rather than
    // failing to render.
  }
  return DEFAULT_LANGUAGE;
}

function revealPage() {
  document.documentElement.removeAttribute(LANGUAGE_PENDING_ATTR);
}

/** Wraps the app so every component can reach `useTranslation()`.
 *
 * Language resolution order: the person's saved choice, then the device
 * locale, then English. FR089 makes this a person-level profile field, so once
 * a profile exists the server value takes over from this local one — this is
 * the pre-login fallback, not the source of truth.
 */
export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [i18n] = useState(() => getI18n(DEFAULT_LANGUAGE));

  /* [D17, 2026-10-06] "The Telugu screen showed English for a moment."
     Cause: the server always renders English (it cannot read the browser's
     saved choice), the client hydrates in English to match, and the saved
     language used to be applied in a useEffect, i.e. AFTER the browser had
     already painted the English page. Any full load (a reload, a dev-mode
     refresh after a resize) therefore flashed English.
     Fix: the inline script in app/layout.tsx hides the page before the first
     paint when the saved language is not English; here the language is
     applied in a layout effect (before the hydrated page is painted) and the
     page is revealed only once the chosen language is in place. Hydration
     itself still happens in English, so there is no hydration mismatch. */
  useLayoutEffect(() => {
    const next = initialLanguage();
    document.documentElement.lang = next;
    if (i18n.language === next) {
      revealPage();
      return;
    }
    let done = false;
    const reveal = () => {
      if (done) return;
      done = true;
      // One frame later, so React has committed the re-render in the new language.
      requestAnimationFrame(revealPage);
    };
    void i18n.changeLanguage(next).then(reveal, reveal);
    // Never leave the page hidden if a language file is slow to arrive.
    const safety = window.setTimeout(reveal, 2000);
    return () => window.clearTimeout(safety);
  }, [i18n]);

  useEffect(() => {
    // [Owner, 2026-09-27] The language chosen in ForKhatri is the person's
    // language everywhere: read it from their ForKhatri account (identity
    // service) when Mangalya opens, and again whenever the tab comes back into
    // view (they may have changed it in ForKhatri meanwhile). The local value
    // above is only the first paint and the signed-out fallback.
    let alive = true;
    const syncFromAccount = async () => {
      const lang = await accountLanguage();
      if (!alive || !lang || lang === i18n.language) return;
      void i18n.changeLanguage(lang);
      document.documentElement.lang = lang;
      try {
        localStorage.setItem(STORAGE_KEY, lang);
      } catch {
        // Non-fatal.
      }
    };
    void syncFromAccount();
    const onVisible = () => {
      if (document.visibilityState === 'visible') void syncFromAccount();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      alive = false;
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [i18n]);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

/** The signed-in person's language from their ForKhatri account, or null. */
async function accountLanguage(): Promise<Language | null> {
  try {
    const res = await fetch(`${IDENTITY_API}/v1/session`, { credentials: 'include', cache: 'no-store' });
    if (!res.ok) return null;
    const body = (await res.json()) as { member?: { preferred_language?: string } };
    const lang = body.member?.preferred_language;
    return isSupported(lang) ? lang : null;
  } catch {
    return null;
  }
}

export function setPreferredLanguage(lang: Language): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Non-fatal: the choice just will not survive a reload.
  }
  document.documentElement.lang = lang;
  // A choice made in Mangalya is the person's choice everywhere: save it to
  // their ForKhatri account, which every module reads. Best effort — the
  // visible switch never waits on it.
  void fetch(`${IDENTITY_API}/v1/me`, {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preferred_language: lang }),
  }).catch(() => {});
}
