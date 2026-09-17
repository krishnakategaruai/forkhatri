"use client";

/**
 * Gesture-friendly sheet: a bottom sheet with a drag handle on phones, a
 * floating panel under the header on wider screens. Modal dialog semantics,
 * focus kept inside while open, Escape and backdrop close, focus returns to
 * the control that opened it.
 */
import { AnimatePresence, motion, useDragControls } from "motion/react";
import { useEffect, useId, useRef, type ReactNode } from "react";
import { useMediaQuery } from "@/lib/hooks";
import { CloseIcon } from "./ui";

type SheetProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  closeLabel: string;
  children: ReactNode;
};

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select,textarea,[tabindex]:not([tabindex="-1"])';

export default function Sheet({ open, onClose, title, closeLabel, children }: SheetProps) {
  const wide = useMediaQuery("(min-width: 720px)");
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const dragControls = useDragControls();

  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    const frame = requestAnimationFrame(() => {
      const panel = panelRef.current;
      const first = panel?.querySelector<HTMLElement>("[data-autofocus]") ?? panel;
      first?.focus({ preventScroll: true });
    });
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const items = [...panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener("keydown", onKey);
      opener?.focus?.({ preventScroll: true });
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            key="backdrop"
            className="sheet-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            key="panel"
            ref={panelRef}
            className="sheet"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            tabIndex={-1}
            initial={wide ? { opacity: 0, y: -8, scale: 0.98 } : { y: "100%" }}
            animate={wide ? { opacity: 1, y: 0, scale: 1 } : { y: 0 }}
            exit={wide ? { opacity: 0, y: -8, scale: 0.98 } : { y: "100%" }}
            transition={wide ? { duration: 0.18, ease: [0.2, 0.8, 0.2, 1] } : { type: "spring", stiffness: 420, damping: 40, mass: 0.9 }}
            drag={wide ? false : "y"}
            dragControls={dragControls}
            dragListener={false}
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={{ top: 0, bottom: 0.7 }}
            onDragEnd={(_, info) => {
              if (info.offset.y > 110 || info.velocity.y > 600) onClose();
            }}
          >
            <div className="sheet-head" onPointerDown={(event) => !wide && dragControls.start(event)}>
              <span className="sheet-handle" aria-hidden="true" />
              <div className="sheet-titlebar">
                <h2 id={titleId} className="sheet-title">
                  {title}
                </h2>
                <button type="button" className="icon-btn icon-btn-quiet" onClick={onClose} aria-label={closeLabel}>
                  <CloseIcon />
                </button>
              </div>
            </div>
            <div className="sheet-body">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
