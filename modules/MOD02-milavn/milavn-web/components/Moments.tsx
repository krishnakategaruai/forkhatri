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
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    api<{ photos: Photo[]; can_add: boolean }>(`/occurrences/${occurrenceId}/photos`).then((r) => { setPhotos(r.photos); setCanAdd(r.can_add); }).catch(() => setPhotos([]));
  }, [occurrenceId]);
  useEffect(load, [load]);

  const upload = async (file: File | undefined) => {
    if (!file) return;
    setUploading(true);
    const form = new FormData(); form.append('photo', file);
    try { await api(`/occurrences/${occurrenceId}/photos`, { form }); load(); }
    catch (e) { onError(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ''; }
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
      {photos && photos.length === 0 && canAdd && <p className="caption" style={{ margin: 0 }}>{t('moments.empty')}</p>}
      <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => upload(e.target.files?.[0])} />
      {open && (
        <>
          <div className="scrim-layer" onClick={() => setOpen(null)} aria-hidden="true" />
          <div className="modal" role="dialog" aria-modal="true" aria-label={open.caption ?? open.display_name} style={{ width: 'min(calc(100% - 32px), 720px)', padding: 12 }}>
            <img src={resolveMediaUrl(open.url) ?? ''} alt={open.caption ?? ''} style={{ width: '100%', borderRadius: 14, maxHeight: '70vh', objectFit: 'contain', background: '#000' }} />
            <div className="row row--between" style={{ marginTop: 10 }}>
              <span className="caption">{open.display_name}{open.caption ? ` · ${open.caption}` : ''}</span>
              <div className="row">{open.mine && <button className="link" onClick={() => remove(open)}>{t('moments.remove')}</button>}<button className="btn btn--ghost btn--sm" onClick={() => setOpen(null)}>{t('common.close')}</button></div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
