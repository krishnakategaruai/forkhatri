"use client";

// [IMP38 — Refactor C] One opportunity card, presentational (props in,
// callbacks out, no fetching). It wraps the shared LivingCard and owns the
// three meta lines Vyapar shows for an opportunity, which used to be
// assembled inline in three places:
//   - "feed":      Discover section card — action · source · freshness ·
//                  relevance, with the per-card Not interested/Share/Report
//                  menu (UX08);
//   - "sponsored": Discover's single labelled paid card — action · freshness;
//   - "similar":   the detail screen's "Similar opportunities" — which of
//                  the viewer's skills it matches (or the action), then
//                  "Posted n days ago".
// Text, classes and motion are exactly what those call sites rendered.
import { useTranslation } from "react-i18next";
import LivingCard from "@/app/components/LivingCard";
import { useRoutes } from "@/app/host/HostProvider";
import { freshnessLabel, postedLabel, signalLabel } from "./labels";
import type { Badge } from "@/lib/sdk";
import { BadgeList } from "@/app/components/trust/Badges";

export interface OpportunityCardItem {
  id: string;
  title: string;
  type_action_label: string;
  location: string | null;
  compensation: string | null;
  submitter_name: string | null;
  posted_days_ago: number | null;
  source_segment?: string;
  relevance_reason?: string | null;
  viewer_matched_labels?: string[];
  /** [FE2] real distance from the viewer, when both have coordinates */
  distance_km?: number | null;
  /** [FE2] the poster's earned badges */
  poster_badges?: Badge[];
}

export type OpportunityCardVariant = "feed" | "sponsored" | "similar";

export default function OpportunityCard({
  item,
  variant = "feed",
  index,
  onNotInterested,
}: {
  item: OpportunityCardItem;
  variant?: OpportunityCardVariant;
  /** Position in its list (entrance stagger). */
  index?: number;
  /** Feed only: remove the card (the caller records the reason). */
  onNotInterested?: () => void;
}) {
  const { t } = useTranslation(["discover", "opportunities", "ranking"]);
  const routes = useRoutes();
  const href = routes.opportunity(item.id);
  const subtitle = [item.location, item.compensation].filter(Boolean).join(" · ");
  const action = t(`opportunities:actionLabel.${item.type_action_label}` as "actionLabel.apply");

  if (variant === "similar") {
    return (
      <LivingCard
        index={index}
        href={href}
        morphName={`opportunity-${item.id}`}
        title={item.title}
        subtitle={subtitle}
        submitterName={item.submitter_name ?? undefined}
        meta={[
          item.viewer_matched_labels && item.viewer_matched_labels.length > 0
            ? t("opportunities:detail.matchesYourSkill", { skills: item.viewer_matched_labels.join(", ") })
            : action,
          postedLabel(t, item.posted_days_ago),
        ]
          .filter(Boolean)
          .join(" · ")}
      />
    );
  }

  if (variant === "sponsored") {
    return (
      <LivingCard
        href={href}
        morphName={`opportunity-${item.id}`}
        title={item.title}
        subtitle={subtitle}
        sponsored
        submitterName={item.submitter_name || undefined}
        meta={[action, freshnessLabel(t, item.posted_days_ago)].filter(Boolean).join(" · ")}
      />
    );
  }

  return (
    <LivingCard
      index={index}
      morphName={`opportunity-${item.id}`}
      href={href}
      title={item.title}
      subtitle={subtitle}
      submitterName={item.submitter_name || undefined}
      meta={[
        action,
        item.distance_km != null ? t("discover:businesses.distanceAway", { km: item.distance_km < 10 ? item.distance_km.toFixed(1) : Math.round(item.distance_km) }) : "",
        item.source_segment === "community" ? t("discover:home.sectionCommunity") : t("discover:home.sectionPublic"),
        freshnessLabel(t, item.posted_days_ago),
        item.relevance_reason ? signalLabel(t, item.relevance_reason, "") : "",
      ]
        .filter(Boolean)
        .join(" · ")}
      onNotInterested={onNotInterested}
      shareText={`${item.title} — found on Vyapar`}
      reportHref={`${href}#report-opportunity`}
    >
      <BadgeList badges={item.poster_badges} compact max={2} />
    </LivingCard>
  );
}
