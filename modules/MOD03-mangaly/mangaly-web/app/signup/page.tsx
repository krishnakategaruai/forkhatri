'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Field } from '@/components/form/Field';
import { SubmitButton } from '@/components/form/SubmitButton';
import { signUp } from '@/lib/auth';
import { authErrorText } from '@/lib/authErrorText';

/* FR092 · TR092 · UX03 · UI03 · TS203–TS205 · SP092 · SP104 · DEC-V1-012
 *
 * [DEC-V1-012, 2026-09-13] Identifier + OTP only — no password field. Real
 * competitor research (BharatMatrimony/Shaadi.com/Jeevansathi all treat OTP
 * as first-class; PhonePe/Swiggy/Truecaller are effectively OTP-only) found
 * password-at-signup to be exactly the friction point this module's own
 * named audience (tier-2/3 connectivity, older parent-generation users) is
 * worst served by. Setting a password remains a real, supported feature —
 * added later from Settings, not here.
 *
 * The success state is identical whether the identifier was new or already
 * registered — SP092 found an "already registered" branch to be an
 * account-enumeration oracle, and UI03 already set the single-variant-success
 * precedent for the reset screen this follows. */

type Mode = 'phone' | 'email';

export default function SignUpPage() {
  const { t } = useTranslation(['auth', 'common']);
  const router = useRouter();

  const [mode, setMode] = useState<Mode>('phone');
  const [identifier, setIdentifier] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);

    const result = await signUp(identifier);
    setBusy(false);

    if (result.ok) {
      // [UX03/UX04] Sign-Up → OTP verification → Onboarding.
      router.push(`/otp?id=${encodeURIComponent(identifier)}&purpose=signup`);
      return;
    }
    setError(authErrorText(result, t));
  }

  return (
    <>
      <header className="topbar">
        <h1>{t('auth:signup.title')}</h1>
      </header>

      <main className="screen screen--form">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <p className="muted body-lg" style={{ margin: 0 }}>
          {t('auth:signup.subtitle')}
        </p>

        <form className="form" onSubmit={onSubmit} noValidate>
          {/* [UI03] Segmented control with Phone pre-selected, per the
              BharatMatrimony/Shaadi convention that research cites. */}
          <div className="segmented" role="tablist" aria-label={t('auth:signup.field.phone')}>
            {(['phone', 'email'] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                role="tab"
                aria-selected={mode === m}
                className={`segmented__opt${mode === m ? ' is-active' : ''}`}
                onClick={() => {
                  setMode(m);
                  setIdentifier('');
                }}
              >
                {t(`auth:signup.tab.${m}`)}
              </button>
            ))}
          </div>

          <Field
            label={t(`auth:signup.field.${mode}`)}
            value={identifier}
            onChange={setIdentifier}
            type={mode === 'email' ? 'email' : 'tel'}
            inputMode={mode === 'email' ? 'email' : 'tel'}
            autoComplete={mode === 'email' ? 'email' : 'tel'}
            disabled={busy}
            required
          />

          <p className="form__error" role="status" aria-live="polite">
            {error ?? ''}
          </p>

          <div className="form__actions">
            <SubmitButton
              label={busy ? t('auth:state.submitting') : t('auth:signup.submit')}
              busy={busy}
              disabled={!identifier}
            />
            <p className="form__alt">
              {t('auth:signup.haveAccount')}{' '}
              <Link className="link" href="/login">
                {t('auth:signup.logInLink')}
              </Link>
            </p>
          </div>
        </form>
      </main>
    </>
  );
}
