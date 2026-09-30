"use client";

// [FE2 — owner direction 2026-09-29, pattern studied from ixigo's hotel
// rows] The unfiltered Discover home as themed rows: each row a titled,
// horizontally scrolling strip with "See all". Phones swipe with snap and
// the next card peeks; desktop pages the strip with ‹ › arrows (disabled
// at the ends). "See all" opens the row as ONE flat filtered list.
//
// [Design language 2026-09-29, §11–12] Each row title gets its icon
// (words + icon), in bold title type with a quiet count; cards rise in
// with a short stagger the first time a row mounts (reduced motion: none).
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { motion, useReducedMotion } from "motion/react";
import {
  Bookmark, ChevronLeft, ChevronRight, History, Sparkles, Navigation, Clock, Zap, IndianRupee, BadgeCheck, Users, BriefcaseBusiness, House, type LucideIcon,
} from "lucide-react";
import type { FeedRow } from "@/lib/sdk";
import DiscoverCard from "./DiscoverCard";
import { categoryVisual } from "./trades";
import { useHiddenPosts } from "@/app/components/reco/feedbackStore";

const ROW_ICON: Record<string, LucideIcon> = {
  for_you: Sparkles,
  near_you: Navigation,
  new_today: Clock,
  starting_now: Zap,
  pay_20k: IndianRupee,
  pay_projects: IndianRupee,
  verified: BadgeCheck,
  community: Users,
  projects: BriefcaseBusiness,
  remote: House,
  // [Recommendations 2026-09-30] rows learned from what the member did
  taste_saved: Bookmark,
};

function rowVisual(key: string): { icon: LucideIcon; family: string } {
  if (key.startsWith("category:")) {
    const v = categoryVisual(key.slice(9));
    return { icon: v.icon, family: v.family };
  }
  if (key.startsWith("taste_applied:")) return { icon: History, family: "neutral" };
  return { icon: ROW_ICON[key] ?? Sparkles, family: "neutral" };
}

function Row({ row, onSeeAll, index }: { row: FeedRow; onSeeAll: (row: FeedRow) => void; index: number }) {
  const { t } = useTranslation(["explore"]);
  const reduce = useReducedMotion();
  const strip = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ start: true, end: false });

  useEffect(() => {
    const el = strip.current;
    if (!el) return;
    const update = () => setEdges({ start: el.scrollLeft <= 4, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 4 });
    update();
    el.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);

  const page = (dir: 1 | -1) =>
    strip.current?.scrollBy({ left: dir * strip.current.clientWidth * 0.9, behavior: reduce ? "auto" : "smooth" });
  const titleId = `row-${row.key.replace(/[^a-z0-9]/gi, "-")}`;
  const v = rowVisual(row.key);
  const I = v.icon;

  return (
    <section className="vy-row2" aria-labelledby={titleId}>
      <div className="vy-row2-head">
        <h2 id={titleId} className="vy-row-title2">
          <span className={`vy-row-icon vy-trade-${v.family}`} aria-hidden="true">
            <I size={18} strokeWidth={2} />
          </span>
          <span>{row.title || t(`explore:rows.${row.title_key}`, row.title_params)}</span>
        </h2>
        <div className="vy-row2-tools">
          {row.total > row.items.length || row.items.length > 2 ? (
            <button type="button" className="vy-seeall" onClick={() => onSeeAll(row)}>
              {t("explore:rows.seeAll", { count: row.total })}
              <ChevronRight size={16} strokeWidth={2.25} aria-hidden="true" />
            </button>
          ) : null}
          <span className="vy-desktop-only vy-row2-arrows">
            <button type="button" className="vy-row2-arrow" aria-label={t("explore:rows.prev")} disabled={edges.start} onClick={() => page(-1)}>
              <ChevronLeft size={18} strokeWidth={2.25} aria-hidden="true" />
            </button>
            <button type="button" className="vy-row2-arrow" aria-label={t("explore:rows.next")} disabled={edges.end} onClick={() => page(1)}>
              <ChevronRight size={18} strokeWidth={2.25} aria-hidden="true" />
            </button>
          </span>
        </div>
      </div>
      <div ref={strip} className="vy-row2-strip" role="list">
        {row.items.map((item, i) => (
          <motion.div
            key={item.id}
            role="listitem"
            className="vy-row2-cell"
            initial={reduce || index > 2 ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 420, damping: 34, delay: Math.min(i, 6) * 0.03 }}
          >
            <DiscoverCard item={item} />
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export default function FeedRows({ rows, onSeeAll }: { rows: FeedRow[]; onSeeAll: (row: FeedRow) => void }) {
  // [Recommendations] a post hidden with "Not interested" leaves its row at
  // once (no empty slot in the strip); a row left with nothing goes too.
  const hidden = useHiddenPosts();
  const visible = rows
    .map((r) => (r.items.some((x) => hidden.has(x.id)) ? { ...r, items: r.items.filter((x) => !hidden.has(x.id)) } : r))
    .filter((r) => r.items.length > 0);
  return (
    <div className="vy-rows2">
      {visible.map((r, i) => (
        <Row key={r.key} row={r} onSeeAll={onSeeAll} index={i} />
      ))}
    </div>
  );
}
