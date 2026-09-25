"use client";

// ======================================================================
// [IMP33 — loading and empty states]
//
// REQUIREMENT: "polished empty/loading/skeleton states rather than bare
// text" (product owner, 2026-09-17).
//
// WHAT WAS WRONG: every screen in this app rendered its loading state as
// a single muted sentence and its empty state as another one. Two real
// consequences, both visible at 1440px: (1) the page has no height while
// loading, so content lands with a jump instead of resolving in place;
// (2) an empty screen gives no shape and no next action, so a new member
// with no data sees a page that looks broken rather than one that looks
// ready.
//
// DESIGN DECISION — no shimmer sweep: the conventional skeleton treatment
// is a light gradient travelling across the placeholder. This product's
// standing rules forbid gradients outright, and the owner has rejected
// that class of effect more than once. The pulse used instead (see
// `.vy-skeleton` in globals.css) moves between two steps of the existing
// ink ramp, which carries the same "this is coming" meaning using the
// lightness-step language the rest of the system already speaks.
//
// Traces to: product-owner direction 2026-09-17; FR43/TR043 (the
// skeletons are aria-hidden with a single polite live region, so a screen
// reader hears "Loading" once instead of reading placeholder boxes).
// ======================================================================

import { useTranslation } from "react-i18next";

export function SkeletonCard({ lines = 2 }: { lines?: number }) {
  return (
    <div className="vy-card vy-stack" aria-hidden="true" style={{ gap: 10 }}>
      <div className="vy-skeleton" style={{ height: 18, width: "62%" }} />
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="vy-skeleton"
          style={{ height: 12, width: i === lines - 1 ? "45%" : "88%" }}
        />
      ))}
    </div>
  );
}

// A loading state that occupies the shape the real content will occupy —
// same grid, same card count — so nothing moves when data lands.
export function SkeletonGrid({ count = 4, grid = true }: { count?: number; grid?: boolean }) {
  const { t } = useTranslation("common");
  return (
    <>
      <span role="status" aria-live="polite" className="vy-visually-hidden">
        {t("state.loading")}
      </span>
      <div className={grid ? "vy-grid vy-grid-3" : "vy-stack"}>
        {Array.from({ length: count }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </>
  );
}

export function EmptyState({
  mark = "◌",
  title,
  body,
  action,
}: {
  mark?: string;
  title: string;
  body?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="vy-empty">
      <span className="vy-empty-mark" aria-hidden="true">
        {mark}
      </span>
      <h3 style={{ color: "var(--text-primary)" }}>{title}</h3>
      {body && <p>{body}</p>}
      {action}
    </div>
  );
}
