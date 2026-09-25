// [IMP38 — Refactor C] The host adapter contract.
//
// Vyapar's core screens never name the platform they run inside. Anything
// a host platform owns — who the member is and how they switch account, the
// way back to the platform, the brand line, where the notification bell's
// items come from, and the URLs of Vyapar's own screens inside that host —
// is supplied through this one interface. `forkhatri` (today's behaviour,
// the default) and `standalone` are the two implementations shipped; a new
// host adds a third file, not edits to pages.
import type { ComponentType } from "react";
import type { Notification, VyaparSdk } from "@/lib/sdk";

export type HostId = "forkhatri" | "standalone";

/** Where the notification bell's inbox comes from. */
export interface NotificationSource {
  unreadCount(): Promise<number>;
  list(): Promise<Notification[]>;
  markAllRead(): Promise<void>;
}

/** URLs of Vyapar's own screens, so an embedding host can mount them under its own paths. */
export interface VyaparRoutes {
  home: string;
  opportunity(id: string): string;
  listing(id: string): string;
  enquireOpportunity(opportunityId: string): string;
  enquireListing(listingId: string): string;
  enquiry(id: string): string;
  boost(kind: "opportunity" | "listing", id: string): string;
  workspace(listingId: string): string;
  proposePartnership(listingId: string): string;
  partnership(id: string): string;
  feedSection(key: string): string;
  businesses(query?: string): string;
  post: string;
  newListing: string;
  myListings: string;
}

export interface HostConfig {
  id: HostId | string;
  /** Rail brand: product name plus an optional host qualifier (proper nouns, not translated). */
  brand: { name: string; qualifier: string | null };
  /** Account control in the top-right corner (the development member switcher on ForKhatri). Null hides it. */
  AccountControl: ComponentType | null;
  /** A link back to the host platform on the Profile screen. `labelKey` is an i18n key. Null hides it. */
  platformLink: { href: string; labelKey: string } | null;
  /** Notification bell source, built from the SDK in scope. Null hides the bell. */
  notifications: ((sdk: VyaparSdk) => NotificationSource) | null;
  routes: VyaparRoutes;
}
