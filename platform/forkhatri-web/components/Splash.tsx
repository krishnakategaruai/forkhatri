"use client";

/**
 * First-load devotional splash (owner request, 2026-09-24): Bhagwan Kartavirya
 * Sahasrarjun, the SSK community deity, on a kumkum-maroon ground with a slowly
 * turning Sudarshan-chakra ring, the ForKhatri wordmark and a one-line blessing.
 *
 * - Once per browser session (sessionStorage `fk.splash.v1`). SPLASH_BOOT_SCRIPT in
 *   <head> hides the server-rendered splash before first paint on a repeat visit, so
 *   a reload in the same tab never shows or waits for it.
 * - It is painted from the server HTML and animated with CSS, so it appears before
 *   the page hydrates. It leaves once ~2s have passed since navigation AND the boot
 *   session check has finished (`ready`), capped so a slow service never strands it.
 *   It never delays a redirect: `ready` is true while redirecting, and navigation
 *   proceeds underneath it.
 * - Tap, click or any key skips it. prefers-reduced-motion: no rotation or scale,
 *   and a shorter stay.
 */
import Image from "next/image";
import { useEffect, useState } from "react";
import type { Lang } from "@/lib/api";
import { langFromNavigator, translator } from "@/lib/i18n";
import { SPLASH_IMAGE, SPLASH_SEEN_KEY } from "@/lib/splash-script";
import { loadStoredLang } from "@/lib/storage";

const MIN_MS = 2000;
const MIN_MS_REDUCED = 900;
const MAX_MS = 5000;
const EXIT_MS = 520;

type Stage = "showing" | "leaving" | "gone";

/**
 * Decided once per page load. Module scope, so React's development double-mount
 * (which re-runs effects) does not read back the flag this same load just wrote.
 */
let seenThisLoad: boolean | null = null;

function alreadySeen(): boolean {
  if (seenThisLoad !== null) return seenThisLoad;
  seenThisLoad = false;
  try {
    seenThisLoad = sessionStorage.getItem(SPLASH_SEEN_KEY) !== null;
    if (!seenThisLoad) sessionStorage.setItem(SPLASH_SEEN_KEY, "1");
  } catch {
    // Blocked storage: show it this once; the page works either way.
  }
  return seenThisLoad;
}

export default function Splash({ ready }: { ready: boolean }) {
  const [stage, setStage] = useState<Stage>("showing");
  const [lang, setLang] = useState<Lang | null>(null);
  const [minElapsed, setMinElapsed] = useState(false);

  // Decide once, on mount, whether this session has already seen the splash.
  useEffect(() => {
    const seen = alreadySeen();
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    // Measured from navigation start: the splash has been on screen since first paint.
    const remaining = Math.max(0, (reduced ? MIN_MS_REDUCED : MIN_MS) - performance.now());
    const timers: number[] = [];
    void Promise.resolve().then(() => {
      if (seen) {
        setStage("gone");
        return;
      }
      setLang(loadStoredLang() ?? langFromNavigator());
      timers.push(window.setTimeout(() => setMinElapsed(true), remaining));
      timers.push(window.setTimeout(() => setStage((s) => (s === "showing" ? "leaving" : s)), Math.max(remaining, MAX_MS - performance.now())));
    });
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, []);

  // Leave once the minimum stay has passed and the entrance knows what to show.
  useEffect(() => {
    if (stage !== "showing" || !minElapsed || !ready) return;
    void Promise.resolve().then(() => setStage((s) => (s === "showing" ? "leaving" : s)));
  }, [stage, minElapsed, ready]);

  // Any tap, click or key skips it.
  useEffect(() => {
    if (stage !== "showing") return;
    const skip = () => setStage((s) => (s === "showing" ? "leaving" : s));
    window.addEventListener("pointerdown", skip);
    window.addEventListener("keydown", skip);
    return () => {
      window.removeEventListener("pointerdown", skip);
      window.removeEventListener("keydown", skip);
    };
  }, [stage]);

  useEffect(() => {
    if (stage !== "leaving") return;
    const id = window.setTimeout(() => setStage("gone"), EXIT_MS);
    return () => window.clearTimeout(id);
  }, [stage]);

  if (stage === "gone") return null;
  const t = translator(lang ?? "en");

  return (
    <div className="splash" data-stage={stage} aria-busy={stage === "showing"}>
      <div className="splash-stage">
        <span className="splash-halo" aria-hidden="true" />
        <SudarshanRing />
        <span className="splash-figure" role="img" aria-label={t("deityName")}>
          <Image
            src={SPLASH_IMAGE.src}
            width={SPLASH_IMAGE.width}
            height={SPLASH_IMAGE.height}
            alt=""
            loading="eager"
            fetchPriority="high"
            unoptimized
            draggable={false}
          />
        </span>
      </div>
      <p className="splash-wordmark" aria-hidden="true">
        For<b>Khatri</b>
      </p>
      <p className="splash-blessing" lang={lang ?? undefined} data-ready={lang !== null}>
        {lang ? t("splashBlessing") : " "}
      </p>
      <span className="sr-only">{t("splashSkip")}</span>
    </div>
  );
}

/** Thin turmeric-gold line art of the Sudarshan chakra: rim, serrated edge, spokes, lotus hub. */
function SudarshanRing() {
  const teeth = 48;
  const spokes = 24;
  const serration = Array.from({ length: teeth }, (_, i) => {
    const a0 = (i / teeth) * Math.PI * 2;
    const a1 = ((i + 0.5) / teeth) * Math.PI * 2;
    const a2 = ((i + 1) / teeth) * Math.PI * 2;
    const p = (r: number, a: number) => `${(100 + r * Math.cos(a)).toFixed(2)} ${(100 + r * Math.sin(a)).toFixed(2)}`;
    return `${i === 0 ? "M" : "L"}${p(92, a0)} L${p(98, a1)} L${p(92, a2)}`;
  }).join(" ");
  return (
    <svg className="splash-ring" viewBox="0 0 200 200" aria-hidden="true" focusable="false">
      <g fill="none" stroke="currentColor" strokeLinejoin="round">
        <path d={`${serration} Z`} strokeWidth="0.45" />
        <circle cx="100" cy="100" r="88" strokeWidth="0.6" />
        <circle cx="100" cy="100" r="84.5" strokeWidth="0.3" strokeDasharray="0.6 2.2" />
        <circle cx="100" cy="100" r="62" strokeWidth="0.35" />
        {Array.from({ length: spokes }, (_, i) => {
          const a = (i / spokes) * 360;
          return <path key={i} d="M100 38 L100 16" strokeWidth={i % 2 ? 0.25 : 0.45} transform={`rotate(${a} 100 100)`} />;
        })}
        {Array.from({ length: 12 }, (_, i) => (
          <path key={`petal-${i}`} d="M100 100 Q106 84 100 70 Q94 84 100 100 Z" strokeWidth="0.3" transform={`rotate(${i * 30} 100 100)`} />
        ))}
      </g>
    </svg>
  );
}
