"use client";

// ======================================================================
// [IMP33 — route transitions + the responsive shell, in one wrapper]
//
// REQUIREMENT: (a) 04-ui.md F4's sealed breakpoint model was never built —
// every screen was a 480px phone column at any viewport width; (b) the
// product owner asked for real motion including "view transitions between
// routes".
//
// APPROACH: one component that every screen's <main> becomes. It does two
// things that were previously either missing or copy-pasted:
//
//  1. Shell width. `width` picks the F4 measure the screen actually needs:
//     "reading" = F4's 720px content column (forms, prose, detail
//     screens), "wide" = a collection measure (grids of cards),
//     "console" = the ≥1024px Admin list+detail measure. A page states
//     its intent once; globals.css owns the numbers.
//
//  2. Route motion. React's <ViewTransition> (React 19.2 / Next 16.3.5,
//     per nextjs.org/docs/app/guides/view-transitions) with a per-type
//     enter/exit map. The guide is explicit that this wrapper must live
//     in the page, not the layout — "Layouts persist across navigations,
//     so enter and exit never fire there" — which is exactly why this is
//     a component pages wrap themselves in rather than something added
//     once to layout.tsx. `default: "none"` means untyped navigations
//     (browser back/forward, router.refresh, Suspense reveals) do not
//     pick up a directional slide they did not ask for.
//
// Direction is decided by the link, not by this component: links going
// deeper pass transitionTypes={["vy-forward"]}, links going back pass
// ["vy-back"]. See LivingCard and the detail screens' back links.
//
// Traces to: 04-ui.md F4; product-owner direction 2026-09-17.
// ======================================================================

import * as React from "react";

// React's <ViewTransition> ships in the React build Next.js 16's App
// Router bundles (`next/dist/compiled/react` — verified present in this
// install), but NOT in the `@types/react` 19 typings, and not in the
// stable `react` package a non-Next tool would resolve. Reading it off the
// namespace with a fallback keeps this file type-safe AND keeps every
// screen rendering normally if a future React build drops or renames it —
// the documented behaviour without browser/runtime support is "your
// application works normally; the transitions do not animate", and this
// preserves that guarantee at the module level too.
type VTProps = {
  enter?: unknown;
  exit?: unknown;
  default?: unknown;
  children: React.ReactNode;
};
const ViewTransition =
  (React as unknown as { ViewTransition?: React.ComponentType<VTProps> }).ViewTransition ??
  (({ children }: VTProps) => <>{children}</>);

type Width = "reading" | "wide" | "console";

const WIDTH_CLASS: Record<Width, string> = {
  reading: "",
  wide: "vy-shell-wide",
  console: "vy-shell-wide vy-shell-console",
};

export default function Screen({
  width = "reading",
  className = "",
  children,
}: {
  width?: Width;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <ViewTransition
      enter={{ "vy-forward": "vy-nav-forward", "vy-back": "vy-nav-back", default: "none" }}
      exit={{ "vy-forward": "vy-nav-forward", "vy-back": "vy-nav-back", default: "none" }}
      default="none"
    >
      <main className={`vy-shell ${WIDTH_CLASS[width]} ${className}`.trim()}>{children}</main>
    </ViewTransition>
  );
}

// [IMP33 — shared-element transition] The card a person taps on a list and
// the heading of the screen it opens are the SAME object; naming both the
// same thing makes the browser animate one element moving, instead of one
// element vanishing and an unrelated one appearing. The Next.js guide
// calls this "the most important transition pattern" and names the exact
// prop combination used here: an explicit `share` alongside
// `default="none"` (with `default="none"` and no `share`, the pair
// silently stops morphing — a real footgun, documented).
//
// Usage: <Morph name={`listing-${id}`}> around the card title, and around
// the <h1> on the detail screen.
export function Morph({ name, children }: { name: string; children: React.ReactNode }) {
  const P = ViewTransition as React.ComponentType<VTProps & { name?: string; share?: string }>;
  return (
    <P name={name} share="vy-morph" default="none">
      {children}
    </P>
  );
}
