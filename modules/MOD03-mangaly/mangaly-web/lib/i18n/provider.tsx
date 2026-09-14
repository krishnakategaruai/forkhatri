'use client';

import { I18nextProvider } from 'react-i18next';
import { useEffect, useState } from 'react';

import {
  DEFAULT_LANGUAGE,
  type Language,
  getI18n,
  isSupported,
} from './config';

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
  }, [i18n]);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

export function setPreferredLanguage(lang: Language): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Non-fatal: the choice just will not survive a reload.
  }
  document.documentElement.lang = lang;
}
