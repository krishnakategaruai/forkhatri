"use client";

// ======================================================================
// [FE1 — 2026-09-28] "Check & publish" — the suggestions step.
//
// Apna's nudge ("relax criteria or make the job more attractive", +23 %
// leads when acted on) moved to publish time, where it costs the poster one
// tap instead of an edit two days later (research §1). The rule-based
// suggestions (getOpportunitySuggestions) and the AI posting tips
// (getPostingTips) arrive as one merged, de-duplicated list of "Get more
// responses" cards; each card carries its change as chips or a single
// button, applied in place — no dialog. Tips that need real text (a
// salary, an area) offer "Add it", which returns to that field.
// Presentational: fixes and the draft come in, changes go out.
// ======================================================================

import { useTranslation } from "react-i18next";
import { DURATIONS, OPENINGS, SHIFTS, URGENCIES, isoInDays, type ComposerDraft, type Fix, type FixKey, FIX_FIELD, type FieldCode } from "./draft";
import { INTERVIEW_PRESETS, QUESTION_PRESETS, TIMING_PRESETS } from "./ComposerForm";

export interface ReviewStepProps {
  draft: ComposerDraft;
  fixes: Fix[];
  loadingFixes: boolean;
  applying: FixKey | null;
  onApply: (key: FixKey, patch: Partial<ComposerDraft>) => void;
  onEdit: (field: FieldCode) => void;
}

export default function ReviewStep({ draft, fixes, loadingFixes, applying, onApply, onEdit }: ReviewStepProps) {
  const { t } = useTranslation("hiring");

  function actions(key: FixKey): React.ReactNode {
    const one = (label: string, patch: Partial<ComposerDraft>) => (
      <button type="button" className="vy-btn vy-btn-secondary" disabled={applying !== null} onClick={() => onApply(key, patch)} style={{ alignSelf: "flex-start", padding: "9px 16px", fontSize: 14 }}>
        {label}
      </button>
    );
    const chips = (items: { label: string; patch: Partial<ComposerDraft> }[]) => (
      <div className="vy-options">
        {items.map((it) => (
          <button key={it.label} type="button" className="vy-chip" disabled={applying !== null} onClick={() => onApply(key, it.patch)}>
            {it.label}
          </button>
        ))}
      </div>
    );
    switch (key) {
      case "qualification_12th":
        return one(t("tips.accept12th"), { qualification: "12th" });
      case "english_basic":
        return one(t("tips.basicEnglish"), { english: "basic" });
      case "experience_1y":
        return chips([
          { label: t("tips.accept1Year"), patch: { experienceMonths: 12 } },
          { label: t("options.experience.freshersWelcome"), patch: { experienceMonths: 0 } },
        ]);
      case "add_shift":
        return chips(SHIFTS.map((s) => ({ label: t(`options.shift.${s}`), patch: { shift: s } })));
      case "add_openings":
        return chips(OPENINGS.map((n) => ({ label: String(n), patch: { openings: n } })));
      case "add_job_timings":
        return chips(TIMING_PRESETS.map((p) => ({ label: t(`presets.timings.${p}`), patch: { jobTimings: t(`presets.timings.${p}`) } })));
      case "add_interview":
        return chips(INTERVIEW_PRESETS.map((p) => ({ label: t(`presets.interviewShort.${p}`), patch: { interview: t(`presets.interview.${p}`) } })));
      case "add_incentives":
        return one(t("tips.addIncentives"), { incentiveType: "fixed_plus_incentive" });
      case "add_duration":
        return chips(DURATIONS.map((v) => ({ label: t(`options.duration.${v}`), patch: { duration: v } })));
      case "add_question":
        return chips(
          QUESTION_PRESETS.map((p) => ({ label: t(`presets.questions.${p}`), patch: { questions: [...draft.questions.filter(Boolean), t(`presets.questions.${p}`)].slice(0, 3) } })),
        );
      case "experience_level_intermediate":
        return one(t("tips.intermediateOk"), { experienceLevel: "intermediate" });
      case "add_deadline":
        return chips([7, 14, 30].map((n) => ({ label: t("options.deadlineIn", { count: n }), patch: { deadline: isoInDays(n) } })));
      case "add_preferred_date":
        return chips([
          { label: t("options.urgency.today"), patch: { preferredDate: isoInDays(0), urgency: "today" } },
          { label: t("tips.tomorrow"), patch: { preferredDate: isoInDays(1) } },
          { label: t("tips.inDays", { count: 3 }), patch: { preferredDate: isoInDays(3) } },
        ]);
      case "add_urgency":
        return chips(URGENCIES.map((v) => ({ label: t(`options.urgency.${v}`), patch: { urgency: v } })));
      case "allow_remote":
        return one(t("tips.allowRemote"), { workMode: "both" });
      case "fewer_skills":
        return one(t("tips.keepFirst5"), { skills: draft.skills.slice(0, 5) });
      default:
        return (
          <button type="button" className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", paddingLeft: 0 }} onClick={() => onEdit(FIX_FIELD[key])}>
            {key === "fix_title" || key === "expand_description" ? t("tips.editIt") : t("tips.addIt")} →
          </button>
        );
    }
  }

  return (
    <section className="vy-stack" style={{ gap: 12 }} aria-labelledby="vy-tips-title">
      <div className="vy-stack" style={{ gap: 4 }}>
        <h2 id="vy-tips-title" className="vy-card-title">{t("tips.title")}</h2>
        <p style={{ fontSize: 14 }}>{t("tips.subtitle")}</p>
      </div>
      {loadingFixes && fixes.length === 0 ? (
        <div className="vy-tips" aria-busy="true">
          {[0, 1].map((i) => (
            <div key={i} className="vy-skeleton" style={{ height: 118, borderRadius: 16 }} />
          ))}
        </div>
      ) : fixes.length === 0 ? (
        <div className="vy-tip">
          <span className="vy-tip-impact">{t("tips.allGood")}</span>
          <p>{t("tips.allGoodBody")}</p>
        </div>
      ) : (
        <div className="vy-tips">
          {fixes.map((f) => (
            <div key={f.key} className={`vy-tip${applying === f.key ? " vy-tip-done" : ""}`}>
              <span className="vy-tip-impact">{t(`tips.impact.${f.impact}`)}</span>
              <p>{f.text}</p>
              {actions(f.key)}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
