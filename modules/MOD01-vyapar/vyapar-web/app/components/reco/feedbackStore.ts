"use client";

// [Recommendations 2026-09-30] One small store for the feedback a member
// gives on a post card ("Not interested", "More like this"), shared by
// every surface that shows cards (Discover rows, the flat results grid,
// "See all", the post page) and the one toast that confirms it.
//
// Why a module store and not component state: the card that was tapped
// disappears, so it cannot own the toast or the Undo. The store keeps
//   - the ids hidden on this device (every card list filters them out),
//   - the single toast on screen (message + optional Undo),
// and fires `vyapar:feed-changed` once the server has the feedback, so a
// Discover page re-reads its rows and similar posts drop without a reload.
//
// "Not interested" has no server-side undo (references/imp-recommendations.md),
// so the card hides at once and the call waits while the Undo toast is on
// screen: Undo cancels it (nothing is sent, nothing is learned); when the
// toast closes, times out or is replaced, or the page is left, it is sent.
import { useSyncExternalStore } from "react";

export const FEED_CHANGED_EVENT = "vyapar:feed-changed";

export interface RecoToast {
  id: number;
  message: string;
  /** Present when the action can be undone. */
  undo?: () => void;
  /** Runs once when the toast goes without Undo (the deferred commit). */
  commit?: () => void;
}

interface State {
  hidden: ReadonlySet<string>;
  toast: RecoToast | null;
}

let state: State = { hidden: new Set(), toast: null };
const listeners = new Set<() => void>();
let toastSeq = 0;
let toastTimer: ReturnType<typeof setTimeout> | null = null;

function emit(next: Partial<State>) {
  state = { ...state, ...next };
  listeners.forEach((l) => l());
}

function subscribe(l: () => void) {
  listeners.add(l);
  return () => listeners.delete(l);
}

const EMPTY: State = { hidden: new Set(), toast: null };

export function useRecoFeedback(): State {
  return useSyncExternalStore(subscribe, () => state, () => EMPTY);
}

/** Cards the member hid on this device (filters every card list). */
export function useHiddenPosts(): ReadonlySet<string> {
  return useRecoFeedback().hidden;
}

export function feedChanged() {
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent(FEED_CHANGED_EVENT));
}

function settle(toast: RecoToast | null) {
  const commit = toast?.commit;
  if (toast) toast.commit = undefined;
  commit?.();
}

export function showToast(message: string, opts: { undo?: () => void; commit?: () => void } = {}, ms = 6000) {
  if (toastTimer) clearTimeout(toastTimer);
  settle(state.toast); // a replaced toast keeps its action
  const toast: RecoToast = { id: ++toastSeq, message, undo: opts.undo, commit: opts.commit };
  emit({ toast });
  toastTimer = setTimeout(() => {
    if (state.toast?.id === toast.id) dismissToast();
  }, ms);
}

/** Close the toast; a pending action is sent. */
export function dismissToast() {
  if (toastTimer) clearTimeout(toastTimer);
  const t = state.toast;
  emit({ toast: null });
  settle(t);
}

/** Undo: close the toast and drop its pending action. */
export function undoToast() {
  if (toastTimer) clearTimeout(toastTimer);
  const t = state.toast;
  if (t) t.commit = undefined;
  emit({ toast: null });
  t?.undo?.();
}

if (typeof window !== "undefined") {
  // Leaving the page must not lose a "Not interested" still waiting on Undo.
  window.addEventListener("pagehide", () => settle(state.toast));
}

export function hidePost(id: string) {
  const hidden = new Set(state.hidden);
  hidden.add(id);
  emit({ hidden });
}

export function unhidePost(id: string) {
  const hidden = new Set(state.hidden);
  hidden.delete(id);
  emit({ hidden });
}
