"use client";

// [Fix #5 — "See all" affordance] Full, unbounded view of one Discover
// feed section, reached only by tapping "See all N" on the home feed's
// capped preview — keeps the home screen itself short (no scrolling
// burden on primary content) while still making every eligible item
// reachable, not silently dropped past the cap.
// Traces to: FR18 (not a separate FR — a UX completion of the same one)
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import LivingCard from "@/app/components/LivingCard";

interface OpportunityCard {
  id: string;
  title: string;
  location: string | null;
  compensation: string | null;
  type_action_label: string;
  source_segment: string;
  submitter_name: string | null;
  posted_days_ago: number | null;
  relevance_reason: string | null;
}

const SECTION_LABEL_KEY: Record<string, string> = {
  for_you: "sectionForYou",
  explore: "sectionExplore",
  near_you: "sectionNearYou",
  community: "sectionCommunity",
  public: "sectionPublic",
};

export default function FeedSectionPage({ params }: { params: Promise<{ key: string }> }) {
  const { key } = useParamsPromise(params);
  const { t } = useTranslation(["discover", "opportunities", "ranking"]);
  const [items, setItems] = useState<OpportunityCard[] | null>(null);

  useEffect(() => {
    api.get<OpportunityCard[]>(`/v1/opportunities/feed/section/${key}`).then(setItems);
  }, [key]);

  function freshnessLabel(days: number | null): string {
    if (days === null) return "";
    if (days === 0) return t("discover:card.postedToday");
    if (days === 1) return t("discover:card.postedYesterday");
    return t("discover:card.postedDaysAgo", { days });
  }

  return (
    <main className="vy-shell">
      <h1>{t(`discover:home.${SECTION_LABEL_KEY[key] ?? "sectionForYou"}` as "home.sectionForYou")}</h1>
      {items === null && <p className="vy-muted">{t("common:state.loading")}</p>}
      <div className="vy-stack">
        {items?.map((item) => (
          <LivingCard
            key={item.id}
            href={`/opportunities/${item.id}`}
            title={item.title}
            subtitle={[item.location, item.compensation].filter(Boolean).join(" · ")}
            meta={[
              t(`opportunities:actionLabel.${item.type_action_label}` as "actionLabel.apply"),
              item.submitter_name || undefined,
              freshnessLabel(item.posted_days_ago),
            ]
              .filter(Boolean)
              .join(" · ")}
          />
        ))}
      </div>
    </main>
  );
}
