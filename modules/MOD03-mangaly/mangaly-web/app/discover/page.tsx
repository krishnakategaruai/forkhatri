'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Avatar } from '@/components/Avatar';
import { SwipeDeck } from '@/components/SwipeDeck';
import { getSession } from '@/lib/auth';
import { accept, decline, listIncoming, sendRequest, type Connection } from '@/lib/connections';
import {
  getSnippet,
  search,
  whyThisMatch,
  type CompatibilityReason,
  type SearchResult,
  type Snippet,
} from '@/lib/discovery';

/* FR021/FR026/FR027/FR030/FR042/FR043 · UX15-UX19
 *
 * Discover: incoming connection requests first (they need a decision), then
 * the ranked search feed. Both use the same demographic-snippet
 * identification (locality/education/profession) — never name or photo,
 * and never a numeric score shown to the user (DEC-V1-002's weights drive
 * ORDER only).
 *
 * [2026-09-14, product-owner-requested pass] The blank silhouette + hidden
 * name previously read as an incomplete/broken profile rather than the
 * deliberate privacy design it is — nothing on screen told a first-time
 * user WHY identity was withheld, so the app's actual differentiation
 * (evidence over scores, no browsing of your identity without consent —
 * the opposite of the pay-to-unlock-name/photo pattern most matrimony apps
 * use) was invisible. Fixed by: (1) an explicit `identityProtected` caption
 * next to every anonymized avatar so the absence reads as a stated feature,
 * not a gap; (2) the top compatibility reason is now prefetched and shown
 * inline on every card by default (previously hidden behind a click) —
 * FR030/043's "evidence, not a score" model is the actual product thesis
 * and needs to be seen before a decision, not discovered after one.
 *
 * [2026-09-14, product-owner-requested pass #2: "candidate gets a Hinge
 * kind of thing"] The ranked search feed is now a one-at-a-time swipeable
 * card deck (`SwipeDeck`) instead of a scrolling list — a real gesture
 * interaction (drag to fling, or tap the explicit ✕/♥ buttons), matching
 * the review-one-candidate-at-a-time pattern of the named reference apps,
 * while keeping every privacy/evidence property above unchanged: the card
 * underneath is still identity-protected, still shows the same evidence
 * reasons, still sends the same `sendRequest()` call on a right-swipe. A
 * left-swipe/✕ is a local-only "not now" (no persisted state) — declining
 * an INCOMING request is a different, already-tracked action (FR043); this
 * is only about the order someone reviews an open-ended search feed in. */

type State = {
  phase: 'checking' | 'ready';
  incoming: Connection[];
  incomingSnippets: Record<string, Snippet | null>;
  results: SearchResult[];
  reasons: Record<string, CompatibilityReason[]>;
  sentTo: Set<string>;
};

export default function DiscoverPage() {
  const { t } = useTranslation(['common', 'discover']);
  const router = useRouter();
  const [state, setState] = useState<State>({
    phase: 'checking',
    incoming: [],
    incomingSnippets: {},
    results: [],
    reasons: {},
    sentTo: new Set(),
  });
  const [locality, setLocality] = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  async function refresh(localityFilter?: string) {
    const [incoming, results] = await Promise.all([listIncoming(), search(localityFilter)]);
    const candidateIds = [
      ...new Set([...incoming.map((r) => r.acting_account_id), ...results.map((r) => r.candidate_account_id)]),
    ];
    const [snippetEntries, reasonEntries] = await Promise.all([
      Promise.all(incoming.map(async (req) => [req.acting_account_id, await getSnippet(req.acting_account_id)] as const)),
      Promise.all(candidateIds.map(async (id) => [id, await whyThisMatch(id)] as const)),
    ]);
    setState((prev) => ({
      ...prev,
      phase: 'ready',
      incoming,
      incomingSnippets: Object.fromEntries(snippetEntries),
      results,
      reasons: Object.fromEntries(reasonEntries),
    }));
  }

  useEffect(() => {
    let active = true;
    (async () => {
      const session = await getSession();
      if (!active) return;
      if (!session) {
        router.replace('/login');
        return;
      }
      await refresh();
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

  async function onFilter(e: React.FormEvent) {
    e.preventDefault();
    await refresh(locality || undefined);
  }

  async function onAcceptIncoming(id: string) {
    await accept(id);
    await refresh(locality || undefined);
  }

  async function onDeclineIncoming(id: string) {
    await decline(id);
    await refresh(locality || undefined);
  }

  async function onConnect(candidateAccountId: string) {
    setError(null);
    const outcome = await sendRequest(candidateAccountId);
    if (!outcome.ok) {
      setError(
        outcome.message ?? (outcome.status === 0 ? t('discover:error.network') : t('discover:error.rateLimited'))
      );
      return;
    }
    setState((prev) => ({ ...prev, sentTo: new Set(prev.sentTo).add(candidateAccountId) }));
  }

  function toggleExpanded(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function snippetLabel(s: Snippet | null | undefined): string {
    if (!s) return t('discover:title');
    return [s.education_level, s.profession].filter(Boolean).join(' · ') || t('discover:title');
  }

  /* The evidence list for one candidate: the top reason always visible, the
     rest behind a one-tap expand — never a click just to see whether any
     evidence exists at all. */
  function ReasonList({ candidateId }: { candidateId: string }) {
    const list = state.reasons[candidateId] ?? [];
    if (list.length === 0) {
      return (
        <p className="caption" style={{ margin: '6px 0 0' }}>
          {t('discover:detail.noReasons')}
        </p>
      );
    }
    const isOpen = expanded.has(candidateId);
    const rest = list.slice(1);
    return (
      <div style={{ marginTop: 6 }}>
        <p className="caption" style={{ margin: 0, color: 'var(--text-primary)' }}>
          ✓ {list[0].text}
        </p>
        {isOpen &&
          rest.map((reason, i) => (
            <p key={i} className="caption" style={{ margin: '4px 0 0' }}>
              ✓ {reason.text}
            </p>
          ))}
        {rest.length > 0 && (
          <button
            type="button"
            className="link link--button"
            style={{ fontSize: '0.75rem', marginTop: 4 }}
            onClick={() => toggleExpanded(candidateId)}
          >
            {isOpen ? t('common:action.showLess') : t('discover:search.seeMoreReasons', { count: rest.length })}
          </button>
        )}
      </div>
    );
  }

  return (
    <>
      <header className="topbar">
        <h1>{t('discover:title')}</h1>
      </header>

      <main className="screen">
        <p className="caption" style={{ margin: 0 }}>
          {t('discover:blurb')}
        </p>

        {state.incoming.length > 0 && (
          <div className="card">
            <h2 className="h2">{t('discover:requests.title')}</h2>
            <ul className="category-list">
              {state.incoming.map((req) => {
                const snippet = state.incomingSnippets[req.acting_account_id];
                return (
                  <li key={req.id} className="req req--stacked">
                    <div className="req__main">
                      <Avatar anonymized size={44} />
                      <span className="req__title" style={{ flexDirection: 'column', display: 'flex' }}>
                        <span style={{ fontWeight: 600 }}>{snippetLabel(snippet)}</span>
                        <span className="caption">{snippet?.locality ?? ''}</span>
                        <span className="caption" style={{ opacity: 0.75 }}>
                          🔒 {t('discover:identityProtected')}
                        </span>
                      </span>
                    </div>
                    <ReasonList candidateId={req.acting_account_id} />
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                      <button className="cta" style={{ minHeight: 40 }} onClick={() => onAcceptIncoming(req.id)}>
                        {t('discover:requests.accept')}
                      </button>
                      <button className="icon-btn icon-btn--text" onClick={() => onDeclineIncoming(req.id)}>
                        {t('discover:requests.decline')}
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        <form className="field__box" onSubmit={onFilter} style={{ margin: 0 }}>
          <input
            id="discover-locality"
            name="locality"
            className="field__input"
            placeholder=" "
            value={locality}
            onChange={(e) => setLocality(e.target.value)}
          />
          <label className="field__label" htmlFor="discover-locality">
            {t('discover:search.localityPlaceholder')}
          </label>
        </form>

        <p className="form__error">{error ?? ''}</p>

        <SwipeDeck
          items={state.results}
          getKey={(r) => r.candidate_account_id}
          rightLabel={t('discover:search.connect')}
          leftLabel={t('discover:search.skip')}
          onSwipeRight={(r) => onConnect(r.candidate_account_id)}
          onSwipeLeft={() => {}}
          emptyState={<p className="caption">{t('discover:search.empty')}</p>}
          renderCard={(r) => (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <Avatar anonymized size={52} />
                <div style={{ minWidth: 0 }}>
                  <span className="body-lg" style={{ fontWeight: 600 }}>
                    {[r.education_level, r.profession].filter(Boolean).join(' · ') || t('discover:title')}
                  </span>
                  <p className="caption" style={{ margin: '2px 0 0' }}>
                    {r.locality ?? ''}
                  </p>
                  <p className="caption" style={{ margin: '2px 0 0', opacity: 0.75 }}>
                    🔒 {t('discover:identityProtected')}
                  </p>
                </div>
              </div>
              <div style={{ marginTop: 12, flex: 1, overflowY: 'auto' }}>
                <ReasonList candidateId={r.candidate_account_id} />
              </div>
            </>
          )}
        />
      </main>
    </>
  );
}
