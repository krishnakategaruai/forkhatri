"use client";

// [TR044] Progressive first-run to Discover (FR44) — five short screens,
// none of them a sign-up/login/OTP-sign-in screen (that boundary is FR50's;
// the member arrives here already authenticated by the parent platform via
// the dev identity stub). Each step POSTs immediately and is idempotent —
// refreshing mid-flow resumes from the server's own first_run_step, never
// the client's local state alone.
// [Product-owner i18n rule] Converted to useTranslation(); picking a
// language on step 0 also calls the real i18next language switch.
// [Design language 2026-09-29] The step line and bar from the account
// screens ("Step 1 of 5"), language as three equal chips, "what brings you
// here" as tappable option cards with a check, one brand button per step,
// the reason a button is disabled written under it.
// Traces to: FR44, TR044
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { useTranslation } from "react-i18next";
import { Briefcase, Check, Handshake, Search, Users, type LucideIcon } from "lucide-react";
import { api } from "@/lib/api";
import { setPreferredLanguage } from "@/lib/i18n/provider";
import type { Language } from "@/lib/i18n/config";
import Screen from "@/app/components/Screen";
import DisabledReason from "@/app/components/DisabledReason";
import SkillPicker from "@/app/components/taxonomy/SkillPicker";
import Steps from "@/app/components/account/Steps";
import LocalityField from "@/app/components/account/LocalityField";
import { useTaxonomyAliases, useTaxonomyTree } from "@/app/hooks/hiring";
import "@/app/styles/account-2026.css";
// [Voice interview 2026-09-30] first run can be answered by talking
import VoiceEntry from "@/app/components/voice/VoiceEntry";
import VoiceInterview from "@/app/components/voice/VoiceInterview";
import { toProfile } from "@/app/components/voice/drafts";

const HELP_OPTIONS: { id: string; key: string; icon: LucideIcon }[] = [
  { id: "find_customers", key: "findCustomers", icon: Users },
  { id: "find_work", key: "findWork", icon: Search },
  { id: "hire", key: "hire", icon: Briefcase },
  { id: "partners", key: "partners", icon: Handshake },
];
const LANGUAGE_IDS: Language[] = ["en", "hi", "te"];
const WORK_MODES = ["on_site", "remote", "both"] as const;

const TOTAL_VISIBLE_STEPS = 5;

export default function FirstRunPage() {
  const { t, i18n } = useTranslation(["firstRun", "common", "discover", "listings", "voice"]);
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [displayName, setDisplayName] = useState("");
  const [language, setLanguage] = useState<Language>("en");
  const [locality, setLocality] = useState("");
  const [radiusKm, setRadiusKm] = useState(10);
  const [workMode, setWorkMode] = useState<"on_site" | "remote" | "both">("both");
  // [FR44] "capture capabilities via structured choices plus free text":
  // `capabilities` is the structured multi-select from the shared taxonomy,
  // `capabilitiesOther` the free-text half.
  const tree = useTaxonomyTree();
  const aliases = useTaxonomyAliases();
  const [capabilities, setCapabilities] = useState<string[]>([]);
  const [capabilitiesOther, setCapabilitiesOther] = useState("");
  const [help, setHelp] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [talking, setTalking] = useState(false);

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

  const stepTitles = [t("firstRun:step0.title"), t("firstRun:step1.title"), t("firstRun:step2cap.title"), t("firstRun:step2.title"), t("firstRun:step3.title", { name: displayName.split(" ")[0] || "" })];

  return (
    // [IMP39 — desktop layout] `vy-firstrun` widens the focused column on
    // desktop and turns the help options into a two-column grid.
    <Screen className="vy-shell-center vy-firstrun">
      {/* [Voice interview] The same questions, asked out loud in the chosen
          language; the answers land on these steps for the member to check. */}
      {talking && (
        <VoiceInterview
          flow="profile"
          initialAnswers={displayName.trim() ? { name: displayName.trim() } : undefined}
          title={t("voice:flowTitle.profile")}
          doneLabel={t("voice:doneLabel.profile")}
          onClose={() => setTalking(false)}
          onDone={({ draft }) => {
            setTalking(false);
            const v = toProfile(draft);
            const name = v.name ?? displayName;
            if (v.name) setDisplayName(v.name);
            if (v.locality) setLocality(v.locality);
            if (v.serviceMode) setWorkMode(v.serviceMode);
            if (v.capabilities.length) setCapabilities((c) => Array.from(new Set([...c, ...v.capabilities])));
            if (v.capabilitiesOther) setCapabilitiesOther((prev) => (prev ? `${prev}, ${v.capabilitiesOther}` : (v.capabilitiesOther ?? "")));
            if (name.trim()) void next(1, { display_name: name.trim(), language });
          }}
        />
      )}
      <Steps step={step + 1} total={TOTAL_VISIBLE_STEPS} label={stepTitles[step] ?? ""} stepLabel={t("firstRun:progress.label", { step: step + 1, total: TOTAL_VISIBLE_STEPS })} />
      <AnimatePresence mode="wait">
        {step === 0 && (
          <motion.div key="0" {...fade} className="vy-acct-form">
            <div className="vy-acct-head">
              <h1>{t("firstRun:step0.title")}</h1>
            </div>
            <div className="vy-acct-field">
              <label className="vy-label" htmlFor="fr-name">{t("firstRun:step0.namePrompt")}</label>
              <input id="fr-name" className="vy-input" value={displayName} autoComplete="name" onChange={(e) => setDisplayName(e.target.value)} placeholder={t("firstRun:step0.namePlaceholder")} />
            </div>
            <div className="vy-acct-field">
              <span className="vy-label">{t("firstRun:step0.languagePrompt")}</span>
              <div className="vy-acct-fr-lang" role="group" aria-label={t("common:language.change")}>
                {LANGUAGE_IDS.map((id) => (
                  <button key={id} type="button" className="vy-chip" aria-pressed={language === id} lang={id} onClick={() => chooseLanguage(id)}>
                    {t(`common:language.${id}` as "language.en")}
                  </button>
                ))}
              </div>
            </div>
            <VoiceEntry variant="profile" onStart={() => setTalking(true)} compact />
            <div className="vy-acct-form" style={{ gap: 8 }}>
              <button className="vy-btn vy-btn-primary" aria-describedby="fr-reason-name" disabled={!displayName || saving} onClick={() => next(1, { display_name: displayName, language })}>
                {t("common:action.continue")}
              </button>
              <DisabledReason id="fr-reason-name" show={!displayName.trim() && !saving}>
                {t("listings:new.reasonName")}
              </DisabledReason>
            </div>
          </motion.div>
        )}

        {step === 1 && (
          <motion.div key="1" {...fade} className="vy-acct-form">
            <div className="vy-acct-head">
              <h1>{t("firstRun:step1.title")}</h1>
              <p>{t("firstRun:step1.help")}</p>
            </div>
            {/* [Owner, 2026-09-30] a known locality is shown filled; an unknown
                one offers "Use my current location" before typing. */}
            <LocalityField
              id="fr-locality"
              value={locality}
              onChange={setLocality}
              onCoords={(lat, lng) => setCoords({ lat, lng })}
              label={t("listings:new.localityLabel")}
              placeholder={t("firstRun:step1.placeholder")}
            />
            {/* [FR44 gap closed] radius and work mode captured on the same
                screen as locality, to stay within FR44's "<= 5 screens". */}
            <div className="vy-acct-field">
              <span className="vy-label">{t("firstRun:step1.radiusLabel")}</span>
              <div className="vy-acct-inline-choices" role="group" aria-label={t("firstRun:step1.radiusLabel")}>
                {[5, 10, 25].map((km) => (
                  <button key={km} type="button" className="vy-chip" aria-pressed={radiusKm === km} onClick={() => setRadiusKm(km)}>
                    {t("discover:businesses.radiusKm", { km })}
                  </button>
                ))}
              </div>
            </div>
            <div className="vy-acct-field">
              <span className="vy-label">{t("firstRun:step1.workModeLabel")}</span>
              <div className="vy-acct-inline-choices" role="group" aria-label={t("firstRun:step1.workModeLabel")}>
                {WORK_MODES.map((m) => (
                  <button key={m} type="button" className="vy-chip" aria-pressed={workMode === m} onClick={() => setWorkMode(m)}>
                    {t(`discover:businesses.serviceMode${m === "on_site" ? "OnSite" : m === "remote" ? "Remote" : "Both"}` as "businesses.serviceModeBoth")}
                  </button>
                ))}
              </div>
            </div>
            <div className="vy-acct-form" style={{ gap: 8 }}>
              <button className="vy-btn vy-btn-primary" aria-describedby="fr-reason-loc" disabled={!locality || saving} onClick={() => next(2, { locality, radius_km: radiusKm, work_mode: workMode, ...(coords ?? {}) })}>
                {t("common:action.continue")}
              </button>
              <DisabledReason id="fr-reason-loc" show={!locality.trim() && !saving}>
                {t("listings:new.reasonLocality")}
              </DisabledReason>
            </div>
          </motion.div>
        )}

        {/* [FE1 — 2026-09-28] One step, one picker: the real two-level
            taxonomy. This step's whole job is picking skills, so the grid
            stays open (startOpen); only the posting composer's picker starts
            closed. Anything not in the tree is kept as free text. */}
        {step === 2 && (
          <motion.div key="2-skills" {...fade} className="vy-acct-form">
            <div className="vy-acct-head">
              <h1>{t("firstRun:step2cap.title")}</h1>
              <p>{t("firstRun:step2cat.help")}</p>
            </div>
            <SkillPicker
              tree={tree.data}
              selected={capabilities}
              onChange={setCapabilities}
              max={15}
              aliases={aliases}
              onFreeText={(text) => setCapabilitiesOther((prev) => (prev ? `${prev}, ${text}` : text))}
              startOpen
            />
            {capabilitiesOther && <p className="vy-acct-hint">{t("firstRun:step2cap.otherAdded", { text: capabilitiesOther })}</p>}
            <div className="vy-row" style={{ flexWrap: "wrap", gap: 10 }}>
              <button className="vy-btn vy-btn-primary" aria-describedby="fr-reason-skills" disabled={saving || (capabilities.length === 0 && !capabilitiesOther)} onClick={() => next(3, { capabilities, capabilities_other: capabilitiesOther || null })}>
                {t("common:action.continue")}
              </button>
              <button className="vy-btn vy-btn-ghost" disabled={saving} onClick={() => next(3, {})}>
                {t("firstRun:step2cap.skip")}
              </button>
            </div>
            <DisabledReason id="fr-reason-skills" show={capabilities.length === 0 && !capabilitiesOther && !saving}>
              {t("common:disabled.skills")}
            </DisabledReason>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="3" {...fade} className="vy-acct-form">
            <div className="vy-acct-head">
              <h1>{t("firstRun:step2.title")}</h1>
              <p>{t("firstRun:step2.help")}</p>
            </div>
            <div className="vy-acct-fr-help" role="group" aria-label={t("firstRun:step2.title")}>
              {HELP_OPTIONS.map((o) => {
                const on = help.includes(o.id);
                const Icon = o.icon;
                return (
                  <button key={o.id} type="button" className="vy-card vy-acct-fr-option" aria-pressed={on} onClick={() => toggleHelp(o.id)}>
                    <span className="vy-acct-tile" data-tint={on ? "brand" : undefined} aria-hidden="true">
                      <Icon size={20} strokeWidth={1.9} />
                    </span>
                    <strong>{t(`firstRun:step2.options.${o.key}` as "step2.options.findCustomers")}</strong>
                    <span className="vy-acct-fr-check" aria-hidden="true">
                      <Check size={14} strokeWidth={3} />
                    </span>
                  </button>
                );
              })}
            </div>
            <button className="vy-btn vy-btn-primary" disabled={saving} onClick={() => next(4, { help_with: help })}>
              {t("common:action.continue")}
            </button>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="4" {...fade} className="vy-acct-form">
            <div className="vy-acct-head">
              <h1>{t("firstRun:step3.title", { name: displayName.split(" ")[0] || "" })}</h1>
              <p>{t("firstRun:step3.help")}</p>
            </div>
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
