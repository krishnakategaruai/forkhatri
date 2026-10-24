// ======================================================================
// [FE1 — 2026-09-28] The posting composer's draft model, kept free of
// React so the page, the preview and the suggestions step all read one
// shape. It owns four translations:
//   - an AI draft (draftOpportunity / readOpportunityImage) → form state,
//     with low-confidence fields flagged "please check";
//   - form state → the createOpportunity / updateOpportunity body (typed
//     `structured` fields; money in paise; free-text `compensation` is no
//     longer written for jobs and projects — the server derives it);
//   - form state → the posting-tips draft;
//   - backend-A suggestion codes + AI tip codes → one merged "fix" list,
//     each with its one-tap change.
// ======================================================================

import type {
  AiDraft,
  AiDraftInput,
  BudgetType,
  EnglishLevel,
  ExperienceLevel,
  IncentiveType,
  OpportunitySuggestion,
  OpportunityWrite,
  PostingTip,
  ProjectDuration,
  Qualification,
  ShiftKind,
  StructuredInput,
  Urgency,
} from "@/lib/sdk";
import { paiseToRupeeInput, rupeesToPaise } from "@/lib/money";

export type PostKind = "employment" | "freelance" | "local_service" | "partnership" | "training" | "community";
export const MAIN_KINDS: PostKind[] = ["employment", "freelance", "local_service"];
export const OTHER_KINDS: PostKind[] = ["partnership", "training", "community"];

export const SHIFTS: ShiftKind[] = ["day", "night", "rotational", "flexible"];
export const QUALIFICATIONS: Qualification[] = ["any", "below_10th", "10th", "12th", "iti", "diploma", "graduate", "postgraduate"];
export const ENGLISH_LEVELS: EnglishLevel[] = ["none", "basic", "good", "fluent"];
export const INCENTIVE_TYPES: IncentiveType[] = ["none", "fixed_plus_incentive", "incentive_only"];
export const ASSETS = ["two_wheeler", "driving_licence", "smartphone", "four_wheeler", "laptop", "own_tools"] as const;
export const DURATIONS: ProjectDuration[] = ["under_1_week", "1_4_weeks", "1_3_months", "3_6_months", "over_6_months", "ongoing"];
export const EXPERIENCE_LEVELS: ExperienceLevel[] = ["entry", "intermediate", "expert"];
export const URGENCIES: Urgency[] = ["today", "this_week", "flexible"];
/** Experience chips, in months: 0 = freshers welcome. */
export const EXPERIENCE_MONTHS = [0, 6, 12, 24, 60] as const;
export const OPENINGS = [1, 2, 3, 5, 10] as const;
/** The UI caps screening questions at 3 (research §1); the API allows 5. */
export const MAX_QUESTIONS = 3;

export interface ComposerDraft {
  type: PostKind;
  title: string;
  description: string;
  location: string;
  workMode: "" | "on_site" | "remote" | "both";
  skills: string[];
  segment: "community" | "public";
  sourceName: string;
  /** Free-text pay, only for partnership / training / community. */
  compensation: string;
  timing: string;
  /** YYYY-MM-DD, optional apply-by date. */
  deadline: string;
  /** Jobs and local services: let people call before the poster accepts. */
  allowPrecall: boolean;
  /** Critique W2: what an early caller may use — WhatsApp only (default) or calls too. */
  precallChannel: "whatsapp_only" | "call_and_whatsapp";
  // job
  salaryMin: string;
  salaryMax: string;
  incentiveType: IncentiveType;
  incentiveMax: string;
  openings: number | null;
  shift: ShiftKind | null;
  jobTimings: string;
  experienceMonths: number | null;
  qualification: Qualification | null;
  english: EnglishLevel | null;
  assets: string[];
  interview: string;
  // project
  budgetType: BudgetType;
  budgetMin: string;
  budgetMax: string;
  duration: ProjectDuration | null;
  experienceLevel: ExperienceLevel | null;
  questions: string[];
  // local service
  urgency: Urgency | null;
  preferredDate: string;
  localBudget: string;
}

export function emptyDraft(type: PostKind = "employment", skills: string[] = []): ComposerDraft {
  return {
    type,
    title: "",
    description: "",
    location: "",
    workMode: "",
    skills,
    segment: "community",
    sourceName: "",
    compensation: "",
    timing: "",
    deadline: "",
    allowPrecall: false,
    precallChannel: "whatsapp_only",
    salaryMin: "",
    salaryMax: "",
    incentiveType: "none",
    incentiveMax: "",
    openings: null,
    shift: null,
    jobTimings: "",
    experienceMonths: null,
    qualification: null,
    english: null,
    assets: [],
    interview: "",
    budgetType: "fixed",
    budgetMin: "",
    budgetMax: "",
    duration: null,
    experienceLevel: null,
    questions: [],
    urgency: null,
    preferredDate: "",
    localBudget: "",
  };
}

export function isPostKind(v: string | null | undefined): v is PostKind {
  return !!v && (MAIN_KINDS as string[]).concat(OTHER_KINDS).includes(v);
}

/**
 * Field codes shared by the AI contract (`confidence`, `missing`), the
 * form's field anchors and the suggestions. hourly_rate and budget_type fold
 * into the one budget control.
 */
export type FieldCode =
  | "type"
  | "title"
  | "description"
  | "location"
  | "work_mode"
  | "timing"
  | "required_capabilities"
  | "salary"
  | "incentive_type"
  | "openings"
  | "shift"
  | "job_timings"
  | "interview_details"
  | "min_qualification"
  | "english_level"
  | "experience"
  | "requires_assets"
  | "budget"
  | "duration"
  | "experience_level"
  | "screening_questions"
  | "preferred_date"
  | "urgency"
  | "deadline";

export function fieldCodeOf(code: string): FieldCode | null {
  const alias: Record<string, FieldCode> = {
    hourly_rate: "budget",
    budget_type: "budget",
    budget_paise: "budget",
    salary_min_paise: "salary",
    salary_max_paise: "salary",
    experience_min_months: "experience",
    capabilities: "required_capabilities",
  };
  if (alias[code]) return alias[code];
  const known: FieldCode[] = [
    "type", "title", "description", "location", "work_mode", "timing", "required_capabilities", "salary",
    "incentive_type", "openings", "shift", "job_timings", "interview_details", "min_qualification", "english_level",
    "experience", "requires_assets", "budget", "duration", "experience_level", "screening_questions",
    "preferred_date", "urgency", "deadline",
  ];
  return (known as string[]).includes(code) ? (code as FieldCode) : null;
}

/** Fields that must be looked at (typed in, or "Looks right") before publishing. */
export const MUST_CHECK: FieldCode[] = ["salary", "budget", "incentive_type", "openings"];

/** Below this the draft marks a field "please check" (the rules engine reports 0.55–0.9). */
export const CHECK_THRESHOLD = 0.6;

export interface AiApplied {
  draft: ComposerDraft;
  flagged: FieldCode[];
  questions: { code: FieldCode; question: string }[];
}

/**
 * When the poster picked a type and the draft inferred another, the draft's
 * money lands in the wrong block (a project read as a local service keeps its
 * budget in local_service). Carry the amounts over to the chosen type's
 * block so nothing the poster said is lost.
 */
export function retypeAiDraft(ai: AiDraft, kind: PostKind): AiDraft {
  if (ai.type === kind) return ai;
  const lo = ai.freelance?.budget_min_paise ?? ai.employment?.salary_min_paise ?? ai.local_service?.budget_paise ?? null;
  const hi = ai.freelance?.budget_max_paise ?? ai.employment?.salary_max_paise ?? ai.local_service?.budget_paise ?? null;
  const out: AiDraft = { ...ai, type: kind };
  if (kind === "freelance" && !ai.freelance)
    out.freelance = { budget_type: "fixed", budget_min_paise: lo, budget_max_paise: hi, hourly_rate_min_paise: null, hourly_rate_max_paise: null, duration: null, experience_level: null, screening_questions: [] };
  if (kind === "employment" && !ai.employment)
    out.employment = { salary_min_paise: lo, salary_max_paise: hi, incentive_type: null, openings: null, shift: null, job_timings: null, interview_details: null, min_qualification: null, english_level: null, experience_min_months: null, experience_max_months: null, requires_assets: [] };
  if (kind === "local_service" && !ai.local_service) out.local_service = { preferred_date: null, budget_paise: hi ?? lo, urgency: null };
  return out;
}

/** An AI draft laid onto the form. Anything the draft left empty keeps what the poster already had. */
export function draftFromAi(ai: AiDraft, base: ComposerDraft): AiApplied {
  const type: PostKind = isPostKind(ai.type) ? ai.type : base.type;
  const d: ComposerDraft = { ...base, type };
  if (ai.title) d.title = ai.title;
  if (ai.description) d.description = ai.description;
  if (ai.location) d.location = ai.location;
  if (ai.work_mode === "on_site" || ai.work_mode === "remote" || ai.work_mode === "both") d.workMode = ai.work_mode;
  if (ai.timing) d.timing = ai.timing;
  if (ai.required_capabilities.length) d.skills = [...new Set([...base.skills, ...ai.required_capabilities])].slice(0, 10);
  const e = ai.employment;
  if (e) {
    if (e.salary_min_paise != null) d.salaryMin = paiseToRupeeInput(e.salary_min_paise);
    if (e.salary_max_paise != null) d.salaryMax = paiseToRupeeInput(e.salary_max_paise);
    if (e.incentive_type) d.incentiveType = e.incentive_type;
    if (e.openings != null) d.openings = e.openings;
    if (e.shift) d.shift = e.shift;
    if (e.job_timings) d.jobTimings = e.job_timings;
    if (e.interview_details) d.interview = e.interview_details;
    if (e.min_qualification) d.qualification = e.min_qualification;
    if (e.english_level) d.english = e.english_level;
    if (e.experience_min_months != null) d.experienceMonths = e.experience_min_months;
    if (e.requires_assets.length) d.assets = e.requires_assets.filter((a) => (ASSETS as readonly string[]).includes(a));
  }
  const f = ai.freelance;
  if (f) {
    const hourly = f.budget_type === "hourly" || (f.budget_type == null && (f.hourly_rate_min_paise != null || f.hourly_rate_max_paise != null));
    d.budgetType = hourly ? "hourly" : "fixed";
    const lo = hourly ? f.hourly_rate_min_paise : f.budget_min_paise;
    const hi = hourly ? f.hourly_rate_max_paise : f.budget_max_paise;
    if (lo != null) d.budgetMin = paiseToRupeeInput(lo);
    if (hi != null) d.budgetMax = paiseToRupeeInput(hi);
    if (f.duration) d.duration = f.duration;
    if (f.experience_level) d.experienceLevel = f.experience_level;
    if (f.screening_questions.length) d.questions = f.screening_questions.map((q) => q.text).filter(Boolean).slice(0, MAX_QUESTIONS);
  }
  const l = ai.local_service;
  if (l) {
    if (l.urgency) d.urgency = l.urgency;
    if (l.preferred_date) d.preferredDate = l.preferred_date;
    if (l.budget_paise != null) d.localBudget = paiseToRupeeInput(l.budget_paise);
  }
  const flagged: FieldCode[] = Object.entries(ai.confidence)
    .filter(([, c]) => c < CHECK_THRESHOLD)
    .map(([code]) => fieldCodeOf(code))
    .filter((c): c is FieldCode => c !== null && c !== "description" && c !== "type");
  const questions = ai.missing
    .map((code, i) => ({ code: fieldCodeOf(code), question: ai.questions[i] ?? "" }))
    .filter((q): q is { code: FieldCode; question: string } => q.code !== null && !!q.question);
  // [Critique L8] Money decides whether people respond, and a misread amount
  // "looks filled". Every amount and the openings the draft filled are
  // marked "Please check" whatever the confidence; a range with only one
  // side is asked as a question (the page supplies the localized text for
  // an empty `question`).
  if (e && (e.salary_min_paise != null || e.salary_max_paise != null)) flagged.push("salary");
  if (e && (e.salary_min_paise == null) !== (e.salary_max_paise == null)) questions.push({ code: "salary", question: "" });
  if (e && e.openings != null) flagged.push("openings");
  if (e && e.incentive_type && e.incentive_type !== "none") flagged.push("incentive_type");
  if (f && (d.budgetMin || d.budgetMax)) flagged.push("budget");
  if (f && !!d.budgetMin !== !!d.budgetMax) questions.push({ code: "budget", question: "" });
  if (l && l.budget_paise != null) flagged.push("budget");
  return { draft: d, flagged: [...new Set(flagged)], questions: questions.filter((q, i, all) => all.findIndex((x) => x.code === q.code) === i) };
}

function paise(v: string): number | null {
  return rupeesToPaise(v);
}

/** The typed fields for the draft's type — and only its type (the server refuses others). */
export function structuredOf(d: ComposerDraft): StructuredInput | undefined {
  if (d.type === "employment") {
    return {
      salary_min_paise: paise(d.salaryMin),
      salary_max_paise: paise(d.salaryMax),
      incentive_type: d.incentiveType,
      incentive_max_paise: d.incentiveType === "none" ? null : paise(d.incentiveMax),
      openings: d.openings,
      shift: d.shift,
      job_timings: d.jobTimings.trim() || null,
      interview_details: d.interview.trim() || null,
      min_qualification: d.qualification,
      english_level: d.english,
      experience_min_months: d.experienceMonths,
      requires_assets: d.assets,
    };
  }
  if (d.type === "freelance") {
    const hourly = d.budgetType === "hourly";
    return {
      budget_type: d.budgetType,
      budget_min_paise: hourly ? null : paise(d.budgetMin),
      budget_max_paise: hourly ? null : paise(d.budgetMax),
      hourly_rate_min_paise: hourly ? paise(d.budgetMin) : null,
      hourly_rate_max_paise: hourly ? paise(d.budgetMax) : null,
      duration: d.duration,
      experience_level: d.experienceLevel,
      screening_questions: d.questions
        .map((text) => text.trim())
        .filter(Boolean)
        .slice(0, MAX_QUESTIONS)
        .map((text, i) => ({ id: `q${i + 1}`, text })),
    };
  }
  if (d.type === "local_service") {
    return { preferred_date: d.preferredDate || null, budget_paise: paise(d.localBudget), urgency: d.urgency };
  }
  return undefined;
}

/** createOpportunity / updateOpportunity body. */
export function toWrite(d: ComposerDraft): OpportunityWrite {
  const typed = MAIN_KINDS.includes(d.type);
  return {
    title: d.title.trim() || undefined,
    type: d.type,
    description: d.description.trim() || undefined,
    location: d.location.trim() || undefined,
    work_mode: d.workMode || undefined,
    timing: d.timing.trim() || undefined,
    deadline: d.deadline ? `${d.deadline}T23:59:00+05:30` : undefined,
    required_capabilities: d.skills,
    response_method: "in_app",
    // Jobs and projects: the server derives the money line from `structured`.
    // [Trust pack §2] a local service may state how it is paid ("₹300 a visit") instead of a budget.
    compensation: typed && d.type !== "local_service" ? undefined : d.compensation.trim() || undefined,
    structured: structuredOf(d),
    // Only jobs and local services take calls before acceptance (the server
    // refuses the flag elsewhere with precall_not_for_type).
    allow_precall: d.type === "employment" || d.type === "local_service" ? d.allowPrecall : undefined,
    precall_channel: (d.type === "employment" || d.type === "local_service") && d.allowPrecall ? d.precallChannel : undefined,
  };
}

/** getPostingTips draft. */
export function toTipsDraft(d: ComposerDraft): AiDraftInput {
  const s = structuredOf(d) ?? {};
  return {
    type: d.type,
    title: d.title || null,
    description: d.description || null,
    location: d.location || null,
    work_mode: d.workMode || null,
    timing: d.timing || null,
    required_capabilities: d.skills,
    deadline: d.deadline ? `${d.deadline}T23:59:00+05:30` : null,
    employment: d.type === "employment" ? (s as AiDraftInput["employment"]) : null,
    freelance:
      d.type === "freelance"
        ? { ...(s as Record<string, unknown>), screening_questions: d.questions.filter(Boolean).map((text) => ({ text })) }
        : null,
    local_service: d.type === "local_service" ? (s as AiDraftInput["local_service"]) : null,
  };
}

// ---- client-side checks (inline errors before a round trip) -----------------------

export type FieldErrors = Partial<Record<FieldCode, string>>;

/** Error keys (hiring:composer.error.*) for what is missing or contradictory. */
export function validate(d: ComposerDraft): Partial<Record<FieldCode, string>> {
  const e: Partial<Record<FieldCode, string>> = {};
  if (!d.title.trim()) e.title = "titleRequired";
  if ((d.type === "employment" || d.type === "local_service") && !d.location.trim()) e.location = "locationRequired";
  if (d.type === "employment") {
    // [Start flow 2026-10, decision 11] fixed pay is one amount: one side
    // filled is "₹10,000 a month" (the server mirrors it), never an error.
    const lo = rupeesToPaise(d.salaryMin);
    const hi = rupeesToPaise(d.salaryMax);
    if (lo === null && hi === null) e.salary = "salaryRequired";
    else if (lo !== null && hi !== null && lo > hi) e.salary = "salaryRange";
  }
  if (d.type === "freelance") {
    const lo = rupeesToPaise(d.budgetMin);
    const hi = rupeesToPaise(d.budgetMax);
    if (lo === null && hi === null) e.budget = "budgetRequired";
    else if (lo !== null && hi !== null && lo > hi) e.budget = "budgetRange";
  }
  // [Trust pack §2] mirrors 422 pay_basis_required: a budget, or how it is paid.
  if (d.type === "local_service" && rupeesToPaise(d.localBudget) === null && !d.compensation.trim()) e.budget = "payBasisRequired";
  if (d.segment === "public" && !d.sourceName.trim()) e.type = "sourceRequired";
  return e;
}

// ---- suggestions: one merged list of one-tap fixes --------------------------------

export type FixKey =
  | "qualification_12th"
  | "english_basic"
  | "experience_1y"
  | "add_shift"
  | "add_openings"
  | "add_job_timings"
  | "add_interview"
  | "add_incentives"
  | "add_salary"
  | "add_budget"
  | "add_duration"
  | "add_question"
  | "experience_level_intermediate"
  | "add_deadline"
  | "add_preferred_date"
  | "add_urgency"
  | "add_local_budget"
  | "add_skills"
  | "fewer_skills"
  | "add_location"
  | "allow_remote"
  | "expand_description"
  | "fix_title"
  | "add_timing";

const FIX_BY_CODE: Record<string, FixKey> = {
  // backend A (getOpportunitySuggestions)
  lower_qualification: "qualification_12th",
  relax_english: "english_basic",
  lower_experience: "experience_1y",
  add_shift: "add_shift",
  add_openings: "add_openings",
  add_job_timings: "add_job_timings",
  add_interview_details: "add_interview",
  add_salary: "add_salary",
  add_budget: "add_budget",
  add_duration: "add_duration",
  add_screening_question: "add_question",
  relax_experience_level: "experience_level_intermediate",
  add_deadline: "add_deadline",
  add_preferred_date: "add_preferred_date",
  add_urgency: "add_urgency",
  add_local_budget: "add_local_budget",
  add_skills: "add_skills",
  fewer_skills: "fewer_skills",
  add_location: "add_location",
  consider_remote: "allow_remote",
  expand_description: "expand_description",
  // backend C (getPostingTips)
  add_title: "fix_title",
  shorten_title: "fix_title",
  add_description: "expand_description",
  set_remote_or_both: "allow_remote",
  add_capabilities: "add_skills",
  fewer_capabilities: "fewer_skills",
  lower_min_qualification: "qualification_12th",
  relax_english_level: "english_basic",
  reduce_experience: "experience_1y",
  add_hourly_rate: "add_budget",
  add_screening_questions: "add_question",
  set_urgency: "add_urgency",
  add_timing: "add_timing",
  mention_incentives: "add_incentives",
};

/** The form field a fix changes (for "Edit it" jumps and error placement). */
export const FIX_FIELD: Record<FixKey, FieldCode> = {
  qualification_12th: "min_qualification",
  english_basic: "english_level",
  experience_1y: "experience",
  add_shift: "shift",
  add_openings: "openings",
  add_job_timings: "job_timings",
  add_interview: "interview_details",
  add_incentives: "incentive_type",
  add_salary: "salary",
  add_budget: "budget",
  add_duration: "duration",
  add_question: "screening_questions",
  experience_level_intermediate: "experience_level",
  add_deadline: "deadline",
  add_preferred_date: "preferred_date",
  add_urgency: "urgency",
  add_local_budget: "budget",
  add_skills: "required_capabilities",
  fewer_skills: "required_capabilities",
  add_location: "location",
  allow_remote: "work_mode",
  expand_description: "description",
  fix_title: "title",
  add_timing: "timing",
};

export type Impact = "high" | "medium" | "low";

export interface Fix {
  key: FixKey;
  text: string;
  impact: Impact;
}

/** True once the draft already has what the fix asks for (the tip is then hidden). */
export function isSatisfied(key: FixKey, d: ComposerDraft): boolean {
  switch (key) {
    case "qualification_12th":
      return d.qualification !== "graduate" && d.qualification !== "postgraduate";
    case "english_basic":
      return d.english !== "good" && d.english !== "fluent";
    case "experience_1y":
      return (d.experienceMonths ?? 0) <= 24;
    case "add_shift":
      return d.shift !== null;
    case "add_openings":
      return d.openings !== null;
    case "add_job_timings":
      return !!d.jobTimings.trim();
    case "add_interview":
      return !!d.interview.trim();
    case "add_incentives":
      return d.incentiveType !== "none";
    case "add_salary":
      return !!d.salaryMin || !!d.salaryMax;
    case "add_budget":
      return !!d.budgetMin || !!d.budgetMax;
    case "add_duration":
      return d.duration !== null;
    case "add_question":
      return d.questions.some((q) => q.trim());
    case "experience_level_intermediate":
      return d.experienceLevel !== "expert";
    case "add_deadline":
      return !!d.deadline;
    case "add_preferred_date":
      return !!d.preferredDate || d.urgency === "today";
    case "add_urgency":
      return d.urgency !== null;
    case "add_local_budget":
      return !!d.localBudget;
    case "add_skills":
      return d.skills.length > 0;
    case "fewer_skills":
      return d.skills.length <= 5;
    case "add_location":
      return !!d.location.trim();
    case "allow_remote":
      return d.workMode === "remote" || d.workMode === "both";
    case "expand_description":
      return d.description.trim().length >= 80;
    case "fix_title":
      return d.title.trim().length >= 8 && d.title.trim().length <= 90;
    case "add_timing":
      return !!d.timing.trim();
  }
}

const IMPACT_OF_SUGGESTION: Record<OpportunitySuggestion["impact"], Impact> = {
  more_responses: "high",
  better_fit: "medium",
  trust: "medium",
};
const RANK: Record<Impact, number> = { high: 0, medium: 1, low: 2 };

/** Both tip sources as one de-duplicated list, highest impact first, already-done ones dropped. */
export function mergeFixes(suggestions: OpportunitySuggestion[], tips: PostingTip[], d: ComposerDraft, limit = 6): Fix[] {
  const byKey = new Map<FixKey, Fix>();
  for (const s of suggestions) {
    const key = FIX_BY_CODE[s.code];
    if (!key || isSatisfied(key, d) || byKey.has(key)) continue;
    byKey.set(key, { key, text: s.message, impact: IMPACT_OF_SUGGESTION[s.impact] ?? "medium" });
  }
  for (const tip of tips) {
    const key = FIX_BY_CODE[tip.code];
    if (!key || isSatisfied(key, d)) continue;
    const had = byKey.get(key);
    if (!had) byKey.set(key, { key, text: tip.text, impact: tip.impact });
    else if (RANK[tip.impact] < RANK[had.impact]) byKey.set(key, { ...had, impact: tip.impact });
  }
  return [...byKey.values()].sort((a, b) => RANK[a.impact] - RANK[b.impact]).slice(0, limit);
}

/** YYYY-MM-DD for today + n days, in the member's local calendar. */
export function isoInDays(n: number): string {
  const t = new Date();
  t.setDate(t.getDate() + n);
  const m = String(t.getMonth() + 1).padStart(2, "0");
  const day = String(t.getDate()).padStart(2, "0");
  return `${t.getFullYear()}-${m}-${day}`;
}
