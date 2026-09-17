'use client';

/* Moments — photos added after the activity by the people who were there,
 * visible to the same people (Strava's "activity creates identity", Meetup's
 * event photos, without a public feed). */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { api, ApiError, resolveMediaUrl } from '@/lib/api';

type Photo = { id: string; member_id: string; display_name: string; url: string; caption: string | null; created_at: string; mine: boolean };

export default function Moments({ occurrenceId, onError }: { occurrenceId: string; onError: (m: string) => void }) {
  const { t } = useTranslation();
  const [photos, setPhotos] = useState<Photo[] | null>(null);
  const [canAdd, setCanAdd] = useState(false);
  const [open, setOpen] = useState<Photo | null>(null);
  const [uploading, setUploading] = useState(false);
  // [FR113] Consent to take a photo is not consent to share it: confirm first, and see who asked not to be pictured.
  const [optOuts, setOptOuts] = useState<string[]>([]);
  const [pending, setPending] = useState<File | null>(null);
  const [okPeople, setOkPeople] = useState(false);
  const [okChildren, setOkChildren] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    api<{ photos: Photo[]; can_add: boolean; opt_outs?: string[] }>(`/occurrences/${occurrenceId}/photos`).then((r) => { setPhotos(r.photos); setCanAdd(r.can_add); setOptOuts(r.opt_outs ?? []); }).catch(() => setPhotos([]));
  }, [occurrenceId]);
  useEffect(load, [load]);

  const cancelPending = () => { setPending(null); setOkPeople(false); setOkChildren(false); if (fileRef.current) fileRef.current.value = ''; };

  const upload = async (file: File | null) => {
    if (!file) return;
    setUploading(true);
    const form = new FormData(); form.append('photo', file);
    try { await api(`/occurrences/${occurrenceId}/photos`, { form }); cancelPending(); load(); }
    catch (e) { onError(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setUploading(false); }
  };

  const removeMe = async (p: Photo) => {
    setOpen(null); setPhotos((cur) => (cur ?? []).filter((x) => x.id !== p.id));
    try { await api(`/occurrences/${occurrenceId}/photos/${p.id}/remove`, { body: {} }); onError(t('moments.removed')); }
    catch (e) { onError(e instanceof ApiError ? e.message : t('state.error')); load(); }
  };

  const remove = async (p: Photo) => {
    setOpen(null); setPhotos((cur) => (cur ?? []).filter((x) => x.id !== p.id));
    await api(`/occurrences/${occurrenceId}/photos/${p.id}`, { method: 'DELETE' }).catch(() => load());
  };

  if (photos && photos.length === 0 && !canAdd) return null;

  return (
    <section className="stack" style={{ gap: 10 }}>
      <div className="row row--between">
        <span className="label">{t('moments.title')}</span>
        {photos && photos.length > 0 && <span className="caption">{t('moments.count', { count: photos.length })}</span>}
      </div>
      {photos === null && <div className="moments">{[0, 1, 2].map((i) => <div key={i} className="sk" style={{ aspectRatio: '1' }} />)}</div>}
      {photos && (
        <div className="moments">
          {canAdd && (
            <button type="button" className="moments__add" onClick={() => fileRef.current?.click()} disabled={uploading}>
              <span style={{ fontSize: '1.4rem' }}>{uploading ? '…' : '＋'}</span>{t('moments.add')}
            </button>
          )}
          {photos.map((p) => (
            <a key={p.id} href={resolveMediaUrl(p.url) ?? '#'} onClick={(e) => { e.preventDefault(); setOpen(p); }} aria-label={p.caption ?? p.display_name}>
              <img src={resolveMediaUrl(p.url) ?? ''} alt={p.caption ?? ''} loading="lazy" />
            </a>
          ))}
        </div>
      )}
      {photos && photos.length === 0 && canAdd && !pending && <p className="caption" style={{ margin: 0 }}>{t('moments.empty')}</p>}
      {pending && (
        <div className="card stack fade-in" style={{ gap: 8 }}>
          <b>{t('moments.beforeSharing')}</b>
          {optOuts.length > 0 && <span className="caption" style={{ color: 'var(--accent-pressed)' }}>{t('moments.optOuts', { names: optOuts.join(', ') })}</span>}
          <label className="row" style={{ gap: 8, alignItems: 'flex-start' }}><input type="checkbox" name="ok-people" checked={okPeople} onChange={(e) => setOkPeople(e.target.checked)} /><span className="caption">{t('moments.okPeople')}</span></label>
          <label className="row" style={{ gap: 8, alignItems: 'flex-start' }}><input type="checkbox" name="ok-children" checked={okChildren} onChange={(e) => setOkChildren(e.target.checked)} /><span className="caption">{t('moments.okChildren')}</span></label>
          <div className="row" style={{ gap: 8 }}>
            <button type="button" className="btn btn--ghost grow" onClick={cancelPending}>{t('common.cancel')}</button>
            <button type="button" className="btn btn--primary grow" disabled={!okPeople || !okChildren || uploading} onClick={() => upload(pending)}>{uploading ? '…' : t('moments.share')}</button>
          </div>
        </div>
      )}
      <input ref={fileRef} type="file" name="moment-photo" accept="image/*" hidden onChange={(e) => setPending(e.target.files?.[0] ?? null)} />
      {open && (
        <>
          <div className="scrim-layer" onClick={() => setOpen(null)} aria-hidden="true" />
          <div className="modal" role="dialog" aria-modal="true" aria-label={open.caption ?? open.display_name} style={{ width: 'min(calc(100% - 32px), 720px)', padding: 12 }}>
            <img src={resolveMediaUrl(open.url) ?? ''} alt={open.caption ?? ''} style={{ width: '100%', borderRadius: 14, maxHeight: '70vh', objectFit: 'contain', background: '#000' }} />
            <div className="row row--between" style={{ marginTop: 10 }}>
              <span className="caption">{open.display_name}{open.caption ? ` · ${open.caption}` : ''}</span>
              <div className="row">{open.mine ? <button className="link" onClick={() => remove(open)}>{t('moments.remove')}</button> : <button className="link" onClick={() => removeMe(open)}>{t('moments.removeMe')}</button>}<button className="btn btn--ghost btn--sm" onClick={() => setOpen(null)}>{t('common.close')}</button></div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
