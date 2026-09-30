"use client";

// [Design language 2026-09-29, §8, §11] The trade rail: tinted icon tiles
// with the trade's name under each (Swiggy/Zepto category lanes, Urban
// Company service tiles). Tapping a tile filters Discover IN PLACE (it sets
// the skills filter — the same URL filter as FE2's Skills section, so the
// flat list, facet counts, "Save this search" and "See all" all keep
// working); tapping it again clears it. The last tile, "All", opens every
// category of GET /v1/taxonomy/tree as a grid in a sheet. Airbnb retired
// mood categories because they did no work (Skift, 2025); every tile here
// is a real filter named the way people say it ("Electricians").
//
// Phone (critique W1): one compact lane — 52px tiles, a one-line label —
// so the first card still shows above the fold at 360×740. Desktop: 64px
// tiles, labels up to two lines.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { motion, useReducedMotion } from "motion/react";
import { Check, ChevronLeft, ChevronRight, LayoutGrid, X } from "lucide-react";
import type { TaxonomyTree } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "@/app/hooks/useResource";
import { categoryVisual, orderedRail, type RailTrade } from "./trades";

function sameSet(a: readonly string[], b: readonly string[]) {
  return a.length === b.length && a.every((x) => b.includes(x));
}

export default function TradeRail({
  skills,
  onSkills,
  viewerCategories,
}: {
  skills: readonly string[];
  onSkills: (next: string[]) => void;
  /** The viewer's own work categories (rows API); their trades come first. */
  viewerCategories?: readonly string[];
}) {
  const { t } = useTranslation(["explore"]);
  const sdk = useSdk();
  const reduce = useReducedMotion();
  const tree = useResource<TaxonomyTree | null>(() => sdk.taxonomy.tree(), [sdk], { fallback: null });
  const [allOpen, setAllOpen] = useState(false);
  const categories = tree.data?.categories ?? [];
  // Desktop: ‹ › page the lane (a mouse has no sideways swipe).
  const lane = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ start: true, end: false });
  useEffect(() => {
    const el = lane.current;
    if (!el) return;
    el.scrollLeft = 0;
    const update = () => setEdges({ start: el.scrollLeft <= 4, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 4 });
    update();
    el.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);
  const page = (dir: 1 | -1) => lane.current?.scrollBy({ left: dir * lane.current.clientWidth * 0.8, behavior: reduce ? "auto" : "smooth" });

  const targetSkills = (target: string): string[] | null => {
    if (!target.startsWith("cat:")) return [target];
    const cat = categories.find((c) => c.slug === target.slice(4));
    return cat ? (cat.children ?? []).map((c) => c.slug) : null;
  };

  const pick = (list: string[] | null) => {
    if (!list || list.length === 0) return;
    onSkills(sameSet(skills, list) ? [] : list);
  };

  const tile = (key: string, label: string, Icon: RailTrade["icon"], family: string, list: string[] | null) => {
    const on = !!list && skills.length > 0 && sameSet(skills, list);
    return (
      <motion.button
        key={key}
        type="button"
        className="vy-trade"
        aria-pressed={on}
        onClick={() => pick(list)}
        whileTap={reduce ? undefined : { scale: 0.92 }}
        transition={{ type: "spring", stiffness: 500, damping: 26 }}
      >
        <span className={`vy-trade-tile vy-trade-lg vy-trade-${family}`} aria-hidden="true">
          <Icon size={26} strokeWidth={1.8} />
          {on && (
            <span className="vy-trade-check">
              <Check size={12} strokeWidth={3} />
            </span>
          )}
        </span>
        <span className="vy-trade-label">{label}</span>
      </motion.button>
    );
  };

  return (
    <>
      <div className="vy-trades-wrap">
      <button type="button" className="vy-row2-arrow vy-trades-arrow vy-trades-prev" aria-label={t("explore:rows.prev")} hidden={edges.start} onClick={() => page(-1)}>
        <ChevronLeft size={18} strokeWidth={2.25} aria-hidden="true" />
      </button>
      <div ref={lane} className="vy-trades" role="group" aria-label={t("explore:trades.label")}>
        <button type="button" className="vy-trade" onClick={() => categories.length > 0 && setAllOpen(true)} aria-haspopup="dialog">
          <span className="vy-trade-tile vy-trade-lg vy-trade-all" aria-hidden="true">
            <LayoutGrid size={24} strokeWidth={1.8} />
          </span>
          <span className="vy-trade-label">{t("explore:trades.all")}</span>
        </button>
        {orderedRail(viewerCategories).map((r) => tile(r.key, t(`explore:trades.${r.key}`), r.icon, r.family, targetSkills(r.target)))}
      </div>
      <button type="button" className="vy-row2-arrow vy-trades-arrow vy-trades-next" aria-label={t("explore:rows.next")} hidden={edges.end} onClick={() => page(1)}>
        <ChevronRight size={18} strokeWidth={2.25} aria-hidden="true" />
      </button>
      </div>

      {allOpen && (
        <AllTrades
          onClose={() => setAllOpen(false)}
          categories={categories}
          skills={skills}
          onPick={(list) => {
            pick(list);
            setAllOpen(false);
          }}
        />
      )}
    </>
  );
}

function AllTrades({
  categories,
  skills,
  onPick,
  onClose,
}: {
  categories: TaxonomyTree["categories"];
  skills: readonly string[];
  onPick: (list: string[]) => void;
  onClose: () => void;
}) {
  const { t } = useTranslation(["explore"]);
  const reduce = useReducedMotion();
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => box.current?.focus(), []);
  return (
    <>
      <div className="vy-sheet-scrim" onClick={onClose} aria-hidden="true" />
      <motion.div
        ref={box}
        tabIndex={-1}
        className="vy-sheet vy-sheet-center"
        role="dialog"
        aria-modal="true"
        aria-labelledby="vy-alltrades-title"
        initial={reduce ? false : { y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 380, damping: 36 }}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
      >
        <div className="vy-sheet-head2">
          <div>
            <h2 id="vy-alltrades-title">{t("explore:trades.allTitle")}</h2>
            <p className="vy-muted">{t("explore:trades.allHint")}</p>
          </div>
          <button type="button" className="vy-iconbtn" onClick={onClose} aria-label={t("explore:filters.close")}>
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        <div className="vy-sheet-body">
          <div className="vy-alltrades">
            {categories.map((c) => {
              const v = categoryVisual(c.slug);
              const I = v.icon;
              const list = (c.children ?? []).map((x) => x.slug);
              const on = skills.length > 0 && sameSet(skills, list);
              return (
                <button key={c.slug} type="button" className="vy-trade vy-trade-grid" aria-pressed={on} onClick={() => onPick(list)}>
                  <span className={`vy-trade-tile vy-trade-lg vy-trade-${v.family}`} aria-hidden="true">
                    <I size={26} strokeWidth={1.8} />
                  </span>
                  <span className="vy-trade-label">{c.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </motion.div>
    </>
  );
}
