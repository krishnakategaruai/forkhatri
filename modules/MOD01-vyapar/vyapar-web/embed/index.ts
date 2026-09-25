// [IMP38 — Refactor C] Embeddable Vyapar surfaces. See README.md.
//
//   <VyaparEmbedProvider sdk={createVyaparSdk({...})} language="hi">
//     <OpportunityDetailPanel opportunityId={id} />
//   </VyaparEmbedProvider>
export { default as VyaparEmbedProvider } from "./VyaparEmbedProvider";
export type { VyaparEmbedProviderProps } from "./VyaparEmbedProvider";
export { default as OpportunityDetailPanel } from "./OpportunityDetailPanel";
export type { OpportunityDetailPanelProps } from "./OpportunityDetailPanel";
export { default as OpportunityCard } from "@/app/components/opportunity/OpportunityCard";
export type { OpportunityCardItem, OpportunityCardVariant } from "@/app/components/opportunity/OpportunityCard";
export { default as ProfileRecommendations, ProfileRecommendationsView } from "@/app/components/ProfileRecommendations";

// Building blocks for hosts that compose their own surfaces.
export { default as OpportunityDetailView } from "@/app/components/opportunity/OpportunityDetailView";
export { useOpportunityDetailController } from "@/app/components/opportunity/useOpportunityDetailController";
export * from "@/app/hooks";
export { HostProvider, useHost, useRoutes, forkhatriHost, standaloneHost, defaultRoutes, vyaparInbox } from "@/app/host";
export type { HostConfig, VyaparRoutes, NotificationSource } from "@/app/host";
export { VyaparSdkProvider, useSdk } from "@/lib/sdk/react";
export {
  createVyaparSdk,
  devHeaderAuth,
  cookieSessionAuth,
  bearerTokenAuth,
  anonymousAuth,
  ApiError,
} from "@/lib/sdk";
export type { VyaparSdk, AuthStrategy } from "@/lib/sdk";
