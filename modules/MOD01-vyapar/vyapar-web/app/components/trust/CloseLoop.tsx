"use client";

// ======================================================================
// [Trust pack §3, 2026-09-30] Close the loop.
//
// REQUIREMENT: nobody who applied is left without an answer. Before the
// person who posted closes a post, they see how many applicants are still
// waiting, with a way to review them first; the confirmation says the ones
// still waiting will be told politely. Applicants see "Post closed" quietly
// in their Requests, never "Rejected".
// APPROACH:
//  - <ApplicantsWaitingNudge>: the poster's own post shows
//    `applicants_waiting.message` above the applicants card (whose button
//    is the way in) — nothing when nobody waits.
//  - <CloseConfirmSheet>: Close opens this sheet; it reads
//    getOpportunityCloseCheck and shows the waiting line, "Review
//    applicants" (the board) and the server's `close_message`, then
//    "Close post". With nobody waiting it is one line and one button.
// ======================================================================

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Hourglass, Users } from "lucide-react";
import type { ApplicantsWaiting, CloseCheck } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Sheet from "@/app/components/respond/Sheet";

// The applicants card right under it carries the way in ("Review 1 new"), so
// the nudge is one line of fact, not a second button to the same place.
export function ApplicantsWaitingNudge({ waiting }: { waiting: ApplicantsWaiting | null | undefined }) {
  const { t } = useTranslation(["opportunities"]);
  if (!waiting || waiting.waiting <= 0 || !waiting.message) return null;
  return (
    <div className="vy-waiting vy-waiting-nudge" role="status">
      <Hourglass size={18} strokeWidth={1.9} aria-hidden="true" />
      <div className="vy-waiting-text">
        <strong>{waiting.message}</strong>
        {waiting.oldest_waiting_days != null && waiting.oldest_waiting_days > 0 && (
          <span className="vy-num">{t("opportunities:closeLoop.oldest", { count: waiting.oldest_waiting_days })}</span>
        )}
      </div>
    </div>
  );
}

export function CloseConfirmSheet({ opportunityId, busy, onConfirm, onCancel }: { opportunityId: string; busy: boolean; onConfirm: () => void; onCancel: () => void }) {
  const { t } = useTranslation(["opportunities", "common"]);
  const sdk = useSdk();
  const [check, setCheck] = useState<CloseCheck | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let live = true;
    sdk.trustPack
      .closeCheck(opportunityId)
      .then((c) => live && setCheck(c))
      .catch(() => live && setFailed(true));
    return () => {
      live = false;
    };
  }, [sdk, opportunityId]);

  const waiting = check?.waiting ?? 0;

  return (
    <Sheet title={t("opportunities:closeLoop.title")} onClose={onCancel}>
      <div className="vy-closecheck">
        {!check && !failed && <div className="vy-skeleton" style={{ height: 72 }} aria-hidden="true" />}
        {check && waiting > 0 && (
          <div className="vy-waiting">
            <Users size={18} strokeWidth={1.9} aria-hidden="true" />
            <div className="vy-waiting-text">
              <strong>{check.message}</strong>
              {/* the split only says something when there are both kinds */}
              {check.new > 0 && check.shortlisted > 0 && (
                <span className="vy-num">
                  {t("opportunities:closeLoop.newCount", { count: check.new })} · {t("opportunities:closeLoop.shortlistedCount", { count: check.shortlisted })}
                </span>
              )}
            </div>
          </div>
        )}
        {/* our own plural ("the person" / "the 3 people"); the API's line when nobody waits */}
        {check && <p className="vy-closecheck-body">{waiting > 0 ? t("opportunities:closeLoop.closeMessage", { count: waiting }) : check.close_message}</p>}
        {failed && <p className="vy-closecheck-body">{t("opportunities:closeLoop.fallback")}</p>}
        <div className="vy-closecheck-actions">
          {waiting > 0 && (
            <Link className="vy-btn vy-btn-primary" href={`/opportunities/${opportunityId}/applicants`} transitionTypes={["vy-forward"]}>
              {t("opportunities:closeLoop.reviewFirst")}
            </Link>
          )}
          <button type="button" className={`vy-btn ${waiting > 0 ? "vy-btn-secondary" : "vy-btn-primary"}`} disabled={busy || (!check && !failed)} onClick={onConfirm}>
            {t("opportunities:closeLoop.confirm")}
          </button>
          <button type="button" className="vy-btn vy-btn-ghost" disabled={busy} onClick={onCancel}>
            {t("common:action.cancel")}
          </button>
        </div>
      </div>
    </Sheet>
  );
}
