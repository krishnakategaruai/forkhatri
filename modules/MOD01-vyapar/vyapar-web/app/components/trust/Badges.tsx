"use client";

// [FE2 — imp-backend-b §3, research §7] Count-based badges, rendered quietly.
//
// Each badge is an earned count ("Responds fast", "Repeat hires") — never a
// star, never a score. It renders as a neutral pill: thin-line icon plus a
// short label. The accent is deliberately NOT used (the accent marks the one
// thing that matters on a screen, and a badge is supporting evidence). Tap a
// badge and its plain-language description ("Median first reply under 2 h
// over 5+ enquiries") opens in place right under the row — no tooltip that a
// phone cannot hover, no sheet. On a card the tap is kept inside the card,
// so opening a description never navigates.
import { useState } from "react";
import type { Badge } from "@/lib/sdk";
import Icon from "@/app/components/Icon";

const BADGE_ICON: Record<string, string> = {
  responds_fast: "bolt",
  reliable: "shield",
  rising: "rising",
  top_recommended: "ribbon",
  verified_business: "check",
  repeat_hires: "repeat",
};

export function BadgeList({
  badges,
  compact = false,
  max,
}: {
  badges: Badge[] | null | undefined;
  /** Card size: slightly smaller type. */
  compact?: boolean;
  /** Show at most this many; the rest are summarised as "+n". */
  max?: number;
}) {
  const [open, setOpen] = useState<string | null>(null);
  if (!badges || badges.length === 0) return null;
  const shown = max ? badges.slice(0, max) : badges;
  const rest = badges.length - shown.length;
  const openBadge = badges.find((b) => b.key === open) ?? null;

  function toggle(e: React.MouseEvent, key: string) {
    // inside a card link: explain the badge, don't open the card
    e.preventDefault();
    e.stopPropagation();
    setOpen((cur) => (cur === key ? null : key));
  }

  return (
    <div className="vy-trust-badges" data-compact={compact || undefined}>
      <div className="vy-trust-badge-row">
        {shown.map((b) => (
          <button
            key={b.key}
            type="button"
            className="vy-trust-badge"
            aria-expanded={open === b.key}
            onClick={(e) => toggle(e, b.key)}
          >
            <Icon name={BADGE_ICON[b.key] ?? "check"} size={compact ? 13 : 14} strokeWidth={1.8} />
            <span>{b.label}</span>
          </button>
        ))}
        {rest > 0 && (
          <button
            type="button"
            className="vy-trust-badge"
            aria-expanded={false}
            onClick={(e) => toggle(e, badges[shown.length].key)}
          >
            +{rest}
          </button>
        )}
      </div>
      {openBadge && (
        <p className="vy-trust-badge-desc" role="note">
          <strong>{openBadge.label}</strong> · {openBadge.description}
        </p>
      )}
    </div>
  );
}
