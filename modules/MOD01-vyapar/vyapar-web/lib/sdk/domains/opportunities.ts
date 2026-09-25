// [IMP38 — Refactor C] Opportunities and the Discover feed.
// operation_id names follow the backend contract (workstream A) so the SDK,
// the OpenAPI document and the agent (MCP) tools all use one vocabulary.
import { seg, type VyaparClient } from "../client";
import type {
  FeedParams,
  FeedResponse,
  NotInterestedReason,
  Opportunity,
  OpportunityCard,
  Page,
  PageParams,
  ProfileCardData,
  WhyResponse,
} from "../types";

export function opportunitiesApi(c: VyaparClient) {
  const base = (id: string) => `/v1/opportunities/${seg(id)}`;
  return {
    /** getOpportunity */
    get: (id: string) => c.get<Opportunity>(base(id)),
    /** listSimilarOpportunities */
    similar: (id: string) => c.get<Opportunity[]>(`${base(id)}/similar`),
    /** getOpportunityWhy — the "Why this?" signals */
    why: (id: string) => c.get<WhyResponse>(`${base(id)}/why`),
    /** listMatchingProfiles — profiles that have the skills the poster asked for (poster only) */
    matchingProfiles: (id: string) => c.get<ProfileCardData[]>(`${base(id)}/matching-profiles`),
    /** listMyOpportunities / listMyOpportunitiesPage — the member's own posts */
    mine: () => c.get<Opportunity[]>("/v1/opportunities/mine"),
    minePage: (page: PageParams = {}) => c.get<Page<Opportunity>>("/v1/opportunities/mine/page", { ...page }),
    /** createOpportunity */
    create: <T = { id: string }>(body: Record<string, unknown>) => c.post<T>("/v1/opportunities", body),
    /** updateOpportunity (poster) */
    update: <T = Opportunity>(id: string, patch: Record<string, unknown>) => c.patch<T>(base(id), patch),
    /** shareOpportunity — records a share */
    share: (id: string, body?: Record<string, unknown>) => c.post<unknown>(`${base(id)}/share`, body),
    /** saveOpportunity / unsaveOpportunity */
    save: (id: string) => c.post<unknown>(`${base(id)}/save`),
    unsave: (id: string) => c.delete<unknown>(`${base(id)}/save`),
    /** markOpportunityNotInterested */
    notInterested: (id: string, reason: NotInterestedReason) => c.post<unknown>(`${base(id)}/not-interested`, { reason }),
    /** recordOpportunityExternalOpen — the member followed the link to the public source */
    externalOpen: (id: string) => c.post<unknown>(`${base(id)}/external-open`),
    /** Poster lifecycle */
    pause: (id: string) => c.post<unknown>(`${base(id)}/pause`),
    resume: (id: string) => c.post<unknown>(`${base(id)}/resume`),
    renew: (id: string) => c.post<unknown>(`${base(id)}/renew`),
    close: (id: string) => c.post<unknown>(`${base(id)}/close`),
    publish: (id: string) => c.post<unknown>(`${base(id)}/publish`),
    /** confirmOpportunityFields — the poster confirms extracted draft fields */
    confirm: (id: string, fields: string[]) => c.patch<unknown>(`${base(id)}/confirm`, { fields }),
  };
}

export function feedApi(c: VyaparClient) {
  return {
    /** listOpportunityFeed — the five Discover sections for the caller */
    get: (params: FeedParams = {}) => c.get<FeedResponse>("/v1/opportunities/feed", { skills: params.skills }),
    /** listOpportunityFeedSection — every item in one section ("See all") */
    section: <T = { key: string; items: OpportunityCard[] }>(key: string) =>
      c.get<T>(`/v1/opportunities/feed/section/${seg(key)}`),
    /** listOpportunityFeedSectionPage — cursor-paginated */
    sectionPage: (key: string, page: PageParams = {}) =>
      c.get<Page<OpportunityCard>>(`/v1/opportunities/feed/section/${seg(key)}/page`, { ...page }),
  };
}

export type OpportunitiesApi = ReturnType<typeof opportunitiesApi>;
export type FeedApi = ReturnType<typeof feedApi>;
