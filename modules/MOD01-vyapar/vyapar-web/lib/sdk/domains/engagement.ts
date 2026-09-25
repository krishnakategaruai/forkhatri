// [IMP38 — Refactor C] Enquiries, activity, reviews, partnerships, reports,
// notifications — everything a member does with another member.
import { seg, type VyaparClient } from "../client";
import type { ActivityResponse, EnquiryDetail, EnquiryRole, EnquirySummary, Notification, Page, PageParams } from "../types";

export function enquiriesApi(c: VyaparClient) {
  const base = (id: string) => `/v1/enquiries/${seg(id)}`;
  return {
    /** listMyEnquiries */
    mine: (role: EnquiryRole) => c.get<EnquirySummary[]>("/v1/enquiries/mine", { role }),
    /** listMyEnquiriesPage — cursor-paginated */
    minePage: (role: EnquiryRole, page: PageParams = {}) => c.get<Page<EnquirySummary>>("/v1/enquiries/mine/page", { role, ...page }),
    /** getEnquiry */
    get: (id: string) => c.get<EnquiryDetail>(base(id)),
    /** createEnquiry */
    create: <T = { id: string }>(body: Record<string, unknown>) => c.post<T>("/v1/enquiries", body),
    /** replyToEnquiry */
    sendMessage: <T = unknown>(id: string, body: { body: string; attachment_url?: string | null; [k: string]: unknown }) =>
      c.post<T>(`${base(id)}/messages`, body),
    accept: (id: string, body?: Record<string, unknown>) => c.post<unknown>(`${base(id)}/accept`, body),
    resolve: (id: string, body?: Record<string, unknown>) => c.post<unknown>(`${base(id)}/resolve`, body),
    close: (id: string, body?: Record<string, unknown>) => c.post<unknown>(`${base(id)}/close`, body),
    withdraw: (id: string, body?: Record<string, unknown>) => c.post<unknown>(`${base(id)}/withdraw`, body),
    restrict: (id: string, body?: Record<string, unknown>) => c.post<unknown>(`${base(id)}/restrict`, body),
    referToCounsel: (id: string, body?: Record<string, unknown>) => c.post<unknown>(`${base(id)}/refer-to-counsel`, body),
    /** blockMember */
    block: (blockedId: string) => c.post<unknown>("/v1/enquiries/block", { blocked_id: blockedId }),
  };
}

export function activityApi(c: VyaparClient) {
  return {
    /** getActivity — the caller's grouped Saved / Responded / Posted … items */
    get: () => c.get<ActivityResponse>("/v1/activity"),
  };
}

export function notificationsApi(c: VyaparClient) {
  return {
    list: () => c.get<Notification[]>("/v1/notifications"),
    /** listNotificationsPage */
    listPage: (page: PageParams = {}) => c.get<Page<Notification>>("/v1/notifications/page", { ...page }),
    unreadCount: () => c.get<{ count: number }>("/v1/notifications/unread-count"),
    markAllRead: () => c.post<unknown>("/v1/notifications/read-all"),
  };
}

export function reviewsApi(c: VyaparClient) {
  return {
    invite: <T = unknown>(interactionKind: string, interactionId: string) =>
      c.get<T>(`/v1/reviews/invite/${seg(interactionKind)}/${seg(interactionId)}`),
    create: <T = unknown>(body: Record<string, unknown>) => c.post<T>("/v1/reviews", body),
    dispute: <T = unknown>(reviewId: string, body?: Record<string, unknown>) => c.post<T>(`/v1/reviews/${seg(reviewId)}/dispute`, body),
  };
}

export function partnershipsApi(c: VyaparClient) {
  return {
    create: <T = { id: string }>(body: Record<string, unknown>) => c.post<T>("/v1/partnership-requests", body),
    /** listMyPartnershipRequests / listMyPartnershipRequestsPage */
    mine: <T = unknown[]>() => c.get<T>("/v1/partnership-requests/mine"),
    minePage: <T = unknown>(page: PageParams = {}) => c.get<Page<T>>("/v1/partnership-requests/mine/page", { ...page }),
    get: <T = unknown>(id: string) => c.get<T>(`/v1/partnership-requests/${seg(id)}`),
    /** accept | decline | withdraw … */
    act: <T = unknown>(id: string, action: string) => c.post<T>(`/v1/partnership-requests/${seg(id)}/${seg(action)}`),
  };
}

export function trustSafetyApi(c: VyaparClient) {
  return {
    /** createReport — send an Idempotency-Key so a retried tap never files twice */
    report: <T = { received: boolean; block_member_id: string | null }>(body: Record<string, unknown>, idempotencyKey?: string) =>
      c.post<T>("/v1/reports", body, { idempotencyKey }),
    moderationOutcomes: <T = unknown[]>() => c.get<T>("/v1/moderation/outcomes"),
    appeal: <T = unknown>(body: { case_id: string; text: string; evidence_urls?: string[] }) => c.post<T>("/v1/appeals", body),
  };
}

export type EnquiriesApi = ReturnType<typeof enquiriesApi>;
export type ActivityApi = ReturnType<typeof activityApi>;
export type NotificationsApi = ReturnType<typeof notificationsApi>;
