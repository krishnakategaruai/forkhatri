"use client";

// [IMP38 — Refactor C] Activity, presentational half — markup moved
// verbatim out of app/activity/page.tsx (see that file for why this is a
// group grid rather than a split pane). Data in, nothing out: every row is a
// link to its own screen, built from the host's routes.
import { useTranslation } from "react-i18next";
import type { ActivityItem, ActivityResponse } from "@/lib/sdk";
import { RevealSection } from "@/app/components/Motion";
import { EmptyState } from "@/app/components/States";
import { useRoutes } from "@/app/host/HostProvider";
import type { VyaparRoutes } from "@/app/host/types";

export const ACTIVITY_GROUP_KEYS: [keyof ActivityResponse, string][] = [
  ["to_review", "groupToReview"],
  ["responded", "groupResponded"],
  ["partnerships", "groupPartnerships"],
  ["saved", "groupSaved"],
  ["posted", "groupPosted"],
  ["recently_viewed", "groupRecentlyViewed"],
  ["shared", "groupShared"],
  ["completed", "groupCompleted"],
];

function itemHref(routes: VyaparRoutes, item: ActivityItem): string {
  switch (item.kind) {
    case "listing":
      return routes.listing(item.id);
    case "opportunity":
      return routes.opportunity(item.id);
    case "enquiry":
      return routes.enquiry(item.id);
    default:
      return routes.partnership(item.id);
  }
}

export default function ActivityView({
  data,
  extrasSlot,
  hasExtras = false,
}: {
  data: ActivityResponse;
  /** [FE2] contracts and saved searches, shown under the title */
  extrasSlot?: React.ReactNode;
  /** [FE2] true when the extras have content, so "nothing here yet" is not shown next to them */
  hasExtras?: boolean;
}) {
  const { t } = useTranslation(["activity", "common"]);
  const routes = useRoutes();
  const isEmpty = ACTIVITY_GROUP_KEYS.every(([key]) => (data[key] ?? []).length === 0);
  const groups = ACTIVITY_GROUP_KEYS.filter(([key]) => (data[key] ?? []).length > 0);

  return (
    <>
      <h1>{t("activity:title")}</h1>
      {extrasSlot}
      {isEmpty && !hasExtras && <EmptyState mark="◔" title={t("activity:empty")} body={t("activity:emptyBody")} />}
      <div className="vy-grid">
        {groups.map(([key, labelKey], gi) => (
          <RevealSection key={key} index={gi} className="vy-stack">
            <h2 className="vy-section-title">{t(`activity:${labelKey}` as "groupSaved")}</h2>
            <div className="vy-stack" style={{ gap: "var(--space-2)" }}>
              {data[key].map((item) => (
                <a
                  key={`${item.kind}-${item.id}`}
                  className="vy-card vy-row"
                  style={{ textDecoration: "none", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}
                  href={itemHref(routes, item)}
                >
                  <span>{item.title || t("activity:untitled")}</span>
                  {item.status && (
                    <span className="vy-badge vy-badge-member-provided">
                      {t(`activity:status.${item.kind}.${item.status}` as "status.listing.draft", { defaultValue: item.status })}
                    </span>
                  )}
                </a>
              ))}
            </div>
          </RevealSection>
        ))}
      </div>
    </>
  );
}
