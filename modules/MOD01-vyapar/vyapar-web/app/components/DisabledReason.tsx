"use client";

// [Critique P2, design language 2026-09-29] A disabled primary action must
// say why, in words, right under it ("Add your name to continue") — a
// greyed button with no reason reads as broken, especially to a first-time
// or less literate user. Render it only while the action is blocked for a
// reason the person can fix (not while a request is in flight); give the
// button `aria-describedby={id}` so screen readers hear the same reason.
import { Info } from "lucide-react";

export default function DisabledReason({ id, show, children }: { id: string; show: boolean; children: React.ReactNode }) {
  if (!show) return null;
  return (
    <p id={id} className="vy-disabled-reason" role="note">
      <Info size={16} strokeWidth={2} aria-hidden="true" />
      <span>{children}</span>
    </p>
  );
}
