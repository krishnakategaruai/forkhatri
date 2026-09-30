"use client";

// [Design system 2026-09-30 — owner hit a notifications panel that would not
// close] One rule for every popover, menu and dropdown in Vyapar: it closes
// on a tap or click outside it, on Escape, when the route changes, and when
// another popover opens (only one is ever open). Components keep their own
// `open` state and call this with a ref to the element that contains BOTH
// the trigger and the panel, so tapping the trigger again still toggles.
import { useEffect, useId, useRef } from "react";
import { usePathname } from "next/navigation";

const OPEN_EVENT = "vyapar:popover-open";

/** `panel`: a panel rendered elsewhere (a portal) that also counts as inside. */
export function usePopoverDismiss<T extends HTMLElement = HTMLDivElement>(
  open: boolean,
  close: () => void,
  panel?: React.RefObject<HTMLElement | null>,
) {
  const ref = useRef<T>(null);
  const id = useId();
  const pathname = usePathname();
  const closeRef = useRef(close);
  useEffect(() => {
    closeRef.current = close;
  });

  // Route change closes it.
  const openedAt = useRef<string | null>(null);
  useEffect(() => {
    if (!open) {
      openedAt.current = null;
      return;
    }
    if (openedAt.current === null) openedAt.current = pathname;
    else if (openedAt.current !== pathname) closeRef.current();
  }, [open, pathname]);

  useEffect(() => {
    if (!open) return;
    // Tell the others; close when another one opens.
    window.dispatchEvent(new CustomEvent(OPEN_EVENT, { detail: id }));
    const onOther = (e: Event) => {
      if ((e as CustomEvent<string>).detail !== id) closeRef.current();
    };
    // pointerdown covers mouse, touch and pen; capture so a stopPropagation
    // inside the page cannot keep a stale popover open.
    const onDown = (e: PointerEvent) => {
      const target = e.target as Node;
      if (ref.current?.contains(target) || panel?.current?.contains(target)) return;
      closeRef.current();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeRef.current();
    };
    window.addEventListener(OPEN_EVENT, onOther);
    document.addEventListener("pointerdown", onDown, true);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener(OPEN_EVENT, onOther);
      document.removeEventListener("pointerdown", onDown, true);
      window.removeEventListener("keydown", onKey);
    };
  }, [open, id, panel]);

  return ref;
}
