"use client";

// [Design language 2026-09-29, owner review of /profile] The Profile hub's
// shortcuts as ONE card of rows (icon tile, label, one-line hint, chevron)
// grouped under quiet uppercase titles, the way Settings screens read in
// WhatsApp, Airbnb or Google. Replaces nine full-size tiles that did not
// fit a 390px screen. Rows are 56px tall (44px minimum target, more for a
// budget phone). Internal paths use the router link; the way back to the
// host platform is a plain anchor.
import type { ReactNode } from "react";
import Link from "next/link";
import { ChevronRight, type LucideIcon } from "lucide-react";

export type Tint = "brand" | "secondary" | "amber" | "sky" | "green" | "indigo" | "plum" | "teal" | "danger" | "warning" | "verified";

export interface Shortcut {
  href: string;
  label: string;
  hint?: string;
  icon: LucideIcon;
  tint?: Tint;
  /** A count shown as a solid pill before the chevron (open requests, invites). */
  count?: number;
  /** A small badge instead of the chevron (a role, a state). */
  badge?: ReactNode;
}

export interface ShortcutGroup {
  title?: string;
  items: Shortcut[];
}

function Row({ item }: { item: Shortcut }) {
  const Icon = item.icon;
  const external = /^https?:\/\//.test(item.href);
  const body = (
    <>
      <span className="vy-acct-tile" data-tint={item.tint} aria-hidden="true">
        <Icon size={20} strokeWidth={1.9} />
      </span>
      <span className="vy-acct-row-text">
        <span className="vy-acct-row-label">{item.label}</span>
        {item.hint && <span className="vy-acct-row-hint">{item.hint}</span>}
      </span>
      <span className="vy-acct-row-end">
        {item.count != null && item.count > 0 && <span className="vy-acct-row-count">{item.count}</span>}
        {item.badge ?? <ChevronRight size={18} strokeWidth={2} aria-hidden="true" />}
      </span>
    </>
  );
  const dataBadge = item.badge ? "" : undefined;
  if (external) {
    return (
      <a className="vy-acct-row" href={item.href} data-badge={dataBadge}>
        {body}
      </a>
    );
  }
  return (
    <Link className="vy-acct-row" href={item.href} transitionTypes={["vy-forward"]} data-badge={dataBadge}>
      {body}
    </Link>
  );
}

export default function ShortcutList({ groups, ariaLabel }: { groups: ShortcutGroup[]; ariaLabel?: string }) {
  const shown = groups.filter((g) => g.items.length > 0);
  if (shown.length === 0) return null;
  return (
    <nav className="vy-card vy-acct-list" aria-label={ariaLabel}>
      {shown.map((g, gi) => (
        <div key={g.title ?? gi} className="vy-acct-list-group">
          {g.title && <div className="vy-acct-group">{g.title}</div>}
          {g.items.map((item) => (
            <Row key={item.href + item.label} item={item} />
          ))}
        </div>
      ))}
    </nav>
  );
}
