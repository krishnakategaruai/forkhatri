// [IMP38 — Refactor C] Paid features (boosts, campaigns, entitlements,
// payments, performance) and operator (admin) tools.
import { seg, type Query, type VyaparClient } from "../client";

type Body = Record<string, unknown>;

export function commercialApi(c: VyaparClient) {
  return {
    promotionOptions: <T = unknown>(targetKind: string, targetId: string) =>
      c.get<T>("/v1/promotions/options", { target_kind: targetKind, target_id: targetId }),
    createPromotion: <T = unknown>(body: Body) => c.post<T>("/v1/promotions", body),
    myPromotions: <T = unknown[]>() => c.get<T>("/v1/promotions/mine"),
    myPromotionsPage: <T = unknown>(page: { limit?: number; cursor?: string | null } = {}) =>
      c.get<{ items: T[]; next_cursor?: string | null }>("/v1/promotions/mine/page", { ...page }),
    getPromotion: <T = unknown>(id: string) => c.get<T>(`/v1/promotions/${seg(id)}`),
    cancelPromotion: <T = unknown>(id: string) => c.post<T>(`/v1/promotions/${seg(id)}/cancel`),
    confirmPromotionPurchase: <T = unknown>(id: string, body?: Body) => c.post<T>(`/v1/promotions/${seg(id)}/confirm-purchase`, body),
    campaignOptions: <T = unknown>(listingId: string) => c.get<T>("/v1/campaigns/options", { listing_id: listingId }),
    createCampaign: <T = unknown>(body: Body) => c.post<T>("/v1/campaigns", body),
    getCampaign: <T = unknown>(id: string) => c.get<T>(`/v1/campaigns/${seg(id)}`),
    confirmCampaignPurchase: <T = unknown>(id: string, body?: Body) => c.post<T>(`/v1/campaigns/${seg(id)}/confirm-purchase`, body),
    setCampaignItemsState: <T = unknown>(id: string, body: Body) => c.post<T>(`/v1/campaigns/${seg(id)}/items-state`, body),
    createEntitlement: <T = unknown>(body: Body) => c.post<T>("/v1/entitlements", body),
    confirmEntitlementPurchase: <T = unknown>(id: string, body?: Body) => c.post<T>(`/v1/entitlements/${seg(id)}/confirm-purchase`, body),
    setEntitlementRenewal: <T = unknown>(id: string, body: Body) => c.post<T>(`/v1/entitlements/${seg(id)}/renewal`, body),
    getOrder: <T = unknown>(orderId: string) => c.get<T>(`/v1/payments/orders/${seg(orderId)}`),
    simulateOrder: <T = unknown>(orderId: string, body?: Body) => c.post<T>(`/v1/payments/orders/${seg(orderId)}/simulate`, body),
    performance: <T = unknown>(targetKind: string, targetId: string, query?: Query) =>
      c.get<T>(`/v1/performance/${seg(targetKind)}/${seg(targetId)}`, query),
  };
}

export function adminApi(c: VyaparClient) {
  return {
    verificationQueue: <T = unknown[]>() => c.get<T>("/v1/admin/verification-queue"),
    decideVerification: <T = unknown>(id: string, action: string, body?: Body) => c.post<T>(`/v1/admin/verification-queue/${seg(id)}/${seg(action)}`, body),
    moderationQueue: <T = unknown[]>() => c.get<T>("/v1/admin/moderation-queue"),
    decideModerationCase: <T = unknown>(id: string, body: Body) => c.post<T>(`/v1/admin/moderation-cases/${seg(id)}/decide`, body),
    appeals: <T = unknown[]>() => c.get<T>("/v1/admin/appeals"),
    decideAppeal: <T = unknown>(id: string, body: Body) => c.post<T>(`/v1/admin/appeals/${seg(id)}/decide`, body),
    opportunitiesQueue: <T = unknown[]>() => c.get<T>("/v1/admin/opportunities-queue"),
    decideOpportunity: <T = unknown>(id: string, body: Body) => c.post<T>(`/v1/admin/opportunities-queue/${seg(id)}/decide`, body),
    staleQueue: <T = unknown[]>() => c.get<T>("/v1/admin/stale-queue"),
    staleBulk: <T = unknown>(body: Body) => c.post<T>("/v1/admin/stale-queue/bulk", body),
    taxonomy: <T = unknown>() => c.get<T>("/v1/admin/taxonomy"),
    marketplaceHealth: <T = unknown>() => c.get<T>("/v1/admin/marketplace-health"),
    audit: <T = unknown[]>(query?: Query) => c.get<T>("/v1/admin/audit", query),
    commercialOrders: <T = unknown[]>(kind?: string) => c.get<T>("/v1/admin/commercial/orders", { kind }),
    commercialProducts: <T = unknown[]>() => c.get<T>("/v1/admin/commercial/products"),
    createCommercialProduct: <T = unknown>(body: Body) => c.post<T>("/v1/admin/commercial/products", body),
    refund: <T = unknown>(body: Body) => c.post<T>("/v1/admin/commercial/refunds", body),
    commercialDiagnostics: <T = unknown>(kind: string, id: string) => c.get<T>(`/v1/admin/commercial/diagnostics/${seg(kind)}/${seg(id)}`),
  };
}
