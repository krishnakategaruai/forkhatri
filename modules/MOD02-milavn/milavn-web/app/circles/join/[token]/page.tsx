'use client';

/* Joining from a shared invite link (owner, 2026-09-29: adding people to a circle). The link is
 * the approval, so one tap joins — the same page shape as the circle itself, with its cover. */

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import CircleCover, { coverKind } from '@/components/CircleCover';
import { ErrorState } from '@/components/States';
import { api, ApiError, type Circle } from '@/lib/api';

type Preview = { valid: boolean; circle: (Circle & { cover_url?: string | null }) | null; already_member?: boolean };

export default function JoinByLinkPage() {
  const { t } = useTranslation();
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const [p, setP] = useState<Preview | null>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [asked, setAsked] = useState(false);

  useEffect(() => {
    api<Preview>(`/circles/join/${token}`).then(setP).catch((e) => {
      if (e instanceof ApiError && e.status === 404) setP({ valid: false, circle: null });
      else setError(true);
    });
  }, [token]);

  const join = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await api<{ status: string; id?: string; circle_id?: string }>(`/circles/join/${token}`, { body: {} });
      if (r.status === 'pending') { setMessage(t('join.asked')); setAsked(true); setBusy(false); return; }
      router.replace(`/circles/${r.id ?? r.circle_id}`);
    } catch (e) { setMessage(e instanceof ApiError ? e.message : t('state.error')); setBusy(false); }
  };

  const c = p?.circle;
  return (
    <main className="screen cx">
      {error && <ErrorState onRetry={() => location.reload()} />}
      {!p && !error && <div className="sk" style={{ height: 220, borderRadius: 20 }} />}
      {p && !p.valid && (
        <div className="stack" style={{ gap: 12, paddingTop: 40 }}>
          <h1 className="cx-title" style={{ fontSize: '1.75rem' }}>{t('joinLink.invalidTitle')}</h1>
          <p className="cx-caption" style={{ margin: 0 }}>{t('joinLink.invalidBody')}</p>
          <Link href="/circles" className="cx-btn cx-btn--quiet cx-btn--lg">{t('joinLink.browse')}</Link>
        </div>
      )}
      {p && p.valid && c && (
        <div className="stack" style={{ gap: 16 }}>
          {coverKind(c.cover_url) === 'photo' && (
            <div style={{ borderRadius: 20, overflow: 'hidden' }}>
              <CircleCover variant="card" name={c.name} coverUrl={c.cover_url} />
            </div>
          )}
          <span className="cx-label">{t('joinLink.invited')}</span>
          <h1 className="cx-title">{c.name}</h1>
          <span className="cx-caption">{[c.circle_type === 'public' ? t('circles.openToAll') : c.type_label, c.locality_label, t('circles.members', { count: c.member_count })].filter(Boolean).join(' · ')}</span>
          {c.description && <p className="cx-desc is-open">{c.description}</p>}
          {p.already_member ? (
            <Link href={`/circles/${c.id}`} className="cx-btn cx-btn--quiet cx-btn--lg">{t('joinLink.open')}</Link>
          ) : (
            <button className="cx-btn cx-btn--primary cx-btn--lg" disabled={busy || asked} onClick={join}>{asked ? t('join.waiting') : t('joinLink.join')}</button>
          )}
          {message && <p className="cx-caption" style={{ margin: 0, color: asked ? undefined : 'var(--danger)' }}>{message}</p>}
        </div>
      )}
    </main>
  );
}
