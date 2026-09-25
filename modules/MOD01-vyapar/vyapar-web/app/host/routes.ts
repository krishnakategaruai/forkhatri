// [IMP38 — Refactor C] Vyapar's own screen URLs as the standalone web app
// serves them. Hosts that mount Vyapar elsewhere override these.
import type { NotificationSource, VyaparRoutes } from "./types";
import type { VyaparSdk } from "@/lib/sdk";

export const defaultRoutes: VyaparRoutes = {
  home: "/",
  opportunity: (id) => `/opportunities/${id}`,
  listing: (id) => `/listings/${id}`,
  enquireOpportunity: (id) => `/enquiries/new?opportunity_id=${id}`,
  enquireListing: (id) => `/enquiries/new?listing_id=${id}`,
  enquiry: (id) => `/enquiries/${id}`,
  boost: (kind, id) => `/boost/${kind}/${id}`,
  workspace: (listingId) => `/workspace/${listingId}`,
  proposePartnership: (listingId) => `/partnerships/new?listing_id=${listingId}`,
  partnership: (id) => `/partnerships/${id}`,
  feedSection: (key) => `/opportunities/section/${key}`,
  businesses: (query) => (query !== undefined ? `/businesses?${query}` : "/businesses"),
  post: "/post",
  newListing: "/listings/new",
  myListings: "/listings/mine",
};

/** Vyapar's own in-app inbox — the bell source both shipped hosts use. */
export function vyaparInbox(sdk: VyaparSdk): NotificationSource {
  return {
    unreadCount: async () => (await sdk.notifications.unreadCount()).count,
    list: () => sdk.notifications.list(),
    markAllRead: async () => {
      await sdk.notifications.markAllRead();
    },
  };
}
