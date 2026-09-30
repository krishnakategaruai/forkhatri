'use client';

import { I18nextProvider } from 'react-i18next';
import { useEffect, useState } from 'react';

import {
  DEFAULT_LANGUAGE,
  type Language,
  getI18n,
  isSupported,
} from './config';
import { IDENTITY_API } from '../platform';

const STORAGE_KEY = 'mangaly.language';

/** Wraps the app so every component can reach `useTranslation()`.
 *
 * Language resolution order: the person's saved choice, then the device
 * locale, then English. FR089 makes this a person-level profile field, so once
 * a profile exists the server value takes over from this local one — this is
 * the pre-login fallback, not the source of truth.
 */
export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [i18n] = useState(() => getI18n(DEFAULT_LANGUAGE));

  useEffect(() => {
    let next: Language = DEFAULT_LANGUAGE;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (isSupported(saved)) {
        next = saved;
      } else {
        const device = navigator.language?.split('-')[0];
        if (isSupported(device)) next = device;
      }
    } catch {
      // Private mode or blocked storage: fall through to English rather than
      // failing to render.
    }
    if (i18n.language !== next) void i18n.changeLanguage(next);
    document.documentElement.lang = next;

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
