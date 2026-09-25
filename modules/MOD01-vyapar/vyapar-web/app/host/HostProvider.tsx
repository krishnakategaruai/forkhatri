"use client";

// [IMP38 — Refactor C] Host context. The root layout mounts <HostProvider>
// with no props and gets the host named by NEXT_PUBLIC_VYAPAR_HOST
// ("forkhatri" by default, or "standalone"). An embedding app passes its
// own `host` object instead. Components read it with useHost()/useRoutes().
import { createContext, useContext } from "react";
import type { HostConfig, VyaparRoutes } from "./types";
import { forkhatriHost } from "./forkhatri";
import { standaloneHost } from "./standalone";
import { HOST_ID } from "./meta";

export function selectHost(id: string | undefined = HOST_ID): HostConfig {
  return id === "standalone" ? standaloneHost : forkhatriHost;
}

const HostContext = createContext<HostConfig | null>(null);

export function HostProvider({ host, children }: { host?: HostConfig; children: React.ReactNode }) {
  return <HostContext.Provider value={host ?? selectHost()}>{children}</HostContext.Provider>;
}

export function useHost(): HostConfig {
  return useContext(HostContext) ?? selectHost();
}

export function useRoutes(): VyaparRoutes {
  return useHost().routes;
}
