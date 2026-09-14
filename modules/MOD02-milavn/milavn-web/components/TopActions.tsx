'use client';

/* Header actions shared by the main screens, in the owner's fixed order:
 * [People] · [Alerts bell with unread count] · [Profile avatar — always last].
 * Alerts are not a navigation destination; they live here. */

import { Bell, Users } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { getUnread, resolveMediaUrl } from '@/lib/api';
import { useIdentity } from '@/lib/identity';

export default function TopActions({ people = false }: { people?: boolean }) {
  const { t } = useTranslation();
  const { identity, profile } = useIdentity();
  const pathname = usePathname();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!identity) return;
    let alive = true;
    const tick = () => getUnread().then((r) => alive && setUnread(r.unread)).catch(() => undefined);
    tick();
    const id = setInterval(tick, 20000);
    return () => { alive = false; clearInterval(id); };
  }, [identity, pathname]);

  const avatar = resolveMediaUrl(profile?.photo_url ?? identity?.avatar ?? null);

  return (
    <div className="row" style={{ gap: 8 }}>
      {people && (
        <Link href="/people" className="icon-btn" aria-label={t('people.title')}><Users size={20} strokeWidth={1.8} aria-hidden="true" /></Link>
      )}
      <Link href="/notifications" className="icon-btn bell" aria-label={unread > 0 ? `${t('nav.notifications')} · ${unread}` : t('nav.notifications')}>
        <Bell size={20} strokeWidth={1.8} aria-hidden="true" />
        {unread > 0 && <span className="bell__badge">{unread > 9 ? '9+' : unread}</span>}
      </Link>
      {identity && (
        <Link href="/me" className="avatar-btn" aria-label={t('nav.profile')} aria-current={pathname === '/me' ? 'page' : undefined}>
          {avatar ? <img className="avatar avatar--lg" src={avatar} alt="" /> : <span className="avatar avatar--lg" />}
        </Link>
      )}
    </div>
  );
}
