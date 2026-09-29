'use client';

import { useSyncExternalStore } from 'react';
import { useTranslation } from 'react-i18next';

import { isOutage, retryAfterOutage, subscribeOutage } from '@/lib/outage';

/* [ForKhatri TR15/TR16] The single retry state every Mangaly screen shows when
 * it cannot load because MangalyService or ForKhatri sign-in is unreachable.
 * Mounted once, in the root layout, around the page — pages do not render
 * their own copy. See `lib/outage.ts` for what triggers it and why. */

export default function OutageGate({ children }: { children: React.ReactNode }) {
  const down = useSyncExternalStore(subscribeOutage, isOutage, () => false);
  const { t } = useTranslation('common');

  if (!down) return <>{children}</>;

  return (
    <main className="screen screen--centered">
      <span className="brand-mark brand-mark--lg" aria-hidden="true">
        m
      </span>
      <p className="caption" role="status" aria-live="polite" style={{ textAlign: 'center', maxWidth: 320 }}>
        {t('common:platform.unavailable')}
      </p>
      <button type="button" className="cta" onClick={retryAfterOutage}>
        {t('common:action.retry')}
      </button>
    </main>
  );
}
