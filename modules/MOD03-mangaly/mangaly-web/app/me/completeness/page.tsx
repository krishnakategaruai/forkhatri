'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { requireSession } from '@/lib/auth';
import { ENHANCED_CATEGORIES } from '@/lib/profileCategoryConfig';
import { getAllAttributes, getCompleteness, type AttributeState, type CompletenessReport } from '@/lib/profile';

/* FR005/TR005 · UX11 "Completeness status screen"
 *
 * Three physically separate sections — never one blended bar (BR01 DEC-003,
 * re-affirmed by UX11's own Decisions log). Each missing item is tappable and
 * jumps straight to the category that would satisfy it, and each section is
 * its own labelled region so a screen reader gets the same "never blended"
 * guarantee a sighted user gets (UX11 accessibility notes).
 *
 * [2026-09-14, critique-agent finding] The enhanced tier previously showed
 * only a bare "{filled}/{total}" count with zero tappable targets — the one
 * screen whose entire job is "here's what's left" refused to take anyone to
 * what was actually left. `getAllAttributes()` (already fetched by `/me`)
 * is fetched here too so the same missing-category list UX the
 * discoverability tier already had can apply to the enhanced tier too,
 * without needing a new backend field. */

type PageState =
  | { phase: 'checking' }
  | { phase: 'ready'; report: CompletenessReport; attrStates: Record<string, Record<string, AttributeState>> };

function categoryOf(missingKey: string): string {
  // "education.highest_education_level" / "partner_preference.age_range_or_locality"
  return missingKey.split('.')[0];
}

export default function CompletenessPage() {
  const { t } = useTranslation(['common', 'profile']);
  const router = useRouter();
  const [state, setState] = useState<PageState>({ phase: 'checking' });

  useEffect(() => {
    let active = true;
    (async () => {
      const session = await requireSession();
      if (!active) return;
      if (!session) {
        // requireSession() has already handed off to the ForKhatri entrance (TR16).
        return;
      }
      const [report, attrStates] = await Promise.all([getCompleteness(), getAllAttributes()]);
      if (!active) return;
      if (!report) {
        router.replace('/profile/create');
        return;
      }
      setState({ phase: 'ready', report, attrStates });
    })();
    return () => {
      active = false;
    };
  }, [router]);

  if (state.phase === 'checking') {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  const { report, attrStates } = state;
  const unfilledEnhanced = ENHANCED_CATEGORIES.filter((cat) => {
    const values = Object.values(attrStates[cat.category] ?? {});
    return !values.some((s) => s === 'value' || s === 'declined');
  });

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" onClick={() => router.push('/me')} aria-label={t('common:action.back')}>
          ←
        </button>
        <h1>{t('profile:completeness.title')}</h1>
        <span style={{ width: 44 }} aria-hidden="true" />
      </header>

      <main className="screen">
        <section className="tier-section" aria-label={t('profile:completeness.tier.existence.title')}>
          <div className="tier-section__head">
            <h2 className="h2">{t('profile:completeness.tier.existence.title')}</h2>
            <span className="pill pill--live">✓</span>
          </div>
          <p className="tier-section__note">{t('profile:completeness.tier.existence.met')}</p>
        </section>

        <section
          className="tier-section"
          aria-label={t('profile:completeness.tier.discoverability.title')}
        >
          <div className="tier-section__head">
            <h2 className="h2">{t('profile:completeness.tier.discoverability.title')}</h2>
            <span className={`pill ${report.discoverability_complete ? 'pill--live' : 'pill--pending'}`}>
              {report.discoverability_complete ? '✓' : report.discoverability_missing.length}
            </span>
          </div>
          {report.discoverability_complete ? (
            <p className="tier-section__note">{t('profile:completeness.tier.discoverability.met')}</p>
          ) : (
            <>
              <p className="tier-section__note">{t('profile:completeness.tier.discoverability.notMet')}</p>
              <ul className="tier-section__missing">
                {report.discoverability_missing.map((missing) => {
                  const category = categoryOf(missing);
                  return (
                    <li key={missing}>
                      <Link href={`/me?edit=${category}`} className="tier-section__missing-item">
                        <span>{t(`profile:hub.category.${category}`)}</span>
                        <span aria-hidden="true">→</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </section>

        <section className="tier-section" aria-label={t('profile:completeness.tier.enhanced.title')}>
          <div className="tier-section__head">
            <h2 className="h2">{t('profile:completeness.tier.enhanced.title')}</h2>
            <span className="pill pill--wip">
              {report.enhanced_filled_categories}/{report.enhanced_total_categories}
            </span>
          </div>
          <p className="tier-section__note">{t('profile:completeness.tier.enhanced.note')}</p>
          <p className="tier-section__note">
            {t('profile:completeness.tier.enhanced.progress', {
              filled: report.enhanced_filled_categories,
              total: report.enhanced_total_categories,
            })}
          </p>
          {unfilledEnhanced.length > 0 && (
            <ul className="tier-section__missing">
              {unfilledEnhanced.map((cat) => (
                <li key={cat.category}>
                  <Link href={`/me?edit=${cat.category}`} className="tier-section__missing-item">
                    <span>{t(`profile:hub.category.${cat.category}`)}</span>
                    <span aria-hidden="true">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </>
  );
}
