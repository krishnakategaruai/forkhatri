'use client';

import { useRef } from 'react';
import { useTranslation } from 'react-i18next';

/* [UX04/UI04] Six discrete auto-advancing digit boxes (WhatsApp/Truecaller
 * convention) rather than one free-text field. Exposed to assistive tech as
 * ONE logical field with a live digit-count announcement, per UX04's
 * accessibility note — not six separately-labeled, confusing stops. */

const LENGTH = 6;

export function OtpBoxes({
  value,
  onChange,
  disabled,
  error,
}: {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  error?: boolean;
}) {
  const { t } = useTranslation('auth');
  const refs = useRef<(HTMLInputElement | null)[]>([]);
  const digits = value.padEnd(LENGTH, ' ').split('').slice(0, LENGTH);

  function setDigit(index: number, char: string) {
    const next = digits.slice();
    next[index] = char;
    const joined = next.join('').trimEnd();
    onChange(joined);
    if (char !== ' ' && index < LENGTH - 1) refs.current[index + 1]?.focus();
  }

  function handleChange(index: number, raw: string) {
    const clean = raw.replace(/\D/g, '');
    if (clean.length <= 1) {
      setDigit(index, clean || ' ');
      return;
    }
    // [UI04] OS SMS-autofill supported — a paste/autofill can deliver all 6
    // digits into one box at once, filling in one tap rather than per-digit.
    const pasted = clean.slice(0, LENGTH);
    onChange(pasted);
    refs.current[Math.min(pasted.length, LENGTH - 1)]?.focus();
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace' && digits[index] === ' ' && index > 0) {
      refs.current[index - 1]?.focus();
    }
  }

  const filledCount = value.length;

  return (
    <div>
      <div
        className="otp-boxes"
        role="group"
        aria-label={t('otp.explainer', { identifier: '' })}
      >
        {digits.map((d, i) => (
          <input
            key={i}
            ref={(el) => {
              refs.current[i] = el;
            }}
            className={`otp-box${error ? ' otp-box--error' : ''}${d !== ' ' ? ' otp-box--filled' : ''}`}
            type="text"
            inputMode="numeric"
            autoComplete={i === 0 ? 'one-time-code' : 'off'}
            maxLength={LENGTH}
            value={d === ' ' ? '' : d}
            disabled={disabled}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            aria-label={`Digit ${i + 1} of ${LENGTH}`}
          />
        ))}
      </div>
      {/* [UX04] Live-announced digit count, not per-box labels. */}
      <p className="sr-only" aria-live="polite">
        {t('otp.digitsEntered', { count: filledCount })}
      </p>
    </div>
  );
}
