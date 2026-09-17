'use client';

/* The persistent shell: routing guard (FR076 launch routing), offline banner
 * (FR084), and the floating nav (FR083). Chromeless on welcome/onboarding/
 * public pages — a nav bar implies places you can go before you can go anywhere. */

import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import OfflineBanner from '@/components/OfflineBanner';
import SideNav from '@/components/SideNav';
import { ErrorState } from '@/components/States';
import TabBar from '@/components/TabBar';
import { api } from '@/lib/api';
import { appUrl } from '@/lib/base-path';
import { useIdentity } from '@/lib/identity';
import { goToEntrance } from '@/lib/platform';

const CHROMELESS_PREFIXES = ['/welcome', '/onboarding', '/a/', '/create', '/organizer/', '/admin', '/chats/', '/pay/'];
// On a wide screen the rail stays for everything except the launch/onboarding flow, so a person never loses their way.
const RAILLESS_PREFIXES = ['/welcome', '/onboarding'];

export default function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { ready, identity, profile, unavailable, reload } = useIdentity();
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
    if (!ready || isPublic || unavailable) return;
    // [ParentApp TR16] Signed out → the ForKhatri entrance signs the person in and returns them here.
    // /welcome is the old launch screen: come back to Milavn's home, not to it.
    if (!identity) goToEntrance(pathname === '/welcome' ? appUrl('/') : undefined);
    // A moderator works the console without a participant profile (UX20 is operations-facing).
    else if (profile === null && pathname !== '/onboarding' && !pathname.startsWith('/admin')) router.replace('/onboarding');
    else if (profile && (pathname === '/welcome' || pathname === '/onboarding')) router.replace('/');
  }, [ready, identity, profile, pathname, router, isPublic, unavailable]);

  if (ready && unavailable && !isPublic) {
    return (
      <div className="shell shell--chromeless">
        <div className="screen" style={{ alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
          <div className="brand-mark" style={{ width: 64, height: 64, fontSize: '1.6rem', borderRadius: 20 }}>M</div>
          <ErrorState message={t('platform.unavailable')} onRetry={() => void reload()} />
        </div>
      </div>
    );
  }

  // Signed out on a member-only page: hold the splash while the entrance loads, never flash member UI.
  if ((!ready || !identity) && !isPublic) {
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
