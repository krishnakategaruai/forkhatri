'use client';

/* Moderation queue (FR065 · UX20 · UI20) rendered against the shared Admin &
 * Governance Console contract (TR-PLAT-01): queue list -> case detail ->
 * human action (dismiss / warn / restrict / escalate), each audited. Until the
 * platform console ships, this page is the console's queue-list component. */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Modal } from '@/components/Sheet';
import { EmptyState, ErrorState, Toast } from '@/components/States';
import { api, ApiError } from '@/lib/api';
import { formatRelative } from '@/lib/format';

type Item = { item_id: string; item_type: string; submitted_at: string; priority: string; status: string; summary_text: string; reason?: string; subject_type?: string; subject_title?: string | null };
type Case = { item_id: string; case_detail: { reporter: { display_name: string }; subject: Record<string, string>; reason: string; description: string | null; status: string; created_at: string; history: { action: string; by: string; notes: string | null; at: string }[] }; available_actions: string[] };

export default function ModerationPage() {
  const { t } = useTranslation();
  const [status, setStatus] = useState('open');
  const [items, setItems] = useState<Item[] | null>(null);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState<Case | null>(null);
  const [confirm, setConfirm] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(() => { setError(false); setItems(null); api<Item[]>(`/milavn/admin/moderation?status=${status}`).then(setItems).catch(() => setError(true)); }, [status]);
  useEffect(load, [load]);

  const openCase = async (it: Item) => { try { setOpen(await api<Case>(`/milavn/admin/moderation/${it.item_id}`)); } catch (e) { setToast(e instanceof ApiError ? e.message : t('state.error')); } };
  const act = async () => {
    if (!open || !confirm) return;
    try { await api(`/milavn/admin/moderation/${open.item_id}/actions/${confirm}`, { body: { notes } }); setConfirm(null); setNotes(''); setOpen(null); load(); }
    catch (e) { setToast(e instanceof ApiError ? e.message : t('state.error')); }
  };

  return (
    <>
      <header className="topbar"><h1>{t('moderation.title')}</h1></header>
      <main className="screen">
        <div className="chips chips--scroll">{['open', 'in_review', 'actioned', 'dismissed'].map((s) => <button key={s} className="chip chip--sm" aria-pressed={status === s} onClick={() => setStatus(s)}>{t(`moderation.${s}`)}</button>)}</div>
        {error && <ErrorState onRetry={load} />}
        {items && items.length === 0 && <EmptyState message={t('moderation.empty')} />}
        {items && items.map((it) => (
          <button key={it.item_id} className="lrow lrow--tap" style={{ width: '100%', textAlign: 'left' }} onClick={() => openCase(it)}>
            <span className={`pill ${it.priority === 'high' ? 'pill--danger' : 'pill--neutral'}`}>{it.priority}</span>
            <span className="grow">
              <b>{it.reason ? t(`safety.reasons.${it.reason}`, { defaultValue: it.reason }) : it.summary_text}{it.subject_title ? ` · “${it.subject_title}”` : ''}</b><br />
              <span className="caption">{t('moderation.reported', { type: t(`moderation.types.${it.subject_type ?? 'occurrence'}`, { defaultValue: it.subject_type }) })} · {formatRelative(it.submitted_at)}</span>
            </span>
            <span className="muted">›</span>
          </button>
        ))}
      </main>

      <Modal open={open !== null} onClose={() => setOpen(null)} label="Case">
        {open && (
          <div className="stack">
            <h2 className="h2">{t(`safety.reasons.${open.case_detail.reason}`, { defaultValue: open.case_detail.reason })}</h2>
            <div className="caption">{t('moderation.reporter')}: {open.case_detail.reporter.display_name} · {formatRelative(open.case_detail.created_at)}</div>
            <div className="caption">{t('moderation.subject')}: {open.case_detail.subject.title ?? open.case_detail.subject.display_name ?? open.case_detail.subject.type} {open.case_detail.subject.organizer ? `(by ${open.case_detail.subject.organizer})` : ''}</div>
            {open.case_detail.description && <p style={{ margin: 0 }}>{open.case_detail.description}</p>}
            {open.case_detail.history.map((h, i) => <div key={i} className="caption">↳ {h.action} by {h.by} {h.notes ? `— ${h.notes}` : ''}</div>)}
            {open.available_actions.length > 0 && (
              <>
                <label className="field"><span className="field__label">{t('moderation.notes')}</span><textarea value={notes} onChange={(e) => setNotes(e.target.value)} /></label>
                <div className="grid-2">
                  {open.available_actions.map((a) => <button key={a} className={`btn btn--sm ${['restrict', 'escalate'].includes(a) ? 'btn--danger-outline' : 'btn--secondary'}`} onClick={() => setConfirm(a)}>{t(`moderation.actions.${a}`)}</button>)}
                </div>
              </>
            )}
            {confirm && (
              <div className="card stack" style={{ borderColor: 'var(--danger)' }}>
                <p style={{ margin: 0 }}>{t('moderation.confirm', { action: t(`moderation.actions.${confirm}`) })}</p>
                <div className="row"><button className="btn btn--ghost grow" onClick={() => setConfirm(null)}>{t('common.cancel')}</button><button className="btn btn--danger grow" onClick={act}>{t('common.ok')}</button></div>
              </div>
            )}
          </div>
        )}
      </Modal>
      <Toast text={toast} />
    </>
  );
}
