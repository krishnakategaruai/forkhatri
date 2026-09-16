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
// Traces to: FR44, FR18, FR19, FR20
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import IntentBar, { ParsedIntent } from "@/app/components/IntentBar";
import LivingCard from "@/app/components/LivingCard";

interface FirstRunState {
  step: number;
  done: boolean;
  display_name: string;
}

interface OpportunityCard {
  id: string;
  title: string;
  type: string;
  type_action_label: string;
  location: string | null;
  compensation: string | null;
  source_segment: string;
  submitter_name: string | null;
  posted_days_ago: number | null;
  relevance_reason: string | null;
}

interface FeedSection {
  key: string;
  items: OpportunityCard[];
  total_available: number;
}

interface FeedResponse {
  sections: FeedSection[];
  enrichment_prompt: string | null;
  sponsored?: OpportunityCard[]; // [FR30] at most one labelled card; sections stay organic
}

export default function HomePage() {
  const router = useRouter();
  const { t } = useTranslation(["discover", "opportunities", "ranking"]);
  const [state, setState] = useState<FirstRunState | null>(null);
  const [feed, setFeed] = useState<FeedResponse | null>(null);

  useEffect(() => {
    api
      .get<FirstRunState>("/v1/first-run/state")
      .then((s) => {
        setState(s);
        if (!s.done) {
          router.replace("/first-run");
          return;
        }
        api.get<FeedResponse>("/v1/opportunities/feed").then(setFeed);
      })
      .catch(() => setState(null));
  }, [router]);

  function runSearch(intent: ParsedIntent) {
    const params = new URLSearchParams();
    if (intent.text) params.set("q", intent.text);
    if (intent.category) params.set("category", intent.category.replace(" ", "_"));
    if (intent.locality) params.set("locality", intent.locality);
    router.push(`/businesses?${params.toString()}`);
  }

  function freshnessLabel(days: number | null): string {
    if (days === null) return "";
    if (days === 0) return t("discover:card.postedToday");
    if (days === 1) return t("discover:card.postedYesterday");
    return t("discover:card.postedDaysAgo", { days });
  }

  function relevanceLabel(reasonKey: string | null): string {
    if (!reasonKey) return "";
    if (["capability_fit", "intent_fit", "location_fit", "timing_fit", "value_fit", "experience_fit", "freshness_fit", "trust_fit"].includes(reasonKey)) {
      return t(`ranking:signal.${reasonKey}` as "signal.capability_fit");
    }
    return t(`ranking:fallback.${reasonKey}` as "fallback.matchedSearch", { defaultValue: "" });
  }

  return (
    <main className="vy-shell">
      {/* [Fix #8] Search-first home, WorkIndia/Upwork lens: intent bar +
          one-tap directory entry, both above the feed and above the fold. */}
      <div className="vy-stack">
        <IntentBar onSearch={runSearch} />
        <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} onClick={() => router.push("/businesses")}>
          ▤ {t("discover:home.openDirectory")}
        </button>
      </div>

      {state && <h1 style={{ fontSize: 22 }}>{t("discover:home.greeting", { name: state.display_name.split(" ")[0] })}</h1>}

      {feed === null && <p className="vy-muted">{t("discover:home.loadingFeed")}</p>}
      {feed?.enrichment_prompt && (
        <div className="vy-card">
          <p>{t(`discover:enrichment.${feed.enrichment_prompt}` as "enrichment.sparseProfile")}</p>
          <button className="vy-btn vy-btn-secondary" style={{ marginTop: 8 }} onClick={() => router.push("/listings/new")}>
            {t("discover:home.addCapabilities")}
          </button>
        </div>
      )}

      {feed?.sponsored?.map((item) => (
        <LivingCard
          key={`sponsored-${item.id}`}
          href={`/opportunities/${item.id}`}
          title={item.title}
          subtitle={[item.location, item.compensation].filter(Boolean).join(" · ")}
          sponsored
          meta={[
            t(`opportunities:actionLabel.${item.type_action_label}` as "actionLabel.apply"),
            item.submitter_name || undefined,
            freshnessLabel(item.posted_days_ago),
          ]
            .filter(Boolean)
            .join(" · ")}
        />
      ))}

      {feed?.sections.map((section) => (
        <div key={section.key} className="vy-stack">
          <div className="vy-row" style={{ justifyContent: "space-between" }}>
            <h2 style={{ fontSize: 16, color: "var(--text-secondary)" }}>{t(`discover:home.section${section.key.replace(/_(.)/g, (_, c) => c.toUpperCase()).replace(/^(.)/, (c) => c.toUpperCase())}` as "home.sectionForYou")}</h2>
            {section.total_available > section.items.length && (
              <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} onClick={() => router.push(`/opportunities/section/${section.key}`)}>
                {t("discover:home.seeAll", { count: section.total_available })}
              </button>
            )}
          </div>
          <div className="vy-stack">
            {section.items.map((item) => (
              <LivingCard
                key={item.id}
                href={`/opportunities/${item.id}`}
                title={item.title}
                subtitle={[item.location, item.compensation].filter(Boolean).join(" · ")}
                meta={[
                  t(`opportunities:actionLabel.${item.type_action_label}` as "actionLabel.apply"),
                  item.source_segment === "community" ? t("discover:home.sectionCommunity") : t("discover:home.sectionPublic"),
                  item.submitter_name || undefined,
                  freshnessLabel(item.posted_days_ago),
                  relevanceLabel(item.relevance_reason),
                ]
                  .filter(Boolean)
                  .join(" · ")}
              />
            ))}
          </div>
        </div>
      ))}

      {feed && feed.sections.length === 0 && !feed.enrichment_prompt && (
        <p className="vy-muted">{t("discover:home.noOpportunities")}</p>
      )}
    </main>
  );
}
