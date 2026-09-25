"use client";

// [IMP38 — Refactor C] Listing (business / professional profile) and
// directory-search data hooks.
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Listing, ListingSearchParams, SearchResponse } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "./useResource";

export function useListing(id: string) {
  const sdk = useSdk();
  return useResource<Listing>(() => sdk.listings.get(id), [id, sdk]);
}

/**
 * Directory search, run on demand (the Businesses screen searches when the
 * member submits, not on mount). The last search is re-run on a live
 * language switch so category and skill labels follow the new language.
 */
export function useListingSearch() {
  const sdk = useSdk();
  const { i18n } = useTranslation();
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const last = useRef<ListingSearchParams | null>(null);
  const seq = useRef(0);

  const search = useCallback(
    async (params: ListingSearchParams) => {
      last.current = params;
      const mine = ++seq.current;
      setLoading(true);
      try {
        const res = await sdk.listings.search(params);
        if (mine === seq.current) setResponse(res);
      } finally {
        if (mine === seq.current) setLoading(false);
      }
    },
    [sdk],
  );

  const firstLang = useRef(i18n.language);
  useEffect(() => {
    if (i18n.language === firstLang.current) return;
    firstLang.current = i18n.language;
    if (last.current) void search(last.current).catch(() => {});
  }, [i18n.language, search]);

  return { response, loading, search };
}
