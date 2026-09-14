'use client';

/* When picker — replaces the browser's native datetime box. A day strip for
 * the next two weeks, then time as chips (the hours people actually meet),
 * with a small time field for anything else. Value in/out is the same
 * "YYYY-MM-DDTHH:MM" local string the form already uses. */

import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

const HOURS: [string, number, number][] = [['6 am', 6, 0], ['7 am', 7, 0], ['8 am', 8, 0], ['10 am', 10, 0], ['12 pm', 12, 0], ['4 pm', 16, 0], ['6 pm', 18, 0], ['7 pm', 19, 0], ['8 pm', 20, 0], ['9 pm', 21, 0]];
const LOCALE: Record<string, string> = { en: 'en-IN', hi: 'hi-IN', te: 'te-IN' };

function pad(n: number) { return String(n).padStart(2, '0'); }
function toValue(d: Date) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`; }

export default function WhenPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const { t, i18n } = useTranslation();
  const loc = LOCALE[i18n.language] ?? 'en-IN';
  const current = value ? new Date(value) : null;
  const days = useMemo(() => Array.from({ length: 14 }, (_, i) => { const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() + i); return d; }), []);
  const sameDay = (a: Date, b: Date) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

  const pickDay = (d: Date) => { const n = new Date(d); n.setHours(current?.getHours() ?? 18, current?.getMinutes() ?? 0, 0, 0); onChange(toValue(n)); };
  const pickHour = (h: number, m: number) => { const n = current ? new Date(current) : new Date(); if (!current) n.setDate(n.getDate() + 1); n.setHours(h, m, 0, 0); onChange(toValue(n)); };
  const setTime = (hhmm: string) => { const [h, m] = hhmm.split(':').map(Number); if (Number.isFinite(h)) pickHour(h, m || 0); };

  return (
    <div className="stack" style={{ gap: 10 }}>
      <div className="date-strip" role="listbox" aria-label={t('when.day')}>
        {days.map((d, i) => {
          const on = !!current && sameDay(current, d);
          return (
            <button key={d.toISOString()} type="button" role="option" aria-selected={on} aria-pressed={on} onClick={() => pickDay(d)}>
              <small>{i === 0 ? t('when.today') : i === 1 ? t('when.tomorrow') : new Intl.DateTimeFormat(loc, { weekday: 'short' }).format(d)}</small><b>{d.getDate()}</b>
            </button>
          );
        })}
      </div>
      <div className="chips chips--scroll" aria-label={t('when.time')}>
        {HOURS.map(([label, h, m]) => <button key={label} type="button" className="chip chip--sm" aria-pressed={!!current && current.getHours() === h && current.getMinutes() === m} onClick={() => pickHour(h, m)}>{label}</button>)}
        <input className="field__input" type="time" aria-label={t('when.time')} value={current ? `${pad(current.getHours())}:${pad(current.getMinutes())}` : ''} onChange={(e) => setTime(e.target.value)} style={{ minHeight: 36, width: 'auto', padding: '0 10px', borderRadius: 999 }} />
      </div>
      {current && <div className="caption" aria-live="polite">{new Intl.DateTimeFormat(loc, { weekday: 'long', day: 'numeric', month: 'long', hour: 'numeric', minute: '2-digit' }).format(current)}</div>}
    </div>
  );
}
