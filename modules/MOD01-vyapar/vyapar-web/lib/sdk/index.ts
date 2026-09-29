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
// [FE2] contact control, packages, saved searches, badges, seeker protection, contracts
// and the taxonomy tree (shared with FE1's hiring screens)
import { contactApi } from "./domains/contact";
import { packagesApi } from "./domains/packages";
import { savedSearchesApi } from "./domains/savedSearches";
import { badgesApi, seekerProtectionApi } from "./domains/trust";
import { contractsApi } from "./domains/contracts";
import { taxonomyApi } from "./domains/taxonomy";
import { aiApi, applicantsApi, postingApi, responsesApi } from "./domains/hiring";

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
    contact: contactApi(client),
    packages: packagesApi(client),
    savedSearches: savedSearchesApi(client),
    badges: badgesApi(client),
    seekerProtection: seekerProtectionApi(client),
    contracts: contractsApi(client),
    taxonomy: taxonomyApi(client),
    /** [FE1] typed opportunity writes (structured fields) + posting suggestions */
    posting: postingApi(client),
    /** [FE1] structured responses: one-tap apply, proposals, quotes */
    responses: responsesApi(client),
    /** [FE1] the poster's applicant pipeline */
    applicants: applicantsApi(client),
    /** [FE1] AI assistance: drafts, photo reading, shortlist, posting tips, proposal help */
    ai: aiApi(client),
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
export type * from "./domains/contact";
export type * from "./domains/packages";
export type * from "./domains/savedSearches";
export type * from "./domains/trust";
export type * from "./domains/contracts";
export type * from "./domains/taxonomy";
export * from "./hiring-types";
