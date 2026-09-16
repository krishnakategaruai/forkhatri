"use client";

// [TR044] Progressive first-run to Discover (FR44) — five short screens,
// none of them a sign-up/login/OTP-sign-in screen (that boundary is FR50's;
// the member arrives here already authenticated by the parent platform via
// the dev identity stub). Each step POSTs immediately and is idempotent —
// refreshing mid-flow resumes from the server's own first_run_step, never
// the client's local state alone.
// [Product-owner i18n rule] Converted to useTranslation(); picking a
// language on step 0 now also calls the real i18next language switch
// (previously it only saved the choice to the backend without changing
// what the member saw for the rest of first-run).
// Traces to: FR44, TR044
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { setPreferredLanguage } from "@/lib/i18n/provider";
import type { Language } from "@/lib/i18n/config";

const HELP_OPTION_IDS = ["find_customers", "find_work", "hire", "partners"];
const LANGUAGE_IDS: Language[] = ["en", "hi", "te"];

export default function FirstRunPage() {
  const { t, i18n } = useTranslation(["firstRun", "common"]);
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [displayName, setDisplayName] = useState("");
  const [language, setLanguage] = useState<Language>("en");
  const [locality, setLocality] = useState("");
  const [help, setHelp] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get<{ step: number; display_name: string; language: string; locality: string | null; help_with: string[] }>(
      "/v1/first-run/state"
    ).then((s) => {
      setStep(Math.min(s.step, 3));
      setDisplayName(s.display_name);
      setLanguage((s.language as Language) ?? "en");
      setLocality(s.locality ?? "");
      setHelp(s.help_with ?? []);
    });
  }, []);

  async function next(nextStep: number, extra: Record<string, unknown> = {}) {
    setSaving(true);
    try {
      await api.post("/v1/first-run/step", { step: nextStep, ...extra });
      if (nextStep >= 4) {
        router.replace("/");
      } else {
        setStep(nextStep);
      }
    } finally {
      setSaving(false);
    }
  }

  function toggleHelp(id: string) {
    setHelp((h) => (h.includes(id) ? h.filter((x) => x !== id) : [...h, id]));
  }

  function chooseLanguage(lang: Language) {
    setLanguage(lang);
    void i18n.changeLanguage(lang);
    setPreferredLanguage(lang);
  }

  return (
    <main className="vy-shell" style={{ justifyContent: "center" }}>
      <AnimatePresence mode="wait">
        {step === 0 && (
          <motion.div key="0" {...fade} className="vy-stack">
            <h1>{t("firstRun:step0.title")}</h1>
            <p>{t("firstRun:step0.namePrompt")}</p>
            <input
              className="vy-input"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder={t("firstRun:step0.namePlaceholder")}
            />
            <div className="vy-row" style={{ flexWrap: "wrap" }}>
              {LANGUAGE_IDS.map((id) => (
                <button
                  key={id}
                  className="vy-btn"
                  style={{
                    background: language === id ? "var(--accent)" : "var(--surface-overlay)",
                    color: language === id ? "var(--accent-ink)" : "var(--text-primary)",
                  }}
                  onClick={() => chooseLanguage(id)}
                >
                  {t(`common:language.${id}` as "language.en")}
                </button>
              ))}
            </div>
            <button
              className="vy-btn vy-btn-primary"
              disabled={!displayName || saving}
              onClick={() => next(1, { display_name: displayName, language })}
            >
              {t("common:action.continue")}
            </button>
          </motion.div>
        )}

        {step === 1 && (
          <motion.div key="1" {...fade} className="vy-stack">
            <h1>{t("firstRun:step1.title")}</h1>
            <p>{t("firstRun:step1.help")}</p>
            <input
              className="vy-input"
              value={locality}
              onChange={(e) => setLocality(e.target.value)}
              placeholder={t("firstRun:step1.placeholder")}
            />
            <button className="vy-btn vy-btn-primary" disabled={!locality || saving} onClick={() => next(2, { locality })}>
              {t("common:action.continue")}
            </button>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="2" {...fade} className="vy-stack">
            <h1>{t("firstRun:step2.title")}</h1>
            <p>{t("firstRun:step2.help")}</p>
            <div className="vy-stack">
              {HELP_OPTION_IDS.map((id) => (
                <button
                  key={id}
                  className="vy-btn"
                  style={{
                    justifyContent: "flex-start",
                    background: help.includes(id) ? "var(--accent-soft)" : "var(--surface-overlay)",
                    color: help.includes(id) ? "var(--accent-strong)" : "var(--text-primary)",
                  }}
                  onClick={() => toggleHelp(id)}
                >
                  {help.includes(id) ? "✓ " : ""}
                  {t(`firstRun:step2.options.${id.replace(/_(.)/g, (_, c) => c.toUpperCase())}` as "step2.options.findCustomers")}
                </button>
              ))}
            </div>
            <button className="vy-btn vy-btn-primary" disabled={saving} onClick={() => next(3, { help_with: help })}>
              {t("common:action.continue")}
            </button>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="3" {...fade} className="vy-stack">
            <h1>{t("firstRun:step3.title", { name: displayName.split(" ")[0] || "" })}</h1>
            <p>{t("firstRun:step3.help")}</p>
            <button className="vy-btn vy-btn-primary" disabled={saving} onClick={() => next(4)}>
              {t("firstRun:step3.cta")}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}

const fade = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -16 },
  transition: { type: "spring" as const, stiffness: 340, damping: 30 },
};
