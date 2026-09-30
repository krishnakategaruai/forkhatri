"use client";

// [Design language 2026-09-29, §13 .vy-empty] An empty state for the deals
// screens: a tinted icon tile (a real icon, not a glyph), a bold title, one
// line, one action. Shared by requests, contracts, promotions, workspace
// and the operator consoles so every "nothing here yet" reads the same.
import type { ReactNode } from "react";

export default function DealsEmpty({
  icon,
  title,
  body,
  action,
  tone = "brand",
}: {
  icon: ReactNode;
  title: string;
  body?: string;
  action?: ReactNode;
  tone?: "brand" | "teal" | "green" | "neutral";
}) {
  return (
    <div className="vy-empty">
      <span className={`vy-dl-tile vy-dl-tile-lg${tone === "neutral" ? "" : ` vy-dl-tile-${tone}`}`} aria-hidden="true">
        {icon}
      </span>
      <h3 style={{ color: "var(--text-primary)" }}>{title}</h3>
      {body && <p>{body}</p>}
      {action}
    </div>
  );
}
