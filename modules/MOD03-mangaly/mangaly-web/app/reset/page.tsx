'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { OtpBoxes } from '@/components/form/OtpBoxes';
import { Field } from '@/components/form/Field';
import { SubmitButton } from '@/components/form/SubmitButton';
import { confirmPasswordReset, requestPasswordReset } from '@/lib/auth';
import { authErrorText } from '@/lib/authErrorText';

/* FR094 · TR094 · UX03/UI03 (reset screen) · SP094
 *
 * Two steps, one screen each: (1) identifier → request a code, always the
 * same response whether or not an account exists (SP094 anti-enumeration,
 * same shape as sign-up/login-OTP); (2) code + new password, submitted
 * together — the reset OTP is single-use, so there is no separate "verify"
 * step before setting the password (see `identity.confirm_password_reset`'s
 * docstring on the backend for why). */

type Step = { phase: 'request' } | { phase: 'confirm'; identifier: string };

const OUTCOME_ERROR_KEY = {
  invalid: 'auth:otp.error.invalid',
  expired: 'auth:otp.error.expired',
  too_many_attempts: 'auth:otp.error.tooManyAttempts',
} as const;

export default function ResetPage() {
  const { t } = useTranslation('auth');

  const [step, setStep] = useState<Step>({ phase: 'request' });
  const [identifier, setIdentifier] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [codeError, setCodeError] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function onRequest(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const result = await requestPasswordReset(identifier);
    setBusy(false);
    if (!result.ok) {
      setError(authErrorText(result, t));
      return;
    }
    setStep({ phase: 'confirm', identifier });
  }

  async function onConfirm(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCodeError(false);

    if (password !== confirmPassword) {
      setError(t('auth:newPassword.mismatch'));
      return;
    }

    setBusy(true);
    const result = await confirmPasswordReset(identifier, code, password);
    setBusy(false);

    if (!result.ok) {
      setError(authErrorText(result, t));
      return;
    }
    if (result.data.outcome !== 'verified') {
      setCodeError(true);
      setError(t(OUTCOME_ERROR_KEY[result.data.outcome]));
      return;
    }
    // [ADR-010] The server already localized this ("Your password has been
    // reset...") — shown verbatim, same rule every other auth response follows.
    setSuccessMessage(result.data.message);
  }

  if (successMessage) {
    return (
      <main className="screen screen--centered">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <div style={{ textAlign: 'center' }}>
          <h1 className="h2" style={{ margin: '0 0 8px' }}>
            {t('auth:newPassword.title')}
          </h1>
          <p className="muted">{successMessage}</p>
        </div>
        <div className="form__actions" style={{ width: '100%' }}>
          <Link className="cta cta--link" href="/login">
            {t('auth:signup.sent.back')}
          </Link>
        </div>
      </main>
    );
  }

  if (step.phase === 'confirm') {
    return (
      <>
        <header className="topbar">
          <h1>{t('auth:newPassword.title')}</h1>
        </header>
        <main className="screen screen--form">
          <span className="brand-mark brand-mark--lg" aria-hidden="true">
            m
          </span>
          <p className="muted body-lg" style={{ margin: 0 }}>
            {t('auth:otp.explainer', { identifier: step.identifier })}
          </p>
          <form className="form" onSubmit={onConfirm} noValidate>
            <OtpBoxes value={code} onChange={setCode} disabled={busy} error={codeError} />

            <Field
              label={t('auth:newPassword.field.password')}
              value={password}
              onChange={setPassword}
              type="password"
              autoComplete="new-password"
              disabled={busy}
              required
            />
            <Field
              label={t('auth:newPassword.field.confirm')}
              value={confirmPassword}
              onChange={setConfirmPassword}
              type="password"
              autoComplete="new-password"
              disabled={busy}
              required
            />

            <p className="form__error" role="status" aria-live="polite">
              {error ?? ''}
            </p>

            <div className="form__actions">
              <SubmitButton
                label={busy ? t('auth:state.submitting') : t('auth:newPassword.submit')}
                busy={busy}
                disabled={code.length < 6 || !password || !confirmPassword}
              />
            </div>
          </form>
        </main>
      </>
    );
  }

  return (
    <>
      <header className="topbar">
        <h1>{t('auth:reset.title')}</h1>
      </header>
      <main className="screen screen--form">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <p className="muted body-lg" style={{ margin: 0 }}>
          {t('auth:reset.explainer')}
        </p>
        <form className="form" onSubmit={onRequest} noValidate>
          <Field
            label={t('auth:reset.field.identifier')}
            value={identifier}
            onChange={setIdentifier}
            type="text"
            inputMode="text"
            autoComplete="username"
            disabled={busy}
            required
          />
          <p className="form__error" role="status" aria-live="polite">
            {error ?? ''}
          </p>
          <div className="form__actions">
            <SubmitButton
              label={busy ? t('auth:state.submitting') : t('auth:reset.submit')}
              busy={busy}
              disabled={!identifier}
            />
            <p className="form__alt">
              <Link className="link" href="/login">
                {t('auth:signup.sent.back')}
              </Link>
            </p>
          </div>
        </form>
      </main>
    </>
  );
}
