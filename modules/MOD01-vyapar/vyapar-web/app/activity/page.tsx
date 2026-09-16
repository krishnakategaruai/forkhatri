"use client";

// [TR055] Activity screen — the member's Saved, Responded, Shared, Posted,
// Recently viewed and Completed items grouped by state (FR55). "Responded"
// now has a real home (Enquiries, built in slice 4) — closes IMP14's own
// noted gap; the other five groups are real, backed by
// member_opportunity/member_listing.
// [Product-owner i18n rule] Converted to useTranslation().
// Traces to: FR55, TR055, FR22-FR24
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";

// [FR27/FR26 — slice 7] "To review" (open review invites, first — they
// expire in 30 days) and "Partnerships" (sent/received requests). Each row
// opens the thread, where the review composer sits in place.
interface ActivityItem {
  kind: "listing" | "opportunity" | "enquiry" | "partnership";
  id: string;
  title: string;
  group: string;
}

interface ActivityResponse {
  saved: ActivityItem[];
  posted: ActivityItem[];
  recently_viewed: ActivityItem[];
  shared: ActivityItem[];
  completed: ActivityItem[];
  responded: ActivityItem[];
  to_review: ActivityItem[];
  partnerships: ActivityItem[];
}

const GROUP_KEYS: [keyof ActivityResponse, string][] = [
  ["to_review", "groupToReview"],
  ["responded", "groupResponded"],
  ["partnerships", "groupPartnerships"],
  ["saved", "groupSaved"],
  ["posted", "groupPosted"],
  ["recently_viewed", "groupRecentlyViewed"],
  ["shared", "groupShared"],
  ["completed", "groupCompleted"],
];

const KIND_PATH: Record<ActivityItem["kind"], string> = {
  listing: "listings",
  opportunity: "opportunities",
  enquiry: "enquiries",
  partnership: "partnerships",
};

export default function ActivityPage() {
  const { t } = useTranslation(["activity", "common"]);
  const [data, setData] = useState<ActivityResponse | null>(null);

  useEffect(() => {
    api.get<ActivityResponse>("/v1/activity").then(setData);
  }, []);

  if (!data) return <main className="vy-shell"><p>{t("common:state.loading")}</p></main>;

  const isEmpty = GROUP_KEYS.every(([key]) => (data[key] ?? []).length === 0);

  return (
    <main className="vy-shell">
      <h1>{t("activity:title")}</h1>
      {isEmpty && <p className="vy-muted">{t("activity:empty")}</p>}
      {GROUP_KEYS.map(([key, labelKey]) =>
        (data[key] ?? []).length > 0 ? (
          <div key={key} className="vy-stack">
            <h2 style={{ fontSize: 16, color: "var(--text-secondary)" }}>{t(`activity:${labelKey}` as "groupSaved")}</h2>
            <div className="vy-stack">
              {data[key].map((item) => (
                <a key={`${item.kind}-${item.id}`} className="vy-card" style={{ textDecoration: "none" }} href={`/${KIND_PATH[item.kind]}/${item.id}`}>
                  {item.title || t("activity:untitled")}
                </a>
              ))}
            </div>
          </div>
        ) : null
      )}
    </main>
  );
}
