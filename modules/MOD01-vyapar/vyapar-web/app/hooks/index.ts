// [IMP38 — Refactor C] Data hooks: screens and embeddable components state
// what they need; these fetch it through the SDK in scope and re-fetch on a
// live language switch.
export { useResource } from "./useResource";
export type { Resource, ResourceOptions } from "./useResource";
export {
  useOpportunity,
  useSimilarOpportunities,
  useOpportunityWhy,
  useFirstRunState,
  useFeed,
  useProfileRecommendations,
} from "./opportunities";
export { useListing, useListingSearch } from "./listings";
export { useEnquiries, useActivity } from "./engagement";
