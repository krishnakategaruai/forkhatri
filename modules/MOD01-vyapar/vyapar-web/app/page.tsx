"use client";

// [TR018] Opportunity Discover feed, five sections (FR18) — the home
// screen. [TR044] first-run redirect (FR44).
// [Coordinator browser-check fixes, 2026-09-15]:
//  - The WorkIndia/Upwork lens puts search first: an <IntentBar> now sits
//    at the very top of home, above the feed, with a one-tap "Businesses &
//    Professionals" directory link right next to it — both fit on a
//    phone's first screen without scrolling, per the design direction's
//    own no-scrolling-burden rule.
//  - Cards now render the freshness stamp, source segment + submitter, and
//    the one-line relevance reason feed.py's fix now sends per FR18's own
//    required card fields — previously only title/location/value/segment.
//  - Sections that have more items than shown now render a "See all N"
//    link (feed.py's `total_available` field) instead of a long,
//    repetitive scroll.
// [Product-owner i18n rule] Converted to useTranslation() — every string
// on this screen is a key in locales/<lang>/discover.json, not literal text.
// [IMP38 — Refactor C] Now only the route: first-run check and feed come
// from data hooks (useFirstRunState, useFeed — both via the SDK, the feed
// re-fetching on a live language switch), the markup from <DiscoverView>.
// Traces to: FR44, FR18, FR19, FR20
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSdk } from "@/lib/sdk/react";
import type { ParsedIntent } from "@/app/components/IntentBar";
import { DEFAULT_FILTERS, type Filters } from "@/app/components/FilterSheet";
import Screen from "@/app/components/Screen";
import DiscoverView from "@/app/components/discover/DiscoverView";
import { useFeed, useFirstRunState } from "@/app/hooks/opportunities";
import { useRoutes } from "@/app/host/HostProvider";

export default function HomePage() {
  const router = useRouter();
  const sdk = useSdk();
  const routes = useRoutes();
  // [Original-Vyapar upgrade, product-owner direction: "based on skills we
  // need list to be flown"] the same shared FilterSheet Businesses already
  // uses — on Discover only `skills` actually narrows results (the feed's
  // other sections are relevance-ranked by FR19, not independently
  // sortable/radius-filtered the way a flat search list is).
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const firstRun = useFirstRunState();
  const state = firstRun.data;
  const feed = useFeed({ skills: filters.skills }, { enabled: !!state?.done });

  // [TR044] A member who has not finished first run goes there first.
  useEffect(() => {
    if (state && !state.done) router.replace("/first-run");
  }, [state, router]);

  function runSearch(intent: ParsedIntent) {
    const params = new URLSearchParams();
    if (intent.text) params.set("q", intent.text);
    // [Third critique pass fix] intent.category is now a real taxonomy
    // slug from IntentBar's own suggestion fetch.
    if (intent.category) params.set("category", intent.category);
    if (intent.locality) params.set("locality", intent.locality);
    router.push(routes.businesses(params.toString()));
  }

  function notInterested(sectionKey: string, opportunityId: string) {
    sdk.opportunities
      .notInterested(opportunityId, "not_interested")
      .then(() =>
        feed.setData((f) =>
          f ? { ...f, sections: f.sections.map((s) => (s.key === sectionKey ? { ...s, items: s.items.filter((i) => i.id !== opportunityId) } : s)) } : f,
        ),
      )
      .catch(() => {});
  }

  return (
    // [IMP33] Discover is a *collection* screen, so it takes the wide
    // measure (F4's 720px reading column is the right max for prose and
    // the wrong max for a grid of opportunity cards).
    <Screen width="wide">
      <DiscoverView
        displayName={state ? state.display_name : null}
        feed={feed.data}
        filters={filters}
        onFiltersChange={setFilters}
        onSearch={runSearch}
        onOpenDirectory={() => router.push(routes.businesses())}
        onAddCapabilities={() => router.push(routes.newListing)}
        onSeeAll={(key) => router.push(routes.feedSection(key))}
        onPost={() => router.push(routes.post)}
        onNotInterested={notInterested}
      />
    </Screen>
  );
}
