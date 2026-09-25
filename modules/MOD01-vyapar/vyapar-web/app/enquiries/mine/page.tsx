"use client";

// [TR023] Provider/sender enquiry list — the Activity screen's "Responded"
// group (deferred in IMP14) now has a real home: a dedicated Enquiries
// list, sent/received tabs.
// [Real bug found live via coordinator's two-user test, fixed here] this
// row used to render literally as "enquire · open" — the raw action_type
// and state enum values, no target name, no counterpart, no timestamp.
// Every other list in the app (Discover, Businesses, Activity) resolves
// enum values to translated labels and real names; this one now matches
// that pattern instead of being a second, divergent rendering path.
// [Original-Vyapar upgrade, 2026-09-17] Upwork's "My proposals" screen was
// read as RESEARCH into the underlying problem this screen has, not copied:
// a flat list under Sent/Received gives no way to jump straight to what
// needs attention. The solution here is Vyapar's own — a second row of
// count-badged filter CHIPS (this app's existing `vy-chip` primitive, not
// Upwork's own tab-strip styling) for FR23's five real states, computed
// client-side from the same list already fetched (no new endpoint), with
// an "All" chip showing the unfiltered total. Filtering narrows in place;
// no navigation, no reload.
// [IMP38 — Refactor C] Now only the route: tab/filter/selection state and
// the useEnquiries data hook (SDK) here, markup in <EnquiriesView>.
// Traces to: FR23, TR023
import { useState } from "react";
import type { EnquiryRole } from "@/lib/sdk";
import Screen from "@/app/components/Screen";
import EnquiryThread from "@/app/components/EnquiryThread";
import EnquiriesView from "@/app/components/enquiries/EnquiriesView";
import { useEnquiries } from "@/app/hooks/engagement";

export default function MyEnquiriesPage() {
  const [role, setRole] = useState<EnquiryRole>("sent");
  const [stateFilter, setStateFilter] = useState<string | null>(null);
  // [IMP33] Which thread the ≥1024px split pane is showing. Unused below
  // that breakpoint, where rows navigate instead.
  const [selected, setSelected] = useState<string | null>(null);
  const enquiries = useEnquiries(role);

  // Switching Sent/Received starts from "All" with nothing selected.
  function changeRole(next: EnquiryRole) {
    setRole(next);
    setStateFilter(null);
    setSelected(null);
  }

  return (
    // ==================================================================
    // [IMP33 — desktop split pane]
    // REQUIREMENT (owner, 2026-09-17): "Enquiries/Activity: list + detail
    // split pane, so clicking a thread opens it beside the list instead
    // of navigating away." 04-ui.md F4's `--fk-bp-console` (≥1024) is the
    // sealed breakpoint for exactly this pattern.
    // APPROACH: below 1024px every row stays an ordinary <a> that
    // navigates to /enquiries/[id] — identical to today's phone flow, no
    // regression, and the route keeps working for notifications and
    // shared links. At ≥1024px the same rows become buttons that select a
    // thread into the right pane, rendered by the SAME <EnquiryThread>
    // component the route uses. The two behaviours are chosen by CSS
    // (`vy-console-only` / the mobile anchor), not by a viewport read, so
    // there is no hydration mismatch.
    // Traces to: FR23, 04-ui.md F4, product-owner direction 2026-09-17.
    // ==================================================================
    <Screen width="console">
      <EnquiriesView
        role={role}
        onRoleChange={changeRole}
        items={enquiries.data}
        stateFilter={stateFilter}
        onStateFilterChange={setStateFilter}
        selected={selected}
        onSelect={setSelected}
        renderThread={(id) => (
          <EnquiryThread
            key={id}
            id={id}
            onChanged={() => {
              void enquiries.refresh();
            }}
          />
        )}
      />
    </Screen>
  );
}
