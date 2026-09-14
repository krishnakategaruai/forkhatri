'use client';

/* Desktop navigation rail (≥ 900px). The phone keeps the floating tab bar; on a
 * wide screen the same five destinations live in a left rail with the brand,
 * the primary "Make something happen" action and the signed-in person, so the
 * app reads as a product on a laptop rather than a phone column in a void. */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslation } from 'react-i18next';

import { TABS } from '@/components/TabBar';
import { Users } from 'lucide-react';
import { resolveMediaUrl } from '@/lib/api';
import { useIdentity } from '@/lib/identity';

export default function SideNav() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { identity, profile } = useIdentity();
  const activeIndex = TABS.findIndex((tab) => (tab.href === '/' ? pathname === '/' : pathname.startsWith(tab.href)));

  return (
    <aside className="sidenav" aria-label="Primary">
      <Link href="/" className="sidenav__brand">
        <span className="brand-mark brand-mark--glow">M</span>
        <span><b>{t('app.name')}</b><span className="caption" style={{ display: 'block' }}>{t('app.tagline')}</span></span>
      </Link>
      <Link href="/create" className="btn btn--primary btn--glow sidenav__cta"><span aria-hidden="true">＋</span> {t('home.makeSomething')}</Link>
      <nav className="sidenav__list">
        {TABS.map((tab, i) => {
          const active = i === activeIndex;
          return (
            <Link key={tab.href} href={tab.href} className="sidenav__item" aria-current={active ? 'page' : undefined}>
              {tab.icon(active)}
              <span className="grow">{t(`nav.${tab.key}`)}</span>
            </Link>
          );
        })}
        <Link href="/people" className="sidenav__item" aria-current={pathname.startsWith('/people') ? 'page' : undefined}>
          <Users size={22} strokeWidth={1.7} aria-hidden="true" />
          <span className="grow">{t('people.title')}</span>
        </Link>
      </nav>
      {identity && (
        <Link href="/me" className="sidenav__me">
          {identity.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(identity.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
          <span className="grow truncate"><b className="truncate" style={{ display: 'block' }}>{identity.display_name}</b><span className="caption">{profile?.locality_locality ?? profile?.locality_city ?? `@${identity.handle}`}</span></span>
        </Link>
      )}
    </aside>
  );
}
