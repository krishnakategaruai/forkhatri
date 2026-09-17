'use client';

/* Profile (FR002, FR003, FR041, FR085, FR087, FR088 · UX17 · UI17): the page
 * is about the person — identity, how the community sees them, interests,
 * what they host and go to. Preferences (language, appearance, location
 * precision, help, sign-out, delete) live behind one gear icon in a sheet,
 * so settings never crowd the profile. Deletion itself is a ForKhatri
 * platform action. */

import { Bell, Camera, Globe, HelpCircle, LayoutGrid, LogOut, MapPin, Settings, SunMoon, Trash2, Wallet } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import { Modal, Sheet } from '@/components/Sheet';
import { Toast } from '@/components/States';
import TopActions from '@/components/TopActions';
import { api, ApiError, resolveMediaUrl, type Card, type Profile } from '@/lib/api';
import { LANGUAGE_NATIVE, SUPPORTED_LANGUAGES, type Language } from '@/lib/i18n/config';
import { applyLanguage } from '@/lib/i18n/provider';
import { formatDateLong, formatInr } from '@/lib/format';
import { useIdentity } from '@/lib/identity';
import { FORKHATRI_ACCOUNT_URL, FORKHATRI_ENTRANCE_URL } from '@/lib/platform';

type Taxonomy = { group: string; interests: { tag: string; label: string }[] }[];
type MyTicket = { id: string; status: string; amount_paise: number; refund_amount_paise: number | null; title: string; slug: string; time_start: string };
const THEME_KEY = 'milavn.theme';

export default function MePage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { identity, profile, setProfile, signOut } = useIdentity();
  const [edit, setEdit] = useState(false);
  const [settings, setSettings] = useState(false);
  const [bio, setBio] = useState(profile?.bio ?? '');
  const [taxonomy, setTaxonomy] = useState<Taxonomy>([]);
  const [extra, setExtra] = useState<string[]>([]);
  const [photo, setPhoto] = useState<File | null>(null);
  const [precision, setPrecision] = useState<string>('locality');
  const [noPhotos, setNoPhotos] = useState(false); // FR113
  const [theme, setTheme] = useState<'system' | 'light' | 'dark'>('system');
  const [reputation, setReputation] = useState<string[]>([]);
  const [mine, setMine] = useState<{ participating: Card[]; hosting: Card[] } | null>(null);
  const [help, setHelp] = useState(false);
  const [supportText, setSupportText] = useState('');
  const [del, setDel] = useState(false);
  const [paySheet, setPaySheet] = useState(false);
  const [tickets, setTickets] = useState<MyTicket[] | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const openPayments = async () => { setPaySheet(true); try { setTickets(await api<MyTicket[]>('/tickets/mine')); } catch { setTickets([]); } };
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2000); };

  useEffect(() => {
    api<{ precision_level: string }>('/privacy/location').then((r) => setPrecision(r.precision_level)).catch(() => undefined);
    api<{ prefer_not_pictured: boolean }>('/moments/preference').then((r) => setNoPhotos(r.prefer_not_pictured)).catch(() => undefined);
    api<Taxonomy>('/profile/interests/taxonomy').then(setTaxonomy).catch(() => undefined);
    api<{ participating: Card[]; hosting: Card[] }>('/occurrences/mine').then(setMine).catch(() => undefined);
    try { const saved = localStorage.getItem(THEME_KEY) as 'light' | 'dark' | null; if (saved) { setTheme(saved); document.documentElement.dataset.theme = saved; } } catch { /* ignore */ }
  }, [identity]);
  useEffect(() => { setBio(profile?.bio ?? ''); }, [profile]);
  useEffect(() => {
    if (!identity) return;
    api<string[]>(`/people/reputation/${identity.member_id}`).then(setReputation).catch(() => setReputation([]));
  }, [identity]);

  const setThemeChoice = (v: 'system' | 'light' | 'dark') => {
    setTheme(v);
    if (v === 'system') { delete document.documentElement.dataset.theme; try { localStorage.removeItem(THEME_KEY); } catch { /* ignore */ } }
    else { document.documentElement.dataset.theme = v; try { localStorage.setItem(THEME_KEY, v); } catch { /* ignore */ } }
  };

  const saveEdit = async () => {
    const form = new FormData();
    form.append('bio', bio);
    if (extra.length) form.append('extra_interests', extra.join(','));
    if (photo) form.append('photo', photo);
    try { const p = await api<Profile>('/profile/enrichment', { method: 'PATCH', form }); setProfile(p); setEdit(false); setExtra([]); setPhoto(null); say(t('profile.saved')); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const setLang = async (l: Language) => {
    applyLanguage(l);
    try { setProfile(await api<Profile>('/profile/language', { method: 'PATCH', body: { language_preference: l } })); } catch { /* local applies anyway */ }
  };
  const setPrec = async (lvl: string) => {
    try { const r = await api<{ precision_level: string }>('/privacy/location', { method: 'PUT', body: { precision_level: lvl } }); setPrecision(r.precision_level); say(t('profile.saved')); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const sendSupport = async () => {
    if (!identity) return;
    try { await api('/safety/reports', { body: { subject_type: 'content', subject_id: identity.member_id, reason_category: 'other', description: `[support] ${supportText}` }, idempotent: true }); setHelp(false); setSupportText(''); say(t('safety.submitted')); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  if (!identity || !profile) return <main className="screen" />;
  const lang = (profile.language_preference as Language) ?? 'en';
  const place = profile.locality_locality ?? profile.locality_zone ?? profile.locality_city;

  return (
    <>
      <header className="topbar">
        <h1>{t('profile.title')}</h1>
        <div className="row" style={{ gap: 8 }}>
          <button className="icon-btn" aria-label={t('profile.settings')} onClick={() => setSettings(true)}><Settings size={20} strokeWidth={1.8} aria-hidden="true" /></button>
          <TopActions />
        </div>
      </header>
      <main className="screen" style={{ gap: 22 }}>
        <div className="person__head fade-in">
          {profile.photo_url || identity.avatar ? <img className="avatar avatar--xl" src={resolveMediaUrl(profile.photo_url ?? identity.avatar) ?? ''} alt="" /> : <span className="avatar avatar--xl" />}
          <div className="grow">
            <div className="greeting" style={{ fontSize: '1.7rem' }}>{identity.display_name}</div>
            <div className="caption">@{identity.handle} · <MapPin size={12} aria-hidden="true" style={{ verticalAlign: '-1px' }} /> {place}, {profile.locality_city}</div>
            {profile.bio && <p className="muted" style={{ margin: '4px 0 0' }}>{profile.bio}</p>}
          </div>
          <button className="btn btn--secondary btn--sm" onClick={() => setEdit(true)}>{t('profile.edit')}</button>
        </div>

        <div className="row" style={{ gap: 8 }}>
          <div className="stat"><b>{mine?.hosting.length ?? 0}</b><span>{t('profile.hosting')}</span></div>
          <div className="stat"><b>{mine?.participating.length ?? 0}</b><span>{t('profile.attending')}</span></div>
          <Link href="/people" className="stat" style={{ textDecoration: 'none' }}><b>→</b><span>{t('people.title')}</span></Link>
        </div>

        {reputation.length > 0 && (
          <section className="stack" style={{ gap: 8 }}>
            <span className="label">{t('profile.reputation')}</span>
            <div className="chips">{reputation.map((r) => <span key={r} className="pill pill--trust">{r}</span>)}</div>
          </section>
        )}

        <section className="stack" style={{ gap: 8 }}>
          <span className="label">{t('profile.interests')}</span>
          <div className="chips">{profile.interest_labels.map((l) => <span key={l} className="chip chip--sm chip--on">{l}</span>)}</div>
        </section>

        {mine && mine.participating.length > 0 && (
          <section className="stack" style={{ gap: 10 }}>
            <div className="section__head"><h2>{t('profile.attending')}</h2><span className="count-chip">{mine.participating.length}</span></div>
            <div className="rail">{mine.participating.slice(0, 6).map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>
          </section>
        )}
        {mine && mine.hosting.length > 0 && (
          <section className="stack" style={{ gap: 10 }}>
            <div className="section__head"><h2>{t('profile.hosting')}</h2><span className="count-chip">{mine.hosting.length}</span></div>
            <div className="rail">{mine.hosting.slice(0, 6).map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>
          </section>
        )}
      </main>

      <Sheet open={settings} onClose={() => setSettings(false)} label={t('profile.settings')}>
        <div className="stack" style={{ gap: 16 }}>
          <h2 className="h2">{t('profile.settings')}</h2>
          <div className="setrow"><span className="setrow__icon"><Globe size={18} aria-hidden="true" /></span><span className="grow">{t('profile.language')}</span>
            <div className="chips">{SUPPORTED_LANGUAGES.map((l) => <button key={l} className="chip chip--sm" aria-pressed={lang === l} onClick={() => setLang(l)}>{LANGUAGE_NATIVE[l]}</button>)}</div></div>
          <div className="setrow"><span className="setrow__icon"><SunMoon size={18} aria-hidden="true" /></span><span className="grow">{t('profile.appearance')}</span>
            <div className="chips">{(['system', 'light', 'dark'] as const).map((v) => <button key={v} className="chip chip--sm" aria-pressed={theme === v} onClick={() => setThemeChoice(v)}>{t(`profile.${v}`)}</button>)}</div></div>
          <div className="setrow"><span className="setrow__icon"><MapPin size={18} aria-hidden="true" /></span><span className="grow">{t('profile.locationPrivacy')}<br /><span className="caption">{t('profile.locationBody')}</span></span>
            <div className="chips">{['city', 'zone', 'locality'].map((v) => <button key={v} className="chip chip--sm" aria-pressed={precision === v} onClick={() => setPrec(v)}>{t(`profile.precision.${v}`)}</button>)}</div></div>
          <div className="setrow"><span className="setrow__icon"><Camera size={18} aria-hidden="true" /></span><span className="grow">{t('moments.prefTitle')}<br /><span className="caption">{t('moments.prefBody')}</span></span>
            <div className="chips">
              {[false, true].map((v) => <button key={String(v)} className="chip chip--sm" aria-pressed={noPhotos === v} onClick={async () => { try { const r = await api<{ prefer_not_pictured: boolean }>('/moments/preference', { method: 'PUT', body: { prefer_not_pictured: v } }); setNoPhotos(r.prefer_not_pictured); say(t('profile.saved')); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); } }}>{v ? t('moments.prefNo') : t('moments.prefFine')}</button>)}
            </div></div>
          <button className="setrow setrow--tap" onClick={() => { setSettings(false); void openPayments(); }}><span className="setrow__icon"><Wallet size={18} aria-hidden="true" /></span><span className="grow">{t('pay.mine.title')}</span><span className="muted">›</span></button>
          <Link href="/notifications" className="setrow setrow--tap" onClick={() => setSettings(false)}><span className="setrow__icon"><Bell size={18} aria-hidden="true" /></span><span className="grow">{t('notifications.settings')}</span><span className="muted">›</span></Link>
          {identity.scopes.includes('milavn.moderate') && <Link href="/admin/moderation" className="setrow setrow--tap"><span className="setrow__icon">🛡️</span><span className="grow">{t('moderation.title')}</span><span className="muted">›</span></Link>}
          <a href={`${FORKHATRI_ENTRANCE_URL}/`} className="setrow setrow--tap"><span className="setrow__icon"><LayoutGrid size={18} aria-hidden="true" /></span><span className="grow">{t('platform.backToHub')}</span><span className="muted">›</span></a>
          <button className="setrow setrow--tap" onClick={() => { setSettings(false); setHelp(true); }}><span className="setrow__icon"><HelpCircle size={18} aria-hidden="true" /></span><span className="grow">{t('profile.help')}</span><span className="muted">›</span></button>
          <button className="setrow setrow--tap" onClick={() => { void signOut(); }}><span className="setrow__icon"><LogOut size={18} aria-hidden="true" /></span><span className="grow">{t('profile.signOut')}</span></button>
          <button className="setrow setrow--tap" style={{ color: 'var(--danger)' }} onClick={() => { setSettings(false); setDel(true); }}><span className="setrow__icon"><Trash2 size={18} aria-hidden="true" /></span><span className="grow">{t('profile.deleteAccount')}</span></button>
        </div>
      </Sheet>

      <Sheet open={paySheet} onClose={() => setPaySheet(false)} label={t('pay.mine.title')}>
        <div className="stack" style={{ gap: 12 }}>
          <h2 className="h2">{t('pay.mine.title')}</h2>
          {tickets === null && <div className="sk" style={{ height: 64 }} />}
          {tickets && tickets.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('pay.mine.empty')}</p>}
          {tickets && tickets.length > 0 && (
            <div className="list">
              {tickets.map((p) => (
                <Link key={p.id} href={`/a/${p.slug}`} className="lrow lrow--tap" onClick={() => setPaySheet(false)}>
                  <span className="grow" style={{ minWidth: 0 }}><b className="truncate" style={{ display: 'block' }}>{p.title}</b><span className="caption">{formatDateLong(p.time_start, lang)}</span></span>
                  <span className="stack" style={{ gap: 2, alignItems: 'flex-end' }}>
                    <b>{formatInr(p.status === 'refunded' || p.status === 'refund_pending' ? (p.refund_amount_paise ?? p.amount_paise) : p.amount_paise, lang)}</b>
                    <span className="caption">{t(`pay.mine.status.${p.status}`)}</span>
                  </span>
                </Link>
              ))}
            </div>
          )}
          <p className="caption" style={{ margin: 0 }}>{t('pay.mine.note')}</p>
        </div>
      </Sheet>

      <Sheet open={edit} onClose={() => setEdit(false)} label={t('profile.edit')}>
        <div className="stack">
          <h2 className="h2">{t('profile.edit')}</h2>
          <label className="field"><span className="field__label">{t('profile.photo')}</span><input className="field__input" type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} /></label>
          <label className="field"><span className="field__label">{t('profile.bio')}</span><textarea placeholder={t('profile.bioPlaceholder')} value={bio} onChange={(e) => setBio(e.target.value)} maxLength={280} /></label>
          <div className="stack" style={{ gap: 8 }}>
            <span className="field__label">{t('profile.interests')}</span>
            <div className="chips">
              {taxonomy.flatMap((g) => g.interests).filter((i) => !profile.interests.includes(i.tag)).map((i) => (
                <button key={i.tag} className="chip chip--sm" aria-pressed={extra.includes(i.tag)} onClick={() => setExtra((c) => (c.includes(i.tag) ? c.filter((x) => x !== i.tag) : [...c, i.tag]))}>{i.label}</button>
              ))}
            </div>
          </div>
          <button className="btn btn--primary btn--block" onClick={saveEdit}>{t('create.save')}</button>
        </div>
      </Sheet>

      <Sheet open={help} onClose={() => setHelp(false)} label={t('help.title')}>
        <div className="stack">
          <h2 className="h2">{t('help.title')}</h2>
          {[1, 2, 3].map((n) => <details key={n} className="card" style={{ padding: 12 }}><summary style={{ fontWeight: 600, cursor: 'pointer' }}>{t(`help.faq${n}q`)}</summary><p className="muted" style={{ margin: '8px 0 0' }}>{t(`help.faq${n}a`)}</p></details>)}
          <span className="label">{t('help.contact')}</span>
          <span className="caption">{t('help.contactBody')}</span>
          <label className="field"><textarea value={supportText} onChange={(e) => setSupportText(e.target.value)} /></label>
          <button className="btn btn--primary btn--block" disabled={!supportText.trim()} onClick={sendSupport}>{t('help.send')}</button>
        </div>
      </Sheet>

      <Modal open={del} onClose={() => setDel(false)} label={t('profile.deleteAccount')}>
        <div className="stack">
          <h2 className="h2">{t('profile.deleteAccount')}</h2>
          <p className="muted" style={{ margin: 0 }}>{t('profile.deleteBody')}</p>
          <div className="row"><button className="btn btn--ghost grow" onClick={() => setDel(false)}>{t('common.cancel')}</button><button className="btn btn--danger grow" onClick={() => { setDel(false); window.location.assign(FORKHATRI_ACCOUNT_URL); }}>{t('profile.deleteConfirm')}</button></div>
        </div>
      </Modal>
      <Toast text={toast} />
    </>
  );
}
