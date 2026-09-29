// [FE1 — 2026-09-28] Translated labels for the structured-field enums, used
// by the composer, its live preview, the opportunity detail facts and the
// applicants board, so every surface names a value the same way.
import type { StructuredFields } from "@/lib/sdk";
import { formatDateIN, formatRupeeRange, formatRupees } from "@/lib/money";

export type T = (key: string, options?: Record<string, unknown>) => string;

export function experienceLabel(t: T, months: number | null | undefined): string | null {
  if (months === null || months === undefined) return null;
  if (months === 0) return t("hiring:options.experience.freshersWelcome");
  if (months < 12) return t("hiring:options.experience.months", { count: months });
  return t("hiring:options.experience.years", { count: Math.round(months / 12) });
}

/** Pay line built from typed fields, in the viewer's language (mirrors the server's compensation_label). */
export function payLine(t: T, type: string, s: Partial<StructuredFields> | null | undefined, lang: string): string | null {
  if (!s) return null;
  if (type === "employment") {
    const range = formatRupeeRange(s.salary_min_paise, s.salary_max_paise, lang);
    if (!range && s.incentive_type !== "incentive_only") return null;
    const base = s.incentive_type === "incentive_only" ? t("hiring:preview.incentiveOnly") : t("hiring:preview.perMonth", { range });
    if (s.incentive_type === "fixed_plus_incentive") {
      return s.incentive_max_paise
        ? `${base} ${t("hiring:preview.plusIncentivesUpTo", { amount: formatRupees(s.incentive_max_paise, lang) })}`
        : `${base} ${t("hiring:preview.plusIncentives")}`;
    }
    return base;
  }
  if (type === "freelance") {
    if (s.budget_type === "hourly" || s.hourly_rate_min_paise != null || s.hourly_rate_max_paise != null) {
      const range = formatRupeeRange(s.hourly_rate_min_paise, s.hourly_rate_max_paise, lang);
      return range ? t("hiring:preview.perHour", { range }) : null;
    }
    const range = formatRupeeRange(s.budget_min_paise, s.budget_max_paise, lang);
    return range ? t("hiring:preview.fixedPrice", { range }) : null;
  }
  if (type === "local_service") {
    return s.budget_paise != null ? t("hiring:preview.budget", { amount: formatRupees(s.budget_paise, lang) }) : null;
  }
  return null;
}

export interface Fact {
  key: string;
  label: string;
  value: string;
  /** Long text that should span the whole facts grid. */
  wide?: boolean;
}

/** Structured fields as labelled facts, in the order an applicant scans them. */
export function structuredFacts(t: T, type: string, s: Partial<StructuredFields> | null | undefined, lang: string): Fact[] {
  if (!s) return [];
  const out: Fact[] = [];
  const push = (key: string, label: string, value: string | null | undefined, wide = false) => {
    if (value) out.push({ key, label, value, wide });
  };
  if (type === "employment") {
    push("shift", t("hiring:fields.shift"), s.shift ? t(`hiring:options.shift.${s.shift}`) : null);
    push("openings", t("hiring:fields.openings"), s.openings ? t("hiring:preview.openings", { count: s.openings }) : null);
    push(
      "experience",
      t("hiring:fields.experience"),
      s.experience_min_months ? t("hiring:options.experience.atLeast", { value: experienceLabel(t, s.experience_min_months) }) : experienceLabel(t, s.experience_min_months),
    );
    push("qualification", t("hiring:fields.qualification"), s.min_qualification ? t(`hiring:options.qualification.${s.min_qualification}`) : null);
    push("english", t("hiring:fields.english"), s.english_level ? t(`hiring:options.english.${s.english_level}`) : null);
    push(
      "assets",
      t("hiring:fields.assets"),
      s.requires_assets && s.requires_assets.length ? s.requires_assets.map((a) => t(`hiring:options.asset.${a}`, { defaultValue: a })).join(", ") : null,
    );
    push("timings", t("hiring:fields.jobTimings"), s.job_timings, true);
    push("interview", t("hiring:fields.interview"), s.interview_details, true);
  } else if (type === "freelance") {
    push("budgetType", t("hiring:fields.budgetType"), s.budget_type ? t(`hiring:options.budgetType.${s.budget_type}`) : null);
    push("duration", t("hiring:fields.duration"), s.duration ? t(`hiring:options.duration.${s.duration}`) : null);
    push("level", t("hiring:fields.experienceLevel"), s.experience_level ? t(`hiring:options.experienceLevel.${s.experience_level}`) : null);
  } else if (type === "local_service") {
    push("when", t("hiring:fields.when"), s.urgency ? t(`hiring:options.urgency.${s.urgency}`) : null);
    push("date", t("hiring:fields.preferredDate"), s.preferred_date ? formatDateIN(s.preferred_date, lang) : null);
  }
  return out;
}
