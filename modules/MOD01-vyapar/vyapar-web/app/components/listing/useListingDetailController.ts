"use client";

// [IMP38 — Refactor C] Listing detail, behavioural half: the data hook plus
// every owner/viewer action through the SDK in scope. Same contract the
// page always had: one GET, and after each mutating action the canonical
// listing is re-read from the server (never guessed client-side), so the
// screen can never drift from what RLS / the state machine allowed.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useListing } from "@/app/hooks/listings";
import type { ListingDetailActions } from "./ListingDetailView";

export function useListingDetailController(id: string) {
  const { t } = useTranslation(["listings", "common"]);
  const sdk = useSdk();
  const resource = useListing(id);
  const listing = resource.data;
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [otpRequested, setOtpRequested] = useState(false);
  const [devCode, setDevCode] = useState<string | null>(null);

  // [Audit 2026-10-06] a coded refusal's `detail` is an object
  // ({message, code, kind}); String() on it read "[object Object]" to the
  // member who tapped "Send for review". The message is what is shown.
  const detailText = (e: unknown, fallback: string): string => {
    if (!(e instanceof ApiError)) return fallback;
    if (typeof e.detail === "string" && e.detail) return e.detail;
    const d = e.detail as { message?: unknown } | null;
    return d && typeof d.message === "string" && d.message ? d.message : fallback;
  };
  const error = resource.error ? detailText(resource.error, t("common:state.notFound")) : null;

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setNotice(null);
    try {
      await fn();
      await resource.refresh();
    } catch (e) {
      setNotice(detailText(e, t("common:state.actionFailed")));
    } finally {
      setBusy(false);
    }
  }

  async function share() {
    if (!listing) return;
    const url = typeof window !== "undefined" ? window.location.href : "";
    const shareData = { title: listing.name, text: `${listing.name} on Vyapar`, url };
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share(shareData);
      } catch {
        /* member cancelled the native share sheet — not an error */
      }
    } else if (typeof navigator !== "undefined" && navigator.clipboard) {
      await navigator.clipboard.writeText(url);
      setNotice(t("common:action.linkCopied"));
    }
  }

  const actions: ListingDetailActions = {
    onToggleSave: () => act(() => (listing?.saved ? sdk.listings.unsave(id) : sdk.listings.save(id))),
    onShare: share,
    onAttachCredential: () => act(() => sdk.listings.attachCredential(id)),
    onSubmit: () => act(() => sdk.listings.submit(id)),
    onArchive: () => act(() => sdk.listings.archive(id)),
    onRequestOtp: (phone) =>
      act(async () => {
        const r = await sdk.listings.requestOtp(id, phone);
        setOtpRequested(true);
        setDevCode(r.dev_code ?? null);
      }),
    onVerifyOtp: (code) => act(() => sdk.listings.verifyOtp(id, code)),
    onUpdateContact: (index, disclosure) => {
      if (!listing) return;
      const next = listing.contacts.map((c, i) => (i === index ? { ...c, disclosure } : c));
      void act(() => sdk.listings.updateContacts(id, next));
    },
    onToggleDiscoverable: (discoverable) => act(() => sdk.listings.setVisibility(id, discoverable, false)),
    onUpdateIntent: (patch) => act(() => sdk.listings.updateIntent(id, patch)),
  };

  return { listing, error, busy, notice, otpRequested, devCode, actions, refresh: resource.refresh };
}
