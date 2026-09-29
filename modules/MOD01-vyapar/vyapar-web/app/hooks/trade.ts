"use client";

// [FE2] Data hooks for contact actions, contact preferences, service
// packages, saved searches and contracts. Presentational components never
// fetch; they take these hooks' data and call the actions they return.
import { useCallback, useState } from "react";
import {
  ApiError,
  type Contract,
  type ContractListParams,
  type ContactActions,
  type ContactChannel,
  type ContactPreferences,
  type ContactPreferencesPatch,
  type ListingContactPreferences,
  type Page,
  type ContractSummary,
  type SavedSearch,
} from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "./useResource";

/** Error text for a failed call: the server's localized message when there is one. */
export function errorText(e: unknown, fallback: string): string {
  // A schema error arrives as a list of field problems, not a sentence: show
  // the friendly fallback rather than raw JSON.
  if (e instanceof ApiError && typeof e.detail === "string" && e.detail) return e.detail;
  return fallback;
}

// ---- contact actions -------------------------------------------------------

/** Call / WhatsApp for an accepted enquiry. `record` logs the tap first and returns the updated actions. */
export function useContactActions(enquiryId: string, enabled: boolean) {
  const sdk = useSdk();
  const res = useResource<ContactActions>(() => sdk.contact.actions(enquiryId), [enquiryId, sdk], { enabled });
  const record = useCallback(
    async (channel: ContactChannel) => {
      const next = await sdk.contact.recordAttempt(enquiryId, channel);
      res.setData(next);
      return next;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [enquiryId, sdk],
  );
  return { ...res, record };
}

// ---- contact preferences ------------------------------------------------------

export function useContactPreferences() {
  const sdk = useSdk();
  const res = useResource<ContactPreferences>(() => sdk.contact.preferences(), [sdk], { language: false });
  const save = useCallback(
    async (patch: ContactPreferencesPatch) => {
      const next = await sdk.contact.updatePreferences(patch);
      res.setData(next);
      return next;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [sdk],
  );
  return { ...res, save };
}

export function useListingContactPreferences(listingId: string, enabled = true) {
  const sdk = useSdk();
  const res = useResource<ListingContactPreferences>(() => sdk.contact.listingPreferences(listingId), [listingId, sdk], {
    enabled,
    language: false,
  });
  const save = useCallback(
    async (patch: ContactPreferencesPatch) => {
      const next = await sdk.contact.updateListingPreferences(listingId, patch);
      res.setData(next);
      return next;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [listingId, sdk],
  );
  return { ...res, save };
}

// ---- saved searches ------------------------------------------------------------

export function useSavedSearches(enabled = true) {
  const sdk = useSdk();
  return useResource<SavedSearch[]>(() => sdk.savedSearches.list(), [sdk], { enabled, language: false });
}

// ---- contracts --------------------------------------------------------------------

export function useContracts(params: ContractListParams) {
  const sdk = useSdk();
  const key = JSON.stringify(params);
  return useResource<Page<ContractSummary>>(() => sdk.contracts.list(params), [key, sdk]);
}

/** One contract plus a runner for its actions: each action returns the new contract, which replaces the old one. */
export function useContract(id: string) {
  const sdk = useSdk();
  const res = useResource<Contract>(() => sdk.contracts.get(id), [id, sdk]);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const run = useCallback(
    async <T,>(fn: () => Promise<T>, fallback: string): Promise<T | undefined> => {
      setBusy(true);
      setActionError(null);
      try {
        const out = await fn();
        if (out && typeof out === "object" && "milestones" in (out as object)) res.setData(out as unknown as Contract);
        else await res.refresh();
        return out;
      } catch (e) {
        setActionError(errorText(e, fallback));
        return undefined;
      } finally {
        setBusy(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [id, sdk],
  );

  return { ...res, busy, actionError, setActionError, run };
}
