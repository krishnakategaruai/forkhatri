"use client";

// [Product-owner standing i18n rule, 2026-09-15] "Add a language switcher
// (English / हिन्दी / తెలుగు) reachable without a sign-in form; it sets the
// member's language preference." Placed top-LEFT (the member pill already
// owns top-right) so the two fixed-position controls never collide —
// exactly the header-overlap class of bug the coordinator's browser check
// found once already; this component is deliberately positioned to not
// repeat it.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "motion/react";
import { SUPPORTED_LANGUAGES, type Language } from "@/lib/i18n/config";
import { setPreferredLanguage } from "@/lib/i18n/provider";

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation("common");
  const [open, setOpen] = useState(false);

  function choose(lang: Language) {
    void i18n.changeLanguage(lang);
    setPreferredLanguage(lang);
    setOpen(false);
  }

  return (
    <div style={{ position: "fixed", top: 14, left: 14, zIndex: 60 }}>
      <button
        className="vy-btn vy-btn-secondary"
        style={{ fontSize: 13, padding: "8px 14px" }}
        onClick={() => setOpen((v) => !v)}
        aria-label={t("language.change")}
      >
        {t(`language.${i18n.language}` as "language.en")}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 32 }}
            className="vy-card"
            style={{ position: "absolute", top: 44, left: 0, width: 140, padding: 6 }}
          >
            <div className="vy-stack" style={{ gap: 2 }}>
              {SUPPORTED_LANGUAGES.map((lang) => (
                <button
                  key={lang}
                  className="vy-btn vy-btn-ghost"
                  style={{
                    justifyContent: "flex-start",
                    background: lang === i18n.language ? "var(--accent-soft)" : "transparent",
                    color: lang === i18n.language ? "var(--accent-strong)" : "var(--text-primary)",
                  }}
                  onClick={() => choose(lang)}
                >
                  {t(`language.${lang}` as "language.en")}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
