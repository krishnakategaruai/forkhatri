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
import Screen from "@/app/components/Screen";
import SkillPicker from "@/app/components/taxonomy/SkillPicker";
import { useTaxonomyAliases, useTaxonomyTree } from "@/app/hooks/hiring";

const HELP_OPTION_IDS = ["find_customers", "find_work", "hire", "partners"];
const LANGUAGE_IDS: Language[] = ["en", "hi", "te"];
const WORK_MODES = ["on_site", "remote", "both"] as const;

const TOTAL_VISIBLE_STEPS = 5;

export default function FirstRunPage() {
  const { t, i18n } = useTranslation(["firstRun", "common", "discover"]);
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [displayName, setDisplayName] = useState("");
  const [language, setLanguage] = useState<Language>("en");
  const [locality, setLocality] = useState("");
  const [radiusKm, setRadiusKm] = useState(10);
  const [workMode, setWorkMode] = useState<"on_site" | "remote" | "both">("both");
  // [Original-Vyapar upgrade, 2026-09-17] FR44's own "capture capabilities
  // via structured choices plus free text" criterion — genuinely missing
  // before this change. `capabilityOptions` is the real, shared taxonomy
  // capability list (same one every listing already picks from, not a
  // second first-run-only list); `capabilities` is the structured
  // multi-select, `capabilitiesOther` is the free-text half.
  // [Original-Vyapar upgrade, 2026-09-17, product-owner-reaffirmed] two
  // sub-phases within this ONE first-run step (never a 6th required
  // screen — FR44's "<= 5 screens" limit is unchanged): phase "categories"
  // (real taxonomy categories, searchable, tap cards with a one-line
  // description) then phase "skills" (real capability suggestions SCOPED
  // to whichever categories were just picked, plus a search box to add
  // anything not suggested). Solves the same problem WorkIndia's
  // screenshots show — guided, scoped capability capture instead of a
  // blank textbox — as an original Vyapar screen: this app's own chip/
  // card primitives, near-monochrome palette, no photos/gradients.
  const tree = useTaxonomyTree();
  const aliases = useTaxonomyAliases();
  const [capabilities, setCapabilities] = useState<string[]>([]);
  const [capabilitiesOther, setCapabilitiesOther] = useState("");
  const [help, setHelp] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get<{
      step: number; display_name: string; language: string; locality: string | null;
      radius_km: number; work_mode: string | null; capabilities: string[]; capabilities_other: string | null;
      help_with: string[];
    }>("/v1/first-run/state").then((s) => {
      setStep(Math.min(s.step, 4));
      setDisplayName(s.display_name);
      setLanguage((s.language as Language) ?? "en");
      setLocality(s.locality ?? "");
      setRadiusKm(s.radius_km ?? 10);
      setWorkMode((s.work_mode as typeof workMode) ?? "both");
      setCapabilities(s.capabilities ?? []);
      setCapabilitiesOther(s.capabilities_other ?? "");
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
    // [IMP39 — desktop layout] `vy-firstrun` widens the focused column on
    // desktop (inputs keep a readable measure, primary buttons stop being
    // 880px bars) and turns the category cards and the help options into
    // multi-column grids. No effect below 900px.
    <Screen className="vy-shell-center vy-firstrun">
      {/* [Original-Vyapar upgrade — step-progress indicator, own visual
          language: quiet accent-filled segments, never a literal copy of
          any reference app's stepper/rocket-icon chrome] */}
      <div className="vy-row" aria-label={t("firstRun:progress.label", { step: step + 1, total: TOTAL_VISIBLE_STEPS })} style={{ gap: 4 }}>
        {Array.from({ length: TOTAL_VISIBLE_STEPS }, (_, i) => (
          <div
            key={i}
            style={{
              height: 4,
              flex: 1,
              borderRadius: 2,
              background: i <= step ? "var(--accent)" : "var(--surface-overlay)",
            }}
          />
        ))}
      </div>
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
                    background: language === id ? "var(--selected-solid-bg)" : "var(--surface-overlay)",
                    color: language === id ? "var(--selected-solid-fg)" : "var(--text-primary)",
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
            {/* [FR44 gap closed] radius and work mode existed on the member
                row since the very first migration and were already used by
                the Businesses & Professionals filter, but first-run never
                asked for either — captured here on the same screen as
                locality, not a separate 6th step, to stay within FR44's
                own "<= 5 screens" limit. */}
            <label className="vy-label">{t("firstRun:step1.radiusLabel")}</label>
            <div className="vy-row">
              {[5, 10, 25].map((km) => (
                <button
                  key={km}
                  className="vy-chip"
                  aria-pressed={radiusKm === km}
                style={{ cursor: "pointer" }}
                  onClick={() => setRadiusKm(km)}
                >
                  {t("discover:businesses.radiusKm", { km })}
                </button>
              ))}
            </div>
            <label className="vy-label">{t("firstRun:step1.workModeLabel")}</label>
            <div className="vy-row">
              {WORK_MODES.map((m) => (
                <button
                  key={m}
                  className="vy-chip"
                  aria-pressed={workMode === m}
                style={{ cursor: "pointer" }}
                  onClick={() => setWorkMode(m)}
                >
                  {t(`discover:businesses.serviceMode${m === "on_site" ? "OnSite" : m === "remote" ? "Remote" : "Both"}` as "businesses.serviceModeBoth")}
                </button>
              ))}
            </div>
            <button
              className="vy-btn vy-btn-primary"
              disabled={!locality || saving}
              onClick={() => next(2, { locality, radius_km: radiusKm, work_mode: workMode })}
            >
              {t("common:action.continue")}
            </button>
          </motion.div>
        )}

        {/* [FE1 — 2026-09-28] One step, one picker: the real two-level
            taxonomy (GET /v1/taxonomy/tree) — category → skill/role with a
            one-line description each, drill-in on a phone and two columns
            on desktop, a search that matches both levels (and the English
            name, in Hindi or Telugu). Anything not in the tree is kept as
            free text in capabilities_other, exactly as before. Replaces
            the earlier two sub-phases that fetched first-run-only lists. */}
        {step === 2 && (
          <motion.div key="2-skills" {...fade} className="vy-stack">
            <h1>{t("firstRun:step2cap.title")}</h1>
            <p>{t("firstRun:step2cat.help")}</p>
            <SkillPicker
              tree={tree.data}
              selected={capabilities}
              onChange={setCapabilities}
              max={15}
              aliases={aliases}
              onFreeText={(text) => setCapabilitiesOther((prev) => (prev ? `${prev}, ${text}` : text))}
            />
            {capabilitiesOther && <p className="vy-muted" style={{ fontSize: 13 }}>{t("firstRun:step2cap.otherAdded", { text: capabilitiesOther })}</p>}
            <button
              className="vy-btn vy-btn-primary"
              disabled={saving || (capabilities.length === 0 && !capabilitiesOther)}
              onClick={() => next(3, { capabilities, capabilities_other: capabilitiesOther || null })}
            >
              {t("common:action.continue")}
            </button>
            <button className="vy-btn vy-btn-ghost" disabled={saving} onClick={() => next(3, {})}>
              {t("firstRun:step2cap.skip")}
            </button>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="3" {...fade} className="vy-stack">
            <h1>{t("firstRun:step2.title")}</h1>
            <p>{t("firstRun:step2.help")}</p>
            <div className="vy-stack vy-firstrun-help">
              {HELP_OPTION_IDS.map((id) => (
                <button
                  key={id}
                  className="vy-btn"
                  style={{
                    justifyContent: "flex-start",
                    background: help.includes(id) ? "var(--selected-bg)" : "var(--surface-overlay)",
                    color: help.includes(id) ? "var(--selected-fg)" : "var(--text-primary)",
                  }}
                  onClick={() => toggleHelp(id)}
                >
                  {help.includes(id) ? "✓ " : ""}
                  {t(`firstRun:step2.options.${id.replace(/_(.)/g, (_, c) => c.toUpperCase())}` as "step2.options.findCustomers")}
                </button>
              ))}
            </div>
            <button className="vy-btn vy-btn-primary" disabled={saving} onClick={() => next(4, { help_with: help })}>
              {t("common:action.continue")}
            </button>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="4" {...fade} className="vy-stack">
            <h1>{t("firstRun:step3.title", { name: displayName.split(" ")[0] || "" })}</h1>
            <p>{t("firstRun:step3.help")}</p>
            <button className="vy-btn vy-btn-primary" disabled={saving} onClick={() => next(5)}>
              {t("firstRun:step3.cta")}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </Screen>
  );
}

const fade = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -16 },
  transition: { type: "spring" as const, stiffness: 340, damping: 30 },
};
