'use client';

/* Circle photo albums (Phase 2, Step 6; migration 053) — the top of a circle's Photos tab.
 * Any member names an album and adds photos (several at once); an album opens in place, no new
 * screen. The person who added a photo, or an organizer / assistant, removes it; organizers and
 * assistants remove a whole album with a second, deliberate tap. Photos are private circle media. */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ImagePlus, Plus, X } from 'lucide-react';

import { api, ApiError, resolveMediaUrl } from '@/lib/api';

type Album = { id: string; name: string; mine: boolean; created_at: string; photo_count: number; covers: string[] };
type AlbumPhoto = { id: string; url: string; caption: string | null; created_at: string; mine: boolean; added_by: string };
type AlbumDetail = { id: string; name: string; mine: boolean; photos: AlbumPhoto[] };

type Props = {
  circleId: string;
  canManage: boolean;
  maxPerUpload: number;
  photoMb: number;
  say: (text: string) => void;
  openPhotos: (urls: string[], index: number) => void;
};

export default function CircleAlbums({ circleId, canManage, maxPerUpload, photoMb, say, openPhotos }: Props) {
  const { t } = useTranslation();
  const [albums, setAlbums] = useState<Album[] | null>(null);
  const [open, setOpen] = useState<AlbumDetail | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);

  const load = useCallback(() => { api<Album[]>(`/circles/${circleId}/albums`).then(setAlbums).catch(() => setAlbums([])); }, [circleId]);
  useEffect(load, [load]);
  const openAlbum = useCallback((id: string) => {
    setConfirmRemove(false);
    api<AlbumDetail>(`/circles/${circleId}/albums/${id}`).then(setOpen).catch((e) => say(e instanceof ApiError ? e.message : t('state.error')));
  }, [circleId, say, t]);

  const create = async () => {
    if (!name.trim() || busy) return;
    setBusy(true);
    try {
      const a = await api<Album>(`/circles/${circleId}/albums`, { body: { name: name.trim() } });
      setName(''); setCreating(false); load(); openAlbum(a.id);
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(false); }
  };

  const addPhotos = async (files: File[]) => {
    if (!open || files.length === 0) return;
    if (files.length > maxPerUpload) { say(t('cs.tooManyPhotos', { n: maxPerUpload })); return; }
    const big = files.find((f) => f.size > photoMb * 1024 * 1024);
    if (big) { say(t('cs.tooBig', { name: big.name, mb: photoMb })); return; }
    setBusy(true);
    try {
      const form = new FormData();
      files.forEach((f) => form.append('photos', f));
      const r = await api<{ added: number }>(`/circles/${circleId}/albums/${open.id}/photos`, { form });
      say(t('cs.added', { count: r.added }));
      openAlbum(open.id); load();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(false); }
  };

  const removePhoto = async (p: AlbumPhoto) => {
    if (!open) return;
    try { await api(`/circles/${circleId}/albums/${open.id}/photos/${p.id}`, { method: 'DELETE' }); say(t('cs.photoRemoved')); openAlbum(open.id); load(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const removeAlbum = async () => {
    if (!open) return;
    if (!confirmRemove) { setConfirmRemove(true); return; }
    try { await api(`/circles/${circleId}/albums/${open.id}`, { method: 'DELETE' }); say(t('cs.albumRemoved')); setOpen(null); load(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const picker = (
    <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden
      onChange={(e) => { const fs = Array.from(e.target.files ?? []); e.target.value = ''; void addPhotos(fs); }} />
  );

  if (open) {
    return (
      <section className="stack cx-albums" style={{ gap: 12 }} aria-label={open.name}>
        <div className="cx-sechead" style={{ alignItems: 'center' }}>
          <button className="cx-textbtn row" style={{ gap: 6 }} onClick={() => { setOpen(null); setConfirmRemove(false); }}><ArrowLeft size={16} strokeWidth={1.75} aria-hidden="true" />{t('cs.allAlbums')}</button>
          <button className="cx-btn cx-btn--quiet" disabled={busy} onClick={() => fileInput.current?.click()}><ImagePlus size={16} strokeWidth={1.75} aria-hidden="true" />{busy ? t('cs.adding') : t('cs.addToAlbum')}</button>
        </div>
        <div>
          <h3 className="cx-h2" style={{ margin: 0 }}>{open.name}</h3>
          <span className="cx-caption">{t('cs.photosCount', { count: open.photos.length })}</span>
        </div>
        {open.photos.length === 0 ? <p className="cx-caption" style={{ margin: 0 }}>{t('cs.albumEmpty')}</p> : (
          <div className="cx-photos cx-photos--album">
            {open.photos.map((p, i) => (
              <div key={p.id} className="cx-albumtile">
                <button className="cx-plain" onClick={() => openPhotos(open.photos.map((x) => x.url), i)} aria-label={t('cs.photoOf', { i: i + 1, n: open.photos.length })}>
                  <img src={resolveMediaUrl(p.url) ?? ''} alt={p.caption ?? t('cs.addedBy', { name: p.added_by })} loading="lazy" />
                </button>
                {(p.mine || canManage) && (
                  <button className="cx-albumtile__x" aria-label={t('cs.removePhoto')} onClick={() => removePhoto(p)}><X size={14} strokeWidth={2} /></button>
                )}
              </div>
            ))}
          </div>
        )}
        {canManage && (
          <button className={`cx-btn ${confirmRemove ? 'cx-btn--danger' : 'cx-btn--danger-text'}`} style={{ alignSelf: 'flex-start' }} onClick={removeAlbum}>
            {confirmRemove ? t('cs.removeAlbumConfirm') : t('cs.removeAlbum')}
          </button>
        )}
        {picker}
      </section>
    );
  }

  return (
    <section className="stack cx-albums" style={{ gap: 12, paddingTop: 16 }} aria-label={t('cs.albums')}>
      <div className="cx-sechead" style={{ alignItems: 'center' }}>
        <span className="cx-label">{t('cs.albums')}</span>
        {!creating && <button className="cx-btn cx-btn--quiet" onClick={() => setCreating(true)}><Plus size={16} strokeWidth={1.75} aria-hidden="true" />{t('cs.newAlbum')}</button>}
      </div>
      {creating && (
        <div className="row" style={{ gap: 8 }}>
          <input className="cx-input grow" name="album-name" autoFocus maxLength={60} placeholder={t('cs.albumNamePlaceholder')} aria-label={t('cs.albumName')}
            value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void create(); } }} />
          <button className="cx-btn cx-btn--ghost" onClick={() => { setCreating(false); setName(''); }}>{t('common.cancel')}</button>
          <button className="cx-btn cx-btn--primary" disabled={!name.trim() || busy} onClick={create}>{t('cs.create')}</button>
        </div>
      )}
      {albums !== null && albums.length === 0 && !creating && <p className="cx-caption" style={{ margin: 0 }}>{t('cs.noAlbums')}</p>}
      {albums && albums.length > 0 && (
        <div className="cx-albumgrid">
          {albums.map((a) => (
            <button key={a.id} className="cx-plain cx-album" onClick={() => openAlbum(a.id)}>
              <span className={`cx-album__cover cx-album__cover--${Math.min(a.covers.length, 4)}`}>
                {a.covers.slice(0, 4).map((u) => <img key={u} src={resolveMediaUrl(u) ?? ''} alt="" loading="lazy" />)}
              </span>
              <span className="cx-strong truncate">{a.name}</span>
              <span className="cx-caption">{t('cs.photosCount', { count: a.photo_count })}</span>
            </button>
          ))}
        </div>
      )}
      {picker}
    </section>
  );
}
