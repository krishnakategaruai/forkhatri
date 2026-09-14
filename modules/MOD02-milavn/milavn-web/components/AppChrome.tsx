'use client';

/* The persistent shell: routing guard (FR076 launch routing), offline banner
 * (FR084), and the floating nav (FR083). Chromeless on welcome/onboarding/
 * public pages — a nav bar implies places you can go before you can go anywhere. */

import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import OfflineBanner from '@/components/OfflineBanner';
import SideNav from '@/components/SideNav';
import TabBar from '@/components/TabBar';
import { api } from '@/lib/api';
import { useIdentity } from '@/lib/identity';

const CHROMELESS_PREFIXES = ['/welcome', '/onboarding', '/a/', '/create', '/organizer/', '/admin', '/chats/'];
// On a wide screen the rail stays for everything except the launch/onboarding flow, so a person never loses their way.
const RAILLESS_PREFIXES = ['/welcome', '/onboarding'];

export default function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { ready, identity, profile } = useIdentity();
  const { t } = useTranslation();

  const isPublic = pathname.startsWith('/a/');
  const chromeless = CHROMELESS_PREFIXES.some((p) => pathname.startsWith(p));
  const railless = RAILLESS_PREFIXES.some((p) => pathname.startsWith(p)) || (!identity && isPublic);

  // Appearance (UX17): an explicit light/dark choice persists across full page
  // loads; "System" leaves the attribute off so prefers-color-scheme decides.
  useEffect(() => {
    try {
      const saved = localStorage.getItem('milavn.theme');
      if (saved === 'light' || saved === 'dark') document.documentElement.dataset.theme = saved;
    } catch { /* ignore */ }
  }, []);

  // Presence heartbeat (chat: "active now"): a timestamp, never a location.
  useEffect(() => {
    if (!identity) return;
    let alive = true;
    const beat = () => { if (alive) api('/presence', { body: {} }).catch(() => undefined); };
    beat();
    const id = setInterval(beat, 30000);
    return () => { alive = false; clearInterval(id); };
  }, [identity]);

  useEffect(() => {
    if (!ready || isPublic) return;
    if (!identity && pathname !== '/welcome') router.replace('/welcome');
    // A moderator works the console without a participant profile (UX20 is operations-facing).
    else if (identity && profile === null && pathname !== '/onboarding' && pathname !== '/welcome' && !pathname.startsWith('/admin')) router.replace('/onboarding');
    else if (identity && profile && (pathname === '/welcome' || pathname === '/onboarding')) router.replace('/');
  }, [ready, identity, profile, pathname, router, isPublic]);

  if (!ready && !isPublic) {
    return (
      <div className="shell shell--chromeless" aria-busy="true">
        <div className="screen" style={{ alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
          <div className="brand-mark" style={{ width: 64, height: 64, fontSize: '1.6rem', borderRadius: 20 }}>M</div>
          <p className="caption">{t('app.tagline')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${chromeless ? 'shell shell--chromeless' : 'shell'}${railless ? ' shell--railless' : ''}`}>
      {!railless && <SideNav />}
      <div className="shell__content">
        <OfflineBanner />
        {children}
      </div>
      {!chromeless && <TabBar />}
    </div>
  );
}
