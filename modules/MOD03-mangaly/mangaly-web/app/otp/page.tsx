'use client';

import EntranceRedirect from '@/components/EntranceRedirect';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { OtpBoxes } from '@/components/form/OtpBoxes';
import { SubmitButton } from '@/components/form/SubmitButton';
import { resendOtp, verifyOtp, type OtpOutcome, type OtpPurpose } from '@/lib/auth';

/* FR095 · TR095 · UX04 · UI04 · TS212-213 · SP095
 *
 * `outcome` from the server is a machine-readable code (verified / invalid /
 * expired / too_many_attempts) — this screen supplies UX04's distinct copy
 * for each one itself. That is not a contradiction of SP095's anti-
 * enumeration requirement: SP095 hides whether an ACCOUNT exists, not why a
 * code the caller already proved they received got rejected (see the
 * backend's `identity.verify_otp` docstring for the full reasoning). */

const RESEND_COOLDOWN_SECONDS = 45;

function maskIdentifier(identifier: string): string {
  if (identifier.includes('@')) {
    const [local, domain] = identifier.split('@');
    const head = local.slice(0, Math.min(2, local.length));
    return `${head}${'·'.repeat(Math.max(3, local.length - head.length))}@${domain}`;
  }
  const tail = identifier.slice(-3);
  return `${identifier.slice(0, 3)}${'·'.repeat(Math.max(3, identifier.length - 6))}${tail}`;
}

const ERROR_KEY: Record<Exclude<OtpOutcome, 'verified'>, string> = {
  invalid: 'auth:otp.error.invalid',
  expired: 'auth:otp.error.expired',
  too_many_attempts: 'auth:otp.error.tooManyAttempts',
};

function OtpEntry() {
  const { t } = useTranslation(['auth', 'common']);
  const router = useRouter();
  const params = useSearchParams();
  const identifier = params.get('id') ?? '';
  const purpose = (params.get('purpose') ?? 'signup') as OtpPurpose;

  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(RESEND_COOLDOWN_SECONDS);
  const [resendNotice, setResendNotice] = useState<string | null>(null);
  const submittedRef = useRef(false);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  async function submit(fullCode: string) {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setBusy(true);
    setError(null);

    const result = await verifyOtp(identifier, fullCode, purpose);
    setBusy(false);
    submittedRef.current = false;

    if (!result.ok) {
      setError(t('auth:error.network'));
      setCode('');
      return;
    }
    if (result.data.outcome === 'verified') {
      // [UX04, DEC-V1-012] Both signup and login (the OTP-primary path) open
      // a session server-side and land on Home directly — neither should ask
      // the user to log in a second time right after proving who they are.
      // Only password_reset/identifier_change have no session to route into
      // yet, so they fall back to Login.
      const opensSession = purpose === 'signup' || purpose === 'login';
      router.push(opensSession ? '/' : '/login');
      return;
    }
    setError(t(ERROR_KEY[result.data.outcome]));
    setCode('');
  }

  // [UX04] Auto-submits once all 6 digits are entered.
  useEffect(() => {
    if (code.length === 6 && !busy) void submit(code);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  async function onResend() {
    setResendNotice(null);
    setError(null);
    const result = await resendOtp(identifier, purpose);
    if (result.ok) {
      setResendNotice(t('auth:otp.resent'));
      setCooldown(RESEND_COOLDOWN_SECONDS);
    } else if (result.kind === 'rateLimited') {
      setError(t('auth:otp.error.resendRateLimited'));
    } else {
      setError(result.message ?? t('auth:error.network'));
    }
  }

  return (
    <>
      <header className="topbar">
        <h1>{t('auth:otp.title', { channel: identifier.includes('@') ? 'email' : 'phone' })}</h1>
      </header>

      <main className="screen screen--form">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <p className="muted body-lg" style={{ margin: 0 }}>
          {t('auth:otp.explainer', { identifier: maskIdentifier(identifier) })}
        </p>

        <div className="form">
          <OtpBoxes value={code} onChange={setCode} disabled={busy} error={!!error} />

          <p className="form__error" role="status" aria-live="polite">
            {error ?? resendNotice ?? ''}
          </p>

          <div className="otp-resend">
            {cooldown > 0 ? (
              <span className="caption">{t('auth:otp.resendIn', { seconds: cooldown })}</span>
            ) : (
              <button type="button" className="link link--button" onClick={onResend}>
                {t('auth:otp.resend')}
              </button>
            )}
          </div>

          <div className="form__actions">
            <SubmitButton
              label={busy ? t('auth:otp.verifying') : t('auth:otp.verify')}
              busy={busy}
              disabled={code.length < 6}
            />
          </div>
        </div>
      </main>
    </>
  );
}

/* [ForKhatri TR16, 2026-09-14] Sign-in, sign-up, one-time codes and password
 * reset belong to the ForKhatri entrance. This route only hands off to it; the
 * interim screen below is retained (not rendered) rather than deleted. */
export default function OtpPage() {
  return <EntranceRedirect />;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function LegacyOtpPage() {
  // useSearchParams requires a Suspense boundary in the App Router.
  return (
    <Suspense fallback={null}>
      <OtpEntry />
    </Suspense>
  );
}
