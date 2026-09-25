// [IMP38 — Refactor C] Standalone host — Vyapar on its own.
//
// No development member switcher (identity comes from the deployment's own
// session — see lib/sdk/default.ts, which picks cookie auth for this host),
// no link back to a parent platform, and a neutral brand line. Vyapar's own
// in-app inbox still backs the notification bell: the inbox is part of the
// product, not of any host.
import type { HostConfig } from "./types";
import { defaultRoutes, vyaparInbox } from "./routes";

export const standaloneHost: HostConfig = {
  id: "standalone",
  brand: { name: "Vyapar", qualifier: null },
  AccountControl: null,
  platformLink: null,
  notifications: vyaparInbox,
  routes: defaultRoutes,
};
