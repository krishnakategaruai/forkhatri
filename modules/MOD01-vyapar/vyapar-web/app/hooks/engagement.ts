"use client";

// [IMP38 — Refactor C] Enquiries and Activity data hooks.
import type { ActivityResponse, EnquiryRole, EnquirySummary } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "./useResource";

/** The caller's sent or received enquiries. */
export function useEnquiries(role: EnquiryRole) {
  const sdk = useSdk();
  return useResource<EnquirySummary[]>(() => sdk.enquiries.mine(role), [role, sdk]);
}

/** The caller's grouped activity (Saved, Responded, Posted …). */
export function useActivity() {
  const sdk = useSdk();
  return useResource<ActivityResponse>(() => sdk.activity.get(), [sdk]);
}
