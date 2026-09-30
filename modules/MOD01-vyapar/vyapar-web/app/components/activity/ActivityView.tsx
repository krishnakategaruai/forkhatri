"use client";

// [IMP38 — Refactor C] Activity, presentational half. Data in, nothing out:
// every row is a link to its own screen, built from the host's routes.
//
// [Design language 2026-09-29] A page header, then filter chips (All plus
// each non-empty group, with its count), then one list card per group:
// rows with a tinted tile for the kind of thing (post, profile, request,
// business partnership), the title, the kind as a hint, and the state as a
// badge. Contracts and saved searches (ActivityExtras) sit first on a phone
// and in a left column on desktop. No split pane: rows open four different
// kinds of screen, so a shared detail pane cannot exist (see the page).
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Briefcase, ChevronRight, Handshake, Inbox, Store, type LucideIcon } from "lucide-react";
import type { ActivityItem, ActivityResponse } from "@/lib/sdk";
import { useRoutes } from "@/app/host/HostProvider";
import type { VyaparRoutes } from "@/app/host/types";
import PageHeader from "@/app/components/account/PageHeader";
import type { Tint } from "@/app/components/account/ShortcutList";

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

const KIND_VISUAL: Record<ActivityItem["kind"], { icon: LucideIcon; tint: Tint }> = {
  listing: { icon: Store, tint: "indigo" },
  opportunity: { icon: Briefcase, tint: "brand" },
  enquiry: { icon: Inbox, tint: "teal" },
  partnership: { icon: Handshake, tint: "plum" },
};

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
  /** [FE2] contracts and saved searches */
  extrasSlot?: React.ReactNode;
  /** true when the extras have content, so "nothing here yet" is not shown next to them */
  hasExtras?: boolean;
}) {
  const { t } = useTranslation(["activity", "common"]);
  const routes = useRoutes();
  const [tab, setTab] = useState<"all" | keyof ActivityResponse>("all");
  const groups = ACTIVITY_GROUP_KEYS.filter(([key]) => (data[key] ?? []).length > 0);
  const isEmpty = groups.length === 0;
  const shown = tab === "all" ? groups : groups.filter(([key]) => key === tab);

  return (
    <>
      <PageHeader title={t("activity:title")} purpose={t("activity:purpose")} />
      <div className="vy-acct-two" data-side="left">
        <div className="vy-acct-two-main">
          {groups.length > 1 && (
            <div className="vy-acct-tabs" role="group" aria-label={t("activity:title")}>
              <button type="button" className="vy-chip" aria-pressed={tab === "all"} onClick={() => setTab("all")}>
                {t("activity:all")}
              </button>
              {groups.map(([key, labelKey]) => (
                <button key={key} type="button" className="vy-chip" aria-pressed={tab === key} onClick={() => setTab(key)}>
                  {t(`activity:${labelKey}` as "groupSaved")}
                  <span className="vy-acct-tab-count">{data[key].length}</span>
                </button>
              ))}
            </div>
          )}

          {isEmpty && !hasExtras && (
            <div className="vy-empty">
              <span className="vy-empty-mark" aria-hidden="true">
                <Inbox size={26} strokeWidth={1.9} />
              </span>
              <h3 style={{ color: "var(--text-primary)" }}>{t("activity:empty")}</h3>
              <p>{t("activity:emptyBody")}</p>
            </div>
          )}

          {shown.map(([key, labelKey]) => (
            <section key={key} className="vy-acct-section" aria-labelledby={`act-${key}`}>
              <div className="vy-acct-section-head">
                <h2 id={`act-${key}`} className="vy-section-title">
                  {t(`activity:${labelKey}` as "groupSaved")}
                </h2>
                <p>{data[key].length}</p>
              </div>
              <div className="vy-card vy-acct-list">
                {data[key].map((item) => {
                  const v = KIND_VISUAL[item.kind] ?? KIND_VISUAL.opportunity;
                  const Icon = v.icon;
                  return (
                    <Link key={`${item.kind}-${item.id}`} className="vy-acct-row" href={itemHref(routes, item)} transitionTypes={["vy-forward"]} data-badge={item.status ? "" : undefined}>
                      <span className="vy-acct-tile" data-tint={v.tint} aria-hidden="true">
                        <Icon size={20} strokeWidth={1.9} />
                      </span>
                      <span className="vy-acct-row-text">
                        <span className="vy-acct-row-label">{item.title || t("activity:untitled")}</span>
                        <span className="vy-acct-row-hint">{t(`activity:kind.${item.kind}` as "kind.listing")}</span>
                      </span>
                      <span className="vy-acct-row-end">
                        {item.status ? (
                          <span className="vy-badge vy-badge-member-provided">
                            {t(`activity:status.${item.kind}.${item.status}` as "status.listing.draft", { defaultValue: item.status })}
                          </span>
                        ) : (
                          <ChevronRight size={18} strokeWidth={2} aria-hidden="true" />
                        )}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
        {hasExtras && <aside className="vy-acct-two-side">{extrasSlot}</aside>}
      </div>
    </>
  );
}
