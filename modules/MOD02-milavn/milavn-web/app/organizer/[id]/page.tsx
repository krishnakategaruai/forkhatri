'use client';

/* Organizer tools (FR056-FR059, FR018, FR019 · UX13 · UI13): attendee list
 * (organizer-only), announcements, co-organizer delegation, QR check-in token
 * + manual mark (attended / no-show, never punitive), close-out, edit/cancel. */

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import QrCode from '@/components/QrCode';
import { Sheet } from '@/components/Sheet';
import { ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl, type Card, type Identity } from '@/lib/api';
import { formatDateLong, formatRelative } from '@/lib/format';

type Attendee = { member_id: string; display_name: string; avatar: string | null; status: string; waitlist_position: number | null; checked_in_at: string | null };
type Detail = Card & { viewer_role: string; co_organizers: { member_id: string; display_name: string }[]; announcements: { id: string; message: string; created_at: string; by: string }[] };

export default function OrganizerPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [d, setD] = useState<Detail | null>(null);
  const [att, setAtt] = useState<Attendee[]>([]);
  const [error, setError] = useState(false);
  const [msg, setMsg] = useState('');
  const [qr, setQr] = useState<{ token: string; qr_payload: string; expires_at: string } | null>(null);
  const [delegate, setDelegate] = useState(false);
  const [members, setMembers] = useState<Identity[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [openedAt] = useState(() => Date.now());
  const [allUpdates, setAllUpdates] = useState(false);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };

  const load = useCallback(() => {
    setError(false);
    Promise.all([api<Detail>(`/occurrences/${id}`), api<Attendee[]>(`/occurrences/${id}/attendees`)]).then(([dd, a]) => { setD(dd); setAtt(a); }).catch(() => setError(true));
  }, [id]);
  useEffect(load, [load]);

  const call = async (fn: () => Promise<unknown>, ok?: string) => { try { await fn(); if (ok) say(ok); load(); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); } };
  const announce = () => call(() => api(`/occurrences/${id}/announcements`, { body: { message: msg } }).then(() => setMsg('')), '✓');
  const mark = (m: Attendee, outcome: string) => call(() => api(`/occurrences/${id}/attendance`, { body: { member_id: m.member_id, outcome } }));
  const token = () => call(async () => setQr(await api(`/occurrences/${id}/checkin/token`, { body: {} })));
  const complete = () => call(() => api(`/occurrences/${id}/complete`, { body: {} }), '✓');
  const openDelegate = async () => { setDelegate(true); setMembers(await api<Identity[]>('/identity/dev/members')); };
  const grant = (m: Identity) => call(() => api(`/occurrences/${id}/co-organizers`, { body: { member_id: m.member_id } }).then(() => setDelegate(false)), '✓');
  const revoke = (memberId: string) => call(() => api(`/occurrences/${id}/co-organizers/${memberId}`, { method: 'DELETE' }));

  const going = att.filter((a) => ['going', 'checked_in', 'attended'].includes(a.status));
  const wait = att.filter((a) => a.status === 'waitlisted');
  const interested = att.filter((a) => a.status === 'interested');
  const past = d ? new Date(d.time_start).getTime() < openedAt : false;

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" aria-label={t('common.back')} onClick={() => router.back()}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
        </button>
        <h1 style={{ fontSize: '1.25rem' }}>{t('detail.manage')}</h1>
        <span style={{ width: 44 }} />
      </header>
      <main className="screen" style={{ gap: 20 }}>
        {error && <ErrorState onRetry={load} />}
        {d && (
          <>
            <div>
              <div className="h2">{d.title}</div>
              <div className="caption">{formatDateLong(d.time_start)} · {d.location_label}</div>
            </div>
            <div className="row">
              <div className="stat"><b>{going.length}</b><span>{t('detail.going')}</span></div>
              <div className="stat"><b>{wait.length}</b><span>{t('card.youAre.waitlisted')}</span></div>
              <div className="stat"><b>{interested.length}</b><span>{t('detail.interested')}</span></div>
              {d.capacity !== null && <div className="stat"><b>{d.capacity}</b><span>{t('detail.capacity')}</span></div>}
            </div>
            <div className="grid-2">
              <Link href={`/create?edit=${d.id}`} className="btn btn--secondary">{t('create.edit')}</Link>
              <Link href={`/a/${d.slug}`} className="btn btn--secondary">{t('create.view')}</Link>
            </div>

            <section className="card stack" style={{ gap: 10 }}>
              <span className="label">{t('detail.announcements')}</span>
              <label className="field"><textarea value={msg} onChange={(e) => setMsg(e.target.value)} placeholder="…" /></label>
              <button className="btn btn--primary" disabled={!msg.trim()} onClick={announce}>{t('detail.sendUpdate')}</button>
              {d.announcements.length > 0 && (
                <div className="stack" style={{ gap: 6 }}>
                  <span className="caption">{t('detail.updatesSent')}</span>
                  {(allUpdates ? d.announcements : d.announcements.slice(0, 3)).map((a) => (
                    <div key={a.id} className="card" style={{ padding: 10 }}>
                      <p style={{ margin: 0 }}>{a.message}</p>
                      <span className="caption">{a.by} · {formatRelative(a.created_at)}</span>
                    </div>
                  ))}
                  {!allUpdates && d.announcements.length > 3 && <button className="link" style={{ alignSelf: 'flex-start' }} onClick={() => setAllUpdates(true)}>{t('detail.showAllUpdates', { count: d.announcements.length })}</button>}
                </div>
              )}
            </section>

            <section className="stack" style={{ gap: 8 }}>
              <div className="row row--between"><span className="label">{t('detail.checkIn')}</span><button className="btn btn--secondary btn--sm" onClick={token}>{t('detail.qrCheckIn')}</button></div>
              {qr && <div className="stack" style={{ alignItems: 'center', gap: 6 }}><QrCode value={qr.qr_payload} size={180} label="Check-in QR" /><span className="caption">{t('detail.expires', { time: new Date(qr.expires_at).toLocaleTimeString() })}</span></div>}
              <div className="list">
                {[...going, ...wait, ...interested].map((a) => (
                  <div key={a.member_id} className="lrow" style={{ minHeight: 56 }}>
                    {a.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(a.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
                    <span className="grow"><Link href={`/p/${a.member_id}`}><b>{a.display_name}</b></Link><br /><span className="caption">{t(`card.youAre.${a.status}`, { defaultValue: a.status })}{a.waitlist_position ? ` #${a.waitlist_position}` : ''}</span></span>
                    {['going', 'interested', 'waitlisted'].includes(a.status) && <button className="btn btn--secondary btn--sm" onClick={() => mark(a, 'checked_in')}>✓ In</button>}
                    {['checked_in', 'going'].includes(a.status) && past && <button className="btn btn--ghost btn--sm" onClick={() => mark(a, 'attended')}>Attended</button>}
                    {['going', 'interested'].includes(a.status) && past && <button className="btn btn--ghost btn--sm" onClick={() => mark(a, 'no_show')}>No-show</button>}
                  </div>
                ))}
                {att.length === 0 && <span className="caption">{t('detail.noRsvps')}</span>}
              </div>
            </section>

            <section className="stack" style={{ gap: 8 }}>
              <div className="row row--between"><span className="label">{t('detail.coOrganizers')}</span>{d.viewer_role === 'organizer' && <button className="btn btn--secondary btn--sm" onClick={openDelegate}>+ {t('detail.delegate')}</button>}</div>
              {d.co_organizers.length === 0 && <span className="caption">{t('detail.noneYet')}</span>}
              {d.co_organizers.map((c) => <div key={c.member_id} className="row row--between"><span>{c.display_name}</span>{d.viewer_role === 'organizer' && <button className="link" onClick={() => revoke(c.member_id)}>{t('detail.revoke')}</button>}</div>)}
            </section>

            {past && <button className="btn btn--secondary btn--block" onClick={complete}>{t('detail.markHeld')} ✓</button>}
          </>
        )}
      </main>
      <Sheet open={delegate} onClose={() => setDelegate(false)} label={t('detail.delegate')}>
        <div className="list">
          {members.filter((m) => m.member_id !== d?.host_member_id).map((m) => (
            <button key={m.member_id} className="lrow lrow--tap" style={{ width: '100%', textAlign: 'left' }} onClick={() => grant(m)}>
              {m.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(m.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
              <span className="grow">{m.display_name}</span>
            </button>
          ))}
        </div>
      </Sheet>
      <Toast text={toast} />
    </>
  );
}
