'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { getSession } from '@/lib/auth';
import { findCategory, type FieldDef } from '@/lib/profileCategoryConfig';
import {
  getCategoryAttributes,
  updateCategoryAttributes,
  type AttributeState,
  type AttributeValue,
} from '@/lib/profile';

/* FR002/TR002 · UX11 "Category edit screen (generic pattern, reused per
 * category)" — one config-driven component for all 13 categories rather
 * than 13 bespoke screens, matching UX11's own "generic pattern" framing.
 * Every non-essential field carries an inline "Decline this field" control,
 * distinct from leaving it empty (FieldState's tri-state contract). */

type FieldLocalState = { state: AttributeState; value: unknown };
type FormState = Record<string, FieldLocalState>;

function emptyFormState(fields: FieldDef[]): FormState {
  const out: FormState = {};
  for (const f of fields) out[f.key] = { state: 'unset', value: f.kind === 'ageRange' ? { min: '', max: '' } : '' };
  return out;
}

export default function CategoryEditorPage() {
  const { t } = useTranslation(['common', 'profile']);
  const router = useRouter();
  const params = useParams<{ category: string }>();
  const category = params.category;
  const def = findCategory(category);

  const [form, setForm] = useState<FormState | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!def) return;
    let active = true;
    (async () => {
      const session = await getSession();
      if (!active) return;
      if (!session) {
        router.replace('/login');
        return;
      }
      const saved = await getCategoryAttributes(category);
      if (!active) return;
      const initial = emptyFormState(def.fields);
      for (const f of def.fields) {
        const row = saved[f.key];
        if (row) {
          initial[f.key] = {
            state: row.state,
            value: row.state === 'value' ? row.value ?? (f.kind === 'ageRange' ? { min: '', max: '' } : '') : (f.kind === 'ageRange' ? { min: '', max: '' } : ''),
          };
        }
      }
      setForm(initial);
    })();
    return () => {
      active = false;
    };
  }, [category, def, router]);

  if (!def) {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.empty')}</p>
      </main>
    );
  }

  if (!form) {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  function setField(key: string, patch: Partial<FieldLocalState>) {
    setForm((prev) => (prev ? { ...prev, [key]: { ...prev[key], ...patch } } : prev));
  }

  function decline(key: string) {
    setField(key, { state: 'declined', value: '' });
  }

  function undecline(key: string) {
    setField(key, { state: 'unset', value: '' });
  }

  async function onSave() {
    if (!form || !def) return;
    setSaving(true);
    setError(null);

    const payload: Record<string, { state: AttributeState; value?: AttributeValue }> = {};
    for (const f of def.fields) {
      const entry = form[f.key];
      if (entry.state === 'unset') continue; // nothing to persist — a real row is only written on value/decline
      const value =
        f.kind === 'ageRange' && entry.value && typeof entry.value === 'object'
          ? {
              min: Number((entry.value as { min?: unknown }).min) || null,
              max: Number((entry.value as { max?: unknown }).max) || null,
            }
          : entry.value;
      payload[f.key] =
        entry.state === 'declined'
          ? { state: 'declined', value: null }
          : { state: 'value', value: value as AttributeValue };
    }

    if (Object.keys(payload).length === 0) {
      router.push('/me');
      return;
    }

    const outcome = await updateCategoryAttributes(category, payload);
    setSaving(false);
    if (!outcome.ok) {
      setError(t(outcome.kind === 'network' ? 'profile:error.network' : 'profile:editor.saveError'));
      return;
    }
    router.push('/me');
  }

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" onClick={() => router.push('/me')} aria-label={t('common:action.back')}>
          ←
        </button>
        <h1>{t(`profile:hub.category.${category}`)}</h1>
        <span style={{ width: 44 }} aria-hidden="true" />
      </header>

      <main className="screen">
        <div className="card">
          {def.fields.map((f) => {
            const entry = form[f.key];
            const isDeclined = entry.state === 'declined';
            return (
              <div className={`attr-field${isDeclined ? ' is-declined' : ''}`} key={f.key}>
                <div className="attr-field__head">
                  <label className="attr-field__label" htmlFor={`f-${f.key}`}>
                    {t(`profile:${f.labelKey}`)}
                  </label>
                  {isDeclined ? (
                    <button type="button" className="attr-field__decline" onClick={() => undecline(f.key)}>
                      {t('profile:editor.change')}
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="attr-field__decline"
                      aria-label={`${t('profile:editor.decline')}: ${t(`profile:${f.labelKey}`)}`}
                      onClick={() => decline(f.key)}
                    >
                      {t('profile:editor.decline')}
                    </button>
                  )}
                </div>

                {isDeclined ? (
                  <p className="attr-field__declined-row">{t('profile:editor.declined')}</p>
                ) : f.kind === 'select' ? (
                  <select
                    id={`f-${f.key}`}
                    className="field__input"
                    value={typeof entry.value === 'string' ? entry.value : ''}
                    onChange={(e) => setField(f.key, { state: 'value', value: e.target.value })}
                  >
                    <option value="" disabled>
                      {t('profile:editor.selectPlaceholder')}
                    </option>
                    {f.options?.map((opt) => (
                      <option key={opt} value={opt}>
                        {t(`profile:option.${f.key}.${opt}`)}
                      </option>
                    ))}
                  </select>
                ) : f.kind === 'ageRange' ? (
                  <div className="age-range">
                    <input
                      id={`f-${f.key}`}
                      className="field__input"
                      type="number"
                      inputMode="numeric"
                      placeholder={t('profile:editor.ageRangeFrom')}
                      value={
                        typeof entry.value === 'object' && entry.value && 'min' in (entry.value as Record<string, unknown>)
                          ? String((entry.value as { min: unknown }).min ?? '')
                          : ''
                      }
                      onChange={(e) => {
                        const current = (entry.value as { min?: unknown; max?: unknown }) ?? {};
                        setField(f.key, { state: 'value', value: { ...current, min: e.target.value } });
                      }}
                    />
                    <span aria-hidden="true">–</span>
                    <input
                      className="field__input"
                      type="number"
                      inputMode="numeric"
                      placeholder={t('profile:editor.ageRangeTo')}
                      value={
                        typeof entry.value === 'object' && entry.value && 'max' in (entry.value as Record<string, unknown>)
                          ? String((entry.value as { max: unknown }).max ?? '')
                          : ''
                      }
                      onChange={(e) => {
                        const current = (entry.value as { min?: unknown; max?: unknown }) ?? {};
                        setField(f.key, { state: 'value', value: { ...current, max: e.target.value } });
                      }}
                    />
                  </div>
                ) : (
                  <input
                    id={`f-${f.key}`}
                    className="field__input"
                    type="text"
                    value={typeof entry.value === 'string' ? entry.value : ''}
                    onChange={(e) => setField(f.key, { state: 'value', value: e.target.value })}
                  />
                )}
              </div>
            );
          })}
        </div>

        <p className="form__error">{error ?? ''}</p>

        <div className="form__actions">
          <button className="cta" disabled={saving} onClick={onSave}>
            <span className={saving ? 'cta__label--hidden' : undefined}>{t('profile:editor.save')}</span>
            {saving && <span className="cta__spinner" aria-hidden="true" />}
          </button>
        </div>
      </main>
    </>
  );
}
