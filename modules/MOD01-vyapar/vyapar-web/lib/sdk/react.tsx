"use client";

// [IMP38 — Refactor C] React binding for the SDK: one context so every data
// hook and embeddable component reads the SAME instance — the web app's
// default one, or whatever instance an embedding app passes in.
import { createContext, useContext } from "react";
import type { VyaparSdk } from "./index";
import { defaultSdk } from "./default";

const SdkContext = createContext<VyaparSdk | null>(null);

export function VyaparSdkProvider({ sdk, children }: { sdk: VyaparSdk; children: React.ReactNode }) {
  return <SdkContext.Provider value={sdk}>{children}</SdkContext.Provider>;
}

/** The SDK instance in scope; falls back to the web app's default instance. */
export function useSdk(): VyaparSdk {
  return useContext(SdkContext) ?? defaultSdk;
}
