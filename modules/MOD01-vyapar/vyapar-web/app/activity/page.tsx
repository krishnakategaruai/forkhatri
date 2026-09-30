"use client";

// [TR055] Activity screen — the member's Saved, Responded, Shared, Posted,
// Recently viewed and Completed items grouped by state (FR55), plus the
// "To review" / "Partnerships" groups (FR27/FR26) and, from FE2, contracts
// and saved searches.
// [IMP38 — Refactor C] Only the route: the useActivity data hook (SDK,
// re-fetched on a live language switch) and <ActivityView>.
//
// DECISION (kept from IMP33): a group list, NOT a list+detail split pane.
// Activity's rows are heterogeneous — a row can be a profile, a post, a
// request or a partnership, each with its own full screen — so a shared
// right pane would have to be four different detail views. On desktop the
// width goes to a two-column layout instead: contracts and saved searches
// on the left, the grouped list on the right.
// Traces to: FR55, TR055, FR22-FR24
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import ActivityView from "@/app/components/activity/ActivityView";
import { useActivity } from "@/app/hooks/engagement";
import ActivityExtras, { useActivityExtras } from "@/app/components/activity/ActivityExtras";
import "@/app/styles/account-2026.css";

export default function ActivityPage() {
  const { data } = useActivity();
  const extras = useActivityExtras();

  if (!data)
    return (
      <Screen width="wide">
        <div className="vy-skeleton" style={{ height: 40, width: 220, maxWidth: "60%" }} aria-hidden="true" />
        <SkeletonGrid count={4} grid={false} />
      </Screen>
    );

  return (
    <Screen width="wide">
      <ActivityView data={data} extrasSlot={<ActivityExtras extras={extras} />} hasExtras={extras.hasAny} />
    </Screen>
  );
}
