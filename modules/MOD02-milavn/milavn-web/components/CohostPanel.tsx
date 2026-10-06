'use client';

/* Circles co-hosting an event (Phase 2, Step 6; migration 053).
 * Everyone who can see the event sees which circles host it together. The event's hosts invite a
 * circle in place (search, one tap); that circle's organizer accepts on their circle's page. Pending
 * invitations show only to the hosts, with a one-tap withdraw. Nothing renders when there is
 * nothing to show and the viewer cannot invite. */

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { api, ApiError, resolveMediaUrl } from '@/lib/api';

type Cohost = { circle_id: string; name: string; status: 'pending' | 'accepted' | 'declined'; cover_url: string | null };
type Candidate = { id: string; name: string; member_count: number; viewer_role: string | null; locality_label: string | null; cover_url: string | null };

export default function CohostPanel({ occurrenceId, ended }: { occurrenceId: string; ended?: boolean }) {
  const { t } = useTranslation();
  const [rows, setRows] = useState<Cohost[]>([]);
  const [canInvite, setCanInvite] = useState(false);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [cands, setCands] = useState<Candidate[] | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(() => {
    api<{ cohosts: Cohost[]; can_invite: boolean }>(`/occurrences/${occurrenceId}/cohosts`)
      .then((r) => { setRows(r.cohosts); setCanInvite(r.can_invite); })
      .catch(() => { setRows([]); setCanInvite(false); });
  }, [occurrenceId]);
  useEffect(load, [load]);

  // Search as the host types (their own circles show before anything is typed).
  useEffect(() => {
    if (!open) return;
    const ctl = new AbortController();
    const handle = setTimeout(() => {
      api<Candidate[]>(`/occurrences/${occurrenceId}/cohost-candidates${q.trim() ? `?q=${encodeURIComponent(q.trim())}` : ''}`, { signal: ctl.signal })
        .then(setCands).catch(() => {});
    }, 250);
    return () => { clearTimeout(handle); ctl.abort(); };
  }, [open, q, occurrenceId]);

  const invite = async (c: Candidate) => {
    setBusy(c.id);
    try {
      const r = await api<{ status: string }>(`/occurrences/${occurrenceId}/cohosts`, { body: { circle_id: c.id } });
      setNote(r.status === 'accepted' ? t('cs.nowCohosting', { name: c.name }) : t('cs.invited', { name: c.name }));
      setOpen(false); setQ(''); setCands(null); load();
    } catch (e) { setNote(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(null); }
  };

  const remove = async (c: Cohost) => {
    setBusy(c.circle_id);
    try { await api(`/occurrences/${occurrenceId}/cohosts/${c.circle_id}`, { method: 'DELETE' }); load(); }
    catch (e) { setNote(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(null); }
  };

  const accepted = rows.filter((r) => r.status === 'accepted');
  const pending = rows.filter((r) => r.status === 'pending');
  if (accepted.length === 0 && !(canInvite && !ended)) return null;

  return (
    <section className="stack fade-in cohost" style={{ gap: 10 }} aria-label={t('cs.hostedWith')}>
      {accepted.length > 0 && <span className="label">{t('cs.hostedWith')}</span>}
      {accepted.map((c) => (
        <div key={c.circle_id} className="row cohost__row" style={{ gap: 12 }}>
          <Link href={`/circles/${c.circle_id}`} className="row grow" style={{ gap: 12, minWidth: 0 }}>
            {c.cover_url ? <img className="cohost__cover" src={resolveMediaUrl(c.cover_url) ?? ''} alt="" /> : <span className="cohost__cover" aria-hidden="true" />}
            <b className="truncate">{c.name}</b>
          </Link>
          {canInvite && <button className="btn btn--ghost btn--sm" disabled={busy === c.circle_id} onClick={() => remove(c)}>{t('cs.stopCohosting')}</button>}
        </div>
      ))}
      {canInvite && pending.map((c) => (
        <div key={c.circle_id} className="row cohost__row" style={{ gap: 12 }}>
          <span className="caption grow">{t('cs.pending', { name: c.name })}</span>
          <button className="btn btn--ghost btn--sm" disabled={busy === c.circle_id} onClick={() => remove(c)}>{t('cs.withdraw')}</button>
        </div>
      ))}
      {canInvite && !ended && (open ? (
        <div className="stack" style={{ gap: 8 }}>
          <input className="field__input" name="cohost-search" autoFocus placeholder={t('cs.searchCircles')} aria-label={t('cs.searchCircles')} value={q} onChange={(e) => setQ(e.target.value)} />
          {cands && cands.length === 0 && <span className="caption">{t('cs.noCandidates')}</span>}
          {(cands ?? []).map((c) => (
            <div key={c.id} className="row cohost__row" style={{ gap: 12 }}>
              {c.cover_url ? <img className="cohost__cover" src={resolveMediaUrl(c.cover_url) ?? ''} alt="" /> : <span className="cohost__cover" aria-hidden="true" />}
              <span className="grow" style={{ minWidth: 0 }}>
                <b className="truncate" style={{ display: 'block' }}>{c.name}</b>
                <span className="caption">{[t('circles.members', { count: c.member_count }), c.locality_label].filter(Boolean).join(' · ')}</span>
              </span>
              <button className="btn btn--secondary btn--sm" disabled={busy === c.id} onClick={() => invite(c)}>{t('cs.invite')}</button>
            </div>
          ))}
          <span className="caption">{t('cs.cohostHint')}</span>
          <button className="btn btn--ghost btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => { setOpen(false); setQ(''); }}>{t('common.cancel')}</button>
        </div>
      ) : (
        <button className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => { setOpen(true); setNote(null); }}>{t('cs.inviteCircle')}</button>
      ))}
      {note && <span className="caption" role="status">{note}</span>}
    </section>
  );
}
