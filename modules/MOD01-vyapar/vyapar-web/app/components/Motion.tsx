"use client";

// ======================================================================
// [IMP33 — motion system] The app's shared motion vocabulary, in one file.
//
// REQUIREMENT (product owner, 2026-09-17): "I really feel you should
// drastically improve styling, themes, colors, motions, etc in the app."
// Within the standing, repeatedly-restated constraints: near-monochrome
// base, exactly one accent, no gradients, no glassmorphism, no glow, no
// ambient mesh, minimalist first.
//
// WHY THESE PRIMITIVES AND NOT AD-HOC ANIMATION PER SCREEN: before this
// pass, motion in Vyapar existed in exactly three places (the command hub
// expand, LivingCard's hover lift, the language dropdown) and every list
// in the app appeared instantly, fully-formed, with no sense of order or
// arrival. Adding one-off `motion.div`s per screen would have produced
// fifteen slightly-different timings. These three components are the only
// entrance motion in the app, so every list on every screen shares one
// curve and one rhythm.
//
// WHY `motion` AND NOT React's <ViewTransition> FOR THIS: the Next.js 16
// view-transitions guide (nextjs.org/docs/app/guides/view-transitions, doc
// version 16.3.5 — this app's exact Next version) states that per-item
// staggered animations during navigation are not available through the
// View Transitions path. Route-level and shared-element motion therefore
// use <ViewTransition> (see Screen.tsx and LivingCard.tsx); list/card
// entrance staggering uses `motion`, which is already a dependency. That
// division is the documented one, not a preference.
//
// SPRING CHOICE: stiffness 320 / damping 30 is critically-ish damped — it
// settles without visible overshoot. Overshoot ("bounce") is the single
// most common way motion reads as toy-like rather than premium, and this
// product's tone is a trust/commerce surface for a community, not a
// consumer toy.
//
// Traces to: product-owner direction 2026-09-17; 04-ui.md's per-screen
// motion sections (list reveals, 150-250ms, reduced-motion → fades).
// ======================================================================

import { motion, useReducedMotion } from "motion/react";

const SPRING = { type: "spring", stiffness: 320, damping: 30, mass: 0.9 } as const;

// Stagger step. 35ms is deliberately short: long enough that the eye reads
// the list as arriving in order (top item first), short enough that a
// 12-item grid is fully settled in under half a second. A cap stops a long
// list from making its last rows feel broken.
const STEP = 0.035;
const MAX_DELAY = 0.28;

export function Reveal({
  index = 0,
  children,
  className,
  style,
}: {
  index?: number;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  // Honouring prefers-reduced-motion in JS as well as CSS: the CSS block in
  // globals.css cannot reach the motion library's inline transforms.
  const reduce = useReducedMotion();
  if (reduce) {
    return (
      <div className={className} style={style}>
        {children}
      </div>
    );
  }
  return (
    <motion.div
      className={className}
      style={style}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...SPRING, delay: Math.min(index * STEP, MAX_DELAY) }}
    >
      {children}
    </motion.div>
  );
}

// A section (a whole group on Discover/Activity) arrives as one unit, with
// its own cards staggering inside it. Sections use a plain fade-up rather
// than a stagger of their own, so the screen does not read as a cascade of
// cascades.
export function RevealSection({
  index = 0,
  children,
  className,
  style,
}: {
  index?: number;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  const reduce = useReducedMotion();
  if (reduce) {
    return (
      <div className={className} style={style}>
        {children}
      </div>
    );
  }
  return (
    <motion.div
      className={className}
      style={style}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...SPRING, delay: Math.min(index * 0.06, 0.24) }}
    >
      {children}
    </motion.div>
  );
}
