'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import SacredLoader from '@/components/SacredLoader';
import VoiceInput from '@/components/VoiceInput';
import { setManaging } from '@/lib/api';
import { requireSession } from '@/lib/auth';
import {
  ITEM_FIELDS,
  ITEM_OPTIONS,
  SCALES,
  THEMES,
  getBrief,
  saveBrief,
  understand,
  type Brief,
  type Scale,
  type ScaleWish,
  type Theme,
  type UnderstoodItem,
} from '@/lib/matchmaker';
import { useLoaderHold } from '@/lib/useLoaderHold';

import './matchmaker.css';

/* [DEC-V1-031] "Who you're looking for" — the AI matchmaker.
 *
 * The family says it in their own words (typed or spoken, in English, Hindi
 * or Telugu). The words are read into points the engine can check; each
 * point shows the words it came from and an importance slider, 1–10, where
 * 10 makes it a must. Beside that, the six 1–10 scales: where they would like
 * a partner to be (and how much it matters), and where the candidate is.
 * Nothing is saved until the family presses Save — the product never acts on
 * something a person did not confirm. All of it is private.
 *
 * [Owner, 2026-09-28] Also the last step of setting up a profile
 * (`?setup=1`): it opens already filled from the profile (an age range
 * around the candidate's age, their city) and asks "what matters to you"
 * for each theme, compared with the candidate's own facts — nothing asked
 * twice. It can be skipped; without it the profile page still rates every
 * match on what the two have in common. */

const OPTION_KEY: Record<string, string> = {
  relocation: 'relocation_willingness',
  education: 'highest_education_level',
};
/* Which option list labels a theme's own value on "Yours: Telugu, Khatri". */
const FACT_OPTION: Record<string, string> = {
  roots: 'mother_tongue',
  life: 'diet',
  family_view: 'family_values',
  education: 'highest_education_level',
};
/* "What matters" in words a family uses, mapped onto the engine's 1–10:
   doesn't matter (unset), nice to have, important, must (10 = must). */
const LEVELS: [string, number | null][] = [
  ['none', null],
  ['nice', 4],
  ['important', 7],
  ['must', 10],
];
function levelOf(n: number | undefined): string {
  if (!n) return 'none';
  if (n >= 10) return 'must';
  if (n >= 6) return 'important';
  return 'nice';
}
const RANGE_BOUNDS: Record<string, [number, number]> = { age: [18, 80], height_cm: [120, 220] };
const MUST = 10;

type Phase = 'loading' | 'ready';
type Note = { kind: 'ok' | 'error'; text: string } | null;

function hasValue(item: UnderstoodItem): boolean {
  if (item.field in RANGE_BOUNDS) return !!(item.min || item.max);
  return (item.values?.length ?? 0) > 0;
}

export default function MatchmakerPage() {
  const loaderHold = useLoaderHold();
  const { t } = useTranslation(['discover', 'profile', 'common']);
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>('loading');
  const [brief, setBrief] = useState<Brief | null>(null);
  const [words, setWords] = useState('');
  const [items, setItems] = useState<UnderstoodItem[]>([]);
  const [wanted, setWanted] = useState<Partial<Record<Scale, ScaleWish>>>({});
  const [own, setOwn] = useState<Partial<Record<Scale, number>>>({});
  const [reading, setReading] = useState(false);
  const [source, setSource] = useState<'ai' | 'basic' | null>(null);
  const [saving, setSaving] = useState(false);
  const [note, setNote] = useState<Note>(null);
  const [manage, setManage] = useState<string | null>(null);
  const [setup, setSetup] = useState(false);
  const [started, setStarted] = useState(false);
  const [matters, setMatters] = useState<Partial<Record<Theme, number>>>({});

  useEffect(() => {
    let active = true;
    (async () => {
      const session = await requireSession();
      if (!active || !session) return;
      // A parent describing the partner they want for the child whose
      // profile they made (DEC-V1-019); the server checks the right.
      const params = new URLSearchParams(window.location.search);
      const wantedFor = params.get('manage');
      setSetup(params.get('setup') === '1');
      if (wantedFor) {
        setManaging(wantedFor);
        setManage(wantedFor);
      }
      const saved = await getBrief();
      if (!active) return;
      if (!saved) {
        router.replace('/profile/create');
        return;
      }
      setBrief(saved);
      setWords(saved.text);
      // Nothing said yet: start from what the profile already says.
      if (saved.items.length === 0 && (saved.suggested?.length ?? 0) > 0) {
        setItems(saved.suggested);
        setStarted(true);
      } else {
        setItems(saved.items);
      }
      setMatters(saved.priorities ?? {});
      setWanted(saved.partner_scales ?? {});
      setOwn(saved.self_scales ?? {});
      setPhase('ready');
    })();
    return () => {
      active = false;
      setManaging(null);
    };
  }, [router]);

  if (phase === 'loading' || loaderHold || !brief) {
    return (
      <main className="screen screen--centered">
        <SacredLoader />
      </main>
    );
  }

  const back = manage ? `/me?manage=${manage}` : '/me';
  // Where setting up continues: the profile they made, or Home.
  const done = manage ? `/me?manage=${manage}` : '/';
  const fieldLabel = (field: string) => t(`discover:matchmaker.field.${field}`);
  const optionLabel = (field: string, value: string) =>
    t(`profile:option.${OPTION_KEY[field] ?? field}.${value}`, { defaultValue: value });

  async function read() {
    if (!words.trim() || reading) return;
    setReading(true);
    setNote(null);
    const res = await understand(words);
    setReading(false);
    if (!res.ok) {
      setNote({
        kind: 'error',
        text: t(res.status === 429 ? 'discover:matchmaker.rateLimited' : 'discover:matchmaker.failed'),
      });
      return;
    }
    // The latest words describe the partner; scales they speak to are
    // filled in, the rest keep what was set by hand.
    setItems(res.data.items);
    setWanted((w) => ({ ...w, ...res.data.scales }));
    setSource(res.data.source);
  }

  function update(index: number, patch: Partial<UnderstoodItem>) {
    setItems((list) => list.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function toggleValue(index: number, value: string) {
    const current = items[index].values ?? [];
    update(index, {
      values: current.includes(value) ? current.filter((v) => v !== value) : [...current, value],
    });
  }

  async function save() {
    setSaving(true);
    setNote(null);
    const res = await saveBrief({
      text: words,
      items: items.filter(hasValue),
      partner_scales: wanted,
      self_scales: brief?.can_rate_self ? own : undefined,
      priorities: matters,
    });
    setSaving(false);
    if (res.ok && setup) {
      router.push(done);
      return;
    }
    setNote(
      res.ok
        ? { kind: 'ok', text: t('discover:matchmaker.saved') }
        : { kind: 'error', text: t('discover:matchmaker.error') },
    );
    if (res.ok) setItems((list) => list.filter(hasValue));
  }

  const unused = ITEM_FIELDS.filter((f) => !items.some((it) => it.field === f));

  function renderValue(item: UnderstoodItem, index: number) {
    if (item.field in RANGE_BOUNDS) {
      const [lo, hi] = RANGE_BOUNDS[item.field];
      const unit = t(`discover:matchmaker.range.${item.field === 'age' ? 'years' : 'cm'}`);
      const num = (key: 'min' | 'max', label: string) => (
        <label className="mm-range__part">
          <span className="mm-range__label">{label}</span>
          <input
            type="number"
            inputMode="numeric"
            min={lo}
            max={hi}
            value={item[key] ?? ''}
            onChange={(e) => update(index, { [key]: e.target.value ? Number(e.target.value) : null })}
          />
        </label>
      );
      return (
        <div className="mm-range">
          {num('min', t('discover:matchmaker.range.from'))}
          {num('max', t('discover:matchmaker.range.to'))}
          <span className="mm-range__unit">{unit}</span>
        </div>
      );
    }
    const options = ITEM_OPTIONS[item.field];
    if (options) {
      return (
        <div className="fchips" role="group" aria-label={fieldLabel(item.field)}>
          {options.map((v) => {
            const on = item.values?.includes(v) ?? false;
            return (
              <button
                key={v}
                type="button"
                className={`fchip${on ? ' is-on' : ''}`}
                aria-pressed={on}
                onClick={() => toggleValue(index, v)}
              >
                {optionLabel(item.field, v)}
              </button>
            );
          })}
        </div>
      );
    }
    return (
      <input
        className="mm-text"
        type="text"
        aria-label={t(`discover:matchmaker.${item.field === 'locality' ? 'places' : 'hobbies'}`)}
        placeholder={t(`discover:matchmaker.${item.field === 'locality' ? 'places' : 'hobbies'}`)}
        value={(item.values ?? []).join(', ')}
        onChange={(e) =>
          update(index, {
            values: e.target.value
              .split(',')
              .map((s) => s.trimStart())
              .filter((s, i, all) => s || i === all.length - 1),
          })
        }
        onBlur={(e) =>
          update(index, { values: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })
        }
      />
    );
  }

  function renderTheme(theme: Theme) {
    const value = matters[theme];
    const facts = brief?.theme_facts?.[theme] ?? [];
    const factText = facts
      .map((v) =>
        FACT_OPTION[theme]
          ? t(`profile:option.${FACT_OPTION[theme]}.${v}`, { defaultValue: v.replace(/_/g, ' ') })
          : v,
      )
      .join(', ');
    // A theme compared with the candidate's own facts needs those facts;
    // horoscope needs a chart, which Discover checks on its own.
    const usable = theme === 'horoscope' || facts.length > 0;
    const set = (n: number | null) =>
      setMatters((m) => {
        const next = { ...m };
        if (n === null) delete next[theme];
        else next[theme] = n;
        return next;
      });
    const name = t(`discover:matchmaker.matters.theme.${theme}.name`);
    return (
      <div key={theme} className={`mm-theme${value ? ' is-set' : ''}`}>
        <div className="mm-scale__head">
          <span className="mm-scale__name">{name}</span>
        </div>
        <p className="caption">
          {t(`discover:matchmaker.matters.theme.${theme}.note`)}
          {factText && ` · ${t('discover:matchmaker.matters.yours', { facts: factText })}`}
          {!usable && ` · ${t('discover:matchmaker.matters.noFacts')}`}
        </p>
        {usable && (
          <div className="mm-levels" role="radiogroup" aria-label={name}>
            {LEVELS.map(([level, n]) => {
              const on = level === 'none' ? !value : levelOf(value) === level;
              return (
                <button
                  key={level}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  className={`mm-level${on ? ' is-on' : ''}`}
                  onClick={() => set(n)}
                >
                  {t(`discover:matchmaker.matters.level.${level}`)}
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  function renderScale(dim: Scale, mode: 'wanted' | 'own') {
    const name = t(`discover:matchmaker.scales.dim.${dim}.name`);
    const low = t(`discover:matchmaker.scales.dim.${dim}.low`);
    const high = t(`discover:matchmaker.scales.dim.${dim}.high`);
    const value = mode === 'wanted' ? wanted[dim]?.want : own[dim];
    const set = (n: number | null) => {
      if (mode === 'wanted') {
        setWanted((w) => {
          const next = { ...w };
          if (n === null) delete next[dim];
          else next[dim] = { want: n, importance: w[dim]?.importance ?? 6 };
          return next;
        });
      } else {
        setOwn((o) => {
          const next = { ...o };
          if (n === null) delete next[dim];
          else next[dim] = n;
          return next;
        });
      }
    };
    return (
      <div key={`${mode}-${dim}`} className={`mm-scale${value ? '' : ' is-unset'}`}>
        <div className="mm-scale__head">
          <span className="mm-scale__name">{name}</span>
          {value ? (
            <button type="button" className="mm-link" onClick={() => set(null)}>
              {t('discover:matchmaker.scales.clear')}
            </button>
          ) : (
            <button type="button" className="mm-link" onClick={() => set(5)}>
              {t('discover:matchmaker.scales.set')}
            </button>
          )}
        </div>
        {value ? (
          <>
            <input
              type="range"
              min={1}
              max={10}
              step={1}
              value={value}
              aria-label={`${name} · ${t(mode === 'wanted' ? 'discover:matchmaker.scales.wanted' : 'discover:matchmaker.scales.you')}`}
              aria-valuetext={`${value} · ${low} – ${high}`}
              onChange={(e) => set(Number(e.target.value))}
            />
            <div className="mm-scale__ends">
              <span>{low}</span>
              <span className="mm-scale__n">{value}</span>
              <span>{high}</span>
            </div>
            {mode === 'wanted' && (
              <label className="mm-imp mm-imp--small">
                <span>{t('discover:matchmaker.importance')}</span>
                <input
                  type="range"
                  min={1}
                  max={10}
                  step={1}
                  value={wanted[dim]?.importance ?? 6}
                  aria-valuetext={t('discover:matchmaker.importanceValue', { n: wanted[dim]?.importance ?? 6 })}
                  onChange={(e) =>
                    setWanted((w) => ({ ...w, [dim]: { want: value, importance: Number(e.target.value) } }))
                  }
                />
                <span className="mm-imp__n">{wanted[dim]?.importance ?? 6}</span>
              </label>
            )}
          </>
        ) : (
          <div className="mm-scale__ends mm-scale__ends--quiet">
            <span>{low}</span>
            <span>{high}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <>
      <header className="topbar">
        {setup ? (
          <span style={{ width: 44 }} aria-hidden="true" />
        ) : (
          <button className="icon-btn" onClick={() => router.push(back)} aria-label={t('common:action.back')}>
            ←
          </button>
        )}
        <h1>{t(setup ? 'discover:matchmaker.setup.title' : 'discover:matchmaker.title')}</h1>
        {setup ? (
          <button type="button" className="mm-link" onClick={() => router.push(done)}>
            {t('discover:matchmaker.setup.skip')}
          </button>
        ) : (
          <span style={{ width: 44 }} aria-hidden="true" />
        )}
      </header>

      <main className="screen mm">
        <div className="mm-grid">
          <div className="mm-col">
            <section className="mm-words" aria-labelledby="mm-words-label">
              {setup && <p className="label">{t('discover:matchmaker.setup.step')}</p>}
              <p className="mm-intro">{t('discover:matchmaker.intro')}</p>
              <label id="mm-words-label" className="label" htmlFor="mm-words">
                {t('discover:matchmaker.wordsLabel')}
              </label>
              <textarea
                id="mm-words"
                className="mm-textarea"
                rows={5}
                maxLength={1500}
                placeholder={t('discover:matchmaker.placeholder')}
                value={words}
                onChange={(e) => setWords(e.target.value)}
              />
              <div className="mm-words__actions">
                <VoiceInput onText={(said) => setWords((w) => (w.trim() ? `${w.trim()} ${said}` : said))} />
                <button
                  type="button"
                  className="btn btn--primary"
                  disabled={!words.trim() || reading}
                  onClick={read}
                >
                  {reading ? t('discover:matchmaker.understanding') : t('discover:matchmaker.understand')}
                </button>
              </div>
              <p className="caption">
                {t(brief.ai_available ? 'discover:matchmaker.aiNote' : 'discover:matchmaker.privacy')}
              </p>
            </section>

            <section className="mm-understood" aria-labelledby="mm-understood-title" aria-busy={reading}>
              <h2 id="mm-understood-title" className="h2">
                {t('discover:matchmaker.understood')}
              </h2>
              <p className="caption">
                {source === 'basic'
                  ? t('discover:matchmaker.basicNote')
                  : started && !source
                    ? t('discover:matchmaker.setup.started')
                    : t('discover:matchmaker.understoodHint')}
              </p>
              {items.length === 0 && <p className="mm-empty">{t('discover:matchmaker.nothing')}</p>}
              <ul className="mm-items">
                {items.map((item, index) => {
                  const must = item.importance >= MUST;
                  return (
                    <li key={item.field} className={`mm-item${must ? ' is-must' : ''}`}>
                      <div className="mm-item__head">
                        <span className="mm-item__name">{fieldLabel(item.field)}</span>
                        {must && <span className="mm-must">{t('discover:matchmaker.must')}</span>}
                        <button
                          type="button"
                          className="mm-x"
                          aria-label={t('discover:matchmaker.remove', { what: fieldLabel(item.field) })}
                          onClick={() => setItems((list) => list.filter((_, i) => i !== index))}
                        >
                          ×
                        </button>
                      </div>
                      {renderValue(item, index)}
                      <label className="mm-imp">
                        <span>{t('discover:matchmaker.importance')}</span>
                        <input
                          type="range"
                          min={1}
                          max={10}
                          step={1}
                          value={item.importance}
                          aria-valuetext={
                            must
                              ? t('discover:matchmaker.must')
                              : t('discover:matchmaker.importanceValue', { n: item.importance })
                          }
                          onChange={(e) => update(index, { importance: Number(e.target.value) })}
                        />
                        <span className="mm-imp__n">{item.importance}</span>
                      </label>
                      {item.quote && (
                        <p className="mm-quote">{t('discover:matchmaker.from', { quote: item.quote })}</p>
                      )}
                    </li>
                  );
                })}
              </ul>
              {unused.length > 0 && (
                <label className="mm-add">
                  <span className="label">{t('discover:matchmaker.add')}</span>
                  <select
                    value=""
                    onChange={(e) => {
                      const field = e.target.value;
                      if (field) setItems((list) => [...list, { field, importance: 6, values: [] }]);
                    }}
                  >
                    <option value="">{`+ ${t('discover:matchmaker.add')}`}</option>
                    {unused.map((f) => (
                      <option key={f} value={f}>
                        {fieldLabel(f)}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </section>
          </div>

          <div className="mm-col">
            <section className="mm-scales" aria-labelledby="mm-matters-title">
              <h2 id="mm-matters-title" className="h2">
                {t('discover:matchmaker.matters.title')}
              </h2>
              <p className="caption">{t('discover:matchmaker.matters.hint')}</p>
              {THEMES.map((theme) => renderTheme(theme))}
            </section>

            {/* The six 1–10 scales are fine-tuning: folded away so the page
                reads as words first, not as a form. */}
            <details className="mm-fine">
              <summary className="mm-fine__summary">
                <span className="mm-fine__title">{t('discover:matchmaker.fine.title')}</span>
                <span className="caption">{t('discover:matchmaker.fine.hint')}</span>
              </summary>
            <section className="mm-scales" aria-labelledby="mm-partner-title">
              <h2 id="mm-partner-title" className="h2">
                {t('discover:matchmaker.scales.partnerTitle')}
              </h2>
              <p className="caption">{t('discover:matchmaker.scales.partnerHint')}</p>
              {SCALES.map((dim) => renderScale(dim, 'wanted'))}
            </section>

            <section className="mm-scales" aria-labelledby="mm-self-title">
              <h2 id="mm-self-title" className="h2">
                {t('discover:matchmaker.scales.selfTitle')}
              </h2>
              {brief.can_rate_self ? (
                <>
                  <p className="caption">{t('discover:matchmaker.scales.selfHint')}</p>
                  {SCALES.map((dim) => renderScale(dim, 'own'))}
                </>
              ) : (
                <p className="caption">{t('discover:matchmaker.scales.selfManaged')}</p>
              )}
            </section>
            </details>
          </div>
        </div>

        <div className="mm-savebar">
          {note && (
            <p className={`mm-note mm-note--${note.kind}`} role={note.kind === 'error' ? 'alert' : 'status'}>
              {note.text}
            </p>
          )}
          <button type="button" className="btn btn--primary" disabled={saving} onClick={save}>
            {saving
              ? t('discover:matchmaker.saving')
              : t(setup ? 'discover:matchmaker.setup.continue' : 'discover:matchmaker.save')}
          </button>
        </div>
      </main>
    </>
  );
}
