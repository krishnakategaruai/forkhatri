"use client";

// [IMP38 — Refactor C] Opportunity + feed data hooks. Each one is a thin,
// named wrapper over useResource and the SDK in scope, so a screen (or an
// embedding app) states WHAT it needs, never how to fetch it. All of them
// re-fetch on a live language switch (see useResource).
import { useCallback, useState } from "react";
import type { FeedParams, FeedResponse, Opportunity, ProfileCardData, WhyResponse } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "./useResource";

export function useOpportunity(id: string) {
  const sdk = useSdk();
  return useResource<Opportunity>(() => sdk.opportunities.get(id), [id, sdk]);
}

/** Similar opportunities; an empty list when there are none or the call fails. */
export function useSimilarOpportunities(id: string) {
  const sdk = useSdk();
  return useResource<Opportunity[]>(() => sdk.opportunities.similar(id), [id, sdk], { fallback: [] });
}

/**
 * "Why this?" — fetched lazily, only the first time the member asks. Not
 * re-fetched on a language switch: the signals are keys the screen
 * translates itself.
 */
export function useOpportunityWhy(id: string) {
  const sdk = useSdk();
  const [why, setWhy] = useState<WhyResponse | null>(null);
  const load = useCallback(() => {
    if (!why) sdk.opportunities.why(id).then(setWhy);
  }, [why, sdk, id]);
  return { why, load };
}

export function useFirstRunState() {
  const sdk = useSdk();
  return useResource(() => sdk.firstRun.state(), [sdk], { language: false });
}

/** The Discover feed for the given filters. `enabled: false` holds it back (e.g. until first run is done). */
export function useFeed(params: FeedParams, options: { enabled?: boolean } = {}) {
  const sdk = useSdk();
  const skillsKey = (params.skills ?? []).join(",");
  return useResource<FeedResponse>(() => sdk.feed.get(params), [skillsKey, sdk], { enabled: options.enabled });
}

/** Profiles recommended by any SDK call (similar profiles, matching profiles…). Empty on failure. */
export function useProfileRecommendations(load: () => Promise<ProfileCardData[]>, key: string) {
  return useResource<ProfileCardData[]>(load, [key], { fallback: [] });
}
