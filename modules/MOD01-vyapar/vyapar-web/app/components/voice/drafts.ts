// [Voice interview 2026-09-30] What the interview's `draft` becomes on the
// normal screens. Posting: the draftOpportunity shape (AiDraft), completed
// with safe empties so the composer's draftFromAi can lay it onto the form.
// Profile: the fields /listings/new already edits.
import type { AiDraft, VoiceFlow } from "@/lib/sdk";
import type { PostKind } from "@/app/components/composer/draft";

export const FLOW_KIND: Record<Exclude<VoiceFlow, "profile">, PostKind> = {
  post_job: "employment",
  post_project: "freelance",
  post_local: "local_service",
};

export function flowForKind(kind: PostKind | null): VoiceFlow | null {
  if (kind === "employment") return "post_job";
  if (kind === "freelance") return "post_project";
  if (kind === "local_service") return "post_local";
  return null;
}

const arr = (v: unknown): string[] => (Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : []);
const str = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v.trim() : null);

export function toAiDraft(raw: Record<string, unknown>, flow: VoiceFlow, language: string): AiDraft {
  const d = raw as Partial<AiDraft>;
  const kind = flow === "profile" ? "employment" : FLOW_KIND[flow];
  return {
    type: typeof d.type === "string" && d.type ? d.type : kind,
    title: str(d.title),
    description: str(d.description),
    location: str(d.location),
    work_mode: str(d.work_mode),
    timing: str(d.timing),
    required_capabilities: arr(d.required_capabilities),
    capability_labels: arr(d.capability_labels),
    employment: d.employment ? { ...d.employment, requires_assets: d.employment.requires_assets ?? [] } : null,
    freelance: d.freelance ? { ...d.freelance, screening_questions: d.freelance.screening_questions ?? [] } : null,
    local_service: d.local_service ?? null,
    confidence: d.confidence && typeof d.confidence === "object" ? d.confidence : {},
    missing: arr(d.missing),
    questions: arr(d.questions),
    source: d.source === "ai" ? "ai" : "rules",
    language: typeof d.language === "string" ? d.language : language,
  };
}

export interface VoiceProfile {
  name: string | null;
  headline: string | null;
  locality: string | null;
  capabilities: string[];
  capabilitiesOther: string | null;
  serviceMode: "on_site" | "remote" | "both" | null;
  phone: string | null;
  /** Saved as-is with the profile (PATCH /v1/me/profile); the form has no field for them. */
  experienceYears: number | null;
  ownAssets: string[] | null;
}

/** Post-only extras the draftOpportunity shape doesn't carry. */
export function postExtras(raw: Record<string, unknown>): { deadline: string | null; compensation: string | null } {
  return { deadline: str(raw.deadline), compensation: str(raw.compensation) };
}

export function toProfile(raw: Record<string, unknown>): VoiceProfile {
  const mode = str(raw.service_mode);
  const other = raw.capabilities_other;
  return {
    name: str(raw.name),
    headline: str(raw.headline),
    locality: str(raw.locality),
    capabilities: arr(raw.capabilities),
    capabilitiesOther: Array.isArray(other) ? arr(other).join(", ") || null : str(other),
    serviceMode: mode === "on_site" || mode === "remote" || mode === "both" ? mode : null,
    phone: str(raw.primary_phone) ?? str(raw.phone),
    experienceYears: typeof raw.experience_years === "number" ? raw.experience_years : null,
    ownAssets: Array.isArray(raw.own_assets) ? arr(raw.own_assets) : null,
  };
}
