'use client';

import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';

/* [UI03] The shared form template all four auth screens use: floating-label
 * fields on `surface.raised`, `border.default` → saffron `focus.ring` on focus,
 * 48dp minimum target, `inputmode` forced per field type. Written once here so
 * Login/Sign-Up/Reset/Set-password cannot drift apart visually. */

type Props = {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: 'text' | 'password' | 'email' | 'tel';
  autoComplete?: string;
  inputMode?: 'text' | 'email' | 'tel' | 'numeric';
  error?: string;
  disabled?: boolean;
  required?: boolean;
};

export function Field({
  label,
  value,
  onChange,
  type = 'text',
  autoComplete,
  inputMode,
  error,
  disabled,
  required,
}: Props) {
  const id = useId();
  const { t } = useTranslation('auth');
  const [reveal, setReveal] = useState(false);
  const isPassword = type === 'password';
  const effectiveType = isPassword && reveal ? 'text' : type;

  return (
    <div className={`field${error ? ' field--error' : ''}`}>
      <div className="field__box">
        <input
          id={id}
          className="field__input"
          type={effectiveType}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder=" "
          autoComplete={autoComplete}
          inputMode={inputMode}
          disabled={disabled}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-err` : undefined}
        />
        <label className="field__label" htmlFor={id}>
          {label}
        </label>
        {isPassword && (
          <button
            type="button"
            className="field__reveal"
            onClick={() => setReveal((r) => !r)}
            // The control's purpose changes with its state, so the label has to
            // as well — otherwise a screen-reader user is told "show password"
            // on a field that is already showing.
            aria-label={reveal ? t('action.hidePassword') : t('action.showPassword')}
            aria-pressed={reveal}
          >
            {reveal ? <EyeOff /> : <Eye />}
          </button>
        )}
      </div>
      {error && (
        <p className="field__err" id={`${id}-err`}>
          {error}
        </p>
      )}
    </div>
  );
}

const svg = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

function Eye() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <path {...svg} d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
      <circle {...svg} cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOff() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <path {...svg} d="M3 3l18 18" />
      <path {...svg} d="M10.6 6.1A9.7 9.7 0 0 1 12 6c6 0 9.5 6 9.5 6a17 17 0 0 1-3.2 3.9" />
      <path {...svg} d="M6.3 7.9A16.7 16.7 0 0 0 2.5 12S6 18 12 18a9.6 9.6 0 0 0 3.2-.5" />
      <path {...svg} d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
    </svg>
  );
}
