"use client";

// [Recommendations 2026-09-30] The one toast for card feedback ("Hidden.
// You'll see fewer like this." · Undo). Mounted once in the root layout so
// it outlives the card that was tapped and works on every screen that
// shows cards. Uses the shared .vy-toast look (hiring.css); announced
// politely to screen readers.
import { useTranslation } from "react-i18next";
import { X } from "lucide-react";
import { dismissToast, undoToast, useRecoFeedback } from "./feedbackStore";

export default function RecoToast() {
  const { t } = useTranslation(["explore", "common"]);
  const { toast } = useRecoFeedback();
  return (
    <div className="vy-reco-toast-slot" role="status" aria-live="polite">
      {toast && (
        <div key={toast.id} className="vy-toast vy-reco-toast">
          <span>{toast.message}</span>
          {toast.undo && (
            <button
              type="button"
              className="vy-btn vy-btn-secondary"
              onClick={undoToast}
            >
              {t("explore:reco.undo")}
            </button>
          )}
          <button type="button" className="vy-reco-toast-close" aria-label={t("common:action.close")} onClick={dismissToast}>
            <X size={16} strokeWidth={2.25} aria-hidden="true" />
          </button>
        </div>
      )}
    </div>
  );
}
