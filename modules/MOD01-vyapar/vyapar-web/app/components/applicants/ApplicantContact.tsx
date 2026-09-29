"use client";

// [FE1 — 2026-09-29, imp-backend-a §6] Call / WhatsApp for a shortlisted
// applicant (WorkIndia / Apna: the poster calls the people they shortlist).
// Presentational: the actions come from the row's `contact_actions`, a tap
// goes out through `onContact`, which records the attempt first and only
// then opens tel: / wa.me. An action that is off right now shows its
// server-localized reason instead of a dead button.
import { useTranslation } from "react-i18next";
import type { ContactAction } from "@/lib/sdk";
import Icon from "@/app/components/Icon";

export default function ApplicantContact({
  actions,
  busy,
  onContact,
}: {
  actions: ContactAction[];
  busy: string | null;
  onContact: (action: ContactAction) => void;
}) {
  const { t } = useTranslation("hiring");
  if (actions.length === 0) return null;
  const reason = actions.find((a) => !a.available_now && a.reason_label)?.reason_label ?? null;
  return (
    <div className="vy-stack" style={{ gap: 4 }}>
      <div className="vy-applicant-actions">
        {actions.map((a) => (
          <button
            key={a.channel}
            type="button"
            className="vy-btn vy-btn-secondary"
            disabled={!a.available_now || !a.href || busy !== null}
            onClick={() => onContact(a)}
          >
            <Icon name={a.channel === "whatsapp" ? "whatsapp" : "phone"} size={16} />{" "}
            {busy === a.channel ? t("board.opening") : a.channel === "whatsapp" ? t("board.whatsapp") : t("board.call")}
          </button>
        ))}
      </div>
      {reason && <span className="vy-field-hint">{reason}</span>}
    </div>
  );
}
