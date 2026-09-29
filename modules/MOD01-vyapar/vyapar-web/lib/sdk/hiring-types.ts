// [FE1 — 2026-09-28] Wire types for structured opportunities, structured
// applications, the poster's applicant pipeline, the two-level taxonomy and
// the AI assistance endpoints. Contracts: references/imp-backend-a.md
// (structured fields, applicants, taxonomy) and references/imp-backend-c.md
// (AI). Money is always integer paise; labels arrive already translated
// into the language sent in X-Vyapar-Language.

import type { ContactAction } from "./domains/contact";

// ---- structured opportunity fields (migration 018) ------------------------------

export type ShiftKind = "day" | "night" | "rotational" | "flexible";
export type IncentiveType = "none" | "fixed_plus_incentive" | "incentive_only";
export type Qualification = "below_10th" | "10th" | "12th" | "diploma" | "iti" | "graduate" | "postgraduate" | "any";
export type EnglishLevel = "none" | "basic" | "good" | "fluent";
export type BudgetType = "fixed" | "hourly";
export type ProjectDuration = "under_1_week" | "1_4_weeks" | "1_3_months" | "3_6_months" | "over_6_months" | "ongoing";
export type ExperienceLevel = "entry" | "intermediate" | "expert";
export type Urgency = "today" | "this_week" | "flexible";

export interface ScreeningQuestion {
  id?: string;
  text: string;
}

/**
 * Every typed field, as `OpportunityOut.structured` returns it: all keys are
 * present, the ones belonging to another type are null ([] for the lists).
 * On create/patch the same shape is sent, partially.
 */
export interface StructuredFields {
  // employment
  salary_min_paise: number | null;
  salary_max_paise: number | null;
  incentive_type: IncentiveType | null;
  incentive_max_paise: number | null;
  openings: number | null;
  shift: ShiftKind | null;
  job_timings: string | null;
  interview_details: string | null;
  min_qualification: Qualification | null;
  english_level: EnglishLevel | null;
  experience_min_months: number | null;
  experience_max_months: number | null;
  requires_assets: string[];
  // freelance
  budget_type: BudgetType | null;
  budget_min_paise: number | null;
  budget_max_paise: number | null;
  hourly_rate_min_paise: number | null;
  hourly_rate_max_paise: number | null;
  duration: ProjectDuration | null;
  experience_level: ExperienceLevel | null;
  screening_questions: ScreeningQuestion[];
  // local service
  preferred_date: string | null;
  budget_paise: number | null;
  urgency: Urgency | null;
}

export type StructuredInput = Partial<StructuredFields>;

/** Body of createOpportunity / updateOpportunity with the typed fields. */
export interface OpportunityWrite {
  entry_mode?: "create" | "share" | "upload";
  title?: string;
  type?: string;
  description?: string;
  requirements?: string;
  compensation?: string;
  location?: string;
  work_mode?: "on_site" | "remote" | "both";
  timing?: string;
  required_capabilities?: string[];
  response_method?: "in_app" | "external";
  deadline?: string;
  source_segment?: "community" | "public";
  source_name?: string;
  source_url?: string;
  raw_input?: string;
  raw_image_url?: string;
  structured?: StructuredInput;
  candidate_pays?: boolean;
  /** Jobs and local services only: people may call before the poster accepts. */
  allow_precall?: boolean;
  /** Backend B (critique W2): "whatsapp_only" (default) or "call_and_whatsapp". */
  precall_channel?: "whatsapp_only" | "call_and_whatsapp";
}

/** getOpportunitySuggestions — rule-based tips on a saved opportunity (poster only). */
export interface OpportunitySuggestion {
  code: string;
  field: string | null;
  impact: "more_responses" | "better_fit" | "trust";
  message: string;
}

export interface OpportunitySuggestions {
  opportunity_id: string;
  suggestions: OpportunitySuggestion[];
}

// ---- structured applications (createEnquiry) --------------------------------------

export interface MilestoneInput {
  title: string;
  amount_paise: number;
  due_days: number;
}

export interface ScreeningAnswerInput {
  question_id: string;
  answer: string;
}

export type AppliedVia = "form" | "one_tap" | "voice" | "agent";

export interface CreateEnquiryBody {
  listing_id?: string;
  opportunity_id?: string;
  message: string;
  sub_choice?: "ask_question" | "request_quote";
  attachment_url?: string;
  bid_amount_paise?: number;
  bid_type?: BudgetType;
  timeline_days?: number;
  milestones?: MilestoneInput[];
  screening_answers?: ScreeningAnswerInput[];
  applied_via?: AppliedVia;
}

/** The sender's profile as it stood when they applied. */
export interface ProfileSnapshot {
  name: string | null;
  headline: string | null;
  experience_years: number | null;
  capabilities: string[];
  locality: string | null;
  languages: string[];
  availability: "now" | "this_week" | "later" | null;
  listing_id: string | null;
  listing_kind: "business" | "professional" | null;
}

// ---- applicant pipeline (poster only) ---------------------------------------------

export type ApplicantStage = "new" | "shortlisted" | "hired" | "declined";
export const APPLICANT_STAGES: readonly ApplicantStage[] = ["new", "shortlisted", "hired", "declined"];

export interface ApplicantProfile extends ProfileSnapshot {
  capability_labels: string[];
}

export interface ApplicantScreeningAnswer {
  question_id: string;
  question: string | null;
  answer: string;
}

/** imp-backend-a §7: the one skills verdict per applicant, worded for the poster. */
export interface SkillsMatch {
  state: "all" | "some" | "none" | "not_required";
  kind: "reason" | "risk" | null;
  matched_count: number;
  required_count: number;
  matched_skills: string[];
  missing_skills: string[];
  text: string | null;
  missing_text: string | null;
}

export interface Applicant {
  enquiry_id: string;
  sender_id: string;
  name: string | null;
  profile: ApplicantProfile;
  action_type: string;
  applied_via: AppliedVia | string;
  stage: ApplicantStage;
  stage_changed_at: string | null;
  thread_state: string;
  bid_amount_paise: number | null;
  bid_type: BudgetType | null;
  timeline_days: number | null;
  milestones: MilestoneInput[];
  screening_answers: ApplicantScreeningAnswer[];
  message_preview: string | null;
  created_at: string;
  /** Rule-based fit, 0–100. Never shown as a percentage. */
  match_score: number;
  match_signals: string[];
  match_reasons: string[];
  matched_capability_labels: string[];
  missing_capability_labels: string[];
  /** §7 — reasons above are poster-worded; the skills line leads them when it is a reason. */
  skills_match?: SkillsMatch | null;
  missing_skills?: { slug: string; label: string }[];
  match_risks?: string[];
  /** §6 — Call / WhatsApp for the poster once shortlisted (B's shape). */
  contact_actions?: ContactAction[];
  contact_revealed?: boolean;
}

export interface ApplicantListParams {
  stage?: ApplicantStage;
  sort?: "newest" | "match";
  limit?: number;
  cursor?: string | null;
}

export interface ApplicantPage {
  items: Applicant[];
  next_cursor: string | null;
  total: number;
  stage_counts: Record<ApplicantStage, number>;
}

export interface ApplicantCompare {
  opportunity_id: string;
  opportunity_title: string;
  required_capabilities: string[];
  required_capability_labels: string[];
  items: Applicant[];
}

// The taxonomy tree (getTaxonomyTree) and member badges (getMemberBadges)
// are FE2's domains/taxonomy.ts and domains/trust.ts; the hiring screens
// reuse those types.

// ---- AI assistance -------------------------------------------------------------------

export interface AiEmploymentDraft {
  salary_min_paise: number | null;
  salary_max_paise: number | null;
  incentive_type: IncentiveType | null;
  openings: number | null;
  shift: ShiftKind | null;
  job_timings: string | null;
  interview_details: string | null;
  min_qualification: Qualification | null;
  english_level: EnglishLevel | null;
  experience_min_months: number | null;
  experience_max_months: number | null;
  requires_assets: string[];
}

export interface AiFreelanceDraft {
  budget_type: BudgetType | null;
  budget_min_paise: number | null;
  budget_max_paise: number | null;
  hourly_rate_min_paise: number | null;
  hourly_rate_max_paise: number | null;
  duration: ProjectDuration | null;
  experience_level: ExperienceLevel | null;
  screening_questions: { text: string }[];
}

export interface AiLocalServiceDraft {
  preferred_date: string | null;
  budget_paise: number | null;
  urgency: Urgency | null;
}

/** draftOpportunity / readOpportunityImage */
export interface AiDraft {
  type: string;
  title: string | null;
  description: string | null;
  location: string | null;
  work_mode: string | null;
  timing: string | null;
  required_capabilities: string[];
  capability_labels: string[];
  employment: AiEmploymentDraft | null;
  freelance: AiFreelanceDraft | null;
  local_service: AiLocalServiceDraft | null;
  /** Field code → 0..1. */
  confidence: Record<string, number>;
  /** Field codes the poster still has to give. */
  missing: string[];
  /** Localized question for missing[i]. */
  questions: string[];
  source: "ai" | "rules";
  language: string;
}

export interface AiDraftRequest {
  text: string;
  language?: string;
  entry?: "text" | "voice";
}

export interface AiImageRequest {
  image_url?: string;
  upload_id?: string;
  language?: string;
}

export interface AiLabelledCode {
  code: string;
  text: string;
}

export interface AiShortlistItem {
  enquiry_id: string;
  sender_id: string;
  listing_id: string | null;
  name: string | null;
  kind: string | null;
  verified: boolean;
  experience_years: number | null;
  distance_km: number | null;
  availability: string | null;
  stage: string | null;
  bid_paise: number | null;
  /** 1–10. */
  match_score: number;
  reasons: AiLabelledCode[];
  risks: AiLabelledCode[];
  summary: string | null;
}

export interface AiShortlist {
  opportunity_id: string;
  applicant_count: number;
  items: AiShortlistItem[];
  source: "ai" | "rules";
  language: string;
}

export interface AiDraftInput {
  type?: string | null;
  title?: string | null;
  description?: string | null;
  location?: string | null;
  work_mode?: string | null;
  timing?: string | null;
  required_capabilities?: string[];
  deadline?: string | null;
  employment?: Partial<AiEmploymentDraft> | null;
  freelance?: Partial<AiFreelanceDraft> | null;
  local_service?: Partial<AiLocalServiceDraft> | null;
}

export interface PostingTip {
  code: string;
  impact: "high" | "medium" | "low";
  text: string;
}

export interface PostingTips {
  tips: PostingTip[];
  source: "ai" | "rules";
  language: string;
}

export interface BidRange {
  min_paise: number | null;
  median_paise: number | null;
  max_paise: number | null;
  sample_size: number;
  basis: "capability_overlap" | "same_type" | "poster_budget" | "none";
}

export interface ProposalHelp {
  cover_text: string;
  improvements: AiLabelledCode[];
  bid: BidRange;
  source: "ai" | "rules";
  language: string;
}
