"use client";

// [Product-owner standing i18n rule, 2026-09-15] English / हिन्दी / తెలుగు,
// reachable from every screen without a sign-in form; it sets the member's
// language preference.
//
// [Design language 2026-09-29, §9 — owner: "Vyapar must adapt to everyone"]
// Now the top bar's "Language and display" menu. The button shows a globe
// and the current language in its OWN script (EN · हि · తె), so a
// Hindi-only or Telugu-only reader recognises it without reading English.
// The menu adds Text size (Normal / Large / Larger — the whole UI scales,
// all type is rem) and High contrast, for older readers and bright
// sunlight; both also follow the OS settings.
import { useEffect, useState } from "react";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { Check, Globe } from "lucide-react";
import { SUPPORTED_LANGUAGES, type Language } from "@/lib/i18n/config";
import { setPreferredLanguage } from "@/lib/i18n/provider";
import { getContrast, getTextSize, setContrast, setTextSize, type TextSize } from "@/lib/display";

const SHORT: Record<string, string> = { en: "EN", hi: "हि", te: "తె" };

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation("common");
  const reduce = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [size, setSize] = useState<TextSize>("m");
  const [more, setMore] = useState(false);
  const ref = usePopoverDismiss(open, () => setOpen(false));

  useEffect(() => {
    // localStorage is read after mount (never during SSR).
    queueMicrotask(() => {
      setSize(getTextSize());
      setMore(getContrast() === "more");
    });
  }, []);

  function choose(lang: Language) {
    void i18n.changeLanguage(lang);
    setPreferredLanguage(lang);
  }

  return (
    <div ref={ref} className="vy-menu-anchor">
      <button
        type="button"
        className="vy-iconbtn vy-iconbtn-text"
        onClick={() => setOpen((v) => !v)}
        aria-label={t("display.title")}
        aria-expanded={open}
        aria-haspopup="dialog"
        title={t("display.title")}
      >
        <Globe size={20} strokeWidth={1.75} aria-hidden="true" />
        <span>{SHORT[i18n.language] ?? i18n.language.toUpperCase()}</span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={reduce ? false : { opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, y: -6, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 420, damping: 34 }}
            className="vy-popover vy-popover-end vy-display-menu"
            role="dialog"
            aria-label={t("display.title")}
          >
            <p className="vy-popover-label">{t("display.language")}</p>
            <div className="vy-stack" style={{ gap: 2 }} role="radiogroup" aria-label={t("display.language")}>
              {SUPPORTED_LANGUAGES.map((lang) => (
                <button
                  key={lang}
                  type="button"
                  role="radio"
                  aria-checked={lang === i18n.language}
                  className="vy-menu-item"
                  onClick={() => choose(lang)}
                  lang={lang}
                >
                  <span>{t(`language.${lang}` as "language.en")}</span>
                  {lang === i18n.language && <Check size={18} aria-hidden="true" />}
                </button>
              ))}
            </div>

            <p className="vy-popover-label">{t("display.textSize")}</p>
            <div className="vy-segmented" role="group" aria-label={t("display.textSize")}>
              {(["m", "l", "xl"] as const).map((s) => (
                <button
                  key={s}
                  type="button"
                  aria-pressed={size === s}
                  onClick={() => {
                    setTextSize(s);
                    setSize(s);
                  }}
                >
                  <span aria-hidden="true" className={`vy-size-glyph vy-size-${s}`}>A</span>
                  <span className="vy-visually-hidden">{t(s === "m" ? "display.sizeNormal" : s === "l" ? "display.sizeLarge" : "display.sizeLarger")}</span>
                </button>
              ))}
            </div>

            <label className="vy-display-switch">
              <span>
                <strong>{t("display.contrast")}</strong>
                <small>{t("display.contrastHint")}</small>
              </span>
              <input
                type="checkbox"
                role="switch"
                checked={more}
                onChange={(e) => {
                  setContrast(e.target.checked ? "more" : "auto");
                  setMore(e.target.checked);
                }}
              />
            </label>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
