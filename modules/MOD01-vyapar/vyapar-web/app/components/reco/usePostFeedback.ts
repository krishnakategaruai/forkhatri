"use client";

// [Recommendations 2026-09-30] The two things a member can tell Vyapar about
// a post, wired once for the card menu and the post page:
//   - More like this: one call, a toast, the feed re-reads (a "More like
//     what you saved" row can appear);
//   - Not interested + a reason: the card disappears at once and the toast
//     offers Undo; when the toast goes, the server hides the post and
//     learns from the reason, and the feed re-reads.
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import type { NotInterestedReason } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { feedChanged, hidePost, showToast, unhidePost } from "./feedbackStore";

/** The five reasons, in the order a worker thinks of them. The values are
 *  the API's existing reason names (references/imp-recommendations.md). */
export const NOT_INTERESTED_REASONS: { value: NotInterestedReason; key: string }[] = [
  { value: "not_my_capability", key: "wrongTrade" },
  { value: "too_far", key: "tooFar" },
  { value: "value_too_low", key: "payTooLow" },
  { value: "wrong_type", key: "notMyKind" },
  { value: "already_found", key: "alreadyFilled" },
];

export function usePostFeedback() {
  const { t } = useTranslation(["explore", "common"]);
  const sdk = useSdk();

  const moreLikeThis = useCallback(
    async (id: string) => {
      try {
        await sdk.opportunities.moreLikeThis(id);
        showToast(t("explore:reco.moreDone"));
        feedChanged();
      } catch {
        showToast(t("common:state.actionFailed"));
      }
    },
    [sdk, t],
  );

  /** Hides the post at once and offers Undo; the call is sent when the
   *  toast goes (see feedbackStore). `onUndone` runs after Undo (the post
   *  page shows itself again). */
  const notInterested = useCallback(
    (id: string, reason: NotInterestedReason, onUndone?: () => void) => {
      hidePost(id);
      showToast(t("explore:reco.hiddenDone"), {
        undo: () => {
          unhidePost(id);
          onUndone?.();
        },
        commit: () => {
          sdk.opportunities
            .notInterested(id, reason)
            .then(feedChanged)
            .catch(() => {
              unhidePost(id);
              onUndone?.();
              showToast(t("common:state.actionFailed"));
            });
        },
      });
      return true;
    },
    [sdk, t],
  );

  return { moreLikeThis, notInterested };
}
