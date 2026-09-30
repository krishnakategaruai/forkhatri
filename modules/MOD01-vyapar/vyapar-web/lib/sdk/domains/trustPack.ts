// [Trust pack, 2026-09-30 — references/imp-trust-pack.md] Scam shield,
// "paid on time", close the loop, restrictions and appeals, profession
// rules and council registrations. Types follow the contract exactly; every
// label, message and explanation arrives already in the reader's language
// (X-Vyapar-Language), so screens render them as sent and never map enums.
import { seg, type VyaparClient } from "../client";

// ---- 1. Scam shield ---------------------------------------------------------

export type ScamSurface = "opportunity" | "enquiry_reply" | "package";

export interface ScamCheck {
  allowed: boolean;
  code: string | null;
  message: string | null;
  explanation: string | null;
  rule: string | null;
  matched: string | null;
}

// ---- 2. Paid on time ----------------------------------------------------------

export interface PaidOnTimeAsk {
  id: string;
  source_kind: "hire" | "milestone" | string;
  title: string;
  payer_id: string;
  payer_name: string | null;
  question: string;
  asked_at: string;
  answered: boolean;
  answer: boolean | null;
  answered_at: string | null;
  link: string | null;
}

export interface PaidOnTime {
  member_id: string;
  answered: number;
  paid_on_time: number;
  shown: boolean;
  label: string | null;
  min_answers: number;
}

// ---- 3. Close the loop --------------------------------------------------------

export interface ApplicantsWaiting {
  waiting: number;
  new: number;
  shortlisted: number;
  oldest_waiting_days: number | null;
  message: string | null;
}

export interface CloseCheck extends ApplicantsWaiting {
  close_message: string;
}

// ---- Restrictions -------------------------------------------------------------

export interface Restriction {
  object_kind: "opportunity" | "listing" | string;
  object_id: string;
  title: string | null;
  restriction: "removed" | "paused" | "suspended" | "limited" | "held" | "hidden" | string;
  restriction_label: string;
  reason_code: string | null;
  reason_label: string | null;
  case_id: string | null;
  under_review: boolean;
  can_appeal: boolean;
  appeal_state: string | null;
  appeal_deadline: string | null;
  appeal_link: string | null;
  message: string | null;
}

// ---- 4. Profession rules ------------------------------------------------------

export interface ProfessionVerdict {
  profession: string;
  profession_label: string;
  regulator: string | null;
  restricted: boolean;
  allow_promotion: boolean;
  allow_public_reviews: boolean;
  allow_ranking_boost: boolean;
  allow_public_prices: boolean;
  permitted_fields: string[];
  hidden_fields: string[];
  contact_label: string | null;
  note: string | null;
  rule_reference?: string | null;
  rules_checked_on?: string | null;
  source_url?: string | null;
}

// ---- 5. Council registrations -------------------------------------------------

export interface CredentialType {
  credential_type: string;
  label: string;
  fixed_council: string | null;
  council_suggestions: string[];
  number_hint: string;
  needs_document_uri: boolean;
}

export type CredentialStatus = "claimed" | "verified" | "failed" | "expired" | string;

export interface CouncilBadge {
  id: string;
  credential_type: string;
  type_label: string;
  council: string;
  registration_number: string;
  registered_on: string | null;
  status: CredentialStatus;
  label: string;
  checked_on: string | null;
  checked_on_label: string | null;
  check_source?: string | null;
}

export interface Credential extends CouncilBadge {
  last_attempt_at: string | null;
  expires_at: string | null;
  verification_record_id: string | null;
  check_note: string | null;
  listing_id: string | null;
}

export interface CredentialInput {
  credential_type: string;
  registration_number: string;
  council?: string | null;
  registered_on?: string | null;
  document_uri?: string | null;
}

export function trustPackApi(c: VyaparClient) {
  return {
    /** checkScamShield — never raises, stores nothing */
    scamCheck: (body: { text: string; surface: ScamSurface; opportunity_type?: string | null }, signal?: AbortSignal) =>
      c.post<ScamCheck>("/v1/trust/scam-check", body, { signal }),
    /** listMyPaidOnTimeAsks */
    paidOnTimeAsks: (state: "open" | "all" = "open") => c.get<PaidOnTimeAsk[]>("/v1/paid-on-time/asks", { state }),
    /** answerPaidOnTime */
    answerPaidOnTime: (askId: string, paidOnTime: boolean) =>
      c.post<PaidOnTimeAsk>(`/v1/paid-on-time/asks/${seg(askId)}/answer`, { paid_on_time: paidOnTime }),
    /** getMemberPaidOnTime */
    memberPaidOnTime: (memberId: string) => c.get<PaidOnTime>(`/v1/members/${seg(memberId)}/paid-on-time`),
    /** getOpportunityCloseCheck — the person who posted only */
    closeCheck: (opportunityId: string) => c.get<CloseCheck>(`/v1/opportunities/${seg(opportunityId)}/close-check`),
    /** listMyRestrictions */
    myRestrictions: () => c.get<Restriction[]>("/v1/me/restrictions"),
    /** listCredentialTypes */
    credentialTypes: () => c.get<CredentialType[]>("/v1/credentials/types"),
    /** listMyCredentials */
    myCredentials: () => c.get<Credential[]>("/v1/me/profile/credentials"),
    /** addCredential */
    addCredential: (body: CredentialInput) => c.post<Credential>("/v1/me/profile/credentials", body),
    /** recheckCredential */
    recheckCredential: (id: string) => c.post<Credential>(`/v1/me/profile/credentials/${seg(id)}/recheck`),
    /** deleteCredential */
    deleteCredential: (id: string) => c.delete<{ deleted: boolean }>(`/v1/me/profile/credentials/${seg(id)}`),
  };
}

export type TrustPackApi = ReturnType<typeof trustPackApi>;
