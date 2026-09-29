"use client";

// ======================================================================
// [FE1 — 2026-09-28] The posting composer's form — one structured form per
// opportunity type, in the researched field order (references/2026-screen-
// research.md §1, Apna/WorkIndia for jobs, Upwork for projects):
//   Job: title → role → exact area → monthly in-hand salary min–max →
//        incentives → openings → shift + timings → experience (freshers
//        welcome) → minimum qualification → English → things needed →
//        interview → description.
//   Project: title → skills → budget (fixed or hourly, a range) → duration
//        → experience level → up to 3 screening questions → description.
//   Local service: what → where → when (urgency or a date) → budget →
//        description.
// Every choice with a closed set of answers is one tap (chips), money is a
// ₹ field that reads back in Indian format, and prose fields take voice.
// Presentational: state comes in, changes go out. `renderControl(code)`
// is also used by the missing-detail question chips, so a question is
// answered with the very same control the form shows.
// ======================================================================

import { useTranslation } from "react-i18next";
import type { TaxonomyTree } from "@/lib/sdk";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import SkillPicker from "@/app/components/taxonomy/SkillPicker";
import {
  ASSETS,
  DURATIONS,
  ENGLISH_LEVELS,
  EXPERIENCE_LEVELS,
  EXPERIENCE_MONTHS,
  INCENTIVE_TYPES,
  MAIN_KINDS,
  MAX_QUESTIONS,
  OPENINGS,
  OTHER_KINDS,
  QUALIFICATIONS,
  SHIFTS,
  URGENCIES,
  isoInDays,
  type ComposerDraft,
  type FieldCode,
  type PostKind,
} from "./draft";
import { FieldBlock, MoneyInput, MoneyRange, MultiChips, OptionChips, Segmented, readbackRange } from "./fields";
import { experienceLabel } from "./labels";
import { rupeesToPaise } from "@/lib/money";

const SALARY_PRESETS: [number, number][] = [
  [10000, 15000],
  [15000, 20000],
  [20000, 30000],
  [30000, 50000],
];
export const TIMING_PRESETS = ["a", "b", "c", "night"] as const;
export const INTERVIEW_PRESETS = ["walkIn", "callFirst", "chatFirst"] as const;
export const QUESTION_PRESETS = ["similarWork", "startWhen", "tools"] as const;

export interface ComposerFormProps {
  draft: ComposerDraft;
  onChange: (patch: Partial<ComposerDraft>) => void;
  tree: TaxonomyTree | null;
  flagged: ReadonlySet<FieldCode>;
  onLooksRight: (code: FieldCode) => void;
  errors: Partial<Record<FieldCode, string>>;
  /** slug → English name for the skill search (see useTaxonomyAliases). */
  aliases?: ReadonlyMap<string, string>;
}

export function useComposerControls({ draft, onChange, tree, errors, aliases }: Omit<ComposerFormProps, "flagged" | "onLooksRight">) {
  const { t, i18n } = useTranslation(["hiring", "opportunities"]);
  const lang = i18n.language;
  const d = draft;
  const set = onChange;
  const rupee = (n: number) => new Intl.NumberFormat(`${lang}-IN`, { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

  function renderControl(code: FieldCode): React.ReactNode {
    switch (code) {
      case "title":
        return (
          <input
            id="vy-title"
            className="vy-input"
            value={d.title}
            maxLength={200}
            onChange={(e) => set({ title: e.target.value })}
            placeholder={t(`hiring:placeholders.title.${d.type}`, { defaultValue: t("hiring:placeholders.title.other") })}
            aria-invalid={!!errors.title || undefined}
          />
        );
      case "location":
        return (
          <input
            id="vy-location"
            className="vy-input"
            value={d.location}
            onChange={(e) => set({ location: e.target.value })}
            placeholder={t(d.type === "employment" ? "hiring:placeholders.exactArea" : "hiring:placeholders.location")}
            aria-invalid={!!errors.location || undefined}
          />
        );
      case "required_capabilities":
        return <SkillPicker tree={tree} selected={d.skills} onChange={(skills) => set({ skills })} max={10} aliases={aliases} collapsible />;
      case "salary":
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <MoneyRange
              min={d.salaryMin}
              max={d.salaryMax}
              onMin={(v) => set({ salaryMin: v })}
              onMax={(v) => set({ salaryMax: v })}
              minLabel={t("hiring:fields.min")}
              maxLabel={t("hiring:fields.max")}
              invalid={!!errors.salary}
            />
            <div className="vy-options">
              {SALARY_PRESETS.map(([lo, hi]) => (
                <button
                  key={lo}
                  type="button"
                  className="vy-chip"
                  aria-pressed={rupeesToPaise(d.salaryMin) === lo * 100 && rupeesToPaise(d.salaryMax) === hi * 100}
                  onClick={() => set({ salaryMin: String(lo), salaryMax: String(hi) })}
                >
                  {rupee(lo)} – {rupee(hi)}
                </button>
              ))}
            </div>
            {readbackRange(d.salaryMin, d.salaryMax, lang) && (
              <span className="vy-readback">{t("hiring:preview.perMonth", { range: readbackRange(d.salaryMin, d.salaryMax, lang) })}</span>
            )}
          </div>
        );
      case "incentive_type":
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <OptionChips
              options={INCENTIVE_TYPES}
              value={d.incentiveType}
              allowClear={false}
              onChange={(v) => set({ incentiveType: v ?? "none" })}
              label={(v) => t(`hiring:options.incentive.${v}`)}
            />
            {d.incentiveType !== "none" && (
              <MoneyInput value={d.incentiveMax} onChange={(v) => set({ incentiveMax: v })} placeholder={t("hiring:fields.incentiveUpTo")} ariaLabel={t("hiring:fields.incentiveUpTo")} readbackSuffix={t("hiring:preview.aMonth")} />
            )}
          </div>
        );
      case "openings":
        return (
          <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
            <OptionChips options={OPENINGS} value={d.openings} onChange={(v) => set({ openings: v })} label={(v) => String(v)} ariaLabel={t("hiring:fields.openings")} />
            <input
              className="vy-input"
              style={{ width: 96 }}
              inputMode="numeric"
              aria-label={t("hiring:fields.openingsOther")}
              placeholder={t("hiring:fields.openingsOther")}
              value={d.openings !== null && !(OPENINGS as readonly number[]).includes(d.openings) ? String(d.openings) : ""}
              onChange={(e) => {
                const n = Number(e.target.value.replace(/[^\d]/g, ""));
                set({ openings: n > 0 ? Math.min(n, 1000) : null });
              }}
            />
          </div>
        );
      case "shift":
        return <OptionChips options={SHIFTS} value={d.shift} onChange={(v) => set({ shift: v })} label={(v) => t(`hiring:options.shift.${v}`)} ariaLabel={t("hiring:fields.shift")} />;
      case "job_timings":
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <input className="vy-input" value={d.jobTimings} maxLength={200} onChange={(e) => set({ jobTimings: e.target.value })} placeholder={t("hiring:placeholders.jobTimings")} />
            <div className="vy-options">
              {TIMING_PRESETS.map((p) => {
                const text = t(`hiring:presets.timings.${p}`);
                return (
                  <button key={p} type="button" className="vy-chip" aria-pressed={d.jobTimings === text} onClick={() => set({ jobTimings: text })}>
                    {text}
                  </button>
                );
              })}
            </div>
          </div>
        );
      case "experience":
        return (
          <OptionChips
            options={EXPERIENCE_MONTHS}
            value={d.experienceMonths as (typeof EXPERIENCE_MONTHS)[number] | null}
            onChange={(v) => set({ experienceMonths: v })}
            label={(v) => (v === 0 ? t("hiring:options.experience.freshersWelcome") : t("hiring:options.experience.atLeast", { value: experienceLabel(t, v) }))}
            ariaLabel={t("hiring:fields.experience")}
          />
        );
      case "min_qualification":
        return (
          <OptionChips
            options={QUALIFICATIONS}
            value={d.qualification}
            onChange={(v) => set({ qualification: v })}
            label={(v) => t(`hiring:options.qualification.${v}`)}
            ariaLabel={t("hiring:fields.qualification")}
          />
        );
      case "english_level":
        return (
          <OptionChips options={ENGLISH_LEVELS} value={d.english} onChange={(v) => set({ english: v })} label={(v) => t(`hiring:options.english.${v}`)} ariaLabel={t("hiring:fields.english")} />
        );
      case "requires_assets":
        return <MultiChips options={ASSETS} value={d.assets} onChange={(assets) => set({ assets })} label={(v) => t(`hiring:options.asset.${v}`)} ariaLabel={t("hiring:fields.assets")} />;
      case "interview_details":
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <div className="vy-options">
              {INTERVIEW_PRESETS.map((p) => {
                const text = t(`hiring:presets.interview.${p}`);
                return (
                  <button key={p} type="button" className="vy-chip" aria-pressed={d.interview === text} onClick={() => set({ interview: text })}>
                    {t(`hiring:presets.interviewShort.${p}`)}
                  </button>
                );
              })}
            </div>
            <VoiceInput fieldLabel={t("hiring:fields.interview")} onConfirm={(text) => set({ interview: appendSpoken(d.interview, text) })}>
              <textarea
                className="vy-textarea"
                rows={2}
                maxLength={500}
                value={d.interview}
                onChange={(e) => set({ interview: e.target.value })}
                placeholder={t("hiring:placeholders.interview")}
              />
            </VoiceInput>
          </div>
        );
      case "budget":
        if (d.type === "local_service") {
          return <MoneyInput value={d.localBudget} onChange={(v) => set({ localBudget: v })} placeholder={t("hiring:placeholders.localBudget")} ariaLabel={t("hiring:fields.budget")} />;
        }
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <Segmented
              options={["fixed", "hourly"] as const}
              value={d.budgetType}
              onChange={(v) => set({ budgetType: v })}
              label={(v) => t(`hiring:options.budgetType.${v}`)}
              ariaLabel={t("hiring:fields.budgetType")}
            />
            <MoneyRange
              min={d.budgetMin}
              max={d.budgetMax}
              onMin={(v) => set({ budgetMin: v })}
              onMax={(v) => set({ budgetMax: v })}
              minLabel={t("hiring:fields.min")}
              maxLabel={t("hiring:fields.max")}
              invalid={!!errors.budget}
            />
            {readbackRange(d.budgetMin, d.budgetMax, lang) && (
              <span className="vy-readback">
                {d.budgetType === "hourly"
                  ? t("hiring:preview.perHour", { range: readbackRange(d.budgetMin, d.budgetMax, lang) })
                  : t("hiring:preview.fixedPrice", { range: readbackRange(d.budgetMin, d.budgetMax, lang) })}
              </span>
            )}
          </div>
        );
      case "duration":
        return <OptionChips options={DURATIONS} value={d.duration} onChange={(v) => set({ duration: v })} label={(v) => t(`hiring:options.duration.${v}`)} ariaLabel={t("hiring:fields.duration")} />;
      case "experience_level":
        return (
          <OptionChips
            options={EXPERIENCE_LEVELS}
            value={d.experienceLevel}
            onChange={(v) => set({ experienceLevel: v })}
            label={(v) => t(`hiring:options.experienceLevel.${v}`)}
            ariaLabel={t("hiring:fields.experienceLevel")}
          />
        );
      case "screening_questions": {
        const qs = d.questions;
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            {qs.map((q, i) => (
              <div key={i} className="vy-row" style={{ alignItems: "flex-start" }}>
                <span className="vy-muted" style={{ paddingTop: 13, minWidth: 18 }}>{i + 1}.</span>
                <input
                  className="vy-input"
                  value={q}
                  maxLength={300}
                  onChange={(e) => set({ questions: qs.map((x, j) => (j === i ? e.target.value : x)) })}
                  aria-label={t("hiring:fields.questionN", { n: i + 1 })}
                />
                <button type="button" className="vy-icon-btn" aria-label={t("hiring:composer.removeQuestion", { n: i + 1 })} onClick={() => set({ questions: qs.filter((_, j) => j !== i) })}>
                  ×
                </button>
              </div>
            ))}
            {qs.length < MAX_QUESTIONS && (
              <div className="vy-options">
                {QUESTION_PRESETS.map((p) => {
                  const text = t(`hiring:presets.questions.${p}`);
                  if (qs.includes(text)) return null;
                  return (
                    <button key={p} type="button" className="vy-chip" onClick={() => set({ questions: [...qs, text] })}>
                      + {text}
                    </button>
                  );
                })}
                <button type="button" className="vy-chip" onClick={() => set({ questions: [...qs, ""] })}>
                  + {t("hiring:composer.ownQuestion")}
                </button>
              </div>
            )}
          </div>
        );
      }
      case "urgency":
        return (
          <OptionChips
            options={URGENCIES}
            value={d.urgency}
            onChange={(v) => set({ urgency: v, preferredDate: v === "today" ? isoInDays(0) : d.preferredDate })}
            label={(v) => t(`hiring:options.urgency.${v}`)}
            ariaLabel={t("hiring:fields.when")}
          />
        );
      case "preferred_date":
        return (
          <input
            type="date"
            className="vy-input"
            style={{ maxWidth: 220 }}
            min={isoInDays(0)}
            value={d.preferredDate}
            onChange={(e) => set({ preferredDate: e.target.value })}
            aria-label={t("hiring:fields.preferredDate")}
          />
        );
      case "deadline":
        return (
          <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
            {[7, 14, 30].map((n) => (
              <button key={n} type="button" className="vy-chip" aria-pressed={d.deadline === isoInDays(n)} onClick={() => set({ deadline: d.deadline === isoInDays(n) ? "" : isoInDays(n) })}>
                {t("hiring:options.deadlineIn", { count: n })}
              </button>
            ))}
            <input type="date" className="vy-input" style={{ maxWidth: 200 }} min={isoInDays(1)} value={d.deadline} onChange={(e) => set({ deadline: e.target.value })} aria-label={t("hiring:fields.deadline")} />
          </div>
        );
      case "work_mode":
        return (
          <OptionChips
            options={["on_site", "remote", "both"] as const}
            value={d.workMode || null}
            onChange={(v) => set({ workMode: v ?? "" })}
            label={(v) => t(`opportunities:workMode.${v}`)}
            ariaLabel={t("hiring:fields.workMode")}
          />
        );
      case "timing":
        return <input className="vy-input" value={d.timing} onChange={(e) => set({ timing: e.target.value })} placeholder={t("hiring:placeholders.timing")} />;
      case "description":
        return (
          <VoiceInput fieldLabel={t("hiring:fields.description")} onConfirm={(text) => set({ description: appendSpoken(d.description, text) })}>
            <textarea
              className="vy-textarea"
              rows={5}
              maxLength={4000}
              value={d.description}
              onChange={(e) => set({ description: e.target.value })}
              placeholder={t(`hiring:placeholders.description.${d.type}`, { defaultValue: t("hiring:placeholders.description.other") })}
            />
          </VoiceInput>
        );
      default:
        return null;
    }
  }

  return { renderControl };
}

/** The field label for a code, by type (what / where for a local service). */
export function fieldLabel(t: (k: string) => string, code: FieldCode, type: PostKind): string {
  if (code === "title") return t(type === "local_service" ? "hiring:fields.whatNeeded" : type === "employment" ? "hiring:fields.jobTitle" : "hiring:fields.title");
  if (code === "location") return t(type === "employment" ? "hiring:fields.exactArea" : type === "local_service" ? "hiring:fields.where" : "hiring:fields.location");
  if (code === "required_capabilities") return t(type === "employment" ? "hiring:fields.role" : "hiring:fields.skills");
  if (code === "salary") return t("hiring:fields.salary");
  if (code === "budget") return t(type === "local_service" ? "hiring:fields.budget" : "hiring:fields.budgetProject");
  const map: Partial<Record<FieldCode, string>> = {
    incentive_type: "hiring:fields.incentives",
    openings: "hiring:fields.openings",
    shift: "hiring:fields.shift",
    job_timings: "hiring:fields.jobTimings",
    experience: "hiring:fields.experience",
    min_qualification: "hiring:fields.qualification",
    english_level: "hiring:fields.english",
    requires_assets: "hiring:fields.assets",
    interview_details: "hiring:fields.interview",
    duration: "hiring:fields.duration",
    experience_level: "hiring:fields.experienceLevel",
    screening_questions: "hiring:fields.questions",
    urgency: "hiring:fields.when",
    preferred_date: "hiring:fields.preferredDate",
    deadline: "hiring:fields.deadline",
    work_mode: "hiring:fields.workMode",
    timing: "hiring:fields.timing",
    description: "hiring:fields.description",
  };
  return t(map[code] ?? "hiring:fields.description");
}

/** Which fields each type shows, in order, and which are optional. */
export const LAYOUT: Record<"employment" | "freelance" | "local_service" | "other", { code: FieldCode; optional?: boolean; hintKey?: string }[]> = {
  // Critique L6: title → exact area → salary first (the researched order);
  // the role comes after the money, and folds to chips once picked.
  employment: [
    { code: "title" },
    { code: "location", hintKey: "hiring:hints.exactArea" },
    { code: "salary", hintKey: "hiring:hints.salary" },
    { code: "incentive_type", optional: true },
    { code: "required_capabilities", optional: true, hintKey: "hiring:hints.role" },
    { code: "openings", optional: true },
    { code: "shift", optional: true },
    { code: "job_timings", optional: true },
    { code: "experience", optional: true },
    { code: "min_qualification", optional: true, hintKey: "hiring:hints.qualification" },
    { code: "english_level", optional: true },
    { code: "requires_assets", optional: true },
    { code: "interview_details", optional: true },
    { code: "description", optional: true },
  ],
  freelance: [
    { code: "title" },
    { code: "required_capabilities", hintKey: "hiring:hints.skills" },
    { code: "budget" },
    { code: "duration", optional: true },
    { code: "experience_level", optional: true },
    { code: "screening_questions", optional: true, hintKey: "hiring:hints.questions" },
    { code: "description", optional: true },
  ],
  local_service: [
    { code: "title" },
    { code: "location", hintKey: "hiring:hints.where" },
    { code: "urgency", optional: true },
    { code: "preferred_date", optional: true },
    { code: "budget", optional: true },
    { code: "description", optional: true },
  ],
  other: [
    { code: "title" },
    { code: "location", optional: true },
    { code: "timing", optional: true },
    { code: "required_capabilities", optional: true },
    { code: "description", optional: true },
  ],
};

export default function ComposerForm(props: ComposerFormProps) {
  const { draft, onChange, flagged, onLooksRight, errors } = props;
  const { t } = useTranslation(["hiring", "opportunities"]);
  const { renderControl } = useComposerControls(props);
  const layoutKey = draft.type === "employment" || draft.type === "freelance" || draft.type === "local_service" ? draft.type : "other";
  const otherOpen = OTHER_KINDS.includes(draft.type);

  return (
    <div className="vy-stack" style={{ gap: 20 }}>
      <FieldBlock code="type" label={t("hiring:fields.type")} flagged={flagged.has("type")} onLooksRight={() => onLooksRight("type")}>
        <div className="vy-options" role="group" aria-label={t("hiring:fields.type")}>
          {MAIN_KINDS.map((k) => (
            <button key={k} type="button" className="vy-chip" aria-pressed={draft.type === k} onClick={() => onChange({ type: k })}>
              {t(`hiring:kinds.${k}`)}
            </button>
          ))}
          {otherOpen ? (
            OTHER_KINDS.map((k) => (
              <button key={k} type="button" className="vy-chip" aria-pressed={draft.type === k} onClick={() => onChange({ type: k })}>
                {t(`opportunities:type.${k}`)}
              </button>
            ))
          ) : (
            <button type="button" className="vy-chip" onClick={() => onChange({ type: "partnership" })}>
              {t("hiring:kinds.more")}
            </button>
          )}
        </div>
      </FieldBlock>

      {LAYOUT[layoutKey].map(({ code, optional, hintKey }) => (
        <FieldBlock
          key={code}
          code={code}
          label={fieldLabel(t, code, draft.type)}
          optional={optional}
          flagged={flagged.has(code)}
          onLooksRight={() => onLooksRight(code)}
          error={errors[code] ?? null}
          hint={hintKey ? t(hintKey) : undefined}
        >
          {renderControl(code)}
        </FieldBlock>
      ))}

      {(draft.type === "employment" || draft.type === "local_service") && (
        // [Critique L1, owner-approved] Apna's "Call HR" / WorkIndia's
        // "Click to call HR", off by default; the poster's call hours and
        // daily limit (contact preferences) apply to every caller.
        <FieldBlock code="allow_precall" label={t("hiring:precall.label")}>
          <button
            type="button"
            role="switch"
            aria-checked={draft.allowPrecall}
            className="vy-switch"
            onClick={() => onChange({ allowPrecall: !draft.allowPrecall })}
          >
            <span className="vy-switch-track" aria-hidden="true">
              <span className="vy-switch-thumb" />
            </span>
            <span>{draft.allowPrecall ? t("hiring:precall.on") : t("hiring:precall.off")}</span>
          </button>
          {draft.allowPrecall && (
            <OptionChips
              options={["whatsapp_only", "call_and_whatsapp"] as const}
              value={draft.precallChannel}
              allowClear={false}
              onChange={(v) => onChange({ precallChannel: v ?? "whatsapp_only" })}
              label={(v) => t(`hiring:precall.channel.${v}`)}
              ariaLabel={t("hiring:precall.channelLabel")}
            />
          )}
          <span className="vy-field-hint">
            {t("hiring:precall.explain")} <a href="/profile/contact">{t("hiring:precall.setHours")}</a>
          </span>
        </FieldBlock>
      )}

      {layoutKey === "other" && (
        <FieldBlock code="compensation" label={t("hiring:fields.pay")} optional>
          <input className="vy-input" value={draft.compensation} onChange={(e) => onChange({ compensation: e.target.value })} placeholder={t("opportunities:new.compensationPlaceholder")} />
        </FieldBlock>
      )}

      <details className="vy-card vy-card-nested" style={{ padding: "14px 18px" }}>
        <summary style={{ cursor: "pointer", fontWeight: 600, color: "var(--text-secondary)" }}>{t("hiring:composer.moreOptions")}</summary>
        <div className="vy-stack" style={{ gap: 18, marginTop: 16 }}>
          {draft.type !== "local_service" && (
            <FieldBlock code="work_mode" label={t("hiring:fields.workMode")} optional>
              {renderControl("work_mode")}
            </FieldBlock>
          )}
          <FieldBlock code="deadline" label={t("hiring:fields.deadline")} optional>
            {renderControl("deadline")}
          </FieldBlock>
          <FieldBlock code="segment" label={t("hiring:fields.segment")} error={errors.type ?? null}>
            <OptionChips
              options={["community", "public"] as const}
              value={draft.segment}
              allowClear={false}
              onChange={(v) => onChange({ segment: v ?? "community" })}
              label={(v) => t(v === "community" ? "opportunities:new.segmentCommunity" : "opportunities:new.segmentPublic")}
            />
            {draft.segment === "public" && (
              <input
                className="vy-input"
                value={draft.sourceName}
                onChange={(e) => onChange({ sourceName: e.target.value })}
                placeholder={t("opportunities:new.sourceNamePlaceholder")}
                aria-label={t("opportunities:new.sourceNameLabel")}
              />
            )}
          </FieldBlock>
        </div>
      </details>
    </div>
  );
}
