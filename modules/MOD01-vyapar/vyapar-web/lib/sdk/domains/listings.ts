// [IMP38 — Refactor C] Business and professional profiles (listings),
// directory search, reviews and verification.
import { seg, type VyaparClient } from "../client";
import type {
  Listing,
  ListingContact,
  ListingSearchParams,
  Page,
  PageParams,
  ProfileCardData,
  SearchResponse,
  SearchSuggestions,
} from "../types";

export function listingsApi(c: VyaparClient) {
  const base = (id: string) => `/v1/listings/${seg(id)}`;
  return {
    /** getListing */
    get: <T = Listing>(id: string) => c.get<T>(base(id)),
    /** listSimilarProfiles — "Similar profiles" */
    similar: (id: string) => c.get<ProfileCardData[]>(`${base(id)}/similar`),
    /** searchListings — the Businesses & Professionals directory */
    search: (params: ListingSearchParams) => c.get<SearchResponse>("/v1/listings/search", params),
    /** getSearchSuggestions */
    searchSuggestions: <T = SearchSuggestions>() => c.get<T>("/v1/listings/search-suggestions"),
    /** listMyListings */
    mine: <T = Listing[]>() => c.get<T>("/v1/listings/mine"),
    /** listMyListingsPage */
    minePage: (page: PageParams = {}) => c.get<Page<Listing>>("/v1/listings/mine/page", { ...page }),
    /** createListing */
    create: <T = { id: string }>(body: Record<string, unknown>) => c.post<T>("/v1/listings", body),
    save: (id: string) => c.post<unknown>(`${base(id)}/save`),
    unsave: (id: string) => c.delete<unknown>(`${base(id)}/save`),
    submit: (id: string) => c.post<unknown>(`${base(id)}/submit`),
    archive: (id: string) => c.post<unknown>(`${base(id)}/archive`),
    /** updateListingContacts — per-channel disclosure */
    updateContacts: (id: string, contacts: ListingContact[]) => c.patch<unknown>(`${base(id)}/contacts`, { contacts }),
    /** setListingVisibility */
    setVisibility: (id: string, discoverable: boolean, confirmNoReach = false) =>
      c.patch<unknown>(`${base(id)}/visibility`, { discoverable, confirm_no_reach: confirmNoReach }),
    /** updateListingIntent — capability and seeking visibility, kept separate */
    updateIntent: (id: string, patch: { capability_visible?: boolean; intent_visible?: boolean; intent_state?: string | null }) =>
      c.patch<unknown>(`${base(id)}/intent`, patch),
    /** attachCredentialRef */
    attachCredential: (id: string) => c.post<unknown>(`${base(id)}/credential-ref/attach`),
    /** requestListingOtp / verifyListingOtp — contact verification before submit */
    requestOtp: (id: string, phone: string) => c.post<{ dev_code: string }>(`${base(id)}/otp/request`, { phone }),
    verifyOtp: (id: string, code: string) => c.post<unknown>(`${base(id)}/otp/verify`, { code }),
    /** listListingReviews */
    reviews: <T = unknown[]>(id: string) => c.get<T>(`${base(id)}/reviews`),
    /** listListingReviewsPage */
    reviewsPage: <T = unknown>(id: string, page: PageParams = {}) => c.get<Page<T>>(`${base(id)}/reviews/page`, { ...page }),
    /** listVerificationRecords / requestVerification */
    verification: <T = unknown[]>(id: string) => c.get<T>(`${base(id)}/verification`),
    requestVerification: <T = unknown>(id: string, body: Record<string, unknown>) => c.post<T>(`${base(id)}/verification`, body),
  };
}

export type ListingsApi = ReturnType<typeof listingsApi>;
