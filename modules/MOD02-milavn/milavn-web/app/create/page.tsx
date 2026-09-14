'use client';

/* Make Something Happen (FR010-FR014 · UX07 · UI07): four minimal fields
 * (What / When / Where / How many), "More options" accordion (capacity,
 * visibility/circle, repeats, cover, high-risk), springy confirmation with
 * an immediately shareable link + QR. Also handles Edit (?edit=<id>). */

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import PlacePicker from '@/components/PlacePicker';
import QrCode from '@/components/QrCode';
import WhenPicker from '@/components/WhenPicker';
import { Modal } from '@/components/Sheet';
import { Toast } from '@/components/States';
import { api, ApiError, type Card, type Circle } from '@/lib/api';
import { toLocalInputValue } from '@/lib/format';
import { useIdentity } from '@/lib/identity';

const CATEGORIES: [string, string][] = [['play', '🏸'], ['meet', '☕'], ['eat', '🍛'], ['learn', '📚'], ['work', '💼'], ['explore', '🥾'], ['celebrate', '🎉'], ['help', '🤝']];
// One-tap "when" (thesis §40: one-tap actions over forms). Each returns a local Date.
function at(daysAhead: number, hour: number): Date { const d = new Date(); d.setDate(d.getDate() + daysAhead); d.setHours(hour, 0, 0, 0); return d; }
function nextWeekday(weekday: number, hour: number): Date { const d = new Date(); const delta = (weekday - d.getDay() + 7) % 7 || 7; return at(delta, hour); }
const QUICK_WHEN: [string, () => Date][] = [
  ['tonight', () => at(0, 19)], ['tomorrowMorning', () => at(1, 7)], ['tomorrowEvening', () => at(1, 19)],
  ['saturday', () => nextWeekday(6, 8)], ['sunday', () => nextWeekday(0, 8)],
];

function CreateInner() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useSearchParams();
  const editId = params.get('edit');
  const presetCircle = params.get('circle');
  const { profile } = useIdentity();

  const [category, setCategory] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [when, setWhen] = useState('');
  const [city, setCity] = useState(profile?.locality_city ?? '');
  const [locality, setLocality] = useState(profile?.locality_locality ?? '');
  const [count, setCount] = useState<number | null>(null);
  const [more, setMore] = useState(false);
  const [description, setDescription] = useState('');
  const [scope, setScope] = useState<'public' | 'community' | 'circle'>(presetCircle ? 'circle' : 'public');
  const [circleId, setCircleId] = useState<string>(presetCircle ?? '');
  const [recurring, setRecurring] = useState(false);
  const [highRisk, setHighRisk] = useState(false);
  const [cover, setCover] = useState<{ media_id: string; url: string } | null>(null);
  const [circles, setCircles] = useState<Circle[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [shakeKey, setShakeKey] = useState(0);
  const [created, setCreated] = useState<(Card & { share_url: string }) | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [cancelAsk, setCancelAsk] = useState(false);
  const [smart, setSmart] = useState('');
  const [smartBusy, setSmartBusy] = useState(false);
  const [smartMatched, setSmartMatched] = useState<string[]>([]);

  // Smart fill: one sentence -> the four fields (deterministic parser on the API; the person always sees and can edit the result).
  const smartFill = async () => {
    if (!smart.trim()) return;
    setSmartBusy(true);
    try {
      const d = await api<{ category: string | null; title: string | null; time_start: string | null; locality_city: string | null; locality_locality: string | null; capacity: number | null; matched: string[] }>(`/discovery/smart-fill?text=${encodeURIComponent(smart)}`);
      if (d.category) setCategory(d.category);
      if (d.title) setTitle(d.title);
      if (d.time_start) setWhen(toLocalInputValue(d.time_start));
      if (d.locality_city) setCity(d.locality_city);
      if (d.locality_locality) setLocality(d.locality_locality);
      if (d.capacity) setCount(d.capacity);
      setSmartMatched(d.matched);
    } catch { setToast(t('state.error')); setTimeout(() => setToast(null), 2000); }
    finally { setSmartBusy(false); }
  };

  useEffect(() => {
    api<Circle[]>('/circles/mine').then(setCircles).catch(() => undefined);
    if (editId) {
      api<Card & { description: string | null }>(`/occurrences/${editId}`).then((o) => {
        setTitle(o.title); setCategory(o.intent_category); setWhen(toLocalInputValue(o.time_start)); setCount(o.capacity);
        setDescription(o.description ?? ''); setHighRisk(o.high_risk);
        setScope(o.visibility_scope === 'circle' ? 'circle' : o.visibility_scope === 'community' ? 'community' : 'public');
        setCircleId(o.circle_id ?? ''); setMore(true);
      }).catch(() => undefined);
    }
  }, [editId]);
  useEffect(() => { if (profile && !editId) { setCity(profile.locality_city); setLocality(profile.locality_locality ?? ''); } }, [profile, editId]);

  const canSubmit = !!category && title.trim().length > 0 && !!when && !!city && (scope !== 'circle' || !!circleId);

  const uploadCover = async (file: File | undefined) => {
    if (!file) return;
    const form = new FormData(); form.append('photo', file);
    try { setCover(await api<{ media_id: string; url: string }>('/occurrences/cover', { form })); }
    catch { setToast(t('state.error')); setTimeout(() => setToast(null), 2000); }
  };

  const submit = async () => {
    if (!canSubmit) { setShakeKey((k) => k + 1); return; }
    setBusy(true); setErr(null);
    const body = {
      title: title.trim(), intent_category: category, time_start: new Date(when).toISOString(), locality_city: city, locality_locality: locality || null,
      capacity: count, description: description || null, visibility_scope: scope, circle_id: scope === 'circle' ? circleId : null,
      high_risk: highRisk, recurrence_rule: recurring ? { freq: 'weekly' } : null, cover_image_media_id: cover?.media_id ?? null,
    };
    try {
      if (editId) {
        await api(`/occurrences/${editId}`, { method: 'PATCH', body });
        router.push(`/a/${(await api<Card>(`/occurrences/${editId}`)).slug}`);
        return;
      }
      const c = await api<Card & { share_url: string }>('/occurrences', { body, idempotent: true });
      setCreated(c);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : t('state.error'));
      setShakeKey((k) => k + 1);
    } finally { setBusy(false); }
  };

  const cancelActivity = async () => {
    if (!editId) return;
    try { await api(`/occurrences/${editId}/cancel`, { body: {} }); router.push('/'); }
    catch (e) { setErr(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const shareNow = async () => {
    if (!created) return;
    const url = `${window.location.origin}/a/${created.slug}`;
    if (navigator.share) { try { await navigator.share({ title: created.title, url }); } catch { /* cancelled */ } }
    else { await navigator.clipboard?.writeText(url); setToast(t('create.copied')); setTimeout(() => setToast(null), 2000); }
  };

  if (created) {
    const url = typeof window !== 'undefined' ? `${window.location.origin}/a/${created.slug}` : '';
    return (
      <main className="screen" style={{ minHeight: '100vh', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
        <div className="check-pop" style={{ width: 88, height: 88, borderRadius: 28, background: 'var(--success-tint)', color: 'var(--success-trust)', display: 'grid', placeItems: 'center' }}>
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true"><path d="M5 12l5 5L19 7" /></svg>
        </div>
        <h1 className="display">{t('create.live')}</h1>
        <p className="muted" style={{ margin: 0 }}>{t('create.liveBody')}</p>
        <QrCode value={url} size={160} label="QR code" />
        <code className="caption" style={{ wordBreak: 'break-all' }}>{url}</code>
        <button className="btn btn--primary btn--block" onClick={shareNow}>{t('create.shareNow')}</button>
        <button className="btn btn--ghost" onClick={() => router.push(`/a/${created.slug}`)}>{t('create.view')}</button>
        <Toast text={toast} />
      </main>
    );
  }

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" aria-label={t('common.back')} onClick={() => router.back()}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
        </button>
        <h1 style={{ fontSize: '1.25rem' }}>{editId ? t('create.edit') : t('create.title')}</h1>
        <span style={{ width: 44 }} />
      </header>
      <main className="screen" style={{ gap: 20 }}>
        {!editId && (
          <section className="stack" style={{ gap: 8 }}>
            <form className="ask" onSubmit={(e) => { e.preventDefault(); void smartFill(); }} aria-label={t('create.smartLabel')}>
              <span className="ask__spark" aria-hidden="true">✦</span>
              <input value={smart} onChange={(e) => setSmart(e.target.value)} placeholder={t('create.smartPlaceholder')} aria-label={t('create.smartLabel')} />
              <button type="submit" className="ask__go" aria-label={t('create.smartGo')} disabled={smartBusy || !smart.trim()} style={{ width: 'auto', padding: '0 14px', fontWeight: 700, fontSize: '0.875rem' }}>{smartBusy ? '…' : t('create.smartGo')}</button>
            </form>
            {smartMatched.length > 0 && <div className="ask__understood"><span>{t('ask.understood')}</span>{smartMatched.map((m) => <span key={m} className="pill">{m}</span>)}</div>}
          </section>
        )}
        <section className="stack" style={{ gap: 8 }}>
          <span className="label">{t('create.what')}</span>
          <div className="grid-4" role="radiogroup" aria-label={t('create.what')}>
            {CATEGORIES.map(([c, icon]) => (
              <button key={c} type="button" role="radio" aria-checked={category === c} aria-pressed={category === c} className={`cat${category === c ? ' pop' : ''}`} data-cat={c} onClick={() => setCategory(c)}>
                <span>{icon}</span><span>{t(`create.categories.${c}`)}</span>
              </button>
            ))}
          </div>
          <label className="field"><input className="field__input" placeholder={t('create.titlePlaceholder')} value={title} onChange={(e) => setTitle(e.target.value)} maxLength={140} /></label>
        </section>

        <div className="stack" style={{ gap: 8 }}>
          <span className="field__label">{t('create.when')}</span>
          <div className="chips chips--scroll" aria-label={t('create.when')}>
            {QUICK_WHEN.map(([key, pick]) => {
              const v = toLocalInputValue(pick().toISOString());
              return <button key={key} type="button" className="chip chip--sm" aria-pressed={when === v} onClick={() => setWhen(v)}>{t(`create.quickWhen.${key}`)}</button>;
            })}
          </div>
          <WhenPicker value={when} onChange={setWhen} />
        </div>

        <div className="stack" style={{ gap: 8 }}>
          <span className="field__label">{t('create.where')}</span>
          <PlacePicker city={city} locality={locality} onChange={(c, l) => { setCity(c); setLocality(l); }} label={t('create.where')} />
        </div>

        <div className="row row--between">
          <span className="field__label">{t('create.howMany')}</span>
          <div className="stepper" aria-live="polite">
            <button type="button" aria-label="Fewer" onClick={() => setCount((c) => (c === null ? null : c <= 2 ? null : c - 1))}>−</button>
            <output>{count === null ? t('create.noLimit') : count}</output>
            <button type="button" aria-label="More" onClick={() => setCount((c) => (c === null ? 2 : c + 1))}>+</button>
          </div>
        </div>

        <button type="button" className="row row--between" style={{ background: 'none', border: 0, padding: '8px 0', color: 'var(--accent-pressed)', fontWeight: 600 }} aria-expanded={more} aria-controls="more-options" onClick={() => setMore((v) => !v)}>
          <span>{more ? t('create.less') : t('create.more')}</span><span>{more ? '▴' : '▾'}</span>
        </button>
        {more && (
          <section id="more-options" className="stack fade-in" style={{ gap: 16 }}>
            <label className="field"><span className="field__label">{t('create.description')}</span><textarea value={description} onChange={(e) => setDescription(e.target.value)} /></label>
            <div className="stack" style={{ gap: 8 }}>
              <span className="field__label">{t('create.visibility')}</span>
              <div className="chips">
                {(['public', 'community', 'circle'] as const).map((s) => <button key={s} type="button" className="chip chip--sm" aria-pressed={scope === s} onClick={() => setScope(s)}>{t(`discover.scopes.${s}`)}</button>)}
              </div>
              {scope === 'circle' && (
                <select className="field__input" value={circleId} onChange={(e) => setCircleId(e.target.value)} aria-label={t('create.circle')}>
                  <option value="">{t('create.circle')}</option>
                  {circles.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              )}
            </div>
            {!editId && <div className="row row--between"><span>{t('create.recurring')}</span><button type="button" className="switch" role="switch" aria-checked={recurring} onClick={() => setRecurring((v) => !v)} aria-label={t('create.recurring')} /></div>}
            <div className="row row--between"><span style={{ maxWidth: '75%' }}>{t('create.highRisk')}</span><button type="button" className="switch" role="switch" aria-checked={highRisk} onClick={() => setHighRisk((v) => !v)} aria-label={t('create.highRisk')} /></div>
            <label className="field">
              <span className="field__label">{t('create.cover')}</span>
              <input className="field__input" type="file" accept="image/*" onChange={(e) => uploadCover(e.target.files?.[0])} />
              {cover && <img src={`${process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8001'}${cover.url}`} alt="" style={{ borderRadius: 12, marginTop: 8, aspectRatio: '16/9', objectFit: 'cover' }} />}
            </label>
          </section>
        )}

        {err && <p className="field__error" role="alert">{err}</p>}
        <button key={shakeKey} className={`btn btn--primary btn--block${shakeKey ? ' shake' : ''}`} disabled={busy || !canSubmit} onClick={submit}>{busy ? t('state.loading') : editId ? t('create.save') : t('create.create')}</button>
        {editId && <button className="btn btn--danger-outline btn--block" onClick={() => setCancelAsk(true)}>{t('create.cancelActivity')}</button>}
      </main>
      <Modal open={cancelAsk} onClose={() => setCancelAsk(false)} label={t('create.cancelActivity')}>
        <div className="stack">
          <h2 className="h2">{t('create.cancelActivity')}</h2>
          <p className="muted" style={{ margin: 0 }}>{t('create.cancelConfirm')}</p>
          <div className="row"><button className="btn btn--ghost grow" onClick={() => setCancelAsk(false)}>{t('create.keep')}</button><button className="btn btn--danger grow" onClick={cancelActivity}>{t('create.yesCancel')}</button></div>
        </div>
      </Modal>
      <Toast text={toast} />
    </>
  );
}

export default function CreatePage() {
  return <Suspense fallback={<main className="screen" />}><CreateInner /></Suspense>;
}
