"use client";

// ======================================================================
// [FE1 — 2026-09-28] Applicants board — the behavioural half (data hooks
// and every poster action, wired to the SDK). The markup is in
// ApplicantsBoardView. Rules implemented here:
//  - Tabs are the pipeline stages with counts from `stage_counts`.
//  - "Best match" asks the AI shortlist (1–10 with reasons and risks);
//    if that is unavailable (daily limit, no provider…) the list's own
//    rule-based `sort=match` order is used and the card shows the
//    count-based "matches n of m skills" line instead of a score.
//  - Shortlist is immediate with an Undo toast (back to "new").
//  - Decline is final on the server, so it is held for a few seconds with
//    an Undo toast and only then sent; leaving the page sends it at once.
//  - Hire needs a confirm step (it shares both phone numbers).
//  - Every change re-reads the list; nothing is guessed client-side.
// ======================================================================

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, type ContactAction, type AiShortlist, type AiShortlistItem, type Applicant, type ApplicantStage, type OpportunitySuggestion } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useOpportunity } from "@/app/hooks/opportunities";
import { useApplicants, useMemberBadges } from "@/app/hooks/hiring";
import { openContactNow } from "@/lib/contactTap";

export type SortKey = "newest" | "best";
const DECLINE_GRACE_MS = 5000;

export interface Toast {
  text: string;
  undo?: () => void;
}

export function useApplicantsBoard(opportunityId: string) {
  const { t, i18n } = useTranslation(["hiring", "common"]);
  const sdk = useSdk();
  const opportunity = useOpportunity(opportunityId);
  const [stage, setStage] = useState<ApplicantStage>("new");
  const [sort, setSort] = useState<SortKey>("newest");
  const [aiState, setAiState] = useState<{ data: AiShortlist | null; failed: boolean; loading: boolean }>({ data: null, failed: false, loading: false });
  const list = useApplicants(opportunityId, stage, sort === "best" && aiState.failed ? "match" : "newest");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [confirmHireId, setConfirmHireId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingDecline, setPendingDecline] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<OpportunitySuggestion[]>([]);
  const declineTimers = useRef(new Map<string, ReturnType<typeof setTimeout>>());
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const badges = useMemberBadges((list.data?.items ?? []).map((a) => a.sender_id));

  // AI shortlist: only when "Best match" is chosen (it counts against the daily AI allowance).
  const loadAi = useCallback(async () => {
    setAiState((s) => ({ ...s, loading: true }));
    try {
      const data = await sdk.ai.getAiShortlist(opportunityId, i18n.language);
      setAiState({ data, failed: false, loading: false });
    } catch {
      setAiState({ data: null, failed: true, loading: false });
    }
  }, [sdk, opportunityId, i18n.language]);

  useEffect(() => {
    if (sort !== "best") return;
    let live = true;
    queueMicrotask(() => {
      if (live) void loadAi();
    });
    return () => {
      live = false;
    };
  }, [sort, loadAi]);

  const aiById = useMemo(() => new Map<string, AiShortlistItem>((aiState.data?.items ?? []).map((i) => [i.enquiry_id, i])), [aiState.data]);

  const items = useMemo(() => {
    const rows = (list.data?.items ?? []).filter((a) => !pendingDecline.includes(a.enquiry_id));
    if (sort === "best" && aiState.data) {
      return [...rows].sort((a, b) => (aiById.get(b.enquiry_id)?.match_score ?? -1) - (aiById.get(a.enquiry_id)?.match_score ?? -1));
    }
    return rows;
  }, [list.data, pendingDecline, sort, aiState.data, aiById]);

  const counts = useMemo(() => {
    const c = { ...(list.data?.stage_counts ?? { new: 0, shortlisted: 0, hired: 0, declined: 0 }) };
    for (const id of pendingDecline) {
      const row = list.data?.items.find((a) => a.enquiry_id === id);
      if (row) {
        c[row.stage] = Math.max(0, (c[row.stage] ?? 0) - 1);
        c.declined = (c.declined ?? 0) + 1;
      }
    }
    return c;
  }, [list.data, pendingDecline]);

  // With nothing yet, the empty state shows the same tips the composer uses.
  const total = counts.new + counts.shortlisted + counts.hired + counts.declined;
  useEffect(() => {
    if (!list.data || total > 0) return;
    sdk.posting
      .suggestions(opportunityId)
      .then((r) => setSuggestions(r.suggestions.slice(0, 3)))
      .catch(() => setSuggestions([]));
  }, [list.data, total, sdk, opportunityId]);

  function showToast(next: Toast) {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(next);
    toastTimer.current = setTimeout(() => setToast(null), DECLINE_GRACE_MS);
  }

  function errorText(e: unknown): string {
    if (e instanceof ApiError && e.code) return t(`hiring:errors.${e.code}`, { defaultValue: typeof e.detail === "string" ? e.detail : t("common:state.actionFailed") });
    return t("common:state.actionFailed");
  }

  async function move(a: Applicant, next: ApplicantStage) {
    setBusyId(a.enquiry_id);
    setError(null);
    try {
      await sdk.applicants.setStage(opportunityId, a.enquiry_id, next);
      await list.refresh();
      if (sort === "best" && aiState.data) void loadAi();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusyId(null);
    }
  }

  const displayName = (a: Applicant) => a.profile.name ?? a.name ?? t("hiring:board.someone");

  async function shortlist(a: Applicant) {
    const was = a.stage;
    await move(a, "shortlisted");
    showToast({
      text: t("hiring:board.toastShortlisted", { name: displayName(a) }),
      undo: () => {
        setToast(null);
        void move({ ...a, stage: "shortlisted" }, was);
      },
    });
  }

  function commitDecline(id: string) {
    declineTimers.current.delete(id);
    const a = list.data?.items.find((x) => x.enquiry_id === id);
    if (!a) return;
    void sdk.applicants
      .setStage(opportunityId, id, "declined")
      .catch((e) => setError(errorText(e)))
      .finally(async () => {
        await list.refresh();
        setPendingDecline((p) => p.filter((x) => x !== id));
      });
  }

  function decline(a: Applicant) {
    const id = a.enquiry_id;
    setPendingDecline((p) => [...p, id]);
    setCompareIds((c) => c.filter((x) => x !== id));
    if (selectedId === id) setSelectedId(null);
    declineTimers.current.set(id, setTimeout(() => commitDecline(id), DECLINE_GRACE_MS));
    showToast({
      text: t("hiring:board.toastDeclined", { name: displayName(a) }),
      undo: () => {
        const timer = declineTimers.current.get(id);
        if (timer) clearTimeout(timer);
        declineTimers.current.delete(id);
        setPendingDecline((p) => p.filter((x) => x !== id));
        setToast(null);
      },
    });
  }

  // Leaving the page sends any decline still waiting out its Undo window.
  useEffect(() => {
    const timers = declineTimers.current;
    const flush = () => {
      for (const [id, timer] of timers) {
        clearTimeout(timer);
        void sdk.applicants.setStage(opportunityId, id, "declined").catch(() => undefined);
      }
      timers.clear();
    };
    window.addEventListener("pagehide", flush);
    return () => {
      window.removeEventListener("pagehide", flush);
      flush();
    };
  }, [sdk, opportunityId]);

  // §6 + [FE2, critique L4]: open the link inside the tap (a slow network
  // must never make Call look dead), then record the attempt with keepalive.
  const [contactBusy, setContactBusy] = useState<{ id: string; channel: string } | null>(null);
  function contact(a: Applicant, action: ContactAction) {
    const channel = action.channel === "whatsapp" ? "whatsapp" : "call";
    const href = action.href;
    if (!href) return;
    setContactBusy({ id: a.enquiry_id, channel });
    setError(null);
    openContactNow(channel, href);
    sdk.applicants
      .recordContact(opportunityId, a.enquiry_id, channel)
      .then(() => void list.refresh())
      .catch((e) => setError(errorText(e)))
      .finally(() => setContactBusy(null));
  }

  async function hire(a: Applicant) {
    setConfirmHireId(null);
    await move(a, "hired");
    setSelectedId(a.enquiry_id);
    showToast({ text: t("hiring:board.toastHired", { name: displayName(a) }) });
  }

  function toggleCompare(id: string) {
    setCompareIds((c) => (c.includes(id) ? c.filter((x) => x !== id) : c.length >= 4 ? c : [...c, id]));
  }

  function changeStage(next: ApplicantStage) {
    setStage(next);
    setSelectedId(null);
    setCompareIds([]);
    setConfirmHireId(null);
  }

  return {
    opportunity: opportunity.data,
    opportunityError: opportunity.error,
    loading: list.data === null,
    listError: list.error,
    items,
    counts,
    total,
    stage,
    changeStage,
    sort,
    setSort,
    ai: aiState,
    aiById,
    badges: badges.data ?? {},
    selectedId: selectedId && items.some((a) => a.enquiry_id === selectedId) ? selectedId : (items[0]?.enquiry_id ?? null),
    select: setSelectedId,
    compareIds,
    toggleCompare,
    clearCompare: () => setCompareIds([]),
    confirmHireId,
    askHire: setConfirmHireId,
    busyId,
    error,
    toast,
    dismissToast: () => setToast(null),
    suggestions,
    shortlist,
    decline,
    hire,
    moveBack: (a: Applicant) => move(a, "new"),
    contact,
    contactBusyFor: (a: Applicant) => (contactBusy?.id === a.enquiry_id ? contactBusy.channel : null),
    displayName,
  };
}

export type ApplicantsBoard = ReturnType<typeof useApplicantsBoard>;
