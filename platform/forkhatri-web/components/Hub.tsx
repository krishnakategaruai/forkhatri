"use client";

/**
 * Signed-in hub (TR21), minimalist and single-glance (DESIGN-NOTES.md):
 *   devotional emblem + greeting → inline ask input → "Open now" rows → compact "Coming to ForKhatri" tiles.
 * Every module is visible on the first phone screen without scrolling.
 *
 * The ask input works in place, with no dialog: as the member types, matching rows are
 * highlighted and move to the top, the rest dim, and chips appear under the input.
 * On phones, if the on-screen keyboard (visualViewport) would cover the result, the
 * greeting row collapses so the result stays directly under the input. The header never moves.
 */
import { motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Lang, Member, ModuleEntry } from "@/lib/api";
import { relativeTime, type Translate } from "@/lib/i18n";
import { parseIntent } from "@/lib/intent";
import IntentField, { SUGGESTIONS } from "./CommandOrb";
import DevotionalPortrait from "./DevotionalPortrait";
import { ArrowIcon, LockIcon, Sigil } from "./ui";

type HubProps = {
  t: Translate;
  lang: Lang;
  member: Member;
  modules: ModuleEntry[];
  stale: boolean;
  onEnter: (module: ModuleEntry) => void;
};

const rise = { initial: { opacity: 0, y: 6 }, animate: { opacity: 1, y: 0 } };
const reorder = { type: "spring" as const, stiffness: 520, damping: 42 };

export default function Hub({ t, lang, member, modules, stale, onEnter }: HubProps) {
  const [openedAt] = useState(() => new Date());
  const [query, setQuery] = useState("");
  const [compact, setCompact] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const hour = openedAt.getHours();
  const greetingKey = hour < 12 ? "greetMorning" : hour < 17 ? "greetAfternoon" : "greetEvening";
  const firstName = member.display_name.trim().split(/\s+/)[0] || member.display_name;

  const intent = useMemo(() => parseIntent(query), [query]);
  const active = query.trim().length > 0;
  const matchKeys = useMemo(
    () => new Set<string>(active ? (intent.module ? [intent.module] : intent.candidates) : []),
    [active, intent],
  );
  const hasMatch = matchKeys.size > 0;

  const open = modules.filter((entry) => entry.availability === "available");
  const coming = modules.filter((entry) => entry.availability !== "available");
  // Stable sort: matches first, everything else keeps its registry/recency order.
  const openOrdered = hasMatch ? [...open].sort((a, b) => Number(matchKeys.has(b.key)) - Number(matchKeys.has(a.key))) : open;
  const topMatch = stale ? null : (openOrdered.find((entry) => matchKeys.has(entry.key) && entry.entry_url) ?? null);

  // "/" focuses the input from anywhere that is not already a text field.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
      if (event.key === "/" && !typing && !document.querySelector("[role='dialog']")) {
        event.preventDefault();
        inputRef.current?.focus({ preventScroll: true });
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  // Keep the result above the phone keyboard. Collapsing the greeting (never scrolling
  // the page or moving the header) only happens when the visual viewport would cover it,
  // and it stays collapsed until the input is cleared, so rows never jump under a finger.
  useEffect(() => {
    const viewport = window.visualViewport;
    let frame = 0;
    const check = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        if (!query.trim()) {
          setCompact(false);
          return;
        }
        if (!viewport || document.activeElement !== inputRef.current) return;
        const target =
          document.querySelector<HTMLElement>(".hub .module-row.is-match") ??
          document.querySelector<HTMLElement>(".hub .understanding");
        if (target && target.getBoundingClientRect().bottom > viewport.offsetTop + viewport.height) setCompact(true);
      });
    };
    check();
    viewport?.addEventListener("resize", check);
    return () => {
      cancelAnimationFrame(frame);
      viewport?.removeEventListener("resize", check);
    };
  }, [query]);

  return (
    <main id="main" className="hub" tabIndex={-1} data-compact={compact}>
      <section className="hub-hero">
        <div className="hub-greeting-row">
          <DevotionalPortrait t={t} />
          <div className="greeting-text">
            <p className="deity-line">{t("deityName")}</p>
            <motion.h1 className="greeting" {...rise} transition={{ duration: 0.3 }}>
              {t(greetingKey, { name: firstName })}
            </motion.h1>
          </div>
        </div>
        <p className="hub-sub">{t("hubSubtitle")}</p>

        <IntentField
          t={t}
          lang={lang}
          modules={modules}
          query={query}
          onQueryChange={setQuery}
          intent={intent}
          inputRef={inputRef}
          onSubmit={() => topMatch && onEnter(topMatch)}
        />

        <div className="hero-suggestions">
          <span className="section-label">{t("intentTry")}</span>
          <div className="chip-row">
            {SUGGESTIONS.map((key) => (
              <button
                key={key}
                type="button"
                className="suggestion"
                onClick={() => {
                  setQuery(t(key));
                  inputRef.current?.focus({ preventScroll: true });
                }}
              >
                {t(key)}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="modules" aria-label={t("portalsLabel")}>
        {stale && (
          <p className="stale-notice" role="status">
            {t("cachedNotice")}
          </p>
        )}

        <h2 className="section-label">{t("sectionOpen")}</h2>
        <ul className="module-list">
          {openOrdered.map((module, index) => {
            const visited = module.last_entered_at ? t("lastVisited", { when: relativeTime(lang, module.last_entered_at) }) : null;
            const enterable = !!module.entry_url && !stale;
            const state = hasMatch ? (matchKeys.has(module.key) ? "is-match" : "is-dim") : "";
            const content = (
              <>
                <span className="module-mark">
                  <Sigil moduleKey={module.key} size={24} />
                </span>
                <span className="module-text">
                  <span className="module-name">{module.name}</span>
                  {/* Always its own line under the name, so every row lays out the same way. */}
                  {visited && (
                    <span className="module-meta">
                      <span className="status-dot" aria-hidden="true" />
                      {visited}
                    </span>
                  )}
                  <span className="module-tagline">{module.tagline}</span>
                </span>
                {enterable && (
                  <span className="module-go" aria-hidden="true">
                    <ArrowIcon size={18} />
                  </span>
                )}
              </>
            );
            return (
              <motion.li
                key={module.key}
                layout
                {...rise}
                transition={{ duration: 0.28, delay: active ? 0 : 0.04 + index * 0.04, layout: reorder }}
              >
                {enterable ? (
                  <motion.button
                    type="button"
                    className={`module-row ${state}`}
                    whileTap={{ scale: 0.985 }}
                    onClick={() => onEnter(module)}
                    aria-label={`${module.name}. ${module.tagline}${visited ? `. ${visited}` : ""}`}
                  >
                    {content}
                  </motion.button>
                ) : (
                  <div className={`module-row is-disabled ${state}`} aria-disabled="true">
                    {content}
                  </div>
                )}
              </motion.li>
            );
          })}
        </ul>

        {coming.length > 0 && (
          <motion.div className="coming" {...rise} transition={{ duration: 0.28, delay: 0.14 }}>
            <h2 id="coming-label" className="section-label">
              {t("comingTitle")}
            </h2>
            {/* A real list read by screen readers ("Vyapar, being built"); not controls, no focus stops. */}
            <ul className="coming-grid" aria-labelledby="coming-label">
              {coming.map((module) => {
                const status = module.availability === "in_development" ? t("statusInDevelopment") : t("statusPlanned");
                const state = hasMatch ? (matchKeys.has(module.key) ? "is-match" : "is-dim") : "";
                return (
                  <li key={module.key} className={`coming-tile ${state}`} data-availability={module.availability}>
                    <span className="coming-mark" aria-hidden="true">
                      <Sigil moduleKey={module.key} size={18} />
                    </span>
                    <span className="coming-text">
                      <span className="coming-name">{module.name}</span>
                      <span className="sr-only">, </span>
                      <span className="coming-status">{status}</span>
                    </span>
                  </li>
                );
              })}
            </ul>
          </motion.div>
        )}

        <p className="trust-line">
          <LockIcon size={14} /> {t("trustLine")}
        </p>
      </section>
    </main>
  );
}

export function HubSkeleton({ label }: { label: string }) {
  return (
    <main id="main" className="hub" aria-busy="true" aria-label={label}>
      <section className="hub-hero">
        <span className="skeleton sk-line sk-title" />
        <span className="skeleton sk-field" />
      </section>
      <section className="modules">
        <span className="skeleton sk-line sk-label" />
        <div className="sk-list">
          <span className="skeleton sk-row" />
          <span className="skeleton sk-row" />
        </div>
        <span className="skeleton sk-line sk-label" />
        <div className="coming-grid">
          {[0, 1, 2, 3].map((index) => (
            <span key={index} className="skeleton sk-tile" />
          ))}
        </div>
      </section>
    </main>
  );
}

export function EnteringOverlay({ t, module }: { t: Translate; module: ModuleEntry }) {
  return (
    <div className="entering" role="status" aria-live="polite">
      <div className="entering-core">
        <span className="entering-mark">
          <Sigil moduleKey={module.key} size={36} />
        </span>
        <p className="entering-name">{t("entering", { module: module.name })}</p>
        <span className="entering-line" aria-hidden="true" />
      </div>
    </div>
  );
}
