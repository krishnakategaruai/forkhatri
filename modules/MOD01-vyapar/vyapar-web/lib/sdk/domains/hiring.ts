// [FE1 — 2026-09-28] Hiring: the poster's applicant pipeline, the
// five AI assistance operations (the taxonomy tree and member badges are
// FE2's domains/taxonomy.ts and domains/trust.ts). operation_id names follow the backend contract
// (references/imp-backend-a.md §3–4, imp-backend-c.md) so the SDK, the
// OpenAPI document and the agent (MCP) tools share one vocabulary.
import { seg, type VyaparClient } from "../client";
import type {
  AiDraft,
  AiDraftInput,
  AiDraftRequest,
  AiImageRequest,
  AiShortlist,
  Applicant,
  ApplicantCompare,
  ApplicantListParams,
  ApplicantPage,
  ApplicantStage,
  CreateEnquiryBody,
  OpportunitySuggestions,
  PostingTips,
  ProposalHelp,
  OpportunityWrite,
} from "../hiring-types";
import type { Opportunity } from "../types";

export function postingApi(c: VyaparClient) {
  const base = (id: string) => `/v1/opportunities/${seg(id)}`;
  return {
    /** createOpportunity — always saved as a draft; publish is a separate step */
    create: (body: OpportunityWrite) => c.post<Opportunity>("/v1/opportunities", body),
    /** updateOpportunity — `structured` is partial: fields sent replace, the rest stay */
    update: (id: string, patch: OpportunityWrite) => c.patch<Opportunity>(base(id), patch),
    /** confirmOpportunityFields */
    confirm: (id: string, fields: string[]) => c.patch<Opportunity>(`${base(id)}/confirm`, { fields }),
    /** publishOpportunity — 422 salary_required / budget_required / seeker_charge_not_allowed */
    publish: (id: string) => c.post<Opportunity>(`${base(id)}/publish`),
    /** getOpportunitySuggestions — tips that name the field to change (poster only) */
    suggestions: (id: string) => c.get<OpportunitySuggestions>(`${base(id)}/suggestions`),
  };
}

export function responsesApi(c: VyaparClient) {
  return {
    /**
     * createEnquiry with the structured fields: a one-tap job application,
     * a proposal (bid, timeline, milestones, screening answers) or a
     * quote/question. The server resolves the action from the target.
     */
    create: (body: CreateEnquiryBody, idempotencyKey?: string) =>
      c.post<{ id: string }>("/v1/enquiries", body, { idempotencyKey }),
  };
}

export function applicantsApi(c: VyaparClient) {
  const base = (id: string) => `/v1/opportunities/${seg(id)}/applicants`;
  return {
    /** listOpportunityApplicants — `stage_counts` ignores the stage filter, `total` respects it */
    list: (opportunityId: string, params: ApplicantListParams = {}) =>
      c.get<ApplicantPage>(base(opportunityId), { ...params }),
    /** compareApplicants — 2 to 4 enquiry ids, returned in the order asked */
    compare: (opportunityId: string, enquiryIds: readonly string[]) =>
      c.get<ApplicantCompare>(`${base(opportunityId)}/compare`, { ids: enquiryIds }),
    /** setApplicantStage — hired and declined are final (409 stage_final) */
    setStage: (opportunityId: string, enquiryId: string, stage: ApplicantStage) =>
      c.post<Applicant>(`${base(opportunityId)}/${seg(enquiryId)}/stage`, { stage }),
    /** recordApplicantContactAttempt — log a Call/WhatsApp tap before opening the link (poster only) */
    recordContact: (opportunityId: string, enquiryId: string, channel: "call" | "whatsapp") =>
      c.post<Applicant>(`${base(opportunityId)}/${seg(enquiryId)}/contact-attempts`, { channel }, { keepalive: true }),
  };
}

export function aiApi(c: VyaparClient) {
  return {
    /** draftOpportunity — a typed draft from free text (typed or dictated) */
    draftOpportunity: (body: AiDraftRequest) => c.post<AiDraft>("/v1/ai/draft-opportunity", body),
    /** readOpportunityImage — the same draft, read from a photo or PDF (501 without the AI provider) */
    readOpportunityImage: (body: AiImageRequest) => c.post<AiDraft>("/v1/ai/read-opportunity-image", body),
    /** getAiShortlist — applicants scored 1–10 with reasons and risks (poster only) */
    getAiShortlist: (opportunityId: string, language?: string) =>
      c.get<AiShortlist>(`/v1/opportunities/${seg(opportunityId)}/ai-shortlist`, { language }),
    /** getPostingTips — from a draft, or from a saved opportunity (poster only) */
    getPostingTips: (body: { draft?: AiDraftInput; opportunity_id?: string; language?: string }) =>
      c.post<PostingTips>("/v1/ai/posting-tips", body),
    /** improveProposal — suggested cover text, what is still missing, and a bid range */
    improveProposal: (body: { opportunity_id: string; text?: string; language?: string }) =>
      c.post<ProposalHelp>("/v1/ai/improve-proposal", body),
  };
}

export type PostingApi = ReturnType<typeof postingApi>;
export type ResponsesApi = ReturnType<typeof responsesApi>;
export type ApplicantsApi = ReturnType<typeof applicantsApi>;
export type AiApi = ReturnType<typeof aiApi>;
