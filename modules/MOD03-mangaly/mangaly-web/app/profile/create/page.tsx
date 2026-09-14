'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Field } from '@/components/form/Field';
import { SubmitButton } from '@/components/form/SubmitButton';
import { createProfile } from '@/lib/profile';

/* FR001 · TR001 · UX11 · UI11 · TS001-002/TS010 · SP001 · DEC-V1-001
 *
 * [UX11] "Existence-tier wizard... a short linear sequence of only the fields
 * required to save at all — one or two fields per screen, progress indicator
 * ... no skip — these are the true minimum." DEC-V1-001 fixes the exact
 * field list: name, DOB, gender, city/locality, at least one photo.
 *
 * [UI11] Full-screen takeover, one field centered upper-middle third, steps
 * cross-fade into each other (fragments of one save action, never a slide
 * between separate destinations) — implemented here as a single mounted form
 * with a `step` index, so there is no route change (and no back-button
 * history entry) between steps, matching "fragments of one action."
 */

type Gender = 'female' | 'male' | 'other';

const TOTAL_STEPS = 4;

export default function CreateProfilePage() {
  const { t } = useTranslation(['profile', 'common']);
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState<Gender | ''>('');
  const [cityLocality, setCityLocality] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function onPhotoChange(file: File | null) {
    setPhoto(file);
    setPhotoPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return file ? URL.createObjectURL(file) : null;
    });
  }

  const stepValid =
    (step === 1 && name.trim().length > 0) ||
    (step === 2 && dateOfBirth !== '' && gender !== '') ||
    (step === 3 && cityLocality.trim().length > 0) ||
    (step === 4 && photo !== null);

  async function onNext(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (step < TOTAL_STEPS) {
      setStep((s) => s + 1);
      return;
    }
    if (!photo || !gender) return;

    setBusy(true);
    const result = await createProfile({ name, dateOfBirth, gender, cityLocality, photo });
    setBusy(false);

    if (result.ok) {
      router.push('/');
      return;
    }
    setError(
      result.kind === 'network' ? t('profile:error.network') : (result.message ?? t('profile:error.network')),
    );
  }

  return (
    <>
      <header className="topbar">
        <span className="caption">{t('profile:wizard.step', { current: step, total: TOTAL_STEPS })}</span>
      </header>

      <main className="screen screen--form">
        <div className="progress" aria-hidden="true">
          <div className="progress__bar" style={{ width: `${(step / TOTAL_STEPS) * 100}%` }} />
        </div>

        {/* [UI11] Steps cross-fade — a `key`-driven remount on the wizard body
            gives each step its own fade-in without a route change. */}
        <form className="form wizard-step" key={step} onSubmit={onNext} noValidate>
          {step === 1 && (
            <Field
              label={t('profile:field.name')}
              value={name}
              onChange={setName}
              type="text"
              autoComplete="name"
              disabled={busy}
              required
            />
          )}

          {step === 2 && (
            <>
              <label className="date-field">
                <span className="caption">{t('profile:field.dateOfBirth')}</span>
                <input
                  type="date"
                  className="field__input date-field__input"
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                  max={new Date().toISOString().slice(0, 10)}
                  disabled={busy}
                  required
                />
              </label>
              <div
                className="segmented segmented--3"
                role="radiogroup"
                aria-label={t('profile:field.gender')}
              >
                {(['female', 'male', 'other'] as Gender[]).map((g) => (
                  <button
                    key={g}
                    type="button"
                    role="radio"
                    aria-checked={gender === g}
                    className={`segmented__opt${gender === g ? ' is-active' : ''}`}
                    onClick={() => setGender(g)}
                    disabled={busy}
                  >
                    {t(`profile:field.genderOption.${g}`)}
                  </button>
                ))}
              </div>
            </>
          )}

          {step === 3 && (
            <Field
              label={t('profile:field.cityLocality')}
              value={cityLocality}
              onChange={setCityLocality}
              type="text"
              autoComplete="address-level2"
              disabled={busy}
              required
            />
          )}

          {step === 4 && (
            <div className="photo-picker">
              <button
                type="button"
                className="photo-picker__dropzone"
                onClick={() => fileInputRef.current?.click()}
                disabled={busy}
              >
                {photoPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={photoPreview} alt="" className="photo-picker__preview" />
                ) : (
                  <span className="caption">{t('profile:photo.empty')}</span>
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                hidden
                onChange={(e) => onPhotoChange(e.target.files?.[0] ?? null)}
              />
              {photoPreview && (
                <button
                  type="button"
                  className="link link--button"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {t('profile:photo.change')}
                </button>
              )}
            </div>
          )}

          <p className="form__error" role="status" aria-live="polite">
            {error ?? ''}
          </p>

          <div className="form__actions">
            <SubmitButton
              label={
                busy
                  ? t('profile:wizard.saving')
                  : step < TOTAL_STEPS
                    ? t('profile:wizard.next')
                    : t('profile:wizard.save')
              }
              busy={busy}
              disabled={!stepValid}
            />
          </div>
        </form>
      </main>
    </>
  );
}
