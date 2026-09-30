"use client";

// [TR023] The member's requests (glossary: "Requests", never "Enquiries" on
// screen): sent and received, with FR23's state filters computed client-side
// from the same list (no new endpoint).
// [IMP33] ≥1024px: list + detail split pane; below that a row navigates to
// /enquiries/[id], which also serves notifications and shared links.
// [IMP38 — Refactor C] Route = state + data hooks; markup in <EnquiriesView>.
// [Design language 2026-09-29] Both lists are loaded so the Sent / Received
// switch can carry its counts; switching tabs starts from "All".
// Traces to: FR23, TR023, 04-ui.md F4
import { useState } from "react";
import type { EnquiryRole } from "@/lib/sdk";
import Screen from "@/app/components/Screen";
import EnquiryThread from "@/app/components/EnquiryThread";
import EnquiriesView from "@/app/components/enquiries/EnquiriesView";
import { useEnquiries } from "@/app/hooks/engagement";
import "@/app/styles/deals-2026.css";

export default function MyEnquiriesPage() {
  // Received first: what needs the reader's answer is the reason to open an inbox.
  const [role, setRole] = useState<EnquiryRole>("received");
  const [stateFilter, setStateFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const sent = useEnquiries("sent");
  const received = useEnquiries("received");
  const current = role === "sent" ? sent : received;

  function changeRole(next: EnquiryRole) {
    setRole(next);
    setStateFilter(null);
    setSelected(null);
  }

  function refreshAll() {
    void sent.refresh();
    void received.refresh();
  }

  return (
    <Screen width="console">
      <EnquiriesView
        role={role}
        onRoleChange={changeRole}
        items={current.data}
        counts={{ sent: sent.data?.length ?? null, received: received.data?.length ?? null }}
        stateFilter={stateFilter}
        onStateFilterChange={setStateFilter}
        selected={selected}
        onSelect={setSelected}
        renderThread={(id) => <EnquiryThread key={id} id={id} embedded onChanged={refreshAll} />}
      />
    </Screen>
  );
}
