'use client';

/* Circles (FR020-FR025 · UX09 · UI09). Design brief 2026-09-28 (critique agent,
 * after the owner called the tile version "old school"): photo-led, editorial,
 * near-monochrome. Finding comes first (search, text-only category chips), then
 * your circles as a squircle rail, then Discover as photo cards — Meetup 2025,
 * Discord's "things are squircles", Luma's minimal covers. Saffron is kept for
 * the selected state only; Join on a card is a quiet secondary. Organic
 * suggestions (FR022) are real groups only and need a second person's yes. */

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Lock, MapPin, Plus, Search } from 'lucide-react';

import CircleCover, { coverKind } from '@/components/CircleCover';
import { Sheet } from '@/components/Sheet';
import TopActions from '@/components/TopActions';
import { ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl, type Circle } from '@/lib/api';
import { initials } from '@/lib/format';
import { useIdentity } from '@/lib/identity';

type Face = { member_id: string; display_name: string; avatar: string | null };
// Circles your people are in (owner, 2026-09-29): the reason is always shown — who you know there.
type Recommended = Circle & { known_count: number; known_faces: Face[]; reason: 'known_members' | 'near_you' | 'popular' };
type Invite = { invite_id: string; circle: Circle; invited_by: Face; created_at: string };

type Suggestion = { id: string; name: string; created_at: string; members: { member_id: string; display_name: string; avatar: string | null }[] };
type CircleType = { value: string; label: string; is_open: boolean };

function CircleTile({ c }: { c: Circle }) {
  return (
    <Link href={`/circles/${c.id}`} className="cx-tile">
      <CircleCover variant="tile" name={c.name} coverUrl={c.cover_url} faces={c.faces} />
      <span className="cx-tile__name">{c.name}</span>
    </Link>
  );
}

function knownLine(t: (k: string, o?: Record<string, unknown>) => string, r: Recommended): string {
  const first = r.known_faces[0]?.display_name.split(' ')[0];
  if (r.reason !== 'known_members' || !first) return r.reason === 'near_you' ? t('reco.nearYou') : t('reco.popular');
  return r.known_count > 1 ? t('reco.knownMany', { name: first, count: r.known_count - 1 }) : t('reco.knownOne', { name: first });
}

function CircleCard({ c, onJoin, known }: { c: Circle; onJoin?: (c: Circle) => void; known?: { faces: Face[]; line: string } }) {
  const { t } = useTranslation();
  const caption = [c.circle_type === 'public' ? t('circles.openToAll') : c.type_label, c.locality_label].filter(Boolean).join(' · ');
  // No photo and no faces: the card itself is the typographic cover — never the same words twice.
  const typeOnly = coverKind(c.cover_url, c.faces) === 'type';
  return (
    <article className={`cx-card${typeOnly ? ' cx-card--type' : ''}`}>
      <Link href={`/circles/${c.id}`} className="cx-card__link" aria-label={c.name}>
        {!typeOnly && (
          <div className="cx-card__media">
            <CircleCover variant="card" name={c.name} coverUrl={c.cover_url} faces={c.faces} caption={caption} />
            {!c.is_open && <span className="cx-card__lock" aria-label={t('circles.inviteOnly')}><Lock size={14} strokeWidth={2} /></span>}
          </div>
        )}
        <div className="cx-card__body">
          <span className={typeOnly ? 'cx-label' : 'cx-caption'}>{caption}{typeOnly && !c.is_open ? ` · ${t('circles.inviteOnly')}` : ''}</span>
          {typeOnly && <span className="ccv__rule" style={{ margin: '6px 0 4px' }} />}
          <span className="cx-card__name">{c.name}</span>
          {c.description && <p className="cx-card__desc">{c.description}</p>}
        </div>
      </Link>
      <div className="cx-card__foot">
        {known && known.faces.length > 0 && (
          <span className="cx-stack" aria-hidden="true">
            {known.faces.slice(0, 3).map((f) => (f.avatar ? <img key={f.member_id} className="cx-av cx-av--sm" src={resolveMediaUrl(f.avatar) ?? ''} alt="" /> : <span key={f.member_id} className="cx-av cx-av--sm">{initials(f.display_name)}</span>))}
          </span>
        )}
        <span className="cx-caption grow">{known ? known.line : t('circles.membersShort', { count: c.member_count })}</span>
        {onJoin && c.is_open && <button className="cx-btn cx-btn--quiet" onClick={() => onJoin(c)}>{t('circles.join')}</button>}
      </div>
    </article>
  );
}

export default function CirclesPage() {
  const { t } = useTranslation();
  const { profile } = useIdentity();
  const [mine, setMine] = useState<Circle[] | null>(null);
  const [nearOnly, setNearOnly] = useState(false);
  const [recommended, setRecommended] = useState<Recommended[] | null>(null);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [homeLocality, setHomeLocality] = useState<'home' | 'anywhere'>('home');
  const [found, setFound] = useState<Circle[] | null>(null);
  const [sugs, setSugs] = useState<Suggestion[]>([]);
  const [types, setTypes] = useState<CircleType[]>([]);
  const [q, setQ] = useState('');
  const [error, setError] = useState(false);
  const [create, setCreate] = useState(false);
  // [FR115] A circle can ask a question or two before letting someone in.
  const [askFirst, setAskFirst] = useState(false);
  const [questions, setQuestions] = useState<string[]>(['', '']);
  const [name, setName] = useState('');
  const [type, setType] = useState('public');
  const [desc, setDesc] = useState('');
  const [toast, setToast] = useState<string | null>(null);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2000); };

  const load = useCallback(() => {
    setError(false);
    const qs = new URLSearchParams(); if (q) qs.set('q', q); if (nearOnly) qs.set('near', 'true');
    Promise.all([api<Circle[]>('/circles/mine'), api<Circle[]>(`/circles/discover${qs.toString() ? `?${qs}` : ''}`), api<Suggestion[]>('/circles/suggestions'), api<CircleType[]>('/circles/types')])
      .then(([m, d, s, ty]) => { setMine(m); setFound(d); setSugs(s); setTypes(ty); })
      .catch(() => setError(true));
  }, [q, nearOnly]);
  useEffect(() => { const id = setTimeout(load, 200); return () => clearTimeout(id); }, [load]);
  const loadSocial = useCallback(() => {
    api<Recommended[]>('/circles/recommended').then(setRecommended).catch(() => setRecommended([]));
    api<Invite[]>('/circles/invites/mine').then(setInvites).catch(() => setInvites([]));
  }, []);
  useEffect(loadSocial, [loadSocial]);

  const answerInvite = async (inv: Invite, accept: boolean) => {
    try {
      const r = await api<{ status: string }>(`/circles/invites/${inv.invite_id}/respond`, { body: { accept } });
      // In an "Ask first" circle a member's invite becomes a request the organizer decides on.
      say(!accept ? t('invite.declined') : r.status === 'pending' ? t('join.asked') : t('invite.joined', { name: inv.circle.name }));
      load(); loadSocial();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const join = async (c: Circle) => {
    try {
      const r = await api<{ status: string }>(`/circles/${c.id}/join`, { body: {} });
      say(r.status === 'pending' ? t('join.asked') : t('circles.joined'));
      load(); loadSocial();
    }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const respond = async (s: Suggestion, accept: boolean) => {
    try {
      const r = await api<{ created: Circle | null }>(`/circles/suggestions/${s.id}/respond`, { body: { accept } });
      if (accept) say(r.created ? `${r.created.name} ✓` : t('circles.suggestWaiting'));
      load();
    }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const submit = async () => {
    const place = homeLocality === 'home' && profile ? { locality_city: profile.locality_city, locality_locality: profile.locality_locality } : {};
    const joinSetup = { join_policy: askFirst ? 'approval' : 'open', join_questions: askFirst ? questions.map((q) => q.trim()).filter(Boolean) : [] };
    try { const c = await api<Circle>('/circles', { body: { name, circle_type: type, description: desc, ...place, ...joinSetup } }); setCreate(false); setName(''); setDesc(''); setAskFirst(false); setQuestions(['', '']); say(`${c.name} ✓`); load(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const mineIds = new Set((mine ?? []).map((c) => c.id));
  const recoShown = new Set(!q && typeFilter === null ? (recommended ?? []).slice(0, 6).map((r) => r.id) : []);
  const discoverRest = (found ?? []).filter((c) => !mineIds.has(c.id) && !recoShown.has(c.id) && (typeFilter === null || c.circle_type === typeFilter));
  const discoverList = [...discoverRest.filter((c) => c.near_you), ...discoverRest.filter((c) => !c.near_you)];
  // Nothing new to discover but the section above showed circles: hide Discover rather than claim "nothing to show".
  const hideDiscover = found !== null && discoverList.length === 0 && sugs.length === 0 && recoShown.size > 0 && !nearOnly;
  const typeLabel = (value: string, label: string) => (value === 'public' ? t('circles.openToAll') : label);

  return (
    <>
      <header className="topbar cx-listbar">
        <h1>{t('circles.title')}</h1>
        <div className="row" style={{ gap: 8 }}>
          {/* Finding is this screen's job, so creating is a quiet icon, not an orange pill. */}
          <button className="icon-btn" aria-label={t('circles.create')} onClick={() => setCreate(true)}><Plus size={20} strokeWidth={1.75} /></button>
          <TopActions />
        </div>
      </header>
      <main className="screen cx">
        {error && <ErrorState onRetry={load} />}

        <div className="cx-find">
          <label className="cx-search">
            <Search size={18} strokeWidth={1.75} aria-hidden="true" />
            <input type="search" placeholder={t('circles.searchPlaceholder')} value={q} onChange={(e) => setQ(e.target.value)} aria-label={t('circles.searchPlaceholder')} />
          </label>
          <div className="cx-chips" aria-label={t('circles.discover')}>
            <button className="cx-chip" aria-pressed={typeFilter === null} onClick={() => setTypeFilter(null)}>{t('circles.allTypes')}</button>
            {types.filter((ty) => ty.is_open).map((ty) => (
              <button key={ty.value} className="cx-chip" aria-pressed={typeFilter === ty.value} onClick={() => setTypeFilter((v) => (v === ty.value ? null : ty.value))}>{typeLabel(ty.value, ty.label)}</button>
            ))}
          </div>
        </div>

        {invites.length > 0 && (
          <section className="cx-section">
            <h2 className="cx-h2">{t('invite.title')}</h2>
            <div className="cx-list">
              {invites.map((inv) => (
                <div key={inv.invite_id} className="cx-row">
                  <Link href={`/circles/${inv.circle.id}`} className="cx-invite__cover" aria-label={inv.circle.name}>
                    <CircleCover variant="tile" name={inv.circle.name} coverUrl={inv.circle.cover_url} />
                  </Link>
                  <span className="grow" style={{ minWidth: 0 }}>
                    <span className="cx-strong truncate" style={{ display: 'block' }}>{inv.circle.name}</span>
                    <span className="cx-caption">{t('invite.fromName', { name: inv.invited_by.display_name.split(' ')[0] })}</span>
                  </span>
                  <button className="cx-btn cx-btn--ghost" onClick={() => answerInvite(inv, false)}>{t('invite.decline')}</button>
                  <button className="cx-btn cx-btn--primary" onClick={() => answerInvite(inv, true)}>{t('invite.accept')}</button>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="cx-section">
          <h2 className="cx-h2">{t('circles.yours')}</h2>
          {mine === null && !error && <div className="cx-rail">{[0, 1, 2, 3].map((i) => <div key={i} className="sk cx-tile__sk" />)}</div>}
          {mine && mine.length === 0 && (
            <div className="cx-hairrow">
              <span className="grow">{t('circles.notInAny')}</span>
              <button className="cx-btn cx-btn--quiet" onClick={() => setCreate(true)}>{t('circles.create')}</button>
            </div>
          )}
          {mine && mine.length > 0 && <div className="cx-rail fade-in">{mine.map((c) => <CircleTile key={c.id} c={c} />)}</div>}
        </section>

        {recommended && recommended.length > 0 && !q && typeFilter === null && (
          <section className="cx-section">
            <div className="cx-sechead">
              <h2 className="cx-h2">{t('reco.title')}</h2>
              <span className="cx-caption">{t('reco.subtitle')}</span>
            </div>
            <div className="cx-grid fade-in">
              {recommended.slice(0, 6).map((r) => <CircleCard key={r.id} c={r} onJoin={join} known={{ faces: r.known_faces, line: knownLine(t, r) }} />)}
            </div>
          </section>
        )}

        {!hideDiscover && (
        <section className="cx-section">
          <div className="cx-sechead">
            <h2 className="cx-h2">{t('circles.discoverShort')}</h2>
            <button className="cx-textbtn" aria-pressed={nearOnly} onClick={() => setNearOnly((v) => !v)}>
              <MapPin size={14} strokeWidth={2} aria-hidden="true" /> {nearOnly ? t('circles.nearOnlyOn') : t('circles.nearYouFirst')}
            </button>
          </div>
          {sugs.map((sg) => (
            <article key={sg.id} className="cx-card cx-card--suggest fade-in">
              <div className="cx-card__media">
                <CircleCover variant="card" name={sg.name} faces={sg.members} caption={t('circles.suggested')} />
              </div>
              <div className="cx-card__body">
                <span className="cx-caption">{t('circles.suggested')}</span>
                <span className="cx-card__name">{sg.name}</span>
                <p className="cx-card__desc">{sg.members.map((m) => m.display_name).join(', ')} — {t('circles.suggestedBody')}</p>
              </div>
              <div className="cx-card__foot">
                <button className="cx-btn cx-btn--ghost" onClick={() => respond(sg, false)}>{t('circles.notNow')}</button>
                <span className="grow" />
                <button className="cx-btn cx-btn--primary" onClick={() => respond(sg, true)}>{t('circles.start')}</button>
              </div>
            </article>
          ))}
          {found && discoverList.length === 0 && sugs.length === 0 && <p className="cx-caption" style={{ margin: 0 }}>{t('circles.emptyDiscover')}</p>}
          {discoverList.length > 0 && <div className="cx-grid fade-in">{discoverList.map((c) => <CircleCard key={c.id} c={c} onJoin={join} />)}</div>}
        </section>
        )}
      </main>

      <Sheet open={create} onClose={() => setCreate(false)} label={t('circles.create')}>
        <div className="stack cx" style={{ gap: 16 }}>
          <h2 className="cx-h2">{t('circles.create')}</h2>
          <label className="stack" style={{ gap: 6 }}>
            <span className="cx-label">{t('circles.name')}</span>
            <input className="cx-input" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} />
          </label>
          <div className="stack" style={{ gap: 8 }}>
            <span className="cx-label">{t('circles.type')}</span>
            <div className="cx-chips cx-chips--wrap">
              {types.map((ty) => (
                <button key={ty.value} className="cx-chip" aria-pressed={type === ty.value} onClick={() => setType(ty.value)}>
                  {typeLabel(ty.value, ty.label)}{!ty.is_open && <Lock size={14} strokeWidth={2} aria-label={t('circles.inviteOnly')} />}
                </button>
              ))}
            </div>
          </div>
          <label className="stack" style={{ gap: 6 }}>
            <span className="cx-label">{t('manage.description')}</span>
            <textarea className="cx-input" rows={3} placeholder={t('circles.descriptionPlaceholder')} value={desc} onChange={(e) => setDesc(e.target.value)} />
          </label>
          <div className="stack" style={{ gap: 8 }}>
            <span className="cx-label">{t('circles.home')}</span>
            <div className="cx-chips cx-chips--wrap">
              <button className="cx-chip" aria-pressed={homeLocality === 'home'} onClick={() => setHomeLocality('home')}><MapPin size={14} strokeWidth={2} aria-hidden="true" />{profile?.locality_locality ?? profile?.locality_city ?? t('circles.home')}</button>
              <button className="cx-chip" aria-pressed={homeLocality === 'anywhere'} onClick={() => setHomeLocality('anywhere')}>{t('circles.anywhere')}</button>
            </div>
          </div>
          <div className="stack" style={{ gap: 8 }}>
            <span className="cx-label">{t('join.whoCanJoin')}</span>
            <div className="cx-chips cx-chips--wrap">
              <button type="button" className="cx-chip" aria-pressed={!askFirst} onClick={() => setAskFirst(false)}>{t('join.anyone')}</button>
              <button type="button" className="cx-chip" aria-pressed={askFirst} onClick={() => setAskFirst(true)}>{t('join.askFirst')}</button>
            </div>
            {askFirst && (
              <>
                <span className="cx-caption">{t('join.questionsHint')}</span>
                {questions.map((q, i) => (
                  <input
                    key={i}
                    className="cx-input"
                    name={`join-question-${i}`}
                    maxLength={120}
                    placeholder={t(`join.questionPlaceholder${i}`)}
                    value={q}
                    onChange={(e) => setQuestions((prev) => prev.map((v, j) => (j === i ? e.target.value : v)))}
                  />
                ))}
              </>
            )}
          </div>
          <button className="cx-btn cx-btn--primary cx-btn--lg" disabled={!name.trim()} onClick={submit}>{t('circles.create')}</button>
        </div>
      </Sheet>
      <Toast text={toast} />
    </>
  );
}
