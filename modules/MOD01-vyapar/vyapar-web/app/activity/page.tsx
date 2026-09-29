"use client";

// [TR055] Activity screen — the member's Saved, Responded, Shared, Posted,
// Recently viewed and Completed items grouped by state (FR55). "Responded"
// now has a real home (Enquiries, built in slice 4) — closes IMP14's own
// noted gap; the other five groups are real, backed by
// member_opportunity/member_listing.
// [Product-owner i18n rule] Converted to useTranslation().
// [IMP38 — Refactor C] Now only the route: the useActivity data hook (SDK,
// re-fetched on a live language switch) and <ActivityView>. The
// "To review" / "Partnerships" groups (FR27/FR26, slice 7) and the
// translated status badge are rendered by the view.
// Traces to: FR55, TR055, FR22-FR24
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import ActivityView from "@/app/components/activity/ActivityView";
import { useActivity } from "@/app/hooks/engagement";
import ActivityExtras, { useActivityExtras } from "@/app/components/activity/ActivityExtras";

export default function ActivityPage() {
  const { data } = useActivity();
  const extras = useActivityExtras();

  if (!data)
    return (
      <Screen width="wide">
        <div className="vy-skeleton" style={{ height: 40, width: 220, maxWidth: "60%" }} aria-hidden="true" />
        <SkeletonGrid count={4} />
      </Screen>
    );

  return (
    // ==================================================================
    // [IMP33 — desktop layout for Activity]
    // REQUIREMENT: same complaint, same fix — at 1440px this screen was a
    // single narrow column of eight stacked groups, most of them two or
    // three rows long, requiring a long scroll to see a page's worth of
    // content that fits easily side by side.
    // DECISION — a group grid, NOT a list+detail split pane: the owner's
    // direction named Enquiries and Activity together, and the split pane
    // is right for Enquiries because every row there opens the same kind
    // of thing (a thread). Activity's rows are deliberately heterogeneous
    // — a row can be a listing, an opportunity, an enquiry or a
    // partnership, each with its own full screen — so a shared right pane
    // would have to be four different detail views, and choosing one
    // would make the others feel wrong. Columns of grouped cards use the
    // width honestly without inventing a pane that cannot exist. This
    // divergence from the letter of the direction is recorded here
    // rather than applied silently.
    // Traces to: FR55, TR055, 04-ui.md F4, product-owner direction
    // 2026-09-17.
    // ==================================================================
    <Screen width="wide">
      <ActivityView data={data} extrasSlot={<ActivityExtras extras={extras} />} hasExtras={extras.hasAny} />
    </Screen>
  );
}
