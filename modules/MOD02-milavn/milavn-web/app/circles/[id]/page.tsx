'use client';

/* Circle detail (FR020, FR024, FR025, FR027 · UX09/UI09): stats pills
 * (community memory, members-only for non-open circles), member list,
 * upcoming activities, join/leave, "new activity in this circle". */

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import { CardSkeleton, EmptyState, ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl, type Card, type Circle } from '@/lib/api';
import { formatRelative, initials } from '@/lib/format';

type Post = { id: string; member_id: string; display_name: string; avatar: string | null; body: string; created_at: string; mine: boolean };

type Detail = Circle & {
  members: { member_id: string; display_name: string; avatar: string | null; role: string }[];
  memory: { member_count: number; activities_held: number; upcoming_count: number; first_activity_at: string | null } | null;
  upcoming: Card[];
};

export default function CircleDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [d, setD] = useState<Detail | null>(null);
  const [error, setError] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [posts, setPosts] = useState<Post[] | null>(null);
  const [draft, setDraft] = useState('');
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2000); };

  const loadPosts = useCallback(() => { api<{ posts: Post[] }>(`/circles/${id}/posts`).then((r) => setPosts(r.posts)).catch(() => setPosts([])); }, [id]);
  const load = useCallback(() => { setError(false); api<Detail>(`/circles/${id}`).then(setD).catch(() => setError(true)); loadPosts(); }, [id, loadPosts]);
  useEffect(load, [load]);

  const post = async () => {
    const body = draft.trim(); if (!body) return;
    try { await api(`/circles/${id}/posts`, { body: { body }, idempotent: true }); setDraft(''); loadPosts(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const join = async () => { try { await api(`/circles/${id}/join`, { body: {} }); load(); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); } };
  const leave = async () => { try { await api(`/circles/${id}/leave`, { body: {} }); load(); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); } };

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" aria-label={t('common.back')} onClick={() => router.back()}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
        </button>
        <h1 style={{ fontSize: '1.25rem' }} className="truncate">{d?.name ?? ''}</h1>
        <span style={{ width: 44 }} />
      </header>
      <main className="screen">
        {error && <ErrorState onRetry={load} />}
        {!d && !error && <CardSkeleton count={1} />}
        {d && (
          <>
            <div className="row" style={{ gap: 14 }}>
              <span className="strip__ring" style={{ width: 64, height: 64, borderColor: 'transparent', padding: 0 }}><div style={{ fontSize: '1.25rem' }}>{initials(d.name)}</div></span>
              <div className="grow">
                <div className="row" style={{ gap: 8 }}><span className="pill pill--neutral">{d.type_label}</span>{!d.is_open && <span className="pill pill--neutral">{t('circles.inviteOnly')}</span>}</div>
                {d.description && <p className="muted" style={{ margin: '6px 0 0' }}>{d.description}</p>}
              </div>
            </div>
            <div className="row">
              {d.viewer_role ? (
                <>
                  <Link href={`/create?circle=${d.id}`} className="btn btn--primary grow">{t('circles.newActivity')}</Link>
                  {d.viewer_role !== 'organizer' && <button className="btn btn--ghost" onClick={leave}>{t('circles.leave')}</button>}
                </>
              ) : d.is_open ? (
                <button className="btn btn--primary btn--block btn--spring" onClick={join}>{t('circles.join')}</button>
              ) : null}
            </div>

            {d.memory && (
              <section className="stack" style={{ gap: 8 }}>
                <span className="label">{t('circles.memory')}</span>
                <div className="row">
                  <div className="stat"><b>{d.memory.member_count}</b><span>{t('circles.members', { count: d.memory.member_count }).replace(/^\d+\s*/, '')}</span></div>
                  <div className="stat"><b>{d.memory.activities_held}</b><span>{t('circles.held')}</span></div>
                  <div className="stat"><b>{d.memory.upcoming_count}</b><span>{t('circles.upcoming')}</span></div>
                  {d.memory.first_activity_at && <div className="stat"><b>{new Date(d.memory.first_activity_at).getFullYear()}</b><span>{t('circles.since')}</span></div>}
                </div>
              </section>
            )}

            {d.viewer_role && (
              <section className="card stack" style={{ gap: 12 }}>
                <div className="row row--between"><span className="label">{t('circles.board')}</span><span className="caption">{t('circles.boardPrivate')}</span></div>
                <div className="composer">
                  <textarea rows={1} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={t('circles.boardPlaceholder')} aria-label={t('circles.boardPlaceholder')} maxLength={1000} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void post(); } }} />
                  <button className="btn btn--primary btn--sm btn--spring" disabled={!draft.trim()} onClick={post}>{t('thread.send')}</button>
                </div>
                {posts && posts.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('circles.boardEmpty')}</p>}
                {posts && posts.map((p) => (
                  <div key={p.id} className="row" style={{ gap: 10, alignItems: 'flex-start' }}>
                    <Link href={`/p/${p.member_id}`}>{p.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(p.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}</Link>
                    <div className="grow">
                      <div className="row" style={{ gap: 6 }}><b>{p.display_name}</b><span className="caption">· {formatRelative(p.created_at)}</span></div>
                      <p style={{ margin: '2px 0 0', whiteSpace: 'pre-wrap' }}>{p.body}</p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            <section className="section">
              <div className="section__head"><h2>{t('circles.upcomingIn')}</h2></div>
              {d.upcoming.length === 0 ? <EmptyState message={t('circles.emptyUpcoming')} action={d.viewer_role ? t('circles.newActivity') : undefined} onAction={d.viewer_role ? () => router.push(`/create?circle=${d.id}`) : undefined} /> : <div className="rail">{d.upcoming.map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>}
            </section>

            <section className="section">
              <div className="section__head"><h2>{t('circles.members', { count: d.members.length })}</h2></div>
              <div className="list">
                {d.members.map((m) => (
                  <Link key={m.member_id} href={`/p/${m.member_id}`} className="lrow lrow--tap" style={{ minHeight: 56 }}>
                    {m.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(m.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
                    <span className="grow">{m.display_name}</span>
                    {m.role === 'organizer' && <span className="pill pill--accent">{t('detail.organizer')}</span>}
                    <span className="muted">›</span>
                  </Link>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
      <Toast text={toast} />
    </>
  );
}
