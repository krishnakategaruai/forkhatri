// [IMP38 — Refactor C] ForKhatri host — today's behaviour, and the default.
//
// Everything ForKhatri-specific that used to be written straight into the
// shell lives here: the development member switcher in the top-right
// corner (the stand-in for the platform's avatar until the fk_session
// cookie is wired in), the "Back to ForKhatri" link to the platform
// entrance, and the "Vyapar ForKhatri" rail brand.
import type { HostConfig } from "./types";
import { defaultRoutes, vyaparInbox } from "./routes";
import DevMemberSwitcher from "@/app/components/DevMemberSwitcher";

export const forkhatriHost: HostConfig = {
  id: "forkhatri",
  brand: { name: "Vyapar", qualifier: "ForKhatri" },
  AccountControl: DevMemberSwitcher,
  // No hardcoded fallback (environment values live in .env): without
  // NEXT_PUBLIC_PLATFORM_URL the way-back links are simply not shown.
  platformLink: process.env.NEXT_PUBLIC_PLATFORM_URL
    ? { href: process.env.NEXT_PUBLIC_PLATFORM_URL, labelKey: "profile:backToForKhatri" }
    : null,
  notifications: vyaparInbox,
  routes: defaultRoutes,
};
