'use client';

import { useTranslation } from 'react-i18next';

import { entranceUrl } from '@/lib/platform';

/* [TR16/TR22, 2026-09-14] The persistent way back to the ForKhatri hub.
 *
 * Mangaly is one module inside ForKhatri, so every top-level Mangaly surface
 * carries a small, quiet route home. A plain <a> rather than next/link: the
 * hub is a different zone (a different app in development, a different
 * basePath in production), and links between zones are full navigations.
 * Styled with Mangaly's own `.icon-btn` chrome so it reads as part of this
 * top bar, not as a foreign widget dropped into it. */

export default function ForKhatriHubLink() {
  const { t } = useTranslation('common');

  return (
    <a
      className="icon-btn icon-btn--text hub-link"
      href={entranceUrl()}
      aria-label={t('common:platform.backToHub')}
      title={t('common:platform.backToHub')}
    >
      <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
        <g fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round">
          <rect x="4" y="4" width="6.5" height="6.5" rx="1.8" />
          <rect x="13.5" y="4" width="6.5" height="6.5" rx="1.8" />
          <rect x="4" y="13.5" width="6.5" height="6.5" rx="1.8" />
          <rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.8" />
        </g>
      </svg>
      <span>{t('common:platform.name')}</span>
    </a>
  );
}
