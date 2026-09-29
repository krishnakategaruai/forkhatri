"use client";

// [FE1 — 2026-09-28] A sheet for an action taken in place (apply, compare):
// a bottom sheet on a phone, a centred panel on desktop. A solid scrim (no
// blur, no glass), Escape and the scrim close it, focus moves into it on
// open and returns to the opener on close.
import { useEffect, useRef, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

export default function Sheet({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  const { t } = useTranslation("common");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
      opener?.focus?.();
    };
  }, [onClose]);

  return (
    <div className="vy-hsheet-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div ref={ref} className={`vy-hsheet${wide ? " vy-hsheet-wide" : ""}`} role="dialog" aria-modal="true" aria-label={title} tabIndex={-1}>
        <div className="vy-hsheet-head">
          <h2 className="vy-card-title" style={{ fontSize: 20 }}>{title}</h2>
          <button type="button" className="vy-hsheet-close" onClick={onClose} aria-label={t("action.close")}>
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
