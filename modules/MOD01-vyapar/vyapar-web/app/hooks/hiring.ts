"use client";

// [FE1 — 2026-09-28] Data hooks for the hiring surfaces. Thin named
// wrappers over useResource + the SDK in scope (REFACTOR-PLAN.md §C: pages
// state WHAT they need; presentational components never fetch). All of them
// re-fetch on a live language switch, because every label in these
// responses (skills, reasons, tips) is translated by the server.
import type { ApplicantPage, ApplicantStage, Badge, TaxonomyTree } from "@/lib/sdk";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "./useResource";

/** The two-level category → skill/role tree. */
export function useTaxonomyTree() {
  const sdk = useSdk();
  return useResource<TaxonomyTree>(() => sdk.taxonomy.tree(), [sdk]);
}

/**
 * slug → English name for every skill/role, so the picker's search finds
 * "driver" or "mali" while the app is in Hindi or Telugu. Not fetched when
 * the app is already in English (the labels are English then).
 */
export function useTaxonomyAliases() {
  const sdk = useSdk();
  const { i18n } = useTranslation();
  const res = useResource<TaxonomyTree>(
    () => sdk.client.get<TaxonomyTree>("/v1/taxonomy/tree", undefined, { headers: { "X-Vyapar-Language": "en" } }),
    [sdk],
    { enabled: i18n.language !== "en", language: false },
  );
  return useMemo(() => {
    const m = new Map<string, string>();
    for (const c of res.data?.categories ?? []) for (const s of c.children ?? []) m.set(s.slug, s.label);
    return m;
  }, [res.data]);
}

/** Applicants on one opportunity (poster only), for a stage tab and sort. */
export function useApplicants(opportunityId: string, stage: ApplicantStage, sort: "newest" | "match") {
  const sdk = useSdk();
  return useResource<ApplicantPage>(
    () => sdk.applicants.list(opportunityId, { stage, sort, limit: 100 }),
    [opportunityId, stage, sort, sdk],
  );
}

/** Only the per-stage counts (the poster's summary on the opportunity page). */
export function useApplicantCounts(opportunityId: string, enabled = true) {
  const sdk = useSdk();
  return useResource<ApplicantPage>(() => sdk.applicants.list(opportunityId, { limit: 1 }), [opportunityId, sdk], {
    enabled,
    language: false,
  });
}

/** Earned badges for a set of members, keyed by member id. Missing members map to []. */
export function useMemberBadges(memberIds: readonly string[]) {
  const sdk = useSdk();
  const key = [...new Set(memberIds)].sort().join(",");
  return useResource<Record<string, Badge[]>>(
    async () => {
      const ids = key ? key.split(",") : [];
      const rows = await Promise.all(
        ids.map((id) =>
          sdk.badges
            .forMember(id)
            .then((r) => [id, r.badges] as const)
            .catch(() => [id, [] as Badge[]] as const),
        ),
      );
      return Object.fromEntries(rows);
    },
    [key, sdk],
    { enabled: key.length > 0, fallback: {} },
  );
}

/** Contacts disclosed on an accepted thread (after Hire). Empty until then. */
export function useDisclosedContacts(enquiryId: string | null, enabled: boolean) {
  const sdk = useSdk();
  return useResource<{ channel: string; value: string }[]>(
    async () => (await sdk.enquiries.get(enquiryId as string)).disclosed_contacts ?? [],
    [enquiryId, sdk],
    { enabled: enabled && !!enquiryId, language: false, fallback: [] },
  );
}

/**
 * The viewer's own live response to an opportunity (not withdrawn), so the
 * detail page shows "Applied · Open conversation" instead of a second Apply
 * (critique L12). Null while loading, or when there is none.
 */
export function useMyResponse(opportunityId: string, enabled: boolean) {
  const sdk = useSdk();
  return useResource<{ id: string; stage: string | null; state: string } | null>(
    async () => {
      const rows = await sdk.client.get<{ id: string; opportunity_id: string | null; state: string; stage?: string | null }[]>(
        "/v1/enquiries/mine",
        { role: "sent" },
      );
      const mine = rows.find((r) => r.opportunity_id === opportunityId && r.state !== "withdrawn");
      return mine ? { id: mine.id, stage: mine.stage ?? null, state: mine.state } : null;
    },
    [opportunityId, sdk],
    { enabled, language: false, fallback: null },
  );
}
