"use client";

// [Recommendations 2026-09-30] "Not interested" — five reasons as large
// rows (56px, icon + words), one tap is the whole decision: the sheet
// closes, the card disappears, a toast offers Undo. No Submit button, no
// second step. A bottom sheet on a phone, a small centred panel on desktop
// (the shared <Sheet>), portalled to <body> so a card's transform or a
// row's scroll clipping can never trap it.
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import { Ban, IndianRupee, MapPinOff, Shapes, Wrench, type LucideIcon } from "lucide-react";
import type { NotInterestedReason } from "@/lib/sdk";
import Sheet from "@/app/components/respond/Sheet";
import { NOT_INTERESTED_REASONS } from "./usePostFeedback";

const ICON: Record<string, LucideIcon> = {
  wrongTrade: Wrench,
  tooFar: MapPinOff,
  payTooLow: IndianRupee,
  notMyKind: Shapes,
  alreadyFilled: Ban,
};

export default function NotInterestedSheet({
  onPick,
  onClose,
}: {
  onPick: (reason: NotInterestedReason) => void;
  onClose: () => void;
}) {
  const { t } = useTranslation(["explore"]);
  if (typeof document === "undefined") return null;
  return createPortal(
    <Sheet title={t("explore:reco.sheetTitle")} onClose={onClose}>
      <p className="vy-reco-sheet-lead">{t("explore:reco.sheetLead")}</p>
      <ul className="vy-reco-reasons" role="list">
        {NOT_INTERESTED_REASONS.map((r) => {
          const I = ICON[r.key];
          return (
            <li key={r.value}>
              <button type="button" className="vy-reco-reason" onClick={() => onPick(r.value)}>
                <span className="vy-reco-reason-icon" aria-hidden="true">
                  <I size={20} strokeWidth={1.9} />
                </span>
                <span>{t(`explore:reco.reason.${r.key}`)}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </Sheet>,
    document.body,
  );
}
