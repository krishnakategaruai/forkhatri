"use client";

import { useEffect, useState } from "react";

/* The loading moment is held for at least a second (owner, 2026-09-25: "I
 * want it to stay for 1 sec"). Without it, a fast answer made the
 * Seeta–Rama loader flash for a few frames, which reads as a glitch rather
 * than as a moment. A page shows <SacredLoader /> while its data is loading
 * OR while this hold is still on. */
export function useLoaderHold(ms = 1000): boolean {
  const [holding, setHolding] = useState(true);
  useEffect(() => {
    const timer = window.setTimeout(() => setHolding(false), ms);
    return () => window.clearTimeout(timer);
  }, [ms]);
  return holding;
}
