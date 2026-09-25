// [IMP38 — Refactor C] Vyapar web SDK — typed client for the Vyapar API.
//
//   const sdk = createVyaparSdk({
//     baseUrl: "https://vyapar.example.com",
//     auth: bearerTokenAuth(() => myTokenStore.get()),
//     language: () => currentLanguage,
//   });
//   const opp = await sdk.opportunities.get(id);
//
// Framework-free (plain fetch); React bindings live in ./react. The web
// app's default instance (configured from NEXT_PUBLIC_* env) is in
// ./default, and lib/api.ts remains as a thin compatibility shim over it.
import { VyaparClient, type VyaparClientConfig } from "./client";
import { opportunitiesApi, feedApi } from "./domains/opportunities";
import { listingsApi } from "./domains/listings";
import {
  activityApi,
  enquiriesApi,
  notificationsApi,
  partnershipsApi,
  reviewsApi,
  trustSafetyApi,
} from "./domains/engagement";
import { devApi, eventsApi, firstRunApi, membersApi, preferencesApi, privacyApi, uploadsApi, workspaceApi } from "./domains/account";
import { adminApi, commercialApi } from "./domains/commercial";
import { integrationsApi } from "./domains/integrations";

export function createVyaparSdk(config: VyaparClientConfig | VyaparClient) {
  const client = config instanceof VyaparClient ? config : new VyaparClient(config);
  return {
    /** Low-level transport, for endpoints not wrapped yet. */
    client,
    opportunities: opportunitiesApi(client),
    feed: feedApi(client),
    listings: listingsApi(client),
    enquiries: enquiriesApi(client),
    activity: activityApi(client),
    notifications: notificationsApi(client),
    reviews: reviewsApi(client),
    partnerships: partnershipsApi(client),
    trustSafety: trustSafetyApi(client),
    members: membersApi(client),
    firstRun: firstRunApi(client),
    privacy: privacyApi(client),
    preferences: preferencesApi(client),
    workspace: workspaceApi(client),
    commercial: commercialApi(client),
    admin: adminApi(client),
    uploads: uploadsApi(client),
    events: eventsApi(client),
    integrations: integrationsApi(client),
    dev: devApi(client),
  };
}

export type VyaparSdk = ReturnType<typeof createVyaparSdk>;

export { VyaparClient, buildQuery } from "./client";
export type { VyaparClientConfig, RequestOptions, Query, HttpMethod } from "./client";
export { ApiError, toApiError } from "./errors";
export type { ErrorEnvelope } from "./errors";
export {
  devHeaderAuth,
  cookieSessionAuth,
  bearerTokenAuth,
  anonymousAuth,
  getDevMemberId,
  setDevMemberId,
  DEV_MEMBER_STORAGE_KEY,
} from "./auth";
export type { AuthStrategy, AuthRequest, TokenSource } from "./auth";
export * from "./types";
