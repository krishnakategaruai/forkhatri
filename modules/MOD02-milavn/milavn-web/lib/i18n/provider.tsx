'use client';

import { I18nextProvider } from 'react-i18next';
import { useEffect, useState } from 'react';

import { setApiLanguage } from '@/lib/api';
import { DEFAULT_LANGUAGE, getI18n, isSupported, type Language } from './config';

const STORAGE_KEY = 'milavn.language';

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [i18n] = useState(() => getI18n(DEFAULT_LANGUAGE));
  useEffect(() => {
    let next: Language = DEFAULT_LANGUAGE;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (isSupported(saved)) next = saved;
      else {
        const device = navigator.language?.split('-')[0];
        if (isSupported(device)) next = device;
      }
    } catch { /* ignore */ }
    applyLanguage(next);
  }, [i18n]);
  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

export function applyLanguage(lang: Language): void {
  const i18n = getI18n();
  if (i18n.language !== lang) void i18n.changeLanguage(lang);
  setApiLanguage(lang);
  if (typeof document !== 'undefined') document.documentElement.lang = lang;
  try { localStorage.setItem(STORAGE_KEY, lang); } catch { /* ignore */ }
}
