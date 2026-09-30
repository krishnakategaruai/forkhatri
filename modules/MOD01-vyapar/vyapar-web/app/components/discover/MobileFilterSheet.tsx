"use client";

// [FE2 — research §6, owner review 2026-09-29] The filters sheet: the SAME
// sections as FE2's FilterPanel. Nothing applies until the sticky
// "Show N results" — N and every option's count come from the results
// endpoint for the draft filters (fetched a moment after each change), so
// the person knows what a tap gives before leaving. Escape or the scrim
// closes without applying.
//
// [Design language 2026-09-29, §11] Now the ONLY home of the full filters
// on every width (the permanent desktop sidebar is gone — critique W4):
// a bottom sheet rising from the thumb on phones, a right-side drawer
// sliding from the pointer's side on desktop (≥900px), spring 380/36.
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { useTranslation } from "react-i18next";
import { X } from "lucide-react";
import type { FeedFacets, FeedFilterValues } from "@/lib/sdk";
import FilterPanel from "./FilterPanel";
import { EMPTY_FILTERS } from "./feedFilters";

function useDesktop() {
  const [desktop, setDesktop] = useState(() => typeof window !== "undefined" && window.matchMedia("(min-width: 900px)").matches);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 900px)");
    const on = () => setDesktop(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return desktop;
}

export default function MobileFilterSheet({
  value,
  onApply,
  onClose,
  preview,
}: {
  value: FeedFilterValues;
  onApply: (next: FeedFilterValues) => void;
  onClose: () => void;
  /** Total and facet counts for the draft filters. */
  preview: (draft: FeedFilterValues) => Promise<{ total: number; facets: FeedFacets }>;
}) {
  const { t } = useTranslation(["explore"]);
  const reduce = useReducedMotion();
  const desktop = useDesktop();
  const [draft, setDraft] = useState<FeedFilterValues>(value);
  const [result, setResult] = useState<{ total: number; facets: FeedFacets } | null>(null);
  const key = JSON.stringify(draft);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => box.current?.focus(), []);

  useEffect(() => {
    let live = true;
    const timer = setTimeout(() => {
      preview(draft)
        .then((r) => live && setResult(r))
        .catch(() => live && setResult(null));
    }, 250);
    return () => {
      live = false;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  const from = desktop ? { x: 60, opacity: 0 } : { y: 60, opacity: 0 };

  return (
    <>
      <div className="vy-sheet-scrim" onClick={onClose} aria-hidden="true" />
      <motion.div
        ref={box}
        tabIndex={-1}
        className="vy-sheet vy-sheet-drawer"
        role="dialog"
        aria-modal="true"
        aria-label={t("explore:filters.title")}
        initial={reduce ? false : from}
        animate={{ x: 0, y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 380, damping: 36 }}
      >
        <button type="button" className="vy-iconbtn vy-sheet-close" onClick={onClose} aria-label={t("explore:filters.close")}>
          <X size={20} aria-hidden="true" />
        </button>
        <div className="vy-sheet-body">
          <FilterPanel value={draft} onChange={setDraft} facets={result?.facets ?? null} />
        </div>
        <div className="vy-sheet-foot">
          <button type="button" className="vy-btn vy-btn-ghost" onClick={() => setDraft({ ...EMPTY_FILTERS, q: draft.q, sort: draft.sort })}>
            {t("explore:filters.clearAll")}
          </button>
          <button type="button" className="vy-btn vy-btn-primary" onClick={() => onApply(draft)}>
            {result === null ? t("explore:filters.showResults") : t("explore:filters.showN", { count: result.total })}
          </button>
        </div>
      </motion.div>
    </>
  );
}
