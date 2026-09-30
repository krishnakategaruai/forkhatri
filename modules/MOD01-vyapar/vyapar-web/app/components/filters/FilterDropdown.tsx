"use client";

// [Design system 2026-09-30 — owner: "i really hate filters section, you can
// add dropdowns or better UX… main issue in filters is throwing all the tags
// which is hard job for user to scroll"] One filter = one button in a
// horizontal bar under the search. The button shows what is chosen
// ("Plumbers", "10 km"), so no second chip row repeats it. Tapping it opens
// a compact panel with only that filter's control and Clear / Apply:
//   - desktop: a popover anchored under the button;
//   - phone (< 600px): a bottom sheet, thumb-reachable.
// The panel is portalled to <body> so a horizontally scrolling bar never
// clips it. Closing follows the shared rule (lib/usePopoverDismiss.ts).
// Presentational: the caller keeps a draft, resets it in onOpen and commits
// it in onApply.
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import { ChevronDown, X } from "lucide-react";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";

function useNarrow() {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 599px)");
    const on = () => setNarrow(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return narrow;
}

export default function FilterDropdown({
  label,
  value,
  active,
  icon,
  onOpen,
  onApply,
  onClear,
  toggle,
  width = 320,
  children,
}: {
  /** The filter's name ("Distance"): shown when nothing is chosen, and as the panel title. */
  label: string;
  /** What is chosen ("10 km"), or null. */
  value?: string | null;
  active: boolean;
  icon?: React.ReactNode;
  onOpen?: () => void;
  onApply?: () => void;
  onClear?: () => void;
  /** A plain on/off filter (e.g. Verified): no panel, the button toggles. */
  toggle?: () => void;
  width?: number;
  children?: React.ReactNode;
}) {
  const { t } = useTranslation("explore");
  const [open, setOpen] = useState(false);
  const narrow = useNarrow();
  const panel = useRef<HTMLDivElement>(null);
  const anchor = usePopoverDismiss<HTMLDivElement>(open, () => setOpen(false), panel);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);

  // Desktop: keep the popover under its button while the page scrolls.
  useLayoutEffect(() => {
    if (!open || narrow) return;
    const place = () => {
      const r = anchor.current?.getBoundingClientRect();
      if (!r) return;
      const left = Math.max(12, Math.min(r.left, window.innerWidth - width - 12));
      setPos({ top: r.bottom + 8, left });
    };
    place();
    window.addEventListener("scroll", place, true);
    window.addEventListener("resize", place);
    return () => {
      window.removeEventListener("scroll", place, true);
      window.removeEventListener("resize", place);
    };
  }, [open, narrow, width, anchor]);

  // Phone sheet: the page behind does not scroll.
  useEffect(() => {
    if (!open || !narrow) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open, narrow]);

  const shown = value ?? label;
  const body = (
    <>
      <div className="vy-fdd-body">{children}</div>
      <div className="vy-fdd-foot">
        <button
          type="button"
          className="vy-btn vy-btn-ghost"
          onClick={() => {
            onClear?.();
            setOpen(false);
          }}
        >
          {t("fbar.clear")}
        </button>
        <button
          type="button"
          className="vy-btn vy-btn-solid"
          onClick={() => {
            onApply?.();
            setOpen(false);
          }}
        >
          {t("fbar.apply")}
        </button>
      </div>
    </>
  );

  return (
    <div ref={anchor} className="vy-fdd">
      <button
        type="button"
        className="vy-chip vy-fdd-btn"
        aria-pressed={toggle ? active : undefined}
        data-active={active ? "" : undefined}
        aria-expanded={toggle ? undefined : open}
        aria-haspopup={toggle ? undefined : "dialog"}
        aria-label={value ? `${label}: ${value}` : label}
        onClick={() => {
          if (toggle) return toggle();
          if (!open) onOpen?.();
          setOpen((v) => !v);
        }}
      >
        {icon}
        <span className="vy-fdd-value">{shown}</span>
        {!toggle && <ChevronDown size={15} strokeWidth={2.25} aria-hidden="true" className="vy-fdd-chev" data-open={open ? "" : undefined} />}
      </button>

      {open &&
        !toggle &&
        typeof document !== "undefined" &&
        createPortal(
          narrow ? (
            <>
              <div className="vy-fdd-scrim" onClick={() => setOpen(false)} aria-hidden="true" />
              <div ref={panel} className="vy-fdd-sheet" role="dialog" aria-modal="true" aria-label={label}>
                <div className="vy-fdd-head">
                  <strong>{label}</strong>
                  <button type="button" className="vy-iconbtn" aria-label={t("fbar.close")} onClick={() => setOpen(false)}>
                    <X size={20} strokeWidth={2} aria-hidden="true" />
                  </button>
                </div>
                {body}
              </div>
            </>
          ) : (
            <div
              ref={panel}
              className="vy-popover vy-fdd-pop"
              role="dialog"
              aria-label={label}
              style={{ position: "fixed", top: pos?.top ?? -9999, left: pos?.left ?? 0, width }}
            >
              {body}
            </div>
          ),
          document.body,
        )}
    </div>
  );
}

/** A one-choice list inside a filter panel (radio semantics, 44px rows). */
export function ChoiceList<T extends string | number | null>({
  options,
  value,
  onChange,
  name,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  name: string;
}) {
  return (
    <div className="vy-fdd-list" role="radiogroup" aria-label={name}>
      {options.map((o) => (
        <button
          key={String(o.value)}
          type="button"
          role="radio"
          aria-checked={o.value === value}
          className="vy-menu-item"
          onClick={() => onChange(o.value)}
        >
          <span>{o.label}</span>
          <span className="vy-fdd-dot" aria-hidden="true" />
        </button>
      ))}
    </div>
  );
}
