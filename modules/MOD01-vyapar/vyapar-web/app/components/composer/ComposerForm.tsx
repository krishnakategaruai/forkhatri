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

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { TaxonomyTree } from "@/lib/sdk";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import SkillPicker from "@/app/components/taxonomy/SkillPicker";
import { FieldSelect, MultiFieldSelect } from "@/app/components/ui/FieldSelect";
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
import { FieldBlock, FieldGroup, MoneyInput, MoneyRange, OptionChips, Segmented, readbackRange } from "./fields";
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

// [FE1 — 2026-09-30, owner: "never ask what we know"] Shown only while the
// area is empty (the saved locality prefills it otherwise). The browser gives
// coordinates; turning them into a colony name needs a reverse-geocoding
// service, configured as NEXT_PUBLIC_REVERSE_GEOCODE_URL_TEMPLATE with
// {lat}, {lon} and {lang} (see .env.example). Unset = the button is hidden,
// never a guess. The response's first "area"-like field is used.
const REVERSE_GEOCODE_TEMPLATE = process.env.NEXT_PUBLIC_REVERSE_GEOCODE_URL_TEMPLATE ?? "";

function UseMyLocation({ onPlace }: { onPlace: (place: string) => void }) {
  const { t, i18n } = useTranslation("hiring");
  const [state, setState] = useState<"idle" | "busy" | "failed">("idle");
  if (!REVERSE_GEOCODE_TEMPLATE || typeof navigator === "undefined" || !("geolocation" in navigator)) return null;
  function locate() {
    setState("busy");
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const url = REVERSE_GEOCODE_TEMPLATE.replace("{lat}", String(coords.latitude)).replace("{lon}", String(coords.longitude)).replace("{lang}", i18n.language);
          const body = (await (await fetch(url)).json()) as { address?: Record<string, string>; display_name?: string };
          const a = body.address ?? {};
          const place = [a.suburb ?? a.neighbourhood ?? a.quarter, a.city ?? a.town ?? a.village].filter(Boolean).join(", ") || body.display_name || "";
          if (!place) throw new Error("no place");
          onPlace(place);
          setState("idle");
        } catch {
          setState("failed");
        }
      },
      () => setState("failed"),
      { timeout: 10000, maximumAge: 600000 },
    );
  }
  return (
    <div className="vy-row" style={{ gap: 8, flexWrap: "wrap" }}>
      <button type="button" className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start" }} disabled={state === "busy"} onClick={locate}>
        {state === "busy" ? t("location.finding") : t("location.useCurrent")}
      </button>
      {state === "failed" && <span className="vy-field-hint">{t("location.failed")}</span>}
    </div>
  );
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
          <div className="vy-stack" style={{ gap: 6 }}>
            <input
              id="vy-location"
              className="vy-input"
              value={d.location}
              onChange={(e) => set({ location: e.target.value })}
              placeholder={t(d.type === "employment" ? "hiring:placeholders.exactArea" : "hiring:placeholders.location")}
              aria-invalid={!!errors.location || undefined}
            />
            {!d.location.trim() && <UseMyLocation onPlace={(place) => set({ location: place })} />}
          </div>
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
      case "openings": {
        const isOther = d.openings !== null && !(OPENINGS as readonly number[]).includes(d.openings);
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <FieldSelect
              options={[...OPENINGS.map((n) => ({ value: n, label: String(n) })), { value: -1, label: t("hiring:fields.openingsOther") }]}
              value={isOther ? -1 : d.openings}
              onChange={(v) => set({ openings: v === -1 ? d.openings ?? 1 : v })}
              placeholder={t("hiring:select.any")}
              ariaLabel={t("hiring:fields.openings")}
            />
            {isOther && (
              <input
                className="vy-input vy-num"
                style={{ maxWidth: 140 }}
                inputMode="numeric"
                aria-label={t("hiring:fields.openingsOther")}
                placeholder={t("hiring:fields.openingsOther")}
                value={d.openings !== null ? String(d.openings) : ""}
                onChange={(e) => {
                  const n = Number(e.target.value.replace(/[^\d]/g, ""));
                  set({ openings: n > 0 ? Math.min(n, 1000) : null });
                }}
              />
            )}
          </div>
        );
      }
      case "shift":
        return (
          <FieldSelect
            options={SHIFTS.map((v) => ({ value: v, label: t(`hiring:options.shift.${v}`) }))}
            value={d.shift}
            onChange={(v) => set({ shift: v })}
            placeholder={t("hiring:select.any")}
            ariaLabel={t("hiring:fields.shift")}
          />
        );
      case "job_timings":
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <input className="vy-input" value={d.jobTimings} maxLength={200} onChange={(e) => set({ jobTimings: e.target.value })} placeholder={t("hiring:placeholders.jobTimings")} />
            <FieldSelect
              options={TIMING_PRESETS.map((p) => ({ value: p, label: t(`hiring:presets.timings.${p}`) }))}
              value={TIMING_PRESETS.find((p) => t(`hiring:presets.timings.${p}`) === d.jobTimings) ?? null}
              onChange={(p) => set({ jobTimings: p ? t(`hiring:presets.timings.${p}`) : "" })}
              placeholder={t("hiring:fields.commonHours")}
              ariaLabel={t("hiring:fields.commonHours")}
            />
          </div>
        );
      case "experience":
        return (
          <FieldSelect
            options={EXPERIENCE_MONTHS.map((v) => ({
              value: v,
              label: v === 0 ? t("hiring:options.experience.freshersWelcome") : t("hiring:options.experience.atLeast", { value: experienceLabel(t, v) }),
            }))}
            value={d.experienceMonths as (typeof EXPERIENCE_MONTHS)[number] | null}
            onChange={(v) => set({ experienceMonths: v })}
            placeholder={t("hiring:select.any")}
            ariaLabel={t("hiring:fields.experience")}
          />
        );
      case "min_qualification":
        return (
          <FieldSelect
            options={QUALIFICATIONS.map((v) => ({ value: v, label: t(`hiring:options.qualification.${v}`) }))}
            value={d.qualification}
            onChange={(v) => set({ qualification: v })}
            placeholder={t("hiring:select.any")}
            ariaLabel={t("hiring:fields.qualification")}
          />
        );
      case "english_level":
        return (
          <FieldSelect
            options={ENGLISH_LEVELS.map((v) => ({ value: v, label: t(`hiring:options.english.${v}`) }))}
            value={d.english}
            onChange={(v) => set({ english: v })}
            placeholder={t("hiring:select.any")}
            ariaLabel={t("hiring:fields.english")}
          />
        );
      case "requires_assets":
        return (
          <MultiFieldSelect
            options={ASSETS.map((v) => ({ value: v, label: t(`hiring:options.asset.${v}`) }))}
            value={d.assets}
            onChange={(assets) => set({ assets })}
            placeholder={t("hiring:select.none")}
            selectedCountLabel={(count) => t("hiring:select.selectedCount", { count })}
            ariaLabel={t("hiring:fields.assets")}
          />
        );
      case "interview_details":
        return (
          <div className="vy-stack" style={{ gap: 8 }}>
            <FieldSelect
              options={INTERVIEW_PRESETS.map((p) => ({ value: p, label: t(`hiring:presets.interviewShort.${p}`) }))}
              value={INTERVIEW_PRESETS.find((p) => t(`hiring:presets.interview.${p}`) === d.interview) ?? null}
              onChange={(p) => set({ interview: p ? t(`hiring:presets.interview.${p}`) : "" })}
              placeholder={t("hiring:select.any")}
              ariaLabel={t("hiring:fields.interview")}
            />
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
        return (
          <FieldSelect
            options={DURATIONS.map((v) => ({ value: v, label: t(`hiring:options.duration.${v}`) }))}
            value={d.duration}
            onChange={(v) => set({ duration: v })}
            placeholder={t("hiring:select.any")}
            ariaLabel={t("hiring:fields.duration")}
          />
        );
      case "experience_level":
        return (
          <FieldSelect
            options={EXPERIENCE_LEVELS.map((v) => ({ value: v, label: t(`hiring:options.experienceLevel.${v}`) }))}
            value={d.experienceLevel}
            onChange={(v) => set({ experienceLevel: v })}
            placeholder={t("hiring:select.any")}
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
          <FieldSelect
            options={URGENCIES.map((v) => ({ value: v, label: t(`hiring:options.urgency.${v}`) }))}
            value={d.urgency}
            onChange={(v) => set({ urgency: v, preferredDate: v === "today" ? isoInDays(0) : d.preferredDate })}
            placeholder={t("hiring:select.any")}
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

// ======================================================================
// [FE1 — 2026-09-29, owner: "that is too worst" on a 14-field, one-scroll
// job form] The fields every type shows up front — enough to publish — are
// LAYOUT minus whatever a group below claims. Everything a group claims is
// tucked behind one tappable row (FieldGroup), open by default only when
// the AI draft filled or flagged something inside it, or (for an existing
// draft being edited) when a field in it already has a value.
// ======================================================================
interface ComposerGroup {
  id: string;
  titleKey: string;
  fields: FieldCode[];
  /** Employment only: fold the "calls before you accept" switch in here too. */
  includesPrecall?: boolean;
}

const GROUPS: Record<"employment" | "freelance" | "local_service" | "other", ComposerGroup[]> = {
  employment: [
    { id: "whenHowMany", titleKey: "hiring:composer.groupWhenHowMany", fields: ["incentive_type", "openings", "shift", "job_timings"] },
    { id: "whoYouNeed", titleKey: "hiring:composer.groupWhoYouNeed", fields: ["experience", "min_qualification", "english_level", "requires_assets"] },
    { id: "interviewContact", titleKey: "hiring:composer.groupInterviewContact", fields: ["interview_details"], includesPrecall: true },
  ],
  freelance: [{ id: "projectDetails", titleKey: "hiring:composer.groupProjectDetails", fields: ["duration", "experience_level", "screening_questions"] }],
  local_service: [{ id: "whenLocal", titleKey: "hiring:composer.groupWhen", fields: ["urgency", "preferred_date"] }],
  other: [],
};

/** The fields a post of this type cannot be published without — mirrors validate() in draft.ts. */
function isRequired(code: FieldCode, type: PostKind): boolean {
  if (code === "title") return true;
  if (code === "location") return type === "employment" || type === "local_service";
  if (code === "salary") return type === "employment";
  if (code === "budget") return type === "freelance";
  return false;
}

function fieldHasValue(d: ComposerDraft, code: FieldCode): boolean {
  switch (code) {
    case "incentive_type":
      return d.incentiveType !== "none";
    case "openings":
      return d.openings !== null;
    case "shift":
      return d.shift !== null;
    case "job_timings":
      return !!d.jobTimings.trim();
    case "experience":
      return d.experienceMonths !== null;
    case "min_qualification":
      return d.qualification !== null;
    case "english_level":
      return d.english !== null;
    case "requires_assets":
      return d.assets.length > 0;
    case "interview_details":
      return !!d.interview.trim();
    case "duration":
      return d.duration !== null;
    case "experience_level":
      return d.experienceLevel !== null;
    case "screening_questions":
      return d.questions.some((q) => q.trim());
    case "urgency":
      return d.urgency !== null;
    case "preferred_date":
      return !!d.preferredDate;
    default:
      return false;
  }
}

function trunc(s: string, n: number): string {
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

/** The closed-row summary — only the parts that are actually set, joined with " · ". */
function summarizeGroup(g: ComposerGroup, d: ComposerDraft, t: (k: string, opts?: Record<string, unknown>) => string, lang: string): string | undefined {
  const parts: string[] = [];
  for (const code of g.fields) {
    switch (code) {
      case "incentive_type":
        if (d.incentiveType !== "none") parts.push(t(`hiring:options.incentive.${d.incentiveType}`));
        break;
      case "openings":
        if (d.openings !== null) parts.push(t("hiring:preview.openings", { count: d.openings }));
        break;
      case "shift":
        if (d.shift !== null) parts.push(t(`hiring:options.shift.${d.shift}`));
        break;
      case "job_timings":
        if (d.jobTimings.trim()) parts.push(trunc(d.jobTimings.trim(), 18));
        break;
      case "experience":
        if (d.experienceMonths !== null)
          parts.push(d.experienceMonths === 0 ? t("hiring:options.experience.freshersWelcome") : t("hiring:options.experience.atLeast", { value: experienceLabel(t, d.experienceMonths) }));
        break;
      case "min_qualification":
        if (d.qualification !== null) parts.push(t(`hiring:options.qualification.${d.qualification}`));
        break;
      case "english_level":
        if (d.english !== null) parts.push(t(`hiring:options.english.${d.english}`));
        break;
      case "requires_assets":
        if (d.assets.length > 0) parts.push(t("hiring:select.selectedCount", { count: d.assets.length }));
        break;
      case "interview_details":
        if (d.interview.trim()) {
          const preset = INTERVIEW_PRESETS.find((p) => t(`hiring:presets.interview.${p}`) === d.interview);
          parts.push(preset ? t(`hiring:presets.interviewShort.${preset}`) : trunc(d.interview.trim(), 24));
        }
        break;
      case "duration":
        if (d.duration !== null) parts.push(t(`hiring:options.duration.${d.duration}`));
        break;
      case "experience_level":
        if (d.experienceLevel !== null) parts.push(t(`hiring:options.experienceLevel.${d.experienceLevel}`));
        break;
      case "screening_questions":
        if (d.questions.some((q) => q.trim())) parts.push(t("hiring:fields.questions"));
        break;
      case "urgency":
        if (d.urgency !== null) parts.push(t(`hiring:options.urgency.${d.urgency}`));
        break;
      case "preferred_date":
        if (d.preferredDate) parts.push(new Date(d.preferredDate).toLocaleDateString(lang, { day: "numeric", month: "short" }));
        break;
    }
  }
  if (g.includesPrecall && d.allowPrecall) parts.push(t("hiring:composer.callsOn"));
  return parts.length ? parts.join(" · ") : undefined;
}

export default function ComposerForm(props: ComposerFormProps) {
  const { draft, onChange, flagged, onLooksRight, errors } = props;
  const { t, i18n } = useTranslation(["hiring", "opportunities"]);
  const { renderControl } = useComposerControls(props);
  const layoutKey = draft.type === "employment" || draft.type === "freelance" || draft.type === "local_service" ? draft.type : "other";
  const otherOpen = OTHER_KINDS.includes(draft.type);
  const groups = GROUPS[layoutKey];
  const groupedCodes = new Set(groups.flatMap((g) => g.fields));
  const coreItems = LAYOUT[layoutKey].filter((item) => !groupedCodes.has(item.code));

  // Only explicit taps are stored; whether a group starts open is computed
  // fresh every render from the draft/flags below, so a group the AI draft
  // fills or flags (drafting is async and can land after the form already
  // rendered) opens itself without needing an effect — right up until the
  // poster taps it themselves, which always wins from then on.
  const [manualOpen, setManualOpen] = useState<Record<string, boolean>>({});
  function isGroupOpen(g: ComposerGroup): boolean {
    if (g.id in manualOpen) return manualOpen[g.id];
    return g.fields.some((f) => flagged.has(f) || fieldHasValue(draft, f)) || !!(g.includesPrecall && draft.allowPrecall);
  }

  function renderPrecall() {
    // [Critique L1, owner-approved] Apna's "Call HR" / WorkIndia's "Click to
    // call HR", off by default; the poster's call hours and daily limit
    // (contact preferences) apply to every caller.
    return (
      <FieldBlock code="allow_precall" label={t("hiring:precall.label")}>
        <button type="button" role="switch" aria-checked={draft.allowPrecall} className="vy-switch" onClick={() => onChange({ allowPrecall: !draft.allowPrecall })}>
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
    );
  }

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

      {coreItems.map(({ code, hintKey }) => (
        <FieldBlock
          key={code}
          code={code}
          label={fieldLabel(t, code, draft.type)}
          required={isRequired(code, draft.type)}
          flagged={flagged.has(code)}
          onLooksRight={() => onLooksRight(code)}
          error={errors[code] ?? null}
          hint={hintKey ? t(hintKey) : undefined}
        >
          {renderControl(code)}
        </FieldBlock>
      ))}

      {groups.map((g) => {
        const items = LAYOUT[layoutKey].filter((item) => g.fields.includes(item.code));
        return (
          <FieldGroup
            key={g.id}
            id={`vy-group-${g.id}`}
            title={`${t(g.titleKey)} · ${t("hiring:fields.optional")}`}
            summary={summarizeGroup(g, draft, t, i18n.language)}
            open={isGroupOpen(g)}
            onToggle={() => setManualOpen((s) => ({ ...s, [g.id]: !isGroupOpen(g) }))}
          >
            {items.map(({ code, hintKey }) => (
              <FieldBlock
                key={code}
                code={code}
                label={fieldLabel(t, code, draft.type)}
                flagged={flagged.has(code)}
                onLooksRight={() => onLooksRight(code)}
                error={errors[code] ?? null}
                hint={hintKey ? t(hintKey) : undefined}
              >
                {renderControl(code)}
              </FieldBlock>
            ))}
            {g.includesPrecall && renderPrecall()}
          </FieldGroup>
        );
      })}

      {draft.type === "local_service" && renderPrecall()}

      {layoutKey === "other" && (
        <FieldBlock code="compensation" label={t("hiring:fields.pay")}>
          <input className="vy-input" value={draft.compensation} onChange={(e) => onChange({ compensation: e.target.value })} placeholder={t("opportunities:new.compensationPlaceholder")} />
        </FieldBlock>
      )}

      <details className="vy-card vy-card-nested" style={{ padding: "14px 18px" }}>
        <summary style={{ cursor: "pointer", fontWeight: 600, color: "var(--text-secondary)" }}>{t("hiring:composer.moreOptions")}</summary>
        <div className="vy-stack" style={{ gap: 18, marginTop: 16 }}>
          {draft.type !== "local_service" && (
            <FieldBlock code="work_mode" label={t("hiring:fields.workMode")}>
              {renderControl("work_mode")}
            </FieldBlock>
          )}
          <FieldBlock code="deadline" label={t("hiring:fields.deadline")}>
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
