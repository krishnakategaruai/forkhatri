"use client";

// [IMP38 — Refactor C] Opportunity detail, behavioural half: the data hooks
// plus every member action, wired to the SDK in scope. Shared by the route
// (app/opportunities/[id]/page.tsx) and the embeddable
// OpportunityDetailPanel so both behave identically: each action shows the
// busy state, clears the notice, runs, then re-reads the opportunity from
// the server (never guesses the new state client-side); a failure shows the
// server's localized message.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, type NotInterestedReason } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useOpportunity, useOpportunityWhy, useSimilarOpportunities } from "@/app/hooks/opportunities";
import type { OpportunityDetailActions } from "./OpportunityDetailView";

export function useOpportunityDetailController(id: string) {
  const { t } = useTranslation(["opportunities", "common"]);
  const sdk = useSdk();
  const opportunity = useOpportunity(id);
  const similar = useSimilarOpportunities(id);
  const { why, load: loadWhy } = useOpportunityWhy(id);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hidden, setHidden] = useState(false);

  const opp = opportunity.data;
  const error = opportunity.error
    ? opportunity.error instanceof ApiError
      ? String(opportunity.error.detail)
      : t("common:state.notFound")
    : null;

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setNotice(null);
    try {
      await fn();
      await opportunity.refresh();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function share() {
    if (!opp) return;
    const url = typeof window !== "undefined" ? window.location.href : "";
    const data = { title: opp.title, text: `${opp.title} · Vyapar`, url };
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share(data);
      } catch {
        /* the member closed the native share sheet — not an error */
      }
    } else if (typeof navigator !== "undefined" && navigator.clipboard) {
      await navigator.clipboard.writeText(url);
      setNotice(t("common:action.linkCopied"));
    }
  }

  const actions: OpportunityDetailActions = {
    onToggleSave: () => act(() => (opp?.saved ? sdk.opportunities.unsave(id) : sdk.opportunities.save(id))),
    onShare: share,
    onExternalOpen: () => {
      sdk.opportunities.externalOpen(id).catch(() => {});
    },
    onPause: () => act(() => sdk.opportunities.pause(id)),
    onResume: () => act(() => sdk.opportunities.resume(id)),
    onRenew: () => act(() => sdk.opportunities.renew(id)),
    onClose: () => act(() => sdk.opportunities.close(id)),
    onConfirmField: (field) => act(() => sdk.opportunities.confirm(id, [field])),
    onPublish: () => act(() => sdk.opportunities.publish(id)),
    onNotInterested: (reason: NotInterestedReason) =>
      act(async () => {
        await sdk.opportunities.notInterested(id, reason);
        setHidden(true);
      }),
    onRequestWhy: loadWhy,
  };

  return {
    opportunity: opp,
    error,
    similar: similar.data ?? [],
    why,
    busy,
    notice,
    hidden,
    actions,
  };
}
