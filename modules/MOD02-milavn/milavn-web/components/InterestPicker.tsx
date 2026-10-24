'use client';

/* Interest picker (FR003, redesigned 2026-10-06 · mockup C): nine broad picture tiles in the member's
 * language. A tile starts closed and opens its own few choices underneath (a taxonomy picker never
 * dumps every option at once); a count on the tile says how many are picked inside. "Other — add your
 * own" keeps the member's own words. Used by the optional Home card and by Edit profile, where chips
 * can be removed as well as added. Controlled: `value` is the full list of tags. */

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { api } from '@/lib/api';
import { GROUP_ICONS, OTHER_MAX_CHARS, OTHER_MAX_COUNT, OTHER_PREFIX, groupLabel, interestLabel, isOwnInterest, type Taxonomy } from '@/lib/interests';

let cached: Taxonomy | null = null;

export function useTaxonomy(): Taxonomy {
  const [tax, setTax] = useState<Taxonomy>(cached ?? []);
  useEffect(() => {
    if (cached) return;
    api<Taxonomy>('/profile/interests/taxonomy').then((x) => { cached = x; setTax(x); }).catch(() => undefined);
  }, []);
  return tax;
}

export default function InterestPicker({ value, onChange }: { value: string[]; onChange: (next: string[]) => void }) {
  const { t } = useTranslation();
  const taxonomy = useTaxonomy();
  const [open, setOpen] = useState<string | null>(null);
  const [own, setOwn] = useState('');
  const toggle = (tag: string) => onChange(value.includes(tag) ? value.filter((x) => x !== tag) : [...value, tag]);
  const owns = value.filter(isOwnInterest);
  const addOwn = () => {
    const words = own.trim().replace(/\s+/g, ' ').slice(0, OTHER_MAX_CHARS);
    if (!words || owns.length >= OTHER_MAX_COUNT) return;
    const tag = `${OTHER_PREFIX}${words}`;
    if (!value.some((v) => v.toLowerCase() === tag.toLowerCase())) onChange([...value, tag]);
    setOwn('');
  };

  return (
    <div className="stack" style={{ gap: 12 }}>
      <div className="itiles">
        {taxonomy.map((g) => {
          const key = g.key ?? g.group;
          const picked = g.interests.filter((i) => value.includes(i.tag)).length;
          return (
            <button
              key={key} type="button" className={`itile${picked ? ' itile--on' : ''}`}
              aria-expanded={open === key} aria-controls={`itile-${key}`} onClick={() => setOpen(open === key ? null : key)}
            >
              <span className="itile__icon" aria-hidden="true">{GROUP_ICONS[key] ?? '✦'}</span>
              <span className="itile__name">{groupLabel(t, g)}</span>
              {picked > 0 && <span className="itile__count" aria-label={t('interest.pickedCount', { count: picked })}>{picked}</span>}
            </button>
          );
        })}
      </div>
      {taxonomy.filter((g) => (g.key ?? g.group) === open).map((g) => (
        <div key={g.key ?? g.group} id={`itile-${g.key ?? g.group}`} className="stack fade-in" style={{ gap: 6 }}>
          <span className="label">{groupLabel(t, g)}</span>
          <div className="chips">
            {g.interests.map((i) => (
              <button key={i.tag} type="button" className="chip chip--sm" aria-pressed={value.includes(i.tag)} onClick={() => toggle(i.tag)}>
                {interestLabel(t, i.tag, i.label)}
              </button>
            ))}
          </div>
        </div>
      ))}
      {open === null && taxonomy.length > 0 && <p className="caption" style={{ margin: 0 }}>{t('interest.tapTile')}</p>}
      <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); addOwn(); }}>
        <input
          className="field__input grow" value={own} maxLength={OTHER_MAX_CHARS} onChange={(e) => setOwn(e.target.value)}
          placeholder={t('interest.otherPlaceholder')} aria-label={t('interest.other')} disabled={owns.length >= OTHER_MAX_COUNT}
        />
        <button type="submit" className="btn btn--secondary btn--sm" disabled={!own.trim() || owns.length >= OTHER_MAX_COUNT}>{t('interest.add')}</button>
      </form>
      {value.length > 0 && (
        <div className="stack" style={{ gap: 6 }}>
          <span className="label">{t('interest.yourPicks')}</span>
          <div className="chips">
            {value.map((tag) => (
              <button key={tag} type="button" className="chip chip--sm chip--on" onClick={() => toggle(tag)} aria-label={t('interest.remove', { name: interestLabel(t, tag) })}>
                {interestLabel(t, tag)} <span aria-hidden="true">✕</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
