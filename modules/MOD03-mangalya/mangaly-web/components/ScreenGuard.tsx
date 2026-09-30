"use client";

/* [Owner, 2026-09-29] No screenshots anywhere in Mangalya. A web page cannot
 * stop the operating system from capturing the screen (only a native app can,
 * e.g. Android's FLAG_SECURE), so this does what a browser allows:
 *  - the Print Screen key covers the page and empties the clipboard;
 *  - while the tab is hidden (switching apps, recording pickers) the page is
 *    covered — not on a plain window blur, which would blank the app every
 *    time someone clicks the address bar;
 *  - printing (and "save as PDF") prints nothing;
 *  - photos cannot be right-clicked, dragged or long-pressed to save. */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

export default function ScreenGuard() {
  const { t } = useTranslation("common");
  const [covered, setCovered] = useState(false);

  useEffect(() => {
    let timer: number | undefined;
    const cover = () => setCovered(true);
    const uncover = () => {
      if (document.visibilityState === "visible") setCovered(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "PrintScreen") return;
      setCovered(true);
      navigator.clipboard?.writeText("").catch(() => undefined);
      window.clearTimeout(timer);
      timer = window.setTimeout(uncover, 1500);
    };
    const onContextMenu = (e: MouseEvent) => {
      if (e.target instanceof HTMLImageElement) e.preventDefault();
    };
    const onDragStart = (e: DragEvent) => {
      if (e.target instanceof HTMLImageElement) e.preventDefault();
    };
    const onVisibility = () => (document.visibilityState === "hidden" ? cover() : uncover());
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("keyup", onKey);
    document.addEventListener("contextmenu", onContextMenu);
    document.addEventListener("dragstart", onDragStart);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("keyup", onKey);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("contextmenu", onContextMenu);
      document.removeEventListener("dragstart", onDragStart);
    };
  }, []);

  if (!covered) return null;
  return (
    <div className="screen-guard" role="presentation">
      <p>{t("screenGuard.message")}</p>
    </div>
  );
}
