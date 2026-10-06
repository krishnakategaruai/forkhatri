'use client';

/* Place picker — live India place search (state, district, city, area).
 * One tap opens a sheet; typing searches (debounced, the API caches and rate-limits
 * for the free OpenStreetMap data behind it); the pick reads back as
 * "Kondapur" over "Hyderabad, Telangana". Approximate places only (FR038): areas
 * and their centre, never a street or a pin by design. */

import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Sheet } from '@/components/Sheet';
import { api } from '@/lib/api';

export type PickedPlace = {
  kind?: string; label?: string;
  locality_city: string; locality_zone: string | null; locality_locality: string | null; locality_state: string | null;
  lat: number | null; lon: number | null;
};

const MIN_CHARS = 2;
const DEBOUNCE_MS = 450;

export default function PlacePicker({ city, locality, state, onChange, label }: { city: string; locality: string; state?: string | null; onChange: (p: PickedPlace) => void; label?: string }) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [hits, setHits] = useState<PickedPlace[]>([]);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const seq = useRef(0);

  useEffect(() => {
    const needle = q.trim();
    if (!open || needle.length < MIN_CHARS) { setHits([]); setBusy(false); setFailed(false); return; }
    const mine = ++seq.current;
    setBusy(true);
    const timer = setTimeout(() => {
      api<PickedPlace[]>(`/profile/places?q=${encodeURIComponent(needle)}`)
        .then((r) => { if (mine === seq.current) { setHits(r); setFailed(false); } })
        .catch(() => { if (mine === seq.current) { setHits([]); setFailed(true); } })
        .finally(() => { if (mine === seq.current) setBusy(false); });
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [q, open, i18n.language]);

  const choose = (p: PickedPlace) => { onChange(p); setOpen(false); setQ(''); };
  const context = [locality ? city : null, state].filter(Boolean).join(', ');
  const needleOk = q.trim().length >= MIN_CHARS;

  return (
    <>
      <button type="button" className="picker" onClick={() => setOpen(true)} aria-haspopup="dialog" aria-label={label ?? t('place.label')}>
        <span className="picker__icon" aria-hidden="true">📍</span>
        <span className="grow" style={{ textAlign: 'left' }}>
          {city ? <><b>{locality || city}</b>{(context || (!locality && state)) && <span className="caption" style={{ display: 'block' }}>{locality ? context : state}</span>}</> : <span className="muted">{t('place.choose')}</span>}
        </span>
        <span className="muted" aria-hidden="true">›</span>
      </button>
      <Sheet open={open} onClose={() => setOpen(false)} label={label ?? t('place.label')}>
        <div className="stack" style={{ gap: 12 }}>
          <h2 className="h2">{label ?? t('place.label')}</h2>
          <label className="field">
            <input className="field__input" type="search" placeholder={t('place.search')} value={q} onChange={(e) => setQ(e.target.value)} autoFocus autoComplete="off" aria-label={t('place.search')} />
          </label>
          <div className="stack" style={{ gap: 6, maxHeight: '52vh', overflowY: 'auto' }} aria-live="polite">
            {!needleOk && <p className="caption" style={{ margin: 0 }}>{t('place.hint')}</p>}
            {needleOk && busy && <p className="caption" style={{ margin: 0 }}>{t('place.searching')}</p>}
            {needleOk && !busy && failed && <p className="field__error" role="alert" style={{ margin: 0 }}>{t('place.unavailable')}</p>}
            {needleOk && !busy && !failed && hits.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('place.none')}</p>}
            {hits.map((p, i) => (
              <button key={`${p.label}-${i}`} type="button" className="picker" onClick={() => choose(p)}>
                <span className="grow" style={{ textAlign: 'left' }}>
                  <b>{p.locality_locality || p.locality_city}</b>
                  <span className="caption" style={{ display: 'block' }}>{(p.label ?? '').split(', ').slice(1).join(', ')}</span>
                </span>
                {p.kind && <span className="pill pill--neutral">{t(`place.kind.${p.kind}`)}</span>}
              </button>
            ))}
          </div>
          <p className="caption" style={{ margin: 0 }}>{t('place.approx')}</p>
        </div>
      </Sheet>
    </>
  );
}
