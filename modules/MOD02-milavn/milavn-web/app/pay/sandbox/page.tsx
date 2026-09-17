'use client';

/* Development test checkout (FR102). In the real product this step belongs to
 * ForKhatri Payments (MOD06: UPI, cards). Until that external dependency is
 * connected, the API's sandbox provider sends payers here so the whole paid-spot
 * flow can be exercised end to end. It says plainly that no money moves, and the
 * API refuses to run the sandbox anywhere but localhost. */

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { ErrorState } from '@/components/States';
import { api, ApiError } from '@/lib/api';
import { formatInr } from '@/lib/format';

type Checkout = { reference: string; amount_paise: number; status: string; hold_expires_at: string | null; title: string; slug: string };

function SandboxInner() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const ref = useSearchParams().get('ref') ?? '';
  const [c, setC] = useState<Checkout | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!ref) return;
    api<Checkout>(`/payments/sandbox/${encodeURIComponent(ref)}`).then(setC).catch((e) => setErr(e instanceof ApiError ? e.message : t('state.error')));
  }, [ref, t]);

  const finish = async (outcome: 'paid' | 'failed') => {
    if (!c) return;
    setBusy(true);
    try {
      await api(`/payments/sandbox/${encodeURIComponent(ref)}/complete`, { body: { outcome } });
      router.replace(`/a/${c.slug}?payment=return`);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : t('state.error'));
      setBusy(false);
    }
  };

  const amount = c ? formatInr(c.amount_paise, i18n.language) : '';
  return (
    <main className="screen checkout">
      <div className="checkout__test" role="note">{t('pay.sandbox.banner')}</div>
      {err && <ErrorState message={err} onRetry={() => window.location.reload()} />}
      {!c && !err && <div className="sk" style={{ height: 220, borderRadius: 20 }} />}
      {c && (
        <section className="card stack checkout__card">
          <span className="label">{t('pay.sandbox.payingFor')}</span>
          <h1 className="h2" style={{ margin: 0 }}>{c.title}</h1>
          <div className="checkout__amount">{amount}</div>
          <p className="caption" style={{ margin: 0 }}>{t('pay.sandbox.explain')}</p>
          {c.status !== 'awaiting_payment' ? (
            <p className="caption" style={{ margin: 0 }}>{t('pay.sandbox.done')}</p>
          ) : (
            <div className="stack" style={{ gap: 8 }}>
              <button className="btn btn--primary btn--block" disabled={busy} onClick={() => finish('paid')}>{t('pay.sandbox.pay', { amount })}</button>
              <button className="btn btn--ghost btn--block" disabled={busy} onClick={() => finish('failed')}>{t('pay.sandbox.fail')}</button>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

export default function SandboxCheckoutPage() {
  return <Suspense fallback={<main className="screen" />}><SandboxInner /></Suspense>;
}
