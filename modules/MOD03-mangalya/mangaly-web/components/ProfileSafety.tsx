"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { REPORT_REASONS, block, report, type ReportReason } from "@/lib/safety";

/* [2026-10-01] Report and block from a profile, not only from inside a chat:
 * a fake or unsafe profile is usually noticed on Discover, before anyone has
 * talked. A quiet line at the foot of the profile (lib/safety: "behind a
 * quiet menu, never a loud button") opens the same reasons the chat uses. */
export default function ProfileSafety({ profileId }: { profileId: string }) {
  const { t } = useTranslation(["messages", "profile"]);
  const router = useRouter();
  const [panel, setPanel] = useState<null | "menu" | "report" | "block">(null);
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [details, setDetails] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function sendReport() {
    if (!reason) return;
    setBusy(true);
    const outcome = await report(profileId, reason, details.trim());
    setBusy(false);
    if (outcome.ok) {
      setPanel(null);
      setNotice(t("messages:thread.reportSent"));
    } else {
      setNotice(t("messages:error.network"));
    }
  }

  return (
    <section className="psafety">
      {notice && (
        <p className="chat-notice" role="status">
          {notice}
        </p>
      )}
      {panel === null && (
        <button type="button" className="psafety__link" onClick={() => setPanel("menu")}>
          {t("profile:safety.link")}
        </button>
      )}
      {panel === "menu" && (
        <div className="chat-panel">
          <div className="chat-panel__actions">
            <button type="button" className="btn" onClick={() => setPanel(null)}>
              {t("messages:thread.cancel")}
            </button>
            <button type="button" className="btn" onClick={() => setPanel("report")}>
              {t("messages:thread.report")}
            </button>
            <button type="button" className="btn btn--danger" onClick={() => setPanel("block")}>
              {t("messages:thread.block")}
            </button>
          </div>
        </div>
      )}
      {panel === "report" && (
        <div className="chat-panel">
          <p className="chat-panel__label">{t("profile:safety.reportTitle")}</p>
          <div className="chip-row">
            {REPORT_REASONS.map((r) => (
              <button
                key={r}
                type="button"
                className={`quick-pick__chip${reason === r ? " is-on" : ""}`}
                aria-pressed={reason === r}
                onClick={() => setReason(r)}
              >
                {t(`messages:reason.${r}`)}
              </button>
            ))}
          </div>
          <div className="field__box">
            <textarea
              className="field__input"
              rows={2}
              placeholder={t("messages:thread.reportDetails")}
              value={details}
              onChange={(e) => setDetails(e.target.value)}
            />
          </div>
          <p className="caption" style={{ margin: 0 }}>
            {t("profile:safety.reportNote")}
          </p>
          <div className="chat-panel__actions">
            <button type="button" className="btn" onClick={() => setPanel(null)}>
              {t("messages:thread.cancel")}
            </button>
            <button
              type="button"
              className="btn btn--primary"
              disabled={!reason || busy}
              onClick={sendReport}
            >
              {t("messages:thread.reportSend")}
            </button>
          </div>
        </div>
      )}
      {panel === "block" && (
        <div className="chat-panel">
          <p className="chat-panel__label">{t("profile:safety.blockConfirm")}</p>
          <div className="chat-panel__actions">
            <button type="button" className="btn" onClick={() => setPanel(null)}>
              {t("messages:thread.cancel")}
            </button>
            <button
              type="button"
              className="btn btn--danger"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                const outcome = await block(profileId);
                setBusy(false);
                if (outcome.ok) router.push("/discover");
                else setNotice(t("messages:error.network"));
              }}
            >
              {t("messages:thread.blockYes")}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
