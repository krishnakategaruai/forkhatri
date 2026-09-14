'use client';

/* Place picker — replaces the browser's native <select> for city / locality.
 * One tap opens a sheet with search and localities grouped by zone; the
 * chosen place reads back as "Hyderabad · Jubilee Hills". Approximate places
 * only (FR038): there is no street or pin here by design. */

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Sheet } from '@/components/Sheet';
import { api } from '@/lib/api';

export type Hierarchy = { city: string; zones: { zone: string; localities: { locality: string }[] }[] }[];

export default function PlacePicker({ city, locality, onChange, allowCityOnly = true, label }: { city: string; locality: string; onChange: (city: string, locality: string) => void; allowCityOnly?: boolean; label?: string }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [hier, setHier] = useState<Hierarchy>([]);
  const [pickCity, setPickCity] = useState(city);

  useEffect(() => { api<Hierarchy>('/profile/localities').then(setHier).catch(() => undefined); }, []);
  useEffect(() => { setPickCity(city); }, [city]);

  const zones = useMemo(() => hier.find((h) => h.city === pickCity)?.zones ?? [], [hier, pickCity]);
  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return zones.map((z) => ({ zone: z.zone, localities: z.localities.filter((l) => !needle || l.locality.toLowerCase().includes(needle) || z.zone.toLowerCase().includes(needle)) })).filter((z) => z.localities.length > 0);
  }, [zones, q]);

  const choose = (loc: string) => { onChange(pickCity, loc); setOpen(false); setQ(''); };

  return (
    <>
      <button type="button" className="picker" onClick={() => setOpen(true)} aria-haspopup="dialog" aria-label={label ?? t('place.label')}>
        <span className="picker__icon" aria-hidden="true">📍</span>
        <span className="grow" style={{ textAlign: 'left' }}>
          {city ? <><b>{locality || t('place.cityWide')}</b><span className="caption" style={{ display: 'block' }}>{city}</span></> : <span className="muted">{t('place.choose')}</span>}
        </span>
        <span className="muted" aria-hidden="true">›</span>
      </button>
      <Sheet open={open} onClose={() => setOpen(false)} label={label ?? t('place.label')}>
        <div className="stack" style={{ gap: 12 }}>
          <h2 className="h2">{label ?? t('place.label')}</h2>
          <div className="chips chips--scroll" aria-label={t('onboarding.city')}>
            {hier.map((h) => <button key={h.city} type="button" className="chip chip--sm" aria-pressed={pickCity === h.city} onClick={() => setPickCity(h.city)}>{h.city}</button>)}
          </div>
          {pickCity && (
            <>
              <label className="field"><input className="field__input" type="search" placeholder={t('place.search')} value={q} onChange={(e) => setQ(e.target.value)} autoFocus /></label>
              {allowCityOnly && !q && <button type="button" className="chip chip--sm" aria-pressed={!locality && city === pickCity} onClick={() => choose('')}>{t('place.cityWide')} · {pickCity}</button>}
              <div className="stack" style={{ gap: 10, maxHeight: '48vh', overflowY: 'auto' }}>
                {filtered.map((z) => (
                  <div key={z.zone} className="stack" style={{ gap: 6 }}>
                    <span className="label">{z.zone}</span>
                    <div className="chips">
                      {z.localities.map((l) => <button key={l.locality} type="button" className="chip chip--sm" aria-pressed={locality === l.locality && city === pickCity} onClick={() => choose(l.locality)}>{l.locality}</button>)}
                    </div>
                  </div>
                ))}
                {filtered.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('place.none')}</p>}
              </div>
            </>
          )}
        </div>
      </Sheet>
    </>
  );
}
