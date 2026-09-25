"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

/* A horizontal row of cards with no visible scrollbar (DEC-V1-030).
 *
 * Native scrollbars under every row read as broken chrome on a desktop
 * (the owner flagged one under each Discover shelf). On touch screens the
 * peeking next card says "swipe"; with a mouse, round arrow buttons appear
 * on hover — each only while there is more to see in its direction — and a
 * press moves by most of the visible width. */
export default function ScrollRail({
  className,
  children,
}: {
  className: string;
  children: React.ReactNode;
}) {
  const { t } = useTranslation("home");
  const ref = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ prev: false, next: false });

  const measure = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    setEdges({
      prev: el.scrollLeft > 4,
      next: el.scrollLeft + el.clientWidth < el.scrollWidth - 4,
    });
  }, []);

  useEffect(() => {
    measure();
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [measure, children]);

  const step = (dir: 1 | -1) =>
    ref.current?.scrollBy({
      left: dir * Math.round(ref.current.clientWidth * 0.8),
      behavior: "smooth",
    });

  return (
    <div className="srail">
      {edges.prev && (
        <button
          type="button"
          className="mrail__nav mrail__nav--prev"
          aria-label={t("home:matches.prev")}
          onClick={() => step(-1)}
        >
          ‹
        </button>
      )}
      <div className={className} ref={ref} onScroll={measure}>
        {children}
      </div>
      {edges.next && (
        <button
          type="button"
          className="mrail__nav mrail__nav--next"
          aria-label={t("home:matches.next")}
          onClick={() => step(1)}
        >
          ›
        </button>
      )}
    </div>
  );
}
