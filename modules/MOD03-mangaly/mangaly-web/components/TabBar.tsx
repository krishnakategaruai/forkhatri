'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslation } from 'react-i18next';

/* Bottom tab bar — the module's primary navigation (UX/UI "nav shell").
   Icons are 1.5px line icons, switching to a filled variant when active,
   per 04-ui.md's iconography convention. Every tab meets the 48dp target.
   [2026-09-14] Labels were hardcoded English strings even though
   `common:nav.*` already existed, translated, and unused — the tab bar is
   the one piece of chrome visible on every single screen, so it was the
   most visible part of the app to never actually respect a language
   choice. Now sourced from `common:nav.*` like everything else. */

type Tab = {
  href: string;
  labelKey: string;
  icon: (active: boolean) => React.ReactNode;
};

const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

const TABS: Tab[] = [
  {
    href: '/',
    labelKey: 'common:nav.home',
    icon: (active) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          {...stroke}
          fill={active ? 'currentColor' : 'none'}
          fillOpacity={active ? 0.18 : 0}
          d="M3 10.2 12 3.5l9 6.7V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"
        />
      </svg>
    ),
  },
  {
    href: '/discover',
    labelKey: 'common:nav.discover',
    icon: (active) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle
          {...stroke}
          cx="11"
          cy="11"
          r="7"
          fill={active ? 'currentColor' : 'none'}
          fillOpacity={active ? 0.18 : 0}
        />
        <path {...stroke} d="m16.5 16.5 4 4" />
      </svg>
    ),
  },
  {
    href: '/circle',
    labelKey: 'common:nav.circle',
    icon: (active) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle
          {...stroke}
          cx="9"
          cy="8"
          r="3.2"
          fill={active ? 'currentColor' : 'none'}
          fillOpacity={active ? 0.18 : 0}
        />
        <path {...stroke} d="M3.5 19.5a5.5 5.5 0 0 1 11 0" />
        <path {...stroke} d="M16 6.2a3 3 0 0 1 0 5.6M17.5 19.5a5.4 5.4 0 0 0-2-4.2" />
      </svg>
    ),
  },
  {
    href: '/messages',
    labelKey: 'common:nav.messages',
    icon: (active) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          {...stroke}
          fill={active ? 'currentColor' : 'none'}
          fillOpacity={active ? 0.18 : 0}
          d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-4.4 3.3A.4.4 0 0 1 4 20z"
        />
      </svg>
    ),
  },
  {
    href: '/me',
    labelKey: 'common:nav.me',
    icon: (active) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle
          {...stroke}
          cx="12"
          cy="8"
          r="3.6"
          fill={active ? 'currentColor' : 'none'}
          fillOpacity={active ? 0.18 : 0}
        />
        <path {...stroke} d="M5 20a7 7 0 0 1 14 0" />
      </svg>
    ),
  },
];

/* Routes that are outside the signed-in shell. Showing a nav bar on a login
   screen implies places you can go before you can go anywhere. */
const CHROMELESS = ['/login', '/signup', '/reset', '/otp', '/profile/create'];

export default function TabBar() {
  const pathname = usePathname();
  const { t } = useTranslation('common');

  if (CHROMELESS.includes(pathname)) return null;

  return (
    <nav className="tabbar" aria-label="Primary">
      {TABS.map((tab) => {
        const active =
          pathname === tab.href || (tab.href !== '/' && pathname.startsWith(`${tab.href}/`));
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className="tab"
            aria-current={active ? 'page' : undefined}
          >
            {tab.icon(active)}
            <span>{t(tab.labelKey)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
