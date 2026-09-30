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
  ResultsResponse,
  RowsResponse,
  TasteResponse,
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
    /** [Recommendations] moreLikeThis — show more posts like this one */
    moreLikeThis: (id: string) => c.post<TasteResponse>(`${base(id)}/more-like-this`),
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

function feedQuery(params: FeedParams) {
  return {
    skills: params.skills,
    q: params.q,
    type: params.type,
    work_mode: params.work_mode,
    radius_km: params.radius_km,
    availability: params.availability,
    // "relevance" is the server default; leaving it out keeps URLs short
    sort: params.sort && params.sort !== "relevance" ? params.sort : undefined,
    types: params.types,
    pay_kind: params.pay_kind,
    pay_min_paise: params.pay_min_paise,
    pay_max_paise: params.pay_max_paise,
    posted_within: params.posted_within,
    shift: params.shift,
    experience: params.experience,
    verified_only: params.verified_only || undefined,
    segment: params.segment,
  };
}

export function feedApi(c: VyaparClient) {
  return {
    /** listOpportunityFeed — the five Discover sections for the caller */
    // [FE2 — imp-backend-b §5] every route takes the same filter query
    // (skills, q, type, work_mode, radius_km, availability, sort); empty
    // values are dropped by buildQuery, so an unfiltered call is unchanged.
    get: (params: FeedParams = {}) => c.get<FeedResponse>("/v1/opportunities/feed", feedQuery(params)),
    /** [FE2] listOpportunityResults — a search or any filter: one ranked list, total, facet counts */
    results: (params: FeedParams = {}, limit = 60) => c.get<ResultsResponse>("/v1/opportunities/feed/results", { ...feedQuery(params), limit }),
    /** [FE2] listOpportunityRows — the unfiltered home as themed rows */
    rows: () => c.get<RowsResponse>("/v1/opportunities/feed/rows"),
    /** listOpportunityFeedSection — every item in one section ("See all") */
    section: <T = OpportunityCard[]>(key: string, params: FeedParams = {}) =>
      c.get<T>(`/v1/opportunities/feed/section/${seg(key)}`, feedQuery(params)),
    /** listOpportunityFeedSectionPage — cursor-paginated */
    sectionPage: (key: string, page: PageParams = {}, params: FeedParams = {}) =>
      c.get<Page<OpportunityCard>>(`/v1/opportunities/feed/section/${seg(key)}/page`, { ...feedQuery(params), ...page }),
  };
}

export type OpportunitiesApi = ReturnType<typeof opportunitiesApi>;
export type FeedApi = ReturnType<typeof feedApi>;
