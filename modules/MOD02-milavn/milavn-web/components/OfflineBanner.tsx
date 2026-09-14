'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

/* FR084/UI18: slim, non-blocking, announced once, auto-dismisses on reconnect. */
export default function OfflineBanner() {
  const [offline, setOffline] = useState(false);
  const { t } = useTranslation();
  useEffect(() => {
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    setOffline(typeof navigator !== 'undefined' && !navigator.onLine);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, []);
  if (!offline) return null;
  return (
    <div className="offline" role="status" aria-live="polite">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M2 8.5a15 15 0 0 1 20 0M5.5 12.5a10 10 0 0 1 13 0M9 16.5a5 5 0 0 1 6 0M12 20h.01M3 3l18 18" /></svg>
      {t('state.offline')}
    </div>
  );
}
