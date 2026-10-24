'use client';

import { I18nextProvider } from 'react-i18next';
import { useEffect, useState } from 'react';

import { setApiLanguage } from '@/lib/api';
import { IDENTITY_API } from '@/lib/platform';
import { DEFAULT_LANGUAGE, getI18n, isSupported, loadLanguage, needsLoad, type Language } from './config';

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

    // [Owner, 2026-09-27] The language chosen in ForKhatri is the person's
    // language in every module: read it from their ForKhatri account when
    // Milavn opens and whenever the tab comes back into view. The local value
    // above is only the first paint and the signed-out fallback.
    let alive = true;
    const sync = async () => {
      const lang = await accountLanguage();
      if (alive && lang && lang !== getI18n().language) applyLanguage(lang);
    };
    void sync();
    const onVisible = () => { if (document.visibilityState === 'visible') void sync(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => { alive = false; document.removeEventListener('visibilitychange', onVisible); };
  }, [i18n]);
  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

let wanted: Language = DEFAULT_LANGUAGE;

export function applyLanguage(lang: Language): void {
  const i18n = getI18n();
  wanted = lang;
  if (i18n.language !== lang) {
    // Marathi/Kannada text arrives on first use; switch once it is here, unless the person picked another language meanwhile.
    if (needsLoad(lang)) void loadLanguage(lang).then(() => { if (wanted === lang) void i18n.changeLanguage(lang); });
    else void i18n.changeLanguage(lang);
  }
  setApiLanguage(lang);
  if (typeof document !== 'undefined') document.documentElement.lang = lang;
  try { localStorage.setItem(STORAGE_KEY, lang); } catch { /* ignore */ }
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

/** A language the person chose inside Milavn: applied here and saved to their
 *  ForKhatri account, which every module reads. Best effort. */
export function chooseLanguage(lang: Language): void {
  applyLanguage(lang);
  void fetch(`${IDENTITY_API}/v1/me`, {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preferred_language: lang }),
  }).catch(() => {});
}
