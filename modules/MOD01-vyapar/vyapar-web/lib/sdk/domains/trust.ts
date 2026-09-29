// [FE2 — imp-backend-b §2, §3] Count-based badges and the "Nobody charges
// job seekers" protection. Types follow the backend contract exactly:
// badges are earned counts with a localized label and description (never a
// score), seeker protection is a localized notice plus the report reason it
// points at.
import { seg, type VyaparClient } from "../client";

export type BadgeKey = "responds_fast" | "reliable" | "rising" | "top_recommended" | "verified_business" | "repeat_hires";

export interface Badge {
  key: BadgeKey | string;
  label: string;
  description: string;
  earned_at: string;
}

export interface MemberBadges {
  member_id: string;
  badges: Badge[];
}

export interface SeekerProtection {
  applies: boolean;
  title: string;
  body: string;
  report_reason?: string;
  report_label: string;
}

export interface SeekerChargeCheck {
  allowed: boolean;
  code?: string | null;
  message?: string | null;
}

export function badgesApi(c: VyaparClient) {
  return {
    /** getMemberBadges */
    forMember: (memberId: string) => c.get<MemberBadges>(`/v1/members/${seg(memberId)}/badges`),
  };
}

export function seekerProtectionApi(c: VyaparClient) {
  return {
    /** getOpportunitySeekerProtection */
    get: (opportunityId: string) => c.get<SeekerProtection | null>(`/v1/opportunities/${seg(opportunityId)}/seeker-protection`),
    /** checkSeekerCharge — ask before saving whether a post charges applicants */
    check: (text: string, structured?: Record<string, unknown>) =>
      c.post<SeekerChargeCheck>("/v1/opportunities/seeker-charge-check", { text, structured }),
  };
}

export type BadgesApi = ReturnType<typeof badgesApi>;
export type SeekerProtectionApi = ReturnType<typeof seekerProtectionApi>;
