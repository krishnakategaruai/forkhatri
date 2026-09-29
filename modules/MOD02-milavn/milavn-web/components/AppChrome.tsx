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
import { followSystemTheme } from '@/lib/theme';

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

  // Appearance (UX17) is applied before first paint by the inline script in
  // app/layout.tsx; here Milavn keeps following the device while "System" is chosen.
  useEffect(() => followSystemTheme(), []);

  // Presence heartbeat (chat: "active now"): a timestamp, never a location.
  // Keyed on the member id: a fresh identity object for the same person must not start a second heartbeat.
  const memberId = identity?.member_id;
  useEffect(() => {
    if (!memberId) return;
    let alive = true;
    const beat = () => { if (alive) api('/presence', { body: {} }).catch(() => undefined); };
    beat();
    const id = setInterval(beat, 30000);
    return () => { alive = false; clearInterval(id); };
  }, [memberId]);

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
      <div className="shell shell--chromeless shell--railless">
        <div className="splash">
          <div className="brand-mark splash__mark">M</div>
          <ErrorState message={t('platform.unavailable')} onRetry={() => void reload()} />
        </div>
      </div>
    );
  }

  // Signed out on a member-only page: hold the splash while the entrance loads, never flash member UI.
  // Railless too: on a wide screen the shell is a two-column grid and the splash would sit in the rail column.
  if ((!ready || !identity) && !isPublic) {
    return (
      <div className="shell shell--chromeless shell--railless" aria-busy="true">
        <div className="splash">
          <div className="brand-mark splash__mark splash__mark--breathe">M</div>
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
