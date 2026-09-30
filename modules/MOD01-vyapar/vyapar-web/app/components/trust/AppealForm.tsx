"use client";

// [FR41 → Trust pack §3] The one appeal form (createAppeal, POST
// /v1/appeals), opened in place on a card: what you want the team to know,
// optional evidence, Appeal / Cancel. Shared by My moderation outcomes and
// the Restrictions screen so both use the same flow and wording.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import FileUpload from "@/app/components/FileUpload";
import DisabledReason from "@/app/components/DisabledReason";

export default function AppealForm({ caseId, onDone, onCancel }: { caseId: string; onDone: () => void; onCancel: () => void }) {
  const { t } = useTranslation(["trustSafety", "common"]);
  const sdk = useSdk();
  const [text, setText] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reasonId = `why-appeal-${caseId}`;

  async function appeal() {
    setBusy(true);
    setError(null);
    try {
      await sdk.trustSafety.appeal({ case_id: caseId, text, evidence_urls: evidenceUrl ? [evidenceUrl] : [] });
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="vy-acct-form" style={{ gap: 12 }}>
      <textarea
        className="vy-textarea"
        rows={4}
        maxLength={1000}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t("trustSafety:outcomes.appealPlaceholder")}
        aria-label={t("trustSafety:outcomes.appeal")}
      />
      <div className="vy-acct-field">
        <span className="vy-label">{t("trustSafety:outcomes.evidenceLabel")}</span>
        <FileUpload value={evidenceUrl} onChange={setEvidenceUrl} />
      </div>
      {error && (
        <p className="vy-error" role="alert">
          {error}
        </p>
      )}
      <div className="vy-row">
        <button className="vy-btn vy-btn-primary" aria-describedby={!text ? reasonId : undefined} disabled={!text || busy} onClick={appeal}>
          {t("trustSafety:outcomes.appeal")}
        </button>
        <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={onCancel}>
          {t("common:action.cancel")}
        </button>
      </div>
      <DisabledReason id={reasonId} show={!text}>
        {t("common:disabled.appeal")}
      </DisabledReason>
    </div>
  );
}
