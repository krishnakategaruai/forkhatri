"use client";

// [Recommendations 2026-09-30] The card's "…" menu. It replaces the footer's
// old info button, so the card face keeps exactly one small control:
//   Why this?        the reasons, shown in place on the card
//   More like this   one tap, a toast
//   Not interested   the five-reason sheet
// The panel is portalled to <body> with fixed coordinates (a Discover row
// scrolls sideways, which would clip an absolutely placed menu), and closes
// by the shared rule (usePopoverDismiss) plus on any scroll.
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import { Info, MoreHorizontal, ThumbsDown, ThumbsUp } from "lucide-react";
import type { NotInterestedReason } from "@/lib/sdk";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";
import NotInterestedSheet from "./NotInterestedSheet";
import { usePostFeedback } from "./usePostFeedback";

const MENU_W = 232;

export default function CardMenu({
  postId,
  title,
  whyOpen,
  onWhy,
}: {
  postId: string;
  title: string;
  /** Present when the card has reasons to show. */
  whyOpen?: boolean;
  onWhy?: () => void;
}) {
  const { t } = useTranslation(["explore", "common"]);
  const [open, setOpen] = useState(false);
  const [sheet, setSheet] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  const panel = useRef<HTMLDivElement>(null);
  const anchor = usePopoverDismiss<HTMLSpanElement>(open, () => setOpen(false), panel);
  const { moreLikeThis, notInterested } = usePostFeedback();

  useLayoutEffect(() => {
    if (!open || !anchor.current) return;
    const r = anchor.current.getBoundingClientRect();
    const h = panel.current?.offsetHeight ?? 160;
    const below = r.bottom + 6 + h < window.innerHeight - 8;
    setPos({
      top: below ? r.bottom + 6 : Math.max(8, r.top - 6 - h),
      left: Math.min(Math.max(8, r.right - MENU_W), window.innerWidth - MENU_W - 8),
    });
  }, [open, anchor]);

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    window.addEventListener("scroll", close, { capture: true, passive: true });
    window.addEventListener("resize", close);
    return () => {
      window.removeEventListener("scroll", close, { capture: true });
      window.removeEventListener("resize", close);
    };
  }, [open]);

  // Every tap inside the card's link must stay out of the link.
  const stop = (e: React.SyntheticEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const item = (icon: React.ReactNode, label: string, onClick: () => void) => (
    <button
      type="button"
      role="menuitem"
      className="vy-reco-menu-item"
      onClick={(e) => {
        stop(e);
        setOpen(false);
        onClick();
      }}
    >
      {icon}
      <span>{label}</span>
    </button>
  );

  return (
    <span ref={anchor} className="vy-reco-anchor">
      <button
        type="button"
        className="vy-ocard-why"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t("explore:reco.menuLabel", { title })}
        title={t("common:action.moreOptions")}
        onClick={(e) => {
          stop(e);
          setOpen((v) => !v);
        }}
      >
        <MoreHorizontal size={18} strokeWidth={2.25} aria-hidden="true" />
      </button>
      {open &&
        createPortal(
          <div
            ref={panel}
            className="vy-reco-menu"
            role="menu"
            aria-label={t("common:action.moreOptions")}
            style={{ top: pos?.top ?? -9999, left: pos?.left ?? -9999, width: MENU_W }}
            onClick={stop}
          >
            {onWhy &&
              item(<Info size={18} strokeWidth={2} aria-hidden="true" />, whyOpen ? t("explore:reco.hideWhy") : t("explore:card.why"), onWhy)}
            {item(<ThumbsUp size={18} strokeWidth={2} aria-hidden="true" />, t("explore:reco.moreLikeThis"), () => void moreLikeThis(postId))}
            {item(<ThumbsDown size={18} strokeWidth={2} aria-hidden="true" />, t("common:action.notInterested"), () => setSheet(true))}
          </div>,
          document.body,
        )}
      {sheet && (
        // React events bubble out of a portal to its React parents: keep
        // taps inside the sheet away from the card's link.
        <span onClick={(e) => e.stopPropagation()} style={{ display: "contents" }}>
        <NotInterestedSheet
          onClose={() => setSheet(false)}
          onPick={(reason: NotInterestedReason) => {
            setSheet(false);
            void notInterested(postId, reason);
          }}
        />
        </span>
      )}
    </span>
  );
}
