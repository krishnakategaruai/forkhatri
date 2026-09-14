'use client';

/* Floating, translucent 5-tab bar with a shape-morphing active pill (UX03/UI03).
 * The pill slides and reshapes with the spring token on every tab switch —
 * the single most-repeated animated moment in the app. */

import { CalendarDays, Home, UserRound, Users } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLayoutEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';


export const TABS = [
  { href: '/', key: 'home', icon: (a: boolean) => <Home size={22} strokeWidth={a ? 2.2 : 1.7} aria-hidden="true" /> },
  { href: '/circles', key: 'circles', icon: (a: boolean) => <Users size={22} strokeWidth={a ? 2.2 : 1.7} aria-hidden="true" /> },
  { href: '/calendar', key: 'calendar', icon: (a: boolean) => <CalendarDays size={22} strokeWidth={a ? 2.2 : 1.7} aria-hidden="true" /> },
  { href: '/me', key: 'profile', icon: (a: boolean) => <UserRound size={22} strokeWidth={a ? 2.2 : 1.7} aria-hidden="true" /> },
];

export default function TabBar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const navRef = useRef<HTMLElement>(null);
  const [pill, setPill] = useState<{ left: number; width: number } | null>(null);

  const activeIndex = TABS.findIndex((tab) => (tab.href === '/' ? pathname === '/' : pathname.startsWith(tab.href)));

  useLayoutEffect(() => {
    const nav = navRef.current;
    if (!nav || activeIndex < 0) return;
    const el = nav.querySelectorAll<HTMLElement>('.nav__tab')[activeIndex];
    if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth });
  }, [activeIndex]);

  return (
    <nav className="nav" aria-label="Primary" ref={navRef}>
      {pill && activeIndex >= 0 && <span className="nav__pill" style={{ left: pill.left, width: pill.width }} aria-hidden="true" />}
      {TABS.map((tab, i) => {
        const active = i === activeIndex;
        return (
          <Link key={tab.href} href={tab.href} className="nav__tab" aria-current={active ? 'page' : undefined}>
            {tab.icon(active)}
            <span>{t(`nav.${tab.key}`)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
