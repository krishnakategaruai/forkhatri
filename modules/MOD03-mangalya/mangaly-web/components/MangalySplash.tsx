"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

/* The first moment of Mangalya (DEC-V1-030).
 *
 * Once per browser tab, the app opens on Seeta–Rama Kalyanam: the divine
 * wedding every South Indian family invokes on a wedding card, set on the
 * kumkum night with the turmeric thread drawing itself under the name. It is
 * the brand's one ceremonial beat, so it stays short (about two seconds),
 * yields to any tap or key, and is skipped entirely for reduced motion.
 *
 * The inline script in app/layout.tsx sets `html[data-splash="1"]` before
 * first paint when this tab has not seen it, and the stylesheet shows the
 * splash only under that attribute — so it covers the page from the first
 * frame instead of flashing the screen underneath while React hydrates.
 * This component only decides when to lift it. */

const HOLD_MS = 2100;
const FADE_MS = 520;

export default function MangalySplash() {
  const { t } = useTranslation("common");
  const [leaving, setLeaving] = useState(false);
  const [gone, setGone] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    if (root.getAttribute("data-splash") !== "1") {
      setGone(true);
      return;
    }
    try {
      sessionStorage.setItem("mangaly.splash", "1");
    } catch {
      // Storage blocked: the splash simply shows again next load.
    }
    let fadeTimer = 0;
    const lift = () => {
      setLeaving(true);
      window.clearTimeout(holdTimer);
      fadeTimer = window.setTimeout(() => {
        root.removeAttribute("data-splash");
        setGone(true);
      }, FADE_MS);
    };
    const holdTimer = window.setTimeout(lift, HOLD_MS);
    const onKey = () => lift();
    window.addEventListener("keydown", onKey, { once: true });
    return () => {
      window.clearTimeout(holdTimer);
      window.clearTimeout(fadeTimer);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  if (gone) return null;

  const skip = () => {
    setLeaving(true);
    window.setTimeout(() => {
      document.documentElement.removeAttribute("data-splash");
      setGone(true);
    }, FADE_MS);
  };

  return (
    <div
      className={`msplash${leaving ? " is-leaving" : ""}`}
      onClick={skip}
      role="presentation"
    >
      <div className="msplash__glow" aria-hidden="true" />
      {/* A kolam ring turning slowly behind the couple: dots and loops,
          drawn in turmeric at low opacity. */}
      <svg className="msplash__kolam" viewBox="0 0 400 400" aria-hidden="true">
        <g fill="none" stroke="currentColor" strokeWidth="1.2">
          <circle cx="200" cy="200" r="186" strokeDasharray="2 10" strokeLinecap="round" />
          <circle cx="200" cy="200" r="160" />
          {Array.from({ length: 16 }, (_, i) => (
            <ellipse
              key={i}
              cx="200"
              cy="200"
              rx="36"
              ry="150"
              transform={`rotate(${i * 11.25} 200 200)`}
              opacity="0.55"
            />
          ))}
        </g>
      </svg>
      <figure className="msplash__art">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/art/seeta-rama-kalyanam.webp"
          alt={t("common:splash.art")}
          width={760}
          height={912}
          fetchPriority="high"
          decoding="async"
        />
      </figure>
      <div className="msplash__words">
        <p className="msplash__name">{t("common:app.name")}</p>
        <svg className="msplash__thread" viewBox="0 0 240 24" aria-hidden="true">
          <path d="M4 6c40 16 80 16 116 16s76 0 116-16" />
          <circle cx="120" cy="21" r="4" />
        </svg>
        <p className="msplash__blessing">{t("common:splash.blessing")}</p>
      </div>
      <button type="button" className="msplash__skip" onClick={skip}>
        {t("common:splash.skip")}
      </button>
    </div>
  );
}
