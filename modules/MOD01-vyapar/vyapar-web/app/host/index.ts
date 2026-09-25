// [IMP38 — Refactor C] Host adapter public surface.
export { HostProvider, useHost, useRoutes, selectHost } from "./HostProvider";
export { forkhatriHost } from "./forkhatri";
export { standaloneHost } from "./standalone";
export { defaultRoutes, vyaparInbox } from "./routes";
export type { HostConfig, HostId, NotificationSource, VyaparRoutes } from "./types";
