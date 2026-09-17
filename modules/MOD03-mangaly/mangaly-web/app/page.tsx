'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { resolveMediaUrl } from '@/lib/api';
import ForKhatriHubLink from '@/components/ForKhatriHubLink';
import { getSession, logOut, type Session } from '@/lib/auth';
import { reportOutage } from '@/lib/outage';
import { redirectToEntrance } from '@/lib/platform';
import { getContexts } from '@/lib/homeCircle';
import { getOwnProfile, type Profile } from '@/lib/profile';

/* FR090 · TR090 · UX01 · UI01 · SP090
 *
 * Launch routing. Checks the session server-side and shows either the signed-in
 * home or the signed-out entry point. TR090 requires this to fall back to a
 * usable screen rather than hanging — a routine condition for this module's
 * tier-2/3 connectivity audience, not an edge case — so a failed check renders
 * the signed-out state instead of an indefinite spinner.
 *
 * [BR01/FR001] A signed-in account with no saved profile is routed straight
 * into the existence-tier wizard — BR01 calls a saved profile "the floor of
 * the product", so there is nothing useful for a profile-less account to do
 * on Home yet. FR091 (Onboarding) sits between OTP verification and this
 * check in UX03's full flow but is not built in this pass (progressive,
 * buildable slices) — skipping stright to the wizard is a scope reduction,
 * not a UX03 contradiction: onboarding is purely explanatory content with no
 * gating behaviour of its own. */

type State =
  | { phase: 'checking' }
  | { phase: 'in'; session: Session; profile: Profile }
  | { phase: 'out' };

export default function HomePage() {
  const { t } = useTranslation(['common', 'auth']);
  const router = useRouter();
  const [state, setState] = useState<State>({ phase: 'checking' });

  useEffect(() => {
    let active = true;
    (async () => {
      let session: Session | null;
      try {
        session = await getSession();
      } catch {
        // [ForKhatri TR15/TR16] Mangaly or ForKhatri sign-in is unreachable:
        // the shared retry state (OutageGate), never "signed out" (a loop).
        if (active) reportOutage();
        return;
      }
      if (!active) return;
      if (!session) {
        // [TR16] Signed out: the ForKhatri entrance signs the member in and
        // returns them here. The old signed-out screen below is retained, unused.
        redirectToEntrance();
        return;
      }
      const profile = await getOwnProfile();
      if (!active) return;
      if (!profile) {
        // A parent or relative helping someone else has no candidate profile of
        // their own; they belong in that candidate's circle, not the wizard.
        const contexts = await getContexts();
        if (!active) return;
        router.replace(contexts?.circles.length ? '/circle' : '/profile/create');
        return;
      }
      setState({ phase: 'in', session, profile });
    })();
    return () => {
      active = false;
    };
  }, [router]);

  if (state.phase === 'checking') {
    return (
      <main className="screen screen--centered">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  if (state.phase === 'out') {
    return (
      <main className="screen screen--centered">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ margin: '0 0 6px', fontSize: '1.75rem', lineHeight: '2.125rem' }}>
            {t('common:app.name')}
          </h1>
          <p className="muted" style={{ margin: 0 }}>
            {t('common:app.tagline')}
          </p>
        </div>
        <div className="form__actions" style={{ width: '100%' }}>
          <Link className="cta cta--link" href="/signup">
            {t('auth:signup.submit')}
          </Link>
          <p className="form__alt">
            {t('auth:signup.haveAccount')}{' '}
            <Link className="link" href="/login">
              {t('auth:signup.logInLink')}
            </Link>
          </p>
        </div>
      </main>
    );
  }

  return (
    <>
      <header className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          <span className="brand-mark" aria-hidden="true">
            m
          </span>
          <h1>{t('common:app.name')}</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <ForKhatriHubLink />
          <button className="icon-btn icon-btn--text" onClick={() => void logOut()}>
            {t('common:action.logOut')}
          </button>
        </div>
      </header>

      <main className="screen">
        <div className="card">
          {state.profile.photo_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={resolveMediaUrl(state.profile.photo_url) ?? undefined}
              alt=""
              style={{
                width: 64,
                height: 64,
                borderRadius: 16,
                objectFit: 'cover',
                float: 'left',
                marginRight: 12,
              }}
            />
          )}
          <h2 className="h2" style={{ margin: 0 }}>
            {state.profile.name}
          </h2>
          <p className="caption" style={{ margin: 0 }}>
            {state.profile.city_locality}
          </p>
          <p className="body-lg" style={{ margin: 0, clear: 'both' }}>
            {t('common:app.tagline')}
          </p>
        </div>

        <div className="card">
          <h2 className="h2">{t('common:build.title')}</h2>
          <p className="caption" style={{ margin: 0 }}>
            {t('common:build.explainer')}
          </p>
          <Link className="link" href="/status">
            {t('common:build.title')} →
          </Link>
        </div>
      </main>
    </>
  );
}
