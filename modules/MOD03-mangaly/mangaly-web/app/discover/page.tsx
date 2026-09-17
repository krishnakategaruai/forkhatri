'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Avatar } from '@/components/Avatar';
import ContextChip from '@/components/ContextChip';
import ForKhatriHubLink from '@/components/ForKhatriHubLink';
import { useActiveContext } from '@/lib/activeContext';
import { resolveMediaUrl } from '@/lib/api';
import { requireSession } from '@/lib/auth';
import { suggestProfile } from '@/lib/homeCircle';
import { accept, decline, listIncoming, sendRequest, type Connection } from '@/lib/connections';
import {
  getSnippet,
  search,
  whyThisMatch,
  type CompatibilityReason,
  type DiscoverFilters,
  type SearchResult,
  type Snippet,
} from '@/lib/discovery';

/* FR021/FR026/FR027/FR030/FR042/FR043 · UX15-UX19
 *
 * Discover: incoming connection requests first (they need a decision), then
 * the ranked search feed. Both use the same demographic-snippet
 * identification (locality/education/profession) — never name, and never a
 * numeric score shown to the user (DEC-V1-002's weights drive ORDER only).
 * Every searchable candidate's main photo is shown (DEC-V1-016).
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
 * inline on every card by default — FR030/043's "evidence, not a score"
 * model is the actual product thesis and needs to be seen before a decision.
 *
 * [2026-09-17, product-owner-requested pass] The one-card-at-a-time swipe
 * deck is replaced by a scrolling feed: "I want discover having list of
 * images so I don't get stuck on one person['s] images only, I can scroll
 * down for new profiles". Every matrimony reference (Shaadi, Jeevansathi,
 * BharatMatrimony) presents matches as a scannable list, and the deck also
 * capped the session at the first 20 results because nothing ever asked for
 * page 2. The feed pages through the backend's existing `page` parameter as
 * the reader nears the end, so scrolling keeps producing new people. Each
 * row keeps every privacy property the card had: photo and demographics
 * only, identity withheld until a connection is accepted. */

const MARITAL_OPTIONS = ['never_married', 'divorced', 'widowed', 'awaiting_divorce'];
const EDUCATION_OPTIONS = ['high_school', 'bachelors', 'masters', 'doctorate', 'other'];
const DIET_OPTIONS = ['vegetarian', 'non_vegetarian', 'eggetarian', 'vegan'];

type State = {
  phase: 'checking' | 'ready';
  incoming: Connection[];
  incomingSnippets: Record<string, Snippet | null>;
  results: SearchResult[];
  lookingForMissing: boolean;
  reasons: Record<string, CompatibilityReason[]>;
  sentTo: Set<string>;
  page: number;
  hasMore: boolean;
};

export default function DiscoverPage() {
  const { t } = useTranslation(['common', 'discover', 'profile']);
  const { contexts, active, choose, loaded } = useActiveContext();
  const family = active?.kind === 'family' ? active.circle : null;
  const familyId = family?.candidate_account_id;
  const familyName = family ? family.candidate_name.split(' ')[0] : '';
  const router = useRouter();
  const [state, setState] = useState<State>({
    phase: 'checking',
    incoming: [],
    incomingSnippets: {},
    results: [],
    lookingForMissing: false,
    reasons: {},
    sentTo: new Set(),
    page: 1,
    hasMore: false,
  });
  const [filters, setFilters] = useState<DiscoverFilters>({});
  const [draftFilters, setDraftFilters] = useState<DiscoverFilters>({});
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [brokenPhotos, setBrokenPhotos] = useState<Set<string>>(new Set());
  const [loadingMore, setLoadingMore] = useState(false);
  const sentinel = useRef<HTMLDivElement | null>(null);

  async function reasonsFor(ids: string[]): Promise<Record<string, CompatibilityReason[]>> {
    const entries = await Promise.all(ids.map(async (id) => [id, await whyThisMatch(id, familyId)] as const));
    return Object.fromEntries(entries);
  }

  async function refresh(activeFilters: DiscoverFilters = filters) {
    // A family member searches for the candidate they help; incoming requests
    // are the candidate's own decisions and never shown to them.
    const [incoming, found] = await Promise.all([
      familyId ? Promise.resolve([] as Connection[]) : listIncoming(),
      search(activeFilters, familyId, 1),
    ]);
    const results = found.results;
    const [snippetEntries, reasons] = await Promise.all([
      Promise.all(
        incoming.map(async (req) => [req.subject_account_id, await getSnippet(req.subject_account_id)] as const)
      ),
      reasonsFor([
        ...new Set([...incoming.map((r) => r.subject_account_id), ...results.map((r) => r.candidate_account_id)]),
      ]),
    ]);
    setState((prev) => ({
      ...prev,
      phase: 'ready',
      incoming,
      incomingSnippets: Object.fromEntries(snippetEntries),
      results,
      lookingForMissing: found.lookingForMissing,
      reasons,
      page: 1,
      hasMore: found.hasMore,
    }));
  }

  /* The next page is fetched as the reader approaches the end of the feed, so
     scrolling keeps producing new people rather than stopping at the first
     page. Results are keyed by account id, so a profile that shifts between
     pages as rankings change is never shown twice. */
  const loadMore = useCallback(async () => {
    if (loadingMore || !state.hasMore || state.lookingForMissing) return;
    setLoadingMore(true);
    const next = state.page + 1;
    const found = await search(filters, familyId, next);
    const fresh = found.results.filter(
      (r) => !state.results.some((existing) => existing.candidate_account_id === r.candidate_account_id)
    );
    const reasons = await reasonsFor(fresh.map((r) => r.candidate_account_id));
    setState((prev) => ({
      ...prev,
      results: [...prev.results, ...fresh],
      reasons: { ...prev.reasons, ...reasons },
      page: next,
      hasMore: found.hasMore,
    }));
    setLoadingMore(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, familyId, loadingMore, state.hasMore, state.lookingForMissing, state.page, state.results]);

  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    (async () => {
      const session = await requireSession();
      if (!alive) return;
      if (!session) {
        // requireSession() has already handed off to the ForKhatri entrance (TR16).
        return;
      }
      await refresh();
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, loaded, familyId]);

  useEffect(() => {
    const target = sentinel.current;
    if (!target) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) void loadMore();
      },
      { rootMargin: '400px' }
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [loadMore]);

  if (state.phase === 'checking') {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  async function applyFilters(next: DiscoverFilters) {
    setFilters(next);
    setFiltersOpen(false);
    await refresh(next);
  }

  function filterChip(label: string, active: boolean, onClick: () => void) {
    return (
      <button
        key={label}
        type="button"
        className={`quick-pick__chip${active ? ' quick-pick__chip--active' : ''}`}
        aria-pressed={active}
        onClick={onClick}
      >
        {label}
      </button>
    );
  }

  function toggleDraft(key: 'maritalStatus' | 'education' | 'diet', value: string) {
    setDraftFilters((d) => {
      const current = d[key] ?? [];
      return { ...d, [key]: current.includes(value) ? current.filter((v) => v !== value) : [...current, value] };
    });
  }

  async function onAcceptIncoming(id: string) {
    await accept(id);
    await refresh();
  }

  async function onDeclineIncoming(id: string) {
    await decline(id);
    await refresh();
  }

  /* FR042 — a Home Circle member sends the request for the candidate they help
     (the owner's 2026-09-17 decision, replacing DEC-V1-019: on Shaadi.com and the
     other matrimony services a parent who runs the profile sends interest
     themselves). The request is recorded as the candidate's, with the parent
     named as the sender, so the recipient always sees whose profile it is. */
  async function onConnect(candidateAccountId: string) {
    setError(null);
    const outcome = await sendRequest(candidateAccountId, familyId);
    if (!outcome.ok) {
      setError(
        outcome.message ?? (outcome.status === 0 ? t('discover:error.network') : t('discover:error.rateLimited'))
      );
      return;
    }
    setState((prev) => ({ ...prev, sentTo: new Set(prev.sentTo).add(candidateAccountId) }));
  }

  async function onSuggest(profileAccountId: string) {
    if (!family) return;
    setError(null);
    setNotice(null);
    const outcome = await suggestProfile(family.membership_id, profileAccountId);
    if (!outcome.ok) {
      setError(t('discover:family.suggestFailed'));
      return;
    }
    setNotice(t('discover:family.suggested', { name: familyName }));
  }

  function toggleExpanded(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function educationLabel(level: string | null | undefined): string | null {
    if (!level) return null;
    const key = `profile:option.highest_education_level.${level}`;
    const label = t(key);
    return label === key || label === `option.highest_education_level.${level}` ? level : label;
  }

  const activeFilterCount = [
    filters.nearby,
    filters.ageMin ?? filters.ageMax,
    filters.openToRelocate ? true : undefined,
    filters.maritalStatus?.length ? true : undefined,
    filters.education?.length ? true : undefined,
    filters.diet?.length ? true : undefined,
  ].filter((v) => v !== undefined).length;

  function snippetLabel(s: Snippet | null | undefined): string {
    if (!s) return t('discover:title');
    return [educationLabel(s.education_level), s.profession].filter(Boolean).join(' · ') || t('discover:title');
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
        <div className="topbar__actions">
          {contexts && active && <ContextChip contexts={contexts} active={active} onChoose={choose} />}
          <ForKhatriHubLink />
        </div>
      </header>

      <main className="screen">
        <p className="caption" style={{ margin: 0 }}>
          {family ? t('discover:family.blurb', { name: familyName }) : t('discover:blurb')}
        </p>

        {!family && state.incoming.length > 0 && (
          <div className="card">
            <h2 className="h2">{t('discover:requests.title')}</h2>
            <ul className="category-list">
              {state.incoming.map((req) => {
                const snippet = state.incomingSnippets[req.subject_account_id];
                return (
                  <li key={req.id} className="req req--stacked">
                    <div className="req__main">
                      <Avatar photoUrl={snippet?.photo_url} anonymized size={52} />
                      <span className="req__title" style={{ flexDirection: 'column', display: 'flex' }}>
                        <span style={{ fontWeight: 600 }}>{snippetLabel(snippet)}</span>
                        <span className="caption">{snippet?.locality ?? ''}</span>
                        <span className="caption" style={{ opacity: 0.75 }}>
                          🔒 {t('discover:identityProtected')}
                        </span>
                      </span>
                    </div>
                    {req.sent_by_family && (
                      <p className="caption" style={{ margin: '6px 0 0' }}>
                        {t('discover:requests.sentByFamily')}
                      </p>
                    )}
                    <ReasonList candidateId={req.subject_account_id} />
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

        <div className="filter-bar">
          <button
            type="button"
            className={`quick-pick__chip${activeFilterCount ? ' quick-pick__chip--active' : ''}`}
            aria-haspopup="dialog"
            onClick={() => {
              setDraftFilters(filters);
              setFiltersOpen(true);
            }}
          >
            {activeFilterCount
              ? t('discover:filters.openCount', { count: activeFilterCount })
              : t('discover:filters.open')}
          </button>
          {filterChip(t('discover:filters.nearbyCity'), filters.nearby === 'city', () =>
            void applyFilters({ ...filters, nearby: filters.nearby === 'city' ? undefined : 'city' })
          )}
        </div>

        {filtersOpen && (
          <div className="sheet-backdrop" onClick={() => setFiltersOpen(false)}>
            <div
              className="sheet"
              role="dialog"
              aria-modal="true"
              aria-label={t('discover:filters.title')}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="sheet__handle" aria-hidden="true" />
              <div className="sheet__head">
                <h2 className="sheet__title">{t('discover:filters.title')}</h2>
              </div>
              <div className="sheet__field">
                <div className="label">{t('discover:filters.location')}</div>
                <div className="quick-pick__chips">
                  {filterChip(t('discover:filters.nearbyCity'), draftFilters.nearby === 'city', () =>
                    setDraftFilters((d) => ({ ...d, nearby: d.nearby === 'city' ? undefined : 'city' }))
                  )}
                  {filterChip(t('discover:filters.nearbyState'), draftFilters.nearby === 'state', () =>
                    setDraftFilters((d) => ({ ...d, nearby: d.nearby === 'state' ? undefined : 'state' }))
                  )}
                  {filterChip(t('discover:filters.openToRelocate'), !!draftFilters.openToRelocate, () =>
                    setDraftFilters((d) => ({ ...d, openToRelocate: !d.openToRelocate }))
                  )}
                </div>
              </div>
              <div className="sheet__field">
                <div className="label">{t('discover:filters.age')}</div>
                <div className="age-range">
                  <input
                    className="field__input"
                    type="number"
                    inputMode="numeric"
                    min={18}
                    max={99}
                    name="age-min"
                    aria-label={t('discover:filters.ageFrom')}
                    placeholder={t('discover:filters.ageFrom')}
                    value={draftFilters.ageMin ?? ''}
                    onChange={(e) =>
                      setDraftFilters((d) => ({ ...d, ageMin: e.target.value ? Number(e.target.value) : undefined }))
                    }
                  />
                  <span aria-hidden="true">–</span>
                  <input
                    className="field__input"
                    type="number"
                    inputMode="numeric"
                    min={18}
                    max={99}
                    name="age-max"
                    aria-label={t('discover:filters.ageTo')}
                    placeholder={t('discover:filters.ageTo')}
                    value={draftFilters.ageMax ?? ''}
                    onChange={(e) =>
                      setDraftFilters((d) => ({ ...d, ageMax: e.target.value ? Number(e.target.value) : undefined }))
                    }
                  />
                </div>
              </div>
              <div className="sheet__field">
                <div className="label">{t('discover:filters.maritalStatus')}</div>
                <div className="quick-pick__chips">
                  {MARITAL_OPTIONS.map((o) =>
                    filterChip(t(`profile:option.marital_status.${o}`), !!draftFilters.maritalStatus?.includes(o), () =>
                      toggleDraft('maritalStatus', o)
                    )
                  )}
                </div>
              </div>
              <div className="sheet__field">
                <div className="label">{t('discover:filters.education')}</div>
                <div className="quick-pick__chips">
                  {EDUCATION_OPTIONS.map((o) =>
                    filterChip(t(`profile:option.highest_education_level.${o}`), !!draftFilters.education?.includes(o), () =>
                      toggleDraft('education', o)
                    )
                  )}
                </div>
              </div>
              <div className="sheet__field">
                <div className="label">{t('discover:filters.diet')}</div>
                <div className="quick-pick__chips">
                  {DIET_OPTIONS.map((o) =>
                    filterChip(t(`profile:option.diet.${o}`), !!draftFilters.diet?.includes(o), () => toggleDraft('diet', o))
                  )}
                </div>
              </div>
              <div className="sheet__actions">
                <button type="button" className="quick-pick__chip" onClick={() => void applyFilters({})}>
                  {t('discover:filters.reset')}
                </button>
                <button type="button" className="cta sheet__save" onClick={() => void applyFilters(draftFilters)}>
                  {t('discover:filters.apply')}
                </button>
              </div>
            </div>
          </div>
        )}

        {error && (
          <p className="form__error" role="alert">
            {error}
          </p>
        )}
        {notice && (
          <p className="caption" role="status" style={{ margin: 0 }}>
            {notice}
          </p>
        )}

        {state.lookingForMissing ? (
          <div className="card">
            <h2 className="h2">
              {family
                ? t('discover:lookingFor.familyTitle', { name: familyName })
                : t('discover:lookingFor.title')}
            </h2>
            <p className="caption">
              {family ? t('discover:lookingFor.familyBody', { name: familyName }) : t('discover:lookingFor.body')}
            </p>
            {!family && (
              <Link href="/me?edit=partner_preference" className="cta cta--link">
                {t('discover:lookingFor.cta')}
              </Link>
            )}
          </div>
        ) : state.results.length === 0 ? (
          <p className="caption">
            {family ? t('discover:family.empty', { name: familyName }) : t('discover:search.empty')}
          </p>
        ) : (
          <>
            <ul className="feed">
              {state.results.map((r) => {
                const sent = state.sentTo.has(r.candidate_account_id);
                return (
                  <li key={r.candidate_account_id} className="feed-card">
                    <div className="feed-card__photo">
                      {r.photo_url && !brokenPhotos.has(r.candidate_account_id) ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={resolveMediaUrl(r.photo_url) ?? ''}
                          alt=""
                          loading="lazy"
                          onError={() => setBrokenPhotos((prev) => new Set(prev).add(r.candidate_account_id))}
                        />
                      ) : (
                        <Avatar anonymized size={96} />
                      )}
                    </div>
                    <div className="feed-card__body">
                      <span className="feed-card__headline">
                        {[r.age ? t('discover:card.age', { age: r.age }) : null, r.locality]
                          .filter(Boolean)
                          .join(' · ')}
                      </span>
                      <span className="caption">
                        {[educationLabel(r.education_level), r.profession].filter(Boolean).join(' · ')}
                      </span>
                      <span className="caption discover-card__privacy">
                        🔒{' '}
                        {family
                          ? t('discover:family.identityProtected', { name: familyName })
                          : t('discover:identityProtected')}
                      </span>
                      <ReasonList candidateId={r.candidate_account_id} />
                      <div className="feed-card__actions">
                        {sent ? (
                          <span className="caption feed-card__sent">{t('discover:search.requestSent')}</span>
                        ) : (
                          <button
                            type="button"
                            className="cta feed-card__cta"
                            onClick={() => void onConnect(r.candidate_account_id)}
                          >
                            {family
                              ? t('discover:family.sendRequest', { name: familyName })
                              : t('discover:search.connect')}
                          </button>
                        )}
                        {family && (
                          <>
                            <button
                              type="button"
                              className="quick-pick__chip"
                              onClick={() => void onSuggest(r.candidate_account_id)}
                            >
                              {t('discover:family.suggest', { name: familyName })}
                            </button>
                            <Link href={`/profile/${r.candidate_account_id}`} className="quick-pick__chip">
                              {t('discover:family.note')}
                            </Link>
                          </>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
            <div ref={sentinel} aria-hidden="true" />
            <p className="caption" role="status" style={{ textAlign: 'center' }}>
              {loadingMore
                ? t('common:state.loading')
                : state.hasMore
                  ? t('discover:search.more')
                  : t('discover:search.end')}
            </p>
          </>
        )}
      </main>
    </>
  );
}
