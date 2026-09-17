'use client';

/* Former launch / development identity chooser (FR076-FR080 are ForKhatri
 * platform flows). Since the platform identity landed (ParentApp TR16), Milavn
 * never picks or signs in a member: a signed-out visit is sent to the
 * ForKhatri entrance by AppChrome (returning to Milavn's home), and a
 * signed-in visit is routed on to home/onboarding. The route is kept so old
 * links and bookmarks still land somewhere sensible. */

import { useTranslation } from 'react-i18next';

import { FORKHATRI_ENTRANCE_URL } from '@/lib/platform';

export default function WelcomePage() {
  const { t } = useTranslation();
  return (
    <main className="screen" style={{ minHeight: '100vh', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }} aria-busy="true">
      <span className="brand-mark brand-mark--glow">M</span>
      <p className="caption">{t('platform.redirecting')}</p>
      <a className="link" href={`${FORKHATRI_ENTRANCE_URL}/`}>{t('platform.backToHub')}</a>
    </main>
  );
}
