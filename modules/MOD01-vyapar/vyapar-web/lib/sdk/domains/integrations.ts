// [IMP38 — Refactor C] Integrations (workstream B's /v1/integrations/*):
// personal access tokens that let an external system or AI agent act for a
// member with scoped, revocable credentials, and outbound webhooks.
// Plain secrets (`token`, `secret`) come back exactly once, at creation.
import { seg, type VyaparClient } from "../client";
import type { AccessToken, AccessTokenCreated, Webhook, WebhookCreated, WebhookDelivery, WebhookEventType } from "../types";

export function integrationsApi(c: VyaparClient) {
  return {
    /** getIntegrationIdentity — who the current credential acts as, and how it authenticated */
    me: <T = Record<string, unknown>>() => c.get<T>("/v1/integrations/me"),
    /** listAccessTokenScopes */
    scopes: <T = { scope: string; description?: string }[]>() => c.get<T>("/v1/integrations/scopes"),
    /** listAccessTokens / createAccessToken / revokeAccessToken */
    tokens: () => c.get<AccessToken[]>("/v1/integrations/tokens"),
    createToken: (body: { name: string; scopes: string[]; expires_in_days?: number }) =>
      c.post<AccessTokenCreated>("/v1/integrations/tokens", body),
    revokeToken: (tokenId: string) => c.delete<unknown>(`/v1/integrations/tokens/${seg(tokenId)}`),
    /** listWebhookEventTypes */
    webhookEvents: () => c.get<WebhookEventType[]>("/v1/integrations/webhooks/events"),
    /** listWebhookSubscriptions / createWebhookSubscription / deleteWebhookSubscription */
    webhooks: () => c.get<Webhook[]>("/v1/integrations/webhooks"),
    createWebhook: (body: { url: string; event_types: string[]; description?: string; all_events?: boolean }) =>
      c.post<WebhookCreated>("/v1/integrations/webhooks", body),
    deleteWebhook: (subscriptionId: string) => c.delete<unknown>(`/v1/integrations/webhooks/${seg(subscriptionId)}`),
    /** testWebhookSubscription */
    testWebhook: <T = unknown>(subscriptionId: string) => c.post<T>(`/v1/integrations/webhooks/${seg(subscriptionId)}/test`),
    /** listWebhookDeliveries */
    deliveries: (subscriptionId: string) => c.get<WebhookDelivery[]>(`/v1/integrations/webhooks/${seg(subscriptionId)}/deliveries`),
  };
}

export type IntegrationsApi = ReturnType<typeof integrationsApi>;
