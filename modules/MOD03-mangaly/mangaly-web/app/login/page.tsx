'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Field } from '@/components/form/Field';
import { SubmitButton } from '@/components/form/SubmitButton';
import { logIn, requestLoginOtp } from '@/lib/auth';
import { authErrorText } from '@/lib/authErrorText';

/* FR093 · TR093 · UX03 · UI03 · TS206–TS208 · SP093 · DEC-V1-012
 *
 * [DEC-V1-012, 2026-09-13] Primary path is OTP (one CTA: "Send code"),
 * password is a secondary path behind a small "Use password instead" link —
 * not a symmetric toggle. Real screen-pattern research found no current app
 * presents both as equal-weight options; NN/G's own passwordless-accounts
 * guidance recommends exactly this "primary + fallback" shape. The anti-
 * enumeration property that made this screen careful before still holds:
 * TR093 requires an identical response whether the identifier exists, on
 * both the OTP-request and password paths alike. */

export default function LoginPage() {
  const { t } = useTranslation(['auth', 'common']);
  const router = useRouter();

  const [identifier, setIdentifier] = useState('');
  const [credential, setCredential] = useState('');
  const [usePassword, setUsePassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmitOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);

    const result = await requestLoginOtp(identifier);
    setBusy(false);

    if (result.ok) {
      router.push(`/otp?id=${encodeURIComponent(identifier)}&purpose=login`);
      return;
    }
    setError(authErrorText(result, t));
  }

  async function onSubmitPassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);

    const result = await logIn(identifier, credential);
    setBusy(false);

    if (result.ok) {
      router.push('/');
      return;
    }
    setError(authErrorText(result, t));
  }

  return (
    <>
      <header className="topbar">
        <h1>{t('auth:login.title')}</h1>
      </header>

      <main className="screen screen--form">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <p className="muted body-lg" style={{ margin: 0 }}>
          {t('auth:login.subtitle')}
        </p>

        <form className="form" onSubmit={usePassword ? onSubmitPassword : onSubmitOtp} noValidate>
          <Field
            label={t('auth:login.field.identifier')}
            value={identifier}
            onChange={setIdentifier}
            type="text"
            inputMode="text"
            autoComplete="username"
            disabled={busy}
            required
          />

          {/* [DEC-V1-012] Secondary path — only revealed behind the link
              below, never shown by default alongside the primary OTP field. */}
          {usePassword && (
            <Field
              label={t('auth:login.field.password')}
              value={credential}
              onChange={setCredential}
              type="password"
              autoComplete="current-password"
              disabled={busy}
              required
            />
          )}

          <div className="form__row-end">
            {usePassword ? (
              <>
                <Link className="link" href="/reset">
                  {t('auth:login.forgot')}
                </Link>
                <button
                  type="button"
                  className="link link--button"
                  onClick={() => {
                    setUsePassword(false);
                    setCredential('');
                    setError(null);
                  }}
                >
                  {t('auth:login.useCode')}
                </button>
              </>
            ) : (
              <button
                type="button"
                className="link link--button"
                onClick={() => setUsePassword(true)}
              >
                {t('auth:login.usePassword')}
              </button>
            )}
          </div>

          {/* [UI03] Announced politely rather than assertively: an error that
              interrupts mid-typing is worse than one read at a natural pause. */}
          <p className="form__error" role="status" aria-live="polite">
            {error ?? ''}
          </p>

          <div className="form__actions">
            <SubmitButton
              label={
                busy
                  ? t('auth:state.submitting')
                  : usePassword
                    ? t('auth:login.submit')
                    : t('auth:login.sendCode')
              }
              busy={busy}
              disabled={!identifier || (usePassword && !credential)}
            />
            <p className="form__alt">
              {t('auth:login.noAccount')}{' '}
              <Link className="link" href="/signup">
                {t('auth:login.signUpLink')}
              </Link>
            </p>
          </div>
        </form>
      </main>
    </>
  );
}
