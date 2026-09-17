'use client';

import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { entranceUrl, mangalyUrl, redirectToEntrance } from '@/lib/platform';

/* [TR16, 2026-09-14] What Mangaly's retired /login, /signup, /otp and /reset
 * routes render: an immediate hand-off to the ForKhatri entrance.
 *
 * `return_to` is Mangaly's home, never the current URL: returning a signed-in
 * member to /login would bounce them straight back here in a loop. The link is
 * a fallback for the moment before the navigation starts (or if script is
 * blocked). */

export default function EntranceRedirect() {
  const { t } = useTranslation('common');

  useEffect(() => {
    redirectToEntrance(mangalyUrl('/'));
  }, []);

  return (
    <main className="screen screen--centered">
      <span className="brand-mark brand-mark--lg" aria-hidden="true">
        m
      </span>
      <p className="caption" role="status" aria-live="polite">
        {t('common:platform.redirecting')}
      </p>
      <a className="link" href={entranceUrl()}>
        {t('common:platform.name')}
      </a>
    </main>
  );
}
