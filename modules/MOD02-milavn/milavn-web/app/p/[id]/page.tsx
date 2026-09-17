'use client';

/* Person page (beyond-MVP). Everything shown is either what the person chose
 * to show (bio, photo, interests, locality at their own precision) or what
 * the community already knows (reputation labels, circles you share, public
 * activities they host). Attendance history is never listed (FR040).
 * No follow, no like, no message button — you meet people at activities. */

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import { Modal } from '@/components/Sheet';
import { CardSkeleton, ErrorState, Toast } from '@/components/States';
import { api, API_BASE, ApiError, resolveMediaUrl, type Card } from '@/lib/api';

type Person = {
  member_id: string; display_name: string; handle: string; avatar: string | null; bio: string | null; interests: string[];
  location_label: string | null; reputation: string[]; shared_circles: { id: string; name: string }[]; hosting: Card[]; is_me: boolean; can_message?: boolean;
  familiar_count?: number; // [FR116] activities you have both been to
  following?: boolean; // [FR122] do I follow their calendar
};

export default function PersonPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [p, setP] = useState<Person | null>(null);
  const [error, setError] = useState(false);
  const [blockAsk, setBlockAsk] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };

  const load = useCallback(() => { setError(false); api<Person>(`/people/${id}`).then(setP).catch(() => setError(true)); }, [id]);
  // [FR122] Follow their calendar — private to me, and undone with the same tap.
  const follow = async (next: boolean) => {
    setP((prev) => (prev ? { ...prev, following: next } : prev));
    try { await api(`/people/${id}/follow`, { body: { follow: next } }); }
    catch { setP((prev) => (prev ? { ...prev, following: !next } : prev)); }
  };
  useEffect(load, [load]);

  const block = async () => {
    if (!p) return;
    try { await api('/safety/blocks', { body: { member_id: p.member_id } }); setBlockAsk(false); say(t('safety.blocked')); router.push('/people'); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" aria-label={t('common.back')} onClick={() => (history.length > 1 ? router.back() : router.push('/people'))}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
        </button>
        <h1 style={{ fontSize: '1.25rem' }}>{p?.display_name ?? ''}</h1>
        <span style={{ width: 44 }} />
      </header>
      <main className="screen" style={{ gap: 22 }}>
        {error && <ErrorState onRetry={load} />}
        {!p && !error && <CardSkeleton count={1} />}
        {p && (
          <>
            <div className="person__head fade-in">
              {p.avatar ? <img className="avatar avatar--xl" src={resolveMediaUrl(p.avatar) ?? ''} alt="" /> : <span className="avatar avatar--xl" />}
              <div className="grow">
                <div className="display" style={{ fontSize: '1.6rem' }}>{p.display_name}</div>
                <div className="caption">@{p.handle}{p.location_label ? ` · ${p.location_label}` : ''}</div>
                {p.bio && <p className="muted" style={{ margin: '6px 0 0' }}>{p.bio}</p>}
              </div>
            </div>

            {!p.is_me && (
              <div className="row" style={{ gap: 8 }}>
                <button className="btn btn--secondary btn--sm" onClick={() => follow(!p.following)}>
                  {p.following ? t('follow.following') : t('follow.follow')}
                </button>
                {p.following && (
                  <a className="link" href={`${API_BASE}/public/hosts/${p.member_id}/calendar.ics`} target="_blank" rel="noopener">
                    {t('follow.subscribe')}
                  </a>
                )}
              </div>
            )}
            {(p.familiar_count ?? 0) > 0 && (
              <p className="caption" style={{ margin: 0, color: 'var(--accent-pressed)' }}>
                ✦ {t('person.familiar', { count: p.familiar_count })}
              </p>
            )}
            {p.reputation.length > 0 && (
              <section className="stack" style={{ gap: 8 }}>
                <span className="label">{t('person.reputation')}</span>
                <div className="chips">{p.reputation.map((r) => <span key={r} className="pill pill--trust">{r}</span>)}</div>
              </section>
            )}

            {p.interests.length > 0 && (
              <section className="stack" style={{ gap: 8 }}>
                <span className="label">{t('profile.interests')}</span>
                <div className="chips">{p.interests.map((i) => <span key={i} className="chip chip--sm chip--on">{i}</span>)}</div>
              </section>
            )}

            {p.shared_circles.length > 0 && (
              <section className="stack" style={{ gap: 8 }}>
                <span className="label">{t('person.sharedCircles')}</span>
                <div className="list">
                  {p.shared_circles.map((c) => <Link key={c.id} href={`/circles/${c.id}`} className="lrow lrow--tap"><span className="grow">{c.name}</span><span className="muted">›</span></Link>)}
                </div>
              </section>
            )}

            <section className="section">
              <div className="section__head"><h2>{t('person.hosting')}</h2></div>
              {p.hosting.length === 0 ? <p className="caption" style={{ margin: 0 }}>{t('person.noHosting')}</p> : <div className="rail">{p.hosting.map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>}
            </section>

            {!p.is_me && (
              <div className="row" style={{ gap: 8 }}>
                {p.can_message && <button className="btn btn--primary btn--sm" onClick={async () => { try { const r = await api<{ id: string }>('/chats/direct', { body: { member_id: p.member_id } }); router.push(`/chats/${r.id}`); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); } }}>{t('chat.message')}</button>}
                <button className="btn btn--danger-outline btn--sm" onClick={() => setBlockAsk(true)}>{t('safety.block', { name: p.display_name })}</button>
              </div>
            )}
            {p.is_me && <Link href="/me" className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }}>{t('profile.edit')}</Link>}
          </>
        )}
      </main>
      <Modal open={blockAsk} onClose={() => setBlockAsk(false)} label={t('safety.block', { name: p?.display_name ?? '' })}>
        <div className="stack">
          <h2 className="h2">{t('safety.block', { name: p?.display_name ?? '' })}</h2>
          <p className="muted" style={{ margin: 0 }}>{t('safety.blockBody')}</p>
          <div className="row"><button className="btn btn--ghost grow" onClick={() => setBlockAsk(false)}>{t('common.cancel')}</button><button className="btn btn--danger grow" onClick={block}>{t('safety.blockConfirm')}</button></div>
        </div>
      </Modal>
      <Toast text={toast} />
    </>
  );
}
